---
type: bug-ledger
title: Bug Ledger - wogd-ddsp-trainer
description: Canonical bug tracker (single source of truth); indexed BUG-<id> entries, next_id counter
status: active
generated:
  by: primary-agent
  at: 2026-08-31
stale_after: 2026-12-31
tags: [bugs, tracking, single-source-of-truth]
---

# wogd-ddsp-trainer - Bug Ledger

_This is the **single source of truth** for all bugs in the project. A bug is
recorded in full **exactly once, here**. Every other document (implementation
plans, `log.md`) references bugs only by `BUG-<id>`._

## Rules (non-redundancy)

1. A bug is described in full **only** in this file.
2. `BUG-<id>` IDs are assigned **only** here, by incrementing `next_id` below.
3. Implementation plans keep a `## BUGS` section that lists **references only**
   (`BUG-<id>` + one-line + status), never the full record.
4. One bug = one owner milestone (the phase where it is rooted); cross-phase
   impacts are listed as `affected:` milestones on the same entry, not
   duplicated.

## Counter

`next_id: 50`

## Bug template (copy for each new bug)

```markdown
## BUG-<id> - <one-line title>
- status: open | in-progress | fixed | verified
- milestone: <owner milestone, e.g. M2>
- affected: <other milestones, optional>
- found-in: <step / commit / context>
- severity: <critical | major | minor>
- description: ...
- reproduction: ...
- resolution: <filled when fixed>
- history: <append-only, newest first>
```

---

## Wont-fix bugs

## BUG-1 - neutone_sdk pinned numpy<2.3 has no cp314 Windows wheel (py3.14)
- status: wont-fix
- milestone: M3 (export, M3.4)
- affected: M1.2
- found-in: M1.2 dependency install
- severity: major
- description: `neutone_sdk` (1.5.2) requires `numpy<2.3.0,>=1.21.6`. On Python
  3.14/Windows, numpy 2.2.x has NO cp314 wheel on PyPI (only an sdist), so pip
  attempts a Meson/source build which fails (`sccache clang cannot compile`);
  `neutone_sdk` cannot be installed into the current 3.14+cu130 environment.
  Additionally its metadata lists `License: LGPL` + an `Other/Proprietary`
  classifier — the OSI status must be verified before adoption.
- reproduction: `pip install neutone_sdk` on `.venv` (py3.14) -> build error.
- resolution: wont-fix. Neutone was rejected on **architectural** grounds (our
  export target is own PyTorch/TorchScript/ONNX; `neutone_sdk` would only wrap
  PyTorch and was not needed). M3.4 export ships via
  `inference/export.py` (`export_torchscript`, `export_onnx`);
  `export_neutone` is a stub (Neutone plugin export left as a future M5 export
  hub task, independent of this bug). `neutone_sdk` is not a runtime/first-class
  dependency and will not be reintroduced.
- history:
  - 2026-08-31 — marked `wont-fix`. Neutone rejected for architectural reasons
    (own PyTorch/TorchScript/ONNX export path); M3.4 implemented via
    `inference/export.py`; `neutone_sdk` no longer required (was `open`/deferred
    from M1.2).

## Fixed bugs

## BUG-3 - webui/src/App.vue imports RouterView as default export (release build fails)
- status: fixed
- milestone: M1 (scaffold, M1.3)
- affected: M6 (release packaging/run)
- found-in: M6.1 release build (`npm run build` -> `vite build`)
- severity: major
- description: `webui/src/App.vue` line 7 used `import RouterView from 'vue-router'`
  (a default import), but `vue-router` exposes `RouterView` only as a **named**
  export. During development Vite's on-demand transform tolerates this, but the
  production build (`vite build`) fails with `"default" is not exported by
  "node_modules/vue-router/dist/vue-router.mjs"` — breaking the M6 release
  bundle and therefore `start-application-release`.
- reproduction: `cd webui && npm run build` -> rollup error `"default" is not
  exported by "…/vue-router.mjs"`.
- resolution: (fixed) changed to a named import:
  `import { RouterView } from 'vue-router'` in `webui/src/App.vue`. `npm run build`
  now succeeds (60 modules, dist emitted). Full verification (ruff/pytest/vitest)
  recorded in `doc/log.md`.
- history:
  - 2026-08-31 — found while wiring `start-application-release` (release build
    failed); fixed the named import in `webui/src/App.vue`.
  - 2026-08-31 — **verified** as part of M6.6: `npm run build` succeeds, vitest
    18 passed, live release backend serves the built UI (root + SPA fallback).

## BUG-2 - datasets_dir() ignores existing-but-empty WOGD_DATASETS_DIR (falls back to cwd/datasets)
- status: fixed
- milestone: M4 (web backend)
- affected: M4.3 (backend tests), repo hygiene
- found-in: M4.3 backend test roundtrip (`tests/test_api_datasets.py`)
- severity: minor
- description: `server/routes/dataset.py::datasets_dir()` used
  `if env and Path(env).is_dir()` — when `WOGD_DATASETS_DIR` was set but the
  directory did not yet exist (a common case: datasets are created lazily on
  first upload), it silently fell back to `Path.cwd()/datasets`. Under tests
  this caused uploads/listings to pollute the repo `datasets/` folder and made
  per-test isolation break.
- reproduction: set `WOGD_DATASETS_DIR` to a not-yet-created path, call
  `upload_dataset` -> files written into `<cwd>/datasets` instead of the env dir.
- resolution: (fixed) `datasets_dir()` now returns `Path(env)` whenever `env` is
  set (non-empty), regardless of whether the directory already exists (the
  upload/list paths `mkdir` on demand). Covered by `tests/test_api_datasets.py`.
- history:
  - 2026-08-31 — found during M4.3 test roundtrip; fixed in `server/routes/dataset.py`.

## BUG-4 - Training Speed (FAST/NORMAL/QUALITY) fehlt als separater Parameter; UI zeigt fake GPU statt echter GPU; keine Preset+Speed-VRAM-Validierung
- status: fixed
- milestone: M6 (Polish/UI)
- found-in: M6 code review / user feedback
- severity: major
- description: Drei zusammenhängende Mängel, die als **ein Bug** behandelt werden
  (waren in M5/M6 geplant, aber nicht umgesetzt):

  **(a) Training-Speed-Parameter fehlt.** Die Backend-Funktionen
  `train/gpu.py::propose_presets()` berechnen korrekt FAST (25% VRAM), NORMAL
  (50%) und QUALITY (100% VRAM) als Built-in-Presets. Das UI bietet aber
  **keinen separaten Training-Speed-Selektor** (FAST/NORMAL/QUALITY). Die drei
  Werte sollen als unabhängiger Parameter funktionieren, der die Parameter eines
  gewählten Presets *modifiziert* — sie sind nicht die Presets selbst. FAST soll
  Training beschleunigen (auch mit Qualitätseinbussen), NORMAL = 75% VRAM = Default,
  QUALITY = 90% VRAM.

  **(b) GPU-Anzeige ist fake.** `webui/src/views/TrainingConfigView.vue` zeigt
  `"Suggested GPU: NVIDIA RTX 3060+ (12GB VRAM)"` — ein hartcodierter Platzhalter.
  Das Backend (`train/gpu.py::detect_gpus()`, `suggest_for_host()`) liest die
  echte GPU aus, aber das UI greift nicht darauf zu. Stattdessen soll die
  **aktuell installierte GPU** angezeigt werden (Name + VRAM).

  **(c) Keine Preset+Speed-VRAM-Validierung.** Das UI prüft nicht, ob ein
  gewähltes Preset + Training-Speed auf der aktuellen GPU ausführbar ist.
  Wenn die Konfiguration den verfügbaren VRAM übersteigt, soll der User einen
  Hinweis bekommen + ein Popup mit Anpassungsvorschlägen ("Anpassungen annehmen?").
- reproduction: (a) Öffne Training Config → kein Speed-Selektor. (b) Öffne
  Training Config → GPU-Abschnitt zeigt fake-Werte. (c) Wähle QUALITY-Preset auf
  einer 6-GB-GPU → keine Warnung.
- resolution: All three sub-deficiencies implemented and verified:
  - (a) Training Speed FAST/NORMAL/QUALITY radio buttons added to TrainingConfigView.vue,
    calling POST /api/host/validate-preset with speed factor modification (FAST 0.5x,
    NORMAL 0.75x, QUALITY 0.9x on hidden_size). `server/routes/host.py` provides
    `apply_speed()` + `validate_preset()` endpoint.
  - (b) GPU display now reads from GET /api/host/info (backend `suggest_for_host()`),
    showing real GPU name, total/available VRAM, and tier. Mock fixture provides
    fallback data for dev/testing.
  - (c) VRAM validation on preset selection and speed change: if `fits_gpu` is false,
    a popup overlay ("VRAM-Warnung") appears with "Anpassungen annehmen" / "Abbrechen"
    buttons. Accepting applies clamped hidden_size to the preset.
- history:
  - 2026-08-31 — angelegt als Bug (nicht Feature, da Plan-Umsetzung fehlte).
  - 2026-08-31 — **fixed** via: (a) `server/routes/host.py` with `apply_speed()` +
    `validate_preset()` + 12 backend tests; (b) `apiClient.getHostInfo()` +
    `getGPUInfo()` + `gpuHostInfoFixture` in fixtures; (c) popup overlay in
    TrainingConfigView.vue with VRAM validation on preset/speed change.
    Full check suite: pytest 151/1, vitest 23/0, ruff/format clean, build clean.

