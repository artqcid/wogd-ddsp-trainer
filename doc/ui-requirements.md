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
- **Custom VST** (wogd realtime plugin, TorchScript + `param_manifest`, up to 16 params)

No TensorFlow (`SavedModel`/TFLite) artifacts are produced; the model/training
stack is PyTorch (see `plan.md`).

#### `ModelParameterBuilder` (mandatory sub-component of `ModelExportView`)

The parameter builder is the single place where users configure **inference
runtime parameters** (VST knobs) before export. It is entirely separate from the
training config flow. Requirements:

- **Dual-section layout:**
  - *Neutone FX section* — always 4 slots (hard limit from Neutone SDK). Names,
    descriptions, and defaults are editable. Slot assignments shown visually as
    knob cards.
  - *Custom VST section* — visible only for `model_tier ≥ component`. Allows
    4 to 16 parameters total. Shows per-tier auto-suggested parameters as a
    starting point; user can add, remove, rename, and reorder.
- **Tier-aware defaults:** on first open, the builder is pre-filled with
  tier-specific default parameters (names, min/max/default, mapping) via
  `GET /api/models/{run_id}/{checkpoint}/params`. The user never starts with
  an empty form.
- **Neutone slot assignment (drag & drop):** for experimental models with >4
  parameters, the user drags any 4 from the full list into the 4 Neutone slots.
  Parameters not assigned to a Neutone slot are labelled "Custom VST / API only".
- **Parameter customization fields per slot/card:**
  - Name (max 30 chars, validated)
  - Description (max 150 chars)
  - Type: `continuous` (min/max/default) or `categorical` (labels list)
  - Mapping curve: `linear` | `log` | `exp`
  - Unit hint (free text, displayed as suffix in VST UI)
  - Group tag (e.g. "Pitch", "Texture", "Latent")
- **VAE latent parameter labelling:** for `advanced` tier with `use_latent=true`,
  latent dimension cards show a "Label" button that opens a synthesis preview:
  the model renders audio at extreme values of that dimension, helping the user
  give it a meaningful name (e.g. "Roughness", "Brightness").
- **Export buttons:** `[Export → Neutone FX (.nm)]` and
  `[Export → Custom VST (.pt)]` are both visible. Each button triggers a
  format-specific export using only the appropriate parameter subset.
- **Mock-data seam:** the builder must render with a fixture `param_manifest`
  (no backend required) for Vitest and dev preview.

Full parameter handling specification: [`parameter-handling.md`](./parameter-handling.md).

## Additional required views (project milestones)

The following are required by the project milestones and must be present in the
UI:

- **Dataset manager** (M5.2): list datasets with validation status and
  train/validation split.
- **Run lifecycle** (M4.2): start/stop/resume training runs, run list/history,
  current run status.

## Visual design system (M14.2.0)

The app uses a modern AI-dashboard dark-mode design language. The single
source of truth for all visual tokens is `webui/src/style.css` (global,
imported in `main.js`). No component may hard-code a color, radius, shadow
or spacing value — all values must reference a CSS custom property from this
file.

### Design reference

Shasanko Das — *AI Content Creation & Analytics SaaS Dashboard – Dark Mode
UI/UX* (Dribbble shot 27444658, published Aug 2026 via Muzli). Adopted
visual traits:

- Deep indigo-black backgrounds (not neutral grey)
- Primary accent: Indigo/Violet `#6366F1` — model, training, interactive
- Secondary accent: Cyan `#06B6D4` — audio, waveform, inference
- Cards: `border-radius: 16px`, glass-morphism border, subtle shadow + glow
- Active states: gradient fill + inward glow, not flat highlight
- Typography: Inter variable font (300–700), JetBrains Mono for numeric values
- Status indicators: pill-shaped `.badge` with semantic color, not plain dots
- Spacing: generous (base 4 px scale, `gap: 24px` in card grids)

### Token categories (defined in `webui/src/style.css`)

| Category | Key tokens |
|---|---|
| Backgrounds | `--bg-base` `--bg-primary` `--bg-secondary` `--bg-tertiary` `--bg-elevated` `--bg-glass` |
| Text | `--text-primary` `--text-secondary` `--text-muted` `--text-on-accent` |
| Primary accent | `--accent` `--accent-light` `--accent-dark` `--accent-glow` `--accent-subtle` |
| Secondary accent | `--accent-2` `--accent-2-light` `--accent-2-dark` `--accent-2-glow` `--accent-2-subtle` |
| Semantic | `--success` `--warning` `--error` `--info` (each with `-subtle` variant) |
| Borders | `--border` `--border-strong` `--border-accent` `--border-accent-2` |
| Shadows | `--shadow-xs` `--shadow-sm` `--shadow-md` `--shadow-lg` `--shadow-glow` `--shadow-card` |
| Radii | `--radius-xs(4)` `--radius-sm(8)` `--radius-md(12)` `--radius-lg(16)` `--radius-xl(20)` `--radius-pill` |
| Spacing | `--space-1` … `--space-12` (4 px scale) |
| Typography | `--font-sans` (Inter) `--font-mono` (JetBrains Mono) · `--text-xs`…`--text-2xl` · `--weight-light`…`--weight-bold` |
| Motion | `--transition-fast(100ms)` `--transition-base(160ms)` `--transition-slow(260ms)` |
| Layout | `--sidebar-width(220px)` `--topbar-height(52px)` `--z-*` |

