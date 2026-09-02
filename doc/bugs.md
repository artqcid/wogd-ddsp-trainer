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

`next_id: 15`

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

## Open bugs

## BUG-10 - Training Config zeigt falschen freien GPU-VRAM-Wert (available_gb)
- status: open
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
- resolution: (open — es wurde noch kein Fix umgesetzt; nur erfasst)
- fix-proposal: `server/routes/gpu.py::gpu_feasibility()` — `available_gb` auf
  `total_vram_gb` umstellen (Training ist GPU-exklusiv; total ist der maßgebliche
  Budgetwert). `GpuFeasibilityBanner.vue` Label von „available" auf „total"
  anpassen; Response beide Felder (`total_gb`, `free_gb`) liefern.
  Siehe [`doc/implementation/m14-dual-mode-ui.md`](implementation/m14-dual-mode-ui.md) §BUGS.
- history:
  - 2026-09-02 — filed (random finding). Wert ist veraltet/startzeitbasiert; UI zeigt
    einen VRAM-Momentaufnahme-Wert statt des aktuell freien VRAM.
  - 2026-09-02 — fix-proposal eingetragen (primary agent, Analyse).

## BUG-11 - Wizard-Tier-Auswahl: Advanced nicht anwählbar, obwohl VRAM-Bedarf erst durch Quality-Qualität festgelegt wird
- status: open
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
- resolution: (open — nur erfasst, kein Fix)
- fix-proposal: Zweiteilig: (1) BUG-10 zuerst beheben (korrektes `available_gb`).
  (2) `WizardModal.vue` — `:disabled` auf Tier-Cards entfernen; Warnung-Badge
  bleibt; Feasibility-Prüfung auf Step 2 (Quality-Auswahl) verlagern: jede
  Quality-Card zeigt `vramFactor × estimated_gb` und wird warn/disabled, wenn
  dieser Wert `available_gb` überschreitet.
  Siehe [`doc/implementation/m14-dual-mode-ui.md`](implementation/m14-dual-mode-ui.md) §BUGS.
- history:
  - 2026-09-02 — filed (random finding). Als akzeptabel gilt, dass die Wizard-Seite den
    VRAM-Bedarf eines Default-Presets (z.B. `NORMAL`) anzeigt; gewünscht ist aber, dass
    die Anwählbarkeit / Warnung erst auf **Stufe der Quality-Auswahl** entscheidet, was
    mit dem verfügbaren VRAM tatsächlich erlaubt ist.
  - 2026-09-02 — fix-proposal eingetragen (primary agent, Analyse).

## BUG-12 - Upload & Ingestion: „Upload"-Button und „Show DDSP requirements" kleben aneinander; Requirements nicht als klickbar erkennbar
- status: open
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
- resolution: (open — es wurde noch kein Fix umgesetzt; nur erfasst)
- fix-proposal: `UploadIngestionView.vue` — `.hints-toggle` CSS: `display: block`,
  `color: var(--accent)`, `text-decoration: underline`, `margin-top: 1.5rem`
  sicherstellen. Damit ist der Button visuell als klickbarer Link erkennbar und
  der Abstand zum Upload-Button ist garantiert.
  Siehe [`doc/implementation/m5-webui.md`](implementation/m5-webui.md) §BUGS.
- history:
  - 2026-09-02 — filed (random finding). Gewünscht: separater Abstand zwischen Button
    und Link sowie optische Kennzeichnung (z.B. Link-Farbe / unterstrichen / Button-Stil)
    von „Show DDSP requirements" als interaktiv/klickbar.
  - 2026-09-02 — fix-proposal eingetragen (primary agent, Analyse).

## BUG-13 - Sidebar-Menü: Abschnitte ab „Export" durcheinander; Presets gehört weder unter Training noch unter Export
- status: open
- milestone: M5 (Web UI, Sidebar/Navigation; `Sidebar.vue` + `ui-requirements.md`)
- affected: M5, M-UI (Gesamtnavigation)
- found-in: 2026-09-02, random finding (Sidebar-Menüstruktur prüfen)
- severity: minor
- description: Die Sidebar-Sektionen ab „Export" sind durcheinander bzw.
  unsauber gruppiert. Aktuelle Anzeige (Ausschnitt):
  `🔊 Inference & Export / 🎵 Inference Playground / 💾 Model Export / 📋 Presets /
  🎤 Voice Conversion / 🧪 Experimental / 🔊 Reverb IR / 🎼 F0 Editor / 🔀 Component
  Mixer / ⚡ Synth Hacks / 🔄 Morphing / 🌌 Latent Explorer`.
  „Presets" gehört sachlich **weder** unter Training **noch** unter Export — es betrifft
  beide (Presets steuern die Trainingskonfiguration **und** die Export/Inferenz-Parameter)
  und sollte ein eigener, von Training und Export losgelöster Abschnitt sein. Zusätzlich
  ist die gesamte Menüstruktur auf Usability zu prüfen (Gruppierung, Reihenfolge,
  Unterordnungen).
- reproduction: Sidebar der App öffnen → Abschnitte ab „Export" sichten; „Presets"
  unter „Inference & Export" eingeordnet, obwohl es Training+Export betrifft.
- resolution: (open — es wurde noch kein Fix umgesetzt; nur erfasst)
- fix-proposal: `Sidebar.vue` — Gruppen neu strukturieren: (1) Datasets &
  Preprocessing, (2) Training (Config + Dashboard), (3) Presets — eigene Gruppe,
  (4) Inference & Export (nur Playground + Model Export), (5) Advanced Features
  (Voice Conversion, Morphing, Latent Explorer — neue Gruppe), (6) Experimental
  (nur echte Hacks: Reverb IR, F0 Editor, Component Mixer, Synth Hacks).
  Vollständige Usability-Review der Reihenfolge und Gruppenlabels.
  Siehe [`doc/implementation/m5-webui.md`](implementation/m5-webui.md) §BUGS.
- history:
  - 2026-09-02 — filed (random finding). Gewünscht: „Presets" als eigener Abschnitt
    (weder unter Training noch unter Export); die gesamte Navigations-/Sidebar-Struktur
    soll anschließend auf Usability geprüft und ggf. neu gruppiert werden.
  - 2026-09-02 — fix-proposal eingetragen (primary agent, Analyse).

## BUG-14 - „Backend: error" beim Start (start-application-release), obwohl die App läuft
- status: open
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
- resolution: (open — es wurde noch kein Fix umgesetzt; nur erfasst)
- fix-proposal: `TopBar.vue` — Health-Check mit Retry-Logik (3 Versuche,
  1 s / 2 s / 4 s Delay) in `onMounted`; bei Erfolg auf 'ok' setzen. Optional:
  Polling-Interval (30 s) für spätere Ausfälle. Alternativ: `scripts/start-app.ps1`
  im Release-Modus vor dem Browserstart auf den `/health`-Endpunkt warten (curl-Loop).
  Siehe [`doc/implementation/m5-webui.md`](implementation/m5-webui.md) §BUGS.
- history:
  - 2026-09-02 — filed (random finding). Kein Root-Cause-Analyse — als Fehlerbild
    festgehalten: fälschliche Fehleranzeige trotz laufendem Backend.
  - 2026-09-02 — fix-proposal eingetragen (primary agent, Analyse).

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
