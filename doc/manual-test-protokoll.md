---
type: test-protocol
title: Manual Test Protocol - wogd-ddsp-trainer
description: Manual end-to-end acceptance tests for training, ordered chronologically from the simplest to the most complex model training definition (standard → component → hacks → engine → advanced)
status: active
generated:
  by: build
  at: 2026-09-02
stale_after: 2027-06-01
tags: [manual-test, qa, training, model-tiers, acceptance]
---

# Manual Test Protocol

_Based on the German user manual [`handbook.md`](./handbook.md). This protocol
runs the training workflows of the web app by hand, in the same order the
handbook introduces them: from the **simplest** model (standard) to the most
**complex** model definitions (component → hacks → engine → advanced). For the
complex tiers only **representative** test cases are defined – not one case per
parameter change._

---

## How to use this protocol

Run the test cases **in order**. Each series builds on the previous one (the
last series leaves a trained model behind that the next series can reuse).

Per test case, fill in the **Result** row:

| Field | Meaning |
|---|---|
| Pass / Fail | Record `PASS` or `FAIL` |
| Date | Date of the test run |
| Tester | Name / initials |
| Notes | Deviations, errors, screenshots, references to `doc/bugs.md` (`BUG-<id>`) |

Prerequisite per case: the previous case left the app in the described state.
Audio material used for the whole protocol: **10–15 min** of clean, monophonic,
dry (no reverb/delay) material, per handbook §2.

---

## Test series A – Standard model (simplest training)

Goal: one full standard training run, from upload to export. References:
handbook §2 (quick start) and §4.2 (core config) / §4.7 (inference params).

### MT-A1 — Upload & Ingestion

| | |
|---|---|
| **Preconditions** | App running, backend + GPU status visible in the top bar |
| **Steps** | 1. Open **Dataset & Preprocessing → Upload & Ingestion**.<br>2. Drag & drop at least one audio file (e.g. WAV/FLAC/MP3).<br>3. Verify a waveform preview appears per file.<br>4. Click **Upload**. |
| **Expected** | File(s) ingested and listed in the dataset manager; waveform previews rendered; no backend error toast. |
| **Result** | FAIL — 2026-09-03 — — Notes: BUG-23 (no GET route for audio → waveform container empty), BUG-22 (name not persisted after refresh), BUG-20 (stale file list — was open, re-check). BUG-16 (waveform render), BUG-18/BUG-21 (name input), BUG-17 (file count) all fixed and verified. |

### MT-A2 — Preprocessing (feature extraction)

| | |
|---|---|
| **Preconditions** | MT-A1 passed, dataset available |
| **Steps** | 1. Open **Dataset & Preprocessing → Preprocessing**.<br>2. Select the dataset.<br>3. Start feature extraction.<br>4. Wait until progress reaches 100 %. |
| **Expected** | F0 and loudness features extracted; progress indicators complete; low-`f0_confidence` warning shown only if tracking reliability is low; dataset marked as trainable. |
| **Result** | FAIL — 2026-09-03 — — Notes: BUG-22 (name not persisted, UUID shown after refresh), BUG-23 (no audio GET route → waveform stays empty), BUG-24 (file_count counted .npy files: 9→19), BUG-25 (resultsText is hardcoded placeholder). BUG-19 (preprocessed status) fixed and verified. BUG-45 (preprocessing result too sparse, wants F0/loudness diagnostics). |

### MT-A3 — Model Setup Wizard (standard tier)

| | |
|---|---|
| **Preconditions** | MT-A2 passed |
| **Steps** | 1. Open **Model Architecture → Training Config**.<br>2. Confirm the wizard opens automatically (or open via **⚙ Reconfigure Model**).<br>3. Step 1: choose **Standard** tier card.<br>4. Step 2: choose **NORMAL** preset (note the displayed VRAM estimate).<br>5. Step 3: choose **Offline / Studio** target mode.<br>6. Click **Start Training Setup ✓**. |
| **Expected** | Wizard completes; tier badge shows **standard**; tab bar `Core | Component | Hacks | Engine | Advanced` visible with all tabs above standard greyed out; **Core** tab active. |
| **Result** | PASS / FAIL — Date — Tester — Notes: |

### MT-A4 — Core configuration and training start

