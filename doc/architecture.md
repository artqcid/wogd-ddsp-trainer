---
type: architecture
status: draft
generated:
  by: setup
  at: 2026-08-30
description: System architecture of the wogd-ddsp-trainer web UI DDSP training app
stale_after: 2026-12-31
---

# wogd-ddsp-trainer - Architecture

_Manually maintained architecture knowledge. Structural detail is auto-generated
in [`code_wiki.md`](./code_wiki.md) (MCP-only). See
[`index.md`](./index.md) for the knowledge catalog and
[`log.md`](./log.md) for the chronological changelog._

## Overview

`wogd-ddsp-trainer` is a **web UI training application for DDSP-based speech
synthesis models**. It exposes a browser UI to prepare datasets, configure and
run DDSP training, monitor progress, and synthesize/inference vocal output.

Building blocks (planned directory layout):

- `dataset/` - dataset prep: audio ingestion, level normalization, feature
  extraction (`f0_hz` + `f0_confidence`, `loudness_db`), train/validation split.
- `model/` - DDSP model definition: self-owned PyTorch core (harmonic
  oscillator + filtered-noise decoder, F0/loudness conditioning, encoder if
  any).
- `train/` - training loop: PyTorch training, checkpoints, logging/metrics
  (TensorBoard), early stopping, resume.
- `inference/` - synthesis: load a checkpoint, condition on target loudness/F0,
  render vocal audio (offline) or export a low-latency realtime model
  (Neutone/TorchScript, ONNX), save/stream result.
- `server/` - web backend (FastAPI) exposing the dataset/model/training/
  inference services over HTTP (REST); Celery + Redis workers for
  asynchronous jobs; TensorBoard URL/embed provisioning.
- `webui/` - browser front-end (Vue 3 + Vite + Pinia) for dataset management,
  training configuration, TensorBoard-based dashboard, and synthesis
  triggers.
- `tests/` - pytest for backend/training, Vitest for the web UI.

## Tech stack (proposed)

- Python 3 runtime; **PyTorch + torchaudio** for the DDSP model + training
  (self-owned DDSP core; `magenta/ddsp` is only a spec reference, not a
  dependency - see `related-work.md`).
- F0 extraction via a **strategy/factory** (`dataset/features.get_f0_extractor`):
  **CREPE-PyTorch (`torchcrepe`) = primary/ML** extractor for dataset prep +
  training (GPU), **parselmouth (Praat) = lightweight CPU fallback** for fast
  unit-tests / local CI / UI preview. `loudness_db` via librosa; `soundfile`
  + librosa for audio I/O. (`rmvpe` was the earlier plan primary but was
  dropped for py3.14/torch2.13 fragility — see `oss-dependencies.md`.)
- FastAPI + uvicorn for the web backend; **Celery + Redis** for asynchronous
  training/synthesis jobs; **TensorBoard** for training monitoring.
- Vue 3 + Vite (+ Pinia) for the web UI (control panel: REST + TensorBoard
  embed; no WebSocket monitoring streaming).
- SQLite / filesystem for dataset + run metadata.

## Training pipeline

1. **Dataset prep:** ingest source audio -> 16 kHz mono -> per-frame features
   (`f0_hz` + `f0_confidence` via the F0 factory — CREPE-PyTorch primary /
   parselmouth fallback, `loudness_db` via librosa). Harmonic amplitude and
   aperiodicity are decoder outputs, not precomputed features.
2. **Batching:** chunk into fixed-length frames + features; normalization.
3. **Model forward:** (optional encoder) -> oscillator + filtered-noise decoder
   -> reconstructed audio; loss = multi-scale spectral loss.
4. **Optimization:** Adam/AdamW, LR schedule, checkpointing each epoch, best
   checkpoint on validation loss; metrics/logs written to TensorBoard.
5. **Inference:** condition the decoder on target features (from reference
   audio or a UI sketch) -> render synthesis offline, or export a low-latency
   realtime model (Neutone/TorchScript, ONNX) -> play/download.

### DataLoader contract (M3.6.1, resolved)

