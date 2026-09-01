"""Tests for MIDI utility functions in model/midi_utils.py."""

import torch

from model.midi_utils import (
    MidiVoiceAllocator,
    generate_f0_frames,
    generate_loudness_frames,
    midi_note_to_hz,
    velocity_to_loudness_db,
)

# ---------------------------------------------------------------------------
# midi_note_to_hz
# ---------------------------------------------------------------------------


def test_midi_note_to_hz_a4() -> None:
    assert midi_note_to_hz(69) == 440.0


def test_midi_note_to_hz_c4() -> None:
    c4 = midi_note_to_hz(60)
    assert abs(c4 - 261.63) < 0.01


def test_midi_note_to_hz_note0() -> None:
    n0 = midi_note_to_hz(0)
    assert abs(n0 - 8.18) < 0.01


def test_midi_note_to_hz_note127() -> None:
    n127 = midi_note_to_hz(127)
    assert abs(n127 - 12543.85) < 0.01


def test_midi_note_to_hz_monotonic() -> None:
    prev = midi_note_to_hz(0)
    for note in range(1, 128):
        cur = midi_note_to_hz(note)
        assert cur > prev
        prev = cur


# ---------------------------------------------------------------------------
# velocity_to_loudness_db
# ---------------------------------------------------------------------------


def test_velocity_to_loudness_db_zero() -> None:
    assert velocity_to_loudness_db(0) == -60.0


def test_velocity_to_loudness_db_max() -> None:
    assert velocity_to_loudness_db(127) == 0.0


def test_velocity_to_loudness_db_mid() -> None:
    db = velocity_to_loudness_db(64)
    assert abs(db - (-29.76)) < 0.5


def test_velocity_to_loudness_db_clamped_below() -> None:
    assert velocity_to_loudness_db(-5) == -60.0


def test_velocity_to_loudness_db_clamped_above() -> None:
    assert velocity_to_loudness_db(200) == 0.0


# ---------------------------------------------------------------------------
# generate_f0_frames
# ---------------------------------------------------------------------------


def test_generate_f0_frames_shape() -> None:
    gate = torch.ones(10)
    f0 = generate_f0_frames(440.0, gate, 10, 2, 3)
    assert f0.shape == (10,)


def test_generate_f0_frames_all_gate_1_sustain_after_attack() -> None:
    n_frames = 10
    attack = 2
    gate = torch.ones(n_frames)
    f0 = generate_f0_frames(440.0, gate, n_frames, attack, 3)
    # Frames 0..attack-1 ramp; frames attack..end sustain at note_hz.
    for i in range(attack, n_frames):
        assert f0[i].item() == 440.0


def test_generate_f0_frames_attack_ramp() -> None:
    n_frames = 5
    attack = 5
    gate = torch.ones(n_frames)
    f0 = generate_f0_frames(100.0, gate, n_frames, attack, 2)
    # frac = (j - 0) / attack
    for j in range(n_frames):
        expected = 100.0 * (j / attack)
        assert abs(f0[j].item() - expected) < 1e-6


def test_generate_f0_frames_gate_transition_1_to_0_release_ramp() -> None:
    # 4 frames of gate=1 (attack=2, sustain 2), then gate drops to 0 with release=3.
    n_frames = 7
    attack = 2
    release = 3
    gate = torch.tensor([1.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0])
    f0 = generate_f0_frames(100.0, gate, n_frames, attack, release)
    # After attack, sustain 100.0 for frames 2..3.
    assert f0[2].item() == 100.0
    assert f0[3].item() == 100.0
    # Release ramp: frame 4 frac=0/3 -> 100*(1-0)=100,
    # frame 5 frac=1/3 -> 100*(1-1/3)=66.67,
    # frame 6 frac=2/3 -> 100*(1-2/3)=33.33.
    assert abs(f0[4].item() - 100.0) < 1e-6
    assert abs(f0[5].item() - 66.6667) < 1e-4
    assert abs(f0[6].item() - 33.3333) < 1e-4
    # Last frame should not reach 0 because release spans only 3 frames.
    assert f0[6].item() > 0.0


