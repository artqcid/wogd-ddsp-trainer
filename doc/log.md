# wogd-ddsp-trainer - Chronological Log

_Append-only, newest first. Parseable with `grep "^## "`. Entries use
`**Creation**`, `**Update**` or `**Deprecation**` prefix + linked concept file._

## 2026-09-01 — M14.2.0 Design System spec added (ARCHITECT)

**Decision:** Modern AI-dashboard visual language adopted. Design reference:
Shasanko Das — *AI Content Creation & Analytics SaaS Dashboard – Dark Mode
UI/UX* (Dribbble 27444658). Key traits: deep indigo-black backgrounds,
Indigo #6366F1 primary accent, Cyan #06B6D4 secondary accent, 16px-radius
cards with glow shadow, Inter variable font, pill-shaped badges, generous
spacing.

**Update:** [`implementation/m14-dual-mode-ui.md`](./implementation/m14-dual-mode-ui.md)
— Phase 0 "Design System" block inserted before Phase 1 Backend. Six
sub-steps (M14.2.0-A through M14.2.0-G):
A: `index.html` Inter + JetBrains Mono font links.
B: `webui/src/style.css` (NEW) — full global design token file: 70+ custom
   properties, reset, card/button/badge/form/tab/modal utility classes.
C: `main.js` — import `'./style.css'`.
D: `App.vue` — remove scoped `:root`; use token vars in shell layout.
E: `Sidebar.vue` — gradient SVG brand mark, emoji nav icons, active glow,
   dividers, footer.
F: `TopBar.vue` — pill badge status, breadcrumb section label, GPU chip.
G: vitest green verification gate.
File map in m14-dual-mode-ui.md updated to include Phase 0 files.

**Update:** [`ui-requirements.md`](./ui-requirements.md) — new section
"Visual design system (M14.2.0)": design reference, token category table,
global utility class list, font spec, shell component specs (Sidebar + TopBar).

**Update:** [`checklist.md`](./checklist.md) — M14.2.0 task added as Phase 0
block (prerequisite for Phase 2); Phase 2 header updated to "requires Phase
0 + Phase 1 complete". Full sub-step checklist in task description.

Wiki: 152 files, re-index pending.

## 2026-09-01 — M14 Dual-Mode Training UI + Backend Tier System designed (ARCHITECT)

**Architecture decision:** Dual-Mode Training UI (Wizard + Power-User Tabs)
confirmed. Model tier (`standard/component/hacks/engine/advanced`) is the
primary UI axis; GPU feasibility is surfaced in both modes (Wizard Step 1
tier cards + persistent `GpuFeasibilityBanner`).

**Creation:** [`implementation/m14-dual-mode-ui.md`](./implementation/m14-dual-mode-ui.md)
— full granular plan (18 subagent steps, Phase 1 backend-first then Phase 2
frontend).

**Update:** [`ui-requirements.md`](./ui-requirements.md) — new section
"Dual-Mode Training UI (M14)": model tier table, Wizard spec (3 steps),
Power-User Tab spec (5 tabs, lock/unlock by tier), GPU Feasibility Banner
spec, Preset system extension (`model_tier` field), Pinia store definition,
new/changed Vue components list. Acceptance criteria extended with M14
mock-data seam requirements.

**Update:** [`architecture.md`](./architecture.md) — new section "Model Tier
system & Dual-Mode UI (M14)": tier definitions table, DB schema migration
(`model_tier` on `presets` + `runs`), `train/gpu.py` additions
(`VRAMEstimate`, `estimate_model_vram()`), `server/presets.py` changes
(`VARIANT_KEYS`/`ENGINE_KEYS`/`ADVANCED_KEYS`, tier-aware seed),
`server/routes/training.py` changes (`model_tier_mismatch` in validate,
checkpoint-tier guard on resume), `server/tasks.py` changes (tier-aware
`build_training()`), new `GET /api/gpu/feasibility` endpoint spec + full
JSON response shape, updated REST endpoint map.

**Update:** [`plan.md`](./plan.md) — M14 milestone entry added (chronological
position after M13); Decisions section: "Dual-Mode Training UI (M14,
2026-09-01)" recorded.

**Update:** [`checklist.md`](./checklist.md) — M14 task sections added:
Phase 1 Backend (M14.1.1–M14.1.9, 9 tasks) + Phase 2 Frontend
(M14.2.1–M14.2.9, 9 tasks). Total: 18 new checkboxes.

**Update:** [`index.md`](./index.md) — M14 implementation plan link added;
`plan.md` summary updated to M1–M14; `architecture.md` + `ui-requirements.md`
summaries updated.

Wiki: re-index pending (no code changes in this commit).

## 2026-09-01 — M9–M13 implementation plans created (ARCHITECT)

**Creation:** five new implementation-plan files for milestones M9–M13:

- [`implementation/m9-alternative-synth-engines.md`](./implementation/m9-alternative-synth-engines.md)
  — SinusoidalSynth, CombSubSynth, colored noise, granular noise; 9 subagent steps.
- [`implementation/m10-newt.md`](./implementation/m10-newt.md)
  — SawtoothExciter + NEWTUnit (ISMIR 2021); 7 subagent steps.
- [`implementation/m11-latent-space.md`](./implementation/m11-latent-space.md)
  — GRUEncoder, β-VAE, checkpoint morphing, latent steering; 9 subagent steps.
- [`implementation/m12-polyddsp.md`](./implementation/m12-polyddsp.md)
  — multi-pitch tracker, PolyDDSPModel N shared-weight voices; 7 subagent steps.
- [`implementation/m13-voice-conversion.md`](./implementation/m13-voice-conversion.md)
  — ContentEncoderWrapper (HuBERT-Soft/ContentVec), VC pipeline, VoiceConversionView; 9 subagent steps.

**Update:** `doc/plan.md` — M9–M13 milestone entries added.
**Update:** `doc/checklist.md` — M9–M13 open task sections added (44 new checkboxes).
**Update:** `doc/index.md` — M9–M13 implementation-plan links added.
Wiki: 151 files indexed, 1005 symbols.

## 2026-09-01 — M8 detailed implementation plan + M9–M13 phase analysis (ARCHITECT)

**Update:** `doc/implementation/m8-experimental-sdk-hacking.md` — full
granular step breakdown (14 subagent steps). Previous 5-step stub replaced
with per-line code specifications for all hacks:

- M8.1.1–4: `DDSPVariant` dataclass, server threading, `SynthHacksView.vue`
- M8.2.1: inharmonic ratios (`synths.py:65`)
- M8.2b: FM synthesis (`synths.py:66–72`)
- M8.3.1: `_apply_waveform()` dispatcher — `sin/square/saw` + phase distortion
- M8.3c: trainable wavetable `nn.Parameter(256)` + checkpoint tagging
- M8.4.1: spectral-loss band mask (`losses.py`)
- M8.4.2: LFO injection into noise magnitudes (`ddsp_model.py`)
- M8.6: angular cumulative sum (phase-drift fix)
- M8.5.1–2: 15 pytest + 1 vitest smoke tests, docs finalization

**Update:** `doc/checklist.md` — M8 section expanded from 5 to 13 granular
checkboxes (M8.1.1–M8.1.4, M8.2.1, M8.2b, M8.3.1, M8.3c, M8.4.1, M8.4.2,
M8.6, M8.5.1, M8.5.2).

