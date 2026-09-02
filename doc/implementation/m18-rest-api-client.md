---
type: implementation-plan
status: draft
milestone: M18 - Frontend-Backend Integration (RestApiClient)
generated:
  by: primary-agent
  at: 2026-09-02
stale_after: 2027-06-01
---

# Implementation Plan — M18 Frontend-Backend Integration

_Granular plan for milestone M18. Meta plan: [`../plan.md`](../plan.md);
status: [`../checklist.md`](../checklist.md).
Prerequisite: M4 (REST backend), M5 (Web UI), M15 (ParamManifest).
Closes the mock-data seam: the UI talks to the real backend instead of fixtures._

---

## Goal

The web UI currently uses `MockApiClient` which returns deterministic fixtures.
All backend endpoints exist (`server/routes/`) but no `RestApiClient` was ever
written. This milestone creates the HTTP client, adds missing backend routes,
and swaps the mock for the real implementation.

---

## Steps

### M18.1 — Add missing backend REST routes

**Files:** `server/routes/dataset.py`, `server/routes/model.py`

Two endpoints declared in the abstract `ApiClient` class have no backend route:

- `DELETE /api/datasets/{dataset_id}` — deletes a dataset directory
- `POST /api/models/{run_id}/{checkpoint}/export/neutone` — triggers Neutone export (function exists in `inference/export.py`)

Add these two routes. Both follow existing patterns (404 on missing resource, error handling).

### M18.2 — Add missing methods to abstract `ApiClient`

**File:** `webui/src/api/apiClient.js`

The abstract class is missing 6 methods that views and stores call:

- `getFirstAudioFile(datasetId) -> Promise<string>` — URL to first audio file for WaveSurfer
- `preprocessDataset(datasetId) -> Promise<object>` — trigger feature extraction
- `exportModel(params) -> Promise<{job_id}>` — start multi-format export
- `exportStatus(jobId) -> Promise<{state, error?, downloads?}>` — poll export job
- `synthesizeMidi(params) -> Promise<{job_id}>` — MIDI preview synthesis
- `getGpuFeasibility(params) -> Promise<object>` — VRAM feasibility check

Add all six with JSDoc return types and the standard `throw new Error(...)` pattern.

### M18.3 — Create `RestApiClient.js`

**File:** `webui/src/api/restApiClient.js` (NEW)

Full `fetch()`-based implementation of every method declared in `ApiClient`.
Maps each method to the correct REST endpoint:

