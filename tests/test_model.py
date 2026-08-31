"""Unit tests for model — DDSPModel forward contracts, determinism, config knobs.
CPU only, fixed seed."""

from __future__ import annotations

import os

import numpy as np
import pytest
import soundfile as sf
import torch

from model import DDSPConfig, DDSPModel
from model.ddsp.synths import SimpleReverb
from model.reverb_injection import extract_ir, inject_ir


def test_forward_returns_keys_and_shapes() -> None:
    torch.manual_seed(0)
    model = DDSPModel(DDSPConfig())
    f0 = torch.full((2, 16), 220.0)
    loudness = torch.rand(2, 16).log()
    out = model(f0, loudness)

    assert set(out.keys()) == {"amplitudes", "harmonic_distribution", "magnitudes", "audio"}

    assert out["amplitudes"].shape == (2, 16, 60)
    assert out["harmonic_distribution"].shape == (2, 16, 60)
    assert out["magnitudes"].shape == (2, 16, 32)
    assert out["audio"].shape == (2, 1921)  # (T-1)*frame_size + 1

    for name, tensor in out.items():
        assert torch.isfinite(tensor).all(), f"{name} not all finite"


def test_harmonic_distribution_softmaxes_to_one() -> None:
    torch.manual_seed(0)
    model = DDSPModel(DDSPConfig())
    f0 = torch.full((2, 8), 220.0)
    loudness = torch.rand(2, 8).log()
    out = model(f0, loudness)

    row_sums = out["harmonic_distribution"].sum(dim=-1)
    expected = torch.ones_like(row_sums)
    torch.testing.assert_allclose(row_sums, expected, atol=1e-5, rtol=1e-7)


def test_deterministic_forward() -> None:
    torch.manual_seed(0)
    model = DDSPModel(DDSPConfig())
    f0 = torch.full((1, 12), 220.0)
    loudness = torch.rand(1, 12).log()
    out_a = model(f0, loudness)

    torch.manual_seed(0)
    model2 = DDSPModel(DDSPConfig())
    out_b = model2(f0, loudness)

    assert torch.equal(out_a["audio"], out_b["audio"]), "audio not bitwise identical across runs"


def test_custom_config() -> None:
    torch.manual_seed(0)
    model = DDSPModel(DDSPConfig(n_harmonics=100, hidden_size=128))
    f0 = torch.full((1, 8), 220.0)
    loudness = torch.rand(1, 8).log()
    out = model(f0, loudness)

    assert out["amplitudes"].shape[-1] == 100
    assert out["harmonic_distribution"].shape[-1] == 100
    assert torch.isfinite(out["audio"]).all()


def test_forward_cpu_no_gpu_hardcode() -> None:
    torch.manual_seed(0)
    model = DDSPModel(DDSPConfig())
    f0 = torch.full((1, 8), 220.0)
    loudness = torch.rand(1, 8).log()
    out = model(f0, loudness)

    audio = out["audio"]
    assert audio.device.type == "cpu"
    assert torch.isfinite(audio).all()


# ---------------------------------------------------------------------------
# Reverb IR injection / extraction tests (Option B — fixed kernel swap)
# ---------------------------------------------------------------------------


def test_inject_ir_replaces_kernel(tmp_path: pytest.TempPath) -> None:
    """inject_ir loads a .wav IR and replaces the kernel buffer."""
    reverb = SimpleReverb()
    original = reverb.kernel.clone()

    # Generate a synthetic IR (short impulse)
    ir = np.zeros(500, dtype=np.float32)
    ir[0] = 1.0
    ir_path = str(tmp_path / "ir.wav")
    sf.write(ir_path, ir, 16000)

    inject_ir(reverb, ir_path, sample_rate=16000)
    assert reverb.kernel.shape == original.shape
    assert not torch.equal(reverb.kernel, original)
    assert reverb.kernel[0] == pytest.approx(1.0, abs=1e-6)


def test_inject_ir_resamples(tmp_path: pytest.TempPath) -> None:
    """inject_ir resamples IR from 48kHz to 16kHz."""
    reverb = SimpleReverb()
    ir = np.zeros(4800, dtype=np.float32)
    ir[0] = 1.0
    ir_path = str(tmp_path / "ir48k.wav")
    sf.write(ir_path, ir, 48000)

    inject_ir(reverb, ir_path, sample_rate=16000)
    assert reverb.kernel.isfinite().all()


def test_inject_ir_mono_conversion(tmp_path: pytest.TempPath) -> None:
    """inject_ir converts stereo IR to mono."""
    reverb = SimpleReverb()
    ir = np.zeros((100, 2), dtype=np.float32)
    ir[0, :] = 1.0
    ir_path = str(tmp_path / "ir_stereo.wav")
    sf.write(ir_path, ir, 16000)

    inject_ir(reverb, ir_path, sample_rate=16000)
    assert reverb.kernel.isfinite().all()


def test_inject_ir_file_not_found() -> None:
    """inject_ir raises FileNotFoundError for missing path."""
    reverb = SimpleReverb()
    with pytest.raises(FileNotFoundError):
        inject_ir(reverb, "/nonexistent/ir.wav")


def test_extract_ir_writes_wav(tmp_path: pytest.TempPath) -> None:
    """extract_ir saves kernel buffer as .wav."""
    reverb = SimpleReverb()
    out_path = str(tmp_path / "extracted.wav")
    result = extract_ir(reverb, out_path, sample_rate=16000)

    assert result == os.path.abspath(out_path)
    assert os.path.exists(out_path)
    assert os.path.getsize(out_path) > 0

    # Verify it's a valid .wav
    loaded, sr = sf.read(out_path)
    assert sr == 16000
    assert len(loaded) == reverb.kernel.shape[0]


def test_extract_ir_returns_path(tmp_path: pytest.TempPath) -> None:
    """extract_ir returns the absolute path."""
    reverb = SimpleReverb()
    result = extract_ir(reverb, str(tmp_path / "ir_out.wav"))
    assert isinstance(result, str)
    assert result.endswith("ir_out.wav")


def test_inject_then_extract_roundtrip(tmp_path: pytest.TempPath) -> None:
    """Inject an IR, extract it, compare (lossy via wav)."""
    reverb = SimpleReverb()
    ir = np.sin(2 * np.pi * 100 * np.arange(500) / 16000, dtype=np.float32)
    ir_path = str(tmp_path / "sine_ir.wav")
    sf.write(ir_path, ir, 16000)

    inject_ir(reverb, ir_path, sample_rate=16000)

    out_path = str(tmp_path / "roundtrip.wav")
    extract_ir(reverb, out_path, sample_rate=16000)

    loaded, _sr = sf.read(out_path)
    assert np.allclose(loaded, reverb.kernel.cpu().numpy(), atol=1e-6)
