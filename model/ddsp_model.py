"""DDSP model: GRU/RNN decoder conditioned on f0 + loudness, driving DDSP core synth."""

from __future__ import annotations

from dataclasses import dataclass

import torch
import torch.nn as nn
import torch.nn.functional as F

from model.ddsp import DDSPCore, DDSPVariant
from model.ddsp.newt import NEWTUnit, SawtoothExciter


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
        variant: DDSP variant to use (engine, LFO settings, etc.); if None, the
            __init__ parameter or a default DDSPVariant() is used.
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
    variant: DDSPVariant | None = None
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
        variant: DDSPVariant | None = None,
    ) -> None:
        super().__init__()
        self.config = config
        self.variant = variant or config.variant or DDSPVariant()
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

        self.sinusoidal_freqs_out: nn.Linear | None = None
        self.comb_magnitudes_out: nn.Linear | None = None
        self.voiced_out: nn.Linear | None = None

        if self.variant.engine == "sinusoidal":
            self.sinusoidal_freqs_out = nn.Linear(config.hidden_size, config.n_harmonics)
        elif self.variant.engine == "combsub":
            self.comb_magnitudes_out = nn.Linear(config.hidden_size, n_noise_bins)
            self.voiced_out = nn.Linear(config.hidden_size, 1)
        elif self.variant.engine == "newt":
            self.newt_gain_out = nn.Linear(config.hidden_size, 1)
            self.newt_bias_out = nn.Linear(config.hidden_size, 1)

        self.ddsp_core = DDSPCore(
            n_harmonics=config.n_harmonics,
            sample_rate=config.sample_rate,
            hop_length=config.frame_size,
            use_reverb=config.use_reverb,
            variant=self.variant,
        )

        self.n_noise_bins = n_noise_bins

        self.sawtooth: SawtoothExciter | None = None
        self.newt: NEWTUnit | None = None

        if self.variant.engine == "newt":
            self.sawtooth = SawtoothExciter()
            self.newt = NEWTUnit(
                n_hidden=self.variant.newt_n_hidden,
                n_layers=self.variant.newt_n_layers,
            )

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
            Dict with engine-dependent decoded parameters and synthesized audio.
        """
        B, T_frames = f0.shape

        # Stack conditioning features: (B, T_frames, 2)
        features = torch.stack([f0, loudness], dim=-1)

        # GRU encoder
        gru_out, _ = self.gru(features)  # (B, T_frames, hidden_size)

        # Project
        hidden = F.relu(self.feature_proj(gru_out))

        engine = self.variant.engine

        if engine == "sinusoidal":
            raw_amplitudes = self.amplitude_out(hidden)
            amplitudes = torch.sigmoid(raw_amplitudes)
            raw_freqs = self.sinusoidal_freqs_out(hidden)
            sinusoidal_freqs = torch.sigmoid(raw_freqs) * (self.config.sample_rate / 2)
            noise_raw = self.noise_magnitudes_out(hidden)
            magnitudes = torch.sigmoid(noise_raw)
            n_samples = (T_frames - 1) * self.config.frame_size + 1
            audio = self.ddsp_core(
                amplitudes=amplitudes,
                sinusoidal_freqs=sinusoidal_freqs,
                noise_magnitudes=magnitudes,
                n_samples=n_samples,
            )
            return {
                "amplitudes": amplitudes,
                "sinusoidal_freqs": sinusoidal_freqs,
                "magnitudes": magnitudes,
                "audio": audio,
            }

        if engine == "combsub":
            raw_mags = self.comb_magnitudes_out(hidden)
            magnitudes = torch.sigmoid(raw_mags)
            raw_voiced = self.voiced_out(hidden)
            voiced = torch.sigmoid(raw_voiced).squeeze(-1)
            n_samples = (T_frames - 1) * self.config.frame_size + 1
            audio = self.ddsp_core(
                noise_magnitudes=magnitudes,
                f0=f0,
                voiced=voiced,
                n_samples=n_samples,
            )
            return {
                "magnitudes": magnitudes,
                "voiced": voiced,
                "audio": audio,
            }

        if engine == "newt":
            gain_frames = torch.sigmoid(self.newt_gain_out(hidden)).squeeze(-1)
            bias_frames = torch.tanh(self.newt_bias_out(hidden)).squeeze(-1)

            n_samples = (T_frames - 1) * self.config.frame_size + 1
            gain_audio = F.interpolate(
                gain_frames.unsqueeze(1), size=n_samples, mode="linear", align_corners=False
            ).squeeze(1)
            bias_audio = F.interpolate(
                bias_frames.unsqueeze(1), size=n_samples, mode="linear", align_corners=False
            ).squeeze(1)

            excitation = self.sawtooth(f0, self.config.sample_rate, self.config.frame_size)
            harmonic_audio = self.newt(excitation, gain_audio, bias_audio)

            noise_raw = self.noise_magnitudes_out(hidden)
            magnitudes = torch.sigmoid(noise_raw)

            audio = self.ddsp_core(
                amplitudes=harmonic_audio.unsqueeze(-1),
                noise_magnitudes=magnitudes,
                n_samples=n_samples,
            )
            return {
                "gain_frames": gain_frames,
                "bias_frames": bias_frames,
                "magnitudes": magnitudes,
                "audio": audio,
            }

        # "harmonic" (default)
        raw_amplitudes = self.amplitude_out(hidden)
        amplitudes = torch.sigmoid(raw_amplitudes)
        raw_distribution = self.distribution_out(hidden)
        harmonic_distribution = F.softmax(raw_distribution, dim=-1)
        noise_raw = self.noise_magnitudes_out(hidden)
        magnitudes = torch.sigmoid(noise_raw)

        if self.variant.lfo_freq > 0:
            t = torch.arange(T_frames, device=f0.device, dtype=f0.dtype)
            t = t / self.config.sample_rate * self.config.frame_size
            lfo = 1.0 + self.variant.lfo_depth * torch.sin(2 * torch.pi * self.variant.lfo_freq * t)
            magnitudes = magnitudes * lfo.unsqueeze(-1)

        n_samples = (T_frames - 1) * self.config.frame_size + 1
        audio = self.ddsp_core(
            amplitudes=amplitudes,
            harmonic_distribution=harmonic_distribution,
            f0=f0,
            noise_magnitudes=magnitudes,
            n_samples=n_samples,
        )

        return {
            "amplitudes": amplitudes,
            "harmonic_distribution": harmonic_distribution,
            "magnitudes": magnitudes,
            "audio": audio,
        }

    def save_checkpoint(self, path: str) -> None:
        state = {
            "model_state_dict": self.state_dict(),
            "config": self.config,
            "engine": self.variant.engine,
        }
        torch.save(state, path)

    @classmethod
    def load_checkpoint(cls, path: str, variant: DDSPVariant | None = None) -> DDSPModel:
        import torch.serialization as _ts
        with _ts.safe_globals([DDSPConfig, DDSPVariant]):
            state = torch.load(path, map_location="cpu", weights_only=True)
        saved_engine = state.get("engine", "harmonic")
        if variant is None:
            variant = DDSPVariant(engine=saved_engine)
        elif variant.engine != saved_engine:
            raise ValueError(
                f"Checkpoint engine '{saved_engine}' does not match "
                f"requested engine '{variant.engine}'"
            )
        config = state["config"]
        if not isinstance(config, DDSPConfig):
            config = DDSPConfig(**config)
        model = cls(config=config, variant=variant)
        model.load_state_dict(state["model_state_dict"])
        return model
