"""Self-owned differentiable DSP synths (no external ddsp dependency).

All modules are torch.nn.Module and operate on float32/64 tensors.
Device is inferred from inputs — no hard-coded cuda() calls.
"""

from __future__ import annotations

from dataclasses import dataclass

import torch
import torch.nn as nn

from .noise_colored import _brown_noise, _pink_noise
from .variant import DDSPVariant


def _angular_cumsum(x: torch.Tensor) -> torch.Tensor:
    cum = torch.cumsum(x, dim=1)
    return (cum + torch.pi) % (2 * torch.pi) - torch.pi


def _apply_waveform(
    phase: torch.Tensor, variant: DDSPVariant, wavetable: torch.Tensor | None = None
) -> torch.Tensor:
    if variant.pd_k != 0.0:
        phase = phase + variant.pd_k * torch.sin(phase)
    if variant.use_trainable_wavetable and wavetable is not None:
        idx = (phase % (2.0 * torch.pi)) / (2.0 * torch.pi) * 255.0
        idx_lo = idx.long().clamp(0, 254)
        idx_hi = (idx_lo + 1).clamp(0, 255)
        frac = idx - idx_lo.float()
        return wavetable[idx_lo] * (1 - frac) + wavetable[idx_hi] * frac
    if variant.waveform == "square":
        return torch.sign(torch.sin(phase))
    if variant.waveform == "saw":
        return (phase % (2.0 * torch.pi)) / torch.pi - 1.0
    return torch.sin(phase)


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

    def __init__(self, n_harmonics: int = 60, variant: DDSPVariant | None = None) -> None:
        super().__init__()
        self.n_harmonics = n_harmonics
        self.variant = variant or DDSPVariant()
        if variant is not None and variant.use_trainable_wavetable:
            t = torch.linspace(0, 2 * torch.pi, 256)
            self.wavetable = nn.Parameter(torch.sin(t))
        else:
            self.wavetable = None

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
        if self.variant.harmonic_ratios is not None:
            _ratios = self.variant.harmonic_ratios
            if len(_ratios) < self.n_harmonics:
                _ratios = _ratios + list(range(len(_ratios) + 1, self.n_harmonics + 1))
            harmonic_indices = torch.tensor(_ratios[: self.n_harmonics], device=device, dtype=dtype)
        else:
            harmonic_indices = torch.arange(1, self.n_harmonics + 1, device=device, dtype=dtype)
        harmonic_freqs = f0.unsqueeze(-1) * harmonic_indices  # (B, T_frames, H)

        # FM synthesis: modulate harmonic frequencies by a modulation oscillator
        if self.variant.fm_depth > 0.0:
            mod_freq = f0 * self.variant.fm_ratio  # (B, T_frames)
            mod_phase = (
                2.0 * torch.pi * mod_freq
                * torch.arange(T_frames, device=device, dtype=dtype).unsqueeze(0)
                * (hop_length / sample_rate)
            )
            mod_phase = torch.cumsum(mod_phase, dim=1)
            mod_signal = self.variant.fm_depth * torch.sin(mod_phase)
            harmonic_freqs = harmonic_freqs + mod_signal.unsqueeze(-1) * f0.unsqueeze(-1)
            harmonic_freqs = harmonic_freqs.clamp(min=1.0)

        # Effective amplitude per harmonic (modulated by distribution)
        harmonic_amps = amplitudes * harmonic_distribution  # (B, T_frames, H)

        # Phase increments per sample for each harmonic: 2*pi * freq / sr
        phase_increments = 2.0 * torch.pi * harmonic_freqs / sample_rate
        # Phase change per hop (integrated over hop_length samples)
        phase_per_frame = phase_increments * hop_length  # (B, T_frames, H)

        # Integrated phase at frame boundaries
        if self.variant.use_angular_cumsum:
            phase_frames = _angular_cumsum(phase_per_frame)
        else:
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
        audio = (amp_audio * _apply_waveform(phase_audio, self.variant, self.wavetable)).sum(dim=-1)
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

    def __init__(
        self,
        hop_length: int = 128,
        max_noise_len: int = 1 << 20,
        variant: DDSPVariant | None = None,
    ) -> None:
        super().__init__()
        self.hop_length = hop_length
        self.variant = variant or DDSPVariant()
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

        # Generate noise at audio rate, respecting variant noise_color and jitter.
        if self.variant.noise_color == "pink":
            noise = _pink_noise(n_samples, device=device, dtype=dtype)
            noise = noise.unsqueeze(0).expand(B, n_samples)
        elif self.variant.noise_color == "brown":
            noise = _brown_noise(n_samples, device=device, dtype=dtype)
            noise = noise.unsqueeze(0).expand(B, n_samples)
        elif self.variant.noise_grain_jitter > 0 and B > 0:
            jitter_samples = int(self.variant.noise_grain_jitter * self.hop_length)
            if jitter_samples > 0:
                noise_slices = []
                max_offset = max(0, len(self.noise_buffer) - n_samples)
                for _i in range(B):
                    offset = torch.randint(0, min(jitter_samples, max_offset + 1), (1,)).item()
                    buf = self.noise_buffer[offset : offset + n_samples].to(
                        device=device, dtype=dtype
                    )
                    noise_slices.append(buf)
                noise = torch.stack(noise_slices, dim=0)
            else:
                noise = self.noise_buffer[:n_samples].to(device=device, dtype=dtype)
                noise = noise.unsqueeze(0).expand(B, n_samples)
        else:
            noise = self.noise_buffer[:n_samples].to(device=device, dtype=dtype)
            noise = noise.unsqueeze(0).expand(B, n_samples)

        # Apply amplitude envelope
        audio = noise * amp_audio  # (B, n_samples)
        return audio


