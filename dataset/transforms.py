"""F0 transformation rules for creative sound design (M7.1.3).

All functions take and return 1-D float32 numpy arrays (F0 in Hz).
These operate BEFORE the normalisation step in compute_features().
"""

from __future__ import annotations

import numpy as np


def quantize_to_scale(
    f0: np.ndarray,
    base_freq: float = 220.0,
    scale: str = "chromatic",
) -> np.ndarray:
    """Quantize F0 to the nearest note on a musical scale.

    Args:
        f0: 1-D float32 F0 array in Hz (0.0 = unvoiced).
        base_freq: Reference frequency for scale root (default A3=220 Hz).
        scale: One of "chromatic", "major", "minor", "pentatonic".

    Returns:
        Quantized F0 array of same shape.
    """
    # Chromatic: 12-tone equal temperament
    semitones = 12.0 * np.log2(np.maximum(f0, 1.0) / base_freq)
    quantized_st = np.round(semitones)

    if scale == "major":
        # Major scale semitone offsets from root: 0, 2, 4, 5, 7, 9, 11
        scale_offsets = np.array([0, 2, 4, 5, 7, 9, 11], dtype=np.float32)
        quantized_st = _snap_to_scale(quantized_st, scale_offsets)
    elif scale == "minor":
        # Natural minor: 0, 2, 3, 5, 7, 8, 10
        scale_offsets = np.array([0, 2, 3, 5, 7, 8, 10], dtype=np.float32)
        quantized_st = _snap_to_scale(quantized_st, scale_offsets)
    elif scale == "pentatonic":
        # Major pentatonic: 0, 2, 4, 7, 9
        scale_offsets = np.array([0, 2, 4, 7, 9], dtype=np.float32)
        quantized_st = _snap_to_scale(quantized_st, scale_offsets)
    # "chromatic" needs no snapping

    result = base_freq * (2.0 ** (quantized_st / 12.0))
    # Preserve unvoiced (0.0) frames
    result[f0 == 0.0] = 0.0
    return result.astype(np.float32)


def _snap_to_scale(semitones: np.ndarray, scale_offsets: np.ndarray) -> np.ndarray:
    """Snap each semitone to the nearest scale degree across octaves."""
    octave = np.floor(semitones / 12.0)
    within_octave = semitones - octave * 12.0
    snapped = np.zeros_like(semitones)
    for i, val in enumerate(within_octave):
        idx = np.argmin(np.abs(scale_offsets - val))
        snapped[i] = octave[i] * 12.0 + scale_offsets[idx]
    return snapped


def inject_noise(
    f0: np.ndarray,
    noise_std: float = 50.0,
    probability: float = 0.1,
    seed: int | None = None,
) -> np.ndarray:
    """Add Gaussian jitter to random F0 frames.

    Args:
        f0: 1-D float32 F0 array in Hz.
        noise_std: Standard deviation of Gaussian noise in Hz.
        probability: Per-frame probability of adding noise.
        seed: Random seed for reproducibility.

    Returns:
        Noisy F0 array of same shape.
    """
    rng = np.random.default_rng(seed)
    mask = rng.random(len(f0)) < probability
    noise = rng.normal(0.0, noise_std, size=len(f0)).astype(np.float32)
    result = f0.copy()
    result[mask] = np.maximum(result[mask] + noise[mask], 0.0)
    return result


def invert_pitch(
    f0: np.ndarray,
    pivot_freq: float = 440.0,
) -> np.ndarray:
    """Invert pitch around a pivot frequency.

    High becomes low and vice versa. Unvoiced frames stay unvoiced.

    Args:
        f0: 1-D float32 F0 array in Hz.
        pivot_freq: Reflection pivot frequency in Hz.

    Returns:
        Inverted F0 array of same shape.
    """
    result = f0.copy()
    voiced = f0 > 0.0
    result[voiced] = np.maximum(2.0 * pivot_freq - f0[voiced], 0.0)
    return result


def silence_unvoiced(f0: np.ndarray) -> np.ndarray:
    """Return a version with only voiced frames kept (unvoiced stay 0.0).

    Identity operation — F0 arrays already have 0.0 for unvoiced frames.
    """
    return f0.copy()
