"""Tests for MidiSynthWrapper in inference/midi_synth_wrapper.py."""

import torch

from inference.midi_synth_wrapper import MidiSynthWrapper
from model import DDSPConfig, DDSPModel
from model.polyddsp_model import PolyDDSPModel


def _make_model() -> DDSPModel:
    config = DDSPConfig(hidden_size=32, n_harmonics=20)
    model = DDSPModel(config)
    model.eval()
    return model


def _f0() -> torch.Tensor:
    return torch.full((10,), 220.0)


def _loudness() -> torch.Tensor:
    return torch.full((10,), -20.0)


# ---------------------------------------------------------------------------
# Mono forward shape / tensor / VAE path
# ---------------------------------------------------------------------------


def test_mono_forward_shape() -> None:
    model = _make_model()
    wrapper = MidiSynthWrapper(model)
    audio = wrapper(_f0(), _loudness())
    assert audio.dim() == 1
    assert audio.numel() > 0


def test_forward_returns_audio_tensor() -> None:
    model = _make_model()
    wrapper = MidiSynthWrapper(model)
    audio = wrapper(_f0(), _loudness())
    assert isinstance(audio, torch.Tensor)
    assert audio.isfinite().all()
    assert audio.numel() > 0


def test_mono_vae_path() -> None:
    config = DDSPConfig(hidden_size=32, n_harmonics=20, use_latent=True, latent_dim=8)
    model = DDSPModel(config)
    model.eval()
    wrapper = MidiSynthWrapper(model)
    audio = wrapper(_f0(), _loudness())
    assert audio.dim() == 1
    assert audio.numel() > 0
    assert audio.isfinite().all()


# ---------------------------------------------------------------------------
# Polyphonic forward
# ---------------------------------------------------------------------------


def test_poly_forward_shape() -> None:
    config = DDSPConfig(hidden_size=32, n_harmonics=20)
    poly = PolyDDSPModel(config, n_voices=2)
    poly.eval()
    wrapper = MidiSynthWrapper(poly)
    f0_voices = torch.full((2, 10), 220.0)
    loudness = torch.full((10,), -20.0)
    audio = wrapper(f0_voices, loudness)
    assert audio.dim() == 1
    assert audio.numel() > 0
    assert torch.isfinite(audio).all()


# ---------------------------------------------------------------------------
# TorchScript
# ---------------------------------------------------------------------------


def test_torchscript_trace() -> None:
    model = _make_model()
    wrapper = MidiSynthWrapper(model)
    f0 = _f0()
    loudness = _loudness()
    traced = torch.jit.trace(wrapper, (f0, loudness))
    assert hasattr(traced, "forward")
    out = traced(f0, loudness)
    assert isinstance(out, torch.Tensor)
    assert out.numel() > 0
    assert torch.isfinite(out).all()
