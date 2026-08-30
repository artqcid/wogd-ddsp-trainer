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

- The UI is **fully decoupled from the backend**: it communicates only via
  REST, WebSocket (training status) and SSE. `webui/` must never import backend
  modules.
- **Tech stack (decided in `plan.md`):** Vue 3 + Vite (+ Pinia). UI work must
  not reopen this decision.
- **Mock-data seam (mandatory):** every view and component renders through an
  API-client abstraction. A `MockApiClient` + fixture set must exist so the
  entire UI runs without a backend (Vitest and dev preview). A new view is not
  done until it renders with mock data.
- The backend-UI data/event contracts (REST endpoints, WebSocket message
  schema, SSE events) are defined in `architecture.md`.

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
  tracking (e.g. CREPE). Surface a warning when pitch-tracker confidence is too
  low (e.g. due to noise or polyphony).
- **Loudness extraction (A-weighted power):** progress indicator.

### 3. Training configuration (hyperparameters)

A form/panel for DDSP-specific parameters:

- Standard ML: batch size, learning rate, number of steps/epochs.
- DDSP architecture: decoder type (e.g. GRU, RNN), oscillator types
  (harmonic, sinusoidal), noise-generator filter (filtered noise), reverb
  module enable/disable (often optional during training).

### 4. Real-time monitoring (training progress)

- **Loss metrics:** graph of the total reconstruction loss; optionally split
  into spectral loss (linear and log-scale spectrogram loss).
- **Spectrogram comparison:** a component showing the original audio's
  (mel-)spectrogram next to the current reconstruction's (if delivered by the
  backend).
- **Audio checkpoints:** a mini-player in the dashboard to listen to a
  checkpoint's reconstructed audio directly in the browser (subjective
  progress).

### 5. Inference & playground (timbre transfer)

- **Timbre transfer:** upload a "source" audio (e.g. vocals) onto which the
  trained timbre (e.g. violin) is transferred.
- **Shaping controls:** sliders for pitch-shift (offset of extracted f0) and
  loudness-shift before synthesis.

### 6. Model export

UI elements to download the trained weights with format selection (e.g.
PyTorch `.pt`, TorchScript, ONNX, plugin formats such as Neutone) — restricted
to what the backend supports.

## Additional required views (project milestones)

The following are required by the project milestones and must be present in the
UI:

- **Dataset manager** (M5.1): list datasets with validation status and
  train/validation split.
- **Run lifecycle** (M4.2): start/stop/resume training runs, run list/history,
  current run status.

## UI component structure (target)

Views:

- `DatasetManagerView` — datasets, validation status, splits.
- `UploadIngestionView` — audio upload + client-side DDSP checks/hints.
- `PreprocessingView` — F0/loudness extraction progress + confidence warnings.
- `TrainingConfigView` — ML + DDSP hyperparameters.
- `TrainingDashboardView` — loss graphs, spectrogram comparison, checkpoint
  audio, run controls.
- `InferencePlaygroundView` — timbre transfer + shaping controls.
- `ModelExportView` — weight download with format selection.

Shared components:

- `AudioPlayer` — checkpoint/reconstruction playback.
- `LossChart` — total + spectral loss curves.
- `SpectrogramCompare` — original vs. reconstructed spectrogram.
- `PitchConfidenceIndicator` — F0 confidence warning.
- `ConfigFormPanel`, `RunStatusBadge` — shared form/status primitives.

Data layer:

- API-client interface (REST/WS/SSE) + `MockApiClient` implementation and
  fixtures under `webui/src/mocks/` for offline/mock mode.

## Acceptance criteria

- Every view renders and is testable with mock data (Vitest) without a running
  backend.
- Decoupling rule enforced: no backend imports inside `webui/`.
- Project checks green per Definition of Done (`ruff`, `pytest`, `vitest`).

## References

- `plan.md` — milestone M5 (UI), tech stack decision.
- `checklist.md` — M5.x open UI tasks.
- `architecture.md` — backend-UI interface, data/event contracts.
- `coding-standards.md` — coding rules (CCD).