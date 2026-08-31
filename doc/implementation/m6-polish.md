---
type: implementation-plan
status: draft
milestone: M6 - Polish
generated:
  by: primary-agent
  at: 2026-08-31
stale_after: 2026-12-31
---

# Implementation Plan - M6 Polish

_Granular plan for milestone M6. Meta plan: [`../plan.md`](../plan.md); status:
[`../checklist.md`](../checklist.md); workflow:
[`../workspace-workflow.md`](../workspace-workflow.md)._

## How to use

- Each step below is one small, self-contained task (approx. one subagent task).
- Work in order; mark `[x]` and record every step in `## History`.
- Bugs: full record only in [`../bugs.md`](../bugs.md); reference by `BUG-<id>`.

## Steps

### M6.1 Packaging (non-Docker)

- [x] **M6.1.1** Build a wheel / local distribution for the backend
      (`pyproject.toml` packaging). *(relevant backend packaging constraints
      documented; full wheel build verified alongside release packaging.)*
- [x] **M6.1.2** Build the frontend production bundle (`vite build`). *(fixes
      BUG-3: `App.vue` named `RouterView` import; dist emits cleanly.)*
- [x] **M6.1.3** Document the local install/run path (no Docker).
- [x] **M6.1.4** `start-application-debug` starts backend + frontend together:
      `scripts/start-app.ps1 -Mode Debug` checks the frontend build (rebuilds
      only if `webui/dist` missing/stale, dev mode), then runs the backend via
      debugpy (`--listen 5678 --wait-for-client`) on `:8000` plus the Vite dev
      server on `:5173`. VSCode attaches via the `Debug Backend (attach)`
      launch config. (BUG-3 fixed; verified -> M6.6.4.)
- [x] **M6.1.5** `start-application-release` starts backend + frontend together:
      `scripts/start-app.ps1 -Mode Release` rebuilds the frontend only if stale,
      then runs uvicorn with `WOGD_SERVE_STATIC=1` on `:8000`, serving both the
      API and the built frontend from `webui/dist` (SPA fallback). Added
      `server.main.mount_frontend` (gated on `WOGD_SERVE_STATIC=1`) + `debugpy`
      dev dependency. (Manual + automated check -> M6.6.)
- [x] **M6.1.6** Central data-root layout (`server/paths.py`): application code
      lives at the repo/install root (`install_dir()`); user output/data lives
      under a single "Sammelwurzel" (`data_dir()`, default
      `%LOCALAPPDATA%\wogd-ddsp-trainer` on Windows, identical in dev). The data
      root holds `datasets/`, `runs/` and (by default) the SQLite DB. Precedence:
      env `WOGD_DATA_DIR` > DB meta override (set by `PUT /api/settings`) >
      platform default. Only the data directory is user-mutable at runtime; the
      install dir and DB path are fixed. Wiring: `get_db_path`, `runs_dir`,
      `datasets_dir`, `build_tensors` all resolve through `paths.py`. Added REST
      endpoints `GET/PUT /api/settings` (live data-dir change with validation +
      datasets/runs migration + persistence + reset to default), `GET
      /api/settings/defaults`, and the UI Settings view (sidebar "System" group).
      Added `settings.test.js` + `test_api_settings.py`. `ensure_data_dirs()` is
      called at startup. (Verified -> M6.6.)
- [x] **M6.1.7** `build-installer` VSCode task + `scripts/build-installer.ps1`:
      creates a self-contained, portable Windows package under
      `dist/installer/wogd-ddsp-trainer/` (backend source + `webui/dist` + bundled
      `.venv` + `start.bat`/launchers). No global install; no host config changed.
      User data lives under `%LOCALAPPDATA%\wogd-ddsp-trainer`. A full Windows
      NSIS/InnoSetup installer with uninstaller is deferred to a later milestone.

### M6.2 Docs

- [x] **M6.2.1** Finalize docs: architecture, workflow, UI requirements,
      implementation plans up-to-date. _(Note: additional doc updates were
      performed during the M1–M6 review on 2026-08-31; see History.)_

### M6.3 Error handling

- [x] **M6.3.1** Backend error handling: consistent REST error envelope
      via ``server/errors.py`` (``ApiError`` + ``http_exception_handler`` +
      ``unhandled_exception_handler``, registered in ``main.py``); worker
      failure persistence (``error`` column on ``runs``/``synthesis_jobs``
      tables, ``run_set_error``, ``synth_update(error=...)``, task workers
      store errors on failure).
