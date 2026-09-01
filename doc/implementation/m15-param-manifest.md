---
type: implementation-plan
status: draft
milestone: M15 - Parameter Manifest Backend
generated:
  by: ARCHITECT_Openrouter
  at: 2026-09-01
stale_after: 2027-06-01
---

# Implementation Plan — M15 Parameter Manifest Backend

_Granular plan for milestone M15. Meta plan: [`../plan.md`](../plan.md);
status: [`../checklist.md`](../checklist.md).
Full spec: [`../parameter-handling.md`](../parameter-handling.md).
Prerequisite: M3 (model + checkpoint save), M4 (REST backend), M6 (export
infrastructure). M14 recommended but not strictly required (tier constants
already defined in `server/presets.py`)._

---

## Goal

Introduce a **`ParamManifest`** — a structured, serializable description of
a checkpoint's ≤16 inference runtime parameters — that travels with the
checkpoint, drives the Neutone FX export (≤4 params) and the Custom VST export
(≤16 params), and is editable via REST before any export.

Key invariant: **no model weights are changed** by any step in this milestone.
The manifest is metadata stored alongside weights in the `.pt` state dict.

---

## Constraints & principles

- **Backward compatibility (mandatory).** Loading an old checkpoint without
  `param_manifest` must succeed silently (generate tier-defaults on the fly).
  No migration step required for existing checkpoints.
- **Backend-only.** No frontend work in this milestone; the UI lands in M16.
- **One subagent per step.** Each step targets a single file (scope pinning).
  Primary agent verifies diff + runs `ruff check` + `pytest` after every step.
- **No VRAM impact.** The manifest is pure metadata; it adds zero to training
  or inference memory cost.
- **TorchScript compatibility.** The Custom VST wrapper must be
  `torch.jit.script`-able without errors on the export path.

---

## File map

```
model/param_manifest.py                NEW  — InferenceParam + ParamManifest dataclasses
                                              + tier-default builders (M15.1 + M15.2)
train/trainer.py                       MOD  — embed param_manifest in save_checkpoint (M15.3)
server/routes/models.py                MOD  — GET + PUT /api/models/{run}/{ckpt}/params (M15.4 + M15.5)
inference/export.py                    MOD  — Neutone export reads manifest dynamically (M15.6)
inference/export_custom_vst.py         NEW  — CustomVSTWrapper + export_custom_vst() (M15.7)
server/routes/models.py                MOD  — POST …/export/custom-vst endpoint (M15.7)
server/routes/inference.py             MOD  — extend synthesize endpoint to N params (M15.8)
tests/test_param_manifest.py           NEW  — pytest: dataclass, serialization, defaults (M15.1–M15.2)
tests/test_checkpoint_manifest.py      NEW  — pytest: save/load round-trip (M15.3)
tests/test_model_params_endpoint.py    NEW  — pytest: GET + PUT params endpoints (M15.4–M15.5)
tests/test_export_neutone_manifest.py  NEW  — pytest: dynamic Neutone wrapper from manifest (M15.6)
tests/test_export_custom_vst.py        NEW  — pytest: CustomVSTWrapper + export (M15.7)
tests/test_inference_n_params.py       NEW  — pytest: synthesize with N params (M15.8)
```

---

## Step M15.1 — `model/param_manifest.py`: core dataclasses

**File:** `model/param_manifest.py` (NEW)

**What:**
- `@dataclass InferenceParam` with fields:
  - `slot: int` — 1-based, unique within manifest, 1..16
  - `name: str` — max 30 chars
  - `description: str` — max 150 chars
  - `param_type: str` — `"continuous"` | `"categorical"`
  - `min_value: float` — default 0.0
  - `max_value: float` — default 1.0
  - `default_value: float`
  - `mapping: str` — `"linear"` | `"log"` | `"exp"`, default `"linear"`
  - `unit_hint: str` — free label suffix, default `""`
  - `group: str` — grouping tag, default `""`
  - `neutone_slot: int | None` — 1..4 or None (Custom/API only)
- `@dataclass ParamManifest` with fields:
  - `format: str = "wogd-vst-params"`
  - `version: str = "1.0"`
  - `params: list[InferenceParam]`
  - Properties: `neutone_params` (sorted by neutone_slot, ≤4), `custom_vst_params` (all ≤16, sorted by slot)
  - Methods: `to_dict() -> dict`, `from_dict(d: dict) -> ParamManifest` (classmethod)
  - Validation in `__post_init__`: slots unique, ≤16 total, neutone_slots unique & ∈ {1,2,3,4}, names ≤ 30 chars
