---
type: implementation-plan
status: draft
milestone: M4 - Web backend
generated:
  by: primary-agent
  at: 2026-08-31
stale_after: 2026-12-31
---

# Implementation Plan - M4 Web backend

_Granular plan for milestone M4. Meta plan: [`../plan.md`](../plan.md); status:
[`../checklist.md`](../checklist.md); architecture:
[`../architecture.md`](../architecture.md)._

## How to use

- Each step below is one small, self-contained task (approx. one subagent task).
- Work in order; mark `[x]` and record every step in `## History`.
- Bugs: full record only in [`../bugs.md`](../bugs.md); reference by `BUG-<id>`.
- The UI consumes REST only (no WebSocket/SSE); see `ui-requirements.md`.

## Steps

### M4.1 FastAPI services

- [x] **M4.1.1** FastAPI app skeleton + dataset service endpoints
      (upload/list/status). Files: `server/main.py`, `server/routes/dataset.py`.
- [x] **M4.1.2** Model service endpoints (list/select trained models).
      Files: `server/routes/model.py`.
- [x] **M4.1.3** Training service endpoints (config + launch).
      Files: `server/routes/training.py`.
- [x] **M4.1.4** Inference service endpoints (timbre transfer + synthesis).
      Files: `server/routes/inference.py`.

### M4.2 Celery + Redis run lifecycle

- [x] **M4.2.1** Wire Celery + Redis (broker/backend).
      Files: `server/tasks.py`.
- [x] **M4.2.2** Async training job (launch trainer in a worker).
      Files: `server/tasks.py`.
- [x] **M4.2.3** Async synthesis job.
      Files: `server/tasks.py`.
- [x] **M4.2.4** Run lifecycle REST (start/stop/resume/status) over Celery task
      state. Files: `server/routes/training.py`.

### M4.3 Backend tests

- [x] **M4.3.1** Dataset service tests (FastAPI `TestClient`).
- [x] **M4.3.2** Training service tests (mocked training backend + Celery
      runner).
- [x] **M4.3.3** Run lifecycle tests (start/stop/resume/status).

### M4.4 TensorBoard provisioning

- [x] **M4.4.1** Launch/attach TensorBoard and expose its URL for the UI embed.
      Files: `server/tensorboard.py`.
      Verify: endpoint returns a reachable TensorBoard URL.

### M4.5 Preset management

- [x] **M4.5.1** Extend SQLite schema: `presets` table (id, name UNIQUE,
      is_builtin BOOL, params JSON, created_from_run_id TEXT NULL). Params
      JSON schema matches the GPU parameter bounds object from `train/gpu.py`.
      Files: `server/db.py`.
      Verify: migration creates the table; test inserts + reads a preset row.
- [x] **M4.5.2** Seed three built-in presets (FAST, NORMAL, QUALITY) on first
      app start. Each preset maps the GPU proposal tier to a specific parameter
      set. Files: `server/presets.py`, `server/db.py`.
      Verify: GET /presets returns all three after init.
- [x] **M4.5.3** CRUD endpoints: GET /presets, POST /presets (create custom),
      PUT /presets/{id} (update custom), DELETE /presets/{id} (custom only).
      Each write validates all values are within the current GPU's allowed
      bounds. Files: `server/routes/presets.py`, `server/presets.py`.
      Verify: FastAPI TestClient tests for each operation.
- [x] **M4.5.4** GPU-constraint validation & clamping: on create/update, clamp
      out-of-bounds values and return a `clamped_fields` warning. On hardware
      change (detected at app start), re-clamp all custom presets and flag
      them. Files: `server/presets.py`.
      Verify: submit out-of-bounds value, receive clamped response.
- [x] **M4.5.5** "Save as Preset" endpoint:
      POST /presets/from-run/{run_id} reads the run's effective parameters
      and creates a custom preset. Files: `server/routes/presets.py`.
      Verify: test creates a preset from a mock run.

### M4.6 Backend tests (expanded)

- [x] **M4.6.1** Dataset service tests (FastAPI `TestClient`).
- [x] **M4.6.2** Training service tests (mocked training backend + Celery
      runner).
- [x] **M4.6.3** Run lifecycle tests (start/stop/resume/status).
- [x] **M4.6.4** Preset CRUD + constraint-validation tests.

## BUGS

_References only; full records in [`../bugs.md`](../bugs.md)._

- `BUG-2` — datasets_dir() ignores existing-but-empty WOGD_DATASETS_DIR (fixed, M4.3)

## History

_Append-only, newest first._

