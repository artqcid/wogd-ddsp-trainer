"""Feature extraction for DDSP training: F0, loudness, normalization, and .npy export.

F0 extraction uses parselmouth (CPU, offline) or torchcrepe (ML primary). Loudness uses a
librosa RMS-to-dB path. All returned arrays are plain 1-D float32 numpy.
"""

from __future__ import annotations

import logging
import os
from collections.abc import Callable

import librosa
import numpy as np
import parselmouth

from .multi_pitch import extract_multi_pitch

logger = logging.getLogger(__name__)

try:  # pragma: no cover - torchcrepe is optional at import time, used by the crepe path only
    import torchcrepe
except Exception:  # torch or torchcrepe not available
    torch = None
    torchcrepe = None


def extract_f0_parselmouth(
    audio: np.ndarray,
    sample_rate: float,
    time_step: float = 0.01,
    f0_min: float = 50.0,
    f0_max: float = 2000.0,
) -> tuple[np.ndarray, np.ndarray]:
    """Extract F0 and voicing strength with parselmouth (Praat) on CPU.

    Returns (f0_hz, f0_confidence) as 1-D float32 arrays. Unvoiced frames have
    f0_hz == 0.0 (kept as 0.0, never NaN). Confidence comes from the pitch strength.
    """
    sound = parselmouth.Sound(audio.astype(np.float64), sampling_frequency=sample_rate)
    pitch = sound.to_pitch(
        time_step=time_step,
        pitch_floor=f0_min,
        pitch_ceiling=f0_max,
    )
    selected = pitch.selected_array
    f0_hz = np.asarray(selected["frequency"], dtype=np.float32)
    strength = np.asarray(selected["strength"], dtype=np.float32)
    # selected_array["frequency"] uses 0.0 for unvoiced frames; keep as 0.0.
    return f0_hz, strength


def extract_f0_crepe(
    audio: np.ndarray,
    sample_rate: float,
    hop_length: int | None = None,
    fmin: float = 50.0,
    fmax: float = 2000.0,
    device: str = "cpu",
) -> tuple[np.ndarray, np.ndarray]:
    """Extract F0 and harmonicity-based confidence with torchcrepe.

    Unvoiced frames are NaN in the raw prediction and are mapped to 0.0 here.
    Raises RuntimeError if the CREPE model/weights cannot be loaded.
    """
    if torchcrepe is None or torch is None:
        raise RuntimeError(
            "torchcrepe (and torch) are required for the CREPE backend. "
            "Use the parselmouth backend instead, or install torch + torchcrepe."
        )
    try:
        (f0, harmonicity), _period = torchcrepe.predict(
            torch.from_numpy(audio).unsqueeze(0).float(),
            sample_rate,
            hop_length=hop_length,
            fmin=fmin,
            fmax=fmax,
            model="full",
            device=device,
            batch_size=512,
            return_harmonicity=True,
            pad=True,
        )
    except Exception as exc:
        raise RuntimeError(
            "CREPE model could not be loaded/run: "
            f"{type(exc).__name__}: {exc}. "
            "Use the parselmouth backend instead, or check network/weight availability."
        ) from exc

    f0_np = f0.squeeze(0).detach().cpu().numpy().astype(np.float32)
    harm_np = harmonicity.squeeze(0).detach().cpu().numpy().astype(np.float32)
    f0_np = np.nan_to_num(f0_np, nan=0.0, posinf=0.0, neginf=0.0)
    harm_np = np.nan_to_num(harm_np, nan=0.0, posinf=1.0, neginf=0.0)
    harm_np = np.clip(harm_np, 0.0, 1.0)
    return f0_np, harm_np


def get_f0_extractor(name: str = "crepe") -> Callable[..., tuple[np.ndarray, np.ndarray]]:
    """Strategy factory: returns the named F0 extractor callable."""
    extractors: dict[str, Callable[..., tuple[np.ndarray, np.ndarray]]] = {
        "crepe": extract_f0_crepe,
        "parselmouth": extract_f0_parselmouth,
    }
    try:
        return extractors[name]
    except KeyError:
        raise ValueError(
            f"Unknown F0 extractor '{name}'. Choose one of: {sorted(extractors)}"
        ) from None


