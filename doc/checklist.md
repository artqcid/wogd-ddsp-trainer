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
      ⚠ _ARCHITECT audit 2026-09-03: M4.2 code exists but training is **non-functional**
      without Redis (BUG-50, critical-open). `LocalTaskRunner` fallback required before
      training works for end-users. M4.2 = "code scaffolded", NOT "end-to-end functional"._
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

- [x] **M9.1** Extend `DDSPVariant`: `engine`, `noise_color`, `noise_grain_jitter` fields.
- [x] **M9.2** `SinusoidalSynth` — freely learned partial frequencies
       (`model/ddsp/sinusoidal.py`).
- [x] **M9.3** `CombSubSynth` — comb-filter subtractive synth, vocal formants
       (`model/ddsp/combsub.py`).
- [x] **M9.4** Colored noise source — pink/brown noise via FFT shaping
       (`model/ddsp/noise_colored.py`).
- [x] **M9.5** Granular noise — per-frame grain jitter on noise buffer
       (`model/ddsp/synths.py`).
- [x] **M9.6** Engine dispatch in `DDSPModel` + checkpoint tag + decoder head
       variants.
- [x] **M9.7** UI: engine selector dropdown + noise controls in `SynthHacksView.vue`.
- [x] **M9.8** `tests/test_synths_engines.py` — 12 pytest.
- [x] **M9.9** Docs: `experimental-sdk-hacking.md` engine section.

### M9 post-release correctness fixes (required before M9 is closed)

- [x] **M9.10** FIX BUG-7: `DDSPModel.load_checkpoint` — add
       `torch.serialization.safe_globals([DDSPConfig])` context manager;
       remove manual `add_safe_globals` workaround from two tests in
       `test_synths_engines.py`. (`model/ddsp_model.py`,
       `tests/test_synths_engines.py`)
- [x] **M9.11** FIX BUG-8: `DDSPCore.forward` sinusoidal path — replace
       `amplitudes`-as-fallback with a proper zero-tensor of shape
       `(B, T, n_noise_bins)` when `noise_magnitudes=None`.
       (`model/ddsp/synths.py`)
- [x] **M9.12** IMP-A: remove redundant `DDSPVariant` `TYPE_CHECKING` import
       in `model/ddsp_model.py` (imported twice: runtime + TYPE_CHECKING).
- [x] **M9.13** IMP-C: normalize `_pink_noise` / `_brown_noise` output to
       unit RMS (add `signal / rms.clamp(min=1e-8)` at end of each helper).
       (`model/ddsp/noise_colored.py`)
- [x] **M9.14** IMP-D: guard `DDSPCore` reverb instantiation — only create
       `self.reverb` for engines that actually use it (`"harmonic"`,
       `"sinusoidal"`); `"combsub"` gets `self.reverb = None`.
       (`model/ddsp/synths.py`)

## Milestone M10 - Neural Waveshaping Unit (NEWT)

- [x] **M10.1** `SawtoothExciter` — deterministic, no parameters
       (`model/ddsp/newt.py`).
- [x] **M10.2** `NEWTUnit` — MLP with sin activations + NEWT weight init
       (`model/ddsp/newt.py`).
- [x] **M10.3** Extend `DDSPVariant.engine` with `"newt"` + tuning params.
- [x] **M10.4** Engine dispatch for NEWT in `DDSPModel` + gain/bias heads +
       checkpoint tag.
- [x] **M10.5** UI: NEWT option in engine dropdown + hidden/layer controls.
- [x] **M10.6** `tests/test_newt.py` — 10 pytest + 1 vitest.
- [x] **M10.7** Docs: `experimental-sdk-hacking.md` NEWT section.

## Milestone M11 - Latent Space & Morphing

- [x] **M11.1** `GRUEncoder` → (μ, σ) latent distribution
       (`model/encoder.py`).
- [x] **M11.2** VAE mode in `DDSPModel`: reparameterisation, z concat,
       `DDSPConfig.use_latent`, checkpoint tag.
- [x] **M11.3** β-VAE loss term + KL warmup schedule in `Trainer` +
       `TrainingConfig.kl_beta`.
- [x] **M11.4** Server wiring: `use_latent`, `latent_dim`, `kl_beta` in run
       config + `PARAM_KEYS`.
