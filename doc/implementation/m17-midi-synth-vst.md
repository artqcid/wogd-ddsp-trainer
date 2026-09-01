---
type: implementation-plan
title: M17 — MIDI Synth VST Export
description: Feasibility analysis + implementation plan for MIDI synthesizer export mode (all tiers). Training unchanged; export-only new wrapper. Tier-by-tier assessment, new MidiSynthWrapper, Usage Mode selector in UI.
status: draft
generated:
  by: build
  at: 2026-09-02
stale_after: 2027-06-01
tags: [midi, synth-vst, export, inference, wrapper, milestone]
---

# M17 — MIDI Synth VST Export

_Full feasibility analysis + granular implementation steps._
_Related: [`architecture.md`](../architecture.md), [`parameter-handling.md`](../parameter-handling.md),
[`handbook.md`](../handbook.md), [`implementation/m15-param-manifest.md`](./m15-param-manifest.md),
[`implementation/m16-param-builder-ui.md`](./m16-param-builder-ui.md)._

---

## 1. Feasibility Analysis

### 1.1 Core question

Can WOGD DDSP-trained models be used as **MIDI synthesizer VSTs** — in addition to
(or instead of) the current Audio FX VST export?

### 1.2 Answer: Yes — for all tiers

The DDSP decoder (`DDSPModel.forward`) is conditioned on two per-frame signals:

```
f0:       (B, T_frames)   — fundamental frequency in Hz per frame
loudness: (B, T_frames)   — log-energy / loudness per frame
```

In the **Audio FX** path these frames come from **real-time audio analysis** of
the incoming audio signal (pitch tracker + loudness meter):

```
[Input Audio] → [F0 + Loudness extractor] → [DDSP Decoder] → [Output Audio]
```

In a **MIDI Synth** path the same frames come from **MIDI note events** —
no audio analysis needed at runtime:

```
[MIDI events] → [MIDI → f0/loudness frame generator] → [DDSP Decoder] → [Output Audio]
```

MIDI → Hz conversion is exact arithmetic (`440 × 2^((note−69)/12)`).
MIDI velocity → loudness_db is a configurable mapping.

**The trained model weights are identical in both modes.** No retraining,
no separate training path. MIDI mode is a pure **inference/export wrapper** change.

### 1.3 Why MIDI mode is possible without training changes

DDSP was designed as a differentiable synthesizer: the decoder IS a synth
conditioned on pitch + loudness. The "Audio FX" usage pattern (feeding it
features from live audio) is only one of its intended operating modes. The
DDSP paper (Engel et al. 2020) explicitly conditions on f0 + loudness; MIDI
is just an alternative source for those same signals.

### 1.4 Training-time recommendation (optional, not required)

For the best MIDI synth quality, the training audio can be **pitch-quantized
to semitone grid** (already possible via the M7.1 pitch-curve editor →
"Quantize to semitones"). This trains the model on exactly-pitched frames that
better match discrete MIDI note frequencies. This is an optional hint in the
UI, not a code change.

---

## 2. Tier-by-tier assessment

| Tier | MIDI Synth support | Value | Notes |
|---|---|---|---|
| 🟢 `standard` | ✅ Full | Moderate | Monophonic. Clean vocal/instrument timbre via MIDI. |
| 🔵 `component` | ✅ Full | Moderate+ | Harmonic/Noise Blend knobs add expressive live control. |
| 🟡 `hacks` | ✅ **Highlighted** | **High** | FM synth, wavetable, phase distortion, LFO → classic synth territory. Most compelling MIDI use case. |
| 🟣 `engine/harmonic` | ✅ Full | Moderate | Same as standard via engine path. |
| 🟣 `engine/sinusoidal` | ✅ **Highlighted** | **High** | Glass, bell, marimba-like inharmonic instruments via MIDI. |
| 🟣 `engine/combsub` | ✅ **Highlighted** | **High** | Resonant body instruments: plucked string, sitar, oud via MIDI. |
| 🟣 `engine/newt` | ✅ **Highlighted** | **High** | Neural waveshaping timbres — unique synth character. |
| 🔴 `advanced/VAE` | ✅ **Premium** | **Very High** | Timbre-morphing synth: MIDI notes + latent Z sliders blend timbres in real time. Unique differentiator. |
| 🔴 `advanced/Poly` | ✅ **Premium** | **High** | Natural fit: each MIDI note → one PolyDDSP voice (up to 4-note chords). |
| 🔴 `advanced/VC` | ⚠️ Hybrid only | Medium | MIDI drives pitch; content encoder still requires a reference audio sample for timbre. "Pitched Voice Conversion" mode. |

### Visual: two export paths per trained model