| | |
|---|---|
| **Preconditions** | MT-A3 passed |
| **Steps** | 1. In tab **Core** verify: preset shows wizard-chosen value (e.g. NORMAL), learning rate 1e-3, batch size (preset-dependent, e.g. 16 for mid tier NORMAL on 6 GB), epochs (e.g. 100), decoder GRU, reverb on.<br>2. Change **Decoder Type** to **RNN**, then back to **GRU**.<br>3. Change **Enable Reverb** off, then on again.<br>4. Click **▶ Start Training**. |
| **Expected** | A run is created and starts; run ID and status displayed; training steps progress in the dashboard. |
| **Result** | PASS / FAIL — Date — Tester — Notes: BUG-44 (preset dropdown), BUG-47 (wizard 2.2 GB), BUG-48 (batch_size now propagates correctly), BUG-49 (HTTP 422 missing name field + no dataset selection + error message overflow) |

### MT-A5 — Monitoring, stop and resume

| | |
|---|---|
| **Preconditions** | MT-A4 passed, run is training |
| **Steps** | 1. Open **Training & Monitor → Training Dashboard**.<br>2. Verify TensorBoard embed shows loss curves / spectrograms / checkpoint audio (or fallback link opens TensorBoard in a new tab).<br>3. **Stop** the run; confirm cooperative stop at next step boundary.<br>4. **Resume** the run from the latest checkpoint. |
| **Expected** | Metrics visible; stop works cooperatively; resume continues training from the newest checkpoint (no tier-mismatch error). |
| **Result** | PASS / FAIL — Date — Tester — Notes: |

### MT-A6 — Standard inference & export (4 params)

| | |
|---|---|
| **Preconditions** | MT-A5 passed, a checkpoint exists |
| **Steps** | 1. Open **Inference & Export → Playground**; render a short clip.<br>2. In **Model Export**, open the parameter builder: verify the 4 standard knobs `Pitch Shift`, `Loudness`, `Noise Level`, `Reverb Mix`.<br>3. Edit the name of one parameter (≤ 30 chars) and a default value.<br>4. Export **Neutone FX (.nm)** and (if visible) **Custom VST (.pt)**. |
| **Expected** | Playback non-empty and intelligible; exactly 4 parameter cards, no "add" button, no Custom VST section for standard; edit validation works; both exports succeed and return a downloadable file. |
| **Result** | PASS / FAIL — Date — Tester — Notes: |

---

## Test series B – Component model (explicit harmonic/noise balance)

Goal: a component training run that explicitly balances harmonics and noise.
References: handbook §3.1 and §4.3; parameter-handling §4 (`component`).

### MT-B1 — Wizard (component) + Component tab

| | |
|---|---|
| **Preconditions** | Series A complete (a dataset + trained standard model exist) |
| **Steps** | 1. Open Training Config → **⚙ Reconfigure Model**.<br>2. Step 1: choose **Component** tier card.<br>3. Step 2: choose **FAST** preset.<br>4. Step 3: choose **Realtime / Low-Latency**.<br>5. Finish the wizard; open tab **Component**.<br>6. Move **Number of Harmonics** to its maximum GPU-bound value; move **Number of Filter Banks** to ~50 % of its bound.<br>7. Open **Open Component Mixer →** and verify the harmonics-vs-noise balance controls. |
| **Expected** | Tier badge `component`; Component tab unlocked and core/hacks/engine/advanced above disabled; slider ranges GPU-clamped; mixer renders. |
| **Result** | PASS / FAIL — Date — Tester — Notes: |

### MT-B2 — Component training + Custom-VST export

| | |
|---|---|
| **Preconditions** | MT-B1 passed |
| **Steps** | 1. Start training and let it run a few steps, then stop.<br>2. Resume once, verify tier guard passes.<br>3. Open Model Export → parameter builder.<br>4. Verify suggested knobs: `Harmonic Blend`, `Noise Blend`, `Reverb Mix`, `Attack`, etc.; Custom VST section visible (≥ component); add/reorder a 5th Custom-VST parameter.<br>5. Export Custom VST (.pt) and Neutone (.nm). |
| **Expected** | Training runs; export proposes the component knob set; Custom VST shows the added parameter; both export files download. |
| **Result** | PASS / FAIL — Date — Tester — Notes: |

---

## Test series C – Hacks model (synthesis experiments)