def test_generate_f0_frames_empty() -> None:
    f0 = generate_f0_frames(440.0, torch.empty(0), 0, 2, 3)
    assert f0.numel() == 0


def test_generate_f0_frames_gate_length_mismatch() -> None:
    gate = torch.ones(5)
    try:
        generate_f0_frames(440.0, gate, 3, 2, 2)
    except ValueError:
        pass
    else:
        raise AssertionError("Expected ValueError for gate/n_frames mismatch")


# ---------------------------------------------------------------------------
# generate_loudness_frames
# ---------------------------------------------------------------------------


def test_generate_loudness_frames_shape() -> None:
    gate = torch.ones(8)
    loud = generate_loudness_frames(-20.0, gate, 8, 2, 3)
    assert loud.shape == (8,)


def test_generate_loudness_frames_sustain_level() -> None:
    n_frames = 6
    attack = 2
    gate = torch.ones(n_frames)
    loud = generate_loudness_frames(-30.0, gate, n_frames, attack, 3)
    for i in range(attack, n_frames):
        assert loud[i].item() == -30.0


def test_generate_loudness_frames_release_floor() -> None:
    # 2 frames gate=1, then release long enough to reach floor.
    n_frames = 5
    attack = 2
    release = 3
    gate = torch.tensor([1.0, 1.0, 0.0, 0.0, 0.0])
    loud = generate_loudness_frames(-30.0, gate, n_frames, attack, release)
    # At end of release ramp (frame 4, frac=2/3) loud = -30 - (30)*2/3 = -50.
    # So it does not reach -60 in 3 frames; test floor isn't reached early.
    assert loud[0].item() == 0.0  # frac 0/2 * -30
    assert loud[1].item() == -15.0  # frac 0.5/2 * -30
    assert loud[2].item() == -30.0  # start of release at frac 0
    assert loud[4].item() == -50.0  # -30 - 30*(2/3)
    assert loud[4].item() > -60.0


def test_generate_loudness_frames_gate_length_mismatch() -> None:
    gate = torch.ones(6)
    try:
        generate_loudness_frames(-20.0, gate, 4, 2, 2)
    except ValueError:
        pass
    else:
        raise AssertionError("Expected ValueError for gate/n_frames mismatch")


# ---------------------------------------------------------------------------
# MidiVoiceAllocator
# ---------------------------------------------------------------------------


def test_midi_voice_allocator_allocate_returns_voice0_first() -> None:
    alloc = MidiVoiceAllocator(n_voices=4)
    voice = alloc.allocate(60)
    assert voice == 0


def test_midi_voice_allocator_two_notes_returns_0_and_1() -> None:
    alloc = MidiVoiceAllocator(n_voices=4)
    v0 = alloc.allocate(60)
    v1 = alloc.allocate(64)
    assert v0 == 0
    assert v1 == 1


def test_midi_voice_allocator_release_frees_voice() -> None:
    alloc = MidiVoiceAllocator(n_voices=2)
    v = alloc.allocate(60)
    assert v == 0
    alloc.release(60)
    # Voice 0 should be free again.
    v2 = alloc.allocate(67)
    assert v2 == 0


def test_midi_voice_allocator_reallocate_reuses_freed_voice() -> None:
    alloc = MidiVoiceAllocator(n_voices=2)
    alloc.release(60)
    v1 = alloc.allocate(67)
    assert v1 == 0


def test_midi_voice_allocator_steals_oldest_when_all_busy() -> None:
    alloc = MidiVoiceAllocator(n_voices=2)
    v0 = alloc.allocate(60)
    v1 = alloc.allocate(64)
    assert v0 == 0
    assert v1 == 1
    # Both busy; allocate another note -> steals oldest (voice 0, allocated first).
    v2 = alloc.allocate(72)
    assert v2 == 0


def test_midi_voice_allocator_reset_clears_all() -> None:
    alloc = MidiVoiceAllocator(n_voices=3)
    alloc.allocate(60)
    alloc.allocate(64)
    alloc.reset()
    # After reset, allocate should return voice 0.
    v = alloc.allocate(72)
    assert v == 0
