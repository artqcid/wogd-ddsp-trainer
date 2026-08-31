"""DDSP model: GRU/RNN decoder conditioned on f0 + loudness, driving DDSP core synth."""

from __future__ import annotations

from dataclasses import dataclass

import torch
import torch.nn as nn
import torch.nn.functional as F

from model.ddsp import DDSPCore


@dataclass
class DDSPConfig:
    """Configuration for the DDSP model.

    Attributes:
        sample_rate: audio sample rate in Hz.
        frame_size: samples per analysis frame (also used as hop length for synthesis).
        n_harmonics: number of harmonic oscillators.
        hidden_size: GRU hidden state dimension.
        decoder_type: decoder architecture name ("gru" or "rnn").
        use_reverb: whether to apply reverb in DDSPCore synthesis.
        stft_scales: list of FFT sizes for multi-scale spectral loss (informational;
            the actual loss uses its own fft_sizes to keep the model config decoupled
            from GPU-specific tunables).
    """

    sample_rate: int = 16000
    frame_size: int = 128
    n_harmonics: int = 60
    n_noise_bins: int = 32
    hidden_size: int = 256
    decoder_type: str = "gru"
    use_reverb: bool = True
    stft_scales: list[int] = None  # set in __post_init__

    def __post_init__(self) -> None:
        if self.stft_scales is None:
            object.__setattr__(self, "stft_scales", [512, 1024, 2048])


class DDSPModel(nn.Module):
    """DDSP model: GRU/RNN decoder conditioned on f0 + loudness, driving DDSP core synth.

    Takes per-frame f0 (Hz) and loudness (log energy) features, runs them
    through a GRU (or RNN in future), and produces harmonic amplitudes, harmonic
    distribution (softmax over H harmonics), and noise magnitudes. These parameters
    drive the internal DDSPCore to synthesize audio (with optional reverb).
    """

    def __init__(
        self,
        config: DDSPConfig,
        n_noise_bins: int | None = None,
    ) -> None:
        super().__init__()
        self.config = config
        n_noise_bins = n_noise_bins if n_noise_bins is not None else config.n_noise_bins

        input_dim = 2  # f0 + loudness

        self.gru = nn.GRU(
            input_size=input_dim,
            hidden_size=config.hidden_size,
            batch_first=True,
        )

        # Frame-level feature projection
        self.feature_proj = nn.Linear(config.hidden_size, config.hidden_size)

        # Outputs
        self.amplitude_out = nn.Linear(config.hidden_size, config.n_harmonics)
        self.distribution_out = nn.Linear(config.hidden_size, config.n_harmonics)
        self.noise_magnitudes_out = nn.Linear(config.hidden_size, n_noise_bins)

        self.ddsp_core = DDSPCore(
            n_harmonics=config.n_harmonics,
            sample_rate=config.sample_rate,
            hop_length=config.frame_size,
            use_reverb=config.use_reverb,
        )

        self.n_noise_bins = n_noise_bins

    def forward(
        self,
        f0: torch.Tensor,
        loudness: torch.Tensor,
    ) -> dict[str, torch.Tensor]:
        """Run the model.

        Args:
            f0: per-frame fundamental frequency in Hz, shape (B, T_frames).
            loudness: per-frame log energy, shape (B, T_frames).

        Returns:
            Dict with:
                - "amplitudes": (B, T_frames, H)
                - "harmonic_distribution": (B, T_frames, H), softmax over H
                - "magnitudes": (B, T_frames, n_noise_bins)
                - "audio": (B, T_audio)
        """
        B, T_frames = f0.shape

        # Stack conditioning features: (B, T_frames, 2)
        features = torch.stack([f0, loudness], dim=-1)

        # GRU encoder
        gru_out, _ = self.gru(features)  # (B, T_frames, hidden_size)

        # Project
        hidden = F.relu(self.feature_proj(gru_out))

        # Decode parameters
        raw_amplitudes = self.amplitude_out(hidden)
        # Bounded amplitudes via sigmoid
        amplitudes = torch.sigmoid(raw_amplitudes)

        raw_distribution = self.distribution_out(hidden)
        # Softmax over harmonics for each frame
        harmonic_distribution = F.softmax(raw_distribution, dim=-1)

        noise_raw = self.noise_magnitudes_out(hidden)
        # Bounded noise magnitudes via sigmoid
        magnitudes = torch.sigmoid(noise_raw)

        # Compute audio length from frames
        n_samples = (T_frames - 1) * self.config.frame_size + 1

        # Synthesize audio via DDSP core
        audio = self.ddsp_core(
            amplitudes=amplitudes,
            harmonic_distribution=harmonic_distribution,
            f0=f0,
            noise_magnitudes=magnitudes,
            n_samples=n_samples,
        )

        return {
            "amplitudes": amplitudes,  # (B, T_frames, H)
            "harmonic_distribution": harmonic_distribution,  # (B, T_frames, H)
            "magnitudes": magnitudes,  # (B, T_frames, n_noise_bins)
            "audio": audio,  # (B, n_samples)
        }