- **2026-08-31 — M4.3.1-3 + M4.6.1-4 Backend-Tests umgesetzt (subagent
  task_ids: `ses_fa9a349bbffeRqPI7h1aLybglF` test_server_db.py,
  `ses_fa9a5d047ffe2NHOk47CJJ2gmZ`+`ses_fa9a333a8ffeR1U0S6pAU1qzz9`
  test_server_presets.py, `ses_fa9a05055ffeQh5INi8fUi0613`
  test_api_datasets.py, `ses_fa9a021d2ffejyfdrfJ5Wovs8G` test_api_training.py,
  `ses_fa9a00306ffelWkrxhuE6BHszM` test_api_inference.py,
  `ses_fa99f5900ffeZPTaB4CRuH0Ts8` test_api_presets.py).** Primary-Fixes
  (Nicht-Subagent, Test-Korruptions-Roundtrips + ein Produktions-Bug):
  - `tests/conftest.py`: E402-`noqa` für die bewusst verzögerten Server-Imports.
  - `tests/test_api_training.py`: URL-Präfix `"/runs"`→`"/api/runs"`; Modul-
    Konstante `RUNS_DIR` entfernt → `server.tasks.runs_dir()` zur Laufzeit
    (Import-Cache-Falle: Test schrieb in Default-Ordner statt tmp).
  - `tests/test_api_inference.py`: `_wav_bytes()`-BytesIO aus Tupel→Bytes;
    `_run_id` fehlende Klammern bei Pfad-Konkatenation; job_id ist
    `str(uuid4())` (kein `"job-"`-Präfix) + optionales audio → 202 statt 422.
  - `tests/test_api_datasets.py`: Multipart als Liste von Tripeln (mehrere
    Dateien unter einem `files`-Feld); fehlende `files` → 422 (Route `File(...)`).
  - `tests/test_api_presets.py`: `_run_payload` braucht `name`; Run gibt
    `run_id` (nicht `id`); `hidden_size_max+100` für Clamp-Nachweis; kein
    GET-Einzel-Preset → Nachweis über DB + Liste; SIM300-Yoda-Fix.
  - **Produktions-Bug BUG-2** (vollständiger Record in [`../bugs.md`](../bugs.md)):
    `server/routes/dataset.py::datasets_dir()` prüfte `Path(env).is_dir()` — ein
    gesetztes `WOGD_DATASETS_DIR`, das noch nicht existiert, fiel still auf
    `Path.cwd()/datasets` zurück (Repo-Verschmutzung). Fix: gesetzten env-Pfad
    immer respektieren.
  - Verifikation: ruff check + format clean (83 Dateien), pytest 132 passed/
    1 GPU-skip, vitest 2 passed (webui). Alle M4-Steps `[x]`.

- **2026-08-31 — M4.1-M4.5 Backend-Code umgesetzt (subagent task_ids:
  `ses_fa9b94638ffeoSpUoZhthGqM0b` dataset.py-SIM-Fixes,
  `ses_fa9b934b6ffeCPJuzkU4AbazvI` training.py-Bugs (run["id"]/run_id,
  checkpoint-subdir, bounds_to_dict-Import, uuid-Placeholder, B008),
  `ses_fa9b9271cffeVA0UXUC9dK1oFR` inference.py-Imports (UploadFile,
  FileResponse aus fastapi.responses, Annotated),
  `ses_fa9b6323affet2zU8gx40jXSMD` training.py-Call-Site,
  `ses_fa9b62622ffeHItHmY0u5qhtVh` inference.py-Importblock,
  `ses_fa9b4bb23ffeXptSkhluSmdWTB` server/main.py,
  `ses_fa9b38990ffexLQuwUaznlQmeD` dataset.py-datasets_dir-Bug).** 
  Alle Schritte M4.1.1-M4.5.5 `[x]`; offen: M4.3.1-3 + M4.6.1-4 (Backend-Tests).
  - `server/`: `main.py` (App-Assembly + Lifespan: init_db, Built-ins-Seed,
    Hardware-Fingerprint-Check + Reclamp, TensorBoard-Manager), `db.py`
    (SQLite: presets/runs/synthesis_jobs/meta), `tasks.py` (Celery-App + 
    Job-Helpers + CeleryTasks + TaskRunner-Protocol + get_task_runner),
    `presets.py` (Bounds/Clamp/Fingerprint/Seed/Reclamp),
    `tensorboard.py` (TB-Subprozess-Lifecycle).
  - `server/routes/`: `dataset.py` (Upload/List/Detail),
    `model.py` (Checkpoint-Registry), `training.py` (Validate/Run-CRUD/
    Stop/Resume/Delete), `inference.py` (Synthesize-Jobs/Artifacts),
    `presets.py` (Preset-CRUD + from-run).
  - `train/trainer.py`: `stop_event`-Parameter für kooperativen Stop.
  - `pyproject.toml`: `server.routes` in packages.
  - Verifikation: ruff clean, pytest 77 passed/1 skip, vitest 2 passed,
    TestClient-Smoke aller `/api`-Endpoints (Temp-DB, FakeTaskRunner).
  - Gefundene & behobene Bugs: `run["id"]` → `run["run_id"]`;
    Checkpoint-Ordner `runs/<id>/checkpoints` via `run_checkpoint_dir`;
    `bound_to_dict` → `bounds_to_dict`; `run_id = str()`-Dead-Code; 
    `FileResponse` fälschlich aus `fastapi` Top-Level importiert;
    fehlendes `UploadFile`/`Annotated`; `datasets_dir()` → `Path("")` 
    (== `Path('.')`) als RD-Bug; B008/F821/SIM108/SIM105-Cleanup.
