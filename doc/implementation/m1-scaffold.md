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

- [ ] **M1.1.1** Create backend package dirs `dataset/`, `model/`, `train/`,
      `inference/`, `server/`, each with an empty `__init__.py`.
      Verify: `ruff check` passes on the new empty modules.
- [ ] **M1.1.2** Create `tests/` with `__init__.py` and a placeholder
      `test_smoke.py` (assert `True`).
      Verify: `pytest` collects the smoke test.

### M1.2 Python environment

- [ ] **M1.2.1** Create `pyproject.toml` with core deps: `torch`, `torchaudio`,
      `rmvpe`, `librosa`, `soundfile`, `fastapi`, `uvicorn`, `celery`, `redis`,
      `neutone_sdk`.
      Verify: file parses (`python -m pip install -e .` dry-run or `ruff`).
- [ ] **M1.2.2** Add dev deps: `ruff`, `pytest`, `pytest-cov`; add `[tool.ruff]`
      config (line length, target py3).
      Verify: `ruff check` runs.
- [ ] **M1.2.3** Create `.venv` and install (`python -m venv .venv`,
      `.venv\Scripts\python.exe -m pip install -e .`).
      Verify: `.venv\Scripts\python.exe -c "import torch, torchaudio"` succeeds.
- [ ] **M1.2.4** Verify mixed precision support:
      `.venv\Scripts\python.exe -c "from torch.cuda.amp import autocast, GradScaler"`.
      If no GPU, the import must still succeed (CPU fallback handled in
      `train/trainer.py`).

### M1.3 Web scaffold

- [ ] **M1.3.1** Scaffold Vue 3 + Vite + Pinia under `webui/`.
      Verify: `npm install` + `npm run dev` boots without errors.
- [ ] **M1.3.2** Add a health-check view + an API-client stub with a
      `MockApiClient` (foundation for the mock-data seam).
      Verify: view renders in dev preview.
- [ ] **M1.3.3** Add a Vitest smoke test.
      Verify: `npx vitest run` passes.

### M1.4 Check commands

- [ ] **M1.4.1** Ensure `ruff check` is clean.
- [ ] **M1.4.2** Ensure `pytest` is green.
- [ ] **M1.4.3** Ensure `vitest` is green.

### M1.5 VSCode tasks

- [ ] **M1.5.1** Create `.vscode/tasks.json` with `build-debug`, `build-release`,
      `e2e-test`, `start-application-debug`, `start-application-release` wired
      to the planned uvicorn/Vite/venv commands.
      Verify: tasks are parseable JSON; commands point at existing entrypoints.

### M1.6 Licensing & OSS review

- [ ] **M1.6.1** Add `LICENSE` (Apache-2.0).
- [ ] **M1.6.2** Write an OSS dependency review (list deps + licenses; note
      Wavesurfer.js BSD-3-Clause) confirming only OSI-approved deps.

### M1.7 Dependency sourcing

- [ ] **M1.7.1** Check `C:\Users\marku\Documents\GitHub\thirdParty`; clone
      reference libs (e.g. `acids-ircam/ddsp_pytorch`) from there when present;
      prefer the venv, reuse global libs only when sufficient.

## BUGS

_References only; full records in [`../bugs.md`](../bugs.md)._

- (none)

## History

_Append-only, newest first._

- (none yet)