The training loop uses a standard PyTorch `DataLoader` wrapping a `DDSPDataset`,
not a `FeatureCache` directly. Rationale:

- **Separation of concerns:** `Trainer` trains; it should not know about
  filesystem paths, cache keys, or chunking logic.
- **PyTorch standard:** `DataLoader` + `Dataset` is the canonical pattern for
  training loops — every tutorial and production system uses it, making the
  codebase easier to understand and maintain.
- **`build_tensors()` stays as the bridge:** `server/tasks.py::build_tensors()`
  creates the `DDSPDataset` from the `FeatureCache` on disk, wraps it in a
  `DataLoader`, and passes it to `Trainer.run()`. This preserves the current
  architecture where `tasks.py` prepares all training inputs.
- **Chunking in the Dataset:** `DDSPDataset.__getitem__` loads a single file's
  `.npy` features via `FeatureCache`, chunks them into fixed-length segments
  (≤4 s @ 16 kHz = 64000 audio samples = 400 frames at 10 ms hop), and yields
  `(f0, loudness, audio_chunk)` triples. Shuffle and seed-reproducibility are
  handled by `DataLoader`'s native `shuffle` + `generator` arguments.
- **Resume safety:** The `DDSPDataset` uses a deterministic, seed-based
  permutation so that resumed training sees the same shuffled order (as long as
  the dataset contents have not changed).

## Model Tier system & Dual-Mode UI (M14)

The training UI supports five **model tiers** that activate progressively more
complex backend features. The tier is stored per-run in the DB and carried
through the entire pipeline from preset → validation → `build_training` →
checkpoint. All tier extensions use safe defaults so existing runs
(`model_tier = 'standard'`) are fully backwards-compatible.

### Tier definitions

| Tier | Milestones | New backend params | VRAM overhead |
|---|---|---|---|
| `standard` | M1–M6 | — (baseline) | ~1.3–2.2 GB |
| `component` | M7.2 | `n_harmonics`, `n_filter_banks` (already in M7.2) | +~0 GB |
| `hacks` | M8 | `DDSPVariant` fields (waveform, FM, PD, LFO, wavetable, …) | +~0 GB |
| `engine` | M9/M10 | `engine` (sinusoidal/combsub/newt), engine-specific params | +~0 GB |
| `advanced` | M11–M13 | `use_latent`, `latent_dim`, `kl_beta`, `n_voices`, `use_content_encoder`, `content_encoder_name` | +0.15–0.36 GB per feature; PolyDDSP N×baseline |

### DB schema changes (M14)

Two `ALTER TABLE ADD COLUMN` migrations (safe: `NOT NULL DEFAULT` on both;
existing rows receive `'standard'` automatically):

```sql
ALTER TABLE presets ADD COLUMN model_tier TEXT NOT NULL DEFAULT 'standard';
ALTER TABLE runs    ADD COLUMN model_tier TEXT NOT NULL DEFAULT 'standard';
```

`init_db()` updated to include `model_tier` in `CREATE TABLE IF NOT EXISTS`
for fresh installs. Migration version tracked in the `meta` table
(`key = 'schema_version'`).

### `train/gpu.py` additions (M14)

New dataclass and function:

```python
@dataclass
class VRAMEstimate:
    peak_gb: float
    warning: str | None = None


def estimate_model_vram(
    model_tier: str,
    n_voices: int = 1,
    use_latent: bool = False,
    use_content_encoder: bool = False,
) -> VRAMEstimate:
    """Estimate peak VRAM in GB for a given model configuration.

    Base per-tier baselines from ``BASE_ESTIMATE_GB``:
      standard  = 2.2 GB
      component = 2.25 GB
      hacks     = 2.3 GB
      engine    = 2.35 GB
      advanced  = 2.35 GB (+ optional overheads below)
      use_latent (GRUEncoder + VAE)                          = +0.15 GB
      use_content_encoder (HuBERT-Soft frozen)               = +0.36 GB
      PolyDDSP N voices                                      = baseline × N
    """
```

