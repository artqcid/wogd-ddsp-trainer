"""Freely-learned sinusoidal oscillator synth (M9 alternative engine).

Unlike `HarmonicOscillatorSynth`, this receives per-partial frequencies
directly (no f0 * harmonic-ratio constraint), enabling inharmonic sounds
(bells, xylophones, metal plates) where harmonics are not integer multiples
of a fundamental.

Phase accumulation and audio-rate upsampling follow the same pattern as
`HarmonicOscillatorSynth` in `model/ddsp/synths.py`.
"""

from __future__ import annotations

import torch
import torch.nn as nn


class SinusoidalSynth(nn.Module):
    """Additive sine synthesis with freely learned per-partial frequencies.

    Args:
        amplitudes: per-frame amplitudes, shape (B, T_frames, N_partials).
        frequencies: per-partial frequencies in Hz, shape (B, T_frames, N_partials).
        sample_rate: audio sample rate in Hz.
        hop_length: samples per frame.

    Returns:
        Audio tensor of shape (B, T_audio), where T_audio = (T_frames - 1) * hop_length + 1.
    """

    def __init__(self) -> None:
        super().__init__()

    def forward(
        self,
        amplitudes: torch.Tensor,
        frequencies: torch.Tensor,
        sample_rate: int,
        hop_length: int,
    ) -> torch.Tensor:
        B, T_frames, n_partials = amplitudes.shape
        dtype = amplitudes.dtype

        # Nyquist normalization: silence partials above Nyquist to avoid aliasing.
        nyquist_mask = (frequencies < sample_rate / 2.0).to(dtype=dtype)
        amplitudes = amplitudes * nyquist_mask  # (B, T_frames, N_partials)

        # Per-partial frequencies are given directly (no f0 * ratio computation).
        harmonic_freqs = frequencies  # (B, T_frames, N_partials)

        # Phase increments per sample: 2*pi * freq / sr
        phase_increments = 2.0 * torch.pi * harmonic_freqs / float(sample_rate)
        # Phase change per hop (integrated over hop_length samples)
        phase_per_frame = phase_increments * float(hop_length)  # (B, T_frames, N_partials)

        # Integrated phase at frame boundaries
        phase_frames = torch.cumsum(phase_per_frame, dim=1)  # (B, T_frames, N_partials)

        # Audio-rate length
        T_audio = (T_frames - 1) * hop_length + 1

        # Upsample phase and amplitudes from T_frames to T_audio.
        # Interpolate expects (B, C, T), so transpose to (B, N_partials, T_frames).
        def _upsample_1d(x: torch.Tensor) -> torch.Tensor:
            # x: (B, T_frames, N_partials) -> (B, N_partials, T_audio)
            y = x.transpose(1, 2)
            y = torch.nn.functional.interpolate(
                y,
                size=T_audio,
                mode="linear",
                align_corners=False,
            )
            return y.transpose(1, 2)  # back to (B, T_audio, N_partials)

        phase_audio = _upsample_1d(phase_frames)  # (B, T_audio, N_partials)
        amp_audio = _upsample_1d(amplitudes)  # (B, T_audio, N_partials)

        # Additive synthesis: sum over partials
        audio = (amp_audio * torch.sin(phase_audio)).sum(dim=-1)  # (B, T_audio)
        return audio