- Module-level validator: `validate_manifest(m: ParamManifest) -> list[str]` — returns list of error strings (empty = valid)

**Tests (`tests/test_param_manifest.py`):**
- Round-trip `to_dict()` → `from_dict()` identity
- `neutone_params` returns only those with neutone_slot set, sorted
- `custom_vst_params` returns all, sorted by slot
- Validation: duplicate slots → error, >16 params → error, name >30 chars → error, neutone_slot >4 → error

---

## Step M15.2 — `model/param_manifest.py`: tier-default builders

**File:** `model/param_manifest.py` (continuation of M15.1, same file)

**What:**
- Private factory functions (not exported, used by `build_default_manifest`):
  - `_standard_manifest() -> ParamManifest`
    — slots 1–4: `Pitch Shift`, `Loudness`, `Noise Level`, `Reverb Mix`; all neutone_slots 1–4
  - `_component_manifest() -> ParamManifest`
    — slots 1–4 as standard but slot 3 = `Harmonic Blend`, slot 4 = `Noise Blend`;
    slots 5–6: `Reverb Mix`, `Spectral Spread` (neutone_slot=None)
  - `_hacks_manifest(variant_flags: dict) -> ParamManifest`
    — detects active hack: `fm_depth > 0` → FM-preset (P3=`FM Depth`, P4=`FM Ratio`, P5=`LFO Rate`, P6=`LFO Depth`);
    `wavetable_on` → wavetable-preset (P3=`Wavetable Pos`, P4=`Noise Level`, P5=`Phase Distort`, P6=`Harmonic Dirt`);
    `pd_k > 0` → PD-preset (P3=`PD Amount`, P4=`Waveshape`);
    fallback → standard 4
  - `_engine_manifest(engine: str) -> ParamManifest`
    — dispatch on `engine`: `"harmonic"` → standard; `"sinusoidal"` → (P3=`Inharmonicity`, P4=`Spectral Spread`, P5=`Partial Density`, P6=`Brightness`);
    `"combsub"` → (P3=`Formant Shift`, P4=`Brightness`, P5=`Vowel`, P6=`Roughness`);
    `"newt"` → (P3=`Tone Character`, P4=`Saturation`, P5=`MLP Layer Bias`, P6=`Odd Harmonics`)
  - `_advanced_manifest(variant_flags: dict) -> ParamManifest`
    — VAE if `use_latent=True`: P1=`Pitch Shift`, P2=`Loudness`, P3=`Timbre Z1`, P4=`Timbre Z2` (neutone 1–4), P5–P10=`Timbre Z3`..`Z8` (neutone_slot=None);
    PolyDDSP if `n_voices > 1`: P3=`Voice Balance`, P4=`Detune`, P5=`Voice Spread`, P6=`Unison Width`;
    VC if `use_content_encoder`: P3=`Style Transfer`, P4=`Formant Scale`, P5=`Breathiness`, P6=`Speaker Blend`;
    fallback → standard 4
- Public entrypoint: `build_default_manifest(model_tier: str, variant_flags: dict) -> ParamManifest`
  — dispatches to the correct private factory; unknown tier → `_standard_manifest()`

**Tests (extend `tests/test_param_manifest.py`):**
- Each factory: correct slot count, correct Neutone-slot assignments, correct names
- `build_default_manifest("standard", {})` → 4 params, all neutone_slots set
- `build_default_manifest("component", {})` → 6 params, 4 neutone, 2 custom
- `build_default_manifest("engine", {"engine": "newt"})` → 6 params, correct names
- `build_default_manifest("advanced", {"use_latent": True, "latent_dim": 32})` → 10 params, 4 neutone

---

## Step M15.3 — Checkpoint embedding (`train/trainer.py`)

**File:** `train/trainer.py`

**What:**
- In `Trainer.save_checkpoint(step, loss)`:
  - If `state` does not yet contain `"param_manifest"`: generate defaults via
    `build_default_manifest(self.model_tier, self.variant_flags)` and embed.
  - If already present (manifest was set via PUT endpoint): preserve as-is.
  - Add `model_tier: str` and `variant_flags: dict` as constructor params to
    `Trainer.__init__` (both default to `"standard"` / `{}`).
  - Backward compat: `build_training()` in `server/tasks.py` passes these from
    `model_config`; existing call sites that omit them stay valid.