Used by `server/routes/host.py` and the new `/api/gpu/feasibility` endpoint.

### `server/presets.py` changes (M14)

- `PARAM_KEYS` (VRAM-bounded params) remains unchanged.
- New constant tuples for per-tier validation (not VRAM-bounded):
  - `VARIANT_KEYS` — DDSPVariant fields (M8)
  - `ENGINE_KEYS` — engine + NEWT params (M9/M10)
  - `ADVANCED_KEYS` — latent, n_voices, content encoder (M11–M13)
- `clamp_params()` — unchanged; continues to clamp only `PARAM_KEYS`.
- `build_builtin_presets(bounds, tier='standard')` — tier parameter added;
  `'standard'` behaviour identical to current; other tiers extend the params
  dict with tier-specific default fields and set `model_tier`.
- `seed_builtin_presets()` — lookup changed to `(name, model_tier)` composite
  to avoid name collision between `FAST/standard` and `FAST/engine`.

### `server/routes/training.py` changes (M14)

`RunCreateRequest` and `ValidateRequest` get `model_tier: str = 'standard'`
(default `'standard'` → no breaking change). The `/validate` response gains:

```json
{
  "params": { ... },
  "clamped_fields": [ ... ],
  "bounds": { ... },
  "model_tier_mismatch": false   // true when preset.model_tier ≠ request.model_tier
}
```

`_clamp_params()` routes to tier-specific validation after the existing
VRAM-bounded clamping. Tier-specific fields use `model_config.get(key, default)`
and are never clamped — only validated (allowed-value checks).

**Checkpoint-compatibility guard on resume:** `POST /api/runs/{id}/resume`
compares the stored run's `model_tier` against the model_tier of the latest
checkpoint's `variant_flags`. If they differ the endpoint returns 409 with
`"checkpoint_tier_mismatch"` detail.

### `server/tasks.py` changes (M14)

`build_training(model_config, checkpoint_dir)` becomes tier-aware:

```python
model_tier = model_config.get("model_tier", "standard")

# Tier hacks (M8) — safe default: DDSPVariant() = no-op
if model_tier in ("hacks", "engine", "advanced"):
    variant = DDSPVariant.from_dict(model_config.get("variant", {}))
else:
    variant = DDSPVariant()

# Tier engine (M9/M10) — safe default: "harmonic"
engine = model_config.get("engine", "harmonic")

# Tier advanced (M11–M13) — all safe defaults
use_latent = model_config.get("use_latent", False)
latent_dim = model_config.get("latent_dim", 32)
kl_beta = model_config.get("kl_beta", 1.0)
n_voices = model_config.get("n_voices", 1)
use_content_encoder = model_config.get("use_content_encoder", False)
content_encoder_name = model_config.get("content_encoder_name", "hubert-soft")
```

All new fields default to the standard-tier behaviour → existing run records
and checkpoints are unaffected.

### New REST endpoint: `GET /api/gpu/feasibility` (M14)

Added to `server/routes/host.py` (or a dedicated `server/routes/gpu.py`):

```
GET /api/gpu/feasibility
    ?model_tier=standard
    &n_voices=1
    &use_latent=false
    &use_content_encoder=false
```

Response:

```json
{
  "fits": true,
  "estimated_gb": 2.2,
  "available_gb": 4.1,
  "warning": null,
  "tier_feasibility": {
    "standard":  { "fits": true,  "estimated_gb": 2.2, "warning": null },
    "component": { "fits": true,  "estimated_gb": 2.25, "warning": null },
    "hacks":     { "fits": true,  "estimated_gb": 2.3, "warning": null },
    "engine":    { "fits": true,  "estimated_gb": 2.35, "warning": null },
    "advanced":  { "fits": false, "estimated_gb": 6.6,
                   "warning": "PolyDDSP N=3 requires ~6.6 GB (8 GB GPU recommended)" }
  }
}
```

`tier_feasibility` is computed for the current GPU using fixed N-voice,
use_latent=false, use_content_encoder=false defaults. The Wizard Step 1
fetches this once to populate all tier-card badges. The `GpuFeasibilityBanner`
calls the endpoint with the live store values to show the current-config
estimate reactively.

