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

- [ ] **M4.1.1** FastAPI app skeleton + dataset service endpoints
      (upload/list/status). Files: `server/main.py`, `server/routes/dataset.py`.
- [ ] **M4.1.2** Model service endpoints (list/select trained models).
      Files: `server/routes/model.py`.
- [ ] **M4.1.3** Training service endpoints (config + launch).
      Files: `server/routes/training.py`.
- [ ] **M4.1.4** Inference service endpoints (timbre transfer + synthesis).
      Files: `server/routes/inference.py`.

### M4.2 Celery + Redis run lifecycle

- [ ] **M4.2.1** Wire Celery + Redis (broker/backend).
      Files: `server/tasks.py`.
- [ ] **M4.2.2** Async training job (launch trainer in a worker).
      Files: `server/tasks.py`.
- [ ] **M4.2.3** Async synthesis job.
      Files: `server/tasks.py`.
- [ ] **M4.2.4** Run lifecycle REST (start/stop/resume/status) over Celery task
      state. Files: `server/routes/training.py`.

### M4.3 Backend tests

- [ ] **M4.3.1** Dataset service tests (FastAPI `TestClient`).
- [ ] **M4.3.2** Training service tests (mocked training backend + Celery
      runner).
- [ ] **M4.3.3** Run lifecycle tests (start/stop/resume/status).

### M4.4 TensorBoard provisioning

### M4.4 TensorBoard provisioning

- [ ] **M4.4.1** Launch/attach TensorBoard and expose its URL for the UI embed.
      Files: `server/tensorboard.py`.
      Verify: endpoint returns a reachable TensorBoard URL.

### M4.5 Preset management

- [ ] **M4.5.1** Extend SQLite schema: `presets` table (id, name UNIQUE,
      is_builtin BOOL, params JSON, created_from_run_id TEXT NULL). Params
      JSON schema matches the GPU parameter bounds object from `train/gpu.py`.
      Files: `server/db.py`.
      Verify: migration creates the table; test inserts + reads a preset row.
- [ ] **M4.5.2** Seed three built-in presets (FAST, NORMAL, QUALITY) on first
      app start. Each preset maps the GPU proposal tier to a specific parameter
      set. Files: `server/presets.py`, `server/db.py`.
      Verify: GET /presets returns all three after init.
- [ ] **M4.5.3** CRUD endpoints: GET /presets, POST /presets (create custom),
      PUT /presets/{id} (update custom), DELETE /presets/{id} (custom only).
      Each write validates all values are within the current GPU's allowed
      bounds. Files: `server/routes/presets.py`, `server/presets.py`.
      Verify: FastAPI TestClient tests for each operation.
- [ ] **M4.5.4** GPU-constraint validation & clamping: on create/update, clamp
      out-of-bounds values and return a `clamped_fields` warning. On hardware
      change (detected at app start), re-clamp all custom presets and flag
      them. Files: `server/presets.py`.
      Verify: submit out-of-bounds value, receive clamped response.
- [ ] **M4.5.5** "Save as Preset" endpoint:
      POST /presets/from-run/{run_id} reads the run's effective parameters
      and creates a custom preset. Files: `server/routes/presets.py`.
      Verify: test creates a preset from a mock run.

### M4.6 Backend tests (expanded)

- [ ] **M4.6.1** Dataset service tests (FastAPI `TestClient`).
- [ ] **M4.6.2** Training service tests (mocked training backend + Celery
      runner).
- [ ] **M4.6.3** Run lifecycle tests (start/stop/resume/status).
- [ ] **M4.6.4** Preset CRUD + constraint-validation tests.

## BUGS

_References only; full records in [`../bugs.md`](../bugs.md)._

- (none)

## History

_Append-only, newest first._

- (none yet)
