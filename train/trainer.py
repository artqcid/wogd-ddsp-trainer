"""Training loop, checkpointing/resume, and TensorBoard logging for DDSP models.

:single-module:
"""

from __future__ import annotations

import os
from dataclasses import dataclass

import torch
from torch import nn
from torch.utils.tensorboard import SummaryWriter

from model import DDSPModel, MultiScaleSpectralLoss


def _resolve_device(device_str: str) -> torch.device:
    """Resolve a device string to a torch.device.

    * ``"auto"`` → ``"cuda"`` if available, else ``"cpu"``.
    * ``"cuda"`` / ``"cpu"`` → passed through verbatim (fails later if
      unavailable, which is acceptable for an explicit user choice).
    """
    if device_str == "auto":
        device_str = "cuda" if torch.cuda.is_available() else "cpu"
    return torch.device(device_str)


@dataclass
class TrainingConfig:
    """Hyperparameters and runtime toggles for the DDSP training loop.

    Attributes:
        device: Target device. ``"auto"`` resolves to ``"cuda"`` when
            CUDA is available, otherwise ``"cpu"``.
        learning_rate: Adam learning rate.
        max_steps: Total number of training steps for :meth:`Trainer.run`.
        log_interval: Log scalar metrics to TensorBoard every N steps.
        checkpoint_interval: Write a checkpoint every N steps.
        use_mixed_precision: Use AMP on CUDA. Automatically disabled on
            CPU or when CUDA is unavailable.
        use_gradient_checkpointing: Wrap model modules with
            ``torch.utils.checkpoint`` to trade compute for memory.
        gradient_accumulation_steps: Accumulate gradients over N steps
            before calling ``optimizer.step()``.
        log_dir: Directory passed to ``SummaryWriter`` for TensorBoard
            logs.
    """

    device: str = "auto"
    learning_rate: float = 1e-3
    max_steps: int = 1000
    log_interval: int = 10
    checkpoint_interval: int = 100
    use_mixed_precision: bool = True
    use_gradient_checkpointing: bool = False
    gradient_accumulation_steps: int = 1
    log_dir: str = "runs"


