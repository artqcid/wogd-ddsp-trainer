---
type: implementation-plan
status: draft
milestone: M1 - Scaffold
generated:
  by: primary-agent
  at: 2026-08-31
stale_after: 2026-12-31
---

# Implementation Plan - M1 Scaffold

_Granular plan for milestone M1. Meta plan: [`../plan.md`](../plan.md); status:
[`../checklist.md`](../checklist.md); architecture:
[`../architecture.md`](../architecture.md)._

## How to use

- Each step below is one small, self-contained task (approx. one subagent task).
- Work in order; mark `[x]` and record every step in `## History` (what + how).
- Bugs are recorded in full only in [`../bugs.md`](../bugs.md); reference them
  here by `BUG-<id>`.

## Steps

### M1.1 Repo structure

- [x] **M1.1.1** Create backend package dirs `dataset/`, `model/`, `train/`,
      `inference/`, `server/`, each with an empty `__init__.py`.
      Verify: `ruff check` passes on the new empty modules.
- [x] **M1.1.2** Create `tests/` with `__init__.py` and a placeholder
      `test_smoke.py` (assert `True`).
      Verify: `pytest` collects the smoke test.

### M1.2 Python environment

- [x] **M1.2.1** Create `pyproject.toml` with core deps: `torch`, `torchaudio`,
      `rmvpe`, `librosa`, `soundfile`, `fastapi`, `uvicorn`, `celery`, `redis`,
      `neutone_sdk`.
      Verify: file parses (`python -m pip install -e .` dry-run or `ruff`).
      Note: rmvpe is NOT on PyPI (sourced via M1.7); `neutone_sdk` is deferred
      to M3.4 (see BUG-1 in `../bugs.md`).
- [x] **M1.2.2** Add dev deps: `ruff`, `pytest`, `pytest-cov`; add `[tool.ruff]`
      config (line length, target py3).
      Verify: `ruff check` runs.
- [x] **M1.2.3** Create `.venv` and install (`python -m venv .venv`,
      `.venv\Scripts\python.exe -m pip install -e .`).
      Verify: `.venv\Scripts\python.exe -c "import torch, torchaudio"` succeeds.
- [x] **M1.2.4** Verify mixed precision support:
      `.venv\Scripts\python.exe -c "from torch.cuda.amp import autocast, GradScaler"`.
      If no GPU, the import must still succeed (CPU fallback handled in
      `train/trainer.py`).

### M1.3 Web scaffold

- [x] **M1.3.1** Scaffold Vue 3 + Vite + Pinia under `webui/`.
      Verify: `npm install` + `npm run dev` boots without errors.
- [x] **M1.3.2** Add a health-check view + an API-client stub with a
      `MockApiClient` (foundation for the mock-data seam).
      Verify: view renders in dev preview.
- [x] **M1.3.3** Add a Vitest smoke test.
      Verify: `npx vitest run` passes.

### M1.4 Check commands

- [x] **M1.4.1** Ensure `ruff check` is clean.
- [x] **M1.4.2** Ensure `pytest` is green.
- [x] **M1.4.3** Ensure `vitest` is green.

### M1.5 VSCode tasks

- [x] **M1.5.1** Create `.vscode/tasks.json` with `build-debug`, `build-release`,
      `e2e-test`, `start-application-debug`, `start-application-release` wired
      to the planned uvicorn/Vite/venv commands.
      Verify: tasks are parseable JSON; commands point at existing entrypoints.

### M1.6 Licensing & OSS review

- [x] **M1.6.1** Add `LICENSE` (Apache-2.0).
- [x] **M1.6.2** Write an OSS dependency review (list deps + licenses; note
      Wavesurfer.js BSD-3-Clause) confirming only OSI-approved deps.

### M1.7 Dependency sourcing

- [x] **M1.7.1** Check `C:\Users\marku\Documents\GitHub\thirdParty`; clone
      reference libs (e.g. `acids-ircam/ddsp_pytorch`) from there when present;
      prefer the venv, reuse global libs only when sufficient.
      Note: `thirdParty\ddsp` holds `magenta/ddsp` (TF spec reference only; we
      own the PyTorch core). rmvpe sourced from GitHub for M2 (see History).

## BUGS

_References only; full records in [`../bugs.md`](../bugs.md)._

- `BUG-1` — neutone_sdk pinned numpy<2.3 lacks cp314 Windows wheel (py3.14). Open.

- (none)

## History

_Append-only, newest first._

- 2026-08-31 — **M1 complete.** Repo structure (`dataset/ model/ train/
  inference/ server/ tests/`), `pyproject.toml`, `.venv` (Python 3.14, torch
  2.13.0+cu130), webui scaffold (Vue3+Vite+Pinia, HealthView, ApiClient +
  MockApiClient mock seam), all checks green (`ruff`, `pytest`, `vitest`).
  Dependency sourcing decisions (see `../oss-dependencies.md`):
  - **torch/torchaudio install:** CUDA-enabled cp314 Windows wheels are NOT on
    PyPI (PyPI has CPU-only for 3.14). Installed via
    `.venv\Scripts\python.exe -m pip install torch==2.13.0 torchaudio==2.11.0
    --index-url https://download.pytorch.org/whl/cu130`. RTX 3060 detected,
    `torch.cuda.is_available() == True`, mixed precision imports OK.
  - **`pip install -e .` uses `--no-deps`** then explicit dep install, because
    pip's isolated editable metadata resolution tries to source-build numpy
    2.2.6 (no cp314 wheel) on Python 3.14/Windows.
  - **`neutone_sdk` deferred to M3.4** (BUG-1): it pins `numpy<2.3`
    which has no cp314 Windows wheel; pip would source-build numpy and fail on
    the missing compiler. Reintroduce once a numpy-compatible release exists.
  - **`rmvpe` sourced from GitHub** (not on PyPI): canonical PyTorch repo
    `Dream-High/RMVPE` (via `yxlllc/RMVPE`); install
    `pip install git+https://github.com/dreamgaussian/rmvpe.git` (verify on
    M2). License to-verify before first use (see `../oss-dependencies.md`).
  - **ruff excludes `wogd_ddsp_mcp_server.py`** (standalone MCP tool script,
    own #noqa/long-line style, not part of the app package).
  - `thirdParty\ddsp` = `magenta/ddsp` (TF spec reference only; self-owned
    PyTorch core in M3).
