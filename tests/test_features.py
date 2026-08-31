"""Tests for dataset.features — deterministic, offline, parselmouth-only (no CREPE/GPU/network)."""

from __future__ import annotations

import numpy as np
import pytest

from dataset import features, loader
from dataset.features import load_f0_override


def test_get_f0_extractor() -> None:
    crepe = features.get_f0_extractor("crepe")
    parselmouth = features.get_f0_extractor("parselmouth")
    assert callable(crepe)
    assert callable(parselmouth)

    with pytest.raises(ValueError, match="Unknown F0 extractor"):
        features.get_f0_extractor("no_such_backend")


def test_extract_f0_parselmouth_sine() -> None:
    sample_rate = 16000.0
    freq = 220.0
    duration = 1.0
    n = int(sample_rate * duration)
    t = np.arange(n) / sample_rate
    audio = (np.sin(2 * np.pi * freq * t)).astype(np.float32)

    f0_hz, f0_conf = features.extract_f0_parselmouth(audio, sample_rate)

    assert f0_hz.dtype == np.float32
    assert f0_conf.dtype == np.float32
    assert f0_hz.ndim == 1
    assert f0_conf.ndim == 1
    assert len(f0_hz) == len(f0_conf)

    voiced = f0_hz > 0.0
    assert np.any(voiced), "Expected some voiced frames in a sustained sine"
    voiced_mean = float(np.mean(f0_hz[voiced]))
    # Allow ~20% tolerance on F0 estimate of a clean synthetic sine.
    assert 0.8 * freq <= voiced_mean <= 1.2 * freq, voiced_mean
    assert np.all((f0_conf >= 0.0) & (f0_conf <= 1.0))


def test_extract_loudness_db_relative() -> None:
    sample_rate = 16000.0
    n = int(sample_rate * 0.5)
    louder = np.full(n, 0.5, dtype=np.float32)
    quieter = np.full(n, 0.05, dtype=np.float32)

    loud_db = features.extract_loudness_db(louder, sample_rate)
    quiet_db = features.extract_loudness_db(quieter, sample_rate)

    assert loud_db.dtype == np.float32
    assert loud_db.ndim == 1
    assert quiet_db.dtype == np.float32
    assert quiet_db.ndim == 1
    assert np.all(np.isfinite(loud_db))
    assert np.all(np.isfinite(quiet_db))
    # Absolute dB (ref=1.0, dBFS) keeps signals comparable across files.
    assert np.max(loud_db) > np.max(quiet_db)


def test_normalize_feature() -> None:
    x = np.array([-1.0, 0.0, 2.0, 5.0], dtype=np.float32)
    out = features.normalize_feature(x)
    assert out.dtype == np.float32
    assert np.all((out >= 0.0) & (out <= 1.0))
    assert np.isclose(out[0], 0.0)
    assert np.isclose(out[-1], 1.0)

    # Explicit lo/hi scale.
    out2 = features.normalize_feature(x, lo=-1.0, hi=5.0)
    assert np.isclose(out2[0], 0.0)
    assert np.isclose(out2[-1], 1.0)

    # Degenerate (lo == hi) -> zeros.
    out3 = features.normalize_feature(x, lo=3.0, hi=3.0)
    assert out3.dtype == np.float32
    assert np.all(out3 == 0.0)


def test_compute_features_keys_and_alignment() -> None:
    sample_rate = 16000.0
    freq = 220.0
    n = int(sample_rate * 1.0)
    t = np.arange(n) / sample_rate
    audio = (np.sin(2 * np.pi * freq * t)).astype(np.float32)

    feat = features.compute_features(audio, sample_rate, f0_extractor_name="parselmouth")

    assert set(feat.keys()) == {"f0_hz", "f0_confidence", "loudness_db"}
    for v in feat.values():
        assert v.dtype == np.float32
        assert v.ndim == 1
    lengths = [len(v) for v in feat.values()]
    assert lengths.count(lengths[0]) == len(lengths)

    assert np.all((feat["f0_hz"] >= 0.0) & (feat["f0_hz"] <= 1.0))
    assert np.all((feat["loudness_db"] >= 0.0) & (feat["loudness_db"] <= 1.0))
    assert np.all((feat["f0_confidence"] >= 0.0) & (feat["f0_confidence"] <= 1.0))


def test_save_and_load_roundtrip(tmp_path) -> None:
    sample_rate = 16000.0
    freq = 220.0
    n = int(sample_rate * 0.5)
    t = np.arange(n) / sample_rate
    audio = (np.sin(2 * np.pi * freq * t)).astype(np.float32)

    feat = features.compute_features(audio, sample_rate, f0_extractor_name="parselmouth")
    out_dir = str(tmp_path / "features_roundtrip")
    base_name = "sine220"
    paths = features.save_features(feat, out_dir, base_name)

    assert len(paths) == 3
    for key, p in zip(("f0_hz", "f0_confidence", "loudness_db"), paths, strict=True):
        assert p.endswith(f"{base_name}.{key}.npy")

    loaded = loader.load_features(out_dir, base_name)
    assert set(loaded.keys()) == set(feat.keys())
    for key in feat:
        assert np.allclose(loaded[key].astype(np.float32), feat[key].astype(np.float32))


def test_compute_features_with_f0_override() -> None:
    audio = np.sin(2 * np.pi * 440 * np.arange(16000) / 16000, dtype=np.float32)
    f0_override = np.full(100, 440.0, dtype=np.float32)
    feat = features.compute_features(audio, 16000, f0_override=f0_override)
    assert "f0_hz" in feat
    assert "f0_confidence" in feat
    assert "loudness_db" in feat
    assert len(feat["f0_hz"]) == len(feat["f0_confidence"]) == len(feat["loudness_db"])
    assert np.all(feat["f0_confidence"] == 1.0)
    assert np.all(feat["f0_hz"] >= 0.0)
    assert np.all(feat["f0_hz"] <= 1.0)


def test_compute_features_override_vs_extract() -> None:
    audio = np.sin(2 * np.pi * 440 * np.arange(16000) / 16000, dtype=np.float32)
    f0_override = np.full(100, 440.0, dtype=np.float32)
    features_ovr = features.compute_features(audio, 16000, f0_override=f0_override)
    features_ext = features.compute_features(audio, 16000, f0_extractor_name="parselmouth")
    assert features_ovr["f0_confidence"][0] == 1.0
    assert features_ext["f0_hz"].shape == features_ovr["f0_hz"].shape


def test_load_f0_override(tmp_path) -> None:
    base = str(tmp_path / "testfile")
    arr = np.array([220.0, 330.0, 440.0], dtype=np.float32)
    np.save(base + ".f0_override.npy", arr)
    loaded = load_f0_override(base)
    assert loaded is not None
    assert np.array_equal(loaded, arr)


def test_load_f0_override_missing(tmp_path) -> None:
    loaded = load_f0_override(str(tmp_path / "nonexistent"))
    assert loaded is None


def test_compute_features_f0_override_normalization() -> None:
    audio = np.zeros(16000, dtype=np.float32)
    f0_override = np.array([0.0, 220.0, 440.0], dtype=np.float32)
    feat = features.compute_features(audio, 16000, f0_override=f0_override)
    assert feat["f0_hz"][0] == 0.0  # 0 Hz -> 0 after min-max
    assert feat["f0_hz"][2] == 1.0  # max value -> 1
