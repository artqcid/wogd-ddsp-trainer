"""Self-owned differentiable DSP synths (no external ddsp dependency).

All modules are torch.nn.Module and operate on float32/64 tensors.
Device is inferred from inputs — no hard-coded cuda() calls.
"""

from __future__ import annotations

from dataclasses import dataclass

import torch
import torch.nn as nn


@dataclass
class SynthConfig:
    """Config shared by the DDSP synth branch."""

    sample_rate: int = 16000
    hop_length: int = 128
    n_harmonics: int = 60


class HarmonicOscillatorSynth(nn.Module):
    """Additive synthesis from per-frame harmonic amplitudes.

    Given frame-aligned amplitudes (B, T_frames, H) and a harmonic distribution
    (B, T_frames, H) that is a softmax over H harmonics, synthesize audio by
    summing H sine oscillators whose frequencies are integer multiples of f0.

    Phase is integrated via cumulative sum of instantaneous phase increments
    (f0 * h * dt, where dt = 1 / sample_rate) and upsampled to audio rate.
    Output length is derived from the frame count and hop.
    """

    def __init__(self, n_harmonics: int = 60) -> None:
        super().__init__()
        self.n_harmonics = n_harmonics

    def forward(
        self,
        amplitudes: torch.Tensor,
        harmonic_distribution: torch.Tensor,
        f0: torch.Tensor,
        sample_rate: int = 16000,
        hop_length: int = 128,
    ) -> torch.Tensor:
        """Synthesize audio from harmonic parameters.

        Args:
            amplitudes: per-frame harmonic amplitudes, shape (B, T_frames, H).
            harmonic_distribution: softmax over harmonics, shape (B, T_frames, H).
            f0: fundamental frequency in Hz, shape (B, T_frames).
            sample_rate: audio sample rate in Hz.
            hop_length: samples per frame.

        Returns:
            Audio tensor of shape (B, T_audio).
        """
        B, T_frames, _ = amplitudes.shape
        device = amplitudes.device
        dtype = amplitudes.dtype

        # Harmonic frequencies: h * f0, shape (B, T_frames, H)
        harmonic_indices = torch.arange(1, self.n_harmonics + 1, device=device, dtype=dtype)
        harmonic_freqs = f0.unsqueeze(-1) * harmonic_indices  # (B, T_frames, H)

        # Effective amplitude per harmonic (modulated by distribution)
        harmonic_amps = amplitudes * harmonic_distribution  # (B, T_frames, H)

        # Phase increments per sample for each harmonic: 2*pi * freq / sr
        phase_increments = 2.0 * torch.pi * harmonic_freqs / sample_rate
        # Phase change per hop (integrated over hop_length samples)
        phase_per_frame = phase_increments * hop_length  # (B, T_frames, H)

        # Integrated phase at frame boundaries
        phase_frames = torch.cumsum(phase_per_frame, dim=1)  # (B, T_frames, H)

        # Audio-rate length
        T_audio = (T_frames - 1) * hop_length + 1

        # Upsample phase and amplitudes from T_frames to T_audio.
        # Interpolate expects (B, C, T), so transpose to (B, H, T_frames).
        def _upsample_1d(x: torch.Tensor) -> torch.Tensor:
            # x: (B, T_frames, H) -> (B, H, T_audio)
            y = x.transpose(1, 2)
            y = torch.nn.functional.interpolate(
                y,
                size=T_audio,
                mode="linear",
                align_corners=False,
            )
            return y.transpose(1, 2)  # back to (B, T_audio, H)

        phase_audio = _upsample_1d(phase_frames)  # (B, T_audio, H)
        amp_audio = _upsample_1d(harmonic_amps)  # (B, T_audio, H)

        # Additive synthesis: sum over harmonics
        audio = (amp_audio * torch.sin(phase_audio)).sum(dim=-1)  # (B, T_audio)
        return audio


class SimpleReverb(nn.Module):
    """Lightweight differentiable reverb via a finite feedforward comb filter.

    Approximates an infinite feedback comb with a finite cascade of decay taps
    applied through a length-T FIR impulse response via conv1d. The impulse
    response is materialized once as a fixed module buffer at init time and
    sliced per-call in a trace-friendly way (no Python-bool on tensors, no
    in-place scatter, no min() on runtime lengths).
    """

    def __init__(
        self,
        delay_seconds: float = 0.03,
        decay: float = 0.5,
        sample_rate: int = 16000,
        n_delays: int = 6,
    ) -> None:
        super().__init__()
        self.delay_samples = int(round(delay_seconds * sample_rate))
        self.decay = decay
        self.n_delays = n_delays

        # Fixed maximum FIR length (trace-independent of the runtime T).
        # Tap k sits at sample offset k * delay_samples with weight decay**k,
        # k in [0, n_delays). The last used tap index is (n_delays - 1),
        # so the kernel needs room up to that offset.
        max_kernel_len = self.n_delays * self.delay_samples + 1
        kernel = torch.zeros(max_kernel_len)
        index_arange = torch.arange(self.n_delays, dtype=torch.int64)
        values_arange = torch.arange(self.n_delays, dtype=kernel.dtype)
        kernel[index_arange * self.delay_samples] = self.decay**values_arange
        self.register_buffer("kernel", kernel)

    def forward(self, x):
        """Apply comb filter reverb to audio.

        Args:
            x: input audio, shape (B, T) or (T,).

        Returns:
            Reverb-processed audio of same shape.
        """
        # Remember original dimensionality to restore at the end
        original_ndim = x.dim()
        if original_ndim == 1:
            x = x.unsqueeze(0)

        # Fixed FIR impulse response, sliced/centred for this input length.
        kernel = self.kernel.to(dtype=x.dtype)  # (L,)
        kernel_2d = kernel.reshape(1, 1, -1)  # (1, 1, L)

        # 'same' padding keeps the output length equal to the input length T.
        out = torch.nn.functional.conv1d(
            x.unsqueeze(1),
            kernel_2d,
            padding="same",
        )  # (B, 1, T)
        out = out.squeeze(1)  # (B, T)

        # Restore original dimensionality
        if original_ndim == 1:
            out = out.squeeze(0)

        return out