> Representative cases only (handbook §3.2, §4.4). Each case activates one
> group of hacks and checks that the **export knobs match the active hacks**
> (parameter-handling §4 `hacks`). Keep all other hacks at default.

### MT-C1 — Waveform Square/Saw + Angular Cumsum

| | |
|---|---|
| **Preconditions** | MT-B2 passed |
| **Steps** | 1. Reconfigure to tier **Hacks** (FAST, Offline).<br>2. Tab **Hacks**: set **Waveform** = `Saw`, enable **Angular Cumsum**.<br>3. Start training; after a few steps render a clip in the Playground.<br>4. Check suggested export knobs in the builder. |
| **Expected** | Training runs; synthesis is audibly saw-like (brighter than sine); knob suggestions include waveform-affecting params; no phase-drift artifacts on clips > 6 s. |
| **Result** | PASS / FAIL — Date — Tester — Notes: |

### MT-C2 — FM synthesis

| | |
|---|---|
| **Preconditions** | MT-B2 passed |
| **Steps** | 1. Reconfigure to tier **Hacks**.<br>2. Tab **Hacks**: keep Waveform `Sine`, set **FM Depth** > 0 and **FM Ratio** = 2.<br>3. Set FM Depth back to 0 and confirm the model behaves like the basline (deactivated default).<br>4. Start training; render a clip.<br>5. Verify export knob suggestions include `FM Depth` and `FM Ratio`. |
| **Expected** | FM > 0 produces inharmonic/metallic spectra; FM = 0 matches standard behaviour; export proposes FM knobs. |
| **Result** | PASS / FAIL — Date — Tester — Notes: |

### MT-C3 — Phase Distortion

| | |
|---|---|
| **Preconditions** | MT-B2 passed |
| **Steps** | 1. Reconfigure to tier **Hacks**.<br>2. Tab **Hacks**: set **Phase Distortion (pd_k)** to ~0.5.<br>3. Start training; render a clip.<br>4. Verify export knobs include `PD Amount` / `Waveshape`. |
| **Expected** | Training runs; audible CZ-style phase-distortion character; export proposes PD knobs. |
| **Result** | PASS / FAIL — Date — Tester — Notes: |

### MT-C4 — Trainable Wavetable + LFO

| | |
|---|---|
| **Preconditions** | MT-B2 passed |
| **Steps** | 1. Reconfigure to tier **Hacks**.<br>2. Tab **Hacks**: enable **Trainable Wavetable**, enable **LFO** with a visible frequency/depth (e.g. 4 Hz, moderate depth).<br>3. Start training; render a clip.<br>4. Verify export knobs include wavetable position and LFO-related params. |
| **Expected** | Training runs; modulation is audible; export proposes the wavetable/LFO knob set. |
| **Result** | PASS / FAIL — Date — Tester — Notes: |

---

## Test series D – Engine models (alternative synthesis engines)

> Representative cases (handbook §3.3, §4.5; parameter-handling §4 `engine`):
> one case per engine. Each case checks engine-specific sound character and
> engine-specific export knobs.

### MT-D1 — Harmonic engine (baseline)

| | |
|---|---|
| **Preconditions** | Series C complete |
| **Steps** | 1. Reconfigure to tier **Engine**.<br>2. Tab **Engine**: choose engine `Harmonic`.<br>3. Start training; render a clip.<br>4. Verify export knobs equal the standard set. |
| **Expected** | Behaviour identical to the standard model; standard export knobs. |
| **Result** | PASS / FAIL — Date — Tester — Notes: |

### MT-D2 — Sinusoidal engine + colored noise

| | |
|---|---|
| **Preconditions** | Series C complete |
| **Steps** | 1. Reconfigure to tier **Engine**.<br>2. Tab **Engine**: engine `Sinusoidal`; **Noise Color** = `Pink`.<br>3. Start training; render a clip.<br>4. Verify export knobs include `Inharmonicity`, `Spectral Spread`, `Partial Density`, `Brightness`. |
| **Expected** | Glassy / pure-partial timbre; pink noise audible in rests; engine-specific knobs proposed. |
| **Result** | PASS / FAIL — Date — Tester — Notes: |

### MT-D3 — Comb-Subtractive engine

