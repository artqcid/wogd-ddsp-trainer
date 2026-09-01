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
- [x] **M7.1** F0/pitch-curve override editor: per-file canvas inspector +
      global dataset transformation rules (quantize, chaos/noise injection,
      pitch inversion).
- [x] **M7.2** DDSP component mixer: harmonics-vs-noise balance sliders.
- [x] **M7.3** Reverb IR injection + freeze (de-reverberation + inverse
      acoustic compensation) + IR extractor (export learned IR as `.wav`).
- [x] **M7.4** Experimental sound-design tests + docs.

## Milestone M9 - Alternative synthesizer engines

- [ ] **M9.1** Extend `DDSPVariant`: `engine`, `noise_color`, `noise_grain_jitter` fields.
- [ ] **M9.2** `SinusoidalSynth` — freely learned partial frequencies
      (`model/ddsp/sinusoidal.py`).
- [ ] **M9.3** `CombSubSynth` — comb-filter subtractive synth, vocal formants
      (`model/ddsp/combsub.py`).
- [ ] **M9.4** Colored noise source — pink/brown noise via FFT shaping
      (`model/ddsp/noise_colored.py`).
- [ ] **M9.5** Granular noise — per-frame grain jitter on noise buffer
      (`model/ddsp/synths.py`).
- [ ] **M9.6** Engine dispatch in `DDSPModel` + checkpoint tag + decoder head
      variants.
- [ ] **M9.7** UI: engine selector dropdown + noise controls in `SynthHacksView.vue`.
- [ ] **M9.8** `tests/test_synths_engines.py` — 12 pytest + 1 vitest.
- [ ] **M9.9** Docs: `experimental-sdk-hacking.md` engine section.

## Milestone M10 - Neural Waveshaping Unit (NEWT)

- [ ] **M10.1** `SawtoothExciter` — deterministic, no parameters
      (`model/ddsp/newt.py`).
- [ ] **M10.2** `NEWTUnit` — MLP with sin activations + NEWT weight init
      (`model/ddsp/newt.py`).
- [ ] **M10.3** Extend `DDSPVariant.engine` with `"newt"` + tuning params.
- [ ] **M10.4** Engine dispatch for NEWT in `DDSPModel` + gain/bias heads +
      checkpoint tag.
- [ ] **M10.5** UI: NEWT option in engine dropdown + hidden/layer controls.
- [ ] **M10.6** `tests/test_newt.py` — 10 pytest + 1 vitest.
- [ ] **M10.7** Docs: `experimental-sdk-hacking.md` NEWT section.

## Milestone M11 - Latent Space & Morphing

- [ ] **M11.1** `GRUEncoder` → (μ, σ) latent distribution
      (`model/encoder.py`).
- [ ] **M11.2** VAE mode in `DDSPModel`: reparameterisation, z concat,
      `DDSPConfig.use_latent`, checkpoint tag.
- [ ] **M11.3** β-VAE loss term + KL warmup schedule in `Trainer` +
      `TrainingConfig.kl_beta`.
- [ ] **M11.4** Server wiring: `use_latent`, `latent_dim`, `kl_beta` in run
      config + `PARAM_KEYS`.
- [ ] **M11.5** Morphing endpoint `POST /api/inference/morph`.
- [ ] **M11.6** `MorphingView.vue` — model A/B selector, alpha slider, render.
- [ ] **M11.7** `LatentExploreView.vue` — per-dimension sliders + scatter
      (optional PCA scatter).
- [ ] **M11.8** `tests/test_latent.py` — 10 pytest + 1 vitest.
- [ ] **M11.9** Docs: `experimental-ddsp.md` latent space section.

## Milestone M12 - PolyDDSP (Polyphony)

- [ ] **M12.1** Multi-pitch tracker wrapper + dependency check
      (`dataset/multi_pitch.py`).
- [ ] **M12.2** Dataset pipeline: `f0_hz_voices.npy` + `DDSPDataset` yields
      N f0 tracks.
- [ ] **M12.3** `PolyDDSPModel` — N shared-weight voices, sum output
      (`model/polyddsp_model.py`).
- [ ] **M12.4** Server wiring: `n_voices` in config + VRAM clamp (max 4) +
      `PARAM_KEYS`.