### Global utility classes

Defined in `style.css`, available in all components without import:

- **Cards:** `.card` `.card-accent` `.card-header` `.card-icon` (`.cyan` `.green` `.amber` variants)
- **Buttons:** `.btn-primary` `.btn-secondary` `.btn-ghost` `.btn-cyan` + `.btn-sm` `.btn-lg`
- **Badges:** `.badge` + `.badge-success` `.badge-warning` `.badge-error` `.badge-info` `.badge-accent` `.badge-cyan` `.badge-muted` `.badge-dot`
- **Forms:** `.form-group` `.form-label` `.checkbox-label` `.radio-group` `.radio-option`
- **Tabs:** `.tab-bar` `.tab-btn` `.tab-btn--active` `.tab-btn--disabled` `.tab-content`
- **Modals:** `.modal-overlay` `.modal-box` `.modal-box--wide` `.modal-header` `.modal-body` `.modal-footer`
- **Utilities:** `.gradient-text` `.glow-accent` `.glow-cyan` `.section` `.section-header` `.section-title` `.divider` `.grid-2/3/4` `.flex` `.flex-col` `.items-center` `.justify-between` `.gap-2/3/4` `.label` `.text-xs/sm/base/muted/secondary/accent/mono`

### Fonts

Inter (variable, 300–700) loaded via Google Fonts CDN in `webui/index.html`.
JetBrains Mono (400, 500) for numeric/code values. Both declared in
`--font-sans` / `--font-mono` tokens and applied globally.

### Shell components (M14.2.0)

**Sidebar** (`components/Sidebar.vue`):
- Brand: SVG waveform icon (Indigo→Cyan gradient stroke) + `.gradient-text` "WOGD" wordmark
- Nav groups: emoji icon prefix on group label, thin `.sidebar-divider` between groups
- Active link: `--accent-subtle` background + 2 px `--accent` left border + `box-shadow: inset 0 0 16px rgba(99,102,241,0.08)`
- Footer: Settings link separate from main scroll area

**TopBar** (`components/TopBar.vue`):
- Left: breadcrumb section name (derived from `route.path` via static map)
- Right: pill `.badge` status indicators for Backend + TensorBoard, GPU chip badge (model + VRAM), version in mono font
- GPU chip visible when `apiClient.getHostInfo()` returns GPU data

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

### Tier identity color system (M14.2.0)

Each tier owns a **unique signal color** that is applied consistently across
every UI surface that shows tier context: the active-tab indicator, the tab
label, the Wizard tier card border/icon, the `ModelTierCard` header,
the `GpuFeasibilityBanner` tier chip, and the TopBar tier badge. The global
`--accent` (Indigo) is never repurposed for tier identity — it remains the
universal interactive / button / navigation accent.

| Tier | Color name | Hex | CSS token | Rationale |
|---|---|---|---|---|
| `standard` | **Emerald** | `#10B981` | `--tier-standard` | Familiar, "works", safe entry point |
| `component` | **Sky / Cyan** | `#06B6D4` | `--tier-component` | Precision, sliders, fine-tuning |
| `hacks` | **Amber** | `#F59E0B` | `--tier-hacks` | Experimental, caution, creative risk |
| `engine` | **Violet** | `#8B5CF6` | `--tier-engine` | Power, alternative architecture |
| `advanced` | **Rose** | `#F43F5E` | `--tier-advanced` | Expert-only, high VRAM, danger zone |