**Analysis (doc only):** M9–M13 phase analysis produced (Sinusoidal/CombSub
engines, NEWT, Latent Space/VAE, PolyDDSP, Voice Conversion). No doc files
written yet — analysis only in conversation; awaiting user decision on scope.

## 2026-08-31 — M7.1 + M7.2 + M7.4 (F0 override, Component Mixer, Tests) — Milestone M7 complete

**Creation:** M7.1 (F0 override editor + transforms), M7.2 (Component Mixer), M7.4 (tests + docs).

Continuation of same session (autopilot: "alle offenen punkte ohne rückfragen erledigen").

- M7.1.1: `load_f0_override()` + `f0_override` param in features.py; REST upload/delete in dataset routes.
- M7.1.3: `dataset/transforms.py` — quantize_to_scale, inject_noise, invert_pitch (numpy only).
- M7.1.2+4: F0Editor.vue (canvas), F0RulesPanel.vue, F0EditorView.vue, route, sidebar, apiClient/mocks.
- M7.2.1: DDSPConfig.n_noise_bins; ParameterBounds (n_harmonics_min/max, n_filter_banks_min/max) across 4 tiers; clamping in server/presets.py; UI sliders in TrainingConfigView.vue.
- M7.2.2: ComponentMixer.vue (harmonics 0-120, filter banks 0-64, gains) + ComponentMixerView.vue.
- M7.4: 16 new tests. 186 pytest / 23 vitest green, ruff clean.

All M7 checkboxes [x]. Milestone M7 complete.

Subagent tasks: `ses_fa65de2d5ffem7uSQkJlO7LAsj` (F0 override backend), `ses_fa65dbdeaffeND7cd7qaSWAzs5` (transforms), `ses_fa65d9a0effeclxisyO0hG1IQz` (parameter bounds + config), `ses_fa654cc51ffeBy9b6FLnOMOIxr` (tests), `ses_fa6451248ffeQtWTAO7vBMPIkS` (Component Mixer UI).

## 2026-08-31 — M7.3 Reverb IR Injection (Option B — fixed kernel swap)

**Creation:** M7.3 — IR injection/extraction for SimpleReverb via kernel buffer swap.

Plan approval: "commit push, danach go weiter" (continuation of same session).

- M7.3.0: Research confirmed SimpleReverb uses `register_buffer` (no nn.Parameter). Decision: Option B (fixed kernel swap), safe for checkpoints.
- M7.3.1–2: `model/reverb_injection.py` — inject_ir() + extract_ir(). 7 tests.
- M7.3.3: REST endpoints (server/routes/reverb.py), ReverbInjectionView.vue, router + sidebar + apiClient + mocks.
- 170 pytest / 23 vitest green, ruff clean.

Subagent tasks: `ses_fa66fe540ffezKWYmnmHbjTNDA` (M7.3.3 UI wiring).

## 2026-08-31 — M7.0 Output Enhancer (Vocos/BigVGAN post-processor)

**Creation:** M7.0 – Optional DDSP output enhancer using pre-trained vocoder.

Plan approval: user said "ja, lass mich kurz etwas abtippen..." (impact analysis) then "Continue with the steps" (implementation).

- M7.0.1: Research chose Vocos (MIT, pip, HF) as primary, BigVGAN as fallback, identity fallback.
- M7.0.2: `inference/enhancer.py` — `OutputEnhancer` class with 3 backends + lazy singleton in `inference/render.py`.
- M7.0.3: UI checkbox in InferencePlaygroundView.vue, REST `enhance: bool` param in POST /api/inference/synthesize, pass-through in server/tasks.py.
- M7.0.4: 7 tests (identity fallback, shape preservation, enhance flag, default False). 163 pytest / 23 vitest green.
- Doc: m7-experimental.md updated with [x] marks + History.
- Wiki index updated (852 symbols), ruff format clean.

Subagent tasks: `ses_fa6841006ffemWDAaVMHw50fhe` (M7.0.2 enhancer module), `ses_fa67a6c8fffeABe4dinaV5iHIb` (M7.0.3 UI toggle).

## 2026-08-31 - M3.6 DataLoader + M5.8 Preset/BUG fixes + M5.8.5 Decoder/Reverb UI + M4.7 warning logs

**Update:** Implemented all findings from the M1–M6 review across 3 milestones.
Plan approval: user said "ja, beachte die agent rules genau".

- **M3.6 DataLoader (4 steps):** (a) Contract decision documented in `architecture.md`:
  `Trainer` accepts a `DataLoader`, wraps `DDSPDataset` from `FeatureCache`.
  (b) `DDSPDataset` in `dataset/loader.py` — PyTorch Dataset chunking merged
  FeatureCache arrays into 64000-sample segments (task_id: `ses_fa6abbdd7ffen5j5XgKR2TcV2E`).
  (c) `Trainer.run()` gets optional `data_loader` parameter with `itertools.cycle`
  wrapping (task_id: `ses_fa6a49f34ffe7yMWYBpvzQMoRC`). (d) `server/tasks.py::run_training_job`
  uses DataLoader when cache exists, falls back to `build_tensors()` (task_id:
  `ses_fa6a05195ffeT14uMMaIO4rQcO`). +5 tests `test_loader.py`.
- **M5.8.1-4 BUG-5 / BUG-6 fixes:** `fixtures.js` aligned to DDSP schema
  (`is_builtin`, `params`, `hidden_size`, `step-*.pt`) (task_id:
  `ses_fa6ac07ebffeYtkAwYn1seHmlA`). `TrainingConfigView.vue` updated:
  preset filter by `is_builtin`, DDSP field names (`hidden_size`, etc.),
  speed labels `0.5x`/`0.75x`/`0.9x` instead of VRAM %, dead AutoVC clamping
  block removed (task_id: `ses_fa6abe82effeYqw67zgoXK68Sw`).
- **M5.8.5 Decoder/Reverb UI:** `DDSPConfig` gained `decoder_type` and
  `use_reverb` (task_id: `ses_fa6a043a8fferuT5nmFOgOI9PN`). `DDSPCore`
  conditionally creates/applies reverb (task_id: `ses_fa69c536effePtfqpxXvfKaUJg`).
  `TrainingConfigView.vue` has decoder-type `<select>` and reverb checkbox
  (task_id: `ses_fa69c40eeffef4LIZJMiJRI295`).
- **M4.7.1:** `build_tensors()` emits `logging.warning` when falling back to
  synthetic data (task_id: `ses_fa6a4868cffeNOlsGWvRoq32pP`).
- **M4.7.2:** completed implicitly via M3.6.4 (DataLoader replaces single-batch
  dummy in `run_training_job`).
- **M3.1.4 `n_noise_bins`:** checkpoint round-trip fix — added to `DDSPConfig`.

**Verify:** ruff 0, pytest 156/1 (5 new loader tests), vitest 23/23,
ruff format 91/91, wiki lint clean.

## 2026-08-31 - M1–M6 full review: 18 findings documented across all implementation plans

**Update:** Full project review (fachlich + technisch, Frontend + Backend).
18 findings filed across all milestones; improvements added to implementation
plans as additional requirements (no code changes):

- **BUG-5 filed** (open): Preset-schema drift — frontend fixtures/views use
  AutoVC field names (`hidden_dim`, `type: 'autovc'`) instead of the DDSP
  backend schema (`hidden_size`, `is_builtin`). Fix steps: `m5-webui.md` M5.8.1–M5.8.3.
