"""MIDI utility functions for DDSP MIDI synth mode.

Provides note-to-frequency, velocity-to-loudness mapping, frame generation
from MIDI note events, and a round-robin voice allocator for polyphonic models.

No extra dependencies beyond Python + torch.
"""

from __future__ import annotations

import torch


def midi_note_to_hz(note: int) -> float:
    """MIDI note number to fundamental frequency in Hz.

    A4 (note 69) = 440 Hz. Formula: 440 * 2^((note-69)/12).

    Args:
        note: MIDI note number (0-127). Note 0 is a valid MIDI key (C-1,
            ~8.18 Hz); it is handled like any other note.
    Returns:
        Frequency in Hz.
    """
    return 440.0 * (2.0 ** ((note - 69) / 12.0))


def velocity_to_loudness_db(velocity: int, min_db: float = -60.0, max_db: float = 0.0) -> float:
    """MIDI velocity (0-127) to loudness in dB.

    Linear mapping from (0, 127) to (min_db, max_db). Velocity 0 maps to
    min_db; velocity 127 maps to max_db.

    Args:
        velocity: MIDI velocity (0-127).
        min_db: Loudness in dB at velocity 0. Default -60.0.
        max_db: Loudness in dB at velocity 127. Default 0.0.
    Returns:
        Loudness in dB.
    """
    if velocity <= 0:
        return min_db
    if velocity >= 127:
        return max_db
    return min_db + (velocity / 127.0) * (max_db - min_db)


def generate_f0_frames(
    note_hz: float,
    gate: torch.Tensor,
    n_frames: int,
    attack_frames: int,
    release_frames: int,
) -> torch.Tensor:
    """Generate per-frame f0 tensor from a note + gate signal.

    f0 = note_hz where gate is 1 (after an attack ramp-up), with a linear
    attack ramp from 0 to note_hz and a linear release ramp from note_hz to
    0. Returns shape (n_frames,).

    Args:
        note_hz: Fundamental frequency in Hz for the held note.
        gate: 1D torch.Tensor of length n_frames with values 0.0 or 1.0.
        n_frames: Number of analysis frames (must match gate length).
        attack_frames: Attack time in frames (ramp from 0 to note_hz).
        release_frames: Release time in frames (ramp from note_hz to 0).
    Returns:
        1D torch.Tensor of shape (n_frames,).
    """
    if n_frames <= 0:
        return torch.empty(0, dtype=torch.float32)

    if gate.shape[0] != n_frames:
        raise ValueError(f"gate length {gate.shape[0]} != n_frames {n_frames}")

    result = torch.zeros((n_frames,), dtype=torch.float32)
    i = 0
    while i < n_frames:
        g = float(gate[i].item())
        if g == 1.0:
            # Attack ramp.
            a_end = min(n_frames, i + attack_frames)
            for j in range(i, a_end):
                frac = (j - i) / max(1, attack_frames)
                result[j] = note_hz * frac
            i = a_end
            # Sustain.
            while i < n_frames and float(gate[i].item()) == 1.0:
                result[i] = note_hz
                i += 1
            # Release ramp at the end of this on-region.
            if i < n_frames:
                r_start = i
                r_end = min(n_frames, i + release_frames)
                for j in range(r_start, r_end):
                    frac = (j - r_start) / max(1, release_frames)
                    result[j] = note_hz * (1.0 - frac)
                i = r_end
        else:
            i += 1
    return result


