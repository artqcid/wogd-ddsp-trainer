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

## Dual-Mode Training UI (M14)

The training configuration UI must support two parallel interaction modes that
share the same underlying Pinia store and REST contracts:

### Model Tier system

Five model tiers define which parameter groups are visible and which backend
features are activated. The tier is the primary configuration axis:

| Tier | Milestone | Description | Min. GPU |
|---|---|---|---|
| `standard` | M1–M6 | Standard DDSP (HarmonicOscillator + FilteredNoise) | 4 GB |
| `component` | M7.2 | Standard + explicit harmonic/noise balance controls | 4 GB |
| `hacks` | M8 | Component + DDSPVariant synthesis hacks (FM, PD, LFO…) | 4 GB |
| `engine` | M9/M10 | Hacks + alternative synth engine (Sinusoidal/CombSub/NEWT) | 4 GB |
| `advanced` | M11–M13 | Engine + VAE latent space / PolyDDSP / Voice Conversion | 6–12 GB |

### Mode A — Wizard (simple users)

A `WizardModal` opens automatically on first visit to Training Config (when
`useModelConfigStore().wizardCompleted === false`). It guides the user through
three steps:

1. **Model Tier card grid** — one card per tier showing name, description,
   GPU-feasibility badge (✓ fits / ⚠ needs N GB), and a short "what it does"
   tooltip. GPU feasibility is pre-fetched via `GET /api/gpu/feasibility` (one
   call, all tiers in the response).
2. **Quality / Preset selector** — FAST / NORMAL / QUALITY cards showing
   estimated VRAM usage and hidden_size for the current GPU, plus an optional
   "load custom preset" selector filtered to the chosen tier.
3. **Target mode** — Offline / Studio vs. Realtime / Low-Latency with export
   format summary.

Wizard completion writes `activeTier`, `selectedPreset`, and `targetMode`
into the Pinia `modelConfig` store and closes the modal. A "Skip — I know
what I'm doing" link is always visible (skips to Mode B with `activeTier`
defaulting to `standard`). Power-users can reopen the Wizard at any time via
the "⚙ Reconfigure Model" button in the Training Config header.

### Mode B — Power-User Tabs (advanced users)

`TrainingConfigView` renders a **tab bar** once `activeTier` is set. Tabs
map 1:1 to tiers:

| Tab | Visible when tier ≥ | Content |
|---|---|---|
| **Core** | always | Preset selector, ML params (LR/batch/epochs), target mode, decoder type, reverb toggle |
| **Component** | `component` | n_harmonics / n_filter_banks sliders (link to ComponentMixerView) |
| **Hacks** | `hacks` | DDSPVariant flags (waveform, FM depth/ratio, PD, LFO, wavetable, angular cumsum, loss band mask) — surfaced from SynthHacksView |
| **Engine** | `engine` | Engine dropdown (harmonic / sinusoidal / combsub / NEWT) + engine-specific params |
| **Advanced** | `advanced` | VAE (use_latent, latent_dim, kl_beta), PolyDDSP (n_voices), Voice Conversion (use_content_encoder, encoder name) |

Tabs with tier > `activeTier` are rendered **disabled** (greyed, not hidden).
Clicking a disabled tab shows a tooltip: "Switch to tier 'Engine' to unlock
this tab" with an inline "Upgrade tier" link that reopens Step 1 of the Wizard.
No parameters are blocked or removed from the DOM — the tab structure is
purely a UX affordance.

### GPU Feasibility Banner

A `GpuFeasibilityBanner` component is permanently displayed at the top of
`TrainingConfigView` (below the global top bar). It shows:

- GPU name, total VRAM, available VRAM, VRAM tier.
- Current config: estimated VRAM usage + fit/warning indicator.
- Reactive updates: re-fetches `GET /api/gpu/feasibility` whenever `activeTier`,
  `n_voices`, `use_latent`, or `use_content_encoder` changes in the store.
- Proactive multi-tier summary: inline chip list showing which other tiers
  would/would not fit on this GPU (visible but non-intrusive).

### Preset system compatibility

The existing FAST / NORMAL / QUALITY presets remain fully unchanged for
`model_tier = 'standard'`. Extensions:

- Every preset carries a `model_tier` field (DB column + API field,
  default `'standard'`).
- Built-in presets for non-standard tiers (`engine`, `advanced`) are generated
  on startup from the same VRAM-relative scaling rules (25/50/100 %) but
  include tier-specific param fields (engine, n_voices, use_latent, etc.).
- When a preset's `model_tier` does not match the active tier, the UI shows a
  **Rebase warning**: "This preset was created for a different model type —
  transfer the compatible parameters?" The user can accept (rebase) or cancel.
