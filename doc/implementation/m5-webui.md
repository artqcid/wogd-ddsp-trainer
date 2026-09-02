---
type: implementation-plan
status: implemented
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

- [x] **M5.1.1** Dark-mode SPA layout (theme + base styles).
      Files: `webui/src/App.vue`, `webui/src/assets/`.
- [x] **M5.1.2** Sidebar with 4 nav groups (Dataset & Preprocessing / Model
      Architecture / Training & Monitor / Inference & Export) + routing.
      Files: `webui/src/components/Sidebar.vue`, router config.
- [x] **M5.1.3** Top bar status (backend connection, GPU, active project).
      Files: `webui/src/components/TopBar.vue`.
- [x] **M5.1.4** API-client interface + `MockApiClient` + fixtures.
      Files: `webui/src/api/`, `webui/src/mocks/`.

### M5.2 Dataset & Preprocessing views

- [x] **M5.2.1** `UploadIngestionView`: drag-drop + Wavesurfer.js waveform +
      DDSP hints (mono/dry/10-15 min).
- [x] **M5.2.2** `DatasetManagerView`: dataset list, validation status,
      train/validation split.
- [x] **M5.2.3** `PreprocessingView`: F0/loudness extraction progress +
      `PitchConfidenceIndicator` warnings.

### M5.3 Model Architecture view

- [x] **M5.3.1** `TrainingConfigView`: ML params (batch size, LR, epochs) +
      target mode (offline/realtime) + DDSP params + GPU suggestions + preset
      selector dropdown (FAST/NORMAL/QUALITY + custom presets). Selecting a
      preset fills all fields and shows clamped warnings where values were
      adjusted.
- [x] **M5.3.2** `PresetSaveDialog`: modal to save current config as a new
      custom preset (name input + confirm). Invoked from TrainingConfigView
      and from run detail.

### M5.4 Training & Monitor view

- [x] **M5.4.1** `TrainingDashboardView`: job control (start/pause/abort,
      epoch/ETA) + TensorBoard iframe with new-tab fallback + status polling.
- [x] **M5.4.2** "Save as Preset" button in run detail: reads run config from
      REST, calls POST /presets/from-run/{run_id}.

### M5.5 Inference & Export views

- [x] **M5.5.1** `InferencePlaygroundView`: timbre transfer + shaping controls +
      `ABComparisonPlayer` (solo/mute).
- [x] **M5.5.2** `ModelExportView`: export hub (Neutone / ONNX / TorchScript).

### M5.6 Preset Management view

- [x] **M5.6.1** `PresetManagerView`: list all presets (built-in + custom) with
      name, type badge, last-used date. Inline edit for custom presets. Delete
      for custom presets only. Each value field clamped to current GPU bounds.
      Files: `webui/src/views/PresetManagerView.vue`.
      Verify: renders with mock data; CRUD buttons call API-client methods.
- [x] **M5.6.2** Navigation: add a `Presets` entry to the sidebar (as a 5th
      group or under Model Architecture). Files: sidebar config.
      Verify: route resolves to PresetManagerView.

### M5.7 Tests

- [x] **M5.7.1** Vitest per view: every view renders with `MockApiClient` +
      fixtures.

### M5.8 Preset-schema alignment and parameter fixes

_Identified during M1–M6 review (2026-08-31). The mock fixtures and the
`TrainingConfigView.vue` logic use AutoVC/DSP-autoencoder field names that do
not match the DDSP backend schema. These must be fixed before any integration
test or real backend run can work._

- [x] **M5.8.1** **[IMPLEMENT — BUG FIX]** Align `webui/src/mocks/fixtures.js`
      `presetsFixture` with the real backend preset schema:
      - Replace `type: 'autovc'` / `type: 'dsp-autoencoder'` with
        `is_builtin: true` (built-in) or `is_builtin: false` (custom).
      - Replace `parameters: { hidden_dim, encoder_dim, decoder_dim,
        postnet_dim, ... }` with the DDSP schema:
        `params: { hidden_size, stft_scales, mixed_precision,
        gradient_checkpointing }`.
      - Align `createPresetFixture`, `createPresetFromRunFixture` likewise.
      - Align `modelsFixture` checkpoints from `*.h5` to `step-*.pt` format.
      Files: `webui/src/mocks/fixtures.js`, `webui/src/mocks/mockApiClient.js`.
      Verify: vitest still green after fixture update.