```
Checkpoint (.pt)
    │
    ├─► Audio FX Export (.nm / .pt)          ← existing today
    │       [Input Audio] → [F0+Loudness] → [DDSP Decoder] → [Audio]
    │       Neutone FX: ≤ 4 params
    │       Custom VST: ≤ 16 params
    │
    └─► MIDI Synth Export (.pt)              ← NEW (M17)
            [MIDI Events] → [f0/loudness frames] → [DDSP Decoder] → [Audio]
            Custom VST: ≤ 16 params (MIDI-specific param set)
            Standard: monophonic
            advanced/Poly: N-voice polyphonic
```

---

## 3. New components overview

| Component | File | Description |
|---|---|---|
| MIDI utilities | `model/midi_utils.py` (NEW) | Note→Hz, velocity→dB, frame generation, envelope, voice allocator |
| MIDI synth wrapper | `inference/midi_synth_wrapper.py` (NEW) | TorchScript-compatible synth wrapper; monophonic + polyphonic |
| Export function | `inference/export.py` (extend) | `export_midi_synth()` |
| REST endpoint | `server/routes/inference.py` (extend) | `POST .../export/midi-synth` |
| ParamManifest | `model/param_manifest.py` (extend) | MIDI-specific param context + default builders |
| UI: Usage Mode | `webui/src/components/WizardModal.vue` (extend) | Step 3: Usage Mode selector (Audio FX / MIDI Synth / Both) |
| UI: Export button | `webui/src/views/ModelExportView.vue` (extend) | "Export → MIDI Synth (.pt)" button |
| UI: MIDI Preview | `webui/src/views/InferencePlaygroundView.vue` (extend) | Virtual keyboard for offline MIDI preview render |
| Store | `webui/src/stores/modelConfig.js` (extend) | `synthesisMode` field |

---

## 4. MIDI inference parameters (new param context)

MIDI synth exports get a **new set of inference params** alongside (or replacing) the
audio-FX params. These are stored in the `param_manifest` as a separate `context`:

| Slot | Name | Type | Min | Max | Default | Description |
|---|---|---|---|---|---|---|
| 1 | `Pitch Shift` | continuous | −24 | +24 | 0 | Semitone offset from MIDI note |
| 2 | `Velocity Sensitivity` | continuous | 0 | 1 | 0.7 | How strongly MIDI velocity affects loudness |
| 3 | `Attack` | continuous | 1 | 500 | 10 | Envelope attack in ms |
| 4 | `Release` | continuous | 10 | 2000 | 150 | Envelope release in ms |
| 5 | `Pitch Bend Range` | continuous | 1 | 24 | 2 | Pitch bend wheel range in semitones |
| 6 | `Noise Level` | continuous | 0 | 1 | 0.5 | (standard/component/hacks) |
| 7+ | tier-specific | — | — | — | — | Harmonic Blend, FM Depth, Timbre Z1… etc. |

The first 5 slots are **universal MIDI params** present in every MIDI synth export.
Slots 6+ carry the same tier-specific params as the audio FX export.

---

## 5. Granular implementation steps

### Phase 1 — Backend

#### M17.1 — `model/midi_utils.py` (NEW)

```python
def midi_note_to_hz(note: int) -> float:
    """MIDI note number to fundamental frequency in Hz."""


def velocity_to_loudness_db(velocity: int, min_db: float = -60.0, max_db: float = 0.0) -> float:
    """MIDI velocity (0–127) to loudness in dB."""


def generate_f0_frames(
    note_hz: float,
    gate: torch.Tensor,
    n_frames: int,
    attack_frames: int,
    release_frames: int,
) -> torch.Tensor:
    """Generate per-frame f0 tensor from a note + gate signal."""


def generate_loudness_frames(
    velocity_db: float,
    gate: torch.Tensor,
    n_frames: int,
    attack_frames: int,
    release_frames: int,
) -> torch.Tensor:
    """Loudness envelope from gate (ADSR-like, A+R only)."""


class MidiVoiceAllocator:
    """Round-robin voice allocation for PolyDDSP (N voices, first-fit)."""
```

Tests: `tests/test_midi_utils.py` — note_to_hz accuracy (A4=440Hz, C4=261.63 Hz),
velocity mapping (0→min_db, 127→max_db), frame generation shape, voice allocator.

#### M17.2 — `inference/midi_synth_wrapper.py` (NEW)

TorchScript-compatible `MidiSynthWrapper(nn.Module)`:

```python
class MidiSynthWrapper(nn.Module):
    """Wraps a trained DDSPModel for MIDI synthesizer inference.

    Input: per-frame MIDI data (note_hz, loudness_db, gate).
    Output: synthesized audio.

    Compatible with DDSPModel (all tiers) and PolyDDSPModel.
    """

    def forward(
        self,
        note_hz: torch.Tensor,  # (T_frames,) — Hz per frame
        loudness_db: torch.Tensor,  # (T_frames,) — loudness per frame
        latent_z: torch.Tensor | None = None,  # (latent_dim,) — for VAE tier
    ) -> torch.Tensor:  # audio waveform
        ...
```