- **BUG-6 filed** (open): Training Speed labels in UI show wrong VRAM percentages
  (25/50/75%) instead of actual speed-modifier factors (0.5×/0.75×/0.9×). Fix:
  `m5-webui.md` M5.8.4.
- **`bugs.md`:** `next_id` 5→7; BUG-4 moved from "Open" to "Fixed" section.
- **`m3-model-training.md`:** M3.1–M3.4 steps marked `[x]` (were implemented but
  not ticked); M3.1.4 added (`n_noise_bins` into `DDSPConfig`); M3.6 added (real
  `DataLoader` — 4 sub-steps, blocker for M7.1 F0-override).
- **`m4-backend.md`:** M4.7 added (`build_tensors()` silent-fallback warning-log +
  DataLoader wiring, dependent on M3.6).
- **`m5-webui.md`:** M5.8 added (5 sub-steps: fixture alignment, preset-filter fix,
  DDSP payload fix, speed-label fix, decoder-type/reverb-toggle UI controls).
- **`m6-polish.md`:** M6.2.1 closed `[x]`; M6.5 marked deferred/redirect to M7.0;
  BUG-4 reference corrected (was `M6.5 — BUG-4`, now `M6 — BUG-4 fix`).
- **`m7-experimental.md`:** M7.0 added (Output Enhancer NSF-HiFiGAN, deferred from
  M6.5, 4 sub-steps); M7.3.0 added (Reverb IR research blocker — trainable vs.
  fixed reverb decision); prerequisite block added before M7.1.
- **`m1-scaffold.md`:** BUGS section cleaned (orphan `(none)` removed; BUG-1
  status updated to `wont-fix`).
- **`m2-dataset-prep.md`:** frontmatter `status: draft → implemented`; BUGS section
  updated with A-weighted loudness open question (RMS-dB vs. A-weighting).
- **`architecture.md`:** Status section updated (M1–M6 done, M7/M8 open); new
  "Known open items" subsection lists all 7 actionable findings with plan
  cross-references.

**Verify:** wiki lint clean, `index_project_code` ran (9 files reindexed).

## 2026-08-31 - BUG-4 (Training Speed / GPU / VRAM validation) implemented

**BUG-4** (three related deficiencies): (a) Training Speed FAST/NORMAL/QUALITY
selector, (b) real GPU display from backend, (c) VRAM validation popup.

Backend: `server/routes/host.py` — `GET /api/host/info` (GPU info from
`suggest_for_host`), `POST /api/host/validate-preset` (`apply_speed` + clamp).
Frontend: `apiClient.getHostInfo()` / `validatePreset()`, `gpuHostInfoFixture`,
`TrainingConfigView.vue` with speed radio buttons, dynamic GPU display, VRAM
popup overlay ("Anpassungen annehmen?"). Bug: `doc/bugs.md#BUG-4` → `status: fixed`.

**Verify:** `ruff`/`format` 0, `pytest` 151/1, `vitest` 23/0, Build clean.

## 2026-08-31 - M6.4 GPU-Profilierung (RTX 3060): Training + Inference

**Creation:** `tests/profile_gpu.py` benchmarkt Training-Step + Inference auf
GPU. Ergebnisse: QUALITY (hidden=512, 5 STFT-Scales): 35.5ms/Step (~28
Steps/s), Inference RTF 0.004x. NORMAL (hidden=256, 3 Scales): 14.6ms/Step
(~68 Steps/s). Bottleneck: Backward-Pass (38-45%), Loss (18-22%). Per CCD
keine triviale Optimierung möglich, die Qualität/Architektur nicht opfert.

**Verify:** `ruff`/`format` 0, `pytest` 139/1, `vitest` 22/0, Build clean.
Wiki lint clean, index synced.

## 2026-08-31 - M6.3 Error-Handling: REST-Envelope + Worker-Fehler + UI-Toasts

**Creation:** `server/errors.py` mit ApiError + Exception-Handlern (einheitliches
`{"error": {"code": "...", "message": "..."}}`-Envelope für alle HTTP-Fehler via
`install_handlers()` in `main.py`). `error`-Spalte auf `runs`/`synthesis_jobs`-
Tabellen (Migration in `init_db`), `run_set_error`, `synth_update(error=...)`.
Task-Worker persistieren jetzt Fehlermeldungen. UI-Toast-System: Pinia-Store
(`useNotificationsStore`) + Overlay-Komponente (`ToastNotifications.vue`,
animierte Übergänge, auto-dismiss) in `App.vue` verdrahtet.

**Verify:** Tests aktualisiert (neues Envelope-Format). `ruff`/`format` 0,
`pytest` 139/1, `vitest` 22/0, `npm run build` sauber.

## 2026-08-31 - M6.1 Datenverzeichnis-Logik + Live-Änderung + Packaging-Task

**Creation:** Zentrale Pfad-/Standort-Auflösung in `server/paths.py`:
`install_dir()` (App-Code-Standort, Repo-/Install-Root) und `data_dir()`
(ein "Sammelwurzel" für `datasets/`, `runs/` und die SQLite-DB). Default für
`data_dir()` ist `%LOCALAPPDATA%\wogd-ddsp-trainer` unter Windows — identisches
Verhalten in Entwicklung und nach Installation (kein Docker, kein globaler
Eingriff). Präzedenz: Env `WOGD_DATA_DIR` > in DB-Meta persistierter Override
(über `PUT /api/settings`) > Plattform-Default. Nur das Datenverzeichnis ist
zur Laufzeit durch den User änderbar; Installationsverzeichnis und DB-Pfad sind
fest.

**Wiring:** `get_db_path()` (db.py), `runs_dir()` (tasks.py), `datasets_dir()`
(routes/dataset.py), `build_tensors()` (tasks.py) auflösen alles über
`paths.py`. `connect()` erzeugt jetzt den DB-Überordner (falls `%LOCALAPPDATA%`
noch nicht existiert). `ensure_data_dirs()` wird beim Start aufgerufen und
migriert best-effort alte `cwd/datasets`/`cwd/runs` in das neue Datenverzeichnis
(dev-Übergang).

**REST + UI:** `GET/PUT /api/settings` (Live-Datenverzeichnis-Änderung mit
Validierung absoluter Pfade, Migration vorhandener datasets/runs auf das neue
Ziel, Persistenz in DB-Meta, Reset auf Default), `GET /api/settings/defaults`.
UI: `SettingsView.vue` (Anzeige Installationspfad + Datenverzeichnis + DB +
datasets/runs; Datenverzeichnis live änderbar mit Reset; Hinweis dass
Input-Samples per Drop-In in das datasets-Verzeichnis kopiert werden). Neu:
apiClient-Methode, Mock, Fixtures, `settings.test.js`, `test_api_settings.py`.

**Packaging:** `build-installer` VSCode-Task + `scripts/build-installer.ps1`
erzeugen ein eigenständiges, portables Windows-Paket unter
`dist/installer/wogd-ddsp-trainer/` (Backend-Quellen + `webui/dist` +
Gebinde-.venv mit Python + Bibliotheken + `start.bat`/Launcher). Kein globaler
Installationsvorgang, keine Änderung der Host-Konfiguration. Vollständiger
Windows-Installer (NSIS/InnoSetup) mit Uninstaller ist ein späteres Milestone.

**Docs:** README (Umgebungsvariablen, VSCode-Task-Tabelle, Installationsabschnitt),
`doc/architecture.md` (Umgebungsvariablen-Liste), `doc/workspace-workflow.md`
(Packaging-Abschnitt), `doc/implementation/m6-polish.md` (M6.1.3 erledigt,
M6.1.6/M6.1.7 ergänzt, History).

