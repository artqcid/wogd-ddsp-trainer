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
  for dependencies; the front-end (Vue/React + Vite) lives under `webui/`.
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
- Vite dev server proxies `/api` and `/ws` to the backend during development.

## 5. Training / inference notes

- Training runs are launched from the backend or a CLI entrypoint; logs and
  checkpoints go to a configured run dir (see `doc/plan.md` for M2/M3).
- GPU-heavy runs are only initiated deliberately (long-running); tests stay
  on CPU.
- The RAG/Code-Wiki MCP (`wogd_ddsp`) is kept current via
  `index_project_code` after every completed task (see `AGENTS.md`).
