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
  injection, FM synthesis, phase distortion, trainable wavetable, angular
  cumsum). Experimental; rationale in
  [`experimental-sdk-hacking.md`](./experimental-sdk-hacking.md).
- **M9 - Alternative synthesizer engines:** `SinusoidalSynth` (freely learned
  partial frequencies, inharmonic instruments), `CombSubSynth` (comb-filter
  subtractive, vocal formants, DDSP-SVC style), colored noise (pink/brown),
  granular noise. Engine selected via `DDSPVariant.engine` feature flag.
  Details: [`implementation/m9-alternative-synth-engines.md`](./implementation/m9-alternative-synth-engines.md).
- **M10 - Neural Waveshaping Unit (NEWT):** replace harmonic branch with a
  lightweight MLP (periodic sin activations) that learns a nonlinear transfer
  function in the waveform domain. ~260k params, real-time on CPU. Based on
  Hayes et al. ISMIR 2021.
  Details: [`implementation/m10-newt.md`](./implementation/m10-newt.md).
- **M11 - Latent Space & Morphing:** VAE encoder → explicit latent `z`;
  checkpoint morphing (interpolate two trained models), random sampling,
  per-dimension latent steering UI. β-VAE training with KL warmup.
  Details: [`implementation/m11-latent-space.md`](./implementation/m11-latent-space.md).
- **M12 - PolyDDSP (Polyphony):** N parallel DDSP voices driven by a
  multi-pitch tracker (basic-pitch / torchcrepe top-K). Shared decoder
  weights by default; N=2–3 on RTX 3060 6 GB.
  Details: [`implementation/m12-polyddsp.md`](./implementation/m12-polyddsp.md).
- **M13 - Voice Conversion (HuBERT/ContentVec):** replace f0+loudness
  autoencoder conditioning with a frozen pretrained semantic content encoder
  (HuBERT-Soft MIT / ContentVec MIT). Enables source-to-target voice
  conversion (DDSP-SVC style, our own PyTorch core). Offline content
  extraction cached as `.npy`.
  Details: [`implementation/m13-voice-conversion.md`](./implementation/m13-voice-conversion.md).

- **M14 - Dual-Mode Training UI + Backend Tier System:** progressive complexity
  system for the training UI spanning both frontend and backend.
  **Backend-first (Phase 1):** DB schema migration (`model_tier` column on
  `presets` + `runs`), `train/gpu.py:estimate_model_vram()`, new
  `VARIANT_KEYS`/`ENGINE_KEYS`/`ADVANCED_KEYS` in `server/presets.py`,
  tier-aware `build_training()` in `server/tasks.py`, new REST endpoint
  `GET /api/gpu/feasibility`, extended `/validate` response
  (`model_tier_mismatch`), checkpoint-tier guard on `/resume`.
  **Frontend (Phase 2):** Pinia `modelConfig` store, `WizardModal.vue`
  (3-step: Tier → Quality/Preset → Target Mode), `ModelTierCard.vue`,
  `GpuFeasibilityBanner.vue`, tab-based `TrainingConfigView` with five
  `Tab*.vue` panels unlocked progressively by tier, `PresetManagerView`
  `model_tier` filter. **No breaking changes:** all new fields default to
  `'standard'`; existing runs/presets/checkpoints unaffected.
  Details: [`implementation/m14-dual-mode-ui.md`](./implementation/m14-dual-mode-ui.md).
  Full spec: [`ui-requirements.md`](./ui-requirements.md#dual-mode-training-ui-m14),
  [`architecture.md`](./architecture.md#model-tier-system--dual-mode-ui-m14).

- **M15 - Parameter Manifest Backend:** introduces `ParamManifest` — the
  serializable description of a checkpoint's ≤16 inference runtime parameters
  (VST knobs). `InferenceParam` + `ParamManifest` dataclasses, tier-default
  builders (`build_default_manifest`), checkpoint embedding under
  `state["param_manifest"]`, REST endpoints `GET/PUT /api/models/{run}/{ckpt}/params`,
  dynamic Neutone wrapper (names + defaults from manifest), new
  `CustomVSTWrapper` TorchScript module + `POST …/export/custom-vst` endpoint,
  extended `POST /api/inference/synthesize` for N params. No breaking changes;
  old checkpoints without manifest key generate defaults transparently.
  Details: [`implementation/m15-param-manifest.md`](./implementation/m15-param-manifest.md).
  Full spec: [`parameter-handling.md`](./parameter-handling.md).

- **M16 - Parameter Builder UI:** frontend for M15's manifest infrastructure.
  `ModelParameterBuilder.vue` (Neutone 4-slot panel + Custom VST ≤16 section,
  tier-aware), `ParamCard.vue` (inline editable parameter card),
  `NeutoneSlotPanel.vue` (HTML5 drag-and-drop Neutone slot assignment).
  Updated `ModelExportView.vue` (dual export buttons: Neutone FX + Custom VST),
  `InferencePlaygroundView.vue` (dynamic N-param sliders from manifest, grouped
  by tag, fallback to 2-slider for old checkpoints). Optional M16.8: VAE Latent
  Dimension Labelling mini-modal. Full mock-data seam + Vitest coverage.
  Prerequisite: M15 complete.
  Details: [`implementation/m16-param-builder-ui.md`](./implementation/m16-param-builder-ui.md).
  Full spec: [`parameter-handling.md`](./parameter-handling.md),
  [`ui-requirements.md`](./ui-requirements.md) §ModelParameterBuilder.

- **M17 - MIDI Synth VST Export:** export trained DDSP models as MIDI synthesizer
  VSTs (alongside the existing Audio FX VST path). Training is **unchanged** —
  a new `MidiSynthWrapper` (TorchScript) replaces the realtime F0-extractor with
  a MIDI-note-to-f0 frame generator. Supported for all tiers; most compelling for
  `hacks` (FM/wavetable/PD synths), `engine` (sinusoidal/combsub/NEWT), and
  `advanced/VAE` (timbre-morphing synth) / `advanced/Poly` (polyphonic MIDI chords).
  `advanced/VC` in hybrid mode (MIDI pitch + reference audio timbre).
  New components: `model/midi_utils.py`, `inference/midi_synth_wrapper.py`,
  `POST .../export/midi-synth` endpoint, Usage Mode wizard step, MIDI Preview in
  the Playground, tier-specific synth hints in tabs.
  Details: [`implementation/m17-midi-synth-vst.md`](./implementation/m17-midi-synth-vst.md).

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
- **Dual-Mode Training UI (M14, 2026-09-01):** two parallel interaction modes
  for the training config — Wizard Modal (simple users, 3-step guided flow)
  and Power-User Tab view (5 tabs unlocked by model tier). Model tier is the
  primary UI axis: `standard → component → hacks → engine → advanced`.
  Backend is extended backend-first: DB migration, `estimate_model_vram()`,
  tier-aware `build_training()`, `GET /api/gpu/feasibility`. No breaking
  changes; all new fields default to `'standard'`.
  (see [`related-work.md`](./related-work.md)). With PyTorch, native vocoders
  (NSF-HiFiGAN) / shallow diffusion can be used directly.
