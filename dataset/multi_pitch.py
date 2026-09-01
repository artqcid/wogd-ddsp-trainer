"""Multi-pitch extraction for polyphonic DDSP training.

Uses STFT-based spectral peak-picking to find multiple f0 candidates per frame:
1. Compute magnitude spectrum via STFT.
2. Find spectral peaks per frame.
3. Assign the N strongest non-harmonic peaks to N voices.
"""

from __future__ import annotations

from typing import Literal

import librosa
import numpy as np


def _spectral_peaks(
    mag: np.ndarray, sample_rate: int, n_peaks: int, fmin: float = 50.0, fmax: float = 2000.0
) -> np.ndarray:
    """Find the top *n_peaks* frequency peaks in a magnitude spectrum.

    Returns sorted Hz values (descending confidence). Unvoiced = 0.0.
    """
    freqs = librosa.fft_frequencies(sr=sample_rate, n_fft=(len(mag) - 1) * 2)
    mask = (freqs >= fmin) & (freqs <= fmax)
    filtered_mag = mag.copy()
    filtered_mag[~mask] = 0.0

    n_fft = len(mag)
    local_max = np.ones(n_fft, dtype=bool)
    local_max[1:-1] = (mag[1:-1] > mag[:-2]) & (mag[1:-1] > mag[2:])
    local_max[~mask] = False

    peak_indices = np.where(local_max)[0]
    if len(peak_indices) == 0:
        return np.zeros(n_peaks, dtype=np.float32)

    peak_values = mag[peak_indices]
    top_idx = np.argsort(peak_values)[::-1][:n_peaks]
    peak_hz = freqs[peak_indices[top_idx]].astype(np.float32)

    result = np.zeros(n_peaks, dtype=np.float32)
    result[: len(peak_hz)] = peak_hz
    return result


def _remove_harmonics(peaks: np.ndarray, f0_primary: float, tolerance: float = 0.05) -> np.ndarray:
    """Zero out peaks that are integer multiples (harmonics) of *f0_primary*.

    A peak at frequency ``f`` is considered a harmonic of ``f0`` if
    ``f / f0`` rounded to the nearest integer is within ``tolerance`` relative.
    """
    if f0_primary <= 0.0:
        return peaks
    result = peaks.copy()
    for i in range(len(result)):
        if result[i] <= 0.0:
            continue
        ratio = result[i] / f0_primary
        nearest = round(ratio)
        if nearest >= 2 and abs(ratio - nearest) / nearest < tolerance:
            result[i] = 0.0
    return result


def extract_multi_pitch(
    audio: np.ndarray,
    sample_rate: int,
    n_voices: int,
    hop_length: int,
    method: Literal["basic_pitch", "stft_peaks"] = "stft_peaks",
) -> np.ndarray:
    """Extract N f0 tracks from polyphonic audio via STFT spectral peak-picking.

    Args:
        audio: 1-D float32 audio samples.
        sample_rate: sample rate in Hz.
        n_voices: number of f0 tracks to extract.
        hop_length: STFT hop length in samples (controls frame rate).
        method: only ``"stft_peaks"`` is implemented.

    Returns:
        f0_tracks: (N, T_frames) float32 array of f0 values in Hz.
                   Unvoiced frames set to 0.0.
    """
    if method != "stft_peaks":
        raise ValueError(f"Unsupported method '{method}'. Only 'stft_peaks' is implemented.")

    n_fft = 2048
    stft = librosa.stft(audio, n_fft=n_fft, hop_length=hop_length, win_length=n_fft, center=True)
    mag = np.abs(stft)  # (n_fft // 2 + 1, T)
    T_frames = mag.shape[1]

    f0_tracks = np.zeros((n_voices, T_frames), dtype=np.float32)

    for t in range(T_frames):
        spectrum = mag[:, t]
        peaks = _spectral_peaks(spectrum, sample_rate, n_peaks=n_voices + 4, fmin=50.0, fmax=2000.0)

        # First voice = strongest peak (primary f0)
        primary = peaks[0] if len(peaks) > 0 and peaks[0] > 0.0 else 0.0
        f0_tracks[0, t] = primary

        if n_voices > 1:
            remaining = peaks[1:] if primary > 0.0 else peaks
            if primary > 0.0:
                remaining = _remove_harmonics(remaining, primary)
            non_zero = remaining[remaining > 0.0]
            for v in range(1, n_voices):
                if v - 1 < len(non_zero):
                    f0_tracks[v, t] = non_zero[v - 1]
                # else stays 0.0 (unvoiced)

    return f0_tracks
