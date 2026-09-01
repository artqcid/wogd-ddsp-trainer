import os
import tempfile

import pytest
import torch

from model.ddsp.combsub import CombSubSynth
from model.ddsp.noise_colored import _brown_noise, _pink_noise
from model.ddsp.sinusoidal import SinusoidalSynth
from model.ddsp.synths import FilteredNoiseSynth
from model.ddsp.variant import DDSPVariant
from model.ddsp_model import DDSPConfig, DDSPModel


def test_sinusoidal_synth_forward() -> None:
    freqs = torch.rand(1, 32, 16) * 4000 + 100
    amps = torch.rand(1, 32, 16)
    out = SinusoidalSynth()(amps, freqs, 16000, 128)
    assert out.shape == (1, 31 * 128 + 1)
    assert torch.isfinite(out).all()


def test_sinusoidal_nyquist_mask() -> None:
    synth = SinusoidalSynth()
    freqs = torch.tensor([[[200.0, 400.0, 9000.0, 12000.0]]])
    amps = torch.ones(1, 1, 4)
    out = synth(amps, freqs, 16000, 128)
    assert torch.isfinite(out).all()
    assert out.abs().max() < 4.0


def test_combsub_voiced() -> None:
    synth = CombSubSynth(n_fir_taps=32)
    mags = torch.rand(1, 32, 32)
    f0 = torch.full((1, 32), 220.0)
    voiced = torch.ones(1, 32)
    out = synth(mags, f0, voiced, n_samples=31 * 128 + 1)
    assert torch.isfinite(out).all()


def test_combsub_unvoiced() -> None:
    synth = CombSubSynth(n_fir_taps=32)
    mags = torch.rand(1, 32, 32)
    f0 = torch.full((1, 32), 220.0)
    voiced = torch.zeros(1, 32)
    out = synth(mags, f0, voiced, n_samples=31 * 128 + 1)
    assert torch.isfinite(out).all()


def test_noise_pink() -> None:
    pn = _pink_noise(1024, "cpu", torch.float32)
    assert torch.isfinite(pn).all()


def test_noise_brown() -> None:
    bn = _brown_noise(1024, "cpu", torch.float32)
    assert torch.isfinite(bn).all()


def test_noise_grain_jitter_varies() -> None:
    variant = DDSPVariant(noise_grain_jitter=2.0)
    synth = FilteredNoiseSynth(variant=variant)
    mags = torch.rand(1, 32, 32)
    out1 = synth(mags, n_samples=1024)
    out2 = synth(mags, n_samples=1024)
    assert not torch.allclose(out1, out2)


def test_engine_harmonic_default() -> None:
    cfg = DDSPConfig(hidden_size=64)
    model = DDSPModel(cfg, variant=DDSPVariant(engine="harmonic"))
    f0 = torch.rand(1, 32) * 300 + 100
    loudness = torch.randn(1, 32)
    out = model(f0, loudness)
    loss = out["audio"].square().mean()
    loss.backward()
    assert torch.isfinite(out["audio"]).all()
    assert all(p.grad is not None for p in model.gru.parameters())


def test_engine_sinusoidal_forward() -> None:
    cfg = DDSPConfig(hidden_size=64)
    model = DDSPModel(cfg, variant=DDSPVariant(engine="sinusoidal"))
    f0 = torch.rand(1, 32) * 300 + 100
    loudness = torch.randn(1, 32)
    out = model(f0, loudness)
    loss = out["audio"].square().mean()
    loss.backward()
    assert "sinusoidal_freqs" in out
    assert torch.isfinite(out["audio"]).all()


def test_engine_combsub_forward() -> None:
    cfg = DDSPConfig(hidden_size=64)
    model = DDSPModel(cfg, variant=DDSPVariant(engine="combsub"))
    f0 = torch.rand(1, 32) * 300 + 100
    loudness = torch.randn(1, 32)
    out = model(f0, loudness)
    loss = out["audio"].square().mean()
    loss.backward()
    assert "voiced" in out
    assert torch.isfinite(out["audio"]).all()


def test_engine_checkpoint_tag() -> None:
    cfg = DDSPConfig(hidden_size=64)
    model = DDSPModel(cfg, variant=DDSPVariant(engine="sinusoidal"))
    with tempfile.NamedTemporaryFile(suffix=".pt", delete=False) as f:
        path = f.name
    try:
        model.save_checkpoint(path)
        loaded = DDSPModel.load_checkpoint(path)
        assert loaded.variant.engine == "sinusoidal"
    finally:
        if os.path.exists(path):
            os.remove(path)


def test_engine_mismatch_raises() -> None:
    cfg = DDSPConfig(hidden_size=64)
    model = DDSPModel(cfg, variant=DDSPVariant(engine="sinusoidal"))
    with tempfile.NamedTemporaryFile(suffix=".pt", delete=False) as f:
        path = f.name
    try:
        model.save_checkpoint(path)
        with pytest.raises(ValueError, match="engine"):
            DDSPModel.load_checkpoint(path, variant=DDSPVariant(engine="harmonic"))
    finally:
        if os.path.exists(path):
            os.remove(path)