Handles:
- Monophonic (standard / component / hacks / engine)
- VAE latent z passthrough (advanced/VAE)
- Multi-voice routing via `MidiVoiceAllocator` (advanced/Poly)
- Pitch bend offset on note_hz

Tests: `tests/test_midi_synth_wrapper.py` — shape, monophonic output, VAE z routing,
poly routing (2 voices), TorchScript traceability (`torch.jit.trace` / `torch.jit.script`).

#### M17.3 — `inference/export.py` extend

New function `export_midi_synth(run_id, checkpoint_path, manifest) → Path`:
- Loads DDSPModel/PolyDDSPModel from checkpoint
- Wraps in `MidiSynthWrapper`
- Embeds `param_manifest` (MIDI context) + `"synth_mode": "midi_synth"` in metadata
- `torch.jit.script(wrapper)` → saves `.pt`

Tests: `tests/test_export_midi_synth.py` — export succeeds, metadata present,
loaded script produces audio from fake MIDI frames.

#### M17.4 — REST endpoint `POST .../export/midi-synth`

```
POST /api/runs/{run_id}/checkpoints/{checkpoint}/export/midi-synth
Body: { "params": [...] }   ← same shape as audio FX export
→ 202 Accepted + job_id → artifact: model_midi.pt
```

Tests: `tests/test_export_midi_synth_endpoint.py` — 202 on valid run,
404 on missing checkpoint, 409 on tier-mismatch.

#### M17.5 — `server/routes/training.py` extend

Add optional `synthesis_mode: str = "audio_fx"` to `RunCreateRequest`
(allowed values: `"audio_fx"`, `"midi_synth"`, `"both"`).
Stored in the run record for UI display. **No training logic change.**

#### M17.6 — `model/param_manifest.py` extend (depends on M15.1–M15.2)

- Add `context: str = "audio_fx"` field to `ParamManifest`
  (allowed: `"audio_fx"`, `"midi_synth"`).
- New builder `_midi_synth_manifest(model_tier, variant_flags) → ParamManifest`
  prepending the 5 universal MIDI params + tier-specific tail.
- Extend `build_default_manifest` with `context` parameter.

#### M17.7 — Tests (suite completion)

- `ruff check`, `ruff format --check`, `pytest` all green.

---

### Phase 2 — UI

#### M17.8 — Wizard: Usage Mode selector

`WizardModal.vue` Step 3 (currently "Target Mode"): extend or add a new
**Usage Mode** card group:

| Card | Icon | Description |
|---|---|---|
| Audio FX VST | 🎛 | Process incoming audio; Neutone FX or Custom VST |
| MIDI Synth VST | 🎹 | Play the model via MIDI notes; Custom VST (≥ hacks highlighted) |
| Both | ↔ | Export both wrappers from the same checkpoint |

`synthesisMode` stored in `modelConfig` Pinia store (M17.9).
No effect on training — purely an export/UI hint.

From `hacks` tier upward, the "MIDI Synth" card shows a **"Recommended for this tier"**
badge. For `standard`/`component` it is available but not highlighted.

For `advanced/VC` a special note: "Hybrid mode — MIDI drives pitch; a reference
audio file sets the timbre."

#### M17.9 — `modelConfig.js` Pinia store extend

```js
synthesisMode: 'audio_fx', // 'audio_fx' | 'midi_synth' | 'both'
```

Action: `setSynthesisMode(mode)`. Store value reflected in:
- Wizard step display
- Export button visibility
- TrainingConfigView header badge

#### M17.10 — `ModelExportView.vue` extend

New export section visible when `synthesisMode` is `"midi_synth"` or `"both"`:

```
[ Export → Audio FX (.nm)     ]   ← Neutone, always
[ Export → Audio FX (.pt)     ]   ← Custom VST, always
[ Export → MIDI Synth (.pt)   ]   ← NEW — visible when midi_synth selected
```

The MIDI Synth section shows the MIDI-specific param cards (Attack, Release,
Velocity Sensitivity, etc.) via an adapted `ModelParameterBuilder` with
`context="midi_synth"`.

#### M17.11 — Training hint in `TrainingConfigView`

When `synthesisMode === 'midi_synth'` or `'both'`:
- Show an info banner in the Core/Dataset section:
  _"Tip: For best MIDI synth results, quantize the training audio F0 to
  semitones in the preprocessing step (Dataset → Preprocessing → Pitch Curve Editor)."_
- Link to M7.1 pitch-curve editor

#### M17.12 — MIDI Preview in `InferencePlaygroundView`