- [x] **M11.5** Morphing endpoint `POST /api/inference/morph`.
- [x] **M11.6** `MorphingView.vue` — model A/B selector, alpha slider, render.
- [x] **M11.7** `LatentExploreView.vue` — per-dimension sliders + scatter
       (optional PCA scatter).
- [x] **M11.8** `tests/test_latent.py` — 10 pytest + 1 vitest.
- [x] **M11.9** Docs: `experimental-ddsp.md` latent space section.

## Milestone M12 - PolyDDSP (Polyphony)

- [x] **M12.1** Multi-pitch tracker wrapper + dependency check
       (`dataset/multi_pitch.py`).
- [x] **M12.2** Dataset pipeline: `f0_hz_voices.npy` + `DDSPDataset` yields
       N f0 tracks.
- [x] **M12.3** `PolyDDSPModel` — N shared-weight voices, sum output
       (`model/polyddsp_model.py`).
- [x] **M12.4** Server wiring: `n_voices` in config + VRAM clamp (max 4) +
       `PARAM_KEYS`.
- [x] **M12.5** UI: `n_voices` input in `TrainingConfigView.vue` + multi-F0
       display in `PreprocessingView.vue`.
- [x] **M12.6** `tests/test_polyddsp.py` — 9 pytest.
- [x] **M12.7** Docs: `ddsp-concepts.md` polyphony section.

## Milestone M13 - Voice Conversion (HuBERT/ContentVec)

- [x] **M13.1** `ContentEncoderWrapper` — frozen HuBERT-Soft / ContentVec
       (`model/content_encoder.py`).
- [x] **M13.2** Offline content extraction: `extract_content_embedding()` in
       `dataset/features.py`; `DDSPDataset` loads `content_embedding.npy`.
- [x] **M13.3** Content conditioning in `DDSPModel`: `content_proj` linear +
       concat to GRU input; `DDSPConfig.use_content_encoder`.
- [x] **M13.4** Server wiring: `use_content_encoder`, `content_encoder_name`
       in run config + `PARAM_KEYS`.
- [x] **M13.5** VC inference endpoint `POST /api/inference/voice-convert` +
       dataset content-extraction trigger.
- [x] **M13.6** `VoiceConversionView.vue` — source upload, pitch/loudness
       shift, A/B player.
- [x] **M13.7** `tests/test_content_encoder.py` + `tests/test_vc_pipeline.py`
       — 10 pytest + 1 vitest.
- [x] **M13.8** Docs: `related-work.md` M13 section.

## Milestone M15 - Parameter Manifest Backend

_Full spec: `parameter-handling.md`. Prerequisite: M3, M4, M6.
No breaking changes; all manifest keys default safely on old checkpoints._

- [x] **M15.1** `model/param_manifest.py` (NEW) — `InferenceParam` + `ParamManifest`
      dataclasses: `to_dict()`/`from_dict()`, `neutone_params`/`custom_vst_params`
      properties, `validate_manifest()`. Tests: `tests/test_param_manifest.py`
      (round-trip, filtering, validation errors).
- [x] **M15.2** `model/param_manifest.py` (extend M15.1) — tier-default builders:
      `_standard/component/hacks/engine/advanced_manifest()`, public
      `build_default_manifest(model_tier, variant_flags)`. Tests: all 7 tier
      variants produce correct Neutone/Custom param counts and names.
- [x] **M15.3** `train/trainer.py` — embed `param_manifest` in `save_checkpoint()`;
      expose `self.param_manifest` on load; backward-compat load for old checkpoints
      (generate defaults transparently). Tests: `tests/test_checkpoint_manifest.py`.
- [x] **M15.4** `server/routes/models.py` — `GET /api/models/{run_id}/{checkpoint}/params`:
      return manifest JSON (or tier-defaults if absent). 404 on missing checkpoint.
      Tests: `tests/test_model_params_endpoint.py`.
- [x] **M15.5** `server/routes/models.py` — `PUT /api/models/{run_id}/{checkpoint}/params`:
      validate + overwrite manifest in checkpoint state dict. 422 on validation
      errors. Tests: extend `tests/test_model_params_endpoint.py`.
- [x] **M15.6** `inference/export.py` — Neutone wrapper reads manifest dynamically:
      `neutone_params` → `get_neutone_parameters()`, assert ≤4; fallback for
      old checkpoints. Tests: `tests/test_export_neutone_manifest.py`.
