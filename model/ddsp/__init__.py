"""DDSP differentiable synthesizer modules (self-owned, not the external ddsp lib)."""

from .combsub import CombSubSynth
from .sinusoidal import SinusoidalSynth
from .synths import (
    DDSPCore,
    FilteredNoiseSynth,
    HarmonicOscillatorSynth,
    SimpleReverb,
)
from .variant import DDSPVariant

__all__ = [
    "CombSubSynth",
    "DDSPCore",
    "DDSPVariant",
    "FilteredNoiseSynth",
    "HarmonicOscillatorSynth",
    "SimpleReverb",
    "SinusoidalSynth",
]