class FilteredNoiseSynth(nn.Module):
    """Filtered noise branch: white gaussian noise shaped by per-frame magnitude filter.

    Generates noise and applies a differentiable magnitude envelope in the
    time domain via per-frame gain applied to noise segments, then vectorized
    via upsampling of the energy envelope.
    """

    def __init__(self, hop_length: int = 128, max_noise_len: int = 1 << 20) -> None:
        super().__init__()
        self.hop_length = hop_length
        generator = torch.Generator().manual_seed(0)
        noise_buffer = torch.randn(max_noise_len, generator=generator)
        self.register_buffer("noise_buffer", noise_buffer)

    def forward(
        self,
        magnitudes: torch.Tensor,
        n_samples: int,
        sample_rate: int = 16000,
    ) -> torch.Tensor:
        """Synthesize filtered noise audio.

        Args:
            magnitudes: per-frame magnitude envelope, shape (B, T_frames, filter_bins).
            n_samples: total output audio length.
            sample_rate: audio sample rate.

        Returns:
            Audio tensor of shape (B, n_samples).
        """
        B, T_frames, _ = magnitudes.shape
        device = magnitudes.device
        dtype = magnitudes.dtype

        # Sum magnitudes across filter bins to get per-frame energy envelope
        frame_energy = magnitudes.sum(dim=-1)  # (B, T_frames)

        # Normalize per frame to bounded [0,1], then amplitude
        frame_energy = torch.sigmoid(frame_energy)
        amp = torch.sqrt(frame_energy + 1e-8)  # (B, T_frames)

        # Upsample amplitude envelope from T_frames to n_samples
        # Interpolate expects (B, C, T), so reshape to (B, 1, T_frames)
        amp_1d = amp.unsqueeze(1)  # (B, 1, T_frames)
        amp_audio = torch.nn.functional.interpolate(
            amp_1d,
            size=n_samples,
            mode="linear",
            align_corners=False,
        )  # (B, 1, n_samples)
        amp_audio = amp_audio.squeeze(1)  # (B, n_samples)

        # Generate white noise at audio rate from deterministic buffer.
        noise = self.noise_buffer[:n_samples].to(device=device, dtype=dtype)
        noise = noise.unsqueeze(0).expand(B, n_samples)

        # Apply amplitude envelope
        audio = noise * amp_audio  # (B, n_samples)
        return audio


class DDSPCore(nn.Module):
    """Composed DDSP core: harmonic oscillator + filtered noise + reverb.

    This is the self-owned synthesis backbone. It does NOT depend on the
    external ddsp Python library.
    """

    def __init__(
        self,
        n_harmonics: int = 60,
        sample_rate: int = 16000,
        hop_length: int = 128,
        reverb_delay: float = 0.03,
        reverb_decay: float = 0.5,
        use_reverb: bool = True,
    ) -> None:
        super().__init__()
        self.sample_rate = sample_rate
        self.hop_length = hop_length
        self.use_reverb = use_reverb

        self.harmonic_synth = HarmonicOscillatorSynth(n_harmonics=n_harmonics)
        self.noise_synth = FilteredNoiseSynth(hop_length=hop_length)
        if use_reverb:
            self.reverb = SimpleReverb(
                delay_seconds=reverb_delay,
                decay=reverb_decay,
                sample_rate=sample_rate,
            )

    def forward(
        self,
        amplitudes: torch.Tensor,
        harmonic_distribution: torch.Tensor,
        f0: torch.Tensor,
        noise_magnitudes: torch.Tensor,
        n_samples: int,
    ) -> torch.Tensor:
        """Synthesize full audio from DDSP parameters.

        Args:
            amplitudes: per-frame harmonic amplitudes, (B, T_frames, H).
            harmonic_distribution: softmax over harmonics, (B, T_frames, H).
            f0: fundamental frequency in Hz, (B, T_frames).
            noise_magnitudes: noise filter magnitudes, (B, T_frames, filter_bins).
            n_samples: total output audio length.

        Returns:
            Mixed audio of shape (B, n_samples).
        """
        harmonic_audio = self.harmonic_synth(
            amplitudes,
            harmonic_distribution,
            f0,
            sample_rate=self.sample_rate,
            hop_length=self.hop_length,
        )

        noise_audio = self.noise_synth(
            noise_magnitudes,
            n_samples=n_samples,
            sample_rate=self.sample_rate,
        )

        # Apply reverb only to noise branch (common DDSP pattern)
        if self.use_reverb:
            noise_audio = self.reverb(noise_audio)

        # Mix: harmonic + filtered noise
        audio = harmonic_audio + noise_audio
        return audio
