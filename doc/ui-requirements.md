---
type: requirements
status: draft
generated:
  by: setup
  at: 2026-08-31
description: UI/product requirements of the wogd-ddsp-trainer web app; applies to ALL workspace agents regardless of role
stale_after: 2026-12-31
---

# wogd-ddsp-trainer - UI Requirements

_Single source of truth for the product/UI requirements of the DDSP trainer web
app. Applies to every workspace agent, independent of role. Role-specific
prompts in `.opencode/agent/` add only deviations; this file is not duplicated
there. See [`index.md`](./index.md) for the knowledge catalog and
[`log.md`](./log.md) for the changelog._

## Applicability (mandatory)

These requirements bind **all** workspace agents: ARCHITECT, BUILD, DEV,
DEV_JUNIOR, and the subagents (`general`, `explore`). Every UI- or
product-relevant design, implementation, review and test must conform here.

Conflict resolution:

- This file wins over individual agent prompts on product/UI requirements.
- `architecture.md` remains authoritative for technical/API contracts
  (backend-UI interface, data/event flow).

## Coupling rules (non-negotiable)

- The UI is **fully decoupled from the backend**: it communicates via REST and
  embeds the server-side TensorBoard for training monitoring. `webui/` must
  never import backend modules.
- **Tech stack (decided in `plan.md`):** Vue 3 + Vite (+ Pinia). UI work must
  not reopen this decision.
- **TensorBoard doctrine (decided in `plan.md`):** the UI is a control panel.
  No custom live charts and no WebSocket/SSE streaming of losses or audio. The
  training dashboard embeds TensorBoard via `<iframe>`; if embedding is
  blocked, provide a prominent link/button that opens TensorBoard in a new tab.
  Lightweight REST polling for run *status* is allowed.
- **Mock-data seam (mandatory):** every view and component renders through an
  API-client abstraction. A `MockApiClient` + fixture set must exist so the
  entire UI runs without a backend (Vitest and dev preview). A new view is not
  done until it renders with mock data.
- The backend-UI data/event contracts (REST endpoints) are defined in
  `architecture.md`.

## App shell (global structure)

The application is a **dark-mode Single-Page Application (SPA)** (industry
convention for audio software) built from three regions:

- **Sidebar (left):** main workflow navigation with four groups:
  1. `Dataset & Preprocessing`
  2. `Model Architecture`
  3. `Training & Monitor`
  4. `Inference & Export`
- **Top bar (top):** global status only (backend connection, GPU
  idle/training, active project). No per-step controls live here.
- **Main content area:** renders the currently selected view; each navigation
  group maps to one or more of the granular views below.

The four groups are the navigation layer only; the granular views remain the
single implementation/ownership unit (see "UI component structure").

## DDSP domain constraints the UI must reflect

### 1. Data ingestion & constraints

The upload UI must communicate and ideally pre-check (client-side) the strict
DDSP data requirements:

- Audio **must** be monophonic and "dry" (no reverb/delay or heavy effects).
  Polyphonic audio causes wrong pitch tracking.
- Quantity hint: typically ~10-15 minutes of continuous, clean audio are needed
  for a good timbre model.

### 2. Preprocessing feedback (feature extraction)

Before training starts the backend extracts features; the UI must visualize
that status:

- **F0 extraction (fundamental frequency):** progress indicator for pitch
  tracking (e.g. CREPE). Surface a warning when pitch-tracker confidence
  (`f0_confidence`) is too low (e.g. due to noise or polyphony).
- **Loudness extraction (A-weighted power):** progress indicator.

### 3. Training configuration (hyperparameters)

A form/panel for DDSP-specific parameters:

- Standard ML: batch size, learning rate, number of steps/epochs.
- DDSP architecture: decoder type (e.g. GRU, RNN), oscillator types
  (harmonic, sinusoidal), noise-generator filter (filtered noise), reverb
  module enable/disable (often optional during training).
- **Target mode:** `Offline (studio quality)` vs `Realtime (causal, low
  latency)`. The realtime path maps to low-latency model export
  (Neutone/TorchScript), not a separate VST target.
- **GPU suggestions:** the app detects/analyzes the local GPU and proposes
  optimal training parameters; the UI surfaces these suggestions (for example
  as pre-filled defaults in the config form).
- **Preset management:**
  - Three built-in presets: `FAST` (~25 % VRAM-Auslastung), `NORMAL` (~50 %),
    `QUALITY` (~90–100 %). Jedes Preset skaliert **relativ zur verfügbaren
    GPU**: eine 6-GB-GPU und eine 12-GB-GPU bekommen unterschiedliche
    absolute Werte, aber das gleiche Auslastungsverhältnis.
  - Custom presets: user creates via a dedicated Preset Management tab or
    by saving the current run's config ("Save as Preset"). Every value is
    clamped to the current GPU's allowed bounds; clamped fields are flagged.
  - On hardware change, custom presets are re-clamped with a warning.

### 4. Training monitoring (TensorBoard doctrine)