- [ ] **M12.5** UI: `n_voices` input in `TrainingConfigView.vue` + multi-F0
      display in `PreprocessingView.vue`.
- [ ] **M12.6** `tests/test_polyddsp.py` — 9 pytest.
- [ ] **M12.7** Docs: `ddsp-concepts.md` polyphony section.

## Milestone M13 - Voice Conversion (HuBERT/ContentVec)

- [ ] **M13.1** `ContentEncoderWrapper` — frozen HuBERT-Soft / ContentVec
      (`model/content_encoder.py`).
- [ ] **M13.2** Offline content extraction: `extract_content_embedding()` in
      `dataset/features.py`; `DDSPDataset` loads `content_embedding.npy`.
- [ ] **M13.3** Content conditioning in `DDSPModel`: `content_proj` linear +
      concat to GRU input; `DDSPConfig.use_content_encoder`.
- [ ] **M13.4** Server wiring: `use_content_encoder`, `content_encoder_name`
      in run config + `PARAM_KEYS`.
- [ ] **M13.5** VC inference endpoint `POST /api/inference/voice-convert` +
      dataset content-extraction trigger.
- [ ] **M13.6** `VoiceConversionView.vue` — source upload, pitch/loudness
      shift, A/B player.
- [ ] **M13.7** `tests/test_content_encoder.py` + `tests/test_vc_pipeline.py`
      — 10 pytest + 1 vitest.
- [ ] **M13.8** Docs: `related-work.md` M13 section.

## Milestone M14 - Dual-Mode Training UI + Backend Tier System

_Full spec: `ui-requirements.md` §"Dual-Mode Training UI", `architecture.md`
§"Model Tier system & Dual-Mode UI". No breaking changes; all new fields
default to `'standard'`._

### Phase 1 — Backend (must be complete before any Phase 2 frontend work)

- [ ] **M14.1.1** `train/gpu.py` — add `VRAMEstimate` dataclass +
      `estimate_model_vram(model_tier, n_voices, use_latent, use_content_encoder)`
      function using baseline figures from `architecture.md` VRAM budget table.
- [ ] **M14.1.2** `server/db.py` — `init_db()`: add `model_tier TEXT NOT NULL
      DEFAULT 'standard'` column to `presets` and `runs` `CREATE TABLE`
      statements. Add migration path via `meta` table `schema_version` key:
      run `ALTER TABLE … ADD COLUMN` if column absent on existing DBs.
- [ ] **M14.1.3** `server/presets.py` — add `VARIANT_KEYS`, `ENGINE_KEYS`,
      `ADVANCED_KEYS` constant tuples (not VRAM-bounded; validated not clamped).
      Extend `build_builtin_presets(bounds, tier='standard')` with tier param.
      Change `seed_builtin_presets()` lookup to `(name, model_tier)` composite.
- [ ] **M14.1.4** `server/routes/training.py` — add `model_tier: str = 'standard'`
      to `RunCreateRequest` + `ValidateRequest`. Extend `/validate` response
      with `model_tier_mismatch: bool`. Add checkpoint-tier guard in
      `POST /api/runs/{id}/resume` (409 on mismatch).
- [ ] **M14.1.5** `server/tasks.py` — make `build_training()` tier-aware:
      read `model_tier` from `model_config`; gate DDSPVariant, engine, and
      advanced fields behind their tier; all new fields use safe defaults.
- [ ] **M14.1.6** `server/routes/host.py` (or new `server/routes/gpu.py`) —
      implement `GET /api/gpu/feasibility` endpoint with `tier_feasibility`
      dict in response (all five tiers with fits/estimated_gb/warning).
- [ ] **M14.1.7** `tests/test_gpu_feasibility.py` — pytest: `estimate_model_vram`
      unit tests (all tier × n_voices × flag combos); endpoint integration test
      (mock GPU, verify tier_feasibility structure + fits logic).
- [ ] **M14.1.8** `tests/test_presets_tier.py` — pytest: `build_builtin_presets`
      with tier param; `seed_builtin_presets` composite-key collision; `clamp_params`
      still works for all tiers.