### Updated REST endpoint map (M14 additions)

| Service | New / Changed Endpoints |
|---|---|
| GPU / Feasibility | **NEW** `GET /api/gpu/feasibility?model_tier=…&n_voices=…&use_latent=…&use_content_encoder=…` |
| Runs | `POST /api/runs/validate` — **extended**: `model_tier_mismatch` in response |
| Runs | `POST /api/runs/{id}/resume` — **extended**: 409 on checkpoint_tier_mismatch |
| Presets | `GET /api/presets?model_tier=standard` — **extended**: optional `model_tier` filter |
| Presets | `POST /api/presets` — **extended**: `model_tier` field in body |

All existing endpoints and their current response shapes remain unchanged.

## Preset management

The app manages training parameter presets — both built-in and user-defined.
Presets drive the training config form and are clamped to the current GPU's
allowed bounds.

### Data model (SQLite)

```sql
CREATE TABLE presets (
    id          TEXT PRIMARY KEY,          -- UUID
    name        TEXT NOT NULL UNIQUE,      -- user-visible name
    is_builtin  INTEGER NOT NULL DEFAULT 0,
    params      TEXT NOT NULL,             -- JSON object matching ParameterBounds schema
    created_from_run_id TEXT,              -- NULL for manually created presets
    created_at  TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at  TEXT NOT NULL DEFAULT (datetime('now'))
);
```

The `params` JSON schema mirrors the `ParameterBounds` output of
`train/gpu.py` — every parameter has min/max/default values + current selection.

### Built-in presets (seeded on first start)

Die drei Built-in-Presets sind **VRAM-relativ**: sie skalieren proportional
zur verfügbaren GPU. Jedes Preset drückt einen Ziel-Auslastungsgrad des
verfügbaren VRAMs aus — unabhängig davon, ob die GPU 4 GB, 6 GB oder 12 GB
hat.

Die absoluten Grenzen liefert die Parameter-Proposal-Tabelle (unten). Die
Presets legen fest, wie viel Prozent dieser Grenzen ausgeschöpft werden:

| Preset | VRAM-Auslastung | hidden_size | STFT scales | Mixed precision | Checkpointing |
|---|---|---|---|---|---|
| **FAST** | ~25 % | `floor(max_hidden × 0.25)` | min. mögliche Scales | Required | Enabled |
| **NORMAL** | ~50 % | `floor(max_hidden × 0.50)` | min. mögliche Scales | Required | Wie Tier-Vorgabe |
| **QUALITY** | ~90–100 % | `max_hidden` | max. mögliche Scales | Wie Tier-Vorgabe | Disabled |

**Beispiele:**

| GPU | 6 GB (Tier 4–8 GB) | 12 GB (Tier 8–12 GB) | 24 GB (Tier ≥ 12 GB) |
|---|---|---|---|
| max_hidden (aus Proposal-Table) | 512 | 512 | 1024 |
| **FAST** hidden | 128 | 128 | 256 |
| **NORMAL** hidden | 256 | 256 | 512 |
| **QUALITY** hidden | 512 | 512 | 1024 |
| **FAST** scales | 3 | 3 | 5 |
| **NORMAL** scales | 3 | 3 | 5 |
| **QUALITY** scales | 3 | 5 | 8 |

Wichtig: Die Skalierung erfolgt **ausschließlich über den Parameter, der am
stärksten VRAM-fressend ist** (hidden_size). Andere Parameter (scales,
checkpointing) folgen festen Regeln pro Preset – sie werden nicht linear
skaliert, sondern auf die nächstsinnvolle Stufe gesetzt.

### Constraint flow

1. App starts → GPU detection (`train/gpu.py`) computes `ParameterBounds` for
   the available VRAM (max hidden_size, min/max STFT scales, etc.).
2. Built-in presets are **computed** from the current bounds: each preset's
   scaling factors (FAST 25 %, NORMAL 50 %, QUALITY 100 %) werden auf die
   Maximalwerte angewendet. Es gibt kein „clamping" — die Presets entstehen
   direkt aus den GPU-Grenzen.
