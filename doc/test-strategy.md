---
type: test-strategy
title: Test Strategy - wogd-ddsp-trainer
description: Automated-first test strategy, CCD yellow/green, coverage targets, test pyramid
status: active
generated:
  by: setup
  at: 2026-08-30
stale_after: 2026-12-31
tags: [testing, ccd, coverage, pytest, vitest]
---

# Test Strategy - wogd-ddsp-trainer

_Complete test strategy. Automated first (CCD yellow/green), manual only where
necessary (audio quality, subjective model output). Applies to all milestones;
per-item test points are listed in `doc/checklist.md`._

## 1. Principles

- **Automated first.** Every deterministic behavior is covered by automated
  tests; manual tests only where automation is impossible or impractical
  (audible quality of synthesis, subjective voice similarity).
- **Test-first** (CCD blue) for new features: write the test before the
  implementation.
- **Fast + deterministic:** unit tests must run in CI/dev without real audio
  files, GPU, or network (mock / fixture everything external).
- **Deterministic seeds:** PyTorch training/feature tests set fixed seeds and
  CPU-only where possible so results are reproducible.

## 2. Test pyramid

1. **Unit tests (most):** functions/classes in isolation - feature extraction,
   batching, model forward, loss computation, server endpoints, Vue components.
2. **Integration tests:** dataset->model->loss roundtrip, FastAPI service with
   test client + mocked training backend, WebSocket status flow.
3. **End-to-end smoke (few):** tiny synthetic dataset trains for a few steps,
   checkpoint saved and reloaded, synthesis produces non-empty audio.

## 3. Coverage

- Aim for ~100%, at least **90%** on the core modules (`dataset/`, `model/`,
  `train/`, `inference/`, `server/`).
- Run with `pytest --cov` (pytest-cov); exclude tests and the web UI build.
- For the web UI, Vitest coverage on components/composables/stores.

## 4. Mocking strategy

- **Audio I/O:** no real files in unit tests. Use tiny in-memory numpy/torch
  tensors or fixture wav snippets (`tests/fixtures/`); stub torchaudio
  decode/save where possible.
- **Feature extraction:** mock or inject lightweight F0/loudness estimators;
  test DSP math with hand-computed expected values.
- **GPU:** train tests run on `cpu`; guard CUDA-only paths with
  `@pytest.mark.parametrize` over device or a fixture that skips without GPU.
- **Server:** use FastAPI `TestClient` with mocked training/inference
  services; WebSocket tests with a mocked runner.
- **Network:** no live downloads; datasets are cached fixtures.

## 5. Commands

- Python tests: `pytest` (add `-q` for quiet, `--cov` for coverage).
- Lint/format (CCD red/orange hygiene): `ruff check` and `ruff format --check`.
- Web UI tests: `vitest` (in `webui/`).
- These exact commands are the Definition-of-Done checks in `AGENTS.md`.

## 6. What is NOT auto-tested (manual)

- Subjective synthesis quality / voice similarity (listen test).
- GPU performance and real-time streaming experience.
