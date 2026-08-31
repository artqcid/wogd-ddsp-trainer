"""Unit tests for dataset.io — audio ingestion, resampling, normalization."""

from __future__ import annotations

import numpy as np
import pytest
import soundfile

from dataset.io import load_audio, normalize_level, process_audio_file, resample_audio, to_mono

# ---------------------------------------------------------------------------
# to_mono
# ---------------------------------------------------------------------------


def test_to_mono_stereo_means_channels() -> None:
    stereo = np.array([[0.2, 0.4], [0.6, 0.8], [1.0, 0.0]], dtype=np.float32)  # (3, 2)
    mono = to_mono(stereo)
    expected = np.array([0.3, 0.7, 0.5], dtype=np.float32)
    np.testing.assert_allclose(mono, expected, rtol=0, atol=1e-7)
    assert mono.ndim == 1
    assert mono.dtype == np.float32


def test_to_mono_mono_passthrough() -> None:
    mono_in = np.array([0.1, 0.2, 0.3], dtype=np.float32)
    mono_out = to_mono(mono_in)
    np.testing.assert_allclose(mono_out, mono_in, rtol=0, atol=0)
    assert mono_out.ndim == 1
    assert mono_out.dtype == np.float32


def test_to_mono_ndim_gt_2_raises() -> None:
    bad = np.zeros((2, 3, 4), dtype=np.float32)
    with pytest.raises(ValueError, match="ndim"):
        to_mono(bad)


# ---------------------------------------------------------------------------
# resample_audio
# ---------------------------------------------------------------------------


def _sine(orig_sr: int, freq: float = 440.0, dur: float = 0.1) -> np.ndarray:
    t = np.arange(int(orig_sr * dur), dtype=np.float32) / orig_sr
    return (np.sin(2.0 * np.pi * freq * t)).astype(np.float32)


def test_resample_audio_upsample_length_grows() -> None:
    audio = _sine(orig_sr=8000, freq=440.0, dur=0.2)
    up = resample_audio(audio, orig_sr=8000, target_sr=16000)
    assert up.dtype == np.float32
    assert up.ndim == 1
    ratio = len(up) / len(audio)
    assert 1.9 < ratio < 2.1, f"expected ~2x length growth, got {ratio:.3f}"


def test_resample_audio_equal_sr_returns_same() -> None:
    audio = _sine(orig_sr=16000, freq=440.0, dur=0.1)
    out = resample_audio(audio, orig_sr=16000, target_sr=16000)
    np.testing.assert_array_equal(out, audio)
    assert out.dtype == np.float32


def test_resample_audio_float32_dtype() -> None:
    audio = _sine(orig_sr=22050, freq=880.0, dur=0.05)
    up = resample_audio(audio, orig_sr=22050, target_sr=16000)
    assert up.dtype == np.float32


# ---------------------------------------------------------------------------
# normalize_level
# ---------------------------------------------------------------------------


def test_normalize_level_peak_099() -> None:
    audio = np.array([-0.4, 0.2, 0.8, -0.5], dtype=np.float32)
    out = normalize_level(audio, peak=0.99)
    assert np.isclose(np.max(np.abs(out)), 0.99, rtol=1e-7)
    assert out.dtype == np.float32


def test_normalize_level_silence_unchanged() -> None:
    audio = np.zeros(5, dtype=np.float32)
    out = normalize_level(audio, peak=0.99)
    np.testing.assert_array_equal(out, audio)
    assert out.dtype == np.float32


def test_normalize_level_float32_dtype_preserved() -> None:
    audio = np.array([0.1, -0.3], dtype=np.float32)
    out = normalize_level(audio, peak=0.99)
    assert out.dtype == np.float32


# ---------------------------------------------------------------------------
# load_audio + process_audio_file (file-based fixture in tmp_path)
# ---------------------------------------------------------------------------


@pytest.fixture
def fixture_wav(tmp_path) -> str:
    path = tmp_path / "fixture.wav"
    sr = 44100
    dur = 1.0
    t = np.arange(int(sr * dur), dtype=np.float32) / sr
    # stereo 440 Hz tone
    tone = np.sin(2.0 * np.pi * 440.0 * t).astype(np.float32)
    stereo = np.stack([tone, tone * 0.5], axis=1)  # (N, 2)
    soundfile.write(str(path), stereo, sr, subtype="PCM_16")
    return str(path)


def test_load_audio_returns_1d_float32_with_sample_rate(fixture_wav: str) -> None:
    audio, sr = load_audio(fixture_wav, target_sample_rate=16000)
    assert sr == 16000
    assert audio.ndim == 1
    assert audio.dtype == np.float32


def test_process_audio_file_16k_mono_normalized(fixture_wav: str) -> None:
    audio = process_audio_file(fixture_wav)
    assert audio.ndim == 1
    assert audio.dtype == np.float32
    approx_len = int(16000 * 1.0)
    assert abs(len(audio) - approx_len) <= 128, f"unexpected length {len(audio)}"
    assert np.max(np.abs(audio)) <= 0.99 + 1e-6, f"peak exceeds 0.99: {np.max(np.abs(audio))}"
