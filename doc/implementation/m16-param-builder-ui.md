---
type: implementation-plan
status: draft
milestone: M16 - Parameter Builder UI
generated:
  by: ARCHITECT_Openrouter
  at: 2026-09-01
stale_after: 2027-06-01
---

# Implementation Plan — M16 Parameter Builder UI

_Granular plan for milestone M16. Meta plan: [`../plan.md`](../plan.md);
status: [`../checklist.md`](../checklist.md).
Full spec: [`../parameter-handling.md`](../parameter-handling.md),
[`../ui-requirements.md`](../ui-requirements.md) §"ModelParameterBuilder".
**Prerequisite: M15 must be complete** (backend REST endpoints for manifest
GET/PUT and both export paths must exist before any step here)._

---

## Goal

Provide the `ModelParameterBuilder` Vue component that lets users view, edit,
and assign the inference parameters of a trained checkpoint before export —
without retraining. The builder drives both the Neutone FX export (≤4 slots)
and the Custom VST export (≤16 slots), and feeds the dynamic parameter sliders
in the Inference Playground.

---

## Constraints & principles

- **Mock-data seam (mandatory).** Every component + view renders fully via
  `MockApiClient` + fixture data. No step is done until its Vitest covers all
  render states.
- **Frontend-only.** This milestone touches no Python/backend files. All REST
  calls go through the API-client abstraction.
- **Tier-aware rendering.** The Custom VST section is hidden for `standard` tier;
  VAE Latent Labelling button is only visible for `advanced/use_latent` configs.
- **One subagent per step.** Single-file scope. Primary agent verifies diff +
  runs `vitest` after every step.
- **Design system compliance.** All new components use CSS tokens from
  `webui/src/style.css`. No hard-coded colours, radii, or spacing.

---

## File map

```
webui/src/mocks/fixtures.js                   MOD  — add param_manifest fixtures (M16.1)
webui/src/mocks/mockApiClient.js              MOD  — add getCheckpointParams / updateCheckpointParams (M16.1)
webui/src/components/ParamCard.vue            NEW  — single editable parameter card (M16.2)
webui/src/components/ModelParameterBuilder.vue NEW  — full builder (Neutone + Custom VST sections) (M16.3)
webui/src/components/NeutoneSlotPanel.vue     NEW  — 4-slot Neutone assignment panel (M16.4)
webui/src/views/ModelExportView.vue           MOD  — embed builder, add Custom VST export button (M16.5)
webui/src/views/InferencePlaygroundView.vue   MOD  — dynamic N-param sliders from manifest (M16.6)
tests/ModelParameterBuilder.test.js           NEW  — Vitest: builder all tiers (M16.3)
tests/NeutoneSlotPanel.test.js                NEW  — Vitest: slot assignment, drag (M16.4)
tests/ModelExportView.test.js                 MOD  — add Custom VST export path test (M16.5)
tests/InferencePlaygroundView.test.js         MOD  — add dynamic N-param render test (M16.6)
```

---

## Step M16.1 — Mock fixtures: `param_manifest` data

**Files:** `webui/src/mocks/fixtures.js`, `webui/src/mocks/mockApiClient.js`

**What (fixtures.js):**
Add `PARAM_MANIFEST_FIXTURES` — one fixture per representative tier variant:

```js
export const PARAM_MANIFEST_FIXTURES = {
  standard: {
    format: "wogd-vst-params", version: "1.0", n_params: 4,
    neutone_slots: [1, 2, 3, 4],
    params: [
      { slot: 1, name: "Pitch Shift",  description: "F0 offset semitones",
        param_type: "continuous", min_value: -24, max_value: 24, default_value: 0,
        mapping: "linear", unit_hint: "st", group: "Pitch", neutone_slot: 1 },
      { slot: 2, name: "Loudness",     description: "Loudness offset dB",
        param_type: "continuous", min_value: -20, max_value: 20, default_value: 0,
        mapping: "linear", unit_hint: "dB", group: "Pitch", neutone_slot: 2 },
      { slot: 3, name: "Noise Level",  description: "FilteredNoise blend",
        param_type: "continuous", min_value: 0, max_value: 1, default_value: 0.5,
        mapping: "linear", unit_hint: "", group: "Texture", neutone_slot: 3 },
      { slot: 4, name: "Reverb Mix",   description: "Dry/Wet reverb",
        param_type: "continuous", min_value: 0, max_value: 1, default_value: 0.3,
        mapping: "linear", unit_hint: "", group: "Effects", neutone_slot: 4 },
    ]
  },
  component: { /* slots 1–6 with Harmonic Blend, Noise Blend + 2 custom */ },
  hacks_fm:  { /* slots 1–6 FM variant */ },
  engine_newt: { /* slots 1–6 NEWT variant */ },
  advanced_vae: { /* slots 1–10 with Timbre Z1–Z8 */ },
}
```

**What (mockApiClient.js):**
- `getCheckpointParams(runId, checkpoint)` → returns fixture keyed by the run's model_tier
- `updateCheckpointParams(runId, checkpoint, params)` → stores update in memory, returns updated manifest
  (stateful mock: subsequent `getCheckpointParams` returns the updated version)

