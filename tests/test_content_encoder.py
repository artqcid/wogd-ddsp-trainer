"""Tests for ContentEncoderWrapper (M13.1)."""

from __future__ import annotations

import numpy as np
import torch

from model.content_encoder import ContentEncoderWrapper, resample_content


def test_content_encoder_offline() -> None:
    """CPU smoke test of ContentEncoderWrapper in mock mode."""
    torch.manual_seed(0)
    enc = ContentEncoderWrapper("hubert_soft", _mock=True)
    audio = torch.randn(1, 16000)
    with torch.no_grad():
        emb = enc(audio, 16000)
    assert emb.shape[-1] == 256
    assert torch.isfinite(emb).all()


def test_resample_content_shape() -> None:
    """resample_content output shape matches target_frames."""
    content = torch.randn(1, 50, 256)  # 50 Hubert frames, 256-dim
    target = 125  # DDSP frames
    result = resample_content(content, target_frames=target)
    assert result.shape == (1, target, 256)
    assert torch.isfinite(result).all()


def test_extract_content_embedding_shape() -> None:
    """extract_content_embedding returns (T_frames, 256) float32."""
    from dataset.features import extract_content_embedding

    audio = np.sin(2 * np.pi * 440 * np.arange(16000) / 16000).astype(np.float32)
    emb = extract_content_embedding(audio, 16000, target_frames=63)
    assert emb.shape == (63, 256)
    assert emb.dtype == np.float32


def test_resample_content_batch() -> None:
    """resample_content handles batched input correctly."""
    content = torch.randn(2, 50, 256)
    result = resample_content(content, target_frames=100)
    assert result.shape == (2, 100, 256)
