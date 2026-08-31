"""Audio ingestion, resampling, and peak-level normalization."""

from __future__ import annotations

import librosa
import numpy as np
import soundfile


def load_audio(path: str, target_sample_rate: int = 16000) -> tuple[np.ndarray, int]:
    """Load audio via soundfile; fall back to librosa on error.

    Returns (audio_1d_float32, sample_rate), resampled to target_sample_rate.
    Stereo is collapsed to mono via channel mean.
    """
    try:
        audio, sr = soundfile.read(path, dtype="float32")
    except Exception:
        audio, sr = librosa.load(path, sr=None, dtype=np.float32)

    audio = to_mono(audio)
    if sr != target_sample_rate:
        audio = resample_audio(audio, sr, target_sample_rate)
        sr = target_sample_rate
    return audio.astype(np.float32, copy=False), sr


def to_mono(audio: np.ndarray) -> np.ndarray:
    """Collapse to mono: 1-D passthrough, 2-D -> mean over channels, else error."""
    if audio.ndim == 1:
        return audio
    if audio.ndim == 2:
        return audio.mean(axis=1).astype(np.float32, copy=False)
    raise ValueError(f"audio.ndim={audio.ndim}; expected 1 or 2")


def resample_audio(audio: np.ndarray, orig_sr: int, target_sr: int = 16000) -> np.ndarray:
    """Resample to target_sr with kaiser_best. No-op if rates match."""
    if orig_sr == target_sr:
        return audio.astype(np.float32, copy=False)
    return librosa.resample(
        audio, orig_sr=orig_sr, target_sr=target_sr, res_type="kaiser_best"
    ).astype(np.float32, copy=False)


def normalize_level(audio: np.ndarray, peak: float = 0.99) -> np.ndarray:
    """Peak-normalize so max-abs == peak. Silence (max-abs==0) returned unchanged."""
    audio = audio.astype(np.float32, copy=False)
    max_abs = float(np.max(np.abs(audio)))
    if max_abs == 0.0:
        return audio
    gain = peak / max_abs
    return (audio * gain).astype(np.float32, copy=False)


def process_audio_file(path: str) -> np.ndarray:
    """Load -> 16 kHz mono -> normalize_level(0.99). Returns float32 array."""
    audio, _ = load_audio(path, target_sample_rate=16000)
    return normalize_level(audio, peak=0.99)
