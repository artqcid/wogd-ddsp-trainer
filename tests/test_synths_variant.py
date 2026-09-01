import os
import tempfile

import torch

from model.ddsp import DDSPVariant
from model.ddsp.synths import HarmonicOscillatorSynth
from model.ddsp_model import DDSPConfig, DDSPModel
from model.losses import MultiScaleSpectralLoss


def _make_f0(B=1, T=32):
    return torch.rand(B, T) * 300 + 100


def _make_loudness(B=1, T=32):
    return torch.randn(B, T)


def test_variant_default_is_noop() -> None:
    v = DDSPVariant()
    assert v.is_default()
    model = DDSPModel(DDSPConfig(hidden_size=64))
    f0 = _make_f0()
    loudness = _make_loudness()
    out = model(f0, loudness)
    assert torch.isfinite(out["audio"]).all()


def test_inharmonic_ratios() -> None:
    v = DDSPVariant(harmonic_ratios=[1.0, 1.414, 2.73, 3.14])
    synth = HarmonicOscillatorSynth(n_harmonics=8, variant=v)
    amps = torch.rand(1, 32, 8)
    dist = torch.rand(1, 32, 8)
    f0 = torch.full((1, 32), 220.0)
    out = synth(amps, dist, f0, sample_rate=16000, hop_length=128)
    assert torch.isfinite(out).all()


def test_fm_synthesis() -> None:
    v = DDSPVariant(fm_depth=0.5, fm_ratio=2.0)
    synth = HarmonicOscillatorSynth(n_harmonics=16, variant=v)
    amps = torch.rand(1, 32, 16)
    dist = torch.rand(1, 32, 16)
    f0 = torch.full((1, 32), 220.0)
    out = synth(amps, dist, f0, sample_rate=16000, hop_length=128)
    assert torch.isfinite(out).all()


def test_fm_zero_depth_noop() -> None:
    v_default = DDSPVariant()
    v_fm_zero = DDSPVariant(fm_depth=0.0, fm_ratio=2.0)
    synth_default = HarmonicOscillatorSynth(n_harmonics=8, variant=v_default)
    synth_fm = HarmonicOscillatorSynth(n_harmonics=8, variant=v_fm_zero)
    amps = torch.rand(1, 16, 8)
    dist = torch.rand(1, 16, 8)
    f0 = torch.full((1, 16), 220.0)
    out_default = synth_default(amps, dist, f0, sample_rate=16000, hop_length=128)
    out_fm = synth_fm(amps, dist, f0, sample_rate=16000, hop_length=128)
    assert torch.allclose(out_default, out_fm)


def test_waveform_square() -> None:
    v = DDSPVariant(waveform="square")
    model = DDSPModel(DDSPConfig(hidden_size=64), variant=v)
    f0 = _make_f0()
    loudness = _make_loudness()
    out = model(f0, loudness)
    assert torch.isfinite(out["audio"]).all()


def test_waveform_saw() -> None:
    v = DDSPVariant(waveform="saw")
    model = DDSPModel(DDSPConfig(hidden_size=64), variant=v)
    f0 = _make_f0()
    loudness = _make_loudness()
    out = model(f0, loudness)
    assert torch.isfinite(out["audio"]).all()


def test_phase_distortion() -> None:
    v = DDSPVariant(pd_k=0.8)
    synth = HarmonicOscillatorSynth(n_harmonics=8, variant=v)
    amps = torch.rand(1, 32, 8)
    dist = torch.rand(1, 32, 8)
    f0 = torch.full((1, 32), 220.0)
    out = synth(amps, dist, f0, sample_rate=16000, hop_length=128)
    assert torch.isfinite(out).all()


def test_trainable_wavetable_gradients() -> None:
    v = DDSPVariant(use_trainable_wavetable=True)
    model = DDSPModel(DDSPConfig(hidden_size=64), variant=v)
    f0 = _make_f0()
    loudness = _make_loudness()
    out = model(f0, loudness)
    loss = out["audio"].square().mean()
    loss.backward()
    assert torch.isfinite(out["audio"]).all()


def test_trainable_wavetable_checkpoint_tag() -> None:
    v = DDSPVariant(use_trainable_wavetable=True)
    model = DDSPModel(DDSPConfig(hidden_size=64), variant=v)
    with tempfile.NamedTemporaryFile(suffix=".pt", delete=False) as f:
        path = f.name
    try:
        model.save_checkpoint(path)
        loaded = DDSPModel.load_checkpoint(path, variant=v)
        assert loaded.variant.engine == "harmonic"
        assert loaded.variant.use_trainable_wavetable
    finally:
        if os.path.exists(path):
            os.remove(path)


def test_loss_band_mask() -> None:
    loss_masked = MultiScaleSpectralLoss(
        fft_sizes=[512], band_mask=[(200.0, 2000.0)], sample_rate=16000
    )
    loss_unmasked = MultiScaleSpectralLoss(fft_sizes=[512], sample_rate=16000)
    pred = torch.randn(1, 16000)
    tgt = torch.randn(1, 16000)
    val_masked = loss_masked(pred, tgt)
    val_unmasked = loss_unmasked(pred, tgt)
    assert torch.isfinite(val_masked) and val_masked > 0
    assert val_masked < val_unmasked


def test_loss_band_mask_zero_band() -> None:
    loss = MultiScaleSpectralLoss(fft_sizes=[512], band_mask=[(0.0, 8000.0)], sample_rate=16000)
    pred = torch.randn(1, 16000)
    tgt = torch.randn(1, 16000)
    val = loss(pred, tgt)
    assert torch.isfinite(val) and val == 0.0


def test_lfo_injection() -> None:
    v = DDSPVariant(lfo_freq=8.0, lfo_depth=0.5)
    model = DDSPModel(DDSPConfig(hidden_size=64), variant=v)
    f0 = _make_f0()
    loudness = _make_loudness()
    out = model(f0, loudness)
    assert torch.isfinite(out["audio"]).all()


def test_lfo_zero_noop() -> None:
    model = DDSPModel(DDSPConfig(hidden_size=64))
    f0 = _make_f0()
    loudness = _make_loudness()
    out_default = model(f0, loudness)
    model.variant.lfo_freq = 0.0
    model.variant.lfo_depth = 0.0
    out_zero = model(f0, loudness)
    assert torch.allclose(out_zero["audio"], out_default["audio"])
    assert torch.isfinite(out_zero["audio"]).all()


def test_angular_cumsum() -> None:
    v = DDSPVariant(use_angular_cumsum=True)
    synth = HarmonicOscillatorSynth(n_harmonics=8, variant=v)
    amps = torch.rand(1, 32, 8)
    dist = torch.rand(1, 32, 8)
    f0 = torch.full((1, 32), 220.0)
    out = synth(amps, dist, f0, sample_rate=16000, hop_length=128)
    assert torch.isfinite(out).all()


def test_variant_from_dict_roundtrip() -> None:
    d = {
        "waveform": "square",
        "fm_depth": 0.5,
        "fm_ratio": 3.0,
        "harmonic_ratios": [1.0, 1.414],
    }
    v = DDSPVariant.from_dict(d)
    assert v.waveform == "square"
    assert v.fm_depth == 0.5
    assert v.fm_ratio == 3.0
    assert v.harmonic_ratios == [1.0, 1.414]
    assert not v.is_default()