| | |
|---|---|
| **Preconditions** | Series C complete |
| **Steps** | 1. Reconfigure to tier **Engine**.<br>2. Tab **Engine**: engine `Comb-Subtractive`; **Noise Color** = `Brown`.<br>3. Start training; render a clip.<br>4. Verify export knobs include `Formant Shift`, `Brightness`, `Vowel`, `Roughness`. |
| **Expected** | Body/resonant comb-filter character; export proposes combsub knobs. |
| **Result** | PASS / FAIL — Date — Tester — Notes: |

### MT-D4 — NEWT engine

| | |
|---|---|
| **Preconditions** | Series C complete |
| **Steps** | 1. Reconfigure to tier **Engine**.<br>2. Tab **Engine**: engine `NEWT`; set **NEWT Hidden Size** = 64 and **NEWT Layers** = 4.<br>3. Start training; render a clip.<br>4. Verify export knobs include `Tone Character`, `Saturation`, `MLP Layer Bias`, `Odd Harmonics`. |
| **Expected** | Training fits the GPU with these NEWT sizes; neural waveshaping character; NEWT knobs proposed. |
| **Result** | PASS / FAIL — Date — Tester — Notes: |

---

## Test series E – Advanced models (VAE, polyphony, voice conversion)

> Highest complexity (GPU **6–12 GB** recommended, handbook §3.4). Three
> representative cases – one per Advanced variant. Cases are independent of
> each other (each reconfigures the tier).

### MT-E1 — VAE / Latent Space (timbre steering & morphing)

| | |
|---|---|
| **Preconditions** | ≥ 6 GB VRAM; a dataset is available; previous series complete |
| **Steps** | 1. Reconfigure to tier **Advanced**; confirm the feasibility badge (✓ or ⚠).<br>2. Tab **Advanced** → **VAE / Latent Space**: enable **Use Latent (VAE)**, keep **Latent Dim** = 32 and **KL Beta** default; start training; render a clip.<br>3. In Inference area: open **Latent Explore**, sweep several latent dimensions (Z1…ZN), label one dimension.<br>4. **Morphing:** interpolate between two checkpoints A and B; render at start/middle/end.<br>5. Export **Custom VST (.pt)**: verify latent dimensions appear as knobs (Timbre Z1…ZN); neutone export shows ≤ 4 of them. |
| **Expected** | Training runs with latent loss; Latent Explore audibly changes timbre per dimension; morphing produces a smooth transition; exports embed the latent knobs. |
| **Result** | PASS / FAIL — Date — Tester — Notes: |

### MT-E2 — Polyphony (multiple voices)

| | |
|---|---|
| **Preconditions** | ≥ 6 GB VRAM (n_voices ≥ 3 needs proportionally more) |
| **Steps** | 1. Reconfigure to tier **Advanced**.<br>2. Tab **Advanced** → **Polyphony**: set **Number of Voices** = 2; verify the VRAM warning appears when raising to 3–4.<br>3. Start training with 2 voices; render a clip.<br>4. Verify export knobs include `Voice Balance`, `Detune`, `Voice Spread`, `Unison Width`. |
| **Expected** | Warning text for > 2 voices; 2-voice training runs; output sounds polyphonic; poly knobs proposed. |
| **Result** | PASS / FAIL — Date — Tester — Notes: |

### MT-E3 — Voice Conversion (HuBERT/ContentVec)

| | |
|---|---|
| **Preconditions** | ≥ 6 GB VRAM |
| **Steps** | 1. Reconfigure to tier **Advanced**.<br>2. Tab **Advanced** → **Voice Conversion**: enable **Use Content Encoder**, choose **HuBERT-Soft** (variant B: repeat with **ContentVec**).<br>3. Start training; render a clip.<br>4. In **Voice Conversion** view: select source model + target model, run a conversion, compare with A/B player.<br>5. Verify export knobs include `Style Transfer`, `Formant Scale`, `Breathiness`, `Speaker Blend`. |
| **Expected** | Content-extraction step runs during training; conversion transfers the target timbre; both encoder variants train and convert successfully; VC knobs proposed. |
| **Result** | PASS / FAIL — Date — Tester — Notes: |

---

## Test series F – MIDI Synth Export

> Tests MIDI synth export path for selected tiers. Each case reconfigures,
> selects Usage Mode "MIDI Synth" or "Both" in the Wizard, trains briefly,
> and verifies the MIDI Synth export button and the MIDI Preview playground.

### MT-F1 — Standard tier MIDI Synth export

