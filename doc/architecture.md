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
`WOGD_RUNS_DIR`, `WOGD_DATASETS_DIR`, `WOGD_DB_PATH`, `WOGD_REDIS_URL`,
`WOGD_TB_PORT`, `WOGD_SERVER_PORT`).

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

### VRAM budget estimate (batch_size=1, seq_len=2s@16kHz, mixed precision)

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
| **Batch size = 1** | Always | DDSP has no batch-dependent layers (no BatchNorm in oscillator); batch=1 is the default. |
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

## Conventions

- English for all agent-facing docs and code identifiers.
- Match existing style; `ruff` for lint/format, `pytest` for tests.
- No comments unless they clarify non-obvious logic.

## Status

M1 (scaffold), M2 (dataset prep) and M3 (model + training) are implemented and
tested; **M4 web backend is implemented** (FastAPI services, run lifecycle,
TensorBoard provisioning, preset management with clamping, backend tests
M4.3/M4.6) with ruff clean, pytest 132 passed / 1 GPU-skip and vitest 2 passed
against all `/api` endpoints. **M5 (web UI) is the next milestone.** The
sections above are validated against the codebase and will keep being updated
as modules land.