- Custom presets are always saved with the current `activeTier`.
- On GPU hardware change, custom presets for all tiers are re-clamped with a
  per-tier warning (same mechanism as the existing hardware-change detection).

### Pinia store: `useModelConfigStore`

All state shared between the Wizard, the Tab view, the GPU banner, and the
Preset selector lives in a single store:

```js
// webui/src/stores/modelConfig.js
{
  activeTier: null,          // null → Wizard not yet completed
  wizardCompleted: false,
  gpuFeasibility: null,      // response from GET /api/gpu/feasibility
  selectedPreset: null,
  targetMode: 'offline',
  coreParams:     { learning_rate, batch_size, epochs, decoder_type, use_reverb },
  componentParams:{ n_harmonics, n_filter_banks },
  hacksVariant:   { /* DDSPVariant fields */ },
  engineParams:   { engine, newt_hidden, newt_layers },
  advancedParams: { use_latent, latent_dim, kl_beta, n_voices,
                    use_content_encoder, content_encoder_name },
}
```

Actions: `setTierFromWizard(tier, preset, targetMode)`,
`checkFeasibility()` (calls `GET /api/gpu/feasibility`), `resetToWizard()`.

### New and changed Vue components (M14)

New:

- `WizardModal.vue` — 3-step modal; opens when `!wizardCompleted`.
- `ModelTierCard.vue` — single tier card (icon, name, GPU badge, tooltip).
- `GpuFeasibilityBanner.vue` — persistent reactive banner.
- `TabCore.vue`, `TabComponent.vue`, `TabHacks.vue`, `TabEngine.vue`,
  `TabAdvanced.vue` — tab content panels extracted from / extending
  `TrainingConfigView`.

Changed:

- `TrainingConfigView.vue` — becomes a tab-wrapper + banner host; delegates
  param sections to the Tab components; tier-awareness via store.
- `PresetManagerView.vue` — `model_tier` filter in preset list.
- `Sidebar.vue` — no structural change; Wizard reopen button lives in
  `TrainingConfigView` header only.
- `webui/src/stores/` — new `modelConfig.js` store.
- `webui/src/mocks/mockApiClient.js` + `fixtures.js` — add `tier_feasibility`
  fixture, `model_tier` field on preset fixtures.

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
  Preset" dialog. **Extended in M14:** tab-based, tier-aware (see Dual-Mode
  Training UI section above).
- `TrainingDashboardView` — TensorBoard embed (iframe/fallback link), run
  controls, optional REST checkpoint-audio player + "Save as Preset" button
  in run detail.
- `InferencePlaygroundView` — timbre transfer + shaping controls + A/B player.
- `ModelExportView` — weight download with format selection (Neutone / ONNX /
  TorchScript).
- `PresetManagerView` — list/edit/delete custom presets (values clamped to
  GPU bounds); view built-in presets (read-only). **Extended in M14:**
  `model_tier` filter column.

Shared components:

- `AudioPlayer` / `WaveformView` — checkpoint/reconstruction playback and
  waveform rendering (Wavesurfer.js).
- `ABComparisonPlayer` — synchronized source vs. target playback with solo/mute.
- `PitchConfidenceIndicator` — F0 confidence warning.
- `ConfigFormPanel`, `RunStatusBadge` — shared form/status primitives.

Data layer:

- API-client interface (REST) + `MockApiClient` implementation and fixtures
  under `webui/src/mocks/` for offline/mock mode. **Extended in M14:**
  `tier_feasibility` fixture + `model_tier` on preset fixtures.

## Acceptance criteria

- Every view renders and is testable with mock data (Vitest) without a running
  backend.
- Decoupling rule enforced: no backend imports inside `webui/`.
- Export formats restricted to the PyTorch stack (Neutone/ONNX/TorchScript).
- Project checks green per Definition of Done (`ruff`, `pytest`, `vitest`).
- **M14 additional:** `WizardModal` completes without a backend (mock feasibility
  fixture); all five Tab components render independently with mock data;
  `GpuFeasibilityBanner` renders in all three states (fits / warning / no-GPU).

## References

- `plan.md` — milestone M5 (UI) + M7 (experimental) + M14 (Dual-Mode UI), tech stack decision.
- `checklist.md` — M5.x / M7.x / M14.x open UI tasks.
- `experimental-ddsp.md` — rationale for the M7 experimental UI features.
- `architecture.md` — backend-UI interface, data/event contracts, M14 backend extensions.
- `coding-standards.md` — coding rules (CCD).