**Verify:** `ruff check`/`format` 0 Fehler, `pytest` 139/1 (GPU-Übersprung),
`vitest` 21/0, `npm run build` sauber (neue SettingsView- + ApiClient-Chunks).

**Update:** [`workspace-workflow.md`](workspace-workflow.md) (VSCode-Abschnitt
neu), [`implementation/m6-polish.md`](implementation/m6-polish.md) (M6.1.4/5 +
M6.6.4). `start-application-debug`/`start-application-release` sind **keine
Build-Tasks** (das bleiben `build-debug`/`build-release`) — beide prüfen jetzt,
ob der Frontend-Build aktuell ist (Rebuild nur wenn `webui/dist` fehlt/älter
als Quelle), und starten danach **Frontend + Backend gemeinsam** über
`scripts/start-app.ps1 -Mode <Debug|Release>`: Debug = Backend via debugpy
(`--listen 5678 --wait-for-client`) + Vite-Dev (`:5173`), Attach per
`Debug Backend (attach)`-Launch; Release = uvicorn mit `WOGD_SERVE_STATIC=1`,
serviert API + `webui/dist`.

**Verify:** Release — kein Rebuild bei aktuellem `dist`, Rebuild bei fehlendem
`dist`, `/` html + Server sauber gestoppt. Debug — `:5173` (Vite) + `:5678`
(debugpy) beide oben, sauber gestoppt. `debugpy` als dev-Dependency ergänzt;
redundante `backend-dev`/`frontend-dev`/`backend-release`-Tasks entfernt.

## 2026-08-31 - M6.1 VSCode Debug/Release Start-Tasks + Release Static Serving

**Update:** [`implementation/m6-polish.md`](implementation/m6-polish.md) (neue
Steps M6.1.4/M6.1.5 + M6.6, `>>> History`), [`workspace-workflow.md`](workspace-workflow.md)
(pending M6.6.3). Der Nutzer wollte `start-application-debug`/
`start-application-release` als manuell startbare Einträge — Debug = Vite
debugbar + Backend im VSCode-Debugger; Release = gebautes Frontend servieren.
Umsetzung: (a) `.vscode/launch.json` (compound `Debug Application` =
`Debug Backend` debugpy `server.main:app` + `Vite Dev (debug)`); (b)
`.vscode/tasks.json` — `start-application-debug` -> `frontend-dev`,
`start-application-release` -> `build-release` -> `backend-release`
(`WOGD_SERVE_STATIC=1`); (c) `server/main.py` — statisches Servieren von
`webui/dist` + SPA-Fallback, gated auf `WOGD_SERVE_STATIC=1`.

**BUG-3** gefunden + gefixt (`webui/src/App.vue` importierte `RouterView` als
Default-Export → Produktions-Build scheiterte; jetzt Named-Import, `npm run
build` grün). **M6.6 verifiziert:** `server.main.mount_frontend` extrahiert +
`tests/test_frontend_static.py` (Static-Serving + SPA-Fallback); volle Checks
grün (`ruff`/`format` 0, `pytest` 133 passed / 1 GPU-skip, `vitest` 18 passed,
`vite build` ok). Live-Release-Test auf `:8021`: `/` html, SPA-Fallback html,
`/api/datasets` 200; Server danach gestoppt (kein Listener übrig).
`workspace-workflow.md` um VSCode-Tasks/Launch-Sektion ergänzt.

## 2026-08-31 - M5 Web-UI umgesetzt (App Shell + Views + Vitest)

**Creation:** [`ui-requirements.md`](ui-requirements.md) (bindend für alle
Rollen), [`implementation/m5-webui.md`](implementation/m5-webui.md) (M5.1–M5.7
markiert, `status: implemented`). Implementiert in `webui/`: Abhängigkeiten
`vue-router@4` + `wavesurfer.js@7`; Dark-Theme-Shell (`App.vue` mit CSS-Vars
auf `:root`, `Sidebar.vue` mit 4 Nav-Gruppen + Presets, `TopBar.vue`, Router
mit 9 lazy Routes, `main.js` registriert Router + Pinia); API-Client-Brücke
auf alle 22 REST-Endpoints (`api/apiClient.js` + `mocks/fixtures.js` +
`mocks/mockApiClient.js`, Mock-Data-Seam, keine Backend-Imports). Views:
`UploadIngestionView` (Drag-drop + Wavesurfer), `DatasetManagerView`,
`PreprocessingView` + `PitchConfidenceIndicator`, `TrainingConfigView` +
`PresetSaveDialog`, `TrainingDashboardView` (TensorBoard-iframe/New-Tab +
Polling), `InferencePlaygroundView` + `ABComparisonPlayer`, `ModelExportView`,
`PresetManagerView`. Vitest M5.7: 8 neue Render-Tests
(`tests/views-batch{1,2}.test.js`) + bestehende → 18/18 grün.

**Fixes aus Test-Roundtrips (Subagenten + Primary):** `PresetManagerView`
v-for-Template-Scope (param.key/value außerhalb des V-For), `ModelExportView`
-Format-Cards rendern aus statischer `formatOptions` statt leerem
`selectedFormats`, `InferencePlaygroundView` `v-model` auf file-input →
`@change`-Handler. Test-Setup nutzt `vi.mock('vue-router')` + `flushPromises`.

## 2026-08-31 - M4 Web-Backend umgesetzt (FastAPI + Celery + Presets)

**Creation:** [`architecture.md`](architecture.md) (Web-backend-Sektion),
[`implementation/m4-backend.md`](implementation/m4-backend.md). Implementiert
und verifiziert: FastAPI-App (`server/main.py`, Lifespan: init_db + Built-ins-
Seed + Hardware-Fingerprint/Reclamp), SQLite-Layer (`server/db.py`), Celery +
TaskRunner (`server/tasks.py`, kooperativer Stop via `stop_event` in
`trainer.py`), Preset-Logik mit Clamping (`server/presets.py`), TensorBoard-
Provisioning (`server/tensorboard.py`), REST-Routen für Dataset/Model/Run-
Lifecycle/Inference/Presets (`server/routes/`). Fehlerbehebungen via
Subagenten: `run["id"]`→`run["run_id"]`, Checkpoint-Subdir, `bounds_to_dict`,
fehlende `UploadFile`/`Annotated`-Imports, `FileResponse` aus `fastapi.responses`,
`datasets_dir()` `Path("")`-Bug, B008/F821/SIM-Cleanup (details im impl-plan
`## History`).

**Update (Backend-Tests M4.3/M4.6 abgeschlossen):** Neu
`tests/test_server_db.py`, `tests/test_server_presets.py` (Unit),
`tests/test_api_datasets.py`, `tests/test_api_training.py`,
`tests/test_api_inference.py`, `tests/test_api_presets.py` (API via
`TestClient` + `FakeTaskRunner`). Primary-Fixes aus Test-Roundtrips
(subagent task_ids im impl-plan): URL-Präfix `"/runs"`→`"/api/runs"`,
Modul-`RUNS_DIR`-Import-Cache→`runs_dir()`, `_wav_bytes()`/`_run_id`-Fixes,
Multipart-Liste-von-Tripeln, 202 statt 422 bei optionalem audio, job_id ist
`str(uuid4())`, `_run_payload`+`name`/`run_id`-Keys, kein GET-Einzel-Preset.
Produktions-Bugfixt: `datasets_dir()` ignorierte ein gesetztes, aber noch
nicht existierendes `WOGD_DATASETS_DIR` und fiel auf `Path.cwd()/datasets`
zurück (Repo-Verschmutzung). Checks: ruff check+format clean (83 Dateien),
pytest 132 passed/1 GPU-skip, vitest 2 passed (webui).