| | |
|---|---|
| **Preconditions** | A trained standard model from series A exists |
| **Steps** | 1. Open Training Config → **⚙ Reconfigure Model**.<br>2. Step 1: choose **Standard** tier.<br>3. Step 2: choose **FAST** preset.<br>4. Step 3 (Target Mode): choose **Offline**.<br>5. Step 3 (Usage Mode): choose **MIDI Synth**.<br>6. Finish the wizard; verify a **MIDI Synth Training Tip** info banner appears.<br>7. Train model; stop after a few steps.<br>8. Open **Model Export**; verify the **Export → MIDI Synth (.pt)** button is visible.<br>9. Click the button; verify the job status completes successfully. |
| **Expected** | Banner visible; MIDI Synth export button appears (only for midi_synth mode); export completes to a downloadable .pt file. |
| **Result** | PASS / FAIL — Date — Tester — Notes: |

### MT-F2 — Hacks tier MIDI Synth (recommended badge)

| | |
|---|---|
| **Preconditions** | A dataset is available; previous series complete |
| **Steps** | 1. Reconfigure to tier **Hacks**.<br>2. Tab **Hacks**: leave defaults (sine, FM off).<br>3. Wizard Step 3 (Usage Mode): verify the "**Recommended for this tier**" badge on the MIDI Synth card.<br>4. Choose **MIDI Synth**.<br>5. Train briefly; stop.<br>6. In Model Export, verify the MIDI Synth button is visible.<br>7. Export MIDI Synth; download the .pt file.<br>8. Open **Inference Playground** → switch to **MIDI Preview** tab.<br>9. Verify the virtual keyboard renders, select a key, click **Play Preview**.<br>10. Verify the job status completes and an audio player appears. |
| **Expected** | "Recommended" badge visible for hacks; MIDI Synth export completes; MIDI Preview virtual keyboard renders; preview playback works. |
| **Result** | PASS / FAIL — Date — Tester — Notes: |

### MT-F3 — Advanced/VAE tier MIDI Synth export

| | |
|---|---|
| **Preconditions** | ≥ 6 GB VRAM; a dataset is available |
| **Steps** | 1. Reconfigure to tier **Advanced**; enable **Use Latent (VAE)** with Latent Dim = 8.<br>2. In the Wizard, choose Usage Mode = **Both** (Audio FX + MIDI Synth).<br>3. Train briefly; stop.<br>4. In Model Export, verify both the regular format cards (Neutone/ONNX/TorchScript) AND the MIDI Synth section are visible.<br>5. Export MIDI Synth; verify the .pt file downloads.<br>6. (Optional) Open MIDI Preview tab and play a note. |
| **Expected** | Both export paths visible simultaneously; MIDI Synth export succeeds alongside Audio FX exports. |
| **Result** | PASS / FAIL — Date — Tester — Notes: |

### MT-F4 — MIDI Preview virtual keyboard corner cases

| | |
|---|---|
| **Preconditions** | Any trained model; MT-F2 or MT-F3 passed |
| **Steps** | 1. Open **Inference Playground** → **MIDI Preview** tab.<br>2. Change octave from 4 to 2, then to 6; verify the keyboard updates.<br>3. Set velocity slider to 0 and then to 127; play a note each time.<br>4. Set duration slider to 0.25s and to 4s; play a note.<br>5. Play a note with no model selected; verify no crash (button should be disabled). |
| **Expected** | Keyboard changes per octave; velocity 0 produces silence/minimal output; extreme durations produce proportionally short/long audio; disabled button when no model selected. |
| **Result** | PASS / FAIL — Date — Tester — Notes: |

---

## Summary / Sign-off

| Series | Test IDs | Passed | Failed | Notes |
|---|---|---|---|---|
| A – Standard | MT-A1 … MT-A6 | | | |
| B – Component | MT-B1 … MT-B2 | | | |
| C – Hacks | MT-C1 … MT-C4 | | | |
| D – Engine | MT-D1 … MT-D4 | | | |
| E – Advanced | MT-E1 … MT-E3 | | | |
| F – MIDI Synth | MT-F1 … MT-F4 | | | |
| **Total** | **MT-A1 … MT-F4 (23 cases)** | | | |

Signed off: ________________________________  Date: ______________

Failures must be filed in [`bugs.md`](./bugs.md) (full record) and referenced
here with their `BUG-<id>`; the bug ledger is the single source of truth.