- In `Trainer.load_checkpoint(path)`:
  - If `state["param_manifest"]` absent → silently generate defaults from stored
    `model_tier` / `variant_flags` keys (also add backward compat for those).
  - Expose `self.param_manifest` property returning `ParamManifest`.

**Tests (`tests/test_checkpoint_manifest.py`):**
- `save_checkpoint` → state dict contains `"param_manifest"` key
- Load checkpoint → `trainer.param_manifest` is a valid `ParamManifest`
- Load old checkpoint (no manifest key) → returns default manifest without error
- `model_tier="engine"`, `variant_flags={"engine": "newt"}` → manifest has NEWT names

---

## Step M15.4 — REST: `GET /api/models/{run_id}/{checkpoint}/params`

**File:** `server/routes/models.py`

**What:**
- New route: `GET /api/models/{run_id}/{checkpoint}/params`
  - Loads the checkpoint file (`runs/<run_id>/checkpoints/<checkpoint>.pt`)
  - Reads `param_manifest` from state (or generates defaults)
  - Returns `ParamManifest.to_dict()` as JSON response
  - 404 if run_id or checkpoint not found
  - No model weights are loaded into GPU; use `torch.load(..., map_location="cpu", weights_only=False)` with safe-globals context for `DDSPConfig`

**Response shape:**
```json
{
  "format": "wogd-vst-params",
  "version": "1.0",
  "n_params": 6,
  "neutone_slots": [1, 2, 3, 4],
  "params": [
    { "slot": 1, "name": "Pitch Shift", "description": "...",
      "param_type": "continuous", "min_value": -24.0, "max_value": 24.0,
      "default_value": 0.0, "mapping": "linear", "unit_hint": "semitones",
      "group": "Pitch", "neutone_slot": 1 },
    ...
  ]
}
```

**Tests (`tests/test_model_params_endpoint.py`):**
- GET on known checkpoint → 200 + correct manifest structure
- GET on unknown run_id → 404
- GET on old checkpoint (no manifest key) → 200 + default manifest (no crash)

---

## Step M15.5 — REST: `PUT /api/models/{run_id}/{checkpoint}/params`

**File:** `server/routes/models.py`

**What:**
- New route: `PUT /api/models/{run_id}/{checkpoint}/params`
  - Body: full `params` array (same shape as GET response)
  - Validate: `validate_manifest()` must return no errors
  - Load checkpoint CPU-only, replace `state["param_manifest"]` with new dict, `torch.save` back
  - Return 200 + updated manifest on success; 422 + error list on validation failure
  - 404 if checkpoint not found
- No weight data is read beyond the state dict header; keep load/save cheap.

**Tests (extend `tests/test_model_params_endpoint.py`):**
- PUT with valid body → 200, GET after PUT returns updated names
- PUT with >16 params → 422 + error detail
- PUT with >4 neutone_slots → 422
- PUT on missing checkpoint → 404

---

## Step M15.6 — Neutone export: dynamic manifest-driven wrapper

**File:** `inference/export.py`

**What:**
- Locate the existing `NeutoneWrapperModel` / `DDSPNeutoneWrapper` (or equivalent).
- Change `get_neutone_parameters()`:
  - Previously: hardcoded 2–4 params (pitch_shift, loudness_shift, …)
  - Now: load `ParamManifest` from the passed checkpoint state; iterate
    `manifest.neutone_params` (sorted by neutone_slot); build a
    `ContinuousNeutoneParameter` for each (using name, description, min, max, default).
  - Assert `len(manifest.neutone_params) <= 4` (SDK hard limit; raise `ValueError` with clear message if violated).
- Change `do_forward_pass(x, params)`:
  - Map `params` dict (keyed by parameter name) to the model's forward call.
  - Standard mapping: slot 1 → pitch_shift, slot 2 → loudness_shift.
  - Additional slots: pass as kwargs to `model.forward()` if the model accepts them,
    else ignore with a logged warning (safe fallback).
- Backward compat: if no manifest is present in checkpoint, fall back to old 2-param behavior.