class Trainer:
    """Single-model DDSP training driver with checkpointing and TensorBoard.

    Owns the model, optimizer, loss function, and summary writer. The public
    loop :meth:`run` repeatedly calls :meth:`train_step` on a single batch for
    prototyping; a real DataLoader/dataset is wired in later milestones.
    """

    def __init__(
        self,
        model: DDSPModel,
        config: TrainingConfig,
        device: str | None = None,
        optimizer: nn.Module | None = None,
    ) -> None:
        """Initialize the trainer.

        Args:
            model: DDSP model to train.
            config: Training hyperparameters and toggles.
            device: Device override. ``None`` means read from
                ``config.device``.
            optimizer: Pre-built optimizer. When ``None``, an Adam
                optimizer is built from ``config.learning_rate`` on the
                model parameters.
        """
        resolved = _resolve_device(device or config.device)
        self.device = resolved
        self.config = config

        self.model = model.to(resolved)

        # Optimizer: accept a pre-built one or build Adam on model params.
        if optimizer is None:
            optimizer = torch.optim.Adam(self.model.parameters(), lr=config.learning_rate)
        self.optimizer = optimizer

        self.loss_fn = MultiScaleSpectralLoss()

        # Mixed precision: auto-disable on CPU or when CUDA is missing.
        use_amp = bool(config.use_mixed_precision and self.device.type == "cuda")
        self.use_amp = use_amp
        if use_amp:
            self.scaler = torch.amp.GradScaler("cuda")
        else:
            self.scaler = None

        # Gradient checkpointing: wrap every nn.Module in the model so that
        # intermediate activations are recomputed instead of stored. Keep it
        # simple and functional — applied once at construction time.
        if config.use_gradient_checkpointing:
            self._enable_gradient_checkpointing()

        # Step counter and TensorBoard writer.
        self._step = 0
        self.writer = SummaryWriter(log_dir=config.log_dir)

    # ------------------------------------------------------------------
    # Gradient checkpointing helper
    # ------------------------------------------------------------------

    def _enable_gradient_checkpointing(self) -> None:
        """Wrap supported submodules with activation checkpointing.

        Uses ``torch.utils.checkpoint`` on each leaf module's ``forward``.
        This is a minimal, functional approach; modules whose forward is not
        compatible with checkpointing (e.g. stateful modules with randomness
        or side effects) may misbehave and should not have checkpointing
        enabled.
        """
        from torch.utils.checkpoint import checkpoint

        def _wrap(module: nn.Module) -> None:
            if isinstance(module, nn.Sequential):
                return  # let Sequential handle its children
            forward = module.forward
            module.forward = lambda *a, **k: checkpoint(forward, *a, use_reentrant=False, **k)

        self.model.apply(_wrap)

    # ------------------------------------------------------------------
    # Core step
    # ------------------------------------------------------------------

    def train_step(
        self,
        f0: torch.Tensor,
        loudness: torch.Tensor,
        target_audio: torch.Tensor,
    ) -> dict[str, object]:
        """Run one optimization step.

        Args:
            f0: Per-frame fundamental frequency in Hz, shape ``(B, T_frames)``.
            loudness: Per-frame log energy, shape ``(B, T_frames)``.
            target_audio: Target waveform, shape ``(B, T_audio)``.

        Returns:
            Dict with keys ``"loss"`` (Python float) and ``"step"``
            (the global step counter *before* this step was executed).
        """
        self.model.train()

        # Move inputs to the training device.
        f0 = f0.to(self.device)
        loudness = loudness.to(self.device)
        target_audio = target_audio.to(self.device)

        # Zero gradients.
        self.optimizer.zero_grad(set_to_none=True)

        # Forward + loss under AMP when enabled.
        if self.use_amp:
            ctx = torch.amp.autocast("cuda")
        else:
            # no-op context manager for the non-AMP path.
            from contextlib import nullcontext

            ctx = nullcontext()

        with ctx:
            predicted = self.model(f0, loudness)["audio"]
            loss = self.loss_fn(predicted, target_audio)

        # Backward + step.
        if self.use_amp:
            self.scaler.scale(loss).backward()
            self.scaler.step(self.optimizer)
            self.scaler.update()
        else:
            loss.backward()
            self.optimizer.step()

        step_before = self._step
        self._step += 1

        return {"loss": float(loss.detach().cpu()), "step": step_before}

    # ------------------------------------------------------------------
    # Convenience loop
    # ------------------------------------------------------------------

    def run(
        self,
        f0: torch.Tensor,
        loudness: torch.Tensor,
        target_audio: torch.Tensor,
    ) -> dict[str, object]:
        """Run a single-batch training loop for ``config.max_steps``.

        Repeats :meth:`train_step` on the same batch, logs ``train/loss`` to
        TensorBoard every ``config.log_interval`` steps, and writes
        checkpoints every ``config.checkpoint_interval`` steps.

        Args:
            f0: Per-frame fundamental frequency in Hz, ``(B, T_frames)``.
            loudness: Per-frame log energy, ``(B, T_frames)``.
            target_audio: Target waveform, ``(B, T_audio)``.

        Returns:
            Summary dict with ``"steps"`` (int) and ``"final_loss"``
            (Python float). ``"final_loss"`` is the last reported loss value
            (which may be ``None`` if ``max_steps`` is zero).
        """
        final_loss: float | None = None

        for _ in range(self.config.max_steps):
            result = self.train_step(f0, loudness, target_audio)
            loss = result["loss"]
            step_after = result["step"] + 1  # step after this iteration

            # Log to TensorBoard.
            if step_after % self.config.log_interval == 0:
                self.writer.add_scalar("train/loss", loss, step_after)
                final_loss = loss

            # Checkpoint.
            if step_after % self.config.checkpoint_interval == 0:
                self._checkpoint_dir = getattr(self, "_checkpoint_dir", "checkpoints")
                ckpt_path = os.path.join(
                    self._checkpoint_dir,
                    f"step-{step_after}.pt",
                )
                self.save_checkpoint(ckpt_path)

        if final_loss is None:
            # max_steps was 0.
            final_loss = 0.0

        return {"steps": self._step, "final_loss": final_loss}

    # ------------------------------------------------------------------
    # Checkpointing
    # ------------------------------------------------------------------

    def save_checkpoint(self, path: str) -> None:
        """Save model, optimizer, and step counter to *path*.

        Args:
            path: Filesystem path for the checkpoint (typically
                ``.pt``).
        """
        torch.save(
            {
                "step": self._step,
                "model_state_dict": self.model.state_dict(),
                "optimizer_state_dict": self.optimizer.state_dict(),
            },
            path,
        )

    def load_checkpoint(self, path: str) -> dict:
        """Load a checkpoint and restore model, optimizer, and step.

        Args:
            path: Path to a checkpoint created by :meth:`save_checkpoint`.

        Returns:
            The loaded checkpoint dict (includes ``"step"``, plus the raw
            ``model_state_dict`` and ``optimizer_state_dict`` keys).
        """
        checkpoint = torch.load(path, map_location=self.device, weights_only=False)

        self.model.load_state_dict(checkpoint["model_state_dict"])
        self.optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
        self._step = int(checkpoint["step"])

        return checkpoint

    def resume(self, path: str) -> int:
        """Convenience wrapper: load *path* and return the restored step.

        Args:
            path: Path to a checkpoint.

        Returns:
            The training step restored from the checkpoint.
        """
        ckpt = self.load_checkpoint(path)
        return int(ckpt["step"])

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------

    def close(self) -> None:
        """Close the TensorBoard summary writer."""
        self.writer.close()
