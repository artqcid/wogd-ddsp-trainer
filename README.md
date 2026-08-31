# wogd-ddsp-trainer

A web UI training application for **DDSP-based speech synthesis** models. It
exposes a browser UI to prepare datasets, configure and run DDSP training,
monitor progress (TensorBoard), and synthesize/export vocal output.

**Status:** scaffold phase — milestones M1-M8 planned, not yet implemented.
Roadmap: [`doc/plan.md`](doc/plan.md) · open tasks:
[`doc/checklist.md`](doc/checklist.md).

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
.venv\Scripts\python.exe -m pip install -r requirements.txt   # or: -e . with pyproject.toml
```

`<TODO M1.2: requirements.txt / pyproject.toml not created yet>`

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

`<TODO M4: server.main:app — the FastAPI app is not implemented yet>`

### 1.7 Tests, lint & build

```pwsh
# Python
.venv\Scripts\python.exe -m ruff check
.venv\Scripts\python.exe -m ruff format --check
.venv\Scripts\python.exe -m pytest

# Web UI
cd webui && npx vitest run && cd ..
```

`<TODO M1: test/build scaffolding not implemented yet>`

### 1.8 VS Code tasks

The workspace defines these tasks (`.vscode/tasks.json`):

| Task | Purpose |
|---|---|
| `build-debug` | frontend development build |
| `build-release` | frontend production build |
| `e2e-test` | end-to-end tests |
| `start-application-debug` | backend + frontend (dev, hot reload) |
| `start-application-release` | backend (release) |

---

## 2. Installation (end users)

`<TODO M6: non-Docker packaging not implemented yet. Planned: a wheel/local
distribution for the backend + a static frontend bundle. See
doc/checklist.md M6.1 and doc/implementation/m6-polish.md>`

Once available, install instructions will go here.

---

## 3. Using the software for training

`<TODO M2-M5: the training pipeline and web UI are not implemented yet>`

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