- [x] **M5.8.2** **[IMPLEMENT — BUG FIX]** Fix `TrainingConfigView.vue`
      `presetOptions` computed property: filter built-in presets by
      `p.is_builtin === true` instead of `p.type === 'builtin' || p.type ===
      'autovc' || p.type === 'dsp-autoencoder'`.
      Files: `webui/src/views/TrainingConfigView.vue`.
      Verify: vitest render test passes with updated fixture.

- [x] **M5.8.3** **[IMPLEMENT — BUG FIX]** Fix `TrainingConfigView.vue`
      `currentParams` computed property and `handleStartTraining()`: replace
      AutoVC field names (`hidden_dim`, `encoder_dim`, `decoder_dim`,
      `postnet_dim`, `n_trees`) with the DDSP backend fields
      (`hidden_size`, `stft_scales`, `mixed_precision`,
      `gradient_checkpointing`). The payload sent to `POST /api/runs` must
      match `build_training()` in `server/tasks.py`.
      Files: `webui/src/views/TrainingConfigView.vue`.
      Verify: vitest render test + mock start-training flow still green.

- [x] **M5.8.4** **[IMPLEMENT — BUG FIX]** Fix Training Speed labels in
      `TrainingConfigView.vue`: the radio buttons currently show
      `FAST (25% VRAM)` / `NORMAL (50% VRAM)` / `QUALITY (75% VRAM)`. These
      labels describe the preset VRAM targets, not the speed-modifier factors
      (FAST 0.5x / NORMAL 0.75x / QUALITY 0.9x on hidden_size). Update the
      labels to accurately reflect what the speed selector does, e.g.:
      `FAST (0.5x hidden_size, max speed)` / `NORMAL (0.75x, default)` /
      `QUALITY (0.9x, best output)`.
      Files: `webui/src/views/TrainingConfigView.vue`.

- [x] **M5.8.5** **[IMPLEMENT]** Add missing DDSP-specific UI controls required
      by `ui-requirements.md` section 3:
      - Decoder type selector (GRU / RNN) — maps to `DDSPConfig.decoder_type`.
      - Reverb enable/disable toggle — maps to a new `use_reverb: bool` flag
        that must also be added to `DDSPConfig` and wired through
        `model/ddsp/synths.py::DDSPCore`.
      Files: `webui/src/views/TrainingConfigView.vue`,
             `model/ddsp_model.py` (DDSPConfig),
             `model/ddsp/synths.py` (DDSPCore reverb toggle).
      Verify: vitest render test passes; ruff clean on Python changes.
      Note: this is a non-trivial cross-stack change; coordinate with M3.

## BUGS

_References only; full records in [`../bugs.md`](../bugs.md)._

- `BUG-5` — Preset-schema drift: fixtures use AutoVC field names; backend uses
  DDSP field names. See M5.8.1–M5.8.3. Status: open.
- `BUG-6` — Training Speed radio button labels misleading (25/50/75% instead of
  actual 0.5×/0.75×/0.9× factors). See M5.8.4. Status: open.

- **BUG-12** — Upload & Ingestion: „Upload"-Button und „Show DDSP requirements"
  kleben aneinander; Requirements nicht als klickbar erkennbar. Status: open.
  - Ursache: `UploadIngestionView.vue` — `.hints-toggle` Button hat keinen visuellen
    Link-Stil (kein `color`, kein underline) und wirkt wie statischer Text. Der
    `margin-top: 1.5rem` auf `.hints-toggle` sollte theoretisch Abstand geben, aber
    ohne `display: block` kann der Abstand bei inlineartigen Buttons kollabieren.
  - Fix-Vorschlag: `.hints-toggle` CSS ergänzen: `display: block`,
    `color: var(--accent)`, `text-decoration: underline`, `margin-top: 1.5rem`
    (sicherstellen). Damit ist der Button visuell als Link erkennbar und der Abstand
    zum Upload-Button ist garantiert.

