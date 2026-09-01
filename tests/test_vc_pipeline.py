"""Tests for VC pipeline (M13.3-M13.5)."""

from __future__ import annotations

import torch

from model.ddsp_model import DDSPConfig, DDSPModel


def test_ddsp_model_with_content_forward() -> None:
    """Content conditioning forward pass produces finite audio."""
    config = DDSPConfig(hidden_size=64, n_harmonics=30, use_content_encoder=True, content_dim=256)
    model = DDSPModel(config)
    torch.manual_seed(0)
    f0 = torch.rand(1, 16) * 400 + 50
    loudness = torch.rand(1, 16)
    content = torch.randn(1, 16, 256)
    out = model(f0, loudness, content_embedding=content)
    assert "audio" in out
    assert torch.isfinite(out["audio"]).all()


def test_ddsp_model_with_content_backward() -> None:
    """Content conditioning backward pass produces gradients."""
    config = DDSPConfig(hidden_size=64, n_harmonics=30, use_content_encoder=True, content_dim=256)
    model = DDSPModel(config)
    torch.manual_seed(0)
    f0 = torch.rand(1, 16) * 400 + 50
    loudness = torch.rand(1, 16)
    content = torch.randn(1, 16, 256)
    out = model(f0, loudness, content_embedding=content)
    loss = out["audio"].sum()
    loss.backward()
    has_grad = False
    for p in model.parameters():
        if p.grad is not None:
            has_grad = True
            assert not torch.isnan(p.grad).any()
    assert has_grad


def test_ddsp_model_content_none_fallback() -> None:
    """None content falls back to f0+loudness path."""
    config = DDSPConfig(hidden_size=64, n_harmonics=30, use_content_encoder=True)
    model = DDSPModel(config)
    f0 = torch.full((1, 16), 220.0)
    loudness = torch.zeros(1, 16)
    out = model(f0, loudness, content_embedding=None)
    assert torch.isfinite(out["audio"]).all()
    assert out["audio"].shape == (1, (16 - 1) * 128 + 1)


def test_ddsp_model_with_content_and_latent() -> None:
    """Content + latent work together."""
    config = DDSPConfig(
        hidden_size=64,
        n_harmonics=30,
        use_content_encoder=True,
        content_dim=256,
        use_latent=True,
        latent_dim=16,
    )
    model = DDSPModel(config)
    model.train()
    f0 = torch.rand(1, 16) * 400 + 50
    loudness = torch.rand(1, 16)
    content = torch.randn(1, 16, 256)
    out = model(f0, loudness, content_embedding=content)
    assert torch.isfinite(out["audio"]).all()


def test_checkpoint_tag_content_encoder(tmp_path: str) -> None:
    """Checkpoint has use_content_encoder and content_encoder_name."""
    import torch.serialization as _ts

    config = DDSPConfig(hidden_size=64, n_harmonics=30, use_content_encoder=True)
    model = DDSPModel(config)
    ckpt_path = str(tmp_path) + "/vc.pt"
    model.save_checkpoint(ckpt_path)
    with _ts.safe_globals([DDSPConfig]):
        state = torch.load(ckpt_path, map_location="cpu", weights_only=True)
    assert state.get("use_content_encoder") is True
    assert state.get("content_encoder_name") == "hubert_soft"


def test_ddsp_model_content_proj_trainable() -> None:
    """Content projection layer participates in gradient flow."""
    config = DDSPConfig(hidden_size=64, n_harmonics=30, use_content_encoder=True, content_dim=256)
    model = DDSPModel(config)
    torch.manual_seed(0)
    f0 = torch.rand(1, 16) * 400 + 50
    loudness = torch.rand(1, 16)
    content = torch.randn(1, 16, 256)
    out = model(f0, loudness, content_embedding=content)
    loss = out["audio"].sum()
    loss.backward()
    assert model.content_proj.weight.grad is not None
    assert not torch.isnan(model.content_proj.weight.grad).any()