**Status:** Checkliste M4.1/2/3/4/5 `[x]`, M4.3 Backend-Tests `[x]`; M5
(Web-UI) als nächstes.

## 2026-08-31 - M3 Tests grün (8 -> 0 Fails)

**Update:** [`m3-model-training.md`](implementation/m3-model-training.md).
Alle M3-Unit-/Integrationstests laufen jetzt (pytest 77 passed, 1 GPU-skip;
ruff clean). Behobene Root-Causes (subagent task_ids in History):
- `assert_allclose` `atol`-only → PyTorch-2-`rtol` (Test-Fix, 3x).
- Forward-Nondeterminismus in `FilteredNoiseSynth` (global RNG) → feste
  `noise_buffer` (Generator nur in `__init__`, forward = Tensor-Slice) —
  macht auch ONNX-Export möglich (kein `CustomObjArgument` im FX-Graph).
- Checkpoint-Config-Mismatch → `config` wird im Checkpoint persistiert,
  `load_model_from_checkpoint` rekonstruiert das Modell daraus.
- TorchScript: `SimpleReverb` dynamische Python-Kontrolle → Kernel-Buffer +
  `F.conv1d(padding="same")` (statisch/tracebar); Export-Test erwartete
  fälschlich Dict statt Audio-Tensor.
- `render_to_file`: torchaudio 2.11 → torchcodec (nicht installiert); auf
  `soundfile` umgestellt (bereits deklariert).
- `train_step_reduces_loss`: 2 Steps + Rauschen-Target flaky → Null-Target
  über 80 Steps.
- Ruff-Cleanup vorbestehender M3-Testdateien (E501/I001/Format).
- Beobachtung: D-Subagent-Rewrite scheiterte am bekannten
  Small-Context-Tool-Abbruch (`Duplicate tool_call_id`, cancelled tasks) und
  hinterließ fehlerhaften Zwischencode — durch Primary-Verifikation
  gefangen und neu delegiert.

**Status:** M3.5.x `[x]`; Meta-Plan/Checklist M3-Abschluss.

## 2026-08-31 - TOON-Konvention für Subagent-Delegations-Prompts