def extract_loudness_db(
    audio: np.ndarray,
    sample_rate: float,
    hop_length: int = 256,
    n_fft: int = 2048,
) -> np.ndarray:
    """A-weighted-style loudness in dB via librosa RMS -> amplitude_to_db.

    Returns a 1-D float32 array of per-frame dB values.
    """
    rms = librosa.feature.rms(y=audio, frame_length=n_fft, hop_length=hop_length)
    db = librosa.amplitude_to_db(rms, ref=1.0)
    return db.astype(np.float32).ravel()


def normalize_feature(
    values: np.ndarray,
    lo: float | None = None,
    hi: float | None = None,
) -> np.ndarray:
    """Min-max normalize to [0,1] using lo/hi as scale bounds (default: min/max of values).

    If lo == hi the output is all zeros. Output is clipped to [0,1].
    """
    arr = np.asarray(values, dtype=np.float32)
    lo_val = float(np.min(arr)) if lo is None else float(lo)
    hi_val = float(np.max(arr)) if hi is None else float(hi)
    if hi_val == lo_val:
        return np.zeros_like(arr, dtype=np.float32)
    scaled = (arr - lo_val) / (hi_val - lo_val)
    return np.clip(scaled, 0.0, 1.0).astype(np.float32)


def _align_arrays(arrays: list[np.ndarray]) -> list[np.ndarray]:
    """Truncate all arrays to the length of the shortest one (deterministic alignment).

    Keeps leading samples and drops trailing samples to make all arrays the same length.
    """
    lengths = [len(a) for a in arrays]
    min_length = int(min(lengths))
    out: list[np.ndarray] = []
    for a in arrays:
        a = np.asarray(a, dtype=np.float32)
        if len(a) > min_length:
            a = a[:min_length]
        out.append(a.astype(np.float32))
    return out


def load_f0_override(base_path: str) -> np.ndarray | None:
    """Load an optional per-file F0 override from a .npy file at {base_path}.f0_override.npy.

    The override must be a 1-D float32 array of F0-in-Hz values (not normalized).
    Returns the array if the file exists, else None.
    """
    path = f"{base_path}.f0_override.npy"
    if not os.path.exists(path):
        return None
    arr = np.load(path, allow_pickle=False)
    if arr.dtype != np.float32:
        arr = arr.astype(np.float32)
    return arr


def compute_features(
    audio: np.ndarray,
    sample_rate: float,
    f0_extractor_name: str = "parselmouth",
    hop_length: int = 256,
    n_fft: int = 2048,
    f0_override: np.ndarray | None = None,
) -> dict[str, np.ndarray]:
    """Run F0 + confidence (chosen extractor) and loudness, normalize each to [0,1].

    If *f0_override* is a 1-D float32 array of F0-in-Hz values (NOT normalized), the F0
    extractor is skipped entirely and the override is used instead — confidence is set to 1.0
    for every frame. Otherwise the named extractor runs as usual.

    Returns a dict with keys "f0_hz", "f0_confidence", "loudness_db" — all float32 1-D
    arrays of the same length (aligned by truncating to the shortest channel).

    Normalization:
    - f0_hz: min-max normalized to [0,1] over its own values.
    - loudness_db: min-max normalized to [0,1] over its own values.
    - f0_confidence: already in [0,1]; passed through unchanged.
    """
    logger.debug(
        "compute_features: extractor=%s audio_len=%d sr=%g",
        f0_extractor_name,
        len(audio),
        sample_rate,
    )
    if f0_override is not None:
        f0_hz_norm = normalize_feature(f0_override)
        confidence = np.ones_like(f0_hz_norm, dtype=np.float32)
        loudness_db = extract_loudness_db(audio, sample_rate, hop_length=hop_length, n_fft=n_fft)
        loudness_norm = normalize_feature(loudness_db)
        f0_hz_norm, confidence, loudness_norm = _align_arrays(
            [f0_hz_norm, confidence, loudness_norm]
        )
        return {
            "f0_hz": f0_hz_norm,
            "f0_confidence": confidence,
            "loudness_db": loudness_norm,
        }

    extractor = get_f0_extractor(f0_extractor_name)
    if f0_extractor_name == "parselmouth":
        f0_hz, f0_confidence = extractor(audio, sample_rate)
    else:
        # crepe (or any future backend that accepts hop_length)
        f0_hz, f0_confidence = extractor(audio, sample_rate, hop_length=hop_length)
    loudness_db = extract_loudness_db(audio, sample_rate, hop_length=hop_length, n_fft=n_fft)

    f0_hz_norm = normalize_feature(f0_hz)
    loudness_norm = normalize_feature(loudness_db)
    # confidence is already in [0,1] from the extractors; pass unchanged.
    confidence = np.asarray(f0_confidence, dtype=np.float32)

    f0_hz_norm, confidence, loudness_norm = _align_arrays([f0_hz_norm, confidence, loudness_norm])

    return {
        "f0_hz": f0_hz_norm,
        "f0_confidence": confidence,
        "loudness_db": loudness_norm,
    }


