"""Unit tests for dataset.cache — on-disk feature caching."""

from __future__ import annotations

import numpy as np
import pytest

from dataset.cache import FeatureCache, cached_feature_loader

# ---------------------------------------------------------------------------
# FeatureCache roundtrip (save / exists / load)
# ---------------------------------------------------------------------------


@pytest.fixture
def cache_dir(tmp_path: str):
    return str(tmp_path / "cache")


@pytest.fixture
def cache(cache_dir: str):
    return FeatureCache(cache_dir)


def _make_features() -> dict[str, np.ndarray]:
    return {
        "f0_hz": np.array([100.0, 120.0, 140.0], dtype=np.float32),
        "loudness_db": np.array([-20.0, -15.0, -10.0], dtype=np.float32),
    }


def _make_meta() -> dict[str, str]:
    return {"source": "synth", "duration_s": "3.0"}


def test_save_exists_load_roundtrip(cache: FeatureCache) -> None:
    key = "track_01"
    features = _make_features()
    meta = _make_meta()
    cache.save(key, features, meta)

    assert cache.exists(key)

    loaded_features, loaded_meta = cache.load(key)
    assert loaded_features is not None
    assert loaded_meta is not None
    for name, arr in features.items():
        assert np.allclose(loaded_features[name], arr, rtol=0, atol=1e-7)
    assert loaded_meta == meta


def test_load_missing_key_returns_none(cache: FeatureCache) -> None:
    features, meta = cache.load("no_such_key")
    assert features is None
    assert meta is None


def test_exists_false_for_missing_key(cache: FeatureCache) -> None:
    assert not cache.exists("no_such_key")


# ---------------------------------------------------------------------------
# cached_feature_loader
# ---------------------------------------------------------------------------


def test_cached_feature_loader_miss_then_hit_no_recompute(
    cache: FeatureCache,
) -> None:
    key = "track_02"
    call_count = 0

    def compute_fn() -> dict[str, np.ndarray]:
        nonlocal call_count
        call_count += 1
        return _make_features()

    first = cached_feature_loader(cache, key, compute_fn, meta=_make_meta())
    assert call_count == 1
    assert np.allclose(first["f0_hz"], _make_features()["f0_hz"])

    second = cached_feature_loader(cache, key, compute_fn, meta=_make_meta())
    assert call_count == 1  # compute_fn not called again
    assert first is not second
    assert np.allclose(second["f0_hz"], _make_features()["f0_hz"])


def test_cached_feature_loader_cache_hit_returns_same_values(
    cache: FeatureCache,
) -> None:
    key = "track_03"
    features = _make_features()
    cached_feature_loader(cache, key, lambda: features, meta=_make_meta())
    loaded, _ = cache.load(key)
    assert loaded is not None
    for name, arr in features.items():
        assert np.allclose(loaded[name], arr, rtol=0, atol=1e-7)


# ---------------------------------------------------------------------------
# clear
# ---------------------------------------------------------------------------


def test_clear_removes_cached_files(cache: FeatureCache) -> None:
    key = "track_04"
    cache.save(key, _make_features(), _make_meta())
    assert cache.exists(key)

    cache.clear()
    assert not cache.exists(key)
    features, meta = cache.load(key)
    assert features is None
    assert meta is None


def test_clear_does_not_delete_cache_directory(cache: FeatureCache) -> None:
    cache.cache_dir.mkdir(parents=True, exist_ok=True)
    cache.save("track_05", _make_features(), _make_meta())
    cache.clear()
    assert cache.cache_dir.exists()
    assert cache.cache_dir.is_dir()
