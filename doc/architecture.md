---
type: architecture
status: draft
generated:
  by: setup
  at: 2026-08-30
description: System architecture of the wogd-ddsp-trainer web UI DDSP training app
stale_after: 2026-12-31
---

# wogd-ddsp-trainer - Architecture

_Manually maintained architecture knowledge. Structural detail is auto-generated
in [`code_wiki.md`](./code_wiki.md) (MCP-only). See
[`index.md`](./index.md) for the knowledge catalog and
[`log.md`](./log.md) for the chronological changelog._

## Overview

`wogd-ddsp-trainer` is a **web UI training application for DDSP-based speech
synthesis models**. It exposes a browser UI to prepare datasets, configure and
run DDSP training, monitor progress, and synthesize/inference vocal output.

Building blocks (planned directory layout):

- `dataset/` - dataset prep: audio ingestion, normalization, feature extraction
  (loudness, F0, harmonic/aperiodic), train/validation split.
- `model/` - DDSP model definition (e.g. harmonic + filtered-noise oscillator
  decoder, F0/loudness conditioning, encoder if any).
- `train/` - training loop: PyTorch `LightningModule`/`Trainer` or plain loop,
  checkpoints, logging/metrics, early stopping, resume.
- `inference/` - synthesis: load a checkpoint, condition on target
  loudness/F0, render vocal audio, save/stream result.
- `server/` - web backend (FastAPI/Flask) exposing the dataset/model/training/
  inference services over HTTP/WebSocket.
- `webui/` - browser front-end (Vue/React + Vite) for dataset management,
  training configuration, live dashboards, and synthesis triggers.
- `tests/` - pytest for backend/training, Vitest for the web UI.

## Tech stack (proposed)

- Python 3 runtime; PyTorch for DDSP model + training.
- torchaudio / librosa / pydub for audio I/O and DSP features.
- FastAPI + uvicorn for the web backend; WebSocket for training-status streaming.
- Vue 3 + Vite (+ Pinia) or React for the web UI.
- SQLite / filesystem for dataset + run metadata.

## Training pipeline

1. **Dataset prep:** ingest source audio -> 16 kHz mono -> per-frame features
   (F0 from CREPE/pyin, harmonic amplitude from STFT, aperiodicity, loudness).
2. **Batching:** chunk into fixed-length frames + features; normalization.
3. **Model forward:** (optional encoder) -> oscillator + filtered-noise decoder
   -> reconstructed audio; loss = spectral + multiscale STFT + F0/loudness MSE.
4. **Optimization:** Adam/AdamW, LR schedule, checkpointing each epoch, best
   checkpoint on validation loss.
5. **Inference:** condition the decoder on target features (from reference
   audio or a UI sketch) -> render synthesis -> stream/play/download.

## Conventions

- English for all agent-facing docs and code identifiers.
- Match existing style; `ruff` for lint/format, `pytest` for tests.
- No comments unless they clarify non-obvious logic.

## Status

Scaffold phase. The codebase is empty; the above is the intended structure and
will be validated/updated as modules land.