3. Custom presets werden aus SQLite geladen. Wenn sich die Hardware geändert
   hat (erkannt per VRAM-Fingerprint), werden überschüssige Werte auf die
   neuen Grenzen **geclamped** und mit Warnung markiert.
4. Frontend erhält die vollständige Preset-Liste + aktuelle GPU-Bounds.
   Der Preset-Editor stellt sicher, dass jeder Eingabewert innerhalb der
   Bounds bleibt. Beim Speichern validiert und clamed das Backend erneut.

### REST endpoints

- `GET  /api/presets` — list all presets (built-in + custom) with current clamp
  status.
- `POST /api/presets` — create custom preset (body: name + params). Values
  outside bounds are clamped; response includes `clamped_fields` warning.
- `PUT  /api/presets/{id}` — update custom preset name/params (same clamping).
- `DELETE /api/presets/{id}` — delete custom preset only (built-in → 403).
- `POST /api/presets/from-run/{run_id}` — snapshot a run's effective params as a
  custom preset.

## Web backend (M4, implemented)

The FastAPI app (`server/main.py`, `app = FastAPI(...)`) mounts all routers
under the `/api` prefix and runs an asyncio lifespan that: creates the SQLite
table schema (`server/db.py`), seeds the built-in presets from the current GPU
bounds, persists the hardware fingerprint and re-clamps custom presets on GPU
change. `GET /api/tensorboard` lazily launches TensorBoard (`server/tensorboard.py`)
and returns its reachable URL for the UI embed.

### REST endpoint map

| Service | Endpoints |
|---|---|
| Datasets | `POST /api/datasets` (multipart upload, uuid id), `GET /api/datasets`, `GET /api/datasets/{id}` |
| Models | `GET /api/models` (checkpoint scan newest-first), `GET /api/models/{run_id}/{checkpoint}` |
| Runs | `POST /api/runs/validate` (clamp + `clamped_fields` + bounds), `POST /api/runs` (create + submit), `GET /api/runs`, `GET /api/runs/{id}`, `POST /api/runs/{id}/stop`, `POST /api/runs/{id}/resume`, `DELETE /api/runs/{id}` |
| Inference | `POST /api/inference/synthesize` (202; multipart: run_id, pitch_shift, loudness_shift, audio), `GET /api/inference/jobs/{job_id}` (status + artifact_url when completed), `GET /api/inference/artifacts/{job_id}` (wav FileResponse; 409/404 guards) |
| Presets | see section above |
| Misc | `GET /` (service info), `GET /api/tensorboard` |

### Run lifecycle

Vocabulary: `pending → running → stopping/stopped → completed/failed`.
`server/tasks.py` define Celery tasks for training and synthesis; a
`TaskRunner` protocol (`submit_training`/`submit_synthesis`) + `get_task_runner`
inject the runner into routes (tests override the dependency). Stop is
cooperative: the worker polls the DB `stop_requested` flag and sets a
`threading.Event` passed into `Trainer.run(stop_event=...)`. Runs and
checkpoints live under `runs/<run_id>/checkpoints/step-*.pt` (env:
`WOGD_DATA_DIR` (default `%LOCALAPPDATA%\wogd-ddsp-trainer` on Windows; sets the
data root holding `datasets/`, `runs/` and the database), `WOGD_DB_PATH`,
`WOGD_REDIS_URL`, `WOGD_TB_PORT`, `WOGD_SERVER_PORT`; the old
`WOGD_RUNS_DIR`/`WOGD_DATASETS_DIR` vars are no longer used).

## Training monitoring (TensorBoard doctrine)

- The UI is a **control panel**: audio upload, hyperparameter config, job
  control (start/stop/resume) via REST.
- Training monitoring is **not** implemented with custom live charts or
  WebSocket/SSE streaming. The training loop logs losses, spectrograms and
  checkpoint audio natively to **TensorBoard**.