- [x] **M15.7** `inference/export_custom_vst.py` (NEW) — `CustomVSTWrapper`
      (TorchScript-compatible, ≤16 params, `param_manifest_json` buffer) +
      `export_custom_vst()`; `POST …/export/custom-vst` endpoint.
      Tests: `tests/test_export_custom_vst.py`.
- [x] **M15.8** `server/routes/inference.py` — extend `POST /api/inference/synthesize`
      with optional `params` JSON dict; backward-compat (old 2-field calls still work).
      Tests: `tests/test_inference_n_params.py`.
- [x] **M15.9** Full suite: `ruff check`, `ruff format --check`, `pytest` all green.

## Milestone M16 - Parameter Builder UI

_Full spec: `parameter-handling.md`, `ui-requirements.md` §ModelParameterBuilder.
**Prerequisite: M15 complete.** All components render with MockApiClient + fixtures._

- [x] **M16.1** `webui/src/mocks/fixtures.js` + `mockApiClient.js` — add
      `PARAM_MANIFEST_FIXTURES` (standard/component/hacks_fm/engine_newt/advanced_vae),
      `getCheckpointParams()`, `updateCheckpointParams()` (stateful mock).
- [x] **M16.2** `webui/src/components/ParamCard.vue` (NEW) — single editable
      parameter card: name/description/type/min-max-default/mapping/unit/group fields,
      inline validation (name ≤30 chars, min < max), neutone-slot badge, readonly mode.
      Vitest: `tests/ParamCard.test.js`.
- [x] **M16.3** `webui/src/components/ModelParameterBuilder.vue` (NEW) — full builder:
      Neutone section (4 slots, readonly for standard), Custom VST section (hidden for
      standard, ≤16 params, + Add button), Save/Reset, Export buttons with validation gate.
      Vitest: `tests/ModelParameterBuilder.test.js` (all 5 tier variants).
- [x] **M16.4** `webui/src/components/NeutoneSlotPanel.vue` (NEW) — 4 knob slots with
      HTML5 drag-and-drop assignment from param pool; empty slot "drag here"; readonly mode.
      Vitest: `tests/NeutoneSlotPanel.test.js` (drag simulation).
- [x] **M16.5** `webui/src/views/ModelExportView.vue` — embed `ModelParameterBuilder`;
      add "Export → Custom VST (.pt)" button; both export buttons show progress +
      trigger file download on success. Vitest: extend `tests/views-batch2.test.js`.
- [x] **M16.6** `webui/src/views/InferencePlaygroundView.vue` — dynamic N-param sliders
      from manifest (grouped by group tag, collapse if >8); synthesize sends `params` JSON;
      "Reset to defaults" button; 2-slider fallback if no manifest.
      Vitest: extend `tests/views-batch2.test.js`.
- [x] **M16.7** Full suite: `vitest run`, `ruff check`, `pytest` all green.
- [ ] **M16.8** _(optional)_ VAE Latent Dimension Labelling mini-modal in `ParamCard.vue`:

## Milestone M18 - Frontend-Backend Integration (RestApiClient)

_Closes the mock-data seam. Prerequisite: M4, M5, M15._

- [x] **M18.1** Add missing backend routes: `DELETE /api/datasets/{id}`, `POST …/export/neutone`
      Files: `server/routes/dataset.py`, `server/routes/model.py`
- [x] **M18.2** Add missing method declarations to abstract `ApiClient` class:
      `getFirstAudioFile`, `preprocessDataset`, `exportModel`, `exportStatus`,
      `synthesizeMidi`, `getGpuFeasibility`.
      File: `webui/src/api/apiClient.js`
- [x] **M18.3** Create `RestApiClient.js` — full `fetch()`-based HTTP implementation
      of all ApiClient methods.
      File: `webui/src/api/restApiClient.js` (NEW)
- [x] **M18.4** Swap `MockApiClient` → `RestApiClient` in `main.js`.
      File: `webui/src/main.js`
- [x] **M18.5** Add CORS middleware (dev mode, behind env flag).
      File: `server/main.py`
- [x] **M18.6** Full verification: `vitest`, `pytest`, `ruff`, `npm run build`.
      "Label this dimension" button → 3-preview modal (min/mid/max synthesis) → name field.
      Only visible for `advanced/use_latent` tier params. Vitest: modal open/confirm/cancel.



_Full spec: `ui-requirements.md` §"Dual-Mode Training UI", `architecture.md`
§"Model Tier system & Dual-Mode UI". No breaking changes; all new fields
default to `'standard'`._