- **No custom charts, no WebSocket/SSE streaming:** the UI must not implement
  custom live loss charts or stream losses/audio to the frontend.
- **TensorBoard embed:** the training dashboard embeds the server-side
  TensorBoard (loss curves, spectrograms, checkpoint audio - written natively
  by the training loop) via `<iframe>`.
- **Fallback:** if the iframe embedding is technically blocked, provide a
  prominent link/button that opens TensorBoard in a new tab.
- **Run controls:** start/stop/resume and run status remain in the UI via REST
  (lightweight polling allowed for status only).
- **Checkpoint audio:** optional play/download of a checkpoint's reconstructed
  audio over REST (not streamed).

### 5. Inference & playground (timbre transfer)

- **Timbre transfer:** upload a "source" audio (e.g. vocals) onto which the
  trained timbre (e.g. violin) is transferred.
- **Shaping controls:** sliders for pitch-shift (offset of extracted f0) and
  loudness-shift before synthesis.
- **A/B comparison:** two synchronized waveform players (source vs. generated)
  with solo/mute for direct auditive comparison.

### 6. Model export

UI elements to download the trained weights with format selection, **restricted
to what the backend supports** (PyTorch stack):

- Neutone (DAW plugin, TorchScript)
- ONNX (cross-platform / web via onnxruntime-web)
- TorchScript (realtime)

No TensorFlow (`SavedModel`/TFLite) artifacts are produced; the model/training
stack is PyTorch (see `plan.md`).

## Additional required views (project milestones)

The following are required by the project milestones and must be present in the
UI:

- **Dataset manager** (M5.2): list datasets with validation status and
  train/validation split.
- **Run lifecycle** (M4.2): start/stop/resume training runs, run list/history,
  current run status.

## Experimental sound-design extensions (M7, non-binding for M1-M6)

The following are **experimental** features scoped to milestone M7 (Musique
Concrète). They must not be built before M5-M6 are complete and must not alter
the coupling rules above. Full rationale lives in
[`experimental-ddsp.md`](./experimental-ddsp.md).

- **F0/pitch-curve override editor** (two-tier):
  - *File-level inspector:* a canvas overlay over the waveform to draw /
    smooth / erase / randomize the pitch curve for a single file.
  - *Global dataset rules:* algorithmic transformations applied to all
    extracted F0 curves (quantization to a scale, chaos/noise injection, pitch
    inversion).
- **DDSP component mixer:** sliders to weight harmonic vs. filtered-noise
  synthesis complexity (e.g. 0 harmonics / many noise filter banks for pure
  noise textures).
- **Reverb IR injection:** upload an impulse response (`.wav`) + "freeze
  (untrainable)" toggle to inject a fixed IR into the trainable reverb, and an
  IR extractor to export the learned IR as `.wav`.

## UI component structure (target)

App shell:

- `AppShell` — sidebar (4 groups), top bar (status), content router.

Views (grouped by navigation):

- `UploadIngestionView` — audio upload + client-side DDSP checks/hints +
  waveform display (Wavesurfer.js).
- `DatasetManagerView` — datasets, validation status, splits.
- `PreprocessingView` — F0/loudness extraction progress + confidence warnings.
- `TrainingConfigView` — ML + DDSP hyperparameters + target mode + GPU
  suggestions + preset selector (FAST/NORMAL/QUALITY + custom) + "Save as
  Preset" dialog.
- `TrainingDashboardView` — TensorBoard embed (iframe/fallback link), run
  controls, optional REST checkpoint-audio player + "Save as Preset" button
  in run detail.
- `InferencePlaygroundView` — timbre transfer + shaping controls + A/B player.
- `ModelExportView` — weight download with format selection (Neutone / ONNX /
  TorchScript).
- `PresetManagerView` — list/edit/delete custom presets (values clamped to
  GPU bounds); view built-in presets (read-only).

Shared components:

- `AudioPlayer` / `WaveformView` — checkpoint/reconstruction playback and
  waveform rendering (Wavesurfer.js).
- `ABComparisonPlayer` — synchronized source vs. target playback with solo/mute.
- `PitchConfidenceIndicator` — F0 confidence warning.
- `ConfigFormPanel`, `RunStatusBadge` — shared form/status primitives.

Data layer:

- API-client interface (REST) + `MockApiClient` implementation and fixtures
  under `webui/src/mocks/` for offline/mock mode.

## Acceptance criteria

- Every view renders and is testable with mock data (Vitest) without a running
  backend.
- Decoupling rule enforced: no backend imports inside `webui/`.
- Export formats restricted to the PyTorch stack (Neutone/ONNX/TorchScript).
- Project checks green per Definition of Done (`ruff`, `pytest`, `vitest`).

## References

- `plan.md` — milestone M5 (UI) + M7 (experimental), tech stack decision.
- `checklist.md` — M5.x / M7.x open UI tasks.
- `experimental-ddsp.md` — rationale for the M7 experimental UI features.
- `architecture.md` — backend-UI interface, data/event contracts.
- `coding-standards.md` — coding rules (CCD).
