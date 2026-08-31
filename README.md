# wogd-ddsp-trainer

A web UI training application for **DDSP-based speech synthesis** models. It
exposes a browser UI to prepare datasets, configure and run DDSP training,
monitor progress (TensorBoard), and synthesize/export vocal output.

**Status:** **M1–M5 implemented** — scaffold, dataset prep, model + training
loop, the web backend (FastAPI + Celery/Redis, run lifecycle, TensorBoard
provisioning, preset management with GPU-constraint clamping), and the web UI
(Vue 3 + Vite + Pinia: dataset/preprocessing, model architecture +
presets, training dashboard, inference/export). All checks green
(`ruff`, `pytest`, `vitest`). Milestones M6 (polish) – M8 planned. Roadmap:
[`doc/plan.md`](doc/plan.md) · open tasks: [`doc/checklist.md`](doc/checklist.md).

- **Stack:** Python + PyTorch + torchaudio (self-owned DDSP core) · FastAPI +
  Celery/Redis · Vue 3 + Vite + Pinia.
- **License:** Apache-2.0 — see [section 4](#4-license).

> This file is the GitHub-facing summary of the project. It is kept in sync
> with the knowledge wiki in [`doc/`](doc/) (start at
> [`doc/index.md`](doc/index.md)); update it whenever a knowledge update lands
> in `doc/` (see `AGENTS.md`).

---

## 1. Development — how this project is built

How to clone the repository and work on it in VS Code.

### 1.1 Prerequisites

- Python 3 (managed via a local `.venv`)
- Node.js + npm (for the web UI)
- Git
- VS Code (recommended)

### 1.2 Clone

```bash
git clone <TODO: repository URL> wogd-ddsp-trainer
cd wogd-ddsp-trainer
```

### 1.3 Open in VS Code

Open the workspace file:

```
wogd-ddsp-trainer.code-workspace
```

Recommended extensions: Python (ms-python.python), Vue/Volar.

### 1.4 Backend setup (Python venv)

```pwsh
python -m venv .venv
# CUDA-enabled torch/torchaudio (cp314 wheels are NOT on PyPI — must use the
# PyTorch CUDA index):
.venv\Scripts\python.exe -m pip install torch==2.13.0 torchaudio==2.11.0 `
  --index-url https://download.pytorch.org/whl/cu130
# Then install the package + dev deps:
.venv\Scripts\python.exe -m pip install -e ".[dev]" --no-deps
.venv\Scripts\python.exe -m pip install "librosa>=0.11" "soundfile>=0.13" `
  "torchcrepe==0.0.24" "praat-parselmouth==0.4.7" "fastapi>=0.115" `
  "celery>=5.4" "redis>=5.0" "ruff>=0.6" "pytest>=8.0" "pytest-cov>=5.0"
```

> **Note:** `neutone_sdk` is deferred to M3.4 (see `doc/bugs.md` BUG-1). F0
> extraction uses a factory (`dataset/features.get_f0_extractor`):
> **CREPE-PyTorch** (`torchcrepe`, MIT) primary + **parselmouth** (GPLv3) CPU
> fallback. See `doc/oss-dependencies.md`.

### 1.5 Frontend setup (web UI)

```pwsh
cd webui
npm install
cd ..
```

### 1.6 Run (development / hot reload)

```pwsh
# backend (FastAPI + uvicorn)
.venv\Scripts\python.exe -m uvicorn server.main:app --reload --port 8000

# web UI dev server
cd webui
npm run dev
```

Backend: `http://127.0.0.1:8000` (OpenAPI at `/docs`). The Vite dev server
proxies `/api` to the backend.

The backend is implemented (`server/main.py`); it serves the REST API under
`/api` (datasets, models, runs, inference, presets, TensorBoard). Optional env
vars: `WOGD_DB_PATH`, `WOGD_DATA_DIR`
(default `%LOCALAPPDATA%\wogd-ddsp-trainer` on Windows; sets the data root that
holds `datasets/`, `runs/` and the database), `WOGD_REDIS_URL`, `WOGD_TB_PORT`,
`WOGD_SERVER_PORT`, `WOGD_SERVE_STATIC=1` (release mode: serve `webui/dist` from
FastAPI). The old `WOGD_RUNS_DIR`/`WOGD_DATASETS_DIR` vars are no longer used;
`runs/` and `datasets/` now live under the data root. Async jobs use Celery +
Redis; with no Redis running, the API still works for everything except actual
job execution.

### 1.7 Tests, lint & build

```pwsh
# Python
.venv\Scripts\python.exe -m ruff check
.venv\Scripts\python.exe -m ruff format --check
.venv\Scripts\python.exe -m pytest

# Web UI
cd webui && npx vitest run && cd ..
```

All four checks are green for the current M1 scaffold (`ruff check`,
`ruff format --check`, `pytest`, `vitest`).

### 1.8 VS Code tasks

The workspace defines these tasks (`.vscode/tasks.json`):

| Task | Purpose |
|---|---|
| `build-debug` | frontend development build |
| `build-release` | frontend production build |
| `build-installer` | create a self-contained, portable Windows package |
| `e2e-test` | end-to-end tests |
| `start-application-debug` | backend + frontend (dev, hot reload) |
| `start-application-release` | backend (release) |

---

## 2. Installation (end users)

A self-contained, portable Windows package is produced by the `build-installer`
VS Code task (`scripts/build-installer.ps1`). It bundles the backend, the
production frontend build, and the application venv (Python + libraries) under
`dist/installer/wogd-ddsp-trainer/` — nothing is installed globally and no
host configuration is changed.

To build the package: run `Ctrl+Shift+B` → `build-installer`, or run
`pwsh scripts/build-installer.ps1`. Then distribute the contents of
`dist/installer/wogd-ddsp-trainer/` (e.g. zip it). Start by double-clicking
`start.bat`; open `http://127.0.0.1:8000`.

User data (datasets, runs, database) is stored under
`%LOCALAPPDATA%\wogd-ddsp-trainer` on first run. This data directory can be
changed live in the app (Settings → Data directory). A full NSIS/InnoSetup
Windows installer with an uninstaller is planned for a later milestone.

`[x] M6.1.3` - local install/run path documented. See `doc/implementation/m6-polish.md`.

---

## 3. Using the software for training

`<TODO M6: packaging not yet implemented.>` (The dataset-prep module, training
loop and web backend — `dataset/`, `model/`, `train/`, `server/` — and the M5
browser UI under `webui/` are all in. REST services under `/api`, run lifecycle
via Celery, preset management, and a Vue 3 dashboard are implemented and
covered by Vitest.)

The intended workflow:

1. **Prepare a dataset** — upload monophonic, dry audio (~10-15 min); the app
   resamples to 16 kHz mono and extracts F0 + loudness features.
2. **Configure the model** — ML + DDSP hyperparameters, target mode
   (offline / realtime), GPU parameter suggestions.
3. **Train & monitor** — start/stop/resume runs; monitor loss, spectrograms and
   checkpoint audio in TensorBoard.
4. **Inference & export** — timbre transfer (source -> trained timbre), A/B
   comparison, export as Neutone / ONNX / TorchScript.

Detailed usage will be documented here as the milestones land.

---

## 4. License

This project is licensed under the **Apache License 2.0** — see
[`LICENSE`](LICENSE).

Dependencies are restricted to OSI-approved open-source licenses; nothing
requires paid licenses or blocks public release.