### Phase 1 — Backend (must be complete before any Phase 2 frontend work)

- [x] **M14.1.1** `train/gpu.py` — add `VRAMEstimate` dataclass +
      `estimate_model_vram(model_tier, n_voices, use_latent, use_content_encoder)`
      function using baseline figures from `architecture.md` VRAM budget table.
- [x] **M14.1.2** `server/db.py` — `init_db()`: add `model_tier TEXT NOT NULL
      DEFAULT 'standard'` column to `presets` and `runs` `CREATE TABLE`
      statements. Add migration path via `meta` table `schema_version` key:
      run `ALTER TABLE … ADD COLUMN` if column absent on existing DBs.
- [x] **M14.1.3** `server/presets.py` — add `VARIANT_KEYS`, `ENGINE_KEYS`,
      `ADVANCED_KEYS` constant tuples (not VRAM-bounded; validated not clamped).
      Extend `build_builtin_presets(bounds, tier='standard')` with tier param.
      Change `seed_builtin_presets()` lookup to `(name, model_tier)` composite.
- [x] **M14.1.4** `server/routes/training.py` — add `model_tier: str = 'standard'`
      to `RunCreateRequest` + `ValidateRequest`. Extend `/validate` response
      with `model_tier_mismatch: bool`. Add checkpoint-tier guard in
      `POST /api/runs/{id}/resume` (409 on mismatch).
- [x] **M14.1.5** `server/tasks.py` — make `build_training()` tier-aware:
      read `model_tier` from `model_config`; gate DDSPVariant, engine, and
      advanced fields behind their tier; all new fields use safe defaults.
- [x] **M14.1.6** `server/routes/host.py` (or new `server/routes/gpu.py`) —
      implement `GET /api/gpu/feasibility` endpoint with `tier_feasibility`
      dict in response (all five tiers with fits/estimated_gb/warning).
- [x] **M14.1.7** `tests/test_gpu_feasibility.py` — pytest: `estimate_model_vram`
      unit tests (all tier × n_voices × flag combos); endpoint integration test
      (mock GPU, verify tier_feasibility structure + fits logic).
- [x] **M14.1.8** `tests/test_presets_tier.py` — pytest: `build_builtin_presets`
      with tier param; `seed_builtin_presets` composite-key collision; `clamp_params`
      still works for all tiers.
- [x] **M14.1.9** `tests/test_training_tier.py` — pytest: `build_training`
      with each tier; validate that non-standard fields are absent/defaulted
      for `'standard'`; validate tier-mismatch 409 on resume.

### Phase 0 — Design System (prerequisite for Phase 2; no backend required)

