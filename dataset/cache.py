"""On-disk feature caching for the dataset pipeline."""

from __future__ import annotations

import json
import os
from collections.abc import Callable
from pathlib import Path

import numpy as np

CacheItem = tuple[dict[str, np.ndarray], dict[str, str]]
"""Type alias only: (features, meta)."""


class FeatureCache:
    """On-disk cache for feature dicts and accompanying metadata."""

    def __init__(self, cache_dir: str | os.PathLike) -> None:
        self.cache_dir = Path(cache_dir)

    def _feature_files(self, key: str) -> list[Path]:
        return sorted(self.cache_dir.glob(f"{key}.*.npy"))

    def _meta_path(self, key: str) -> Path:
        return self.cache_dir / f"{key}.meta.json"

    def save(
        self,
        key: str,
        features: dict[str, np.ndarray],
        meta: dict | None = None,
    ) -> None:
        """Write features as .npy files and meta as JSON under cache_dir/{key}.*."""
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        for name, arr in features.items():
            path = self.cache_dir / f"{key}.{name}.npy"
            np.save(path, arr, allow_pickle=False)
        meta_path = self._meta_path(key)
        with meta_path.open("w", encoding="utf-8") as fh:
            json.dump(meta if meta is not None else {}, fh)

    def load(self, key: str) -> tuple[dict[str, np.ndarray] | None, dict | None]:
        """Return (features, meta) if cached, else (None, None)."""
        feature_files = self._feature_files(key)
        if not feature_files:
            return None, None
        features: dict[str, np.ndarray] = {}
        prefix = f"{key}."
        for path in feature_files:
            stem = path.stem
            name = stem[len(prefix) :] if stem.startswith(prefix) else stem
            features[name] = np.load(path, allow_pickle=False)
        meta_path = self._meta_path(key)
        meta: dict = {}
        if meta_path.exists():
            with meta_path.open("r", encoding="utf-8") as fh:
                meta = json.load(fh)
        return features, meta

    def exists(self, key: str) -> bool:
        """True if at least one feature .npy for the key exists."""
        return bool(self._feature_files(key))

    def clear(self) -> None:
        """Remove cached files managed by this cache, not the cache directory."""
        if not self.cache_dir.exists():
            return
        for path in self.cache_dir.glob("*"):
            if path.is_file() and (path.name.endswith(".npy") or path.name.endswith(".meta.json")):
                path.unlink()


def cached_feature_loader(
    cache: FeatureCache,
    key: str,
    compute_fn: Callable[[], dict[str, np.ndarray]],
    meta: dict | None = None,
) -> dict[str, np.ndarray]:
    """Return cached features if present, else compute, cache, and return them."""
    features, _ = cache.load(key)
    if features is not None:
        return features
    features = compute_fn()
    cache.save(key, features, meta)
    return features
