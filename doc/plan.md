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
- **M3 - Model + training loop:** self-owned DDSP decoder + losses (PyTorch),
  GPU auto-detection + optimal parameter suggestions, training loop with
  checkpoints/metrics, resume, offline + realtime model export + tests. Note:
  raw DDSP output is limited; a post-hoc output enhancer is scoped in M6 (see
  [`related-work.md`](./related-work.md)).
- **M4 - Web backend:** FastAPI + Celery/Redis services for
  dataset/model/training/inference, REST run management, TensorBoard
  provisioning, **preset management (FAST/NORMAL/QUALITY + custom presets,
  GPU-constraint clamping)**, + tests.
- **M5 - Web UI:** dataset manager, training config (GPU-parameter
  suggestions), TensorBoard-based dashboard, model registry,
  inference/synthesis player.
- **M6 - Polish:** packaging (non-Docker), docs, performance, error handling.
- **M7 - Experimental sound design (Musique Concrète):** F0/pitch-curve override
  editor (per-file + global dataset rules), DDSP component mixer (harmonics vs.
  noise), reverb IR injection + freeze (de-reverberation + inverse acoustic
  compensation). Creative/experimental; rationale in
  [`experimental-ddsp.md`](./experimental-ddsp.md).
- **M8 - Experimental synthesis hacks:** first-class hacks on our own DDSP core
  (inharmonic multipliers, wavetable exchange, frequency-band blindness, LFO
  injection). Experimental; rationale in
  [`experimental-sdk-hacking.md`](./experimental-sdk-hacking.md).

## Resolved questions

- **DDSP implementation:** self-owned PyTorch DDSP core (harmonic + filtered
  noise + reverb synth), specified by the DDSP paper (Engel et al. 2020).
  Reference implementations: `acids-ircam/ddsp_pytorch` (Apache-2.0) and
  `magenta/ddsp` (`core.py` / `synths.py`). Owning the core makes the M7/M8
  experimental hacks first-class instead of forking an external SDK.
- **F0/feature extraction:** `f0_hz` + `f0_confidence` (via RMVPE, or
  CREPE-PyTorch / parselmouth) + `loudness_db` (librosa). There are no
  precomputed "harmonic amplitude"/"aperiodicity" features - those are decoder
  outputs. Everything must run on GPU.
- **GPU availability / training budget:** local runtime - the app detects and
  analyzes the available GPU and proposes optimal training parameters.
- **VRAM budget / RTX 3060 6GB:** training MUST fit on 6 GB. Feasibility
  analysis in [`architecture.md`](./architecture.md) (VRAM budget section):
  budget is ~1.3–2.2 GB with batch_size=1, mixed precision, offline feature
  extraction, 3-scale STFT loss and hidden_size ≤ 512. These techniques are
  built into the core training loop from M1/M3 onward.
- **Real-time vs. offline synthesis:** both - offline batch training and
  rendering plus low-latency realtime model export.
- **Web audio streaming / latency:** TensorBoard doctrine - the UI is a control
  panel only; monitoring is served by TensorBoard (embedded via iframe,
  fallback new-tab link). No custom live charts, no WebSocket loss/audio
  streaming.

## Decisions recorded

- Agent-facing docs and identifiers in English.
- Python + FastAPI + Vue (matches ecosystem conventions). Frontend confirmed:
  **Vue 3 + Vite + Pinia** (not React).
- **PyTorch is the framework:** `torch` + `torchaudio` for the model/training
  stack; the DDSP core is self-owned. `magenta/ddsp` (TF) is only a spec
  reference, not a dependency (it is legacy/unmaintained; see
  [`related-work.md`](./related-work.md)).
- **Export formats:** Neutone (TorchScript) for DAW plugins, ONNX for
  cross-platform/web (`onnxruntime-web`), TorchScript for realtime. TF.js /
  TFLite / SavedModel are dropped. The Neutone SDK is PyTorch/TorchScript-only,
  a key reason for the framework choice.
- **TensorBoard doctrine:** the UI is a control panel (upload, config, job
  control via REST). Training monitoring is served by TensorBoard (iframe
  embed, fallback new-tab link); no custom live charts, no WebSocket/SSE loss
  or audio streaming.
- **GPU:** local; the app detects/analyzes the GPU and proposes optimal
  training parameters.
- **Real-time + offline:** both model kinds are supported (offline rendering +
  low-latency realtime export).
- **Open-source licensing:** only OSI-approved OSS dependencies; nothing that
  requires paid licenses or blocks public release. The project is licensed
  under Apache-2.0.
- **Dependency sourcing:** clone required libraries from
  `C:\Users\marku\Documents\GitHub\thirdParty` when present there; prefer the
  project venv, reuse global libraries via workspace config only when
  sufficient; avoid redundancy.
- **No Docker:** M6 packaging is non-Docker (local/wheel-based distribution).
- **Mandatory VSCode task set from the start:** `build-debug`, `build-release`,
  `e2e-test`, `start-application-debug`, `start-application-release`. They are
  created as soon as the build artifacts/process exist (M1).
- **Output quality:** raw DDSP synthesis is not studio-grade; a post-hoc
  output enhancer (vocoder / shallow diffusion) lifts it, informed by DDSP-SVC
  (see [`related-work.md`](./related-work.md)). With PyTorch, native vocoders
  (NSF-HiFiGAN) / shallow diffusion can be used directly.