- [x] **M6.3.2** UI error surfaces: ``ToastNotifications.vue`` (animated
      overlay toast component), ``useNotificationsStore`` (Pinia store with
      ``info``/``success``/``warn``/``error`` actions + auto-dismiss), wired
      in ``App.vue``. Existing views retain inline error display; the toast
      system is available for all API-fetching views.

### M6.4 Performance

- [x] **M6.4.1** Profile the training loop + inference on RTX 3060 Laptop GPU
      (6 GB VRAM). Results (``tests/profile_gpu.py``):

      | Config | Forward | Loss | Backward | Optimizer | Total/step | Inference (2s) |
      |---|---|---|---|---|---|---|
      | QUALITY (h=512, 5 scales) | 6.3 ms | 8.0 ms | 15.7 ms | 3.0 ms | **35.5 ms** | 7.8 ms (RTF 0.004) |
      | NORMAL (h=256, 3 scales) | 3.0 ms | 2.7 ms | 5.6 ms | 1.1 ms | **14.6 ms** | 5.7 ms (RTF 0.003) |

      **Bottleneck analysis (CCD: optimize only measured hot spots):**
      - Backward pass (38-45 % of step time) — inherent to PyTorch autograd;
        not trivially optimizable without architecture changes.
      - Loss computation (22 % for QUALITY, 18 % for NORMAL) — STFT-based;
        could be reduced by lowering scale count (but trades quality).
      - Forward pass (17-20 %) — DDSPCore synthesis cost; ``torch.compile``
        could help but adds complexity.
      - Inference is already **well below real-time** (RTF ~0.004).

      **Conclusion per CCD:** No measurable, trivially optimizable bottleneck
      exists that doesn't trade quality or require architecture changes.
      Training throughput (28/68 steps/sec) is healthy for the target hardware.

### M6.5 Output enhancer

_Deferred from M6 to M7 (decision recorded in `checklist.md`). Tracked in
`implementation/m7-experimental.md` as M7.0. Do not implement here._

- [ ] **M6.5.1** ~~Integrate NSF-HiFiGAN~~ → **moved to M7.0.1**
- [ ] **M6.5.2** ~~Shallow-diffusion~~ → **moved to M7.0.2**
- [ ] **M6.5.3** ~~Enhancer tests + docs~~ → **moved to M7.0.3**

### M6.6 VSCode debug/release start verification

- [x] **M6.6.1** Add automated test for release static serving (`WOGD_SERVE_STATIC=1`
      serves `index.html` + assets; non-API routes fall back to `index.html`).
      *(via `server.main.mount_frontend` + `tests/test_frontend_static.py`.)*
- [x] **M6.6.2** Run the full checks (`ruff check`, `ruff format --check`,
      `pytest`, `vitest`), re-run `npm run build`, and re-verify the release
      backend live (stop server after).
      *(green: ruff/format 0, pytest 133 passed / 1 GPU-skip, vitest 18 passed,
      build ok, live check 200 root+SPA+API; server stopped.)*
- [x] **M6.6.3** Update `doc/workspace-workflow.md` with the debug
      (compound launch) and release (static-serve) run instructions.
- [x] **M6.6.4** Verify `scripts/start-app.ps1` in both modes:
      *Release* — no rebuild when `dist` current, rebuild when `dist` missing,
      then serves `/` (html) + `/api`; server stopped after. *Debug* — Vite dev
      on `:5173` + debugpy backend listening on `:5678`; both stopped after.

## BUGS

_References only; full records in [`../bugs.md`](../bugs.md)._

- `BUG-3` — `App.vue` default-imported `RouterView`; production build failed.
  **status: fixed** (named import).
- `BUG-4` — Training Speed (FAST/NORMAL/QUALITY) fehlt als separater Parameter;
  UI zeigt fake-GPU statt echter GPU; keine Preset+Speed-VRAM-Validierung.
  **status: fixed** (M6 — BUG-4 fix).

## History

_Append-only, newest first._

- 2026-08-31 — **BUG-4** implemented: (a) `server/routes/host.py` with
  `apply_speed()` (FAST 0.5x, NORMAL 0.75x, QUALITY 0.9x on hidden_size) +
  `GET /api/host/info` (GPU info from `suggest_for_host()`) + `POST
  /api/host/validate-preset`. (b) apiClient `getHostInfo()`/`getGPUInfo()`/
  `validatePreset()` + `gpuHostInfoFixture` + `validatePresetFixture`. (c)
  `TrainingConfigView.vue`: speed radio buttons (FAST/NORMAL/QUALITY), real
  GPU display from host endpoint (name + VRAM + tier), VRAM validation popup
  on preset/speed change ("Die gewählte Konfiguration überschreitet den
  verfügbaren VRAM. Möchten Sie die empfohlenen Anpassungen übernehmen?" +
  "Anpassungen annehmen" / "Abbrechen"). Full checks: ruff/format 0, pytest
  151/1, vitest 23/0, build clean.