- The training dashboard embeds the server-side TensorBoard via `<iframe>`
  (fallback: prominent link/button opening TensorBoard in a new tab).

## GPU detection & VRAM budget

- The app runs **locally**: it detects and analyzes the available GPU and
  proposes optimal training parameters to the user before a run starts.
- **Minimum target hardware:** RTX 3060 Laptop (6 GB VRAM). All training and
  feature extraction MUST fit within this budget.
- **Design constraint:** DDSP is a lightweight architecture (small encoder +
  differentiable DSP, not a Transformer or diffusion model). Training on 6 GB
  is feasible with the techniques below.

### VRAM budget estimate (batch_size dynamic, seq_len=2s@16kHz, mixed precision)

| Component | VRAM |
|---|---|
| Model weights (fp32, ~1M params) | ~4 MB |
| Optimizer states (Adam, fp32) | ~8 MB |
| Input audio (fp16, 32000 samples) | ~0.06 MB |
| Features (f0+loudness, fp16) | ~0.01 MB |
| Forward activations | ~400–600 MB |
| Backward gradients | ~400–600 MB |
| Multi-scale STFT loss (3 scales) | ~200–400 MB |
| CUDA context + PyTorch overhead | ~300–500 MB |
| **Total** | **~1.3–2.2 GB** |

→ 3.8–4.7 GB headroom on 6 GB. Gradient checkpointing is optional.

### Required VRAM-saving techniques

| Technique | When | Effect |
|---|---|---|
| **Offline feature extraction** | Preprocessing phase | RMVPE/ContentVec run once before training, save `.npy`. Training loop loads pre-computed tensors — RMVPE GPU usage does not compete with training VRAM. |
| **Mixed precision (fp16)** | Every training step | `torch.cuda.amp.autocast` + `GradScaler` halves activation memory. |
| **Batch size = VRAM-dependent** | Always | `batch_size_max = min(128, max(2, int(vram_GB × 32/6)))`. Presets scale: FAST ×0.25, NORMAL ×0.50, QUALITY ×1.00. e.g. 6 GB → max=32, NORMAL=16. |
| **3-scale STFT loss** | Loss computation | FFT sizes `[512, 1024, 2048]` — 3 instead of the typical 8 scales saves ~300 MB. |
| **Sequence length ≤ 4 s** | Preprocessing | 64000 samples @ 16 kHz; longer audio is chunked. |
| **Hidden size 512 (or 256)** | Model config | 256 saves ~40 % activations with minimal quality loss; GPU auto-detection proposes this for < 8 GB. |
| **Gradient checkpointing** | Optional for safety | `torch.utils.checkpoint` on the encoder; trades ~20 % compute for ~3× less activation VRAM. |

### Parameter proposal logic

The GPU detection module (`train/gpu.py`) reads available VRAM and suggests:

| Available VRAM | Hidden size | STFT scales | Checkpointing | Mixed precision |
|---|---|---|---|---|
| < 4 GB | 128 or 256 | 3 | Enabled | Required |
| 4–8 GB | 256 or 512 | 3 | Optional | Required |
| 8–12 GB | 512 | 5 | Disabled | Recommended |
| ≥ 12 GB | 512–1024 | 5–8 | Disabled | Optional |

## Parameter Export Architecture

Two distinct export paths exist for inference parameters (see `parameter-handling.md`
for the full analysis):

### Dual-Export Targets

| Target | Format | Max params | SDK constraint |
|---|---|---|---|
| **Neutone FX** (realtime DAW plugin) | `.nm` (TorchScript) | **4** | `constants.MAX_N_PARAMS = 4` — SDK assert, hard limit |
| **Custom VST** (wogd realtime plugin) | `.pt` (TorchScript) | **16** | custom `param_manifest` embedded in checkpoint state |
| **API / Offline** | `.pt` | unlimited | params passed as JSON in POST body |

### Parameter Manifest (Custom VST + API)