def compute_features_poly(
    audio: np.ndarray,
    sample_rate: float,
    n_voices: int = 1,
    hop_length: int = 256,
    n_fft: int = 2048,
    f0_extractor_name: str = "parselmouth",
    f0_override: np.ndarray | None = None,
) -> dict[str, np.ndarray]:
    """Run F0 extraction for polyphonic audio.

    When n_voices == 1, delegates to compute_features() for identical behavior.
    When n_voices > 1, calls extract_multi_pitch to get (N, T_frames) f0 tracks
    and also computes single-voice f0 via the existing extractor for backward compat.

    Returns a dict with keys:
      - "f0_hz"          : 1-D float32, min-max normalized to [0,1]
      - "f0_confidence"  : 1-D float32, already in [0,1] (from extractor)
      - "loudness_db"     : 1-D float32, min-max normalized to [0,1]
      - "f0_hz_voices"   : 2-D float32 (N, T_frames), raw Hz, NOT normalized
    """
    if n_voices == 1:
        return compute_features(
            audio,
            sample_rate,
            f0_extractor_name=f0_extractor_name,
            hop_length=hop_length,
            n_fft=n_fft,
            f0_override=f0_override,
        )

    # n_voices > 1: polyphonic path
    if f0_override is not None:
        # Override path for polyphonic: broadcast 1-D override to (n_voices, T)
        # first voice gets the override, remaining voices get zeros
        f0_hz_norm = normalize_feature(f0_override)
        confidence = np.ones_like(f0_hz_norm, dtype=np.float32)
        loudness_db = extract_loudness_db(audio, sample_rate, hop_length=hop_length, n_fft=n_fft)
        loudness_norm = normalize_feature(loudness_db)
        f0_hz_norm, confidence, loudness_norm = _align_arrays(
            [f0_hz_norm, confidence, loudness_norm]
        )
        # Build f0_hz_voices: (n_voices, T_frames) with first voice from override
        t_len = len(f0_hz_norm)
        f0_voices_raw = np.zeros((n_voices, t_len), dtype=np.float32)
        f0_voices_raw[0, :t_len] = np.asarray(f0_override, dtype=np.float32)[:t_len]
        return {
            "f0_hz": f0_hz_norm,
            "f0_confidence": confidence,
            "loudness_db": loudness_norm,
            "f0_hz_voices": f0_voices_raw,
        }

    # Polyphonic: extract multi-pitch (N, T_frames)
    f0_hz_voices = extract_multi_pitch(
        audio,
        int(sample_rate),
        n_voices,
        hop_length,
    )

    # Single-voice f0 for backward compat (use first voice or run extractor)
    extractor = get_f0_extractor(f0_extractor_name)
    if f0_extractor_name == "parselmouth":
        f0_hz, f0_confidence = extractor(audio, sample_rate)
    else:
        f0_hz, f0_confidence = extractor(audio, sample_rate, hop_length=hop_length)
    loudness_db = extract_loudness_db(audio, sample_rate, hop_length=hop_length, n_fft=n_fft)

    # Normalize single-voice f0 and loudness
    f0_hz_norm = normalize_feature(f0_hz)
    loudness_norm = normalize_feature(loudness_db)
    confidence = np.asarray(f0_confidence, dtype=np.float32)

    # Align single-voice arrays
    f0_hz_norm, confidence, loudness_norm = _align_arrays([f0_hz_norm, confidence, loudness_norm])

    # f0_hz_voices stays raw Hz (NOT normalized).
    # Align f0_hz_voices to the same length as the single-voice arrays.
    t_len = len(f0_hz_norm)
    if f0_hz_voices.shape[1] > t_len:
        f0_hz_voices = f0_hz_voices[:, :t_len]
    elif f0_hz_voices.shape[1] < t_len:
        pad = np.zeros((f0_hz_voices.shape[0], t_len - f0_hz_voices.shape[1]), dtype=np.float32)
        f0_hz_voices = np.concatenate([f0_hz_voices, pad], axis=1)
    f0_hz_voices = f0_hz_voices.astype(np.float32)

    return {
        "f0_hz": f0_hz_norm,
        "f0_confidence": confidence,
        "loudness_db": loudness_norm,
        "f0_hz_voices": f0_hz_voices,
    }


