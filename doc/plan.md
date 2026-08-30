---
type: plan
status: draft
generated:
  by: setup
  at: 2026-08-30
description: Development roadmap for the web UI DDSP training app
stale_after: 2026-12-31
---

# Draft Plan

_Roadmap / open questions / risks. Active tasks live in
[`checklist.md`](./checklist.md); chronological history in
[`log.md`](./log.md)._

## Milestones

- **M1 - Scaffold:** repo structure, Python venv + deps, web scaffold
  (backend + frontend), CI-style check commands (`ruff`, `pytest`, `vitest`).
- **M2 - Dataset prep:** audio ingestion, normalization, feature extraction,
  train/validation split + tests.
- **M3 - Model + training loop:** DDSP decoder + losses, training loop with
  checkpoints/metrics, resume, GPU support + tests.
- **M4 - Web backend:** FastAPI services for dataset/model/training/inference,
  WebSocket status streaming, run management + tests.
- **M5 - Web UI:** dataset manager, training config + dashboard, model
  registry, inference/synthesis player.
- **M6 - Polish:** packaging (Docker/image), docs, performance, error handling.

## Open questions / risks

- DDSP implementation: use an existing library (e.g. `ddsp`/`ddsp-pytorch`) or
  implement the decoder from scratch? Licensing + control.
- F0/feature extraction dependency weight vs. pure-torch operations.
- Real-time vs. offline synthesis requirement.
- GPU availability and training time budget.
- Web audio streaming format + playback latency expectations.

## Decisions recorded

- Agent-facing docs and identifiers in English.
- Python + FastAPI + Vue (matches ecosystem conventions).
