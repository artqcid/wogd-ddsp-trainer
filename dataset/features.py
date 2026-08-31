"""Feature extraction for DDSP training: F0, loudness, normalization, and .npy export.

F0 extraction uses parselmouth (CPU, offline) or torchcrepe (ML primary). Loudness uses a
librosa RMS-to-dB path. All returned arrays are plain 1-D float32 numpy.
"""

from __future__ import annotations

import os
from collections.abc import Callable

import librosa
import numpy as np
import parselmouth

try:  # pragma: no cover - torchcrepe is optional at import time, used by the crepe path only
    import torch
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


def save_features(
    features: dict[str, np.ndarray],
    out_dir: str,
    base_name: str,
) -> list[str]:
    """Write one .npy per feature into out_dir (created if needed).

    Files: {base_name}.f0_hz.npy, {base_name}.f0_confidence.npy, {base_name}.loudness_db.npy
    Returns the list of written paths.
    """
    os.makedirs(out_dir, exist_ok=True)
    paths: list[str] = []
    for key in ("f0_hz", "f0_confidence", "loudness_db"):
        path = os.path.join(out_dir, f"{base_name}.{key}.npy")
        np.save(path, np.asarray(features[key], dtype=np.float32), allow_pickle=False)
        paths.append(path)
    return paths
