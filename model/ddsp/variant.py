from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


@dataclass
class DDSPVariant:
    """Opt-in synthesis hacks for the DDSP core.

    All fields default to the standard (no-op) behaviour so existing
    checkpoints are unaffected when no variant is supplied.
    """

    # --- M8.2 Inharmonic multipliers ---
    harmonic_ratios: list[float] | None = None

    # --- M8.3a Waveform function ---
    waveform: Literal["sin", "square", "saw"] = "sin"

    # --- M8.3b Phase distortion (Casio CZ-style) ---
    pd_k: float = 0.0

    # --- M8.3c Trainable wavetable ---
    use_trainable_wavetable: bool = False

    # --- M8.2b FM synthesis ---
    fm_depth: float = 0.0
    fm_ratio: float = 2.0

    # --- M8.4.1 Spectral-loss band mask ---
    loss_band_mask: list[tuple[float, float]] | None = None

    # --- M8.4.2 LFO injection ---
    lfo_freq: float = 0.0
    lfo_depth: float = 0.0

    # --- M8.6 Angular cumulative sum (phase-drift fix) ---
    use_angular_cumsum: bool = False

    # --- M9.1 Engine selector ---
    engine: Literal["harmonic", "sinusoidal", "combsub"] = "harmonic"

    # --- M9.4 Colored noise source ---
    noise_color: Literal["white", "pink", "brown"] = "white"

    # --- M9.5 Granular noise jitter ---
    noise_grain_jitter: float = 0.0

    def is_default(self) -> bool:
        return (
            self.harmonic_ratios is None
            and self.waveform == "sin"
            and self.pd_k == 0.0
            and not self.use_trainable_wavetable
            and self.fm_depth == 0.0
            and self.loss_band_mask is None
            and self.lfo_freq == 0.0
            and not self.use_angular_cumsum
            and self.engine == "harmonic"
            and self.noise_color == "white"
            and self.noise_grain_jitter == 0.0
        )

    @classmethod
    def from_dict(cls, d: dict) -> DDSPVariant:
        from dataclasses import fields

        known = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in d.items() if k in known})