```toon
method                        endpoint                          method  body
───────────────────────────────────────────────────────────────────────────────
health()                      /api/                             GET     —
uploadDataset(files)          /api/datasets                      POST    FormData
listDatasets()                /api/datasets                      GET     —
getDataset(id)                /api/datasets/{id}                 GET     —
deleteDataset(id)             /api/datasets/{id}                 DELETE  —
validateConfig(config)        /api/runs/validate                 POST    JSON
startRun(config)              /api/runs                          POST    JSON
listRuns()                    /api/runs                          GET     —
getRun(id)                    /api/runs/{id}                     GET     —
stopRun(id)                   /api/runs/{id}/stop                POST    —
resumeRun(id)                 /api/runs/{id}/resume              POST    —
deleteRun(id)                 /api/runs/{id}                     DELETE  —
listPresets()                 /api/presets                       GET     —
createPreset(preset)          /api/presets                       POST    JSON
updatePreset(id, preset)      /api/presets/{id}                  PUT     JSON
deletePreset(id)              /api/presets/{id}                  DELETE  —
createPresetFromRun(runId)    /api/presets/from-run/{runId}      POST    —
synthesize(params)            /api/inference/synthesize          POST    FormData
synthesizeMidi(params)        /api/inference/synthesize-midi     POST    FormData
getInferenceJob(id)           /api/inference/jobs/{id}           GET     —
getInferenceArtifacts(id)     /api/inference/artifacts/{id}      GET     —
listModels()                  /api/models                        GET     —
downloadModel(runId, ckpt)    /api/models/{runId}/{ckpt}        GET     —
getCheckpointParams(rid,ck)   /api/models/{rid}/{ck}/params     GET     —
updateCheckpointParams(...)   /api/models/{rid}/{ck}/params     PUT     JSON
exportNeutone(rid, ckpt)      /api/models/{rid}/{ck}/export/neutone POST  —
exportCustomVST(rid, ckpt)    /api/models/{rid}/{ck}/export/custom-vst POST —
getTensorboard()              /api/tensorboard                   GET     —
getSettings()                 /api/settings                      GET     —
updateSettings(dataDir)       /api/settings                      PUT     JSON
getHostInfo()                 /api/host/info                     GET     —
getGPUInfo()                  (same as getHostInfo)              —       —
validatePreset(params, speed) /api/host/validate-preset          POST    JSON
injectIr(runId, irFile)       /api/reverb/ir-inject              POST    FormData
extractIrUrl(runId)           /api/reverb/ir-extract/{runId}     GET     —
getFeatures(datasetId, file)  /api/datasets/{id}/features/{file} GET     —
morph(formData)               /api/inference/morph               POST    FormData
voiceConvert(formData)        /api/inference/voice-convert       POST    FormData
getGpuFeasibility(params)     /api/gpu/feasibility               GET     query
getFirstAudioFile(datasetId)  /api/datasets/{id}                 GET     (extract URL)
preprocessDataset(datasetId)  /api/datasets/{id}/extract-content POST    FormData
exportModel(params)           (composite: calls per-format)      —       —
exportStatus(jobId)           /api/inference/jobs/{jobId}        GET     —
```

Key design decisions:
- Base URL defaults to `""` (same-origin, works via Vite proxy or release mode)
- `constructor(baseUrl = '')` for configurable prefix
- All `fetch()` calls use `response.json()` on success; throw on non-2xx
- Blob-returning methods (downloadModel, exportNeutone, exportCustomVST) use `response.blob()`
- FormData methods build `FormData` from the params object

### M18.4 — Swap `MockApiClient` → `RestApiClient` in `main.js`

**File:** `webui/src/main.js`

Change the import and inject:

```js
// Before:
import { MockApiClient } from './mocks/mockApiClient.js'
app.provide('apiClient', new MockApiClient())

// After:
import { RestApiClient } from './api/restApiClient.js'
app.provide('apiClient', new RestApiClient())
```

### M18.5 — Add CORS middleware (optional, for dev-mode debugging)

**File:** `server/main.py`

Add `CORSMiddleware` allowing `http://127.0.0.1:5173` (Vite dev server) so the
frontend can make direct API calls when not using the Vite proxy. Gated behind
a `WOGD_DEV_CORS` env flag so release mode is unaffected.

### M18.6 — Full verification

- `vitest run` — all 77 tests green (MockApiClient still injected for tests; only production `main.js` changes)
- `pytest` — all backend tests green
- `ruff check` — no new issues
- Production build (`npm run build`) — success
- `index_project_code` — wiki updated

---

## History

- **2026-09-02 — M18.1–M18.6 all completed.** 
  - M18.1: Added `DELETE /api/datasets/{id}` + `POST …/export/neutone` routes.
  - M18.2: Added 6 missing methods to abstract `ApiClient.js`.
  - M18.3: Created `webui/src/api/restApiClient.js` (full `fetch()` implementation).
  - M18.4: Swapped `MockApiClient` → `RestApiClient` in `main.js`.
  - M18.5: Added CORS middleware behind `WOGD_DEV_CORS` env flag.
  - M18.6: Verification: vitest 77/77, pytest 362/1, ruff clean, build success.

---

## BUGS

_References to `doc/bugs.md` entries only. No full bug records here._

<!-- BUG-x refs added here if any arise during M18 -->