---
type: implementation-plan
status: draft
milestone: M5 - Web UI
generated:
  by: primary-agent
  at: 2026-08-31
stale_after: 2026-12-31
---

# Implementation Plan - M5 Web UI

_Granular plan for milestone M5. Meta plan: [`../plan.md`](../plan.md); status:
[`../checklist.md`](../checklist.md); UI source of truth:
[`../ui-requirements.md`](../ui-requirements.md)._

## How to use

- Each step below is one small, self-contained task (approx. one subagent task).
- Work in order; mark `[x]` and record every step in `## History`.
- Bugs: full record only in [`../bugs.md`](../bugs.md); reference by `BUG-<id>`.
- Every view renders through the API-client abstraction with `MockApiClient`
  (mock-data seam); a view is not done until it renders with mock data.

## Steps

### M5.1 App shell

- [ ] **M5.1.1** Dark-mode SPA layout (theme + base styles).
      Files: `webui/src/App.vue`, `webui/src/assets/`.
- [ ] **M5.1.2** Sidebar with 4 nav groups (Dataset & Preprocessing / Model
      Architecture / Training & Monitor / Inference & Export) + routing.
      Files: `webui/src/components/Sidebar.vue`, router config.
- [ ] **M5.1.3** Top bar status (backend connection, GPU, active project).
      Files: `webui/src/components/TopBar.vue`.
- [ ] **M5.1.4** API-client interface + `MockApiClient` + fixtures.
      Files: `webui/src/api/`, `webui/src/mocks/`.

### M5.2 Dataset & Preprocessing views

- [ ] **M5.2.1** `UploadIngestionView`: drag-drop + Wavesurfer.js waveform +
      DDSP hints (mono/dry/10-15 min).
- [ ] **M5.2.2** `DatasetManagerView`: dataset list, validation status,
      train/validation split.
- [ ] **M5.2.3** `PreprocessingView`: F0/loudness extraction progress +
      `PitchConfidenceIndicator` warnings.

### M5.3 Model Architecture view

- [ ] **M5.3.1** `TrainingConfigView`: ML params (batch size, LR, epochs) +
      target mode (offline/realtime) + DDSP params + GPU suggestions + preset
      selector dropdown (FAST/NORMAL/QUALITY + custom presets). Selecting a
      preset fills all fields and shows clamped warnings where values were
      adjusted.
- [ ] **M5.3.2** `PresetSaveDialog`: modal to save current config as a new
      custom preset (name input + confirm). Invoked from TrainingConfigView
      and from run detail.

### M5.4 Training & Monitor view

- [ ] **M5.4.1** `TrainingDashboardView`: job control (start/pause/abort,
      epoch/ETA) + TensorBoard iframe with new-tab fallback + status polling.
- [ ] **M5.4.2** "Save as Preset" button in run detail: reads run config from
      REST, calls POST /presets/from-run/{run_id}.

### M5.5 Inference & Export views

- [ ] **M5.5.1** `InferencePlaygroundView`: timbre transfer + shaping controls +
      `ABComparisonPlayer` (solo/mute).
- [ ] **M5.5.2** `ModelExportView`: export hub (Neutone / ONNX / TorchScript).

### M5.6 Preset Management view

- [ ] **M5.6.1** `PresetManagerView`: list all presets (built-in + custom) with
      name, type badge, last-used date. Inline edit for custom presets. Delete
      for custom presets only. Each value field clamped to current GPU bounds.
      Files: `webui/src/views/PresetManagerView.vue`.
      Verify: renders with mock data; CRUD buttons call API-client methods.
- [ ] **M5.6.2** Navigation: add a `Presets` entry to the sidebar (as a 5th
      group or under Model Architecture). Files: sidebar config.
      Verify: route resolves to PresetManagerView.

### M5.7 Tests

- [ ] **M5.7.1** Vitest per view: every view renders with `MockApiClient` +
      fixtures.

## BUGS

_References only; full records in [`../bugs.md`](../bugs.md)._

- (none)

## History

_Append-only, newest first._

- (none yet)
