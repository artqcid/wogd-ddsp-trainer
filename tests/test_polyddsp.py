"""Tests for PolyDDSP (M12)."""

from __future__ import annotations

import numpy as np
import pytest
import torch

from dataset.cache import FeatureCache
from dataset.loader import DDSPDataset
from dataset.multi_pitch import extract_multi_pitch
from model.ddsp_model import DDSPConfig
from model.polyddsp_model import PolyDDSPModel
from server.presets import N_VOICES_MAX, N_VOICES_MIN, clamp_params
from train.gpu import ParameterBounds


def _audio_440_660(sample_rate: int = 16000, duration_sec: float = 2.0) -> np.ndarray:
    t = np.arange(int(sample_rate * duration_sec)) / sample_rate
    audio = np.sin(2 * np.pi * 440.0 * t) + np.sin(2 * np.pi * 660.0 * t)
    return audio.astype(np.float32)


def test_multi_pitch_shape() -> None:
    audio = _audio_440_660()
    hop_length = 256
    f0_tracks = extract_multi_pitch(audio, 16000, n_voices=2, hop_length=hop_length)
    T_frames = len(audio) // hop_length + 1
    assert f0_tracks.shape == (2, T_frames), f"expected (2, {T_frames}), got {f0_tracks.shape}"
    assert f0_tracks.dtype == np.float32


def test_multi_pitch_nonneg() -> None:
    audio = _audio_440_660()
    f0_tracks = extract_multi_pitch(audio, 16000, n_voices=2, hop_length=256)
    assert (f0_tracks >= 0.0).all()


def test_dataset_multi_voice_yields_correct_shape(tmp_path: pytest.TempPath) -> None:
    cache_dir = str(tmp_path)
    cache = FeatureCache(cache_dir)
    audio = _audio_440_660(sample_rate=16000, duration_sec=1.0)
    hop_length = 256
    sample_rate = 16000
    f0_voices_raw = extract_multi_pitch(audio, sample_rate, n_voices=2, hop_length=hop_length)
    T_frames = f0_voices_raw.shape[1]
    features: dict[str, np.ndarray] = {
        "audio": audio.astype(np.float32),
        "f0_hz": np.zeros(T_frames, dtype=np.float32),
        "f0_confidence": np.zeros(T_frames, dtype=np.float32),
        "loudness_db": np.zeros(T_frames, dtype=np.float32),
        "f0_hz_voices": f0_voices_raw.astype(np.float32),
    }
    meta = {"sample_rate": sample_rate, "hop_length": hop_length, "source_files": []}
    cache.save("train", features, meta)
    dataset = DDSPDataset(cache_dir, key="train", seq_len=16000, seed=42, n_voices=2)
    assert len(dataset) >= 1
    f0_voices_chunk, loudness_chunk, audio_chunk, _content = dataset[0]
    assert f0_voices_chunk.shape[0] == 2, f"expected 2 voices, got {f0_voices_chunk.shape[0]}"
    assert f0_voices_chunk.shape[0] == 2
    assert f0_voices_chunk.ndim == 2


def test_polyddsp_shared_forward() -> None:
    config = DDSPConfig(hidden_size=64, n_harmonics=30)
    model = PolyDDSPModel(config, n_voices=2)
    torch.manual_seed(0)
    f0_voices = torch.rand(1, 2, 16) * 400 + 50
    loudness = torch.rand(1, 16)
    out = model(f0_voices, loudness)
    T_frames = 16
    expected_audio_len = (T_frames - 1) * config.frame_size + 1
    assert out["audio"].shape == (1, expected_audio_len)
    assert torch.isfinite(out["audio"]).all()


def test_polyddsp_independent_forward() -> None:
    config = DDSPConfig(hidden_size=64, n_harmonics=30)
    model = PolyDDSPModel(config, n_voices=2, independent=True)
    torch.manual_seed(0)
    f0_voices = torch.rand(1, 2, 16) * 400 + 50
    loudness = torch.rand(1, 16)
    out = model(f0_voices, loudness)
    assert torch.isfinite(out["audio"]).all()


def test_polyddsp_backward() -> None:
    config = DDSPConfig(hidden_size=64, n_harmonics=30)
    model = PolyDDSPModel(config, n_voices=2)
    torch.manual_seed(0)
    f0_voices = torch.rand(1, 2, 16) * 400 + 50
    loudness = torch.rand(1, 16)
    out = model(f0_voices, loudness)
    loss = out["audio"].sum()
    loss.backward()
    # Check that model parameters received gradients
    has_grad = False
    for p in model.parameters():
        if p.grad is not None:
            has_grad = True
            assert not torch.isnan(p.grad).any()
    assert has_grad, "no model parameter received a gradient"


def test_polyddsp_checkpoint_tag(tmp_path: pytest.TempPath) -> None:
    config = DDSPConfig(hidden_size=64, n_harmonics=30)
    model = PolyDDSPModel(config, n_voices=2)
    checkpoint_path = str(tmp_path / "polyddsp.ckpt.pt")
    model.save_checkpoint(checkpoint_path)
    import torch.serialization as _ts

    with _ts.safe_globals([DDSPConfig]):
        state = torch.load(checkpoint_path, map_location="cpu", weights_only=True)
    assert state["n_voices"] == 2
    PolyDDSPModel.load_checkpoint(checkpoint_path, n_voices=2)


def test_polyddsp_mismatch_raises(tmp_path: pytest.TempPath) -> None:
    config = DDSPConfig(hidden_size=64, n_harmonics=30)
    model = PolyDDSPModel(config, n_voices=2)
    checkpoint_path = str(tmp_path / "polyddsp.ckpt.pt")
    model.save_checkpoint(checkpoint_path)
    with pytest.raises(ValueError, match="n_voices"):
        PolyDDSPModel.load_checkpoint(checkpoint_path, n_voices=1)


def test_n_voices_clamp() -> None:
    bounds = ParameterBounds(
        hidden_size_min=128,
        hidden_size_max=512,
        n_harmonics_min=20,
        n_harmonics_max=60,
        n_filter_banks_min=16,
        n_filter_banks_max=32,
        stft_scales_min=3,
        stft_scales_max=5,
        mixed_precision="required",
        gradient_checkpointing="enabled",
        batch_size_max=8,
    )
    result, flags = clamp_params({"n_voices": 0}, bounds)
    assert result["n_voices"] == N_VOICES_MIN
    assert "n_voices" in flags
    result2, flags2 = clamp_params({"n_voices": 5}, bounds)
    assert result2["n_voices"] == N_VOICES_MAX
    assert "n_voices" in flags2
    result3, flags3 = clamp_params({"n_voices": 2}, bounds)
    assert result3["n_voices"] == 2
    assert "n_voices" not in flags3  # unchanged
