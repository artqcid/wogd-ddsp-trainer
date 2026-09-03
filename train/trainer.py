"""Training loop, checkpointing/resume, and TensorBoard logging for DDSP models.

:single-module:
"""

from __future__ import annotations

import logging
import os
import threading
from dataclasses import asdict, dataclass
from itertools import cycle
from typing import Any

import torch
from torch import nn
from torch.utils.data import DataLoader
from torch.utils.tensorboard import SummaryWriter

from model import DDSPModel, MultiScaleSpectralLoss
from model.param_manifest import ParamManifest, build_default_manifest

logger = logging.getLogger(__name__)


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
    kl_beta: float = 0.0
    kl_warmup_steps: int = 1000


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
        loss_fn: nn.Module | None = None,
        *,
        model_tier: str = "standard",
        variant_flags: dict[str, Any] | None = None,
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
            model_tier: Model tier used for the default parameter manifest.
                Defaults to ``"standard"``.
            variant_flags: Optional variant flags forwarded to the manifest
                builder when *model_tier* depends on them.
        """
        resolved = _resolve_device(device or config.device)
        self.device = resolved
        self.config = config
        self.model = model.to(resolved)

        # Optimizer: accept a pre-built one or build Adam on model params.
        if optimizer is None:
            optimizer = torch.optim.Adam(self.model.parameters(), lr=config.learning_rate)
        self.optimizer = optimizer

        self.loss_fn = loss_fn or MultiScaleSpectralLoss()

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

        # Parameter manifest bookkeeping.
        self._model_tier = model_tier
        self._variant_flags = variant_flags or {}
        self._param_manifest: ParamManifest | None = None

        logger.info(
            "Trainer initialised: device=%s model=%s tier=%s steps=%d lr=%g amp=%s",
            str(self.device),
            type(self.model).__name__,
            model_tier,
            config.max_steps,
            config.learning_rate,
            use_amp,
        )

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
            out = self.model(f0, loudness)
            predicted = out["audio"]
            loss = self.loss_fn(predicted, target_audio)

            if self.config.kl_beta > 0.0 and out.get("mu") is not None:
                mu = out["mu"]
                logvar = out["logvar"]
                kl = -0.5 * (1 + logvar - mu.pow(2) - logvar.exp()).mean()
                step_ratio = min(1.0, self._step / max(1, self.config.kl_warmup_steps))
                effective_beta = self.config.kl_beta * step_ratio
                loss = loss + effective_beta * kl

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

        logger.debug("train_step: step=%d loss=%.6f", step_before, float(loss.detach().cpu()))

        return {"loss": float(loss.detach().cpu()), "step": step_before}

    # ------------------------------------------------------------------
    # Convenience loop
    # ------------------------------------------------------------------

    def run(
        self,
        f0: torch.Tensor | None = None,
        loudness: torch.Tensor | None = None,
        target_audio: torch.Tensor | None = None,
        data_loader: DataLoader | None = None,
        stop_event: threading.Event | None = None,
    ) -> dict[str, object]:
        """Run the training loop for ``config.max_steps`` steps.

        When *data_loader* is provided, the loop iterates over real batches
        from the loader (wrapped with ``itertools.cycle`` so it never
        exhausts).         Each batch is a tuple ``(f0, loudness, audio, content_embedding)`` of
        tensors shaped ``(1, T)`` as yielded by ``DDSPDataset``, so no
        additional reshaping is required.

        When *data_loader* is ``None``, the loop repeats on the single
        pre-loaded batch (backward-compatible with existing callers).

        Args:
            f0: Per-frame fundamental frequency in Hz, ``(B, T_frames)``.
                Ignored when *data_loader* is provided.
            loudness: Per-frame log energy, ``(B, T_frames)``. Ignored when
                *data_loader* is provided.
            target_audio: Target waveform, ``(B, T_audio)``. Ignored when
                *data_loader* is provided.
            data_loader: Optional ``torch.utils.data.DataLoader`` yielding
                ``(f0, loudness, audio)`` tuples. When provided, *f0*,
                *loudness*, and *target_audio* are optional.
            stop_event: Optional ``threading.Event``. When set, the loop stops
                at the start of the next iteration (cooperative stop).

        Returns:
            Summary dict with ``"steps"`` (int) and ``"final_loss"``
            (Python float). ``"final_loss"`` is the last reported loss value
            (which may be ``None`` if ``max_steps`` is zero).
        """
        final_loss: float | None = None

        def _log_and_checkpoint(result: dict) -> None:
            nonlocal final_loss
            loss = result["loss"]
            step_after = result["step"] + 1
            if step_after % self.config.log_interval == 0:
                self.writer.add_scalar("train/loss", loss, step_after)
                final_loss = loss
            if step_after % self.config.checkpoint_interval == 0:
                self._checkpoint_dir = getattr(self, "_checkpoint_dir", "checkpoints")
                ckpt_path = os.path.join(
                    self._checkpoint_dir,
                    f"step-{step_after}.pt",
                )
                self.save_checkpoint(ckpt_path)

        if data_loader is not None:
            logger.info(
                "training run start: max_steps=%d loader=%s",
                self.config.max_steps,
                "data_loader" if data_loader else "single_batch",
            )
            loader_iter = iter(cycle(data_loader))
            for _ in range(self.config.max_steps):
                if stop_event is not None and stop_event.is_set():
                    break
                try:
                    f0_batch, loudness_batch, audio_batch, *_ = next(loader_iter)
                except StopIteration:
                    break
                result = self.train_step(f0_batch, loudness_batch, audio_batch)
                _log_and_checkpoint(result)
        else:
            for _ in range(self.config.max_steps):
                if stop_event is not None and stop_event.is_set():
                    break
                result = self.train_step(f0, loudness, target_audio)
                _log_and_checkpoint(result)

        if final_loss is None:
            # max_steps was 0.
            final_loss = 0.0

        logger.info("training run finish: steps=%d final_loss=%s", self._step, final_loss)

        return {"steps": self._step, "final_loss": final_loss}

    # ------------------------------------------------------------------
    # Checkpointing
    # ------------------------------------------------------------------

    def save_checkpoint(self, path: str) -> None:
        """Save model, optimizer, step, config, and parameter manifest to *path*.

        Args:
            path: Filesystem path for the checkpoint (typically ``.pt``).
        """
        state = {
            "step": self._step,
            "model_state_dict": self.model.state_dict(),
            "optimizer_state_dict": self.optimizer.state_dict(),
            "config": asdict(self.model.config),
        }

        if "param_manifest" not in state:
            state["param_manifest"] = build_default_manifest(
                self._model_tier,
                self._variant_flags,
            ).to_dict()

        state["model_tier"] = self._model_tier
        state["variant_flags"] = self._variant_flags

        torch.save(state, path)

        logger.info("checkpoint saved: step=%d path=%s", self._step, path)

    def load_checkpoint(self, path: str) -> dict:
        """Load a checkpoint and restore model, optimizer, step, and manifest.

        Args:
            path: Path to a checkpoint created by :meth:`save_checkpoint`.

        Returns:
            The loaded checkpoint dict (includes ``"step"``, plus the raw
            ``model_state_dict`` and ``optimizer_state_dict`` keys).
        """
        checkpoint = torch.load(path, map_location=self.device, weights_only=True)

        self.model.load_state_dict(checkpoint["model_state_dict"])
        self.optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
        self._step = int(checkpoint["step"])

        if "param_manifest" in checkpoint:
            self._param_manifest = ParamManifest.from_dict(checkpoint["param_manifest"])
        elif "model_tier" in checkpoint:
            self._param_manifest = build_default_manifest(
                checkpoint["model_tier"],
                checkpoint.get("variant_flags", {}),
            )
        else:
            # Backward-compat: old checkpoints without manifest info.
            self._param_manifest = build_default_manifest("standard", {})

        logger.info("checkpoint loaded: step=%d path=%s", self._step, path)
        return checkpoint

    @property
    def param_manifest(self) -> Any:
        """The parameter manifest associated with this trainer instance.

        When a checkpoint with a manifest (or model_tier/variant_flags) was
        loaded, this returns the deserialized ``ParamManifest``. Otherwise it
        returns ``None`` until :meth:`save_checkpoint` has run at least once.
        """
        return self._param_manifest

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
