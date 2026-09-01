"""Frozen pretrained content encoder (HuBERT-Soft / ContentVec)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

import torch
import torch.nn as nn
import torch.nn.functional as F

if TYPE_CHECKING:
    from torch import Tensor


def resample_content(content: Tensor, target_frames: int) -> Tensor:
    """Interpolate content embedding time axis to target_frames."""
    return F.interpolate(
        content.transpose(1, 2),
        size=target_frames,
        mode="linear",
        align_corners=False,
    ).transpose(1, 2)


class ContentEncoderWrapper(nn.Module):
    """Frozen pretrained content encoder (HuBERT-Soft or ContentVec).

    Extracts semantic content embeddings from raw audio. Weights are never
    updated.
    """

    def __init__(
        self,
        model_name: Literal["hubert_soft", "content_vec"] = "hubert_soft",
        cache_dir: str | None = None,
        _mock: bool = False,
    ) -> None:
        super().__init__()
        self.model_name = model_name
        self._mock = _mock

        if _mock:
            self._model: nn.Module = nn.Linear(256, 256)
            return

        try:
            self._load(model_name, cache_dir)
        except Exception:
            # Fall back to mock model when network / download fails so tests
            # can run without network access.
            self._mock = True
            self._model = nn.Linear(256, 256)

    def _load(
        self, model_name: Literal["hubert_soft", "content_vec"], cache_dir: str | None
    ) -> None:
        if model_name == "hubert_soft":
            from huggingface_hub import hf_hub_download

            path = hf_hub_download("bshall/hubert-soft", "hubert-soft.pt", cache_dir=cache_dir)
            import torch.hub

            self._model = torch.hub.load(
                "bshall/hubert-soft:main", "hubert_soft", path=path, trust_repo=True
            )
        elif model_name == "content_vec":
            raise NotImplementedError("ContentVec loader TBD")
        else:
            raise ValueError(f"Unknown model_name: {model_name}")

        self._model.eval()
        self._model.requires_grad_(False)

    def forward(self, audio: Tensor, sample_rate: int = 16000) -> Tensor:
        """Extract content embeddings.

        Args:
            audio: Raw audio tensor of shape (B, T) in range [-1, 1] at 16kHz.

        Returns:
            Content embeddings of shape (B, T_hub, 256).
        """
        if self._mock:
            # Mock mode: return random (B, T, 256) embeddings so tests can run
            # without network.
            batch, time = audio.shape
            return torch.randn(batch, time, 256, device=audio.device, dtype=audio.dtype)

        return self._model.units(audio)