- [x] **M14.2.0** Design System upgrade — modern AI-dashboard visual language
      with **per-tier signal colors** so the active model complexity is
      always visible across the entire UI.
      Spec: `implementation/m14-dual-mode-ui.md` §"Phase 0". Eight sub-steps:
      - **A** `webui/index.html` — Inter + JetBrains Mono `<link>` tags,
        update `<title>`.
      - **B** `webui/src/style.css` (NEW) — full global design token file:
        `--bg-*`, `--text-*`, `--accent` (Indigo #6366F1) + `--accent-2`
        (Cyan #06B6D4), semantic colors, borders, shadows, radii, spacing,
        fonts, transitions. **Tier identity tokens (per tier: base, -subtle,
        -glow):** `--tier-standard` (Emerald #10B981), `--tier-component`
        (Sky #06B6D4), `--tier-hacks` (Amber #F59E0B), `--tier-engine`
        (Violet #8B5CF6), `--tier-advanced` (Rose #F43F5E). Global reset +
        utility classes: `.card`, `.btn-*`, `.badge` + semantic variants,
        `.form-group`, `.tab-bar`/`.tab-btn`/`.tab-btn--active`/
        `.tab-btn--disabled`, modals, `.gradient-text`, `.glow-*`, grid/flex.
      - **C** `webui/src/main.js` — `import './style.css'` as first import.
      - **D** `webui/src/App.vue` — remove scoped `:root` block; use token vars.
      - **E** `webui/src/components/Sidebar.vue` — gradient SVG brand mark,
        emoji nav icons, active-link glow (`--accent` left border + inward
        shadow), sidebar-divider, footer Settings link. Sidebar uses global
        `--accent` (NOT tier color) for nav state — tier is a model-config
        concept, not a navigation concept.
      - **F** `webui/src/components/TopBar.vue` — **tier badge** (visible on
        ALL views; pill colored with active tier's signal color from
        `--tier-<name>`; `data-testid="tier-badge"`), pill `.badge` status
        indicators, breadcrumb section label, GPU chip badge, mono version.
        Imports `tierColor`/`tierLabel`/`tierIcon` from `tierColors.js`
        (step H) and `useModelConfigStore` from Pinia (step M14.2.1).
      - **G** Vitest verify: `vitest` all green after A–F.
      - **H** `webui/src/utils/tierColors.js` (NEW) — `TIER_META`, `TIER_ORDER`,
        `tierColor()`, `tierLabel()`, `tierIcon()`, `tierAtLeast()`.

### Phase 2 — Frontend (requires Phase 0 + Phase 1 complete)

- [x] **M14.2.1** `webui/src/stores/modelConfig.js` — Pinia store:
      `activeTier`, `wizardCompleted`, `gpuFeasibility`, `selectedPreset`,
      `targetMode`, `coreParams`, `componentParams`, `hacksVariant`,
      `engineParams`, `advancedParams`. Actions: `setTierFromWizard`,
      `checkFeasibility` (calls `/api/gpu/feasibility`), `resetToWizard`.
- [x] **M14.2.2** `webui/src/mocks/fixtures.js` + `mockApiClient.js` — add
      `tier_feasibility` fixture with all five tiers; add `model_tier` field
      to preset fixtures (default `'standard'`). Mock `getGpuFeasibility()`.
- [x] **M14.2.3** `webui/src/components/ModelTierCard.vue` — single tier card:
      icon, name, short description, GPU feasibility badge (✓/⚠), tooltip.
      Renders from fixture data; no backend required.
- [x] **M14.2.4** `webui/src/components/GpuFeasibilityBanner.vue` — persistent
      banner: GPU name/VRAM/tier, current-config estimate, reactive on store
      changes. Three render states: fits / warning / no-GPU (all covered by
      Vitest).
- [x] **M14.2.5** `webui/src/components/WizardModal.vue` — 3-step modal:
      Step 1 = tier card grid (uses `ModelTierCard`); Step 2 = quality/preset
      cards (FAST/NORMAL/QUALITY + custom); Step 3 = target mode selector.
      "Skip" link always visible. On complete: calls `setTierFromWizard`.
      Opens when `!wizardCompleted`; reopenable via "⚙ Reconfigure Model" button.
- [x] **M14.2.6** Tab components — five new files:
      `TabCore.vue` (preset, ML params, target mode, decoder, reverb),
      `TabComponent.vue` (n_harmonics, n_filter_banks, link to ComponentMixerView),
      `TabHacks.vue` (DDSPVariant flags, link to SynthHacksView),
      `TabEngine.vue` (engine dropdown + engine-specific params),
      `TabAdvanced.vue` (use_latent, latent_dim, kl_beta, n_voices,
      use_content_encoder, content_encoder_name).
- [x] **M14.2.7** `webui/src/views/TrainingConfigView.vue` — refactor into
      tab-wrapper: import `GpuFeasibilityBanner`, tab bar (5 tabs, disabled
      when tier < required), `WizardModal` (shown when `!wizardCompleted`),
      delegate param sections to Tab components. "⚙ Reconfigure Model" button
      in header calls `resetToWizard()`.
- [x] **M14.2.8** `webui/src/views/PresetManagerView.vue` — add `model_tier`
      filter (dropdown above preset list); filter calls
      `GET /api/presets?model_tier=…`.
- [x] **M14.2.9** Vitest: `WizardModal` (all 3 steps complete + skip path),
      `GpuFeasibilityBanner` (3 states), `ModelTierCard` (fits/warn/no-gpu),
      all 5 Tab components (render with mock data), `TrainingConfigView`
      tab-switching + disabled-tab tooltip, `PresetManagerView` tier filter.
      All with `MockApiClient` + fixtures; no backend required.
- [x] **M8.1.1** `DDSPVariant` dataclass (`model/ddsp/variant.py` — new).
- [x] **M8.1.2** Thread `DDSPVariant` into `DDSPModel` + `DDSPCore` + `FilteredNoiseSynth`.
- [x] **M8.1.3** Server-layer variant parsing (`server/tasks.py`, `server/presets.py`,
       `model/ddsp_model.py` `DDSPConfig` field).
- [x] **M8.1.4** UI: `SynthHacksView.vue` + router route + sidebar link + mock fixtures.

### M8.2 — Inharmonic Multipliers + FM Synthesis
- [x] **M8.2.1** Configurable `harmonic_ratios` in `HarmonicOscillatorSynth`
      (`synths.py:65`). Bell / gong / gamelan textures.
- [x] **M8.2b** FM synthesis: `harmonic_freqs += fm_depth * sin(fm_ratio * f0 * t)`
      (`synths.py:66–72`).

### M8.3 — Waveform / Wavetable Exchange
- [x] **M8.3.1** `_apply_waveform()` helper + dispatch `sin / square / saw`
      (`synths.py:99`). Includes M8.3b phase distortion (`pd_k`).
- [x] **M8.3c** Trainable wavetable: `nn.Parameter(256)` initialized to sine;
      checkpoint tag `variant_flags`.

### M8.4 — Loss & Decoder Hacks
- [x] **M8.4.1** Frequency-band mask on `MultiScaleSpectralLoss`
      (`losses.py` + `tasks.py`).
- [x] **M8.4.2** LFO injection into noise magnitudes (`ddsp_model.py:forward`).

### M8.6 — Quality: Angular Cumulative Sum
- [x] **M8.6** `_angular_cumsum()` + `use_angular_cumsum` flag (`synths.py:77`).
      Fixes phase drift for synthesis > 6 s.

### M8.5 — Tests + Docs
- [x] **M8.5.1** `tests/test_synths_variant.py` — 15 pytest + 1 vitest smoke tests.
- [x] **M8.5.2** Finalize `doc/experimental-sdk-hacking.md` (result table,
      checkpoint compat matrix, gradient behaviour note).

## Milestone M17 - MIDI Synth VST Export

- [x] **M17.1** `model/midi_utils.py` (NEW) — MIDI note→Hz, velocity→dB, frame generation, voice allocator.
- [x] **M17.2** `inference/midi_synth_wrapper.py` (NEW) — TorchScript-compatible MidiSynthWrapper.
- [x] **M17.3** `inference/export.py` extend — `export_midi_synth()` function.
- [x] **M17.4** REST endpoints: `POST …/export/midi-synth` + `POST …/synthesize-midi`.
- [x] **M17.5** `server/routes/training.py` — `synthesis_mode` field in `RunCreateRequest`.
- [x] **M17.6** `model/param_manifest.py` — `context` field, `_midi_synth_manifest()` builder.
- [x] **M17.7** pytest: `test_midi_utils.py` (26), `test_midi_synth_wrapper.py` (5), `test_export_midi_synth.py` (3).
- [x] **M17.8** `WizardModal.vue` — Usage Mode selector in Step 3.
- [x] **M17.9** `modelConfig.js` store — `synthesisMode` field + `setSynthesisMode` action.
- [x] **M17.10** `ModelExportView.vue` — MIDI Synth export button.
- [x] **M17.11** `TrainingConfigView.vue` — MIDI training hint banner.
- [x] **M17.12** `InferencePlaygroundView.vue` — MIDI Preview tab (virtual keyboard).
- [x] **M17.13** `TabHacks/TabEngine/TabAdvanced.vue` — tier-specific MIDI hints.
- [x] **M17.14** Vitest coverage — 77/77 all green.
- [x] Full suite: `ruff check`, `ruff format --check`, `pytest` (361/361), `vitest` (77/77) all green.

## Open bugs — milestone linkage

_Bugs are described in full **only** in [`bugs.md`](./bugs.md); this section is
the milestone/status view. Granular fix steps: Group A →
[`implementation/m19-bug-fixes.md`](./implementation/m19-bug-fixes.md);
Group B → [`implementation/m20-audio-quality-bugs.md`](./implementation/m20-audio-quality-bugs.md).
Binding UI spec for Group B: [`ui-requirements.md`](./ui-requirements.md)
§"Audio-quality & training-UX controls (BUG-59..67)"._

> **All 16 open bugs were re-verified against the code on 2026-09-03**
> (ARCHITECT_Openrouter). Several filed claims turned out to be stale or wrong;
> the corrections are recorded per bug in `bugs.md` and summarised in its
> §"Open-bug re-analysis". This section reflects the corrected state.

### Group A — SPA / training lifecycle (BUG-52..58, analysed 2026-09-03)

_All seven have full architectural resolution plans in `bugs.md`. Ready for
implementation. Execution order + granular steps in `m19-bug-fixes.md`._

- [ ] **BUG-53** _(critical, M5)_ — `router.push('/training-dashboard')` targets a
      non-existent route → full page reload. **Fix first: BUG-54 depends on it.**
- [ ] **BUG-54** _(major, M5)_ — Page reload resets Pinia store → wizard reopens.
      Two-layer fix: BUG-53 + sessionStorage backup in `modelConfig.js`.
- [ ] **BUG-52** _(major, M5)_ — Preprocessing diagnostics unreachable: wrong
      endpoint call (`/extract-content` → `/preprocess`) + route ordering in
      `dataset.py` (wildcard shadows `/diagnostics`).
- [ ] **BUG-55** _(major, M5)_ — Training button lifecycle: Start → Stop → Failed
      states driven by backend run status, not local `isSubmitting`.
- [ ] **BUG-56** _(major, M5)_ — Dashboard must survive tab switches:
      `hasLoaded` ref, `<KeepAlive>` + `onActivated()`, TensorBoard `iframeKey`.
- [ ] **BUG-58** _(major, M5)_ — Resume path missing in wizard; dashboard needs
      resume CTA when stopped/failed runs exist.
- [ ] **BUG-57** _(major, M4→M3)_ — Clean abort: explicit final checkpoint save when
      the stop event is set. **Single-file fix in `train/trainer.py`** — the
      "watcher spin" sub-fix was withdrawn on 2026-09-03 (verified non-bug:
      `server/tasks.py` already breaks out of the loop after `stop_event.set()`),
      and step M19.7b was removed.

_Shared prerequisite for BUG-54/55/56/58: the `trainingRunStore` Pinia store
(design documented in `architecture.md` §"SPA run-state management")._

### Group B — Audio quality & training UX (BUG-59..67, filed 2026-09-03)

_From the Colab notebook analysis (`hyakuchiki/realtimeDDSP` reference).
Granular steps: [`implementation/m20-audio-quality-bugs.md`](./implementation/m20-audio-quality-bugs.md).
Resolution sub-steps in `bugs.md`; architectural decisions for BUG-59 and
BUG-65 in `architecture.md`; UI spec in `ui-requirements.md`._

- [ ] **BUG-60** _(major, M2)_ — F0 range (`f0_min_hz`/`f0_max_hz`) not configurable
      **end to end**. Corrected 2026-09-03: both trackers already accept the range;
      the gap is the threading from REST → `compute_features()` plus the missing UI.
      Must cover **both** backends (CREPE `fmin`/`fmax`, parselmouth `f0_min`/`f0_max`).
      Also the mitigation for the YIN mismatch in BUG-65.
      ⚠ **First bug in the feature-cache batch** — see the ordering constraint below.
- [ ] **BUG-59** _(major, M2)_ — `sample_rate` effectively 16 kHz; must be
      user-configurable, default 48 kHz. Corrected 2026-09-03: `dataset/features.py`
      is already rate-parameterised — the hardcoding lives in `dataset/io.py`,
      `dataset/loader.py` (`AUDIO_SAMPLES_PER_FRAME`), `server/tasks.py`,
      `server/routes/dataset.py` and `server/routes/reverb.py`.
      Sub-steps: (a) threading per the `architecture.md` 9-layer table,
      (b) **rate-aware** VRAM estimator in `train/gpu.py`, (c) selector in
      PreprocessingView + read-only display & mismatch guard in `TabCore.vue`.
      ⚠ **(a)+(b) are atomic** — see the hardware constraint below.

- [ ] **BUG-61** _(minor, M2)_ — F0 Viterbi smoothing flag not exposed; matters for
      pitch-slide instruments. Corrected 2026-09-03: no `decoder` argument is passed
      at all (Viterbi is torchcrepe's *default*), and the flag is **CREPE-only**
      (parselmouth has no equivalent). ⚠ **Also invalidates the feature cache** —
      belongs in the ordered batch, see constraint 1 below.
- [ ] **BUG-65** _(major, M3)_ — **in-progress.** Realtime export must use
      streaming-compatible YIN/pYIN, not CREPE. Sub-steps: (a) `architecture.md`
      section ✅ done, but the required notes in `m3-model-training.md` and
      `m17-midi-synth-vst.md` are ⬜ still missing; (b) `inference/yin.py`
      TorchScript implementation ⬜ open.
- [ ] **BUG-62** _(minor, M3)_ — No pretrained warm-start checkpoint; limited-range
      instruments train poorly from random init. Canonical field name
      `warm_start_checkpoint`; asset delivered by **download-on-first-run**
      (decision 2026-09-03). Sequenced after BUG-59 (base model must be 48 kHz).
- [ ] **BUG-66** _(minor, M3)_ — TensorBoard does not log reconstructed audio
      (`train_orig` vs `train_resyn`) — the primary DDSP quality signal.
      **Depends on BUG-59** (`config.sample_rate` does not exist yet).
- [ ] **BUG-63** _(minor, M5)_ — `max_steps` shown without estimated-epochs context.
      **Depends on BUG-52** (diagnostics reachable) **and BUG-59** (`slice_length`),
      and needs a backend step first: the diagnostics payload currently returns no
      `total_chunks`.
- [ ] **BUG-67** _(minor, M5)_ — No instrument pitch-range reference guide
      (UX companion to BUG-60; same file → sequential, never parallel).
- [ ] **BUG-64** _(minor, M15)_ — Export metadata (`author`, `description`,
      `is_experimental`, `model_version`) missing from `ParamManifest` + export UI;
      required for Neutone marketplace submission. Fully independent of the
      feature-cache batch — the only Group-B bug whose analysis needed no correction.

**Execution order for Group B** (see `m20-audio-quality-bugs.md` for the granular
steps): **BUG-60 → BUG-61 → BUG-59** (the feature-cache batch, strict order) →
BUG-67 → then, independently, BUG-64, BUG-65, BUG-63, BUG-66, BUG-62.

#### ⚠ Two hard constraints in Group B (not preferences)

**1. BUG-60 → BUG-61 → BUG-59 — feature-cache ordering.**
All **three** bugs add new keys to the feature-cache metadata and each invalidates
every previously extracted `.npy` feature set:

| Bug | New cache key(s) | Invalidates existing features? |
|---|---|---|
| BUG-60 | `f0_min_hz`, `f0_max_hz` | yes — F0 track re-extracted |
| BUG-61 | `f0_viterbi` | yes — F0 track re-extracted |
| BUG-59 | `sample_rate` | yes — audio, F0 **and** loudness re-extracted |

BUG-61 was **missing from this table until the 2026-09-03 re-analysis** — without it
users would have faced a *third* full re-preprocessing pass. Doing them in the order
above collapses everything into a single pass. The three bugs also modify the same
signatures and surfaces (`extract_f0_crepe()`, `extract_f0_parselmouth()`,
`compute_features()`, `run_preprocessing_job()`, `RunCreateRequest`, `PARAM_KEYS`,
`PreprocessingView.vue`, `fixtures.js`), so this order also avoids repeated merge
conflicts. Recorded in `bugs.md` BUG-59 `- sequencing:` / BUG-60 `- blocks:` /
BUG-61 `- batch:`.

**2. BUG-59 sub-steps (a) and (b) are one atomic change.**
Sub-step (b) — making `train/gpu.py::estimate_model_vram()` **rate-aware** — is
**not optional polish**. The stated minimum target hardware is an RTX 3060
Laptop (6 GB). Merging (a) alone flips the default to 48 kHz while the estimator
is still calibrated to 16 kHz, so the feasibility check and `batch_size_max`
under-report by ~3× and the wizard green-lights configurations that OOM on the
project's own baseline GPU. That is strictly worse than today's state: currently
the app is merely low-quality; (a)-without-(b) makes it **broken on the reference
hardware**. Either land (a)+(b) together, or gate the 48 kHz default behind (b).
Note the corrected premise (2026-09-03): `estimate_model_vram()` holds no
sample-rate constants at all — only empirical `BASE_ESTIMATE_GB` baselines plus a
16 kHz docstring — so (b) means "scale the audio-domain terms by `sample_rate/16000`",
not "recalculate a sample-count table".
Recorded in `bugs.md` BUG-59 `- resolution:` and `architecture.md`
§"Sample rate pipeline".

### Group C — Process/quality regressions (found 2026-09-03)

- [ ] **BUG-68** _(minor, M4)_ — `server/tasks.py` is **committed** in an unformatted
      state, so `ruff format --check` is red on a clean checkout and the
      Definition-of-Done formatting gate fails before any work starts. Mechanical
      single-file fix (`ruff format server/tasks.py`), must be delegated as a code
      edit. `ruff check` alone does not surface it.