def generate_loudness_frames(
    velocity_db: float,
    gate: torch.Tensor,
    n_frames: int,
    attack_frames: int,
    release_frames: int,
) -> torch.Tensor:
    """Loudness envelope from gate (ADSR-like, A+R only).

    Linear attack ramp from 0 to velocity_db, linear release ramp from
    velocity_db to -60 dB. Returns shape (n_frames,).

    Args:
        velocity_db: Loudness in dB at full velocity (gate=1 held).
        gate: 1D torch.Tensor of length n_frames with values 0.0 or 1.0.
        n_frames: Number of analysis frames (must match gate length).
        attack_frames: Attack time in frames.
        release_frames: Release time in frames.
    Returns:
        1D torch.Tensor of shape (n_frames,).
    """
    if n_frames <= 0:
        return torch.empty(0, dtype=torch.float32)

    if gate.shape[0] != n_frames:
        raise ValueError(f"gate length {gate.shape[0]} != n_frames {n_frames}")

    release_floor = -60.0
    result = torch.zeros((n_frames,), dtype=torch.float32)

    i = 0
    while i < n_frames:
        g = float(gate[i].item())
        if g == 1.0:
            # Attack ramp.
            a_end = min(n_frames, i + attack_frames)
            for j in range(i, a_end):
                frac = (j - i) / max(1, attack_frames)
                result[j] = velocity_db * frac
            i = a_end
            # Sustain.
            while i < n_frames and float(gate[i].item()) == 1.0:
                result[i] = velocity_db
                i += 1
            # Release ramp.
            if i < n_frames:
                r_start = i
                r_end = min(n_frames, i + release_frames)
                span = velocity_db - release_floor
                for j in range(r_start, r_end):
                    frac = (j - r_start) / max(1, release_frames)
                    result[j] = velocity_db - span * frac
                i = r_end
        else:
            i += 1
    return result


class MidiVoiceAllocator:
    """Round-robin voice allocation for PolyDDSP (N voices, first-fit).

    Manages a pool of N voices. Each voice can be 'free' or 'busy'. On
    note-on, the allocator returns the first free voice index (marking it
    busy) or, if none is free, steals the oldest busy voice. On note-off,
    the matching voice is freed.

    Attributes:
        n_voices: Total number of voices in the pool.
        note_to_voice: Mapping from held note (MIDI note number) to voice
            index, for releasing the correct voice on note-off.
    """

    def __init__(self, n_voices: int = 4) -> None:
        """Initialize a voice pool.

        Args:
            n_voices: Number of voices to manage. Default 4.
        """
        self.n_voices = max(1, n_voices)
        self._busy: list[bool] = [False] * self.n_voices
        # LRU-ish ordering: maintain a list of busy voice indices in order of
        # allocation; oldest = first element.
        self._busy_order: list[int] = []
        # Note -> voice mapping for correct release. A note can be held by
        # at most one voice at a time (monophonic-per-note assumption).
        self.note_to_voice: dict[int, int] = {}

    def allocate(self, note_on: int) -> int | None:
        """Allocate a voice for a MIDI note-on event.

        Args:
            note_on: MIDI note number being turned on.
        Returns:
            Voice index (0..N-1) if a voice is available, or None if all
            voices are busy and cannot be stolen (should not happen for
            n_voices >= 1; kept for forward compatibility).
        """
        # First: check if already allocated (re-trigger same note -> reuse).
        if note_on in self.note_to_voice:
            voice = self.note_to_voice[note_on]
            if self._busy[voice]:
                return voice

        # First-fit: find first free voice.
        for idx in range(self.n_voices):
            if not self._busy[idx]:
                self._claim(idx, note_on)
                return idx

        # All busy: steal oldest.
        if self._busy_order:
            oldest = self._busy_order.pop(0)
            self._release_internal(oldest)
            self._claim(oldest, note_on)
            return oldest

        return None

    def release(self, note_off: int) -> None:
        """Release the voice holding a MIDI note-off event.

        Args:
            note_off: MIDI note number being turned off.
        """
        if note_off in self.note_to_voice:
            voice = self.note_to_voice.pop(note_off)
            self._release_internal(voice)

    def reset(self) -> None:
        """Free all voices and clear mappings."""
        self._busy = [False] * self.n_voices
        self._busy_order.clear()
        self.note_to_voice.clear()

    def _claim(self, voice: int, note: int) -> None:
        self._busy[voice] = True
        self._busy_order.append(voice)
        self.note_to_voice[note] = voice

    def _release_internal(self, voice: int) -> None:
        self._busy[voice] = False
        if voice in self._busy_order:
            self._busy_order.remove(voice)