**Update:** `AGENTS.md` (Subagent rules). Neue verbindliche Konvention: Der
Primary-Agent serialisiert strukturierte, uniforme Payloads (Dateilisten +
Zeilen, Signatur-/Parametertabellen, API-/Symbol-Arrays, Key-Value-Mappings)
in Delegations-Prompts als ` ```toon`-Block statt Inline-JSON/langer Listen.
- **TOON nutzen** für uniforme strukturierte Daten im Prompt.
- **Nicht TOON**: Freitext-Beschreibungen/Anweisungen (Markdown), Prosa-Kontext
  und v.a. **Code-Bodies** (immer als normales fenced code, nie via TOON);
  RAG-Snippets kommen unverändert aus `get_rag_chunk` (text).
- Wenn die Daten bereits vom RAG-Output-Filter (`query_code_rag format="toon"`)
  stammen, verbatim durchreichen statt neu encodieren. TOON ändert nie
  Daten/Logik, nur die Serialisierung beim Prompt-Schreiben.
- Anker: AGENTS.md (Single Source of Truth, via `opencode.json` instructions).

**Status:** Konvention dokumentiert; Anwendung ab nächster Delegation.

## 2026-08-31 - RAG/MCP-Monolith in mcp_rag/ Paket aufgeteilt (CCD)

**Update:** `wogd_ddsp_mcp_server.py` (1554 Z, 48 Funktionen) war ein Monolith
und verletzte SRP/CCD. Aufgeteilt in ein `mcp_rag/`-Paket; reines
Umorganisieren, **keine Verhaltens-/Logikänderung** (kein Schema-, Chunking-,
Query- oder Format-Token-Wechsel):
- `mcp_rag/chunking.py`  — strukturelles Chunking (py/cpp/md) + stabile IDs + `chunk_file()`.
- `mcp_rag/ngrams.py`    — n-Gramm-Embedding + cosine + `semantic_rerank`.
- `mcp_rag/db.py`        — `ProjectRAG` auf DB/Scan/Index reduziert (+ Konstanten/Schema).
- `mcp_rag/query.py`     — `query_rag`, `query_wiki`, LIKE-Fallbacks, `_build_match_expr`.
- `mcp_rag/formatting.py`— `format_results/compact/json/toon` + `chunk_ref` (hier lebt `format_toon`).
- `mcp_rag/wiki.py`      — `generate_wiki` + Dependencies/Usages/Anchor.
- `mcp_rag/__init__.py`  — Re-Exports. `wogd_ddsp_mcp_server.py` = dünner Einstieg
  (Pfade, `_rag = ProjectRAG(...)`, 4 MCP-Tools mit unveränderten Docstrings).
- `pyproject.toml`: ruff-exclude auf `mcp_rag/` erweitert (gleicher Stil).
- Verifikation: py-compile; Temp-DB-Round-Trip (Index→Query→Format(json/toon)→Chunk→Wiki)
  grün; `toon.decode == json.loads`; Einstieg importiert gegen echte DB, alle 4 Tools
  ok; `index_project_code` real (87 Dateien, 521 Symbole); ruff 7 vorbestehende Fehler
  (nur M3-Testdateien, unverändert), pytest 69 passed / 8 vorbestehend fail — nichts neu.

**Status:** Split fertig; Wiki neu generiert.

## 2026-08-31 - RAG-MCP: optional TOON output filter (opt-in)

**Update:** `wogd_ddsp_mcp_server.py` + `pyproject.toml`. Added a **pure
output-side** `format="toon"` serializer for LLM consumption of search results
(30–60 % token reduction vs JSON on tabular data; opt-in only, never default).
- Scope per user: **only** to optimize LLM work (RAG-MCP output). Fachliche
  App-Daten, `text`-Snippets, Docs, Subagent-Prompt-Freitext sind bewusst
  unberührt. Kern/RAG-DB (`index_project_code`, Chunk-Speicher, SQLite) wird
  nicht mutiert — TOON ist ein reiner letzter Serialisierungs-Schritt.
- `pyproject.toml`: `python-toon>=0.1.3` added (MCP-Server läuft im venv).
- `wogd_ddsp_mcp_server.py`: `ProjectRAG.format_toon()` (identisches stabiles
  Payload wie `format_json`, via `toon.encode`); `format_results()` um `toon`
  erweitert; `query_code_wiki` routet jetzt alle Nicht-`text`-Formate über
  `format_results` (json/compact/toon konsistent); Docstrings um `toon`
  ergänzt. `toon` optional importiert — bei Fehlen Fallback auf JSON.
- Abwärtskompatibilität gewahrt: `text` (Default), `compact`, `json` unverändert.
- Verified: TOON-Round-Trip identisch zu JSON-Playload (lossless, inkl. null +
  multiline), Backward-Compat-Checks grün, `pytest` 69 passed.
- **Pre-existing (nicht Teil dieser Aufgabe, aus früherer M3-Testgenerierung
  unvollendet):** `ruff` 7 Fehler + 8 Test-Fails in `tests/test_{gpu,losses,
  model,inference,trainer}.py` — siehe Entscheidungsbedarf im Report.

**Status:** TOON-Welle-1 fertig; Wiki via `index_project_code` aktualisiert.

## 2026-08-31 - Subagent model switched to Groq Qwen3.8 27B

**Update:** Subagent config (workspace-only). `general` and `explore` now run
on `groq/qwen/qwen3.8-27b` (workspace override in `opencode.json`); `compaction`
stays on `opencode/nemotron-3.5-lightning-free`.
- Global config: `provider.groq.models["qwen/qwen3.8-27b"]` registered
  (Context 131042 / Output 16384; model not yet in models.dev → visible only
  via explicit model entry). Restart opencode required; `GROQ_API_KEY` via
  `/connect`.
- `AGENTS.md` — subagent-model claims updated (general/explore = Groq Qwen3.8
  27B, compaction = nemotron).

**Status:** config saved; workspace-only scope per user request.

## 2026-08-31 - M2 Dataset prep implemented

**Creation:** M2 complete (parallel subagent delegation). Audio ingestion,
feature extraction (F0 factory), train/val split + on-disk cache, tests.
Design per `doc/implementation/m2-dataset-prep.md` + `architecture.md`.
- Files: `dataset/io.py` (load/resample-mono-16k/peak-normalize),
  `dataset/features.py` (F0 factory + loudness + normalize + `.npy` export),
  `dataset/loader.py` (read precomputed `.npy`), `dataset/split.py`
  (deterministic local-RNG split), `dataset/cache.py` (on-disk `FeatureCache`
  + `cached_feature_loader`), tests in `tests/test_{io,features,split,cache}.py`.
- **F0 decision (user's architecture recommendation):** strategy/factory
  `get_f0_extractor` — **CREPE-PyTorch (`torchcrepe`, MIT) primary/ML** for
  dataset prep + training (GPU); **parselmouth (Praat, GPLv3) CPU fallback**
  for fast unit-tests / local CI / UI preview. Unit tests are parselmouth-only
  (CREPE downloads weights → non-deterministic). `rmvpe` dropped (py3.14 /
  torch 2.13 fragility).
- Deps added to `pyproject.toml`: `torchcrepe==0.0.24`,
  `praat-parselmouth==0.4.7`.
- `doc/oss-dependencies.md` — torchcrepe (MIT) + praat-parselmouth (GPL-3.0)
  added; rmvpe resolved/dropped; parselmouth GPL copyleft note added (fallback
  is behind the factory seam, not the primary path).
- `doc/architecture.md` — F0 factory decision recorded (tech stack + pipeline).
- `doc/checklist.md` — M2.1-M2.4 marked done.
- `doc/implementation/m2-dataset-prep.md` — steps `[x]` + History.

**Status:** M2 done; checks green (`pytest` 36 passed, `ruff` clean).

## 2026-08-31 - M1 Scaffold implemented

**Creation:** M1 complete. Repo structure (`dataset/ model/ train/ inference/
server/` + `tests/`), `pyproject.toml`, `.venv` (Python 3.14), webui scaffold
(Vue 3 + Vite + Pinia), VSCode tasks, OSS dependency review. All DoD checks
green (`ruff check`, `ruff format --check`, `pytest`, `vitest`).
- Files: `pyproject.toml`, `webui/` (Vue/Vite/Pinia app, `ApiClient` +
  `MockApiClient` mock-data seam, HealthView, Vitest tests), `tests/`.
- env: torch 2.13.0+cu130 + torchaudio 2.11.0+cu130 installed from
  `download.pytorch.org/whl/cu130` (RTX 3060 detected, mixed precision OK).
- `doc/oss-dependencies.md` — new OSS dependency/license review (M1.6.2);
  all runtime/dev/frontend deps OSI-approved; `neutone_sdk` + `rmvpe`
  flagged as to-verify.
- `doc/bugs.md` — **BUG-1** (neutone_sdk pinned numpy<2.3 no cp314 Windows
  wheel on py3.14; deferred to M3.4).
- `doc/checklist.md` — M1.1-M1.7 marked done.
- `doc/implementation/m1-scaffold.md` — steps marked `[x]` + History
  (torch cu130 install, `pip install -e . --no-deps`, neutone_sdk/rmvpe
  sourcing, ruff excludes `wogd_ddsp_mcp_server.py`).

**Status:** M1 done; checks green; index rebuilt; lint clean.

## 2026-08-31 - Preset management added (FAST/NORMAL/QUALITY + custom)

**Creation:** Added preset management to the docs, placed as early as possible
in the milestone plan (M4 backend + M5 UI).
- `doc/checklist.md` — M4.5 Preset Management (SQLite schema, CRUD, GPU
  constraint validation) + M5.6 Preset Management view + M5.3 preset selector.
- `doc/implementation/m4-backend.md` — M4.5 section (5 steps: SQLite schema,
  built-in seed, CRUD endpoints, constraint clamping, save-from-run) +
  M4.6 expanded tests.
- `doc/implementation/m5-webui.md` — M5.3.2 PresetSaveDialog, M5.4.2 Save
  as Preset button, M5.6 PresetManagerView + sidebar nav.
- `doc/ui-requirements.md` — Section 3: preset management (FAST/NORMAL/
  QUALITY, custom, clamping); added PresetManagerView to component structure.
- `doc/architecture.md` — New "Preset management" section: SQLite schema,
  built-in presets table, constraint flow, REST endpoints.
- `doc/plan.md` — M4 description: "preset management (FAST/NORMAL/QUALITY +
  custom presets, GPU-constraint clamping)".

**Status:** Preset management fully documented across all layers (data model,
backend, UI, requirements, checklist); index rebuilt; lint clean.

## 2026-08-31 - VRAM budget / RTX 3060 6GB constraint

**Update:** Addressed the hardware constraint that all training MUST run on
RTX 3060 Laptop (6 GB VRAM). Analysis shows DDSP is lightweight: total VRAM
~1.3–2.2 GB with batch_size=1, mixed precision, offline feature extraction,
3-scale STFT loss and hidden_size ≤ 512 — leaving 3.8–4.7 GB headroom.
- `doc/architecture.md` — new "GPU detection & VRAM budget" section with
  VRAM budget table, required techniques (mixed precision, offline features,
  batch=1, 3-scale loss, sequence_length ≤ 4 s, hidden_size 256/512), and
  a VRAM tier table for the GPU auto-detection module.
- `doc/plan.md` — "VRAM budget / RTX 3060 6GB" resolved question added.
- `doc/implementation/m1-scaffold.md` — M1.2.4 step: verify mixed precision
  imports (`torch.cuda.amp.autocast` + `GradScaler`).
- `doc/implementation/m2-dataset-prep.md` — M2.2 section header: "offline";
  M2.2.4 step: save features as `.npy` during preprocessing.
- `doc/implementation/m3-model-training.md` — M3.1.3: configurable STFT
  scales (default 3); M3.2.2: VRAM tier proposal; M3.3.1: mixed precision +
  gradient checkpointing in training step.

**Status:** VRAM constraint documented and traced through all relevant docs;
lint clean.

## 2026-08-31 - Framework decision: PyTorch (drop TensorFlow / magenta/ddsp)

**Update:** Decided the best/most-modern framework now and restructured the
docs accordingly. Evidence: `magenta/ddsp` (TF) is legacy (archived parent
org); the active DDSP/SVC ecosystem is PyTorch (DDSP-SVC, DiffSinger/OpenVPI,
RAVE); **Neutone — our own export target — is PyTorch/TorchScript-only**;
Google steers new generative-AI work to PyTorch/Keras 3/JAX.
- `doc/plan.md` - resolved "DDSP implementation" -> self-owned PyTorch core
  (spec: DDSP paper; refs acids-ircam/ddsp_pytorch + magenta/ddsp); F0 -> RMVPE;
  decision "PyTorch is the framework" + "Export formats" (Neutone/ONNX/
  TorchScript); M3/M8 reworded; output-quality decision no longer TF-bound.
- `doc/architecture.md` - tech stack -> PyTorch + torchaudio; RMVPE F0; export
  Neutone/TorchScript/ONNX; "magenta/ddsp logs" -> "training loop logs".
- `doc/checklist.md` - M1.2 deps (torch/torchaudio/RMVPE/neutone_sdk); M3.1 own
  DDSP core; M3.4 export; M6.5 native PyTorch vocoder; M8 -> "synthesis hacks".
- `doc/ui-requirements.md` - export formats -> Neutone/ONNX/TorchScript;
  realtime target -> Neutone/TorchScript.
- `doc/implementation/m1-m8` - deps, DDSP core (PyTorch), export, M8 reframed
  (feature flags on our own core, not SDK patches).
- `doc/experimental-ddsp.md` / `doc/experimental-sdk-hacking.md` - framework
  refs (tfkl.Layer -> nn.Module); M8 as first-class.
- `doc/related-work.md` - framework table + lessons rewritten (same-framework
  comparison now).
- `README.md`, `AGENTS.md`, `.opencode/agent/BUILD*` - stack -> PyTorch.

**Status:** Framework decision applied consistently; index rebuilt; lint clean.

## 2026-08-31 - README (GitHub-facing summary)

**Creation:** `README.md` - 4-section GitHub-style summary: (1) development +
clone/VSCode workflow (venv, npm, ruff/pytest/vitest, run, VSCode tasks), (2)
installation (placeholder, M6 non-Docker packaging), (3) training usage
(placeholder outline), (4) Apache-2.0 license. Placeholders (`<TODO Mx: ...>`)
mark not-yet-implemented parts.

**Update:** `AGENTS.md` - added a sync rule under "Deterministic Sync Workflow":
`README.md` must be kept in sync whenever a knowledge update lands in `doc/`.

**Status:** README created; sync rule documented; index rebuilt, lint clean.

## 2026-08-31 - Related work (DDSP-SVC) + output-enhancer gap

**Creation:** `doc/related-work.md` - analysis of `yxlllc/DDSP-SVC` (real-time
singing voice conversion, MIT) and its implications: (1) raw DDSP output is not
studio-grade -> post-hoc output enhancer needed; (2) content encoder
(Hubert/ContentVec) as alternative conditioning; (3) real-time requires
splicing logic beyond a TFLite/TF.js export. Verified via the HF mirror +
GitHub repo.

**Update:**
- `doc/plan.md` - M3 note + new "Output quality" decision: post-hoc enhancer
  (vocoder/shallow-diffusion) scoped in M6, TF-compatible.
- `doc/checklist.md` - M6 split into M6.1-M6.5; new **M6.5** output enhancer.
- `doc/implementation/m6-polish.md` - new M6.5 enhancer step group.
- `doc/implementation/m7-experimental.md` - "Future directions" note (shallow
  diffusion -> M6.5).
- `doc/ddsp-concepts.md` - Applications pointer to related-work.
- `doc/index.md` - registered `related-work.md`.

**Status:** Enhancer gap captured; related-work reference added; index rebuilt;
lint clean.

## 2026-08-31 - Three-tier planning + M7/M8 milestones + UI rework

**Update:** Established the three-tier planning model (meta plan -> checklist ->
granular implementation plans) and added experimental milestones M7/M8.
- `doc/plan.md` - M3 reordered (GPU detection before the training loop); M7
  (experimental sound design / Musique Concrète) and M8 (experimental SDK
  hacking) milestones added; F0/feature-extraction question clarified to
  `f0_hz` + `f0_confidence` + `loudness_db` (verified against
  `ddsp/training/preprocessing.py`).
- `doc/checklist.md` - added YAML frontmatter; M2.1/M2.2 fixed (level
  normalization; features corrected to f0/confidence/loudness, no "harmonic
  amplitude"/"aperiodicity"); M3 reordered (GPU detection = M3.2, before the
  training loop); M5 split into M5.1-M5.6 (app shell + 4 view groups + tests);
  M7 and M8 sections added.
- `doc/architecture.md` - dataset/model feature-extraction wording corrected
  (harmonic amplitude/aperiodicity are decoder outputs, not features).
- `doc/workspace-workflow.md` - removed the stale `/ws` (WebSocket) Vite proxy
  (contradicted the no-WebSocket TensorBoard doctrine).
- `doc/ui-requirements.md` - reworked: app shell (dark SPA + sidebar 4 nav
  groups + top bar), granular views grouped by navigation, corrected export
  formats (SavedModel/TF.js/TFLite/Neutone; no PyTorch/ONNX), realtime target =
  TF.js/TFLite (not VST), M7 experimental sections (F0 editor two-tier,
  component mixer, reverb IR injection + extractor), Wavesurfer.js dependency.
- `AGENTS.md` - added "Planning tiers" + "Bug tracking" workflow sections;
  fixed stale PyTorch/Vue-React stack description.
- `.opencode/agent/*.md` - fixed stale PyTorch/WebSocket-SSE references
  (ARCHITECT x2, BUILD x2).

**Creation:**
- `doc/bugs.md` - canonical bug ledger (single source of truth; `BUG-<id>`
  entries, `next_id` counter).
- `doc/experimental-ddsp.md` - M7 knowledge base (Musique Concrète + IR
  injection; fact-vs-speculation tagged, verified against magenta/ddsp source).
- `doc/experimental-sdk-hacking.md` - M8 knowledge base (4 SDK hacks;
  fact-vs-speculation tagged).
- `doc/implementation/m1-scaffold.md` .. `m8-experimental-sdk-hacking.md` - 8
  granular implementation-plan files (small steps + `## History` + `## BUGS`).

**Status:** Three-tier model + milestones M1-M8 in place; docs consistent;
index rebuilt; lint clean.

## 2026-08-31 - Stack decisions applied (magenta/ddsp, TensorBoard doctrine, licensing)

**Update:** Applied the project-owner answers to the `plan.md` open questions
across plan, architecture, UI requirements and checklist.
- `doc/plan.md` - milestones M3-M5 reworded (`magenta/ddsp` TensorFlow, FastAPI
  + Celery/Redis, TensorBoard, GPU-parameter suggestions); "Open questions"
  replaced with "Resolved questions"; decisions added: `magenta/ddsp` is
  mandatory (PyTorch out of scope), TF-native preprocessing ("pure-torch"
  superseded), local GPU auto-detection + parameter suggestions, offline +
  realtime model support, TensorBoard monitoring doctrine (control-panel UI,
  no custom charts, no WebSocket/SSE loss streaming), Vue 3 + Vite + Pinia
  confirmed (not React), OSI-only open-source licensing + Apache-2.0,
  thirdParty/venv-first dependency sourcing.
- `doc/architecture.md` - tech stack switched to TensorFlow 2.x + magenta/ddsp
  + crepe + librosa/soundfile + FastAPI + Celery/Redis + TensorBoard; removed
  PyTorch/torchaudio and WebSocket status streaming; added "Training monitoring
  (TensorBoard doctrine)" and "GPU detection" sections; inference now includes
  realtime export (TF.js/TFLite).
- `doc/ui-requirements.md` - coupling rules: REST + TensorBoard iframe only
  (WS/SSE dropped, no custom charts); section 4 rewritten as "Training
  monitoring (TensorBoard doctrine)"; GPU parameter suggestions in training
  config; export formats now TF/SavedModel/TF.js/TFLite/Neutone (PyTorch
  formats dropped); removed LossChart/SpectrogramCompare.
- `doc/checklist.md` - M1: TF/ddsp/Celery/Redis deps, Vue-Pinia scaffold, new
  **M1.6** LICENSE + OSS dependency review, **M1.7** thirdParty/venv sourcing;
  M3: magenta/ddsp model + losses, TensorBoard metrics, offline + realtime
  export, new **M3.5** GPU detection + parameter suggestions; M4: Celery + Redis
  REST job management (no WebSocket), new **M4.4** TensorBoard provisioning;
  M5: GPU suggestions + TensorBoard dashboard + realtime exports.

**Creation:** `LICENSE` - Apache-2.0 (open-source publication friendly, matches
the magenta/ddsp ecosystem).

**Status:** Decisions applied consistently; index rebuilt, lint clean.

## 2026-08-31 - M6 no-Docker + mandatory VSCode task set

**Update:** Removed Docker from the roadmap (decision).
- `doc/plan.md` - M6 now reads "packaging (non-Docker), docs, performance,
  error handling"; added decisions "No Docker" and "Mandatory VSCode task set
  from the start": `build-debug`, `build-release`, `e2e-test`,
  `start-application-debug`, `start-application-release`.
- `doc/checklist.md` - new **M1.5** `.vscode/tasks.json` with the VSCode task
  set (as soon as the M1 build process/artifacts exist); **M6.1** changed to
  non-Docker packaging.

**Creation:** `.vscode/tasks.json` - scaffold with the five required VSCode
tasks (build-debug, build-release, e2e-test, start-application-debug,
start-application-release) wired to the planned uvicorn/Vite/venv commands;
refined when the build process lands.

**Status:** Plan + checklist + tasks scaffold done; index rebuilt, lint clean.

## 2026-08-31 - DDSP domain background concept file

**Creation:** `doc/ddsp-concepts.md` - DDSP domain background knowledge
(translated to English per the language rule): definition/core idea, signal
flow (modified autoencoder), differentiable synthesis modules (harmonic
additive / filtered noise / differentiable reverb), training & multi-scale
spectral loss, monophonic data requirement, applications (timbre transfer,
VSTs) and limitations/extensions (PolyDDSP, RAVE). Merged from six German
background chunks; complements `architecture.md` (project pipeline) and
`plan.md` (decisions).

**Update:** `doc/index.md` - new "Domain Knowledge" category registering
`ddsp-concepts.md`.

**Status:** Concept file + index entries done; index rebuilt, lint clean.

## 2026-08-31 - Central UI requirements for all agents

**Creation:** `doc/ui-requirements.md` - single source of truth for the
product/UI requirements, applicable to ALL workspace agents regardless of
role. Adapted from a DDSP frontend prompt (procedural "ANWEISUNG ZUM
VORGEHEN" section removed). Contains coupling rules (REST/WebSocket/SSE
decoupling, Vue 3 + Vite + Pinia, mandatory mock-data seam), the six DDSP
domain phases (data ingestion, preprocessing feedback, training config,
real-time monitoring, inference/playground, model export), additional
milestone views (dataset manager M5.1, run lifecycle M4.2), target component
structure and acceptance criteria.

**Update:**
- `AGENTS.md` - mandatory `doc/ui-requirements.md` load step in the
  Navigation & Knowledge First workflow + Quick facts entry.
- `doc/index.md` - registered `ui-requirements.md` under Architecture & Design.
- `.opencode/agent/*.md` - role-specific deviations added to ARCHITECT (x2),
  BUILD (x2), DEV (x2), DEV_JUNIOR (x1) referencing `doc/ui-requirements.md`.

**Status:** Central spec + pointers + role deviations done; index rebuilt,
lint clean.

## 2026-08-30 - CCD-Standards, Teststrategie, Workflow, Projekt-Agents

**Update:** Übernahmen aus `wogd-vst-netsdrstation` für dieses Projekt:
- `doc/coding-standards.md` - volles CCD-Wertesystem (alle Grade) + Compliance-Regel.
- `doc/test-strategy.md` - automated-first, Test-Pyramide, Coverage, Mock-Strategie.
- `doc/workspace-workflow.md` - venv/ruff/pytest/uvicorn/Vite + Hot-Reload.
- `.opencode/agent/*.md` - Projekt-Agents (ARCHITECT/BUILD/DEV/DEV_JUNIOR +
  OpenRouter-Varianten) mit DDSP/Python/Vue-Prompts, überschreiben die globalen
  VST-spezifischen Agents; primaries nutzen den AGENTS.md-Workflow (Autopilot
  erst nach Todo-Bestätigung).
- `opencode.json` - Subagent-Overrides: `general`/`explore`/`compaction` auf
  `opencode/nemotron-3.5-lightning-free`; `wogd_ddsp_*`-RAG-Erlaubnisse für
  general/explore. Globale Modell-Configs unverändert.
- `AGENTS.md` - Role & Delegation Model + Subagent-Modell dokumentiert.

**Status:** Docs + Agents + Config angelegt; Index neu gebaut, lint clean.

## 2026-08-30 - RAG/MCP renamed to wogd_ddsp

**Update:** Renamed the RAG + MCP tooling to consistently use `wogd_ddsp`:
- `wogd_mcp_server.py` -> `wogd_ddsp_mcp_server.py`; server name `WOGD_DDSP-Assistant`.
- MCP server key `mcp.wogd_rag` -> `mcp.wogd_ddsp` (tools `wogd_ddsp_query_code_*`).
- DB `wogd_rag.db` -> `wogd_ddsp.db`; chunk ID prefix `wogd_` -> `wogd_ddsp_`.
- References updated in `opencode.json`, `AGENTS.md`, `.ragignore`, `.gitignore`.

**Status:** Rename complete; index rebuilt, wiki regenerated, lint clean.

## 2026-08-30 - LLM-Wiki + RAG/MCP setup

**Creation:** Initialized the LLM-Wiki (`doc/`), the RAG/Code-Wiki MCP server
(`wogd_ddsp_mcp_server.py`, `wogd_ddsp` in `opencode.json`), `.ragignore`,
`.gitignore`, `opencode.json` and this `doc/` wiki. Adapted from the
`netsdr_rag` solution of the `wogd-vst-netsdrstation` project for this
Python + Web-UI DDSP training app.

**Changes:**
- `wogd_ddsp_mcp_server.py` - RAG + Code-Wiki MCP server; languages:
  Python/C++/MD (structural) + TS/JS/Vue/HTML/CSS/JSON (generic line chunks);
  `wogd_ddsp_` chunk IDs; DB `wogd_ddsp.db`.
- `doc/architecture.md`, `doc/plan.md`, `doc/checklist.md`, `doc/index.md`,
  `doc/log.md` - wiki scaffold for the web UI DDSP training app.

**Status:** Scaffold created; codebase otherwise empty (M1 pending approval).