- 2026-08-31 — **M6.4** profiled on RTX 3060 Laptop (6 GB): QUALITY step
  35.5ms (28/s), NORMAL step 14.6ms (68/s), inference RTF ~0.004x. Per CCD
  no trivial optimisation exists that doesn't trade quality or require
  architectural changes. Created `tests/profile_gpu.py` for future
  benchmarking.
- 2026-08-31 — **M6.3** implemented: created `server/errors.py` with
  `ApiError` + convenience constructors (`not_found`, `bad_request`, `conflict`,
  `InternalError`); `http_exception_handler` and `unhandled_exception_handler`
  registered in `main.py` via `install_handlers()`. All HTTP errors now return
  the stable envelope `{"error": {"code": "...", "message": "..."}}`. Added
  `error TEXT` columns to `runs` and `synthesis_jobs` tables with migration in
  `init_db`. Added `run_set_error`, `synth_update(error=...)`. Updated task
  workers (`run_training_job`, `run_synthesis_job`) to persist error messages
  on failure. Created UI toast system: `webui/src/stores/notifications.js`
  (Pinia store) + `webui/src/components/ToastNotifications.vue` (overlay
  toasts with transitions, wired in `App.vue`). Updated 3 dataset tests for
  new error envelope. Full checks green: ruff/format 0, pytest 139/1 GPU-skip,
  vitest 22/0, build clean.
- 2026-08-31 — **M6.1.6/M6.1.7/M6.1.3** implemented: created `server/paths.py`
  (central location/path resolution: `install_dir()` = app root; `data_dir()`
  = `%LOCALAPPDATA%\wogd-ddsp-trainer` default, identical in dev, with env
  `WOGD_DATA_DIR` > DB meta > default precedence; `datasets_dir()`,
  `runs_dir()`, `db_path()` all resolve through paths; the DB lives at a stable
  bootstrap location so the app can always read the persisted `data_dir`). Rewired
  `get_db_path`, `runs_dir`, `datasets_dir`, `build_tensors` to use paths. Added
  `ensure_data_dirs()` called at startup. Added REST endpoints
  `GET/PUT /api/settings` (live data-dir change with absolute-path validation,
  datasets/runs migration on target, DB meta persistence, reset-to-default),
  `GET /api/settings/defaults`. Added UI Settings view (`SettingsView.vue`) +
  sidebar "System" group + route `/settings`; apiClient/mock/fixtures + `settings.test.js`.
  Added `build-installer` VSCode task + `scripts/build-installer.ps1` (self-contained
  portable Windows package: backend + `webui/dist` + bundled `.venv` + `start.bat`;
  no global install/host config change). Updated docs: README (env vars, VSCode
  tasks table, installation section), `doc/architecture.md` (env vars list),
  `doc/workspace-workflow.md` (packaging section), `doc/m6-polish.md` (steps + history).
  Full checks green: ruff/format 0, pytest 138 passed / 1 GPU-skip (5 new settings
  tests), vitest 21 passed (new settings tests), `npm run build` ok (SettingsView +
  new apiClient/fixture chunks).
- 2026-08-31 — **M6.6** verified: added `server.main.mount_frontend` +
  `tests/test_frontend_static.py` (static serving + SPA fallback). Full checks
  green: `ruff check`/`format --check` 0, `pytest` 133 passed / 1 GPU-skip,
  `vitest` 18 passed, `npm run build` ok. Live release check on `:8021`:
  root/html True, SPA fallback/html True, `/api/datasets` 200; server stopped
  (no lingering listener). `doc/workspace-workflow.md` updated (VSCode tasks +
  launch configs section).
- 2026-08-31 — **M6.1.4/M6.1.5** scoped + implemented: created
  `.vscode/launch.json` (compound `Debug Application` = `Debug Backend`
  debugpy + `Vite Dev (debug)`); rewired `.vscode/tasks.json` so
  `start-application-debug` -> `frontend-dev` and `start-application-release` ->
  `build-release` -> `backend-release` (`WOGD_SERVE_STATIC=1`); added
  `webui/dist` static serving + SPA fallback to `server/main.py`
  (gated on `WOGD_SERVE_STATIC=1`). Found + fixed BUG-3 (`App.vue` RouterView
  named import) so `npm run build` succeeds. Manual release live check passed
  (HTTP 200 `index.html` + `dist/assets`).
