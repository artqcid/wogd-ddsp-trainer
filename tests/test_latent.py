import os
import tempfile

import torch

from model.ddsp_model import DDSPConfig, DDSPModel
from model.encoder import GRUEncoder
from train.trainer import Trainer, TrainingConfig


def test_gru_encoder_shape() -> None:
    enc = GRUEncoder()
    f0 = torch.rand(1, 32) * 300 + 100
    loudness = torch.randn(1, 32)
    mu, logvar = enc(f0, loudness)
    assert mu.shape == (1, 32, 32)
    assert logvar.shape == (1, 32, 32)


def test_gru_encoder_finite() -> None:
    enc = GRUEncoder()
    f0 = torch.rand(1, 32) * 300 + 100
    loudness = torch.randn(1, 32)
    mu, logvar = enc(f0, loudness)
    assert torch.isfinite(mu).all()
    assert torch.isfinite(logvar).all()


def test_model_latent_forward() -> None:
    cfg = DDSPConfig(hidden_size=64, use_latent=True, latent_dim=32)
    model = DDSPModel(cfg)
    f0 = torch.rand(1, 32) * 300 + 100
    loudness = torch.randn(1, 32)
    out = model(f0, loudness)
    assert torch.isfinite(out["audio"]).all()
    assert out["mu"] is not None
    assert out["logvar"] is not None
    assert out["mu"].shape == (1, 32, 32)


def test_model_latent_backward() -> None:
    cfg = DDSPConfig(hidden_size=64, use_latent=True, latent_dim=32)
    model = DDSPModel(cfg)
    f0 = torch.rand(1, 32) * 300 + 100
    loudness = torch.randn(1, 32)
    out = model(f0, loudness)
    loss = out["audio"].square().mean()
    loss.backward()
    assert all(p.grad is not None for p in model.gru.parameters())


def test_model_latent_eval() -> None:
    cfg = DDSPConfig(hidden_size=64, use_latent=True, latent_dim=32)
    model = DDSPModel(cfg)
    model.eval()
    f0 = torch.rand(1, 32) * 300 + 100
    loudness = torch.randn(1, 32)
    out = model(f0, loudness)
    assert torch.isfinite(out["audio"]).all()


def test_checkpoint_tag_latent() -> None:
    cfg = DDSPConfig(hidden_size=64, use_latent=True, latent_dim=32)
    model = DDSPModel(cfg)
    with tempfile.NamedTemporaryFile(suffix=".pt", delete=False) as f:
        path = f.name
    try:
        model.save_checkpoint(path)
        loaded = DDSPModel.load_checkpoint(path)
        assert loaded.config.use_latent is True
        assert loaded.config.latent_dim == 32
    finally:
        if os.path.exists(path):
            os.remove(path)


def test_model_latent_no_latent_fallback() -> None:
    cfg = DDSPConfig(hidden_size=64, use_latent=False)
    model = DDSPModel(cfg)
    f0 = torch.rand(1, 32) * 300 + 100
    loudness = torch.randn(1, 32)
    out = model(f0, loudness)
    assert out["mu"] is None
    assert out["logvar"] is None
    assert torch.isfinite(out["audio"]).all()


def test_trainer_kl_loss_step() -> None:
    cfg = DDSPConfig(hidden_size=64, use_latent=True, latent_dim=32)
    model = DDSPModel(cfg)
    tcfg = TrainingConfig(kl_beta=0.001, kl_warmup_steps=100)
    trainer = Trainer(model, tcfg)
    f0 = torch.rand(1, 32) * 300 + 100
    loudness = torch.randn(1, 32)
    target = torch.randn(1, 31 * 128 + 1)
    result = trainer.train_step(f0, loudness, target)
    assert "loss" in result
    assert result["loss"] > 0


def test_trainer_kl_warmup() -> None:
    cfg = DDSPConfig(hidden_size=64, use_latent=True, latent_dim=32)
    model = DDSPModel(cfg)
    tcfg = TrainingConfig(kl_beta=0.001, kl_warmup_steps=100)
    trainer = Trainer(model, tcfg)
    f0 = torch.rand(1, 32) * 300 + 100
    loudness = torch.randn(1, 32)
    target = torch.randn(1, 31 * 128 + 1)
    result_step1 = trainer.train_step(f0, loudness, target)
    result_step2 = trainer.train_step(f0, loudness, target)
    assert result_step1["loss"] > 0
    assert result_step2["loss"] > 0


def test_model_latent_harmonic_engine() -> None:
    cfg = DDSPConfig(hidden_size=64, use_latent=True, latent_dim=32)
    model = DDSPModel(cfg)
    f0 = torch.rand(1, 32) * 300 + 100
    loudness = torch.randn(1, 32)
    out = model(f0, loudness)
    assert torch.isfinite(out["audio"]).all()
    assert out["mu"] is not None
    assert out["logvar"] is not None
