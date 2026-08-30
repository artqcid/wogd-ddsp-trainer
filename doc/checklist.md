# wogd-ddsp-trainer - Checklist

_Open tasks only (short descriptions). Detailed info:
[`architecture.md`](./architecture.md); draft plan: [`plan.md`](./plan.md);
coding rules: `doc/coding-standards.md`; test strategy: `doc/test-strategy.md`.
See [`log.md`](./log.md) for the chronological changelog._

## Milestone M1 - Scaffold

- [ ] **M1.1** Repo structure: `dataset/`, `model/`, `train/`, `inference/`,
      `server/`, `webui/`, `tests/`.
- [ ] **M1.2** Python venv (`pyproject.toml` / `requirements.txt`) with PyTorch,
      torchaudio, FastAPI, uvicorn; `ruff` + `pytest` wired.
- [ ] **M1.3** Web scaffold (Vue + Vite) with a health check; Vitest smoke test.
- [ ] **M1.4** End-to-end check commands green (`ruff check`, `pytest`, `vitest`).

## Milestone M2 - Dataset prep

- [ ] **M2.1** Audio ingestion + resampling to 16 kHz mono.
- [ ] **M2.2** Feature extraction: loudness, F0, harmonic amplitude, aperiodicity.
- [ ] **M2.3** Train/validation split + caching dataset module.
- [ ] **M2.4** Dataset tests.

## Milestone M3 - Model + training

- [ ] **M3.1** DDSP decoder (oscillator + filtered-noise) + losses (spectral,
      multiscale STFT, F0/loudness).
- [ ] **M3.2** Training loop: checkpoints, metrics, resume, GPU.
- [ ] **M3.3** Inference/synthesis module (checkpoint -> render).
- [ ] **M3.4** Model + training tests.

## Milestone M4 - Web backend

- [ ] **M4.1** FastAPI services: dataset, model, training, inference.
- [ ] **M4.2** WebSocket training-status streaming + run management.
- [ ] **M4.3** Backend tests.

## Milestone M5 - Web UI

- [ ] **M5.1** Dataset manager view.
- [ ] **M5.2** Training config + live dashboard.
- [ ] **M5.3** Model registry + inference/synthesis player.

## Milestone M6 - Polish

- [ ] **M6.1** Packaging, docs, error handling, performance.