class DDSPCore(nn.Module):
    """Composed DDSP core: selects synths based on variant.engine.

    For ``harmonic``: HarmonicOscillatorSynth + FilteredNoiseSynth + reverb.
    For ``sinusoidal``: SinusoidalSynth + FilteredNoiseSynth + reverb.
    For ``combsub``: CombSubSynth only (self-contained harmonic + noise).

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
        variant: DDSPVariant | None = None,
    ) -> None:
        super().__init__()
        self.sample_rate = sample_rate
        self.hop_length = hop_length
        self.use_reverb = use_reverb
        self.variant = variant or DDSPVariant()

        engine = self.variant.engine
        if engine == "combsub":
            from .combsub import CombSubSynth

            self.harmonic_synth = CombSubSynth(
                n_fir_taps=64,
                sample_rate=sample_rate,
                hop_length=hop_length,
            )
            self.noise_synth = None
        elif engine == "sinusoidal":
            from .sinusoidal import SinusoidalSynth

            self.harmonic_synth = SinusoidalSynth()
            self.noise_synth = FilteredNoiseSynth(hop_length=hop_length, variant=self.variant)
        else:
            self.harmonic_synth = HarmonicOscillatorSynth(
                n_harmonics=n_harmonics, variant=self.variant
            )
            self.noise_synth = FilteredNoiseSynth(hop_length=hop_length, variant=self.variant)

        if use_reverb and self.variant.engine in {"harmonic", "sinusoidal", "newt"}:
            self.reverb = SimpleReverb(
                delay_seconds=reverb_delay,
                decay=reverb_decay,
                sample_rate=sample_rate,
            )
        else:
            self.reverb = None

    def forward(
        self,
        amplitudes: torch.Tensor | None = None,
        harmonic_distribution: torch.Tensor | None = None,
        f0: torch.Tensor | None = None,
        noise_magnitudes: torch.Tensor | None = None,
        sinusoidal_freqs: torch.Tensor | None = None,
        voiced: torch.Tensor | None = None,
        n_samples: int | None = None,
    ) -> torch.Tensor:
        engine = self.variant.engine

        if engine == "combsub":
            audio = self.harmonic_synth(
                comb_magnitudes=noise_magnitudes,
                f0=f0,
                voiced=voiced,
                n_samples=n_samples,
            )
        elif engine == "sinusoidal":
            harmonic_audio = self.harmonic_synth(
                amplitudes=amplitudes,
                frequencies=sinusoidal_freqs,
                sample_rate=self.sample_rate,
                hop_length=self.hop_length,
            )
            noise_magnitudes = (
                torch.zeros_like(amplitudes[..., :1])
                if noise_magnitudes is None
                else noise_magnitudes
            )
            noise_audio = self.noise_synth(
                noise_magnitudes,
                n_samples=n_samples,
                sample_rate=self.sample_rate,
            )
            if self.use_reverb and self.reverb is not None:
                noise_audio = self.reverb(noise_audio)
            audio = harmonic_audio + noise_audio
        elif engine == "newt":
            harmonic_audio = amplitudes.squeeze(-1)
            noise_audio = self.noise_synth(
                noise_magnitudes,
                n_samples=n_samples,
                sample_rate=self.sample_rate,
            )
            if self.use_reverb and self.reverb is not None:
                noise_audio = self.reverb(noise_audio)
            audio = harmonic_audio + noise_audio
        else:
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
            if self.use_reverb and self.reverb is not None:
                noise_audio = self.reverb(noise_audio)
            audio = harmonic_audio + noise_audio

        return audio