**Vitest (quick smoke in existing `mockApiClient.test.js` or new file):**
- `getCheckpointParams` returns correct fixture shape
- `updateCheckpointParams` + re-fetch reflects the update

---

## Step M16.2 — `ParamCard.vue` (new)

**File:** `webui/src/components/ParamCard.vue`

**What:**
A single, compact, fully editable parameter card. Used inside `ModelParameterBuilder`.

Props: `param: Object` (InferenceParam shape), `index: number`, `isNeutoneAssigned: boolean`,
`readonly: boolean` (for standard tier where slots are fixed)

Emits: `update:param` (with updated param object), `remove` (index)

Layout:
```
┌────────────────────────────────────────────────────────┐
│  ⠿  [drag handle]          P{slot}    [neutone badge?] │
│  Name:        [________________]  (max 30 chars)        │
│  Description: [______________________________]          │
│  Type:  ● continuous  ○ categorical                     │
│  Min: [___]  Max: [___]  Default: [___]                 │
│  Mapping: ● linear  ○ log  ○ exp   Unit: [___]         │
│  Group: [_______________]                               │
│                            [🗑 Remove]  (if !readonly)  │
└────────────────────────────────────────────────────────┘
```

- Inline validation: name >30 chars → red border + counter; min > max → error highlight
- `isNeutoneAssigned` → shows `NEUTONE S{n}` pill badge (using `--tier-standard` color)
- `readonly=true` → all fields disabled, no Remove button (used for standard tier's 4 fixed slots)
- Emits debounced `update:param` on every field change (200 ms debounce to avoid jitter)

**Vitest (`tests/ParamCard.test.js` — new):**
- Renders with continuous param fixture: all fields populated
- Name >30 chars shows validation error
- Min > max shows validation error
- `update:param` emitted on name change
- `remove` emitted on Remove click
- `readonly=true` → no Remove button, fields disabled

---

## Step M16.3 — `ModelParameterBuilder.vue` (new, core component)

**File:** `webui/src/components/ModelParameterBuilder.vue`

**What:**
The main parameter builder. Composes `ParamCard` and `NeutoneSlotPanel` (M16.4).

Props:
- `manifest: Object` — initial `ParamManifest` from API
- `modelTier: String` — controls which sections are visible
- `readonly: boolean` — if true, no edits possible (display mode)

Emits: `update:manifest` (complete updated manifest object)

Internal state:
- `localParams: Ref<InferenceParam[]>` — copy of `manifest.params`, mutated locally
- `isDirty: Ref<boolean>` — true if localParams differs from prop
- `saveStatus: Ref<'idle'|'saving'|'saved'|'error'>`

Layout:
```
┌─────────────────────────────────────────────────────┐
│  PARAMETER CONFIGURATION         [Reset] [Save ✓]  │
│                                                      │
│  ▼ NEUTONE FX (max 4)                               │
│  [NeutoneSlotPanel — 4 cards, readonly for standard]│
│                                                      │
│  ▼ CUSTOM VST  (up to 16)  ← hidden if standard    │
│  [ParamCard × N]  [+ Add Parameter]                 │
│                                                      │
│  ─────────────────────────────────────────────────  │
│  [Export → Neutone FX (.nm)]  [Export → Custom VST (.pt)] │
└─────────────────────────────────────────────────────┘
```

Behaviour:
- `standard` tier: Neutone section shows 4 readonly `ParamCard`s (names editable only). Custom VST section hidden.
- `component`+: both sections visible. Custom VST params are fully editable `ParamCard`s.
- `+ Add Parameter` inserts a new param at next available slot (capped at 16 total). Shows warning when at 16.
- `Save` calls `updateCheckpointParams` via apiClient; sets `saveStatus`.
- `Reset` reverts `localParams` to the prop value.
- Validation gate on Export buttons: disabled if manifest has validation errors (shown inline).

**Vitest (`tests/ModelParameterBuilder.test.js` — new):**
- Renders with `standard` fixture → Custom VST section absent
- Renders with `component` fixture → both sections visible
- Renders with `advanced_vae` fixture → 10 params (4 Neutone + 6 Custom)
- Name edit on Neutone card → `update:manifest` emitted with new name
- `+ Add Parameter` → param count increments
- Save button disabled when `!isDirty`
- Save button calls `mockApiClient.updateCheckpointParams`
- Export buttons disabled when validation errors present

---

## Step M16.4 — `NeutoneSlotPanel.vue` (new) — 4-slot assignment panel

**File:** `webui/src/components/NeutoneSlotPanel.vue`

**What:**
Renders the 4 Neutone FX knob slots with drag-and-drop assignment.

Props:
- `allParams: InferenceParam[]` — full param list (assigned + unassigned)
- `readonly: boolean`

Emits: `update:slots` (new array of 4 InferenceParam | null)

Layout:
```
┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
│  KNOB 1  │  │  KNOB 2  │  │  KNOB 3  │  │  KNOB 4  │
│ Pitch    │  │ Loudness │  │ Harm Blnd│  │  ···drag │
│ ──────── │  │ ──────── │  │ ──────── │  │  here    │
│ [-24,24] │  │ [-20,20] │  │ [0,1]    │  │          │
└──────────┘  └──────────┘  └──────────┘  └──────────┘
   ↑ each slot: shows assigned param name + range
       drag a param card here to assign; drag out to unassign
```

- Uses HTML5 Drag and Drop API (no external dependency)
- Empty slot: dashed border + "drag here" label
- Occupied slot: param name, unit, range summary; drag icon to remove/swap
- `readonly=true`: no drag, no unassign
- Emits `update:slots` after every assignment change

**Vitest (`tests/NeutoneSlotPanel.test.js` — new):**
- Renders with 4 assigned params → all 4 slots show param names
- Renders with 2 assigned, 2 empty → empty slots show "drag here" label
- `readonly=true` → no drag targets active (aria-disabled)
- Slot assignment via simulated drop event → `update:slots` emitted with updated array

---

## Step M16.5 — `ModelExportView.vue` update

**File:** `webui/src/views/ModelExportView.vue`

**What:**
- Import and embed `ModelParameterBuilder` above the existing format selection section.
- On view mount: call `apiClient.getCheckpointParams(runId, checkpoint)` to load manifest;
  pass to `ModelParameterBuilder` as `:manifest`.
- Two export buttons (replacing or supplementing existing Neutone button):
  - `[Export → Neutone FX (.nm)]` → calls existing `POST /api/models/{id}/export/neutone` (unchanged)
  - `[Export → Custom VST (.pt)]` → calls new `POST /api/models/{run_id}/{checkpoint}/export/custom-vst`
  - Both buttons show a spinner while the download is in progress.
  - On success: trigger browser file download of the returned binary.
- Existing ONNX / TorchScript export buttons remain unchanged.
- `modelTier` is read from the checkpoint's manifest (or from `useModelConfigStore`) and
  passed to `ModelParameterBuilder`.

**Vitest (`tests/ModelExportView.test.js` — extend):**
- Renders with mock manifest → `ModelParameterBuilder` is present
- "Export → Neutone FX" click → `mockApiClient.exportNeutone` called
- "Export → Custom VST" click → `mockApiClient.exportCustomVST` called (new mock method)
- Both buttons disabled while a previous export is in progress

---

## Step M16.6 — `InferencePlaygroundView.vue`: dynamic N-param sliders

**File:** `webui/src/views/InferencePlaygroundView.vue`

**What:**
Currently: two fixed sliders (`pitch_shift`, `loudness_shift`).

New behaviour:
- On component mount (or when `selectedRunId` changes): call `apiClient.getCheckpointParams(runId, checkpoint)` to fetch manifest.
- Render sliders **dynamically** from `manifest.params`:
  - One `<input type="range">` per param, labelled with `name`, `unit_hint`, min/max/default.
  - Params grouped by `group` tag (collapsible group header, `group=""` → ungrouped at top).
  - Up to 16 sliders. If >8 params: groups are collapsed by default, expandable.
- On synthesize click: build `params` JSON from current slider values, send as `params` field in `POST /api/inference/synthesize`.
- **Fallback (no manifest or old checkpoint):** show the original 2-slider layout (pitch + loudness). This must never break.
- A "Reset to defaults" button below the sliders restores all to `default_value`.

**Vitest (`tests/InferencePlaygroundView.test.js` — extend):**
- Mock returns `standard` manifest (4 params) → 4 sliders rendered
- Mock returns `advanced_vae` manifest (10 params) → 10 sliders, grouped
- `getCheckpointParams` returns null → 2-slider fallback rendered
- Synthesize click with 4-param manifest → `mockApiClient.synthesize` called with correct `params` JSON
- "Reset to defaults" → all slider values reset to `default_value`

---

## Step M16.7 — Full suite verification

- `vitest run` → all tests passing (including all new + modified test files)
- `ruff check .` → 0 issues (Python side unchanged; just a sanity gate)
- `ruff format --check .` → 0 issues
- `pytest` → unchanged green (no Python changes in M16)

---

## VAE Latent Dimension Labelling (optional M16.8)

_This step is **optional** — implement if time/scope allows, defer to M16-post if not._

**File:** `webui/src/components/ParamCard.vue` (extend M16.2)

**What:**
For `advanced` tier VAE params whose `group === "Latent"`:
- Show a `[🔬 Label this dimension]` button.
- Clicking opens a compact modal: title "Explore Latent Dimension", showing three audio
  player rows labelled "Minimum", "Middle", "Maximum".
- Each row: synthesizes the model at that extreme value for this dimension (calls
  `POST /api/inference/synthesize` with `params` setting this dim to min/mid/max,
  all others to default) — or shows a mock audio player in Vitest.
- User listens, then types a name in a text field, confirms → emits `update:param` with new name.

**Vitest:**
- Modal opens on button click
- Confirm with name → `update:param` emitted with `name = "Roughness"` (example)
- Cancel → no emit

---

## History

_Append-only. Newest first._

<!-- entries added here after each completed step -->

---

## BUGS

_References to `doc/bugs.md` entries only. No full bug records here._

<!-- BUG-x refs added here if any arise during M16 -->
