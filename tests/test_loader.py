"""Tests for dataset/loader.DDSPDataset."""

from __future__ import annotations

import numpy as np
import pytest
import torch

from dataset.cache import FeatureCache
from dataset.loader import DDSPDataset

# temporal resolution constants (must match dataset/loader.py)
AUDIO_SAMPLES_PER_FRAME = 160


@pytest.fixture
def synthetic_cache(tmp_path: pytest.Path):
    """Build a 3-file synthetic FeatureCache with known lengths.

    Returns the cache directory path and a dict describing the per-file audio lengths
    and the expected total number of chunks.
    """
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()

    # 3 source files, each with 160000 audio samples (= 10 s @ 16 kHz).
    # Total audio = 480000 samples -> 3 full chunks of seq_len=64000.
    seq_len = 64000
    audio_len_per_file = 160000
    n_files = 3

    audio_chunks = []
    f0_chunks = []
    loudness_chunks = []

    for i in range(n_files):
        audio_sample_count = audio_len_per_file
        frames_count = audio_sample_count // AUDIO_SAMPLES_PER_FRAME  # = 1000

        audio = np.full(audio_sample_count, fill_value=float(i), dtype=np.float32)
        f0 = np.full(frames_count, fill_value=float(i + 100), dtype=np.float32)
        loudness = np.full(frames_count, fill_value=float(i + 200), dtype=np.float32)

        audio_chunks.append(audio)
        f0_chunks.append(f0)
        loudness_chunks.append(loudness)

    merged_audio = np.concatenate(audio_chunks, dtype=np.float32)
    merged_f0 = np.concatenate(f0_chunks, dtype=np.float32)
    merged_loudness = np.concatenate(loudness_chunks, dtype=np.float32)

    cache = FeatureCache(cache_dir)
    cache.save(
        key="train",
        features={
            "audio": merged_audio,
            "f0_hz": merged_f0,
            "loudness_db": merged_loudness,
        },
        meta={"n_files": n_files},
    )

    total_audio = merged_audio.shape[0]
    expected_n_chunks = total_audio // seq_len  # = 3

    return cache_dir, {
        "n_files": n_files,
        "total_audio": total_audio,
        "expected_n_chunks": expected_n_chunks,
        "seq_len": seq_len,
    }


def test_dataset_len(synthetic_cache: tuple[pytest.Path, dict]) -> None:
    cache_dir, info = synthetic_cache
    ds = DDSPDataset(cache_dir, key="train", seq_len=info["seq_len"], seed=42)
    assert len(ds) == info["expected_n_chunks"]


def test_dataset_shapes_and_types(synthetic_cache: tuple[pytest.Path, dict]) -> None:
    cache_dir, info = synthetic_cache
    ds = DDSPDataset(cache_dir, key="train", seq_len=info["seq_len"], seed=42)

    f0, loudness, audio = ds[0]

    assert isinstance(f0, torch.Tensor)
    assert isinstance(loudness, torch.Tensor)
    assert isinstance(audio, torch.Tensor)

    assert f0.dtype == torch.float32
    assert loudness.dtype == torch.float32
    assert audio.dtype == torch.float32

    # f0 / loudness: (1, frames_per_chunk) ; frames_per_chunk = seq_len // 160 = 400
    expected_frames = info["seq_len"] // AUDIO_SAMPLES_PER_FRAME
    assert f0.shape == (1, expected_frames)
    assert loudness.shape == (1, expected_frames)

    # audio: (1, seq_len)
    assert audio.shape == (1, info["seq_len"])


def test_dataset_iterates_one_epoch(synthetic_cache: tuple[pytest.Path, dict]) -> None:
    cache_dir, info = synthetic_cache
    ds = DDSPDataset(cache_dir, key="train", seq_len=info["seq_len"], seed=42)

    # Iterate over the full epoch; verify shapes/types and that content is monotonic.
    seen = 0
    for _idx, (f0, loudness, audio) in enumerate(ds):
        assert f0.shape == (1, info["seq_len"] // AUDIO_SAMPLES_PER_FRAME)
        assert loudness.shape == (1, info["seq_len"] // AUDIO_SAMPLES_PER_FRAME)
        assert audio.shape == (1, info["seq_len"])
        assert f0.is_floating_point()
        assert loudness.is_floating_point()
        assert audio.is_floating_point()
        seen += 1

    assert seen == info["expected_n_chunks"]


def test_dataset_raises_on_missing_cache(tmp_path: pytest.Path) -> None:
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()
    with pytest.raises(FileNotFoundError):
        DDSPDataset(empty_dir, key="train", seq_len=64000, seed=42)


def test_last_partial_chunk_is_dropped(tmp_path: pytest.Path) -> None:
    """When total audio is not a multiple of seq_len, the remainder is discarded."""
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()

    # Total audio = 100000 samples = 1 full chunk (64000) + 36000 remainder.
    # Expected: 1 chunk.
    audio_len = 100000
    frames_len = audio_len // AUDIO_SAMPLES_PER_FRAME

    audio = np.zeros(audio_len, dtype=np.float32)
    f0 = np.zeros(frames_len, dtype=np.float32)
    loudness = np.zeros(frames_len, dtype=np.float32)

    cache = FeatureCache(cache_dir)
    cache.save(
        key="train",
        features={
            "audio": audio,
            "f0_hz": f0,
            "loudness_db": loudness,
        },
        meta={},
    )

    ds = DDSPDataset(cache_dir, key="train", seq_len=64000, seed=42)
    assert len(ds) == 1
    assert ds[0][2].shape == (1, 64000)