## BUG-5 - Preset-schema drift: frontend fixtures/views use AutoVC field names instead of DDSP backend schema
- status: fixed
- milestone: M5 (Web UI)
- affected: M4 (backend), M7 (experimental, any preset-driven flow)
- found-in: M1–M6 review 2026-08-31 (architecture cross-check)
- severity: major
- description: The mock fixtures (`webui/src/mocks/fixtures.js`) and
  `TrainingConfigView.vue` use AutoVC/DSP-autoencoder field names:
  `hidden_dim`, `encoder_dim`, `decoder_dim`, `postnet_dim`, `n_trees`,
  `type: 'autovc'`, `type: 'dsp-autoencoder'`. The real DDSP backend
  (`server/presets.py`, `server/tasks.py::build_training()`) uses:
  `hidden_size`, `stft_scales`, `mixed_precision`, `gradient_checkpointing`,
  `is_builtin`. Additionally, `modelsFixture` checkpoints use `.h5` (Keras)
  instead of `.pt` (PyTorch).
  The Vitest tests pass because they run against the mocks only — an actual
  backend call would fail immediately on the field mismatch.
- reproduction: Run the app against the real backend; select any built-in
  preset in TrainingConfigView → the preset dropdown filter (`type === 'autovc'`)
  finds nothing, training payload contains unknown fields.
- resolution: (fixed) All AutoVC field names removed from `webui/src/mocks/fixtures.js`
  and `TrainingConfigView.vue`; replaced with correct DDSP backend schema (`hidden_size`,
  `stft_scales`, `is_builtin`, `.pt` checkpoints). Steps M5.8.1–M5.8.3 in
  `implementation/m5-webui.md` all marked `[x]`.
- history:
  - 2026-08-31 — filed during M1–M6 review; fix steps added to m5-webui.md.
  - 2026-09-01 — **verified fixed** by ARCHITECT correctness review: `fixtures.js` and
    `TrainingConfigView.vue` contain no AutoVC field names; all DDSP fields present.
    `m5-webui.md` M5.8.1–M5.8.3 marked `[x]`.

## BUG-6 - Training Speed radio button labels show incorrect VRAM percentages
- status: fixed
- milestone: M5 (Web UI, TrainingConfigView)
- found-in: M1–M6 review 2026-08-31
- severity: minor
- description: `TrainingConfigView.vue` speed radio buttons were labeled
  `FAST (25% VRAM)` / `NORMAL (50% VRAM)` / `QUALITY (75% VRAM)`. These
  numbers described the built-in preset VRAM targets, not the speed-modifier
  factors. The actual `apply_speed()` logic in `server/routes/host.py` applies
  factors 0.50× / 0.75× / 0.90× to the preset's `hidden_size`. The QUALITY
  label was especially misleading: it showed 75% but the factor is 0.90×.
- reproduction: Open TrainingConfigView → Training Speed section → read labels.
- resolution: (fixed) Labels updated to `FAST (0.5x hidden_size, max speed)` /
  `NORMAL (0.75x, default)` / `QUALITY (0.9x, best quality)` — accurately reflecting
  the `hidden_size` multiplier factors. Step M5.8.4 in `implementation/m5-webui.md`
  marked `[x]`.
- history:
  - 2026-08-31 — filed during M1–M6 review; fix step added to m5-webui.md.
  - 2026-09-01 — **verified fixed** by ARCHITECT correctness review: labels show
    `0.5x` / `0.75x` / `0.9x` factors; no VRAM percentage text present.

## Fixed bugs

## BUG-10 - Training Config zeigt falschen freien GPU-VRAM-Wert (available_gb)
- status: fixed
- milestone: M14 (Dual-Mode Training UI + Backend Tier System)
- affected: M14, M5
- found-in: 2026-09-02, random finding in TrainingConfigView (`GpuFeasibilityBanner`)
- severity: minor
- description: Das `GpuFeasibilityBanner` in der Training-Config-Ansicht zeigt einen
  zu niedrigen `available GB`-Wert. Anzeige im UI: `GPU · 4.1 GB available · current
  config ~2.2 GB`; real sind auf der GPU (RTX 3060 Laptop) `total=6.44 GB`,
  `free=5.37 GB`. Der Backend-Wert stammt aus `server/routes/gpu.py::gpu_feasibility()`,
  der `available_vram_gb` (aus `torch.cuda.mem_get_info()`) liefert. Der fehlerhafte
  Wert entspricht dem VRAM-Stand **beim App-Start / zur Bereitzeit des
  Feasibility-Responses** — wenn zur Abfrage-Zeit Trainings-/sonstiger GPU-Kontext
  belegt war. Das Banner aktualisiert nur bei Änderungen von `activeTier`/`n_voices`/
  `use_latent`/`use_content_encoder` (und einmalig `onMounted`), nicht bei
  SQLite-`feasibility.available_gb` unabhängig vom App-Start. Zusätzliche Ursache:
  derselbe `available_vram_gb` wird beim `lifespan`-Start gemessen und zwischen
  Abrufen gecacht/veraltet geliefert.
- reproduction: GPU frei (bspw. `free=5.37 GB`), Backend frisch starten
  (`start-application-release`), Training-Config-Ansicht öffnen → Banner zeigt z.B.
  `4.1 GB available`, trotz ~5.4 GB freien VRAM zur Laufzeit.
- resolution: `server/routes/gpu.py::gpu_feasibility()` — `available_gb` auf
  `total_vram_gb` umgestellt (Training ist GPU-exklusiv; total ist der maßgebliche
  Budgetwert). Response liefert `total_gb` + `free_gb` zusätzlich. 
  `GpuFeasibilityBanner.vue` Label von „available" auf „total" angepasst.
  `tierFeasibilityFixture` aktualisiert. Commit `0a5b9bb`.
- history:
  - 2026-09-02 — filed (random finding). Wert ist veraltet/startzeitbasiert; UI zeigt
    einen VRAM-Momentaufnahme-Wert statt des aktuell freien VRAM.
  - 2026-09-02 — fix-proposal eingetragen (primary agent, Analyse).
  - 2026-09-02 — **fixed**: `available_gb`=total_vram_gb, `total_gb`+`free_gb`
    added. pytest 362/1 green, vitest 77/0 green.

