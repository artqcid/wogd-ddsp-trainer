---
type: checklist
title: Checklist - wogd-ddsp-trainer
description: Open tasks (short descriptions) per milestone; source of truth for "what's next"
status: active
generated:
  by: setup
  at: 2026-08-30
stale_after: 2026-12-31
tags: [checklist, milestones, tasks]
---

# wogd-ddsp-trainer - Checklist

_Open tasks only (short descriptions). Detailed info:
[`architecture.md`](./architecture.md); draft plan: [`plan.md`](./plan.md);
granular steps: [`implementation/`](./implementation/m1-scaffold.md);
coding rules: `doc/coding-standards.md`; test strategy: `doc/test-strategy.md`.
See [`log.md`](./log.md) for the chronological changelog._

## Milestone M1 - Scaffold

- [ ] **M1.1** Repo structure: `dataset/`, `model/`, `train/`, `inference/`,
      `server/`, `webui/`, `tests/`.
- [ ] **M1.2** Python venv (`pyproject.toml` / `requirements.txt`) with
      torch + torchaudio, RMVPE (F0), librosa, soundfile, FastAPI, uvicorn,
      Celery, redis, neutone_sdk; `ruff` + `pytest` wired.
- [ ] **M1.3** Vue 3 + Vite (+ Pinia) web scaffold with a health check; Vitest
      smoke test.
- [ ] **M1.4** End-to-end check commands green (`ruff check`, `pytest`, `vitest`).
- [ ] **M1.5** `.vscode/tasks.json` with `build-debug`, `build-release`,
      `e2e-test`, `start-application-debug`, `start-application-release` (as
      soon as the M1 build process/artifacts exist).
- [ ] **M1.6** `LICENSE` (Apache-2.0) + open-source dependency review: only
      OSI-approved OSS deps (incl. Wavesurfer.js, BSD-3-Clause); nothing that
      blocks OSS publication or requires paid licenses.
- [ ] **M1.7** Dependency sourcing: clone needed libs from
      `C:\Users\marku\Documents\GitHub\thirdParty` when present there;
      venv-first, reuse global libs via workspace config only when sufficient.

## Milestone M2 - Dataset prep

- [ ] **M2.1** Audio ingestion + resampling to 16 kHz mono + level normalization.
- [ ] **M2.2** Feature extraction: `f0_hz`, `f0_confidence`, `loudness_db`
      (RMVPE/librosa) + per-feature normalization.
- [ ] **M2.3** Train/validation split + caching dataset module.
- [ ] **M2.4** Dataset tests.

## Milestone M3 - Model + training

- [ ] **M3.1** Self-owned DDSP core (PyTorch): harmonic oscillator +
      filtered-noise + reverb synth + multi-scale spectral loss.
- [ ] **M3.2** GPU auto-detection + analysis + optimal training-parameter
      suggestions.
- [ ] **M3.3** Training loop (PyTorch): checkpoints, metrics (TensorBoard),
      resume, GPU.
- [ ] **M3.4** Inference/synthesis module: offline render + low-latency
      realtime model export (Neutone/TorchScript, ONNX).
- [ ] **M3.5** Model + training tests.

## Milestone M4 - Web backend

- [ ] **M4.1** FastAPI services: dataset, model, training, inference.
- [ ] **M4.2** Celery + Redis async training/synthesis jobs + run lifecycle
      over REST (start/stop/resume).
- [ ] **M4.3** Backend tests.
- [ ] **M4.4** TensorBoard URL/embed provisioning for the UI.
- [ ] **M4.5** Preset management: SQLite schema (`presets` table), CRUD
      endpoints, GPU-constraint validation + clamp-on-hardware-change.

## Milestone M5 - Web UI

- [ ] **M5.1** App shell: dark-mode SPA, sidebar (4 nav groups), top bar
      (backend/GPU/project status).
- [ ] **M5.2** Dataset & Preprocessing views: upload ingestion, dataset
      manager, preprocessing (Wavesurfer.js waveform, F0 confidence
      warnings).
- [ ] **M5.3** Model Architecture view: training config (ML params, target
      mode offline/realtime, GPU suggestions) + preset selection
      (FAST/NORMAL/QUALITY + custom) with constraint-clamping display.
- [ ] **M5.4** Training & Monitor view: job control, TensorBoard
      iframe/fallback link, status polling.
- [ ] **M5.5** Inference & Export views: model registry, timbre transfer +
      A/B player, export hub (Neutone/ONNX/TorchScript).
- [ ] **M5.6** Preset Management view: create/edit custom presets (values
      clamped to GPU bounds), "Save as Preset" button in run detail.
- [ ] **M5.7** UI tests (Vitest): every view renders with `MockApiClient` +
      fixtures (mock-data seam).

## Milestone M6 - Polish

- [ ] **M6.1** Packaging (non-Docker).
- [ ] **M6.2** Docs finalization.
- [ ] **M6.3** Error handling (backend + UI).
- [ ] **M6.4** Performance pass (profile, optimize measured bottlenecks only).
- [ ] **M6.5** Output enhancer (native PyTorch vocoder NSF-HiFiGAN /
      shallow-diffusion) to lift raw DDSP output quality (see
      [`related-work.md`](./related-work.md)).

## Milestone M7 - Experimental sound design (Musique Concrète)

- [ ] **M7.1** F0/pitch-curve override editor: per-file canvas inspector +
      global dataset transformation rules (quantize, chaos/noise injection,
      pitch inversion).
- [ ] **M7.2** DDSP component mixer: harmonics-vs-noise balance sliders.
- [ ] **M7.3** Reverb IR injection + freeze (de-reverberation + inverse
      acoustic compensation) + IR extractor (export learned IR as `.wav`).
- [ ] **M7.4** Experimental sound-design tests + docs.

## Milestone M8 - Experimental synthesis hacks

- [ ] **M8.1** Hack infrastructure: variant/feature flags on our own DDSP core.
- [ ] **M8.2** Inharmonic multipliers (bell hack) in the harmonic synthesizer.
- [ ] **M8.3** Wavetable exchange (replace `sin` with square/saw/wavetable).
- [ ] **M8.4** Frequency-band blindness (spectral-loss masking) + LFO injection
      (decoder bypass).
- [ ] **M8.5** Synthesis-hack docs + tests.