- **BUG-13** — Sidebar-Menü: Abschnitte ab „Export" durcheinander; Presets gehört
  weder unter Training noch unter Export. Status: open.
  - Ursache: `Sidebar.vue` — „Presets" ist in der Gruppe „🔊 Inference & Export"
    eingeordnet, obwohl Presets Training-Konfiguration und Export/Inferenz-Parameter
    betreffen. Voice Conversion ist keine Export-Funktion sondern ein eigenes Feature
    (M13). Morphing und Latent Explorer sind Advanced-Features, keine Experimental-Hacks.
  - Fix-Vorschlag: Sidebar-Gruppen neu strukturieren:
    1. 📦 Datasets & Preprocessing (Upload, Manager, Preprocessing) — unverändert
    2. 🧠 Training (Training Config, Training Dashboard) — Monitor hierhin
    3. 📋 Presets — eigene Gruppe, keine Unterordnung
    4. 🔊 Inference & Export (Inference Playground, Model Export) — nur diese zwei
    5. 🎤 Advanced Features (Voice Conversion, Morphing, Latent Explorer) — neue Gruppe
    6. 🧪 Experimental (Reverb IR, F0 Editor, Component Mixer, Synth Hacks) — nur echte Hacks
    Vollständige Usability-Review der Sidebar-Reihenfolge und Gruppenlabels.

- **BUG-14** — „Backend: error" beim Start (`start-application-release`), obwohl App läuft.
  Status: open.
  - Ursache: `TopBar.vue` — `onMounted` ruft `apiClient.health()` einmalig auf. Im
    Release-Modus öffnet sich der Browser teils bevor uvicorn vollständig bereit ist
    (Race Condition: Start-Skript startet uvicorn und Browser fast gleichzeitig). Der
    Health-Check schlägt fehl → `catch` → `healthStatus = 'err'` → „Backend: error".
    Kein Retry, kein Polling — der Fehlerzustand bleibt dauerhaft.
  - Fix-Vorschlag: `TopBar.vue` — Health-Check mit Retry-Logik (z.B. 3 Versuche mit
    1 s / 2 s / 4 s Delay) in `onMounted`. Bei Erfolg auf 'ok' setzen. Zusätzlich
    optionaler Polling-Interval (z.B. alle 30 s) um spätere Backend-Ausfälle zu
    erkennen. Alternativ: `start-app.ps1` im Release-Modus vor dem Browseröffnen auf
    den `/health`-Endpunkt warten (curl-Loop).

## History

_Append-only, newest first._

- 2026-08-31 — **M5.1–M5.7 implemented.** Added `vue-router@4` + `wavesurfer.js@7`
  to `webui/package.json`. App shell: dark-theme `App.vue` (CSS vars on `:root`),
  `Sidebar.vue` (4 nav groups + Presets), `TopBar.vue` (health/TensorBoard
  status), `router/index.js` (9 lazy routes), `main.js` registers router + Pinia.
  API-client expansion to all 22 backend endpoints in
  `api/apiClient.js` + `mocks/fixtures.js` + `mocks/mockApiClient.js` (mock-data
  seam). Views: `UploadIngestionView`, `DatasetManagerView`,
  `PreprocessingView` + `PitchConfidenceIndicator`, `TrainingConfigView` +
  `PresetSaveDialog`, `TrainingDashboardView` (TensorBoard iframe/fallback +
  polling), `InferencePlaygroundView` + `ABComparisonPlayer`,
  `ModelExportView`, `PresetManagerView`. Vitest M5.7: 8 new render tests in
  `tests/views-batch1.test.js` + `tests/views-batch2.test.js` (18 total green).
  Fixed view bugs found by tests: `PresetManagerView` v-for template scope,
  `ModelExportView` format-options rendering, `InferencePlaygroundView` file
  input v-model → change handler.