A `param_manifest` dict is stored under `state["param_manifest"]` in every checkpoint.
It is written by the trainer with tier-specific defaults and can be updated via the
export UI without touching model weights. Schema: `InferenceParam` dataclass (slot,
name, description, type, min/max/default, mapping, unit_hint, group, neutone_slot)
+ `ParamManifest` container with `to_dict()`/`from_dict()`, tier-default builders,
checkpoint embedding, and a `context` field (`"audio_fx"` or `"midi_synth"`).

#### MIDI Synth Export Path (M17)

A separate **MIDI Synth VST export** path (`MidiSynthWrapper`) replaces the
realtime F0/loudness extractor with a MIDI-note-to-frame generator. Training
is unchanged — the same checkpoint works for both Audio FX and MIDI Synth
modes. The MIDI synth manifest prepends 5 universal MIDI parameters (Pitch
Shift, Velocity Sensitivity, Attack, Release, Pitch Bend Range) to the
tier-specific params. UI: Usage Mode selector in the Wizard (Step 3) and
a MIDI Preview virtual keyboard in the Playground.


```python
# server/routes/models.py — future endpoint
GET /api/models/{run_id}/{checkpoint}/params
→ { "n_params": 8, "neutone_slots": [1,2,3,4], "params": [...] }
```

### Tier-Default Parameter Counts

| Tier | Neutone FX | Custom VST (recommended) | Custom VST (max) |
|---|---|---|---|
| `standard` | 4 | 4 | 4 |
| `component` | 4 | 4–6 | 8 |
| `hacks` | 4 | 4–8 | 12 |
| `engine` | 4 | 4–6 | 8 |
| `advanced/VAE` | 4 | 6–10 | 16 |
| `advanced/Poly` | 4 | 4–8 | 12 |
| `advanced/VC` | 4 | 4–6 | 8 |

The `ModelParameterBuilder.vue` component in `ModelExportView` is the single place
where users configure inference parameters, assign Neutone slots (drag & drop), and
customise names/defaults before export.

## Conventions

- English for all agent-facing docs and code identifiers.
- Match existing style; `ruff` for lint/format, `pytest` for tests.
- No comments unless they clarify non-obvious logic.

## Status

M1 (scaffold), M2 (dataset prep), M3 (model + training), M4 (web backend),
M5 (web UI) and M6 (polish) are implemented and tested. Final check suite:
ruff/format 0, pytest 49+ passed / 1 GPU-skip (GPU-dependent tests), vitest 7+ passed, build clean.
M7 (experimental sound design) and M8 (experimental synthesis hacks) are open.
M14 (Dual-Mode UI + backend tier system) is designed; implementation pending.

### Known open items (identified in M1–M6 review 2026-08-31)

- **Preset-schema drift (BUG-5):** frontend fixtures use AutoVC/DSP-autoencoder
  field names (`hidden_dim`, `type: 'autovc'`) instead of DDSP backend fields
  (`hidden_size`, `is_builtin`). Fix tracked in `implementation/m5-webui.md`
  M5.8.1–M5.8.3.
- **Training Speed labels (BUG-6):** UI radio buttons show incorrect VRAM
  percentages. Fix tracked in `implementation/m5-webui.md` M5.8.4.
- **Real DataLoader missing (M3.6):** `Trainer.run()` and `build_tensors()`
  train on a single dummy batch, not real multi-file datasets. Tracked in
  `implementation/m3-model-training.md` M3.6.
- **`n_noise_bins` not in DDSPConfig (M3.1.4):** checkpoint resume may fail if
  `n_noise_bins` differs. Tracked in `implementation/m3-model-training.md`
  M3.1.4.
- **Missing DDSP UI controls:** decoder-type selector and reverb enable/disable
  required by `ui-requirements.md` but not yet in `TrainingConfigView.vue`.
  Tracked in `implementation/m5-webui.md` M5.8.5.
- **Loudness A-weighting (M2):** `features.py` uses RMS-dB rather than
  A-weighted loudness as documented. Decision pending (see
  `implementation/m2-dataset-prep.md`).
- **Output Enhancer (NSF-HiFiGAN):** deferred from M6.5 to M7; tracked in
  `implementation/m7-experimental.md` M7.0.
