import os
import tempfile

import pytest
import torch

from model.ddsp.newt import NEWTUnit, SawtoothExciter
from model.ddsp.variant import DDSPVariant
from model.ddsp_model import DDSPConfig, DDSPModel


def test_sawtooth_shape() -> None:
    f0 = torch.full((1, 32), 200.0)
    out = SawtoothExciter()(f0, sample_rate=16000, hop_length=128)
    assert out.shape == (1, 31 * 128 + 1)


def test_sawtooth_range() -> None:
    f0 = torch.full((1, 32), 300.0)
    out = SawtoothExciter()(f0, sample_rate=16000, hop_length=128)
    assert out.min() >= -1.0
    assert out.max() <= 1.0
    assert torch.isfinite(out).all()


def test_sawtooth_frequency() -> None:
    f0 = torch.full((1, 32), 220.0)
    out = SawtoothExciter()(f0, sample_rate=16000, hop_length=128)
    saw = out.squeeze()
    sign = saw.sign()
    crossings = (sign[..., 1:] != sign[..., :-1]).sum().item()
    n_samples = out.shape[1]
    estimated_freq = crossings * 16000 / (2 * n_samples)
    assert estimated_freq > 0
    assert estimated_freq < 500


def test_newt_forward() -> None:
    unit = NEWTUnit()
    excitation = torch.randn(1, 1024)
    gain = torch.ones(1, 1024)
    bias = torch.zeros(1, 1024)
    out = unit(excitation, gain, bias)
    assert out.shape == (1, 1024)
    assert torch.isfinite(out).all()


def test_newt_backward() -> None:
    unit = NEWTUnit()
    excitation = torch.randn(1, 1024)
    gain = torch.ones(1, 1024)
    bias = torch.zeros(1, 1024)
    out = unit(excitation, gain, bias)
    loss = out.mean()
    loss.backward()
    assert all(p.grad is not None for p in unit.parameters())


def test_newt_init_weights() -> None:
    unit = NEWTUnit()
    first_w = unit.layers[0].weight
    assert first_w.min() >= -3.15
    assert first_w.max() <= 3.15
    for layer in unit.layers[1:-1]:
        fan_in = layer.weight.shape[1]
        bound = 1.0 / fan_in**0.5
        assert layer.weight.min() >= -bound
        assert layer.weight.max() <= bound


def test_ddsp_model_newt_forward() -> None:
    cfg = DDSPConfig(hidden_size=64)
    variant = DDSPVariant(engine="newt")
    model = DDSPModel(cfg, variant=variant)
    f0 = torch.rand(1, 32) * 300 + 100
    loudness = torch.randn(1, 32)
    out = model(f0, loudness)
    assert torch.isfinite(out["audio"]).all()


def test_ddsp_model_newt_backward() -> None:
    cfg = DDSPConfig(hidden_size=64)
    variant = DDSPVariant(engine="newt")
    model = DDSPModel(cfg, variant=variant)
    f0 = torch.rand(1, 32) * 300 + 100
    loudness = torch.randn(1, 32)
    out = model(f0, loudness)
    loss = out["audio"].square().mean()
    loss.backward()
    assert all(p.grad is not None for p in model.gru.parameters())


def test_ddsp_model_newt_checkpoint_tag() -> None:
    cfg = DDSPConfig(hidden_size=64)
    variant = DDSPVariant(engine="newt")
    model = DDSPModel(cfg, variant=variant)
    with tempfile.NamedTemporaryFile(suffix=".pt", delete=False) as f:
        path = f.name
    try:
        model.save_checkpoint(path)
        loaded = DDSPModel.load_checkpoint(path)
        assert loaded.variant.engine == "newt"
    finally:
        if os.path.exists(path):
            os.remove(path)


def test_ddsp_model_newt_mismatch_raises() -> None:
    cfg = DDSPConfig(hidden_size=64)
    variant = DDSPVariant(engine="newt")
    model = DDSPModel(cfg, variant=variant)
    with tempfile.NamedTemporaryFile(suffix=".pt", delete=False) as f:
        path = f.name
    try:
        model.save_checkpoint(path)
        with pytest.raises(ValueError, match="engine"):
            DDSPModel.load_checkpoint(path, variant=DDSPVariant(engine="harmonic"))
    finally:
        if os.path.exists(path):
            os.remove(path)