## BUG-11 - Wizard-Tier-Auswahl: Advanced nicht anwählbar, obwohl VRAM-Bedarf erst durch Quality-Qualität festgelegt wird
- status: fixed
- milestone: M14 (Dual-Mode Training UI, WizardModal)
- affected: M14, M5, M-UI
- found-in: 2026-09-02, random finding im Wizard (Tier-Zielmodus-Schritt)
- severity: minor
- description: Im Wizard kann der Tier `Advanced` („PolyDDSP, latent space, voice
  conversion. Full power.") nicht angewählt werden; das UI zeigt
  `⚠ needs 6.6 GB`. Das Problem: der VRAM-Bedarf wird in diesem Schritt bereits an der
  Tier-Auswahl festgemacht (qualitätspresetabhängig `estimated_gb` für `advanced`),
  obwohl die eigentliche VRAM-Dimensionierung erst mit der **Quality/Qualität
  (FAST/NORMAL/QUALITY)** gewählt wird — diese Auswahl folgt erst **nach** der
  Tier-Auswahl. In der Folge wird `Advanced` pauschal als „braucht zu viel, also
  gesperrt" angezeigt, ohne dass der Nutzer durch Wahl einer schlankeren Quality die
  Kombination (`advanced` + kleineres preset) erlauben könnte.
- reproduction: Training starten → Wizard → Tier-Schritt: `Advanced` anklicken →
  Anzeige `⚠ needs 6.6 GB` und Tier nicht wählbar, obwohl mit einem Quality-Preset
  `FAST`/`NORMAL` niedrigerer VRAM-Bedarf für `advanced` ausreichend wäre.
- resolution: `WizardModal.vue` — `:disabled` auf Tier-Cards entfernt (alle Tiers
  wählbar); Feasibility-Prüfung auf Step 2 (Quality-Auswahl) verlagert: jede
  Quality-Card zeigt `vramFactor × estimated_gb` und wird warn/disabled, wenn
  dieser Wert `total_gb` überschreitet. Commit `aca10df`.
- history:
  - 2026-09-02 — filed (random finding).
  - 2026-09-02 — fix-proposal eingetragen.
  - 2026-09-02 — **fixed**: Tier-`:disabled` entfernt, Quality-Card VRAM-Warnung
    in Step 2. vitest 77/0 green.

## BUG-12 - Upload & Ingestion: „Upload"-Button und „Show DDSP requirements" kleben aneinander; Requirements nicht als klickbar erkennbar
- status: fixed
- milestone: M5 (Web UI, UploadIngestionView)
- affected: M5, M-UI
- found-in: 2026-09-02, random finding in Upload & Ingestion view
- severity: minor
- description: In der Ansicht Upload & Ingestion fehlt der Abstand zwischen dem
  Upload-Button und dem Link/Text „Show DDSP requirements" — sie kleben aneinander
  (Anzeige: `UploadShow DDSP requirements`). Zusätzlich ist „Show DDSP requirements"
  nicht so gestaltet, dass es als anklickbar zu erkennen ist (kein sichtbarer
  Link-/Button-Stil); es wirkt wie statischer Text.
- reproduction: Upload & Ingestion-Ansicht öffnen → im unteren/angrenzenden Bereich
  liegen „Upload" und „Show DDSP requirements" direkt aneinander; „Show DDSP
  requirements" erscheint nicht als klickbar.
- resolution: `UploadIngestionView.vue` — `.hints-toggle` CSS: `display: block`,
  `color: var(--accent)`, `text-decoration: underline`, `margin-top: 1.5rem`
  sichergestellt. Button ist visuell als klickbarer Link erkennbar und der
  Abstand zum Upload-Button ist garantiert. Commit `b91e4bc`.
- history:
  - 2026-09-02 — filed (random finding).
  - 2026-09-02 — **fixed**: CSS `.hints-toggle` auf accent-color + underline + block.
    vitest 77/0 green.

## BUG-13 - Sidebar-Menü: Abschnitte ab „Export" durcheinander; Presets gehört weder unter Training noch unter Export
- status: fixed
- milestone: M5 (Web UI, Sidebar/Navigation; `Sidebar.vue` + `ui-requirements.md`)
- affected: M5, M-UI (Gesamtnavigation)
- found-in: 2026-09-02, random finding (Sidebar-Menüstruktur prüfen)
- severity: minor
- description: Die Sidebar-Sektionen ab „Export" sind durcheinander bzw.
  unsauber gruppiert. „Presets" gehörte sachlich weder unter Training noch unter Export
  und war unter Inference & Export eingeordnet. Zusätzlich waren Morphing und
  Latent Explorer unter Experimental einsortiert, obwohl sie zu Advanced Features
  gehören.
- reproduction: Sidebar der App öffnen → Abschnitte ab „Export" sichten; „Presets"
  unter „Inference & Export" eingeordnet, obwohl es Training+Export betrifft.
- resolution: `Sidebar.vue` — Gruppen neu strukturiert: (1) Datasets &
  Preprocessing, (2) Training (Config + Dashboard), (3) Presets — eigene Gruppe,
  (4) Inference & Export (Playground + Model Export), (5) Advanced Features
  (Voice Conversion, Morphing, Latent Explorer), (6) Experimental (Reverb IR,
  F0 Editor, Component Mixer, Synth Hacks). Commit `44bc9f4`.
- history:
  - 2026-09-02 — filed (random finding).
  - 2026-09-02 — **fixed**: Sidebar neu gruppiert, Presets als eigener Abschnitt.
    vitest 77/0 green.

## BUG-14 - „Backend: error" beim Start (start-application-release), obwohl die App läuft
- status: fixed
- milestone: M5 (Web UI Gesundheits-/Statusanzeige; `HealthView`/TopBar)
- affected: M6 (Release-Start: `scripts/start-app.ps1` Release-Modus)
- found-in: 2026-09-02, random finding (nach `start-application-release`)
- severity: minor
- description: Nach dem Start per `start-application-release` wird der Backend-Status
  im UI als `error` angezeigt („Backend: error"), obwohl die Anwendung tatsächlich läuft
  (die App ist erreichbar und funktioniert). Die Statusanzeige meldet fälschlich einen
  Fehlerzustand.
- reproduction: `start-application-release`-Task starten, App öffnen → Statusanzeige
  zeigt „Backend: error", obwohl das Backend erreichbar/online ist.
- resolution: `TopBar.vue` — Health-Check mit Retry-Logik (3 Versuche,
  1 s / 2 s / 4 s Delay) in `onMounted`; bei Erfolg auf 'ok' setzen. Während
  Retry-Phase wird „Backend: starting..." angezeigt. Zusätzlich Polling-Interval
  (30 s) für spätere Status-Updates. Commit `894f30c`.
- history:
  - 2026-09-02 — filed (random finding).
  - 2026-09-02 — **fixed**: Retry-Logik + 30s Polling in TopBar.vue.
    vitest 77/0 green.

## BUG-15 - `stop-application-release`/-debug findet keine laufende Applikation (netstat locale mismatch)
- status: fixed
- milestone: M6 (Polish, VSCode Task-Set: `stop-application-release`/`-debug`)
- affected: M6, M1 (Task-Set), alle nicht-englischen Windows-Systeme
- found-in: 2026-09-02, `stop-application-release`-Task ausgeführt während App läuft
- severity: minor
- description: Wird das Backend per `start-application-release` gestartet und
  läuft sichtbar auf `:8000` (Access-Logs im Terminal), so meldet
  `stop-application-release` trotzdem `No running processes found on ports
  8000/5173/5678`. Ursache: Zeile 20 in `scripts/stop-app.ps1` filtert
  `netstat -ano` mit dem Literal `Select-String "LISTENING"`. Auf
  **nicht-englischen Windows-Installationen** (z.B. Deutsch) lautet die
  Zustandsbezeichnung aber `ABHÖREN`. Der locale-abhängige String matcht nie
  → `$conn` ist leer → der Prozess wird nie gefunden und gestoppt.
  Betroffen sind beide Modi (`stop-application-debug` + `-release`).
- reproduction: `start-application-release` starten; in einem zweiten Task-Terminal
  `stop-application-release` ausführen → `No running processes found on ports
  8000/5173/5678`, obwohl das Backend läuft.
- resolution: `scripts/stop-app.ps1` — `netstat -ano`-Pipe durch
  `Get-NetTCPConnection` (PowerShell-cmdlet, locale-unabhängig) ersetzt.
  Fallback für ältere Windows-Versionen via `netstat -ano` ohne LISTENING-Filter.
  Commit `a1614bf`.
- history:
  - 2026-09-02 — filed (random finding, Netstat-ABHÖREN vs. LISTENING
    locale-Mismatch).
  - 2026-09-02 — **fixed**: `Get-NetTCPConnection` statt netstat locale-abhängigem
    `Select-String "LISTENING"`. Commit `a1614bf`.

## Fixed bugs (continued)

## BUG-16 - Upload & Ingestion: waveform preview never appears after drag & drop
- status: fixed
- milestone: M5 (Web UI, UploadIngestionView)
- affected: M5.2, MT-A1
- found-in: 2026-09-02, manual test MT-A1
- severity: major
- description: `UploadIngestionView.vue` defines `renderWaveform(fileItem)` (line 72-94)
  which creates a WaveSurfer instance and loads `fileItem.file` via `loadBlob()`, but
  this function is **never called** after `handleDrop()`. After files are added to
  `files.value`, no code iterates the file list and invokes `renderWaveform` for each
  item. The `waveform-preview` divs render via `v-for` (line 168) but remain empty
  because `renderWaveform` is never invoked.
- reproduction: Open Upload & Ingestion → drag & drop any audio file → the file
  appears in the list but no waveform preview renders below the filename.
- resolution: Added `await nextTick()` then `renderWaveform(f)` loop after `handleDrop()`.
  Same fix in `addFilesFromInput()`.
- history:
  - 2026-09-02 — fixed by subagent (general, task_id ses_f9c05a3d2ffe9ykRb5BQCLPGjR).

## BUG-17 - Dataset Manager: file count always shows `-` (camelCase/snake_case mismatch)
- status: fixed
- milestone: M5 (Web UI, DatasetManagerView)
- affected: M5.2, MT-A1
- found-in: 2026-09-02, manual test MT-A1
- severity: major
- description: Backend `dataset_summary()` in `server/routes/dataset.py` returns
  `file_count` (snake_case). Mock fixtures in `fixtures.js` also use `file_count`.
  But `DatasetManagerView.vue` line 48 reads `ds.fileCount ?? '-'` using camelCase.
  Since neither backend responses nor mock fixtures contain a `fileCount` key, the
  column always displays `-` regardless of actual file count.
- reproduction: Open Dataset Manager → any dataset row → File Count column shows `-`.
- resolution: Changed `ds.fileCount` to `ds.file_count` in template.
- history:
  - 2026-09-02 — fixed by subagent (general, task_id ses_f9c05c648ffeN1vOhfAyRIGOgF).

## BUG-18 - Upload dialog has no name field → datasets appear as UUID in Dataset Manager
- status: fixed
- milestone: M5 (Web UI, UploadIngestionView)
- affected: M5.2, MT-A1
- found-in: 2026-09-02, manual test MT-A1
- severity: major
- description: The backend `POST /api/datasets` accepts an optional `name` form field
  (`server/routes/dataset.py` line 64), defaulting to `dataset_id` (a UUID) when not
  provided. The `UploadIngestionView.vue` never sends a `name` parameter — the upload
  form has no text input for a dataset name. As a result, the user sees the raw UUID
  (`46147676-0409-4dd7-b958-c2352ceb13cb`) as the dataset name in the Dataset Manager.
  The user explicitly needs to name datasets to select them for training.
- reproduction: Open Upload & Ingestion → drag & drop files → click Upload → navigate
  to Dataset Manager → dataset name shown as raw UUID.
- resolution: Added `<input v-model="datasetName">` to upload form + builds FormData
  with `name` field when non-empty. `restApiClient.uploadDataset()` updated to accept
  pre-built FormData.
- history:
  - 2026-09-02 — fixed (subagent + primary restApiClient.js adjustment).

## BUG-19 - No "preprocessed" status after feature extraction completes
- status: fixed
- milestone: M5 (Web UI + Backend, Dataset status lifecycle)
- affected: M5.2, MT-A2, training dataset selection
- found-in: 2026-09-02, manual test MT-A2
- severity: major
- description: After successful preprocessing feature extraction
  (`POST /api/datasets/{id}/extract-content`), the dataset status in
  `dataset_summary()` only ever returns `"uploaded"` (if files exist) or `"empty"`.
  There is no mechanism — no DB column, no sidecar file, no RPC — to mark a dataset
  as "preprocessed" / "features extracted" / "ready for training". The Dataset Manager
  therefore cannot display a distinct status for preprocessed datasets. Additionally,
  `DatasetManagerView.vue` CSS expects `.badge.idle / .badge.ready / .badge.empty`
  classes, none of which match the backend's actual status strings (`"uploaded"`).
  The user expects "preprocessed" as a visible status so they know which datasets
  are trainable.
- reproduction: Upload files → go to Preprocessing → Run Preprocessing (succeeds) →
  go to Dataset Manager → status still shows `uploaded` (or no matching badge color).
- resolution: Backend: `_preprocessed` sentinel file written after `extract-content`
  returns success; `dataset_summary()` returns `"preprocessed"` when sentinel exists.
  Frontend: added `.badge.preprocessed { background: var(--accent); color: #000; }` CSS.
- history:
  - 2026-09-02 — fixed (subagents: backend + frontend CSS).

## BUG-20 - Uploaded file list persists after successful upload (stale state)
- status: fixed
- milestone: M5 (Web UI, UploadIngestionView)
- affected: M5.2, MT-A1
- found-in: 2026-09-02, manual test MT-A1
- severity: minor
- description: After `uploadFiles()` succeeds, `files.value` is never cleared.
  The user sees the pre-upload file listing (with local waveform previews) still
  displayed below the drop zone. The success message is shown, but the stale file
  list remains visible, giving the impression that the upload hasn't completed or
  that the files are still pending. The file list should be cleared after a successful
  upload so the drop zone is ready for the next batch.
- reproduction: Upload files → success message appears → pre-upload file list still
  visible below the drop zone with waveforms.
- resolution: Added `files.value = []` after setting `uploadSuccess.value` in `uploadFiles()`.
- history:
  - 2026-09-02 — fixed by subagent (general, task_id ses_f9c05a3d2ffe9ykRb5BQCLPGjR).

## BUG-21 - UploadIngestionView: no dataset name text input
- status: fixed
- milestone: M5 (Web UI, UploadIngestionView, dataset naming)
- affected: MT-A1, dataset selection for training
- found-in: 2026-09-02, manual test MT-A1
- severity: minor
- description: The upload dialog provides a drop zone and file listing but has no
  text input for naming the dataset. The backend (`POST /api/datasets`) accepts a
  `name` form field, defaulting to the UUID when absent. The user needs to assign
  meaningful names to datasets so they can select the right one during training
  configuration. A text input should be added to the upload form so the user can
  specify a custom dataset name.
- reproduction: Open Upload & Ingestion → no name field visible → upload succeeds →
  Dataset Manager shows UUID as name.
- resolution: (same as BUG-18) Added dataset name input + FormData name field.
- history:
  - 2026-09-02 — fixed (combined with BUG-18).

## BUG-7 - `DDSPModel.load_checkpoint` crashes with `WeightsOnlyLoad` error (DDSPConfig not a safe global)
- status: fixed
- milestone: M9 (Alternative synth engines, M9.10)
- affected: M8 (M8.1.3 server wiring), M10, M11, M12 (any milestone that calls load_checkpoint)
- found-in: post-M9 correctness review 2026-09-01 (ARCHITECT)
- severity: major
- description: `DDSPModel.load_checkpoint` calls `torch.load(path, weights_only=True)` but
  `DDSPConfig` is a plain Python dataclass that is not registered as a PyTorch safe global.
  PyTorch 2.6+ changed the default for `weights_only` to `True`, and any unregistered class
  in the checkpoint raises `WeightsUnpickler error: Unsupported global: GLOBAL
  model.ddsp_model.DDSPConfig was not an allowed global`. The method therefore crashes for
  any real-world checkpoint load. The existing test `test_engine_checkpoint_tag` only
  "works" because it calls `torch.serialization.add_safe_globals([DDSPConfig])` manually
  before the `torch.load` call — the production code path does not.
- reproduction: save a checkpoint via `model.save_checkpoint(path)`, then call
  `DDSPModel.load_checkpoint(path)` → `WeightsUnpickler error`.
- resolution: Fixed in commit 4df2477. `DDSPModel.load_checkpoint` now wraps the
  `torch.load` call in `torch.serialization.safe_globals([DDSPConfig])` context manager.
  Manual `add_safe_globals` calls removed from the two tests in
  `tests/test_synths_engines.py`.
- history:
  - 2026-09-01 — filed by ARCHITECT during post-M9 correctness review.
  - 2026-09-01 — fixed in commit 4df2477 (DEV).

## BUG-9 - app startup crashes: `sqlite3.IntegrityError: UNIQUE constraint failed: presets.name`
- status: fixed
- milestone: M14 (Dual-Mode Training UI + Backend Tier System)
- affected: M4 (original presets schema), any install with a pre-M14 database
- found-in: 2026-09-02, `start-application-release` (startup during `seed_builtin_presets`)
- severity: major
- description: The `presets` table was originally created with
  `name TEXT NOT NULL UNIQUE`. M14 made builtin presets per-tier (FAST /
  NORMAL / QUALITY for every tier, deduplicated by the composite
  `(name, model_tier)`) but `CREATE TABLE IF NOT EXISTS` never alters an
  existing table, so databases created before M14 keep the stale
  `UNIQUE(name)` index. The lifespan loop in `server/main.py` seeds all five
  tiers; the first tier (standard) fits, the second tier (component) raises
  `UNIQUE constraint failed: presets.name` and the app fails to start.
- reproduction: start the app with a pre-M14 `wogd-trainer.db` (contains only
  `builtin-fast/-normal/-quality` with `model_tier='standard'` and a UNIQUE
  index on `name`) → `seed_builtin_presets(conn, bounds, tier='component')`
  → `sqlite3.IntegrityError`.
- resolution: Fixed via a schema migration in `server/db.py`
  (`_migrate_drop_presets_name_unique`, wired into `_migrate_columns`). When a
  UNIQUE index with origin `'u'` exists on `presets`, the table is rebuilt
  without it (rename → recreate with current schema → copy all rows →
  drop), preserving data incl. `model_tier` (COALESCE to `'standard'`).
  Startup then seeds the missing 12 per-tier presets. Regression test
  `tests/test_server_presets.py::test_seed_builtin_presets_on_legacy_unique_name_db`
  (RED→GREEN). Applied to the live `%LOCALAPPDATA%\wogd-ddsp-trainer` DB
  (backup `*.bak-20260902-021629`); smoke boot returns HTTP 200.
- history:
  - 2026-09-02 — filed after release-mode startup crash; root cause: legacy
    UNIQUE(name) from the M4 schema + M14 per-tier seeding.
  - 2026-09-02 — fixed (migration + regression test), pytest 362/1 GPU-skip
    green, ruff clean, live DB migrated, boot smoke-tested.

## BUG-8 - `DDSPCore.forward` sinusoidal path silently passes wrong tensor to `FilteredNoiseSynth` when `noise_magnitudes=None`
- status: fixed
- milestone: M9 (Alternative synth engines, M9.11)
- affected: M9 (any caller of DDSPCore with engine="sinusoidal")
- found-in: post-M9 correctness review 2026-09-01 (ARCHITECT)
- severity: minor
- description: In `DDSPCore.forward`, the sinusoidal engine path contains a fallback
  `noise_magnitudes if noise_magnitudes is not None else amplitudes`. When
  `noise_magnitudes` is omitted (`None`), `amplitudes` (shape `(B, T, n_harmonics)`) is
  passed to `FilteredNoiseSynth` instead of a proper noise magnitude tensor (expected
  shape `(B, T, n_noise_bins)`). No exception is raised because `FilteredNoiseSynth`
  accepts any last-dim size, but the output is semantically wrong: harmonic amplitude
  envelopes are treated as noise spectral envelopes. The bug is latent — `DDSPModel`
  always passes real `noise_magnitudes`, so no test currently triggers it — but any
  direct use of `DDSPCore` with `engine="sinusoidal"` and no `noise_magnitudes` will
  produce incorrect audio silently.
- reproduction: `DDSPCore(variant=DDSPVariant(engine="sinusoidal"))(amplitudes=amps,
  sinusoidal_freqs=freqs, noise_magnitudes=None, n_samples=N)` → output is valid but
  noise branch uses harmonic amplitudes instead of silence/zeros.
- resolution: Fixed in commit 4df2477. Sinusoidal path now defaults `noise_magnitudes`
  to a zero-tensor of shape `(B, T, n_noise_bins)` when `None` is passed.
- history:
  - 2026-09-01 — filed by ARCHITECT during post-M9 correctness review.
  - 2026-09-01 — fixed in commit 4df2477 (DEV).

## BUG-22 - Dataset name not persisted across page refresh (upload_dataset never writes name.txt)
- status: fixed
- milestone: M5 (Web UI, dataset upload lifecycle)
- affected: M5.2, MT-A1
- found-in: 2026-09-03, manual test MT-A1 retest
- severity: major
- description: `POST /api/datasets` accepts an optional `name` Form parameter and
  returns it in the upload response, but never persists it to disk. `dataset_summary()`
  reads the name from a `name.txt` file inside the dataset directory — a sidecar file
  that was never written. After the page is refreshed, `list_datasets()` → `dataset_summary()`
  falls back to `path.name` (the UUID directory name), so the user's custom name is lost.
  The `name.txt` approach exists because there is no `datasets` table in the DB — dataset
  metadata is purely filesystem-based.
- reproduction: Upload files with a custom name → Dataset Manager shows the name immediately
  → refresh the page → name reverts to UUID.
- resolution: Added `name_path.write_text(name.strip(), encoding="utf-8")` in
  `upload_dataset()` after writing files, gated on `if name:`.
- history:
  - 2026-09-03 — filed during MT-A1 manual retest; fixed inline.

## BUG-23 - No backend route to serve dataset audio files (getFirstAudioFile returns 404)
- status: fixed
- milestone: M4 (Web Backend, dataset routes)
- affected: MT-A1, MT-A2 (PreprocessingView waveform), any view loading audio
- found-in: 2026-09-03, manual test MT-A2 (waveform never loads in PreprocessingView)
- severity: major
- description: `PreprocessingView.vue` calls `apiClient.getFirstAudioFile(datasetId)` which
  returns a URL constructed as `/api/datasets/{datasetId}/{firstFilename}`. There was no GET
  route registered for this path — only `POST /{dataset_id}/f0-override/{filename}` existed
  for uploads but not for serving files. As a result, `loadWaveform()` silently fails and
  no waveform is shown in the Preprocessing view. The Dataset Manager is a table view and
  never had waveform rendering by design.
- reproduction: Open Preprocessing → select a dataset → waveform container stays empty
  (no error shown because the error is caught in a silent try/catch).
- resolution: Added `@router.get("/{dataset_id}/{filename}")` returning `FileResponse`
  with validation (dataset exists, file exists, extension allowed).
- history:
  - 2026-09-03 — filed during MT-A2 manual test; fixed inline.

## BUG-24 - dataset_summary counts feature .npy files as dataset files
- status: fixed
- milestone: M4 (Web Backend, dataset routes)
- affected: M5.2, MT-A2 (file count inflation after preprocessing)
- found-in: 2026-09-03, manual test MT-A2 (9 audio files → 19 shown in Dataset Manager)
- severity: minor
- description: After preprocessing runs, the dataset directory contains both the original
  audio files AND `.content_embedding.npy`, `.f0_hz.npy`, `.f0_confidence.npy`,
  `.loudness_db.npy` feature files. `dataset_summary()` used `path.iterdir()` filtering
  only on `p.is_file()` — counting all files including feature .npy files. 9 audio files
  become 19 total after `extract-content` + feature extraction.
  Note: 19 files is factually correct for the total file count (9 audio + 9 .content_embedding.npy
  + 1 _preprocessed sentinel), but the Dataset Manager's "File Count" column is meant to
  show how many audio files a dataset contains, not how many temporary files it has.
- reproduction: Upload 9 audio files → run preprocessing → Dataset Manager shows file_count=19.
- resolution: `dataset_summary()` now filters to `p.suffix.lower() in ALLOWED_EXTENSIONS`
  when counting audio files. Feature .npy files and the _preprocessed sentinel are excluded.
- history:
  - 2026-09-03 — filed during MT-A2 manual test; fixed inline.

## BUG-25 - PreprocessingView resultsText is a hardcoded placeholder, not real backend data
- status: fixed
- milestone: M5 (Web UI, PreprocessingView)
- affected: MT-A2
- found-in: 2026-09-03, manual test MT-A2
- severity: minor
- description: `PreprocessingView.vue` line 73 returns a hardcoded string for `resultsText`:
  `'Extraction complete: F0 range 80-400Hz, Loudness -20 to -5 dBFS'`. This is not real
  backend data — the preprocessing endpoint (`POST /api/datasets/{id}/extract-content`) does
  not return F0 range or loudness statistics, and the UI never requests them. The text is
  always the same regardless of what was actually extracted. After preprocessing completes,
  the user sees this fake diagnostic text, which is misleading.
- reproduction: Upload any audio → Preprocessing → Run Preprocessing → results show
  "F0 range 80-400Hz" regardless of actual content.
- resolution: Fixed in PreprocessingView.vue: added `preprocessingResult` ref; `runPreprocessing` captures `result?.message || result?.status || null`; `resultsText` computed now shows the real API response, falling back to generic `'Extraction complete.'` if no message is returned.
- history:
  - 2026-09-03 — filed during MT-A2 manual test; marked open.
  - 2026-09-03 — fixed by ARCHITECT_Openrouter (Batch 1D subagent).

## BUG-27 - numba.core.byteflow DEBUG spam fills log file (99.9% noise, drowns real signals)
- status: fixed
- milestone: M6 (Polish, logging)
- affected: M6, debugging/troubleshooting
- found-in: 2026-09-03, manual debug log analysis during MT-A1/MT-A2 retest
- severity: minor
- description: The debug log file `%LOCALAPPDATA%\wogd-ddsp-trainer\logs\app-debug.log` is ~60KB
  but nearly all content is `DEBUG`-level bytecode dumps from `numba.core.byteflow`. Of 540+ lines,
  only ~30 lines are actual application log entries (upload/extract/delete events). The numba
  trace output has no diagnostic value for the wogd application and actively harms debugging by
  drowning out useful signals.
- reproduction: Start app in debug mode → any operation that triggers numba JIT compilation
  (e.g., librosa loading) → log file fills with bytecode dumps.
- resolution: Added `logging.getLogger("numba").setLevel(logging.WARNING)` in `setup_logging()`.
- history:
  - 2026-09-03 — filed and fixed inline.

---

## Open bugs — Full Project Analysis 2026-09-03

## BUG-28 - DDSPDataset 4-tuple vs Trainer DataLoader 3-tuple unpack crashes training
- status: fixed
- milestone: M3 (training loop / DataLoader integration)
- affected: M4, M5 (any training run with a real dataset_id)
- found-in: Full project analysis 2026-09-03 (cross-check loader.py vs trainer.py)
- severity: critical
- description: `dataset/loader.py::DDSPDataset.__getitem__` returns a **4-tuple**
  `(f0_t, loudness_t, audio_t, content_t)` (see line 135). The DataLoader path in
  `train/trainer.py::run()` unpacked the batch as:
  `f0_batch, loudness_batch, audio_batch = next(loader_iter)` (line 314) — only 3 targets.
  When a dataset with (or without) content embedding is loaded via a real `DDSPDataset`,
  Python raises `ValueError: too many values to unpack (expected 3)` at the first training
  step, crashing the entire training job. The synthetic fallback (`build_tensors`) is
  unaffected because it returns raw tensors, not 4-tuples.
- reproduction: Create a run with a valid `dataset_id` and an extracted FeatureCache
  on disk → `run_training_job` creates `DDSPDataset`, wraps in `DataLoader`, `trainer.run()`
  starts, first `next(loader_iter)` raises `ValueError`.
- resolution: Fixed `train/trainer.py` line 314: `f0_batch, loudness_batch, audio_batch, *_ = next(loader_iter)`. Updated docstring to reflect 4-tuple.
- history:
  - 2026-09-03 — filed during full project analysis.
  - 2026-09-03 — fixed by ARCHITECT_Openrouter (Batch 1I subagent).

## BUG-29 - PreprocessingView passes dataset name (not id/UUID) to backend calls
- status: fixed
- milestone: M5 (Web UI, PreprocessingView)
- affected: M5.2, MT-A2 (Preprocessing workflow)
- found-in: Full project analysis 2026-09-03 (view code review)
- severity: critical
- description: `PreprocessingView.vue` line 87 uses `:value="ds.name"` in the dataset
  `<option>` elements. `ds.name` is the human-readable dataset name (e.g. "My Voice Dataset"),
  NOT the UUID dataset ID. `selectedDataset.value` is then passed directly to
  `apiClient.preprocessDataset(selectedDataset.value)` and
  `apiClient.getFirstAudioFile(selectedDataset.value)`. Both methods use this value as the
  `dataset_id` path parameter in API calls (`/api/datasets/{id}/extract-content`,
  `/api/datasets/{id}`). The backend will return 404 for any dataset whose name differs
  from its directory UUID.
- reproduction: Upload any dataset with a custom name → navigate to Preprocessing → select
  the dataset → click "Run Preprocessing" → HTTP 404 from backend.
- resolution: Fixed PreprocessingView.vue: changed `:value="ds.name"` to `:value="ds.id"` and `:key="ds.name"` to `:key="ds.id"` in the option loop.
- history:
  - 2026-09-03 — filed during full project analysis.
  - 2026-09-03 — fixed by ARCHITECT_Openrouter (Batch 1D subagent).

## BUG-30 - No full DDSP preprocessing pipeline endpoint — training always falls back to synthetic data
- status: fixed
- milestone: M4 (Web Backend, dataset preprocessing pipeline)
- affected: M3 (training), M4, M5 (UI preprocessing flow), all real training runs
- found-in: Full project analysis 2026-09-03 (tasks.py vs dataset routes cross-check)
- severity: critical
- description: `server/tasks.py::run_training_job()` checks if a `FeatureCache` with
  `key="train"` exists in the dataset directory. If it does, a `DDSPDataset` is created;
  otherwise the job falls back to synthetic data. However, there is **no HTTP endpoint**
  that runs the full DDSP preprocessing pipeline: audio loading → 16 kHz resample → F0
  extraction → loudness extraction → train/val split → `save_features()` → `FeatureCache`
  write. The only preprocessing endpoint (`POST /api/datasets/{id}/extract-content`) only
  extracts HuBERT content embeddings (for M13 voice conversion), not the core F0/loudness
  features that the `FeatureCache`/`DDSPDataset` requires.
  As a result, **every training run falls back to synthetic data**, regardless of what
  dataset was uploaded and preprocessed via the UI.
- reproduction: Upload audio files → run preprocessing via UI → start a training run with
  the dataset → check logs: "cache not found for dataset_id=..., using synthetic data".
- resolution: Added `POST /api/datasets/{id}/preprocess` endpoint (async Celery task `run_preprocessing_job`) that extracts F0+loudness for all audio files and writes FeatureCache train/val splits. Also added `run_preprocessing_job` Celery task in server/tasks.py.
- history:
  - 2026-09-03 — filed during full project analysis.
  - 2026-09-03 — fixed by ARCHITECT_Openrouter (Batch 2A+2B subagents).

## BUG-31 - PreprocessingView: waveform never loads after dataset selection
- status: fixed
- milestone: M5 (Web UI, PreprocessingView)
- affected: M5.2
- found-in: Full project analysis 2026-09-03 (view code review)
- severity: minor
- description: `PreprocessingView.vue` defines `loadWaveform()` (lines 35–56) which
  creates a WaveSurfer instance and loads the first audio file from the selected dataset.
  However, the `<select>` dropdown at line 82–89 has `@change="selectedDataset = ($event.target.value)"` — 
  it only updates the reactive ref, it does NOT call `loadWaveform()`. The waveform
  container therefore always remains empty after dataset selection.
  Additionally, there is no `@change` watcher or `watch()` call that triggers `loadWaveform`
  when `selectedDataset` changes.
- reproduction: Open Preprocessing → select any dataset → waveform container stays blank.
- resolution: Fixed PreprocessingView.vue `@change` handler to also call `loadWaveform()` after setting `selectedDataset`.
- history:
  - 2026-09-03 — filed during full project analysis.
  - 2026-09-03 — fixed by ARCHITECT_Openrouter (Batch 1D subagent).

## BUG-32 - TrainingDashboardView shows undefined for run epoch/loss/max_epochs
- status: fixed
- milestone: M5 (Web UI, TrainingDashboardView)
- affected: M5.4, M4 (run lifecycle)
- found-in: Full project analysis 2026-09-03 (view vs backend API response cross-check)
- severity: major
- description: `TrainingDashboardView.vue` displays `run.epoch`, `run.max_epochs`, and
  `run.loss` (lines 165–168 and 186–188). The backend `run_get()` / `run_all()` responses
  from the DB contain: `{run_id, name, status, config, dataset_id, created_at, updated_at, error}`.
  None of the displayed fields (`epoch`, `max_epochs`, `loss`) exist in the backend response.
  They will all render as `undefined`. The epoch progress bar (`epoch-bar-fill`) calculates
  `(run.epoch / run.max_epochs) * 100` which evaluates to `NaN` → bar shows 0% always.
- reproduction: Start a training run → open Training Dashboard → run card shows "Epoch: undefined / undefined" and "Loss: undefined".
- resolution: Fixed TrainingDashboardView.vue: replaced `run.epoch`/`run.max_epochs`/`run.loss`/`run.dataset` with `run.latest_step`, `run.config?.max_steps`, `run.error`, `run.dataset_id`. Also added `current_step`/`last_loss` DB columns (BUG-40).
- history:
  - 2026-09-03 — filed during full project analysis.
  - 2026-09-03 — fixed by ARCHITECT_Openrouter (Batch 1E + Batch 2C subagents).

## BUG-33 - TrainingDashboardView: Resume button never shown for stopped runs
- status: fixed
- milestone: M5 (Web UI, TrainingDashboardView)
- affected: M5.4, M4 (run lifecycle)
- found-in: Full project analysis 2026-09-03 (view code review vs backend lifecycle vocab)
- severity: major
- description: `TrainingDashboardView.vue` shows the Resume button only when
  `run.status === 'idle' || run.status === 'failed'` (line 203). The backend run lifecycle
  vocabulary is `pending → running → stopping/stopped → completed/failed` (per
  `architecture.md`). The status `'idle'` is **not used** by the backend — user-stopped
  runs become `'stopped'`, not `'idle'`. As a result, the Resume button is never shown
  for a stopped run (only for `'failed'` runs).
- reproduction: Start a run → stop it via the Stop button → run.status becomes `'stopped'`
  → expand the run card → no Resume button visible.
- resolution: Fixed resume button condition from `run.status === 'idle'` to `run.status === 'stopped' || run.status === 'failed'`. Added `.badge.stopped` CSS rule.
- history:
  - 2026-09-03 — filed during full project analysis.
  - 2026-09-03 — fixed by ARCHITECT_Openrouter (Batch 1E subagent).

## BUG-34 - scripts/sync-wiki.py: 2 ruff E402 violations (module-level imports not at top)
- status: fixed
- milestone: M1 (Scaffold, ruff/code quality)
- affected: M1.4 (check commands), Definition of Done
- found-in: Full project analysis 2026-09-03 (ruff check)
- severity: minor
- description: `scripts/sync-wiki.py` has 2 `E402` violations: `from mcp_rag import ProjectRAG`
  and `from mcp_rag import wiki as ragwiki` are placed after a `sys.path.insert()` guard
  (which must be before the imports), but ruff still flags them as "module level import not
  at top of file". The file is included in ruff's scan. While not in the main package,
  `ruff check` (the DoD check) reports these 2 errors, technically meaning the codebase
  is NOT lint-clean.
- reproduction: `.venv\Scripts\python.exe -m ruff check` → reports 2 E402 errors in
  `scripts/sync-wiki.py`.
- resolution: Added `# noqa: E402` to the two import lines (17-18) in `scripts/sync-wiki.py`.
- history:
  - 2026-09-03 — filed during full project analysis.
  - 2026-09-03 — fixed by ARCHITECT_Openrouter (Batch 1A subagent).

## BUG-35 - test_losses.py / test_model.py use deprecated torch.testing.assert_allclose
- status: fixed
- milestone: M3 (Model + training, tests)
- affected: M3.5 (test quality)
- found-in: Full project analysis 2026-09-03 (pytest warning output)
- severity: minor
- description: `tests/test_losses.py` (lines 65, 76) and `tests/test_model.py` (line 53)
  use `torch.testing.assert_allclose()`, deprecated since PyTorch 1.12 with a FutureWarning:
  "will be removed in a future release. Please use `torch.testing.assert_close()` instead."
  These warnings appear in every `pytest` run (3 occurrences) and contribute noise to the
  test output. The replacement API `torch.testing.assert_close()` has been available since
  1.9.
- reproduction: `.venv\Scripts\python.exe -m pytest tests/test_losses.py tests/test_model.py`
  → FutureWarning on 3 calls.
- resolution: Replaced all `torch.testing.assert_allclose(...)` calls with `torch.testing.assert_close(...)` in `tests/test_losses.py` (2 calls) and `tests/test_model.py` (1 call).
- history:
  - 2026-09-03 — filed during full project analysis.
  - 2026-09-03 — fixed by ARCHITECT_Openrouter (Batch 1B+1C subagents).

## BUG-36 - main.py: duplicate @app.get("/") routes; /api/health and /api/tensorboard registered after SPA wildcard in release mode
- status: fixed
- milestone: M6 (Polish, release packaging)
- affected: M6.1, M6.5, release mode startup
- found-in: Full project analysis 2026-09-03 (route order inspection with WOGD_SERVE_STATIC=1)
- severity: major
- description: When `WOGD_SERVE_STATIC=1`, `mount_frontend(app, FRONTEND_DIST)` is called
  at module level (line 121), which registers two routes: `@app.get("/")` for `index.html`
  and `@app.get("/{_:path}")` as SPA fallback. Directly after, lines 124–141 register
  another `@app.get("/")` (the JSON health root), `@app.get("/api/health")`, and
  `@app.get("/api/tensorboard")` — all of which are added AFTER the SPA fallback.
  Route inspection confirms the order: `/`, `/{_:path}` (from mount_frontend) appear before
  `/` (root), `/api/health`, `/api/tensorboard`. FastAPI/Starlette resolves routes in
  registration order: for the path `/api/health`, the `/{_:path}` wildcard **may** match
  before the specific `/api/health` route, depending on Starlette's path specificity logic.
  Confirmed duplicate `/` routes. The `root()` health JSON (line 124) would be shadowed by
  the frontend `index()`.
- reproduction: Start with `WOGD_SERVE_STATIC=1` → `GET /` returns `index.html` (correct),
  but there is ambiguity; `GET /api/health` may return `index.html` if the wildcard fires
  first. The `TopBar.vue` health check uses `/api/health`.
- resolution: Moved `@app.get("/")`, `/api/health` and `/api/tensorboard` endpoint registrations to immediately after `install_handlers(app)` and BEFORE the `mount_frontend()` / `_SERVE_STATIC` block. SPA wildcard is now always the last registered route.
- history:
  - 2026-09-03 — filed during full project analysis.
  - 2026-09-03 — fixed by ARCHITECT_Openrouter (Batch 1H subagent).

## BUG-37 - Trainer.load_checkpoint uses weights_only=False (inconsistent safety; arbitrary pickle)
- status: fixed
- milestone: M3 (training, checkpointing)
- affected: M3.3 (checkpoint safety), security
- found-in: Full project analysis 2026-09-03 (trainer.py vs ddsp_model.py cross-check)
- severity: minor
- description: `DDSPModel.load_checkpoint` was fixed in BUG-7 to use a
  `torch.serialization.safe_globals([DDSPConfig])` context manager with `weights_only=True`
  (the safe default in PyTorch ≥ 2.6). However, `Trainer.load_checkpoint` (line 376 of
  `train/trainer.py`) still uses `torch.load(path, map_location=self.device, weights_only=False)`.
  `weights_only=False` allows arbitrary pickle deserialization from the checkpoint file.
  If a malicious or corrupted checkpoint is loaded, this is a potential code execution
  vector. The inconsistency also means the two load paths have different security properties.
- reproduction: Provide a crafted `.pt` file with a malicious pickle payload → `Trainer.load_checkpoint()`
  will execute arbitrary Python code; `DDSPModel.load_checkpoint()` would not.
- resolution: Changed `torch.load(..., weights_only=False)` to `weights_only=True` in `Trainer.load_checkpoint`. Trainer checkpoints only contain safe primitives (no live dataclass objects), so no `safe_globals` context manager is needed.
- history:
  - 2026-09-03 — filed during full project analysis.
  - 2026-09-03 — fixed by ARCHITECT_Openrouter (Batch 1I subagent).

---

## Open feature requests — Full Project Analysis 2026-09-03

## BUG-38 - FEAT: Redis health check at startup / health endpoint
- status: fixed
- milestone: M4 (Web Backend, operational quality)
- found-in: Full project analysis 2026-09-03
- severity: minor
- description: The app uses Celery+Redis for all training and synthesis jobs, but there is
  no Redis reachability check at startup or in the health endpoint. When Redis is not running,
  the app starts normally (no error), but any attempt to submit a training job silently fails
  or hangs. The `/api/health` endpoint only reports `{"status": "ok"}` without checking
  Celery/Redis availability. Operators and users get no actionable feedback.
- resolution: Added Redis ping (2s timeout) in lifespan startup in `server/main.py`. Logs `WARNING` if unreachable. App still starts normally so offline dev is not blocked.
- history:
  - 2026-09-03 — filed as feature request during full project analysis.
  - 2026-09-03 — implemented by ARCHITECT_Openrouter (Batch 1H subagent).

## BUG-39 - FEAT: Async preprocessing pipeline with status polling
- status: fixed
- milestone: M4 / M5 (Backend + UI, preprocessing workflow)
- found-in: Full project analysis 2026-09-03 (related to BUG-30)
- severity: minor
- description: Once BUG-30 is resolved (full preprocessing endpoint), the preprocessing
  pipeline (F0 extraction via CREPE, loudness, content embeddings, FeatureCache write)
  will be long-running for large datasets (minutes). Running this synchronously in the
  HTTP request handler will timeout. It should be implemented as a Celery task with a
  status/progress endpoint that the UI polls, similar to the inference job pattern
  (`/api/inference/jobs/{id}`). The preprocessing view should show a progress bar based
  on the number of processed files out of total.
- resolution: Implemented `run_preprocessing_job` Celery task in `server/tasks.py` and `POST /api/datasets/{id}/preprocess` endpoint in `server/routes/dataset.py`. Endpoint submits async job, returns task_id immediately. Dataset status can be polled via `GET /api/datasets/{id}` (status field becomes `preprocessed` when done).
- history:
  - 2026-09-03 — filed as feature request during full project analysis.
  - 2026-09-03 — implemented by ARCHITECT_Openrouter (Batch 2A+2B subagents).

## BUG-40 - FEAT: Real training step/epoch progress stored in DB and shown in Dashboard
- status: fixed
- milestone: M4 / M5 (Backend + UI, training progress)
- found-in: Full project analysis 2026-09-03 (related to BUG-32)
- severity: minor
- description: The `runs` DB table has no column for current training step, loss, or epoch.
  The Celery training task writes checkpoints and TensorBoard logs, but does not update the
  DB with live progress. The training dashboard's run cards cannot show meaningful progress
  (BUG-32). TensorBoard provides the loss curves, but a lightweight current-step indicator
  in the run card would improve usability for users who don't want to open TensorBoard.
- resolution: Added `current_step INTEGER DEFAULT 0` and `last_loss REAL` columns to runs table (with migration). Added `run_update_progress()` DB helper. `_watch_stop_request` thread in `run_training_job` writes progress every 0.5s. Exposed via `list_runs` and `get_run` responses. Dashboard reads `run.latest_step` and `run.config?.max_steps`.
- history:
  - 2026-09-03 — filed as feature request during full project analysis.
  - 2026-09-03 — implemented by ARCHITECT_Openrouter (Batch 1G + 2A + 2C subagents).

## BUG-41 - FEAT: Preset "rebase" dialog — warn and migrate when preset.model_tier ≠ active tier
- status: fixed
- milestone: M14 (Dual-Mode Training UI, Preset system compatibility)
- found-in: Full project analysis 2026-09-03 (ui-requirements.md §Preset system compatibility cross-check)
- severity: minor
- description: `ui-requirements.md` §Preset system compatibility explicitly requires:
  "When a preset's model_tier does not match the active tier, the UI shows a Rebase warning:
  'This preset was created for a different model type — transfer the compatible parameters?'
  The user can accept (rebase) or cancel." This dialog is specified but not implemented in
  any of the Tab components or `TrainingConfigView.vue`. When the user selects a preset
  from a different tier, the mismatch is surfaced via `model_tier_mismatch: bool` in the
  `/api/runs/validate` response, but the UI ignores this field.
- resolution: Added tier-mismatch inline warning banner in `TrainingConfigView.vue`. When `/api/runs/validate` returns `model_tier_mismatch: true`, the banner appears with "Proceed anyway" / "Cancel" buttons. Fixed `handleStartTraining` to use correct validate response shape (no `.valid`/`.errors` — backend returns `params`/`clamped_fields`/`model_tier_mismatch`).
- history:
  - 2026-09-03 — filed as feature request during full project analysis.
  - 2026-09-03 — implemented by ARCHITECT_Openrouter (Batch 3 subagent).

## BUG-42 - FEAT: Dataset deletion should warn when active runs reference the dataset
- status: fixed
- milestone: M5 (Web UI, DatasetManagerView)
- found-in: Full project analysis 2026-09-03
- severity: minor
- description: `DELETE /api/datasets/{id}` and `DatasetManagerView.vue` delete a dataset
  without checking whether any training runs have `dataset_id` set to the deleted dataset.
  Deleting such a dataset leaves orphaned run references in the DB. If the run is later
  resumed, the missing dataset causes the training job to silently fall back to synthetic
  data (per the current tasks.py fallback) or to crash.
- resolution: Added cascade check to `DELETE /api/datasets/{id}` in `server/routes/dataset.py`. Returns 409 with active run IDs if any runs with status `pending`/`running`/`stopping` reference the dataset. Supports `?force=true` query param to override.
- history:
  - 2026-09-03 — filed as feature request during full project analysis.
  - 2026-09-03 — implemented by ARCHITECT_Openrouter (Batch 2B subagent).

## BUG-43 - batch_size hardcoded to 1 regardless of VRAM budget — wastes 70-80% of GPU capacity
- status: fixed
- milestone: M3 (training loop / DataLoader / preset system)
- affected: M4, M5, M14 (all training runs), MT-A4
- found-in: 2026-09-03, MT-A4 manual test (RTX 3060 6.44 GB, QUALITY standard preset)
- severity: major
- description: `batch_size` is hardcoded to `1` in two places — the Pinia store default (`webui/src/stores/modelConfig.js:13`) and `server/tasks.py:342` (`DataLoader(ds, batch_size=1, ...)`). It is **not part of the preset system** at all: `ParameterBounds`, `propose_presets()`, `build_builtin_presets()`, the speed factors (`apply_speed()`), and `validate_preset()` all ignore `batch_size`.

  On an RTX 3060 (6.44 GB total, 5.37 GB free, hidden_size=256 in QUALITY standard), the model easily fits batch size 4-8. With `batch_size=1`, 70-80% of VRAM sits unused — training takes 4-8x longer than necessary.

  The VRAM estimation infrastructure (`estimate_model_vram()` in `train/gpu.py`) already computes VRAM per sample. Computing `max_batch_size = floor(free_vram / vram_per_sample)` is straightforward but unimplemented. The speed system (FAST/NORMAL/QUALITY) scales `hidden_size`, `stft_scales`, `mixed_precision`, and `gradient_checkpointing` — never `batch_size`.

- reproduction: Open TrainingConfigView with any preset on a GPU with >4 GB VRAM → Batch Size field shows `1` regardless of selected tier, speed, or available VRAM. Start training → DataLoader runs with `batch_size=1` → GPU utilization is minimal.
- resolution: Added `batch_size_max` to `ParameterBounds` (low=2, mid=4, high=8, ultra=16); `propose_presets()` now includes `batch_size` scaled by speed factor; `clamp_params()` clamps it; `apply_speed()` scales it; DataLoader reads from run config. Fixed in commit eb4e0e1.
- history:
  - 2026-09-03 — filed after MT-A4 manual test analysis.
  - 2026-09-03 — fixed in commit eb4e0e1 (ParameterBounds + propose_presets + clamp_params + apply_speed + tasks.py DataLoader).

## BUG-44 - Training Config preset dropdown shows "-- Select Preset --" after wizard; "Built-In" optgroup confusing
- status: fixed
- milestone: M5 (Web UI, TrainingConfigView / TabCore)
- affected: MT-A4
- found-in: 2026-09-03, MT-A4 manual test
- severity: minor
- description: Two related UI problems in TabCore's preset dropdown:

  **(a) "-- Select Preset --" shown after wizard completes.** After the wizard selects a preset (FAST/NORMAL/QUALITY) and the user reaches the Core tab, the dropdown displays "-- Select Preset --" as if nothing was chosen. It should show the wizard-generated preset (e.g. "NORMAL (wizard)") so the user can see what was selected. "-- Select Preset --" is confusing because it implies no preset is active.

  **(b) "Built-In" optgroup is shown but not usable.** The `<optgroup label="Built-in">` lists `FAST/NORMAL/QUALITY` as selectable options, but selecting one does not actually apply the preset's params to the form — the dropdown only updates `selectedPresetName` in TabCore, which is disconnected from the store. The user has no way to know what "Built-In" means or how to use it. The built-in presets are already applied by the wizard and should either be hidden or clearly marked as read-only info.
- reproduction: Complete wizard → Core tab shows "-- Select Preset --" in the dropdown. Click dropdown → "Built-In" group shows FAST/NORMAL/QUALITY → selecting any of them does nothing visible.
- resolution: TabCore.vue: `selectedPresetName` initialized from `store.selectedPreset`; "-- Select Preset --" hidden via v-if when wizard active; selecting built-in options applies params to store via Object.assign; "(wizard-generated)" badge shown. Fixed in commit eb4e0e1.
- history:
  - 2026-09-03 — filed after MT-A4 manual test.
  - 2026-09-03 — fixed in commit eb4e0e1 (TabCore.vue preset dropdown watch + badge).

## BUG-45 - Preprocessing result shows only file count, no F0/loudness diagnostics
- status: open
- milestone: M5 (Web UI, PreprocessingView + Backend extract-content)
- affected: MT-A2, MT-A4
- found-in: 2026-09-03, MT-A4 manual test (realized after "Processed 3 audio files" feedback)
- severity: minor
- description: The preprocessing result now shows `"Processed 3 audio files"` (BUG-25 fix + BUG-31 follow-up removed the hardcoded fake text). The user wants the rich diagnostic info that was previously hardcoded (F0 range, loudness range) — but computed from real extracted data instead of being fake.

  The backend endpoint `POST /api/datasets/{id}/extract-content` (and the async `POST /api/datasets/{id}/preprocess`) do not compute or return F0/loudness statistics. Computing `min_f0_hz`, `max_f0_hz`, `min_loudness_db`, `max_loudness_db` across all processed files and returning them in the response would allow the frontend to display e.g. `"F0 98–412 Hz · Loudness -22.1 to -4.3 dBFS · 3 files"`.

- reproduction: Upload audio → Preprocessing → Run Preprocessing → result shows only "Processed 3 audio files".
- resolution: (open)
- history:
  - 2026-09-03 — filed after user feedback: preprocessing output too sparse, wants F0 + loudness diagnostics back (real stats, not hardcoded).

## BUG-46 - FEAT: Rename "⚙ Reconfigure Model" button to "⚙ Start Config Wizard"
- status: open
- milestone: M5 (Web UI, TrainingConfigView)
- found-in: 2026-09-03, user feedback
- severity: minor
- description: The button text `⚙ Reconfigure Model` in TrainingConfigView is misleading — it doesn't reconfigure an existing model (there is none yet at config time). It opens the wizard to (re-)start the model setup process. Should be `⚙ Start Config Wizard` to clearly communicate what it does.
- reproduction: Open Training Config → see button "⚙ Reconfigure Model" → confusing because no model exists yet.
- resolution: (open)
- history:
  - 2026-09-03 — filed as feature request.

## BUG-47 - Wizard shows "fits 2.2 GB" for all tiers — estimate_model_vram ignores non-advanced tier differences
- status: open
- milestone: M14 (Dual-Mode Training UI, Backend VRAM estimation)
- affected: M14.1.1, MT-A4 (wizard tier selection)
- found-in: 2026-09-03, MT-A4 manual test (wizard shows every tier with "✓ fits 2.2 GB")
- severity: major
- description: `train/gpu.py::estimate_model_vram()` at line 256-257 states:
  "All tiers from 'standard' through 'engine' have the same baseline; 'advanced' activates the optional overhead params."

  This means every tier returns exactly 2.2 GB when called with default params:
  - `estimate_model_vram("standard")` → 2.2 GB
  - `estimate_model_vram("component")` → 2.2 GB
  - `estimate_model_vram("hacks")` → 2.2 GB
  - `estimate_model_vram("engine")` → 2.2 GB
  - `estimate_model_vram("advanced")` → 2.2 GB (only changes with addons)

  In reality the tiers add real model components that consume VRAM:
  - **component** adds component mixer (denormalize layer, balance sliders) → ~+0.1 GB
  - **hacks** adds variant processing (waveform/FM/phase distortion branches) → ~+0.15 GB
  - **engine** adds alternative synth backends (sinusoidal, comb-sub, NEWT) → ~+0.2 GB
  - **advanced** baseline with n_voices=1 should be ~+0.3 GB over standard for the latent/VC plumbing even without addons active

  The wizard calls `estimate_model_vram(t)` for each tier with default params and displays "✓ fits 2.2 GB" for all five — making the feasibility information completely useless and misleading.

- reproduction: Open wizard → step "Select Model Tier" → every card shows "✓ fits 2.2 GB".
- resolution: (open)
- history:
  - 2026-09-03 — filed after MT-A4 manual test. Root cause: `estimate_model_vram` needs per-tier baseline deltas beyond the single 2.2 GB constant.

## BUG-48 - Batch Size field still shows 1 despite BUG-43 fix — preset params don't reach coreParams
- status: open
- milestone: M3 (training loop / DataLoader / preset system)
- affected: M5, M14 (all training config UI), MT-A4
- found-in: 2026-09-03, MT-A4 retest after BUG-43 fix
- severity: major
- description: BUG-43 added `batch_size` to `propose_presets()` output, `clamp_params()`, `apply_speed()`, and DataLoader config reading. However the Batch Size input field still shows `1` (the store default) after wizard completion.

  Root causes:
  1. **Mock fixtures missing batch_size** (`webui/src/mocks/fixtures.js:78-79`): `presetsFixture` built-in presets have params with `hidden_size`, `stft_scales`, `mixed_precision`, `gradient_checkpointing` — but no `batch_size`. When TabCore's watch finds the preset and applies params via `Object.assign(store.coreParams, preset.params)`, `batch_size` is not overwritten. This affects dev/test mode with MockApiClient.
  2. **Timing gap** in `TabCore.vue` watch: `watch(presets, ..., { immediate: true })` fires immediately with empty array → can't find preset → no params applied. When API data arrives, the second fire should apply params — but if the API response also lacks batch_size (e.g. stale DB seed), the value stays 1.

- reproduction: Complete wizard → Core tab shows Batch Size = 1 even for QUALITY on a 6 GB GPU where preset should suggest batch_size=4.
- resolution: (open)
- history:
  - 2026-09-03 — filed after MT-A4 retest. User confirms batch_size still shows 1 despite BUG-43 backend changes.

## BUG-49 - Start Training fails with HTTP 422: missing required "name" field; no dataset selection; error message overflows text box
- status: open
- milestone: M5 (Web UI, TrainingConfigView + store + WizardModal)
- affected: MT-A4, any training start
- found-in: 2026-09-03, MT-A4 training start attempt
- severity: major
- description: Three related issues:

  **(a) HTTP 422 on Start Training.** The backend `RunCreateRequest` (`server/routes/training.py:31-32`) requires `name: str` as a mandatory field. The frontend `store.buildFullConfig()` (`webui/src/stores/modelConfig.js:58`) does not include a `name` field. When the user clicks "▶ Start Training", `TrainingConfigView.vue` calls `apiClient.startRun(config)` with the config object — but there's no `name`, so the backend returns 422:

  ```
  {"detail":[{"type":"missing","loc":["body","name"],"msg":"Field required","input":{...}}]}
  ```

  The run should either auto-generate a name from the tier/preset (e.g. "standard-NORMAL-realtime") or the UI should ask for a run name. The error is opaque to the user.

  **(b) No dataset selection before training.** The backend `RunCreateRequest` accepts `dataset_id: str | None = None` (optional, falls back to synthetic data), but the frontend never sends a `dataset_id` — `store.buildFullConfig()` has no `dataset_id` field and there is no UI element anywhere (neither in the wizard nor in the Core tab) to select a dataset for training. The user must be able to choose which dataset to train on.

  **Requirement:** Add a dataset dropdown in the wizard (as a new step or integrated into an existing step) and in the Core tab. When the wizard selects a dataset, the Core tab dropdown should be pre-filled with that choice but allow changing to another dataset. When no wizard was used (or no dataset was chosen in the wizard), show "--- Select Dataset ---".

  **(c) Error message overflow.** The validation result `<div>` with class `.validation-result.err` has no `overflow` or `max-height` handling — when the error message is a long JSON 422 string, it grows beyond the red box boundaries or stretches the layout awkwardly. The container should expand vertically with the content (or scroll).

- reproduction: Complete wizard → verify fields → click "▶ Start Training" → HTTP 422 popup shows raw API error in cramped red box. No dataset can be selected anywhere for training.
- resolution: (open)
- history:
  - 2026-09-03 — filed after MT-A4 training start attempt.
