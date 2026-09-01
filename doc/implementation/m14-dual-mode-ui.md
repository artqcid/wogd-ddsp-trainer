---
type: implementation-plan
status: draft
milestone: M14 - Dual-Mode Training UI + Backend Tier System
generated:
  by: ARCHITECT-agent
  at: 2026-09-01
stale_after: 2027-06-01
---

# Implementation Plan — M14 Dual-Mode Training UI + Backend Tier System

_Granular plan for milestone M14. Meta plan: [`../plan.md`](../plan.md);
status: [`../checklist.md`](../checklist.md).
Full spec:
[`../ui-requirements.md`](../ui-requirements.md#dual-mode-training-ui-m14),
[`../architecture.md`](../architecture.md#model-tier-system--dual-mode-ui-m14).
Prerequisite: none (M8–M13 are parallel; M14 is infrastructure)._

## Constraints & principles

- **Backend-first.** All Phase 1 backend steps must be complete and tested
  before any Phase 2 frontend work begins. The frontend depends on
  `GET /api/gpu/feasibility` and the `model_tier` fields in the REST API.
- **No breaking changes.** Every new field uses `model_config.get(key, default)`
  or `DEFAULT 'standard'` in SQL. Existing runs, presets, checkpoints, and
  tests must remain green throughout.
- **One subagent per step.** Each step is sized for a single focused subagent.
  Primary agent builds and runs checks after every step.
- **VRAM budget: 6 GB.** The tier system itself adds zero VRAM. The
  `estimate_model_vram()` function is a lightweight accounting layer, not
  ML code.
- **Mock-data seam (mandatory).** Every frontend component must render with
  `MockApiClient` + fixtures. A component is not done until its Vitest covers
  all render states.

---

## File map

```
Phase 1 — Backend
train/gpu.py                       MOD  — VRAMEstimate + estimate_model_vram (M14.1.1)
server/db.py                       MOD  — model_tier column + migration (M14.1.2)
server/presets.py                  MOD  — VARIANT/ENGINE/ADVANCED_KEYS, tier-aware seed (M14.1.3)
server/routes/training.py          MOD  — model_tier in requests, validate response, resume guard (M14.1.4)
server/tasks.py                    MOD  — tier-aware build_training (M14.1.5)
server/routes/host.py              MOD  — GET /api/gpu/feasibility endpoint (M14.1.6)
tests/test_gpu_feasibility.py      NEW  — pytest: estimate_model_vram + endpoint (M14.1.7)
tests/test_presets_tier.py         NEW  — pytest: tier-aware preset logic (M14.1.8)
tests/test_training_tier.py        NEW  — pytest: tier-aware build_training + resume guard (M14.1.9)

Phase 2 — Frontend
webui/src/stores/modelConfig.js    NEW  — Pinia modelConfig store (M14.2.1)
webui/src/mocks/fixtures.js        MOD  — tier_feasibility fixture + model_tier on presets (M14.2.2)
webui/src/mocks/mockApiClient.js   MOD  — getGpuFeasibility() mock (M14.2.2)
webui/src/components/ModelTierCard.vue       NEW  (M14.2.3)
webui/src/components/GpuFeasibilityBanner.vue NEW  (M14.2.4)
webui/src/components/WizardModal.vue         NEW  (M14.2.5)
webui/src/components/TabCore.vue             NEW  (M14.2.6)
webui/src/components/TabComponent.vue        NEW  (M14.2.6)
webui/src/components/TabHacks.vue            NEW  (M14.2.6)
webui/src/components/TabEngine.vue           NEW  (M14.2.6)
webui/src/components/TabAdvanced.vue         NEW  (M14.2.6)
webui/src/views/TrainingConfigView.vue       MOD  — tab-wrapper + wizard (M14.2.7)
webui/src/views/PresetManagerView.vue        MOD  — model_tier filter (M14.2.8)
tests/  (vitest)                   MOD  — M14.2.9 test suite
```

---

## Phase 1 — Backend

### M14.1.1 — `train/gpu.py`: `VRAMEstimate` + `estimate_model_vram()`

**File:** `train/gpu.py`

Add after `propose_presets()`:

```python
@dataclass
class VRAMEstimate:
    """Lightweight VRAM accounting for a model configuration.

    ``peak_gb`` is the estimated peak VRAM in GB.
    ``warning`` is a human-readable message when the estimate exceeds a
    known threshold (e.g. PolyDDSP N>2 on 6 GB), or ``None``.
    """
    peak_gb: float
    warning: str | None = None


def estimate_model_vram(
    model_tier: str,
    n_voices: int = 1,
    use_latent: bool = False,
    use_content_encoder: bool = False,
) -> VRAMEstimate:
    """Estimate peak VRAM in GB for a given model configuration.

    Base figures from architecture.md VRAM budget table
    (batch_size=1, seq_len=2 s @ 16 kHz, mixed precision, 3-scale STFT):

        baseline (standard DDSP)        ~2.2 GB
        use_latent (+GRUEncoder/VAE)    +0.15 GB
        use_content_encoder (+HuBERT)   +0.36 GB
        PolyDDSP N voices               baseline × N

    All tiers from 'standard' through 'engine' have the same baseline;
    'advanced' activates the optional overhead params.
    """
    BASELINE_GB = 2.2
    overhead = 0.0
    warning = None

    if model_tier == "advanced":
        if use_latent:
            overhead += 0.15
        if use_content_encoder:
            overhead += 0.36
        if n_voices > 1:
            overhead += BASELINE_GB * (n_voices - 1)

    peak = BASELINE_GB + overhead

    if peak > 6.0:
        warning = (
            f"Estimated {peak:.1f} GB exceeds 6 GB — "
            f"recommend a GPU with at least {int(peak) + 1} GB VRAM."
        )

    return VRAMEstimate(peak_gb=round(peak, 2), warning=warning)
```

**VRAM constraint:** function is pure Python arithmetic — zero GPU usage.

---

### M14.1.2 — `server/db.py`: `model_tier` column migration

**File:** `server/db.py`

1. In `init_db()`, add `model_tier TEXT NOT NULL DEFAULT 'standard'` to both
   `CREATE TABLE IF NOT EXISTS presets` and `CREATE TABLE IF NOT EXISTS runs`.

2. Add a migration helper called from `init_db()` after the `CREATE TABLE`
   statements:

```python
def _migrate_add_model_tier(cur: sqlite3.Cursor) -> None:
    """Add model_tier column to presets and runs if not already present.

    Safe to call on existing databases: uses sqlite3 PRAGMA table_info
    to detect the column before attempting ALTER TABLE.
    """
    for table in ("presets", "runs"):
        cur.execute(f"PRAGMA table_info({table})")
        cols = {row[1] for row in cur.fetchall()}
        if "model_tier" not in cols:
            cur.execute(
                f"ALTER TABLE {table} "
                "ADD COLUMN model_tier TEXT NOT NULL DEFAULT 'standard'"
            )
```

Call `_migrate_add_model_tier(cur)` at the end of `init_db()` before
`conn.commit()`.

**No data loss:** `DEFAULT 'standard'` means all existing rows silently
inherit the standard tier.

---

### M14.1.3 — `server/presets.py`: tier-aware keys + seed

**File:** `server/presets.py`

Add after `PARAM_KEYS`:

```python
# Tier-specific param keys (not VRAM-bounded; validated, not clamped)
VARIANT_KEYS: tuple = (          # M8 DDSPVariant fields
    "waveform", "harmonic_ratios", "fm_depth", "fm_ratio",
    "pd_k", "use_lfo", "lfo_freq", "lfo_depth",
    "use_trainable_wavetable", "use_angular_cumsum",
    "band_mask_low_hz", "band_mask_high_hz",
)
ENGINE_KEYS: tuple = (           # M9/M10 engine fields
    "engine",            # "harmonic" | "sinusoidal" | "combsub" | "newt"
    "noise_color",       # "white" | "pink" | "brown"
    "noise_grain_jitter",
    "newt_hidden_size",
    "newt_n_layers",
)
ADVANCED_KEYS: tuple = (         # M11–M13 advanced fields
    "use_latent",
    "latent_dim",
    "kl_beta",
    "n_voices",
    "use_content_encoder",
    "content_encoder_name",
)
```

Change `build_builtin_presets()` signature:

```python
def build_builtin_presets(bounds: ParameterBounds, tier: str = "standard") -> list[dict]:
```

Add `"model_tier": tier` to each preset dict.

Change `seed_builtin_presets()`:

```python
def seed_builtin_presets(conn, bounds: ParameterBounds, tier: str = "standard") -> int:
    inserted = 0
    for preset in build_builtin_presets(bounds, tier=tier):
        # Composite lookup: (name, model_tier) pair must be unique
        existing = preset_by_name_and_tier(conn, preset["name"], tier)
        if existing is None:
            preset_create(conn, ..., model_tier=tier)
            inserted += 1
    conn.commit()
    return inserted
```

Add `preset_by_name_and_tier(conn, name, tier)` query to `server/db.py` and
update `preset_create()` to accept `model_tier` parameter.

**Existing callers** pass no `tier` → default `'standard'` → identical
behaviour.

---

### M14.1.4 — `server/routes/training.py`: tier fields + validate + resume guard

**File:** `server/routes/training.py`

```python
class RunCreateRequest(BaseModel):
    name: str
    dataset_id: str | None = None
    preset_id: str | None = None
    params: dict | None = None
    model_tier: str = "standard"     # NEW — default preserves all existing callers

class ValidateRequest(BaseModel):
    preset_id: str | None = None
    params: dict | None = None
    model_tier: str = "standard"     # NEW
```

In `validate()` response, add:

```python
preset_tier = preset.get("model_tier", "standard") if preset else "standard"
model_tier_mismatch = preset_tier != req.model_tier
return {
    "params": clamped,
    "clamped_fields": clamped_fields,
    "bounds": bounds_to_dict(bounds),
    "model_tier_mismatch": model_tier_mismatch,   # NEW
}
```

In `create_run()`, store `model_tier` in the run record:

```python
run_create(conn, run_id, req.name, config, req.dataset_id,
           created_from_preset=req.preset_id,
           model_tier=req.model_tier)   # NEW
```

Update `run_create()` in `server/db.py` to accept and persist `model_tier`.

In `resume_run()`, add checkpoint-tier guard:

```python
run = run_get(conn, run_id)
stored_tier = run.get("model_tier", "standard")
latest = latest_checkpoint(run_id)
if latest is not None:
    ckpt = torch.load(latest, map_location="cpu", weights_only=True)
    ckpt_tier = ckpt.get("variant_flags", {}).get("model_tier", "standard")
    if ckpt_tier != stored_tier:
        raise HTTPException(
            status_code=409,
            detail=f"checkpoint_tier_mismatch: run={stored_tier}, checkpoint={ckpt_tier}",
        )
```

---

### M14.1.5 — `server/tasks.py`: tier-aware `build_training()`

**File:** `server/tasks.py`

In `build_training(model_config, checkpoint_dir)`:

```python
model_tier = model_config.get("model_tier", "standard")

# --- Tier: hacks / engine / advanced → DDSPVariant (M8) ---
if model_tier in ("hacks", "engine", "advanced"):
    from model.ddsp.variant import DDSPVariant
    variant = DDSPVariant.from_dict(model_config.get("variant", {}))
else:
    from model.ddsp.variant import DDSPVariant
    variant = DDSPVariant()   # all-default no-op

# --- Tier: engine / advanced → engine field (M9/M10) ---
engine = model_config.get("engine", "harmonic")

# --- Tier: advanced → latent / poly / VC (M11–M13) ---
use_latent           = bool(model_config.get("use_latent", False))
latent_dim           = int(model_config.get("latent_dim", 32))
kl_beta              = float(model_config.get("kl_beta", 1.0))
n_voices             = int(model_config.get("n_voices", 1))
use_content_encoder  = bool(model_config.get("use_content_encoder", False))
content_encoder_name = model_config.get("content_encoder_name", "hubert-soft")
```

Pass `variant`, `engine`, and advanced fields into `DDSPConfig` only when the
corresponding milestone's model classes exist (guard with `hasattr(DDSPConfig,
'variant')` until M8 is implemented). Until then they are parsed but silently
ignored — this way M14.1.5 can land before M8–M13 code is written.

---

### M14.1.6 — `server/routes/host.py`: `GET /api/gpu/feasibility`

**File:** `server/routes/host.py`

```python
@router.get("/feasibility")
def gpu_feasibility(
    model_tier: str = "standard",
    n_voices: int = 1,
    use_latent: bool = False,
    use_content_encoder: bool = False,
) -> dict[str, Any]:
    """Return VRAM feasibility for the requested config + all five tiers."""
    from train.gpu import estimate_model_vram, detect_gpus

    gpus = detect_gpus()
    available_gb = max((g["available_vram_gb"] or g["total_vram_gb"]
                        for g in gpus), default=6.0)

    # Current config estimate
    est = estimate_model_vram(model_tier, n_voices, use_latent, use_content_encoder)

    # All-tier summary (default params: n_voices=1, no latent, no CE)
    ALL_TIERS = ("standard", "component", "hacks", "engine", "advanced")
    tier_feasibility = {}
    for t in ALL_TIERS:
        e = estimate_model_vram(t)
        tier_feasibility[t] = {
            "fits": e.peak_gb <= available_gb,
            "estimated_gb": e.peak_gb,
            "warning": e.warning,
        }
    # For 'advanced' also compute worst-case (N=3)
    e_adv = estimate_model_vram("advanced", n_voices=3)
    tier_feasibility["advanced"]["worst_case_gb"] = e_adv.peak_gb
    tier_feasibility["advanced"]["worst_case_warning"] = e_adv.warning

    return {
        "fits": est.peak_gb <= available_gb,
        "estimated_gb": est.peak_gb,
        "available_gb": round(available_gb, 2),
        "warning": est.warning,
        "tier_feasibility": tier_feasibility,
    }
```

Register route prefix: the existing `router = APIRouter(prefix="/host")` in
`host.py` means the endpoint is reachable at `GET /api/host/feasibility`.
Alternatively, a new `APIRouter(prefix="/gpu")` in a new `server/routes/gpu.py`
gives the cleaner path `GET /api/gpu/feasibility`. **Decision: new file
`server/routes/gpu.py`** — keeps `host.py` focused on host-info.

Mount in `server/main.py`:

```python
from server.routes import gpu as gpu_routes
app.include_router(gpu_routes.router, prefix="/api")
```

---

### M14.1.7 — `tests/test_gpu_feasibility.py`

**File:** `tests/test_gpu_feasibility.py` (new)

Test cases:
- `estimate_model_vram("standard")` → `VRAMEstimate(peak_gb=2.2, warning=None)`
- `estimate_model_vram("advanced", n_voices=1)` → `VRAMEstimate(2.2, None)`
- `estimate_model_vram("advanced", use_latent=True)` → `VRAMEstimate(2.35, None)`
- `estimate_model_vram("advanced", use_content_encoder=True)` → `VRAMEstimate(2.56, None)`
- `estimate_model_vram("advanced", n_voices=3)` → `peak_gb=6.6`, warning set
- `estimate_model_vram("advanced", n_voices=3, use_latent=True, use_content_encoder=True)` → peak > 7.0, warning set
- `GET /api/gpu/feasibility` (no GPU mock) → response has `tier_feasibility` with all 5 tiers
- `GET /api/gpu/feasibility?model_tier=advanced&n_voices=3` → `fits=False` on 6 GB mock

---

### M14.1.8 — `tests/test_presets_tier.py`

**File:** `tests/test_presets_tier.py` (new)

Test cases:
- `build_builtin_presets(bounds, tier="standard")` → 3 presets with `model_tier="standard"`
- `build_builtin_presets(bounds, tier="engine")` → 3 presets with `model_tier="engine"`
- `seed_builtin_presets()` twice: second call inserts 0 (idempotent)
- `seed_builtin_presets()` for `"standard"` then `"engine"`: total 6 rows, no collision
- `clamp_params()` with `VARIANT_KEYS`/`ENGINE_KEYS`/`ADVANCED_KEYS` mixed in → only `PARAM_KEYS` are clamped

---

### M14.1.9 — `tests/test_training_tier.py`

**File:** `tests/test_training_tier.py` (new)

Test cases:
- `build_training({...standard params...}, ckpt_dir)` → `DDSPConfig` has default variant
- `build_training({...hacks params, model_tier="hacks"...}, ckpt_dir)` → variant parsed
- `build_training({...advanced params, model_tier="advanced", n_voices=2...}, ckpt_dir)` → `n_voices=2` extracted
- `build_training({model_tier="standard"}, ckpt_dir)` with missing new fields → no KeyError
- `POST /api/runs/{id}/resume` with mismatched checkpoint tier → HTTP 409

---

## Phase 2 — Frontend

### M14.2.1 — `webui/src/stores/modelConfig.js`

**File:** `webui/src/stores/modelConfig.js` (new)

```js
import { defineStore } from 'pinia'

export const useModelConfigStore = defineStore('modelConfig', {
  state: () => ({
    activeTier: null,           // null = wizard not yet completed
    wizardCompleted: false,
    gpuFeasibility: null,       // response from GET /api/gpu/feasibility
    selectedPreset: null,
    targetMode: 'offline',
    coreParams: {
      learning_rate: 0.001,
      batch_size: 1,
      epochs: 100,
      decoder_type: 'gru',
      use_reverb: true,
    },
    componentParams: { n_harmonics: 60, n_filter_banks: 32 },
    hacksVariant: {},           // DDSPVariant fields (M8)
    engineParams: { engine: 'harmonic', noise_color: 'white',
                    newt_hidden_size: 64, newt_n_layers: 4 },
    advancedParams: {
      use_latent: false, latent_dim: 32, kl_beta: 1.0,
      n_voices: 1,
      use_content_encoder: false, content_encoder_name: 'hubert-soft',
    },
  }),
  getters: {
    isFeasible: (state) => state.gpuFeasibility?.fits ?? true,
    currentTierFeasibility: (state) =>
      state.gpuFeasibility?.tier_feasibility ?? {},
  },
  actions: {
    setTierFromWizard(tier, preset, targetMode) {
      this.activeTier = tier
      this.wizardCompleted = true
      this.selectedPreset = preset
      this.targetMode = targetMode
    },
    async checkFeasibility(apiClient) {
      const p = this.advancedParams
      this.gpuFeasibility = await apiClient.getGpuFeasibility({
        model_tier: this.activeTier ?? 'standard',
        n_voices: p.n_voices,
        use_latent: p.use_latent,
        use_content_encoder: p.use_content_encoder,
      })
    },
    resetToWizard() {
      this.activeTier = null
      this.wizardCompleted = false
    },
  },
})
```

---

### M14.2.2 — Mock fixtures + `mockApiClient.js`

**File:** `webui/src/mocks/fixtures.js`

Add `tierFeasibilityFixture`:

```js
export const tierFeasibilityFixture = {
  fits: true,
  estimated_gb: 2.2,
  available_gb: 4.1,
  warning: null,
  tier_feasibility: {
    standard:  { fits: true,  estimated_gb: 2.2, warning: null },
    component: { fits: true,  estimated_gb: 2.4, warning: null },
    hacks:     { fits: true,  estimated_gb: 2.4, warning: null },
    engine:    { fits: true,  estimated_gb: 2.2, warning: null },
    advanced:  { fits: false, estimated_gb: 6.6,
                 warning: 'PolyDDSP N=3 requires ~6.6 GB (8 GB GPU recommended)',
                 worst_case_gb: 7.1, worst_case_warning: '...' },
  },
}
```

Add `model_tier: 'standard'` to all existing preset fixtures.

**File:** `webui/src/mocks/mockApiClient.js`

Add method:

```js
async getGpuFeasibility(_params) {
  return tierFeasibilityFixture
}
```

---

### M14.2.3 — `ModelTierCard.vue`

**Props:** `tier` (string), `label` (string), `description` (string),
`icon` (string), `feasibility` (`{ fits, estimated_gb, warning }`),
`selected` (bool), `disabled` (bool).

**Emits:** `select` (tier string).

Renders: icon, label, short description, GPU badge (`✓ fits X.X GB` /
`⚠ needs Y GB`), selected state (border highlight), disabled state
(greyed, cursor-not-allowed, no emit).

---

### M14.2.4 — `GpuFeasibilityBanner.vue`

**Props:** none (reads from `useModelConfigStore` + injects `apiClient`).

**Three render states** (all must be covered by Vitest):
1. `no-gpu` — "No GPU detected — training will run on CPU (slow)."
2. `fits` — green: "GPU · X GB available · current config ~Y.Y GB ✓"
3. `warning` — amber: "GPU · X GB available · current config ~Y.Y GB ⚠ [message]"

Watches `activeTier`, `advancedParams.n_voices`, `advancedParams.use_latent`,
`advancedParams.use_content_encoder` → calls `checkFeasibility()` on change.

---

### M14.2.5 — `WizardModal.vue`

**Step 1 — Model Tier:**
Renders a 2×3 grid of `ModelTierCard` components. Data sourced from
`gpuFeasibility.tier_feasibility` (fetched on modal open via
`checkFeasibility()`). "Skip" link at bottom-left closes modal and sets
`activeTier = 'standard'`, `wizardCompleted = true`.

**Step 2 — Quality / Preset:**
Three quality cards (FAST / NORMAL / QUALITY) showing `estimated_gb` from
`tier_feasibility[activeTier]` scaled by preset factor (0.25 / 0.50 / 1.0).
Optional "Load custom preset" selector filtered to `model_tier = activeTier`.

**Step 3 — Target Mode:**
Two radio options: Offline / Studio, Realtime / Low-Latency. Short export
format note per option.

On "Start Training Setup ✓": calls `setTierFromWizard(tier, preset, targetMode)`,
emits `complete`, closes modal.

Reopenable: parent `TrainingConfigView` shows "⚙ Reconfigure Model" button
that calls `resetToWizard()`.

---

### M14.2.6 — Tab components (`TabCore`, `TabComponent`, `TabHacks`, `TabEngine`, `TabAdvanced`)

Each tab component:
- Reads/writes the relevant slice of `useModelConfigStore`.
- Is a pure render component (no direct API calls; all data via store + props).
- Has a `data-testid` on every interactive element for Vitest.

**`TabCore.vue`:** preset selector (filtered to `activeTier`), learning rate,
batch size, epochs, decoder type dropdown, reverb toggle, "Save as Preset"
button.

**`TabComponent.vue`:** n_harmonics slider (range from `bounds.n_harmonics_min`
to `bounds.n_harmonics_max`), n_filter_banks slider, link button to
`ComponentMixerView`.

**`TabHacks.vue`:** waveform dropdown (sin/square/saw), FM depth/ratio sliders,
phase distortion `pd_k`, LFO toggle + freq/depth, trainable wavetable toggle,
angular cumsum toggle, loss band-mask Hz range. Link button to SynthHacksView
for full controls.

**`TabEngine.vue`:** engine dropdown (harmonic / sinusoidal / combsub / newt),
conditional NEWT controls (hidden_size, n_layers) shown when `engine === 'newt'`,
noise color selector shown for combsub/sinusoidal.

**`TabAdvanced.vue`:** VAE section (`use_latent` toggle, `latent_dim`, `kl_beta`),
PolyDDSP section (`n_voices` number input with VRAM cost indicator), Voice
Conversion section (`use_content_encoder` toggle, `content_encoder_name`
dropdown). Each section's VRAM cost badge updates reactively via the store.

---

### M14.2.7 — `TrainingConfigView.vue` refactor

**Structural change:** the view becomes a thin wrapper:
1. Imports and renders `GpuFeasibilityBanner` at the top.
2. Shows `WizardModal` when `!wizardCompleted` (via `v-if`).
3. Renders tab bar with five tabs; tabs with tier > `activeTier` get
   `disabled` class + `aria-disabled="true"`.
4. Renders the active tab component in the content area via `<component :is>`.
5. "⚙ Reconfigure Model" button in the view header calls `resetToWizard()`.
6. "▶ Start Training" button at the bottom assembles the full config from all
   store slices and calls `apiClient.startRun(config)`.

All existing `data-testid` attributes on the form fields are migrated to the
respective Tab component so existing Vitest selectors continue to work.

---

### M14.2.8 — `PresetManagerView.vue`: `model_tier` filter

Add a `<select>` dropdown above the preset list:

```
All tiers | Standard | Component | Hacks | Engine | Advanced
```

On change, calls `apiClient.listPresets({ model_tier: selectedFilter })`.
`mockApiClient.listPresets` already supports the `model_tier` query param
after M14.2.2 (filter applied client-side on the fixture array).

---

### M14.2.9 — Vitest suite

**Tests to add / extend:**

- `WizardModal.spec.js` — step 1→2→3 complete flow; skip link; reopen after reset.
- `GpuFeasibilityBanner.spec.js` — 3 render states (no-gpu / fits / warning).
- `ModelTierCard.spec.js` — fits/warn/disabled/selected states; emit on click.
- `TabCore.spec.js`, `TabComponent.spec.js`, `TabHacks.spec.js`,
  `TabEngine.spec.js`, `TabAdvanced.spec.js` — each renders with mock store
  state; interactive controls update store.
- `TrainingConfigView.spec.js` (extend existing) — tab switching; disabled tab
  tooltip; wizard reopens on "Reconfigure"; "Start Training" assembles full
  config.
- `PresetManagerView.spec.js` (extend existing) — model_tier filter changes
  preset list.

All tests use `MockApiClient` + fixtures; no backend required.

---

## History

_Append-only. Add entries as steps are completed._

<!-- Steps will be logged here as work proceeds. -->

## BUGS

_Bug references only (full records in `doc/bugs.md`):_

<!-- Add BUG-<id> references here if issues are discovered during M14. -->
