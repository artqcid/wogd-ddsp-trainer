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

- [x] **M1.1** Repo structure: `dataset/`, `model/`, `train/`, `inference/`,
      `server/`, `webui/`, `tests/`.
- [x] **M1.2** Python venv (`pyproject.toml` / `requirements.txt`) with
      torch + torchaudio, RMVPE (F0), librosa, soundfile, FastAPI, uvicorn,
      Celery, redis, neutone_sdk; `ruff` + `pytest` wired.
      (neutone_sdk deferred to M3.4 — BUG-1; RMVPE sourced from GitHub.)
- [x] **M1.3** Vue 3 + Vite (+ Pinia) web scaffold with a health check; Vitest
      smoke test.
- [x] **M1.4** End-to-end check commands green (`ruff check`, `pytest`, `vitest`).
- [x] **M1.5** `.vscode/tasks.json` with `build-debug`, `build-release`,
      `e2e-test`, `start-application-debug`, `start-application-release` (as
      soon as the M1 build process/artifacts exist).
- [x] **M1.6** `LICENSE` (Apache-2.0) + open-source dependency review: only
      OSI-approved OSS deps (incl. Wavesurfer.js, BSD-3-Clause); nothing that
      blocks OSS publication or requires paid licenses.
- [x] **M1.7** Dependency sourcing: clone needed libs from
      `C:\Users\marku\Documents\GitHub\thirdParty` when present there;
      venv-first, reuse global libs via workspace config only when sufficient.

## Milestone M2 - Dataset prep

- [x] **M2.1** Audio ingestion + resampling to 16 kHz mono + level normalization.
- [x] **M2.2** Feature extraction: `f0_hz`, `f0_confidence`, `loudness_db`
      (F0 via factory: CREPE-PyTorch primary / parselmouth fallback; loudness
      via librosa) + per-feature normalization + `.npy` export/load.
- [x] **M2.3** Train/validation split + caching dataset module.
- [x] **M2.4** Dataset tests (ingestion, features, split, cache).

## Milestone M3 - Model + training

- [x] **M3.1** Self-owned DDSP core (PyTorch): harmonic oscillator +
      filtered-noise + reverb synth + multi-scale spectral loss.
- [x] **M3.2** GPU auto-detection + analysis + optimal training-parameter
      suggestions.
- [x] **M3.3** Training loop (PyTorch): checkpoints, metrics (TensorBoard),
      resume, GPU.
- [x] **M3.4** Inference/synthesis module: offline render + low-latency
      realtime model export (Neutone/TorchScript, ONNX).
- [x] **M3.5** Model + training tests.

## Milestone M4 - Web backend

- [x] **M4.1** FastAPI services: dataset, model, training, inference.
- [x] **M4.2** Celery + Redis async training/synthesis jobs + run lifecycle
      over REST (start/stop/resume).
- [x] **M4.3** Backend tests.
- [x] **M4.4** TensorBoard URL/embed provisioning for the UI.
- [x] **M4.5** Preset management: SQLite schema (`presets` table), CRUD
      endpoints, GPU-constraint validation + clamp-on-hardware-change.

## Milestone M5 - Web UI

- [x] **M5.1** App shell: dark-mode SPA, sidebar (4 nav groups), top bar
      (backend/GPU/project status).
- [x] **M5.2** Dataset & Preprocessing views: upload ingestion, dataset
      manager, preprocessing (Wavesurfer.js waveform, F0 confidence
      warnings).
- [x] **M5.3** Model Architecture view: training config (ML params, target
      mode offline/realtime, GPU suggestions) + preset selection
      (FAST/NORMAL/QUALITY + custom) with constraint-clamping display.
- [x] **M5.4** Training & Monitor view: job control, TensorBoard
      iframe/fallback link, status polling.
- [x] **M5.5** Inference & Export views: model registry, timbre transfer +
      A/B player, export hub (Neutone/ONNX/TorchScript).
- [x] **M5.6** Preset Management view: create/edit custom presets (values
      clamped to GPU bounds), "Save as Preset" button in run detail.
- [x] **M5.7** UI tests (Vitest): every view renders with `MockApiClient` +
      fixtures (mock-data seam).

## Milestone M6 - Polish

- [x] **M6.1** Packaging (non-Docker): data-root layout (`server/paths.py`),
      `%LOCALAPPDATA%` default, live data-dir change (`GET/PUT /api/settings`),
      UI Settings view, `build-installer` VSCode task + packaging script.
- [x] **M6.2** Docs finalization: architecture, workflow, UI requirements,
      implementation plans up-to-date (M6.1/M6.3/M6.4 changes documented).
- [x] **M6.3** Error handling: consistent REST envelope (`server/errors.py`),
      worker failure persistence (`error` columns on DB tables),
      UI toast notifications (Pinia store + overlay component).
- [x] **M6.4** Performance pass: profiled on RTX 3060 Laptop GPU
      (QUALITY: 28 steps/s, NORMAL 68 steps/s; inference RTF ~0.004x).
      Per CCD no trivial optimisation merited.
- [x] **M6.5** BUG-4: Training Speed (FAST/NORMAL/QUALITY) selector,
      real GPU display, VRAM validation popup.
      (`server/routes/host.py`, apiClient, TrainingConfigView.vue)
- [ ] **Moved to M7** Output enhancer (native PyTorch vocoder NSF-HiFiGAN /
      shallow-diffusion) — deferred to M7 experimental milestone.

## Milestone M7 - Experimental sound design (Musique Concrète)

- [x] **M7.0** Output enhancer: pre-trained Vocos/BigVGAN post-processor with UI toggle.
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