def save_features(
    features: dict[str, np.ndarray],
    out_dir: str,
    base_name: str,
) -> list[str]:
    """Write one .npy per feature into out_dir (created if needed).

    Files: {base_name}.f0_hz.npy, {base_name}.f0_confidence.npy,
           {base_name}.loudness_db.npy, [optionally] {base_name}.f0_hz_voices.npy
    Returns the list of written paths.
    """
    os.makedirs(out_dir, exist_ok=True)
    paths: list[str] = []
    keys: tuple[str, ...] = ("f0_hz", "f0_confidence", "loudness_db")
    if "f0_hz_voices" in features:
        keys = (*keys, "f0_hz_voices")
    if "content_embedding" in features:
        keys = (*keys, "content_embedding")
    for key in keys:
        path = os.path.join(out_dir, f"{base_name}.{key}.npy")
        np.save(path, np.asarray(features[key], dtype=np.float32), allow_pickle=False)
        paths.append(path)
    logger.debug("save_features: base=%s keys=%s", base_name, list(keys))
    return paths


def extract_content_embedding(
    audio: np.ndarray,
    sample_rate: int,
    model_name: str = "hubert_soft",
    target_frames: int | None = None,
    cache_dir: str | None = None,
) -> np.ndarray:
    """Extract HuBERT/ContentVec semantic content embeddings from audio.

    Uses ContentEncoderWrapper internally. Returns (T_frames, 256) numpy array.

    Args:
        audio: 1-D float32 audio samples.
        sample_rate: sample rate in Hz (must be 16000 for HuBERT-Soft).
        model_name: "hubert_soft" or "content_vec".
        target_frames: optional resampling to match DDSP frame rate.
        cache_dir: optional HuggingFace cache directory.

    Returns:
        embedding: (T_frames, 256) float32 numpy array.
    """
    logger.debug(
        "extract_content_embedding: model=%s audio_len=%d target_frames=%s",
        model_name,
        len(audio),
        target_frames,
    )
    import torch

    from model.content_encoder import ContentEncoderWrapper, resample_content

    encoder = ContentEncoderWrapper(model_name, cache_dir=cache_dir)
    audio_t = torch.from_numpy(audio).float().unsqueeze(0)
    with torch.no_grad():
        emb = encoder(audio_t, sample_rate)
    if target_frames is not None:
        emb = resample_content(emb, target_frames)
    return emb.squeeze(0).numpy().astype(np.float32)  # (T_frames, 256)
