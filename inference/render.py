"""Offline render from a DDSP checkpoint."""

from __future__ import annotations

import torch

from model import DDSPConfig, DDSPModel


def load_model_from_checkpoint(
    checkpoint_path: str,
    config: DDSPConfig | None = None,
) -> DDSPModel:
    """Load a DDSP model from a training checkpoint.

    The checkpoint must contain a ``"model_state_dict"`` key (as written by
    :mod:`train.trainer`). Ignores other keys such as ``"step"``.
    """
    cfg = config if config is not None else DDSPConfig()
    model = DDSPModel(cfg)
    state = torch.load(checkpoint_path, map_location="cpu", weights_only=True)
    model.load_state_dict(state["model_state_dict"])
    model.eval()
    return model


def render(
    model: DDSPModel,
    f0: torch.Tensor,
    loudness: torch.Tensor,
    sample_rate: int = 16000,
) -> tuple[torch.Tensor, int]:
    """Run DDSP inference and return the generated audio.

    Parameters
    ----------
    f0 : (B, T) or (T,) float tensor, Hz.
    loudness : (B, T) or (T,) float tensor, log energy.
    """
    f0 = _maybe_unsqueeze(f0)
    loudness = _maybe_unsqueeze(loudness)
    assert f0.dim() == 2 and loudness.dim() == 2, (
        "f0 and loudness must be 2D (B, T) after unbatching."
    )
    model.eval()
    with torch.no_grad():
        audio = model(f0, loudness)["audio"]
    if audio.size(0) == 1:
        audio = audio.squeeze(dim=0)
    return audio, sample_rate


def render_to_file(
    model: DDSPModel,
    f0: torch.Tensor,
    loudness: torch.Tensor,
    out_path: str,
    sample_rate: int = 16000,
    mono: bool = True,
) -> str:
    """Render audio and write a 16/24/32-bit float WAV file."""
    audio, _sr = render(model, f0, loudness, sample_rate=sample_rate)
    audio = audio.clamp(-1.0, 1.0)
    audio = audio.cpu().float()
    if mono and audio.dim() == 2 and audio.size(0) > 1:
        # Average across batch into a single mono channel.
        audio = audio.mean(dim=0, keepdim=True)
    if audio.dim() == 1:
        audio = audio.unsqueeze(dim=0)
    import torchaudio as _ta

    _ta.save(out_path, audio, sample_rate)
    return out_path


def _maybe_unsqueeze(x: torch.Tensor) -> torch.Tensor:
    if x.dim() == 1:
        return x.unsqueeze(dim=0)
    return x


def __getattr__(name: str):
    raise AttributeError(name)