- [ ] **M14.1.9** `tests/test_training_tier.py` — pytest: `build_training`
      with each tier; validate that non-standard fields are absent/defaulted
      for `'standard'`; validate tier-mismatch 409 on resume.

### Phase 0 — Design System (prerequisite for Phase 2; no backend required)

- [ ] **M14.2.0** Design System upgrade — modern AI-dashboard visual language.
      Spec: `implementation/m14-dual-mode-ui.md` §"Phase 0". Six sub-steps:
      - **A** `webui/index.html` — Inter + JetBrains Mono `<link>` tags,
        update `<title>`.
      - **B** `webui/src/style.css` (NEW) — full global design token file:
        `--bg-*`, `--text-*`, `--accent` (Indigo #6366F1) + `--accent-2`
        (Cyan #06B6D4), semantic colors, borders, shadows (`--shadow-glow`),
        radii (`--radius-lg: 16px`), spacing scale, font stacks
        (`'Inter'`/`'JetBrains Mono'`), transition vars, z-index layers,
        sidebar/topbar size vars. Global reset + base. Utility classes: `.card`,
        `.card-header`, `.card-icon`, `.btn-primary` (gradient + glow),
        `.btn-secondary`, `.btn-ghost`, `.btn-cyan`, `.btn-sm`/`.btn-lg`,
        `.badge` + semantic variants (`badge-success`, `badge-warning`,
        `badge-error`, `badge-accent`, `badge-cyan`, `badge-muted`,
        `badge-dot`), `.form-group`, all form element styles (input/select/
        range/checkbox/radio), `.tab-bar`/`.tab-btn`/`.tab-btn--active`/
        `.tab-btn--disabled`, `.modal-overlay`/`.modal-box`/`.modal-header`/
        `.modal-body`/`.modal-footer`, `.gradient-text`, `.glow-accent`,
        `.glow-cyan`, grid + flex utilities.
      - **C** `webui/src/main.js` — `import './style.css'` as first import.
      - **D** `webui/src/App.vue` — remove scoped `:root` block; update shell
        layout vars to use `--sidebar-width`, `--topbar-height`, `--bg-base`,
        `--bg-primary`, `--font-sans`.
      - **E** `webui/src/components/Sidebar.vue` — gradient SVG waveform brand
        mark, `.gradient-text` app name, group icons (emoji prefix), thin
        `.sidebar-divider` between groups, `router-link-active` state with
        `--accent-subtle` bg + `--accent` left border + inward glow shadow,
        footer Settings link.
      - **F** `webui/src/components/TopBar.vue` — pill `.badge` status
        indicators (replaces colored dots), breadcrumb section label (derived
        from route path), GPU chip badge (name + VRAM) when GPU detected,
        version in mono font. Script: computed `currentSection` map,
        `gpuChip` computed from `apiClient.getHostInfo()`.
      Verify: `vitest` all green after M14.2.0 (CSS-only; no `data-testid`
      selectors changed).

### Phase 2 — Frontend (requires Phase 0 + Phase 1 complete)

- [ ] **M14.2.1** `webui/src/stores/modelConfig.js` — Pinia store:
      `activeTier`, `wizardCompleted`, `gpuFeasibility`, `selectedPreset`,
      `targetMode`, `coreParams`, `componentParams`, `hacksVariant`,
      `engineParams`, `advancedParams`. Actions: `setTierFromWizard`,
      `checkFeasibility` (calls `/api/gpu/feasibility`), `resetToWizard`.
- [ ] **M14.2.2** `webui/src/mocks/fixtures.js` + `mockApiClient.js` — add
      `tier_feasibility` fixture with all five tiers; add `model_tier` field
      to preset fixtures (default `'standard'`). Mock `getGpuFeasibility()`.
- [ ] **M14.2.3** `webui/src/components/ModelTierCard.vue` — single tier card:
      icon, name, short description, GPU feasibility badge (✓/⚠), tooltip.
      Renders from fixture data; no backend required.
- [ ] **M14.2.4** `webui/src/components/GpuFeasibilityBanner.vue` — persistent
      banner: GPU name/VRAM/tier, current-config estimate, reactive on store
      changes. Three render states: fits / warning / no-GPU (all covered by
      Vitest).
- [ ] **M14.2.5** `webui/src/components/WizardModal.vue` — 3-step modal:
      Step 1 = tier card grid (uses `ModelTierCard`); Step 2 = quality/preset
      cards (FAST/NORMAL/QUALITY + custom); Step 3 = target mode selector.
      "Skip" link always visible. On complete: calls `setTierFromWizard`.
      Opens when `!wizardCompleted`; reopenable via "⚙ Reconfigure Model" button.
- [ ] **M14.2.6** Tab components — five new files:
      `TabCore.vue` (preset, ML params, target mode, decoder, reverb),
      `TabComponent.vue` (n_harmonics, n_filter_banks, link to ComponentMixerView),
      `TabHacks.vue` (DDSPVariant flags, link to SynthHacksView),
      `TabEngine.vue` (engine dropdown + engine-specific params),
      `TabAdvanced.vue` (use_latent, latent_dim, kl_beta, n_voices,
      use_content_encoder, content_encoder_name).
- [ ] **M14.2.7** `webui/src/views/TrainingConfigView.vue` — refactor into
      tab-wrapper: import `GpuFeasibilityBanner`, tab bar (5 tabs, disabled
      when tier < required), `WizardModal` (shown when `!wizardCompleted`),
      delegate param sections to Tab components. "⚙ Reconfigure Model" button
      in header calls `resetToWizard()`.
- [ ] **M14.2.8** `webui/src/views/PresetManagerView.vue` — add `model_tier`
      filter (dropdown above preset list); filter calls
      `GET /api/presets?model_tier=…`.
- [ ] **M14.2.9** Vitest: `WizardModal` (all 3 steps complete + skip path),
      `GpuFeasibilityBanner` (3 states), `ModelTierCard` (fits/warn/no-gpu),
      all 5 Tab components (render with mock data), `TrainingConfigView`
      tab-switching + disabled-tab tooltip, `PresetManagerView` tier filter.
      All with `MockApiClient` + fixtures; no backend required.
- [ ] **M8.1.1** `DDSPVariant` dataclass (`model/ddsp/variant.py` — new).
- [ ] **M8.1.2** Thread `DDSPVariant` into `DDSPModel` + `DDSPCore` + `HarmonicOscillatorSynth`.
- [ ] **M8.1.3** Server-layer variant parsing (`server/tasks.py`, `server/presets.py`,
      `model/ddsp_model.py` `DDSPConfig` field).
- [ ] **M8.1.4** UI: `SynthHacksView.vue` + router route + sidebar link + mock fixtures.

### M8.2 — Inharmonic Multipliers + FM Synthesis
- [ ] **M8.2.1** Configurable `harmonic_ratios` in `HarmonicOscillatorSynth`
      (`synths.py:65`). Bell / gong / gamelan textures.
- [ ] **M8.2b** FM synthesis: `harmonic_freqs += fm_depth * sin(fm_ratio * f0 * t)`
      (`synths.py:66–72`).

### M8.3 — Waveform / Wavetable Exchange
- [ ] **M8.3.1** `_apply_waveform()` helper + dispatch `sin / square / saw`
      (`synths.py:99`). Includes M8.3b phase distortion (`pd_k`).
- [ ] **M8.3c** Trainable wavetable: `nn.Parameter(256)` initialized to sine;
      checkpoint tag `variant_flags`.

### M8.4 — Loss & Decoder Hacks
- [ ] **M8.4.1** Frequency-band mask on `MultiScaleSpectralLoss`
      (`losses.py` + `tasks.py`).
- [ ] **M8.4.2** LFO injection into noise magnitudes (`ddsp_model.py:forward`).

### M8.6 — Quality: Angular Cumulative Sum
- [ ] **M8.6** `_angular_cumsum()` + `use_angular_cumsum` flag (`synths.py:77`).
      Fixes phase drift for synthesis > 6 s.

### M8.5 — Tests + Docs
- [ ] **M8.5.1** `tests/test_synths_variant.py` — 15 pytest + 1 vitest smoke tests.
- [ ] **M8.5.2** Finalize `doc/experimental-sdk-hacking.md` (result table,
      checkpoint compat matrix, gradient behaviour note).
