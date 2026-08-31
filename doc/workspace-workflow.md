---
type: workflow
title: Workspace Workflow - Build, Test, Run, Hot-Reload
description: venv/ruff/pytest/uvicorn/Vite workflow for the wogd-ddsp-trainer project
status: active
generated:
  by: setup
  at: 2026-08-30
stale_after: 2026-12-31
tags: [workflow, build, test, pip, pytest, uvicorn, vite, hot-reload]
---

# Workspace Workflow - wogd-ddsp-trainer

_Setup, lint/format, test, run and hot-reload workflow for the web UI DDSP
training app. Applies to all agents. Architecture: `doc/architecture.md`;
open tasks: `doc/checklist.md`; coding rules: `doc/coding-standards.md`;
test strategy: `doc/test-strategy.md`._

## 1. Standing requirements

- **R1 - Green checks at all times:** `ruff check`, `ruff format --check`,
  `pytest` (Python) and `vitest` (web UI) must pass. These are the
  Definition-of-Done checks (see `AGENTS.md`).
- **R2 - Reproducible env:** the Python venv (`.venv/`) is the single source
  for dependencies; the front-end (Vue 3 + Vite) lives under `webui/`.
- **R3 - Run + hot reload:** it must always be possible to start the FastAPI
  backend and the Vite dev server and see changes live.

## 2. Setup

```pwsh
# Backend
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt   # or -e . with pyproject.toml

# Web UI
cd webui
npm install
cd ..
```

## 3. Checks (Definition of Done)

```pwsh
.venv\Scripts\python.exe -m ruff check
.venv\Scripts\python.exe -m ruff format --check
.venv\Scripts\python.exe -m pytest
cd webui && npx vitest run && cd ..
```

## 4. Run

```pwsh
# Backend (FastAPI + uvicorn, reload for dev)
.venv\Scripts\python.exe -m uvicorn server.main:app --reload --port 8000

# Web UI dev server (hot reload)
cd webui
npm run dev
```

- Backend on `http://127.0.0.1:8000` (OpenAPI at `/docs`).
- Vite dev server proxies `/api` to the backend during development.

## 5. VSCode tasks & launch configs

The app is started via the **Terminal → Run Task** menu (or `Ctrl+Shift+B`):
`start-application-debug` and `start-application-release`. Both are **not** build
tasks — they check whether the frontend build is current (rebuilding only if
`webui/dist` is missing or older than any source under `webui/`), then start the
**whole application** (backend + frontend together) in the background. Their
logs stay in the task terminal; `Ctrl+C` terminates them together.

The actual work lives in `scripts/start-app.ps1 -Mode <Debug|Release>`
(`.vscode/tasks.json` just invokes it). Lint/format checks are unaffected.

### Debug (backend + frontend debuggable)

- `start-application-debug` → builds the frontend only if stale (dev build,
  `--mode development`), then starts:
  - the **backend** with debugpy (`python -m debugpy --listen 5678
    --wait-for-client -m uvicorn server.main:app`) on `:8000`;
  - the **Vite dev server** on `:5173` (JS/HTML debuggable, hot reload).
- To debug the backend: after starting the task, press `F5` with the
  `Debug Backend (attach)` launch config (`.vscode/launch.json`, connects to
  `127.0.0.1:5678`). The backend waits for the attach (so startup/lifespan can
  be debugged), then serves and honours breakpoints in `server/`.
- Alternative native path: the `Debug Application` **compound** launch config
  (Run and Debug panel, `F5`) starts `Debug Backend` + `Vite Dev (debug)`
  directly without the freshness check.

### Release (serves the built frontend from FastAPI)

- `start-application-release` → builds the frontend only if stale (production
  `vite build` -> `webui/dist`), then starts uvicorn on `:8000` with
  `WOGD_SERVE_STATIC=1`. FastAPI serves both the API **and** the built frontend
  from `webui/dist` (SPA fallback for non-`/api` routes) — open
  `http://127.0.0.1:8000`.

- Set `WOGD_SERVE_STATIC=1` in the environment to enable static serving
  (`server/main.py` gates the mount on this flag; disabled by default so Vite
  owns the frontend during development).

## 6. Packaging (portable Windows package)

A self-contained, portable Windows package is produced by the `build-installer`
VSCode task (`scripts/build-installer.ps1`). It bundles the backend source,
the production frontend build (`webui/dist`) and the application venv (Python
interpreter + all runtime libraries) under `dist/installer/wogd-ddsp-trainer/`
— nothing is installed globally and no host configuration is modified.

To build the package: run `Ctrl+Shift+B` → `build-installer`, or run
`pwsh scripts/build-installer.ps1`. Distribute the contents of
`dist/installer/wogd-ddsp-trainer/` (e.g. zip it). Start with `start.bat`;
open `http://127.0.0.1:8000` in a browser.

User data (datasets, runs, database) is stored under
`%LOCALAPPDATA%\wogd-ddsp-trainer` on first run and can be changed live in the
app (Settings → Data directory). The data directory is the single "Sammelwurzel"
that holds `datasets/`, `runs/` and (by default) the SQLite DB; only this folder
is user-mutable at runtime. A full NSIS/InnoSetup Windows installer with an
uninstaller is planned for a later milestone.

## 7. Training / inference notes

- Training runs are launched from the backend or a CLI entrypoint; logs and
  checkpoints go to a configured run dir (see `doc/plan.md` for M2/M3).
- GPU-heavy runs are only initiated deliberately (long-running); tests stay
  on CPU.
- The RAG/Code-Wiki MCP (`wogd_ddsp`) is kept current via
  `index_project_code` after every completed task (see `AGENTS.md`).