Each tier token also has a `-subtle` (12 % opacity fill) and a `-glow`
(30 % opacity) companion, following the same pattern as `--accent-subtle`
and `--accent-glow`. All six values per tier live in `style.css `:root`.

#### Surfaces where tier color must appear

1. **Tab bar** (`TrainingConfigView`): active tab's bottom border-line and
   label use the active tier's `--tier-<name>` color. Inactive (accessible)
   tabs: `--text-secondary`. Disabled (locked) tabs: `--text-muted`.
2. **Tier chip in TopBar**: a small pill badge showing the active tier name
   uses `--tier-<name>` as background (at subtle opacity) with the full color
   as text/border. Visible on every view, not just Training Config.
3. **Wizard tier cards** (`ModelTierCard`): card border and icon tint use the
   tier's signal color. The selected card gets the full color as a glowing
   border (`box-shadow: 0 0 0 2px --tier-<name>, 0 0 18px --tier-<name>-glow`).
4. **GPU Feasibility Banner**: each per-tier chip in the multi-tier summary row
   is tinted with that tier's signal color (`--tier-<name>-subtle` background,
   full color text).
5. **Sidebar nav**: the active route's left-accent bar remains `--accent`
   (Indigo) — **not** tier-colored. Tier is a model config concept, not a
   navigation concept.
6. **Disabled tab tooltip** "Upgrade to `engine`" — the tier name in the
   tooltip is rendered in that tier's color.

#### Helper: `tierColor(tier)` utility

A tiny JS utility in `webui/src/utils/tierColors.js` (no deps) maps a tier
string to its CSS custom property name and a readable label:

```js
// webui/src/utils/tierColors.js
export const TIER_META = {
  standard:  { label: 'Standard',  token: '--tier-standard',  icon: '🟢' },
  component: { label: 'Component', token: '--tier-component', icon: '🔵' },
  hacks:     { label: 'Hacks',     token: '--tier-hacks',     icon: '🟡' },
  engine:    { label: 'Engine',    token: '--tier-engine',    icon: '🟣' },
  advanced:  { label: 'Advanced',  token: '--tier-advanced',  icon: '🔴' },
}

/** Returns the resolved hex color from the CSS custom property at runtime. */
export function tierColor(tier) {
  return getComputedStyle(document.documentElement)
    .getPropertyValue(TIER_META[tier]?.token ?? '--text-muted').trim()
}

/** Returns the tier label. */
export function tierLabel(tier) { return TIER_META[tier]?.label ?? tier }

