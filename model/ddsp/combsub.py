"""Comb-filter subtractive synthesis engine (DDSP-SVC style "combsub").

CombSubSynth generates a harmonic excitation (voiced) via a pulse train at the
f0 rate, or white noise (unvoiced), then shapes the result with a per-frame
spectral envelope derived from `comb_magnitudes`. Reverb is not applied here;
when needed it is handled externally by the caller (e.g. DDSPCore).

Signal flow:
    f0 + voiced_probability
        |-- voiced --> pulse train -----+
        |-- unvoiced -> noise -----------+
        +--> excitation (B, T_audio)
        |--> spectral envelope (from comb_magnitudes) --> shaped audio
"""

from __future__ import annotations

import torch
import torch.nn as nn


class CombSubSynth(nn.Module):
    """Comb-filter subtractive synthesis for vocal formants.

    Args:
        n_fir_taps: number of spectral magnitude bins per frame.
        sample_rate: audio sample rate in Hz.
        hop_length: samples per frame.
        pulse_width: fraction of each f0 period occupied by the bipolar pulse.
        max_noise_len: length of the deterministic noise buffer.
    """

    def __init__(
        self,
        n_fir_taps: int = 64,
        sample_rate: int = 16000,
        hop_length: int = 128,
        pulse_width: float = 0.1,
        max_noise_len: int = 1 << 20,
    ) -> None:
        super().__init__()
        self.n_fir_taps = n_fir_taps
        self.sample_rate = sample_rate
        self.hop_length = hop_length
        self.pulse_width = pulse_width

        # Deterministic noise buffer (same pattern as FilteredNoiseSynth).
        generator = torch.Generator().manual_seed(0)
        noise_buffer = torch.randn(max_noise_len, generator=generator)
        self.register_buffer("noise_buffer", noise_buffer)

    def forward(
        self,
        comb_magnitudes: torch.Tensor,
        f0: torch.Tensor,
        voiced: torch.Tensor,
        n_samples: int,
    ) -> torch.Tensor:
        """Synthesize audio from comb-subtractive parameters.

        Args:
            comb_magnitudes: per-frame spectral magnitudes, (B, T_frames, n_fir_taps).
            f0: fundamental frequency in Hz, (B, T_frames).
            voiced: voiced probability in [0, 1], (B, T_frames).
            n_samples: total output audio length.

        Returns:
            Audio tensor of shape (B, n_samples).
        """
        B, T_frames, _n_taps = comb_magnitudes.shape
        device = comb_magnitudes.device
        dtype = comb_magnitudes.dtype

        # ---- Excitation ----

        # Voiced: bipolar pulse train at f0 rate.
        phase_inc = f0 / self.sample_rate  # (B, T_frames)
        phase = torch.cumsum(phase_inc, dim=1) % 1.0
        pulse = (phase < self.pulse_width).to(dtype) * 2.0 - 1.0  # (B, T_frames)

        # Upsample pulse from T_frames to n_samples.
        pulse_1d = pulse.unsqueeze(1)  # (B, 1, T_frames)
        pulse_audio = torch.nn.functional.interpolate(
            pulse_1d,
            size=n_samples,
            mode="linear",
            align_corners=False,
        )  # (B, 1, n_samples)
        pulse_audio = pulse_audio.squeeze(1)  # (B, n_samples)

        # Unvoiced: white noise from the deterministic buffer.
        noise = self.noise_buffer[:n_samples].to(device=device, dtype=dtype)  # (n_samples,)
        noise = noise.unsqueeze(0).expand(B, n_samples)  # (B, n_samples)

        # ---- Voiced/unvoiced mixing ----

        # Upsample voiced probability to audio rate.
        voiced_1d = voiced.unsqueeze(1)  # (B, 1, T_frames)
        voiced_audio = torch.nn.functional.interpolate(
            voiced_1d,
            size=n_samples,
            mode="linear",
            align_corners=False,
        )  # (B, 1, n_samples)
        voiced_audio = voiced_audio.squeeze(1)  # (B, n_samples)

        excitation = voiced_audio * pulse_audio + (1.0 - voiced_audio) * noise  # (B, n_samples)

        # ---- Spectral envelope (amplitude shaping) ----

        # Frame energy from summed magnitudes; normalize and convert to amplitude.
        frame_energy = comb_magnitudes.sum(dim=-1)  # (B, T_frames)
        frame_energy = torch.sigmoid(frame_energy)
        amp = torch.sqrt(frame_energy + 1e-8)  # (B, T_frames)

        # Upsample amplitude envelope to audio rate.
        amp_1d = amp.unsqueeze(1)  # (B, 1, T_frames)
        amp_audio = torch.nn.functional.interpolate(
            amp_1d,
            size=n_samples,
            mode="linear",
            align_corners=False,
        )  # (B, 1, n_samples)
        amp_audio = amp_audio.squeeze(1)  # (B, n_samples)

        audio = excitation * amp_audio  # (B, n_samples)
        return audio