**Tests (`tests/test_export_neutone_manifest.py`):**
- Wrapper with standard manifest → `get_neutone_parameters()` returns 4 params with correct names
- Wrapper with custom names → names appear in `NeutoneParameter.name`
- Wrapper with 5 neutone_slots → `ValueError` raised on init (not export-time)
- Old checkpoint (no manifest) → fallback to 2-param behavior without crash

---

## Step M15.7 — Custom VST export: new wrapper + endpoint

### M15.7a — `inference/export_custom_vst.py` (NEW)

**What:**
- `class CustomVSTWrapper(nn.Module)`:
  - Constructor: `__init__(self, model: nn.Module, manifest: ParamManifest)`
  - Stores `manifest.to_dict()` as a JSON string buffer (TorchScript-compatible: `self.param_manifest_json: str`)
  - `forward(self, audio: Tensor, params: Dict[str, Tensor]) -> Tensor`
    — maps param names from dict → model forward kwargs; unrecognised params logged + ignored
  - `@torch.jit.export def get_param_manifest_json(self) -> str` — returns the embedded JSON string
    (the Custom VST plugin calls this to discover parameter layout at load time)
  - `@torch.jit.export def get_n_params(self) -> int` — returns `len(params)` for quick sanity check
- `def export_custom_vst(checkpoint_path: str, output_path: str) -> None`:
  - Loads checkpoint CPU-only
  - Reads or generates `ParamManifest`
  - Instantiates `CustomVSTWrapper`
  - `torch.jit.script(wrapper)` → saves as `.pt` TorchScript
  - Validates ≤ 16 params before scripting (raises `ValueError` if exceeded)

### M15.7b — New REST endpoint

**File:** `server/routes/models.py`

- `POST /api/models/{run_id}/{checkpoint}/export/custom-vst`
  - Calls `export_custom_vst(checkpoint_path, output_path)` synchronously (fast; CPU only)
  - Returns `FileResponse` of the generated `.pt` file
  - 404 if checkpoint not found; 422 if manifest is invalid

**Tests (`tests/test_export_custom_vst.py`):**
- `CustomVSTWrapper` is TorchScript-scriptable (no errors)
- `get_param_manifest_json()` round-trips back to `ParamManifest` correctly
- `export_custom_vst()` produces a file; re-loading the `.pt` + calling `get_param_manifest_json()` works
- Manifest with 17 params → `ValueError` before scripting
- Endpoint: 200 + `.pt` file on valid checkpoint; 404 on missing checkpoint

---

## Step M15.8 — Extend inference endpoint for N params

**File:** `server/routes/inference.py`

**What:**
- `POST /api/inference/synthesize` currently accepts `pitch_shift: float` and
  `loudness_shift: float` as fixed multipart fields.
- Extend to accept an optional `params: str` (JSON-encoded dict of name→float).
- If `params` is provided: parsed and passed to the synthesis call.
- If absent: fall back to `{"pitch_shift": pitch_shift, "loudness_shift": loudness_shift}`.
- The synthesis task (`server/tasks.py::run_synthesis`) passes `params` dict through to the model wrapper's `forward()`.
- Backward compat: old clients sending only `pitch_shift`/`loudness_shift` continue to work.

**Tests (`tests/test_inference_n_params.py`):**
- Old-style call (pitch_shift + loudness_shift only) → 202, job created correctly
- New-style call (`params` JSON with 4 named params) → 202, job created correctly
- Both result in synthesis job with the correct param dict stored in DB / passed to task

---

## Step M15.9 — Full suite verification

- `ruff check .` → 0 issues
- `ruff format --check .` → 0 issues
- `pytest` → all passing (including all new test files above)

---

## Dependency notes

- M15.6 + M15.7 depend on M15.1–M15.3 (manifest must exist before wrappers can use it).
- M15.4 + M15.5 depend on M15.1 only (REST can be written as soon as the dataclass exists).
- M15.8 is independent of M15.6/M15.7 (only the param dict plumbing matters, not the wrapper).
- Steps can therefore be parallelised as: `{M15.1 → M15.2} → M15.3`, `M15.1 → {M15.4, M15.5}`, `{M15.2, M15.3} → {M15.6, M15.7}`, `M15.1 → M15.8`.

---

## History

_Append-only. Newest first._

<!-- entries added here after each completed step -->

---

## BUGS

_References to `doc/bugs.md` entries only. No full bug records here._

<!-- BUG-x refs added here if any arise during M15 -->