/** Returns the emoji indicator (for compact display). */
export function tierIcon(tier)  { return TIER_META[tier]?.icon  ?? '⚪' }
```

This utility is used by `ModelTierCard`, `WizardModal`, `TabCore` (tab bar
renderer), `GpuFeasibilityBanner`, and `TopBar`. It must not be imported in
any backend or server file.

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

## Audio-quality & training-UX controls (BUG-59..67)

_Binding UI specification for the Group-B open-bug batch. Added 2026-09-03 by
ARCHITECT_Openrouter after the open-bug re-analysis found that all of these controls
were described **only** inside `bugs.md` resolutions — which is not the binding UI
source of truth. Implementation plan:
[`implementation/m20-audio-quality-bugs.md`](./implementation/m20-audio-quality-bugs.md);
full bug records: [`bugs.md`](./bugs.md)._

### Governing principle: preprocessing-time vs. training-time parameters

Three of these controls (`sample_rate`, `f0_min_hz`/`f0_max_hz`, `f0_viterbi`) are
consumed during **feature extraction** and are baked into the feature cache. The
training loop reads a finished feature set and cannot retroactively change them.

**Rule (non-negotiable):** a parameter that is baked into the feature cache is
**editable only in the Preprocessing view**. Everywhere else it is rendered
**read-only**, accompanied by a "Re-run preprocessing to change" action. The UI must
never present an editable control that cannot take effect — that is a control which
lies to the user. This mirrors the coupling constraint in `architecture.md`
§"Sample rate pipeline".

| Parameter | Editable in | Read-only display in | Bug |
|---|---|---|---|
| `sample_rate` | PreprocessingView | TabCore (+ mismatch warning) | BUG-59 |
| `f0_min_hz` / `f0_max_hz` | PreprocessingView | TabCore | BUG-60 |
| `f0_viterbi` | PreprocessingView (CREPE backend only) | TabCore | BUG-61 |
| `warm_start_checkpoint` | Wizard + TabCore | — | BUG-62 |
| `max_steps` epoch hint | — (derived, read-only) | TabCore | BUG-63 |
| Model Card fields | ModelExportView | — | BUG-64 |
| Pitch-range reference | PreprocessingView (helper) | — | BUG-67 |

### 7. Preprocessing controls (`PreprocessingView.vue`)

**7.1 Sample-rate selector (BUG-59).** A `<select>` bound to the preprocessing
request, options `16000 | 22050 | 44100 | 48000`, default **48000**
("DAW standard — recommended"); `16000` is labelled "Fast iteration, low quality"
and shows the inline hint "16 kHz is phone quality — use only for fast experiments".
The chosen rate is persisted with the dataset and is what all later views display.

**7.2 F0 range inputs (BUG-60).** Two number inputs `f0_min_hz` / `f0_max_hz`,
defaults **80 / 1100**, placed **above** the "Run Preprocessing" button. Client-side
validation mirrors the backend: `0 < min < max` and `max < sample_rate / 2` (Nyquist).
An invalid combination disables the Run button and shows the reason inline — it must
never be silently clamped.

**7.3 Viterbi smoothing checkbox (BUG-61).** `[x] F0 Viterbi smoothing (recommended)`,
default checked, help text: "Disable for instruments with continuous pitch slides
(theremin, fretless bass, bowed strings)." **CREPE-only:** when the parselmouth
backend is active the control is rendered disabled with the hint "Only available with
the CREPE pitch tracker" — never silently ignored.

**7.4 Instrument pitch-range reference (BUG-67).** A collapsible
`<details><summary>Instrument Pitch Range Reference</summary>` panel directly below
the F0 range inputs. Renders a table of common instrument ranges (voice types, strings,
winds, plus a "General voice 80–1100 Hz" catch-all) with a "Use this range" action per
row that fills the two inputs. Inline data — no API call. A selected range that would
violate the Nyquist guard at the current sample rate must surface the same warning as
7.2 rather than being applied silently.

**7.5 Re-preprocessing consequence warning.** Because 7.1–7.3 invalidate the feature
cache, changing any of them for an already-preprocessed dataset must show a
confirmation: "This re-extracts all features for this dataset. Existing runs that used
the previous settings remain valid but cannot be resumed against the new features."

### 8. Training-config additions (`TabCore.vue`)

**8.1 Cached-parameter display (BUG-59/60/61).** Read-only display of the selected
dataset's `sample_rate`, F0 range and Viterbi flag, each with a
"Re-run preprocessing to change" link that routes to the Preprocessing view with the
dataset preselected. **No editable duplicates of these fields.**

**8.2 Sample-rate mismatch guard (BUG-59).** When the run config's `sample_rate`
differs from the selected dataset's cached rate, show a blocking warning with a
"Re-run preprocessing at N Hz" CTA. This is the UI half of the backend's 409 guard —
starting training in this state must be prevented client-side, not merely rejected
server-side.

**8.3 Estimated-epochs hint (BUG-63).** Below the `max_steps` input, a read-only line
`≈ N epochs on selected dataset`, derived from the diagnostics payload
(`total_chunks`, `slice_length`) and `batch_size`. Purely informational — it never
constrains or rewrites `max_steps`. When no dataset is selected or diagnostics are
unavailable, the line is hidden behind the tooltip "Select and preprocess a dataset to
see epoch estimate".

**8.4 Warm-start selector (BUG-62).** A `warm_start_checkpoint` dropdown:
`None` (default) / `Pretrained base model (harmonic sweep)` /
`Custom checkpoint (pick file)`. The base-model option is **disabled with an
explanatory hint when the asset is not available locally and cannot be fetched**
(the asset is downloaded on first use, not shipped in the repo). Selecting it shows a
one-line description of what the base model was trained on. The wizard carries the
same option as a simple toggle, default off.

### 9. Export model card (`ModelExportView.vue`, BUG-64)

A collapsible `<details><summary>Model Card (Neutone metadata)</summary>` section
**above** the export buttons, with fields `model_name` (text, required),
`model_author` (text), `short_description` (text, max 100 chars),
`long_description` (textarea, max 500 chars), `is_experimental` (checkbox, default
checked) and `model_version` (text, default `1.0.0`). Pre-filled from the checkpoint's
stored model card on mount; saved explicitly via a "Save Model Card" button.
**Both the Neutone FX and the MIDI Synth export buttons are disabled while
`model_name` is empty**, with the reason shown inline — a nameless export is unusable
in a DAW plugin list and cannot be submitted to the Neutone marketplace.

### Mock-data seam (Group B)

The mock-first rule applies unchanged: every control above must render and be testable
with `MockApiClient` alone. Required fixture extensions in
`webui/src/mocks/fixtures.js`: `sample_rate`, `f0_min_hz`, `f0_max_hz`, `f0_viterbi`
and `warm_start_checkpoint` on all preset fixtures; a `diagnosticsFixture` carrying
`files_processed`, `total_chunks`, `avg_duration_s`, `slice_length` and the requested
plus detected F0 range; and a `modelCardFixture`.

### Acceptance criteria (Group B)

- No feature-cache parameter is editable outside the Preprocessing view.
- Every invalid F0/Nyquist combination blocks the action with an inline reason;
  nothing is silently clamped or ignored.
- The Viterbi control is visibly disabled (not hidden, not ignored) on the
  parselmouth backend.
- Changing a feature-cache parameter on a preprocessed dataset requires explicit
  confirmation.
- A `sample_rate` mismatch is caught in the UI before the request is sent.
- Export is impossible without a model name.
- All of the above render from mock fixtures with no backend running.

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
- `bugs.md` — open-bug records behind §"Audio-quality & training-UX controls (BUG-59..67)".
- `implementation/m19-bug-fixes.md` — SPA / training-lifecycle fix batch (BUG-52..58).
- `implementation/m20-audio-quality-bugs.md` — audio-quality & training-UX batch (BUG-59..67).