A new "MIDI Preview" tab (alongside existing "Synthesize"):
- Mini virtual keyboard (1–2 octaves, click-to-play)
- Note triggers offline render: sends selected note + velocity to
  `POST /api/inference/synthesize-midi` (new endpoint, returns audio)
- Shows rendered audio waveform + play button (A/B playback)
- **Does not require real-time audio**: purely offline render for preview

New backend endpoint:
```
POST /api/inference/synthesize-midi
Body: { run_id, checkpoint, note, velocity, duration_s, params }
→ 202 + job_id → artifact: wav
```

#### M17.13 — Tier-specific MIDI hints in `TabHacks` / `TabEngine` / `TabAdvanced`

Small info box per relevant tab when `synthesisMode === 'midi_synth'` or `'both'`:

- **TabHacks:** "FM hack → FM synthesizer; Wavetable → wavetable synth; Phase Distortion → CZ-style synth; LFO → vibrato/tremolo."
- **TabEngine/sinusoidal:** "Produces glass, bell, marimba-like inharmonic timbres via MIDI."
- **TabEngine/combsub:** "Resonant body character — plucked strings, oud, sitar textures."
- **TabEngine/newt:** "Neural waveshaping — unique distorted synth character."
- **TabAdvanced/VAE:** "Latent Z sliders morph the timbre in real time while playing MIDI. Unique expressive instrument."
- **TabAdvanced/Poly:** "Each MIDI note routes to one PolyDDSP voice (up to N). Enables polyphonic chords."
- **TabAdvanced/VC:** "Hybrid mode: MIDI drives pitch, a reference audio sample sets the source timbre."

#### M17.14 — Vitest coverage

New + extended tests:
- `tests/WizardModal.test.js` — Usage Mode step renders, mode selection, badge on ≥ hacks
- `tests/ModelExportView.test.js` — MIDI Synth export button shown/hidden per synthesisMode
- `tests/InferencePlaygroundView.test.js` — MIDI Preview tab renders, keyboard click → render trigger
- All with `MockApiClient` + fixtures; no backend required

---

## 6. Risks & mitigations

| Risk | Severity | Mitigation |
|---|---|---|
| TorchScript traceability of `MidiSynthWrapper` | Medium | Test `torch.jit.trace`/`torch.jit.script` in M17.2 tests; avoid Python-only types |
| F0 range mismatch (MIDI notes vs. training range) | Low–Medium | Emit a warning during export if the model was trained on a narrow F0 range |
| PolyDDSP voice allocation complexity | Medium | Start with monophonic M17.2; extend poly in M17.2b (optional, separate step) |
| M15 not yet complete (ParamManifest) | Medium | M17.6 can use minimal stubs if M15.1–M15.2 are not done; add manifest later |
| Custom VST host must support MIDI input | High | Our own Custom VST (DAW plugin) must be updated to support the new MidiSynthWrapper interface — coordinate with Custom VST plugin dev |

---

## 7. Dependencies

| Dependency | Status |
|---|---|
| M15 `ParamManifest` (M15.1–M15.3) | Partially complete (M15.9 done; M15.1–M15.8 open) — M17.6 depends on this |
| M16 `ModelParameterBuilder` UI | Mostly complete — M17.10 reuses the component |
| M14 Dual-Mode UI | Complete — `modelConfig` store and `WizardModal` are extended |
| Custom VST DAW plugin (separate project) | Must be updated to accept the MIDI synth wrapper interface |

---

## History

_Append-only. Newest first._

- 2026-09-02: Feasibility analysis completed; M17 draft created by BUILD (sequential-thinking MCP).
  Conclusion: all tiers support MIDI synth; training unchanged; export-only milestone.
  Highlighted tiers: hacks (FM/wavetable/PD synths), engine (sinusoidal/combsub/NEWT),
  advanced/VAE (timbre-morphing), advanced/Poly (polyphonic MIDI).
- 2026-09-02: M17 implemented by subagent chain (DEV → general subagents).
  Phase 1 backend: midi_utils.py, MidiSynthWrapper, param_manifest context/`_midi_synth_manifest`,
  export_midi_synth(), REST endpoints (export/midi-synth, synthesize-midi), synthesis_mode in training.
  Phase 2 UI: modelConfig synthesisMode, WizardModal Usage Mode, ModelExportView MIDI button,
  TrainingConfigView hint, InferencePlaygroundView MIDI Preview (virtual keyboard),
  TabHacks/TabEngine/TabAdvanced MIDI hints.
  Fixes: neutone_slot=None for MIDI params (Custom VST only), removed latent_z from wrapper
  (VAE latent is internal), poly wrapper uses PolyDDSPModel's batched interface.
  Checks: ruff clean (pre-existing only), pytest 361/361, vitest 77/77.

## BUGS

_Bug references only (full records in `doc/bugs.md`)._

_(none yet)_
