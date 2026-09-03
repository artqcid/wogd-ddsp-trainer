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

## Known structural issues (ARCHITECT audit 2026-09-03)

- **BUG-26 missing:** ID gap exists between BUG-25 and BUG-27. BUG-26 was never assigned.
  `next_id` is correct (52); the gap is permanent and harmless — do not reuse ID 26.
- **Invalid status values:** BUG-46/47/48/49 were marked `resolved` (not in template);
  corrected to `fixed` in the 2026-09-03 audit. **Follow-up (re-analysis 2026-09-03):**
  BUG-47's `- status:` field was still literally `resolved` — the earlier audit had only
  written the correction into the resolution note, not the field. Now actually `fixed`.
- **Numeric ordering:** Bugs appear in section order (wont-fix, fixed, open) rather than
  by ID. This is intentional by design; the template-required sections are `## Wont-fix`,
  `## Fixed`, `## Open`. BUG numbers within each section need not be sequential.
- **`log.md` non-redundancy violation:** The `log.md` entry for BUG-47 (2026-09-03)
  contained the full bug record inline — violating the rule that `log.md` must only
  reference `BUG-<id>`. This is a `log.md` problem, not a `bugs.md` problem; see
  `log.md` audit note.

## Open-bug re-analysis (ARCHITECT_Openrouter, 2026-09-03)

All 16 open bugs (BUG-52..67) were re-verified against the actual code. Corrections are
recorded per bug in the entries themselves; this is the index of what changed:

| Bug | Verified | Correction applied |
|---|---|---|
| BUG-52..56, 58 | claims TRUE | none needed |
| BUG-57 | sub-fix (2) **FALSE** | watcher-spin fix withdrawn (`tasks.py` already `break`s after `stop_event.set()`); step M19.7b removed |
| BUG-59 | description **FALSE** | `features.py` is already rate-parameterised; real hardcoding inventory added; resolution aligned to `architecture.md` threading table; `gpu.py` claim corrected to docstring-only |
| BUG-60 | description **FALSE** | `fmin`/`fmax` already reach both trackers; real gap is the threading; dual-backend requirement added; invalid TabCore override replaced by read-only + CTA |
| BUG-61 | description imprecise | no `decoder` arg is passed at all (torchcrepe default); parselmouth has no equivalent; **added to the cache-invalidation sequencing table** |
| BUG-62 | naming conflict | canonical `warm_start_checkpoint`; asset hosting decided as download-on-first-run; sequenced after BUG-59 |
| BUG-63 | wrong cross-ref | diagnostics endpoint is BUG-45/52 not BUG-60; `total_chunks` does not exist yet → backend sub-step added; `depends-on: BUG-52, BUG-59` |
| BUG-64 | claims TRUE | none needed (only Group-B bug fully intact) |
| BUG-65 | sub-step (a) partly **done** | status `open` → `in-progress`; `architecture.md` section exists, m3/m17 notes still missing |
| BUG-66 | hedge resolved | only `add_scalar` exists (no images either); `depends-on: BUG-59` added |
| BUG-67 | claims TRUE | Nyquist-guard + sequential-with-BUG-60 notes added |

**Cross-cutting findings from the same pass:**

1. **Feature-cache invalidation batch.** BUG-59, BUG-60 **and BUG-61** all invalidate
   extracted `.npy` features. Canonical order **BUG-60 → BUG-61 → BUG-59** gives users
   a single re-preprocessing pass instead of three.
2. **UI specification gap (now closed).** None of the seven Group-B UI additions were
   specified in `ui-requirements.md` — they existed only inside `bugs.md` resolutions,
   which is not the binding UI source of truth. Added as
   `ui-requirements.md` §"Audio-quality & training-UX controls (BUG-59..67)".
3. **Missing implementation plan (now created).** Group A had `m19-bug-fixes.md`;
   Group B had none. Added `implementation/m20-audio-quality-bugs.md`.
4. **Plan-tier drift (now closed).** `plan.md` listed neither M19 nor M20 although
   `m19-bug-fixes.md` already existed and was indexed.
5. **New bug filed: BUG-68.** Running the Definition-of-Done gates against a
   documentation-only change set revealed that `ruff format --check` fails on
   committed code (`server/tasks.py`) — i.e. the formatting gate was already red
   before this session started.

## Counter

`next_id: 69`

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
- resolution: Added `batch_size_max` to `ParameterBounds`, computed dynamically from GPU VRAM via `int(vram * 32/6)`; `propose_presets()` scaled by speed factor (FAST ×0.25, NORMAL ×0.50, QUALITY ×1.00); `clamp_params()` clamps it; `apply_speed()` scales it; DataLoader reads from run config. Fixed in commit eb4e0e1 (initial) + 096d236 (dynamic formula).
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

---
## BUG-45 - Preprocessing result shows only file count, no F0/loudness diagnostics
- status: fixed
- milestone: M5 (Web UI, PreprocessingView + Backend extract-content)
- affected: MT-A2, MT-A4
- found-in: 2026-09-03, MT-A4 manual test (realized after "Processed 3 audio files" feedback)
- severity: minor
- description: The preprocessing result now shows `"Processed 3 audio files"` (BUG-25 fix + BUG-31 follow-up removed the hardcoded fake text). The user wants the rich diagnostic info that was previously hardcoded (F0 range, loudness range) — but computed from real extracted data instead of being fake.

  The backend endpoint `POST /api/datasets/{id}/extract-content` (and the async `POST /api/datasets/{id}/preprocess`) do not compute or return F0/loudness statistics. Computing `min_f0_hz`, `max_f0_hz`, `min_loudness_db`, `max_loudness_db` across all processed files and returning them in the response would allow the frontend to display e.g. `"F0 98–412 Hz · Loudness -22.1 to -4.3 dBFS · 3 files"`.

- reproduction: Upload audio → Preprocessing → Run Preprocessing → result shows only "Processed 3 audio files".
- resolution: Backend: `run_preprocessing_job` in `server/tasks.py` persists `diagnostics.json` sidecar file with f0_voiced_pct, f0_mean_hz, f0_median_hz, loudness_mean_db, loudness_std_db. New `GET /api/datasets/{id}/diagnostics` endpoint in `server/routes/dataset.py`. Frontend: `PreprocessingView.vue` polls endpoint (15 retries @ 2s) after preprocessing completes; displays F0 + loudness diagnostics inline. `apiClient.js`, `mockApiClient.js`, `restApiClient.js` extended with `getDatasetDiagnostics()`.

- history:
  - 2026-09-03 — filed after user feedback: preprocessing output too sparse, wants F0 + loudness diagnostics back (real stats, not hardcoded).
  - 2026-09-03 — backend partial: `run_preprocessing_job` extended with `diagnostics` dict (see `server/tasks.py:295–323`). Frontend display not implemented. Bug stays open.
  - 2026-09-03 — ARCHITECT_Openrouter analysis confirmed: status correctly `open`. Async flow and frontend display path missing.
  - 2026-09-03 — **fixed** by ARCHITECT_Openrouter (2 subagents: `general` tasks ses_f97f944f1ffe + ses_f97f7b7c5ffe). Backend: diagnostics.json persistence + GET endpoint. Frontend: polling + display.

## BUG-46 - FEAT: Rename "⚙ Reconfigure Model" button to "⚙ Start Config Wizard"
- status: fixed
- milestone: M5 (Web UI, TrainingConfigView)
- found-in: 2026-09-03, user feedback
- severity: minor
- description: The button text `⚙ Reconfigure Model` in TrainingConfigView is misleading — it doesn't reconfigure an existing model (there is none yet at config time). It opens the wizard to (re-)start the model setup process. Should be `⚙ Start Config Wizard` to clearly communicate what it does.
- reproduction: Open Training Config → see button "⚙ Reconfigure Model" → confusing because no model exists yet.
- resolution: Button text changed from "⚙ Reconfigure Model" to "⚙ Start Config Wizard" in TrainingConfigView.vue:119.
  **Code verified 2026-09-03:** `TrainingConfigView.vue` line 119 reads `⚙ Start Config Wizard` — confirmed.
  **Note:** Was previously marked `resolved` — corrected to `fixed` (valid template status).
- history:
  - 2026-09-03 — filed as feature request.
  - 2026-09-03 — fixed: one-line text change.
  - 2026-09-03 — ARCHITECT_Openrouter: code verified fixed; status corrected from `resolved` → `fixed`.

## BUG-47 - Wizard shows "fits 2.2 GB" for all tiers — estimate_model_vram ignores non-advanced tier differences
- status: fixed
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
- resolution: `train/gpu.py` now uses `BASE_ESTIMATE_GB` dict with per-tier baseline values (standard=2.2, component=2.25, hacks=2.3, engine=2.35, advanced=2.35); docstring and overhead logic updated.
  **Code verified 2026-09-03:** `train/gpu.py:245` shows `BASE_ESTIMATE_GB` dict with exactly these values — confirmed.
  **Note:** Was previously marked `resolved` — corrected to `fixed` (valid template status).
- history:
  - 2026-09-03 — filed after MT-A4 manual test. Root cause: `estimate_model_vram` needs per-tier baseline deltas beyond the single 2.2 GB constant.
  - 2026-09-03 — fixed: `BASE_ESTIMATE_GB` dict added with per-tier baseline values.
  - 2026-09-03 — ARCHITECT_Openrouter: code verified fixed; status corrected from `resolved` → `fixed`.
  - 2026-09-03 — ARCHITECT_Openrouter (re-analysis): the `- status:` field itself was still literally `resolved`, even though the resolution note claimed the correction had already been applied. The field is now actually set to `fixed`, so the audit note at the top of this file is accurate again.

## BUG-48 - Batch Size field still shows 1 despite BUG-43 fix — preset params don't reach coreParams
- status: fixed
- milestone: M3 (training loop / DataLoader / preset system)
- affected: M5, M14 (all training config UI), MT-A4
- found-in: 2026-09-03, MT-A4 retest after BUG-43 fix
- severity: major
- description: BUG-43 added `batch_size` to `propose_presets()` output, `clamp_params()`, `apply_speed()`, and DataLoader config reading. However the Batch Size input field still shows `1` (the store default) after wizard completion.

  Root causes:
  1. **Mock fixtures missing batch_size** (`webui/src/mocks/fixtures.js:78-79`): `presetsFixture` built-in presets have params with `hidden_size`, `stft_scales`, `mixed_precision`, `gradient_checkpointing` — but no `batch_size`. When TabCore's watch finds the preset and applies params via `Object.assign(store.coreParams, preset.params)`, `batch_size` is not overwritten. This affects dev/test mode with MockApiClient.
  2. **Timing gap** in `TabCore.vue` watch: `watch(presets, ..., { immediate: true })` fires immediately with empty array → can't find preset → no params applied. When API data arrives, the second fire should apply params — but if the API response also lacks batch_size (e.g. stale DB seed), the value stays 1.

- reproduction: Complete wizard → Core tab shows Batch Size = 1 even for QUALITY on a 6 GB GPU where preset should suggest batch_size=4.
- resolution: Extracted preset param application into `applyPresetParams()` helper in TabCore.vue; called from both the `watch(presets, ...)` callback AND the end of `onMounted` after `presets.value = await apiClient.listPresets()`. This ensures params are applied regardless of timing.
  **Code verified 2026-09-03:** `TabCore.vue:63` defines `applyPresetParams()`; called at lines 80, 87, 96 from watch + onMounted — confirmed.
  **Note:** Was previously marked `resolved` — corrected to `fixed` (valid template status).
- history:
  - 2026-09-03 — filed after MT-A4 retest. User confirms batch_size still shows 1 despite BUG-43 backend changes.
  - 2026-09-03 — fixed: `applyPresetParams()` extracted and called explicitly after API load.
  - 2026-09-03 — ARCHITECT_Openrouter: code verified fixed; status corrected from `resolved` → `fixed`.

## BUG-49 - Start Training fails with HTTP 422: missing required "name" field; no dataset selection; error message overflows text box
- status: fixed
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
- resolution: Three sub-issues resolved: (a) `buildFullConfig()` in store now auto-generates `name` from tier/preset/mode (e.g. "standard-NORMAL-offline"); (b) `dataset_id` added to store state, included in `buildFullConfig()`, and a dataset dropdown added to Core tab (fetches datasets via `apiClient.listDatasets()`); (c) `.validation-result.err` CSS now has `overflow-wrap: break-word; word-break: break-word; max-height: 200px; overflow-y: auto`.
  **Code verified 2026-09-03:** `stores/modelConfig.js:64` auto-generates name; `stores/modelConfig.js:65` includes dataset_id; `TabCore.vue:17` has dataset dropdown; `TrainingConfigView.vue:205` has the overflow CSS — all confirmed.
  **Note:** Was previously marked `resolved` — corrected to `fixed` (valid template status).
- history:
  - 2026-09-03 — filed after MT-A4 training start attempt.
  - 2026-09-03 — fixed: name auto-generated, dataset dropdown in Core tab, CSS overflow fix.
  - 2026-09-03 — ARCHITECT_Openrouter: code verified fixed; status corrected from `resolved` → `fixed`.

## BUG-50 - Training cannot start: Celery/Redis external server dependency breaks single-user local app
- status: fixed
- milestone: M4 (Backend, Celery task infrastructure)
- affected: M5 (Web UI, MT-A4)
- found-in: 2026-09-03, MT-A4 training start attempt
- severity: critical
- description: The training pipeline depends on **Celery** with **Redis** as broker and result backend (`redis://localhost:6379/0`). This is an external server requirement that is unacceptable for a single-user local application. When Redis is not running (normal for a local user), `POST /api/runs` fails with HTTP 500:

  ```
  RuntimeError: Retry limit exceeded while trying to reconnect to the Celery result store backend.
  ```

  **Two separate issues:**
  **(a) Architecture:** The `CeleryTaskRunner` (`server/tasks.py:545-554`) is the only `TaskRunner` implementation. There is no fallback that runs `run_training_job()` in-process or in a background thread without Redis. The `get_task_runner()` factory (`server/tasks.py:560-564`) always returns `CeleryTaskRunner`. The app should **not require Redis at all** — training is a heavyweight job but runs locally; a `LocalTaskRunner` using `threading.Thread` or `concurrent.futures.ProcessPoolExecutor` can run the training function directly without any message broker.

  **(b) Error handling in training start:** Even if Redis is unavailable, `create_run()` (`server/routes/training.py:95-132`) inserts the run into SQLite successfully before calling `runner.submit_training()`. But when that call throws, the run is already committed — leaving a zombie "pending" row in the DB that will never transition to "running" or "failed".

- reproduction: Start the application (no Redis running) → complete wizard → click "▶ Start Training" → button does nothing, then red error box shows HTTP 500 message. Backend logs show 20 Redis reconnection attempts then crash. Server continues running but training never starts.

- resolution: Implemented `LocalTaskRunner` in `server/tasks.py` using `ThreadPoolExecutor` (2 workers). `_redis_is_available()` helper probes Redis with 1s timeout. `get_task_runner()` returns `LocalTaskRunner` with warning log when Redis is absent; `CeleryTaskRunner` when Redis is reachable. Zombie-row fix: `create_run()` in `server/routes/training.py` now wraps `runner.submit_training()` in try/except — on failure, marks run as "failed" with error message before re-raising. Full test suite 363/1 pytest + 77/77 vitest green.
- history:
  - 2026-09-03 — filed after MT-A4. User confirms: single-user local app must NOT require an external server.
  - 2026-09-03 — ARCHITECT_Openrouter analysis: recommended `LocalTaskRunner` path documented.
  - 2026-09-03 — **fixed** by ARCHITECT_Openrouter (2 subagents: `general` tasks ses_f98155487ffe + ses_f9815282affe). `server/tasks.py`: `LocalTaskRunner` class, `_redis_is_available()`, updated `get_task_runner()`. `server/routes/training.py`: zombie-row try/except in `create_run()`.

## BUG-51 - Start Training button has no loading/disabled state and no success feedback
- status: fixed
- milestone: M5 (Web UI, TrainingConfigView)
- affected: MT-A4
- found-in: 2026-09-03, MT-A4 training start attempt
- severity: major
- description: The "▶ Start Training" button (`webui/src/views/TrainingConfigView.vue:174`) has no visual feedback during the async training start call:

  **(a) No loading/disabled state.** The button remains fully clickable while `handleStartTraining()` is awaiting the API call. The user can click it multiple times, triggering duplicate `POST /api/runs` requests. No spinner, disabled class, or text change is shown.

  **(b) No success action.** On success, only a small green `.validation-result` text appears ("Training started: <run_id> (pending)"). The user expected either the button text to change to a status (e.g. "Training Running...") or a prompt like "Open Training Dashboard to Observe". There is no navigation prompt or button to go to the training dashboard.

  **(c) Failure message is raw HTTP error.** On failure (e.g. BUG-50 Redis down → HTTP 500), the error `.validation-result.err` shows the raw HTTP message from `_fetchJson`: "HTTP 500 ... Retry limit exceeded...". This is a backend-internal message confusing to the user. A user-facing message like "Training failed: backend task runner unavailable. Check that all required services are running." would be appropriate.

- reproduction: Start app → complete wizard → click "▶ Start Training" → button never changes state → on success a small green text appears → on failure a raw HTTP error appears in red box.
- resolution: Three sub-issues fixed in `TrainingConfigView.vue`: (a) `isSubmitting` ref gates button disabled state + "⏳ Starting..." label during async call; (b) on success, auto-navigates to `/training-dashboard` after 1.2s delay, shows run name in message; (c) catch blocks detect error type (500/422/NetworkError) and show user-friendly messages instead of raw HTTP errors.
- history:
  - 2026-09-03 — filed after MT-A4. User reports "button don't show any update".
  - 2026-09-03 — ARCHITECT_Openrouter analysis: three sub-fixes documented above. No implementation yet.
  - 2026-09-03 — **fixed** by ARCHITECT_Openrouter (subagent: `general` task ses_f97f97822ffe). pytest 363/1 + vitest 77/77 green.

## BUG-52 - Preprocessing shows only "Processed N audio files" — diagnostics endpoint unreachable (route ordering + wrong API call)
- status: open
- milestone: M5 (Web UI, PreprocessingView + Backend dataset routes)
- affected: M4, MT-A2, MT-A4
- found-in: 2026-09-03, manual test session (console shows 17× 404 on /api/datasets/.../diagnostics)
- severity: major
- description: Two sub-issues that together prevent the F0/loudness diagnostics from appearing in the Preprocessing view:

  **(a) Wrong API call.** `PreprocessingView.vue` calls `apiClient.preprocessDataset(datasetId)` which maps to `POST /api/datasets/{id}/extract-content` (sync HuBERT content-embedding extraction only). The `diagnostics.json` file that the frontend polls for is only written by `POST /api/datasets/{id}/preprocess` (the async full pipeline, BUG-30 fix). The `/extract-content` endpoint does NOT persist `diagnostics.json`. So even with a correct route, the diagnostics endpoint returns `{"diagnostics": null}` because the file was never created.

  **(b) Route ordering bug.** In `server/routes/dataset.py`, the generic `GET /{dataset_id}/{filename}` (line 130) is registered BEFORE `GET /{dataset_id}/diagnostics` (line 318). FastAPI matches routes in registration order: a GET to `/api/datasets/{uuid}/diagnostics` hits `/{dataset_id}/{filename}` first with `dataset_id={uuid}, filename=diagnostics`. That handler checks `filename.suffix.lower() in ALLOWED_EXTENSIONS` — `diagnostics` has no suffix or `.json` is not in `ALLOWED_EXTENSIONS` → returns 404. The specific diagnostics route is shadowed and never reached.

  Debug log confirms: 17 consecutive `404 Not Found` for `/api/datasets/8795e6f2-.../diagnostics` between 18:23:29 and 18:25:22.

- reproduction: Open Preprocessing view → select dataset → Run Preprocessing → result shows "Processed 6 audio files" → diagnostics block never appears. Check server console: 404 on `/api/datasets/{id}/diagnostics`.
- resolution: Two independent fixes required, both must be applied:

  **(a) Fix wrong API call — `restApiClient.js` line 352:** `RestApiClient.preprocessDataset()` calls `POST /api/datasets/{id}/extract-content` (HuBERT content-embedding only; does NOT write `diagnostics.json`). It must instead call `POST /api/datasets/{id}/preprocess` (the full async F0+loudness pipeline, added by BUG-30, which writes `diagnostics.json` via `run_preprocessing_job`). Fix: change the URL in `webui/src/api/restApiClient.js:352` from `extract-content` to `preprocess`. The `mockApiClient.preprocessDataset()` returns `{ status: 'ok', files_processed: 3 }` which is compatible with the response shape of the new endpoint.

  **(b) Fix route ordering in `server/routes/dataset.py`:** FastAPI/Starlette evaluates `@router.get(...)` decorators in **registration order**. `GET /{dataset_id}/{filename}` (line 130) is a wildcard that matches `GET /{dataset_id}/diagnostics` with `filename="diagnostics"`. It returns 404 because `diagnostics` has no suffix in `ALLOWED_EXTENSIONS`. The specific route `GET /{dataset_id}/diagnostics` (line 318) is registered after the wildcard and is never reached. Fix: move the `get_dataset_diagnostics` handler (lines 318–329) to ABOVE `get_dataset_file` (line 130). Architectural rule: ALL specific `GET /{dataset_id}/X` routes must be registered before the generic `/{dataset_id}/{filename}` wildcard — apply this globally in the file to prevent future occurrences.

- history:
  - 2026-09-03 — filed after manual test session analysis (console log shows 17× 404 on diagnostics endpoint).
  - 2026-09-03 — ARCHITECT_Openrouter: analysis confirmed from code. (a) `restApiClient.js:352` confirmed calling `extract-content`. (b) route registration order confirmed: diagnostics at line 318 is after wildcard at line 130. Resolution documented.

## BUG-53 - Training Dashboard URL mismatch: router.push('/training-dashboard') but route is only /training — navigation lands on blank page
- status: open
- milestone: M5 (Web UI, TrainingConfigView → router)
- affected: M5.4, BUG-51 (success navigation), all training start attempts
- found-in: 2026-09-03, manual test session (user reports "site goes to /training-dashboard but nothing shown")
- severity: critical
- description: `TrainingConfigView.vue` line 110 calls `router.push('/training-dashboard')` after a successful training start (added by BUG-51). However, the Vue Router in `webui/src/router/index.js` only defines a `/training` route (line 30, name: `'training'`) for `TrainingDashboardView.vue` — there is NO `/training-dashboard` route. 

  Because the router uses `createWebHistory()`, navigating to `/training-dashboard` is NOT handled by the Vue Router as a named route — instead the browser performs a real HTTP navigation to that URL. In dev mode, Vite serves `index.html` for any unmatched path. The Vue app reinitializes from scratch, losing all Pinia store state (including `wizardCompleted`). The user sees the root HealthView (or a blank page) instead of the Training Dashboard.

  The sidebar correctly links to `/training`. The bug is solely in the hardcoded push URL on line 110.

  Also confirmed: the BUG-51 fix's `setTimeout(() => router.push('/training-dashboard'), 1200)` should have been `router.push('/training')`.

- reproduction: Complete wizard → click "▶ Start Training" → validation succeeds → after 1.2s delay → browser navigates to `/training-dashboard` → page reloads → blank/root view shown → no training dashboard visible.
- resolution: Single-line fix in `webui/src/views/TrainingConfigView.vue` line 110: change `router.push('/training-dashboard')` to `router.push({ name: 'training' })`. Using the **named route** (`name: 'training'` as defined in `webui/src/router/index.js:30`) instead of a hardcoded path string prevents future URL drift. The 1200ms `setTimeout` delay can remain as UX affordance (shows the success message before navigation). All other `router.push()` calls in the codebase should be audited to use named routes for the same reason.
- history:
  - 2026-09-03 — filed after manual test session.
  - 2026-09-03 — ARCHITECT_Openrouter: confirmed from code. `TrainingConfigView.vue:110` calls `router.push('/training-dashboard')`. `router/index.js` has no such route; correct route is `/training` (name: `'training'`). Resolution documented.

## BUG-54 - Navigating to non-existent /training-dashboard resets SPA + Pinia store → wizard reopens on return
- status: open
- milestone: M5 (Web UI, Pinia store persistence / router fallback)
- affected: BUG-53 (consequence), all users who start training
- found-in: 2026-09-03, linked to BUG-53
- severity: major
- description: Direct consequence of BUG-53. Because `/training-dashboard` doesn't exist as a Vue route, the browser performs a full navigation (not a client-side SPA transition). This causes the entire Vue app to reload, which:

  1. Destroys the in-memory Pinia store state: `store.wizardCompleted` resets to `false` (the default).
  2. When the user navigates to `/model` (Training Config) via the sidebar, `TrainingConfigView.vue` reinitializes with `showWizard.value = !store.wizardCompleted` (line 22) → evaluates to `true` → the WizardModal opens immediately as if no configuration was ever completed.
  3. The user sees the wizard as if their previous configuration was lost — which is exactly what happened because the store state was not persisted.

  The wizard completion state is meant to persist for the SPA session, but a full page reload bypasses this assumption. The user experience is confusing: they successfully started training, got redirected to a blank page, and when they find their way back to Training Config, the wizard is asking them to reconfigure from scratch.

- reproduction: Start training → redirect to `/training-dashboard` (blank) → click sidebar "Training Config" → wizard modal appears → all previous configuration gone.
- resolution: Two-layer fix:

  **(a) Root cause — fix BUG-53 first.** Once `router.push({ name: 'training' })` is used, the SPA navigation is client-side and the Pinia store is preserved. This eliminates the primary cause of wizard re-opening.

  **(b) Defence in depth — sessionStorage backup for `wizardCompleted` and `activeTier`.** Even with BUG-53 fixed, a full page reload (browser F5, dev HMR, or any future accidental hard navigation) will still reset the Pinia store. To survive this: in `webui/src/stores/modelConfig.js`, the `setTierFromWizard()` action should write `wizardCompleted=true` and `activeTier` to `sessionStorage` after setting the store state. The `state()` factory should read these back on initialization:

  ```js
  state: () => ({
    wizardCompleted: sessionStorage.getItem('wizardCompleted') === 'true',
    activeTier: sessionStorage.getItem('activeTier') ?? null,
    // ... rest of state
  })
  ```

  And in `setTierFromWizard()`:
  ```js
  sessionStorage.setItem('wizardCompleted', 'true')
  sessionStorage.setItem('activeTier', tier)
  ```

  `resetToWizard()` should clear both sessionStorage keys. This pattern does not affect Vitest tests (sessionStorage is not set in mock environment; `wizardCompleted` stays `false` as expected by tests).

- history:
  - 2026-09-03 — filed after manual test session.
  - 2026-09-03 — **update:** training DID start (POST /api/runs → 200, LocalTaskRunner submitted via ThreadPoolExecutor). The redirect to `/training-dashboard` caused full page reload, but the training job continued running in the background. The UI lost all connection to it — no way to see progress, stop, or interact with the running job. The run is visible via GET /api/runs if the user manually navigates to `/training`, but the broken redirect prevents this.
  - 2026-09-03 — ARCHITECT_Openrouter: confirmed from code. `modelConfig.js` store has no sessionStorage. Resolution documents two-layer fix: (a) BUG-53 fix prevents the page reload; (b) sessionStorage backup defends against any future full reload.

## BUG-55 - Training button lifecycle: Start Training must transition to Stop Training when job is running; no duplicate starts
- status: open
- milestone: M5 (Web UI, TrainingConfigView)
- affected: MT-A4, all training UX
- found-in: 2026-09-03, manual test analysis
- severity: major
- description: The "▶ Start Training" button must follow a lifecycle matching the actual run state. Currently it only has two states: default text + disabled-while-submitting (`isSubmitting`). After the run is submitted, the button reverts to "▶ Start Training" and is clickable again — allowing duplicate training starts.

  Required button states:
  - **No run exists:** "▶ Start Training" (enabled)
  - **Submitting/validating:** "⏳ Starting..." (disabled)
  - **Training running:** "⏹ Stop Training" (enabled, calls stopRun API)
  - **Training failed:** "❌ Training Failed" (disabled) + inline error message beside the button
  
  The button must reflect the **actual run status** from the backend (poll GET /api/runs), not just the local `isSubmitting` ref. When a run is `running`, the button must show "Stop Training". When `failed`, show "Training Failed" with the error. The Start Training action itself must be gated: if any run with status `running` or `pending` exists for this configuration, reject the duplicate.

  Additionally, the Start Training button should be usable from the **Training Dashboard view** as well, mirroring the same lifecycle.

- reproduction: Start training → button shows "⏳ Starting..." briefly → run created → button reverts to "▶ Start Training" → user can click again → duplicate POST /api/runs.
- resolution: Requires a new shared Pinia store **`trainingRunStore`** (`webui/src/stores/trainingRun.js`) that tracks the application-level active run. This same store is also the foundation of the BUG-56 fix — both bugs should be implemented together.

  **`trainingRunStore` state:**
  ```js
  { activeRunId: null, activeRunStatus: null, activeRunError: null }
  ```
  **Actions:**
  - `checkActiveRun(apiClient)` — calls `GET /api/runs`, finds first run with `status` in `['running', 'pending']`, updates store state. If none found, sets `activeRunId = null`.
  - `setActiveRun(runId, status, error)` — called immediately after `POST /api/runs` succeeds.
  - `stopActiveRun(apiClient)` — calls `apiClient.stopRun(activeRunId)`, refreshes state.
  - `persistToSession()` / `restoreFromSession()` — reads/writes `activeRunId` from `sessionStorage` for reload survival.

  **`TrainingConfigView.vue` changes:**
  - Import and use `trainingRunStore`.
  - `onMounted()`: call `trainingRunStore.checkActiveRun(apiClient)`.
  - Replace the single `isSubmitting` button with a computed state:
    - `running` → `"⏹ Stop Training"` (enabled; click calls `stopActiveRun`)
    - `pending` → `"⏳ Starting..."` (disabled)
    - `failed` → `"❌ Training Failed"` (disabled) + show `activeRunError` inline
    - else → `"▶ Start Training"` (enabled; click calls `handleStartTraining`)
  - `_doStartRun()` on success: call `trainingRunStore.setActiveRun(run.run_id, run.status, null)` before navigating.
  - Start is gated: if `activeRunStatus` is `'running'` or `'pending'`, show message "Training already running — stop it first" instead of submitting.

  **Files:** `webui/src/stores/trainingRun.js` (new), `webui/src/views/TrainingConfigView.vue`.

- history:
  - 2026-09-03 — filed after manual test analysis (button lifecycle insufficient for real usage).
  - 2026-09-03 — ARCHITECT_Openrouter: architectural solution documented. Root cause: no shared application-level run-state store. `trainingRunStore` is the unified fix for BUG-55 + BUG-56 + BUG-58. Button states confirmed absent in current code (only `isSubmitting` local ref). Named as cross-cutting: implement BUG-55 + BUG-56 together.

## BUG-56 - Training Dashboard must survive tab switches and always show current training state
- status: open
- milestone: M5 (Web UI, TrainingDashboardView)
- affected: all users, training monitoring
- found-in: 2026-09-03, manual test analysis (BUG-53 caused page reload)
- severity: major
- description: The Training Dashboard (`/training`) must reliably survive tab switches within the SPA. Currently it relies on `onMounted` + polling in `TrainingDashboardView.vue`. If the user navigates to another tab (e.g., Inference Playground) and comes back, the component unmounts (polling stops) and remounts (new polling starts) — this works for basic SPA navigation. However, BUG-53 causes a full page reload which completely destroys the dashboard.

  Requirements:
  1. **Pinia store for current run tracking:** `TrainingDashboardView.vue` should store the current run ID and status in a Pinia store (e.g., `trainingRun` store), so that even after component remount/SPA navigation, the dashboard can restore the last known state.
  2. **Immediate reconnect on mount:** On `onMounted`, check if any `running` or `pending` run exists (GET /api/runs) and immediately resume polling without 5s wait.
  3. **Persist across full reloads (optional):** Store last-known run ID + status in `sessionStorage` so even a full page reload can reconnect to the running job.
  4. **TensorBoard auto-refresh:** The TensorBoard iframe must reload/reconnect when returning to the dashboard tab (currently it stays stale).

  This is distinct from BUG-53 (wrong URL) — even after BUG-53 is fixed, the dashboard should robustly survive any SPA navigation or accidental reload.

- reproduction: Start training → navigate to any other sidebar tab → navigate back to Training Dashboard → polling restarts (visible 5s gap) → no prior state shown → TensorBoard iframe stays stale if it had loaded.
- resolution: **Architectural note on existing behaviour (correction):** The current `TrainingDashboardView.vue` already calls `loadRuns()` immediately in `onMounted` (line 113), so there is no 5-second reconnect gap on SPA navigation — the immediate fetch IS present. The real gaps are:

  1. **Brief empty-state flash on remount:** `runs` starts as `ref([])` locally in the component. During the in-flight `loadRuns()` API call, the template renders the empty-state block. This causes a visible flicker.
  2. **No cross-reload recovery:** If the page is reloaded (due to BUG-53 or F5), the dashboard has no way to know there was a running job — it starts fresh.
  3. **TensorBoard iframe stale:** The iframe renders once; navigating away and back does not reload it. The browser may serve a stale cached response.

  **Resolution — three changes, building on BUG-55's `trainingRunStore`:**

  **(1) Eliminate empty-state flash:** `TrainingDashboardView.vue` reads cached `runs` from `trainingRunStore` before the API call returns. The store holds the last-known run list. On remount, the cached list renders immediately; the API call updates it silently.

  **(2) SessionStorage recovery:** `trainingRunStore.restoreFromSession()` is called in `onMounted`. If `activeRunId` is found in sessionStorage, the empty-state is suppressed and polling starts immediately, even before the first API response.

  **(3) TensorBoard iframe refresh on route activation:** Wrap `TrainingDashboardView` in `<KeepAlive>` in `App.vue` (so it never unmounts during SPA navigation). Add an `onActivated()` hook that increments a `iframeKey` ref — the iframe element uses `:key="iframeKey"` which forces a full DOM rebuild (and thus iframe reload) each time the user returns to the dashboard tab. This is the correct Vue pattern for forcing iframe reload without a full component remount.

  **Files:** `webui/src/stores/trainingRun.js` (shared with BUG-55), `webui/src/views/TrainingDashboardView.vue`, `webui/src/App.vue` (KeepAlive wrapper for `/training` route).

- history:
  - 2026-09-03 — filed after manual test analysis (BUG-53 consequence + general resilience gap).
  - 2026-09-03 — ARCHITECT_Openrouter: analysis corrected — immediate `loadRuns()` on mount IS present; the "5s gap" claim was overstated. Real issues are empty-state flash, no sessionStorage recovery, and stale TensorBoard iframe. Resolution documented. Depends on BUG-55 `trainingRunStore` — implement together.

## BUG-57 - Clean training abort: stopping must save checkpoint + model state for resume
- status: open
- milestone: M4 (Backend, training lifecycle)
- affected: M3, M5, all training stop/resume workflow
- found-in: 2026-09-03, manual test analysis
- severity: major
- description: When a user requests a training stop (via UI Stop button or API), the training job must not just kill the process — it must:

  1. **Wait for current step to finish:** The training loop should complete the current batch step, then save a full checkpoint (model weights + optimizer state + current step number).
  2. **Save training state:** The checkpoint must contain `latest_step`, `loss`, and optimizer state so that `resume` can pick up exactly where it left off.
  3. **Mark run as `stopped` (not `failed`):** The DB status must transition to `stopped` so the Resume button is available.
  4. **Graceful shutdown within timeout:** If the step doesn't finish within a reasonable timeout (e.g., 30s), force-stop and log a warning.

  Currently `run_training_job` in `server/tasks.py` uses a `_watch_stop_request` thread that polls the DB for stop requests every 0.5s (lines 405-420). On stop, it sets `stop_event.set()` which the trainer checks at the end of each step (via `stop_event` in `trainer.run()`). The checkpoint save on stop is **not verified** — the trainer saves checkpoints periodically, but on stop it may not save the latest state. The `run_training_job` flow at line 432-436 sets status to `"stopped"` on stop, but the final checkpoint save must be ensured.

  Additionally, **DDSP training stop semantics:** Stopping a DDSP training loop means:
  - The model has been learning to reconstruct audio via multi-scale spectral loss
  - The current weights represent the best model so far (not necessarily the final one)
  - Saving a checkpoint on stop preserves these weights — the user can later resume and continue training from this point
  - No special "cooldown" or "finalization pass" is needed; the last completed step's gradient update is valid

- reproduction: Click Stop on a running training → `stop_event.set()` → trainer finishes current step → no explicit checkpoint save → run.status = `stopped` → resume loads the last **periodic** checkpoint (may be many steps behind).
- resolution: **One** targeted fix (a second proposed fix was withdrawn — see (2)):

  **(1) Final checkpoint save in `train/trainer.py::run()` (owner: M3):**

  The training loop in `Trainer.run()` checks `stop_event.is_set()` at the **start** of each iteration (lines 309 / 319). When stop is triggered: the last `train_step()` already ran to completion; `_log_and_checkpoint()` saved a checkpoint only if `step % checkpoint_interval == 0`. If training was stopped between checkpoint intervals, the last saved checkpoint may be many steps behind current.

  Fix — add after the for-loop in both branches (data_loader and single-batch):
  ```python
  # After for-loop exits:
  if stop_event is not None and stop_event.is_set():
      if self._step > 0 and self._step % self.config.checkpoint_interval != 0:
          ckpt_path = os.path.join(
              getattr(self, "_checkpoint_dir", "checkpoints"),
              f"step-{self._step}.pt",
          )
          self.save_checkpoint(ckpt_path)
          logger.info("stop checkpoint saved at step %d", self._step)
  ```
  This ensures the most recent completed step is always checkpointed on stop.

  **(2) ~~Stop watcher spin fix in `server/tasks.py::_watch_stop_request()`~~ — WITHDRAWN (2026-09-03 re-analysis):**

  The original claim was that the watcher thread spins after `stop_event.set()` because `stop_event.wait(0.5)` returns immediately on an already-set event. **This is not true of the current code.** `server/tasks.py:417-419` reads:

  ```python
  if stop:
      stop_event.set()
      break
  ```

  The `break` exits the `while not stop_event.is_set()` loop immediately after the set, so the watcher thread terminates and never spins. There is nothing to fix here. This sub-fix is withdrawn; do NOT edit `server/tasks.py` for this bug.

  **DDSP checkpoint resume semantics (confirmed):** `Trainer.save_checkpoint()` (lines 336–356) stores `step`, `model_state_dict`, `optimizer_state_dict`, `config`, `param_manifest`, `model_tier`, `variant_flags`. The resume path (`POST /api/runs/{id}/resume` → `Trainer.load_checkpoint()`) reads all of these. Adam optimizer state contains the per-parameter moment estimates — resume from a mid-training checkpoint is as accurate as continuing from a complete epoch. No "cooldown" or finalization pass needed.

  **Files:** `train/trainer.py` (save-on-stop after loop). **`server/tasks.py` is NOT in scope** — see withdrawn sub-fix (2).

- history:
  - 2026-09-03 — filed after manual test analysis (stop semantics not safe for resume).
  - 2026-09-03 — ARCHITECT_Openrouter: precision analysis from code. Confirmed: stop check is at iteration START (before train_step), so last step IS complete. Gap confirmed: no save-on-stop unless `step % checkpoint_interval == 0`. `save_checkpoint` payload confirmed sufficient for resume (model + optimizer + step + config). Resolution documented with exact fix location and code sketch.
  - 2026-09-03 — ARCHITECT_Openrouter (re-analysis): **sub-fix (2) withdrawn as a non-bug.** Verified `server/tasks.py:417-419` already `break`s out of the watcher loop right after `stop_event.set()`; no spin occurs. Bug scope reduced to the single `train/trainer.py` save-on-stop fix. Consequence: implementation step **M19.7b is removed** from `implementation/m19-bug-fixes.md`.

## BUG-58 - Resume training from wizard and dashboard when no training is running
- status: open
- milestone: M5 (Web UI, WizardModal + TrainingDashboardView)
- affected: all users, training workflow
- found-in: 2026-09-03, manual test analysis
- severity: major
- description: When no training is currently running, the user should be able to resume a previously stopped/failed training run. Two entry points:

  **(a) From the wizard.** The wizard (WizardModal) currently shows 3 steps: Tier → Quality → Target Mode. When a `stopped` or `failed` training run exists, the wizard should offer a **"Resume Existing Training"** option as an alternative to configuring a new model. This user story:
  1. Wizard opens → first step shows "Start New Training" / "Resume Existing Training" choice
  2. Choosing "Resume" → shows list of `stopped`/`failed` runs (name, tier, dataset, last step, loss)
  3. User selects a run → wizard completes → navigates to Training Dashboard with the resumed run
  4. The Resume API call is made automatically

  **(b) From the Training Dashboard.** `TrainingDashboardView.vue` already shows a `Resume` button on individual run cards when `run.status === 'stopped' || run.status === 'failed'` (BUG-33 fix). This is correct, but the empty state (line 146-149) should also show a "Resume Training" link/button when `stopped`/`failed` runs exist, not just "No training runs yet. Start one from the Training Config page."

  Additionally, the Training Dashboard should show **all** runs (including completed/stopped/failed), not just the currently running one. The current implementation already lists all runs — this is correct.

- reproduction: Complete a training run → stop it → refresh page → open Training Dashboard → empty state shows "No training runs yet" if runs list hasn't loaded yet → click "Training Config" → wizard starts from scratch → no "Resume" option.
- resolution: Two entry points to fix, plus one analysis correction:

  **Analysis correction:** The Training Dashboard "empty state" (`runs.length === 0`, line 146) fires both when there truly are no runs AND during the in-flight API call on mount (before `loadRuns()` returns). This causes a misleading flash even for users who do have runs. Separate these with a `hasLoaded` ref:
  ```js
  const hasLoaded = ref(false)
  // in loadRuns() after apiClient.listRuns():
  hasLoaded.value = true
  ```
  Template: `v-if="hasLoaded && runs.length === 0"` for empty state.

  **(a) Resume from wizard (`WizardModal.vue`):**

  WizardModal opens when `!store.wizardCompleted`. Currently it always starts at step 1 (Tier selection). Add a pre-check: on modal mount, call `GET /api/runs` and check for `stopped`/`failed` runs. If any exist, insert a **"Step 0: Choose Path"** before the tier grid:

  - Card A: **"▶ Start New Training"** — proceeds to existing step 1 (Tier → Quality → Target Mode).
  - Card B: **"↩ Resume Existing Training"** — shows a list of stopped/failed runs (columns: name, tier, dataset, last step, last loss). Selecting a run and clicking "Resume" calls `POST /api/runs/{id}/resume` → store updates `activeRunId` via `trainingRunStore.setActiveRun()` → wizard closes → navigate to `/training` (dashboard).

  If no stopped/failed runs exist, the wizard skips Step 0 and starts at Step 1 directly (current behaviour preserved).

  **(b) Resume from Training Dashboard empty state:**

  When `hasLoaded && runs.length === 0`: message stays "No training runs yet. Start one from the Training Config page." — this is already correct for truly empty state.

  When `hasLoaded && runs.length > 0` but all runs are `stopped`/`failed`/`completed`: the runs list IS shown (current code already does this — `v-else` branch renders run cards). The per-card Resume button is already present for `stopped`/`failed` (BUG-33 fix). No additional empty-state change needed here — the runs are visible.

  Improvement: Add a **"Resume Training" shortcut** at the top of the dashboard when any run is `stopped` or `failed` (above the run list, as a prominent CTA card), so the user doesn't have to click into a card to find the Resume button.

  **Files:** `webui/src/components/WizardModal.vue` (Step 0 with pre-check), `webui/src/views/TrainingDashboardView.vue` (`hasLoaded` ref + optional CTA card), `webui/src/stores/trainingRun.js` (shared with BUG-55/BUG-56).

- history:
  - 2026-09-03 — filed after manual test analysis (no resume workflow for stopped runs).
  - 2026-09-03 — ARCHITECT_Openrouter: analysis corrected — empty-state currently fires during in-flight API call (fix: `hasLoaded` ref). Dashboard already shows all runs (not just running) — per-card Resume button sufficient when runs exist. Real gap is wizard has no resume path. Resolution documented with Step 0 wizard pattern. Depends on `trainingRunStore` (BUG-55) — implement all four together.

---

## Open bugs — Colab notebook analysis 2026-09-03

## BUG-59 - sample_rate hardcoded to 16 kHz — professional audio quality requires 44.1/48 kHz; not user-configurable
- status: open
- milestone: M2 (Dataset prep — preprocessing pipeline)
- affected: M3 (training), M4 (backend config), M5 (UI), M6 (export quality)
- depends-on: **BUG-60 must land first.** Both bugs change the feature-cache format
  (`sample_rate` here, `f0_min_hz`/`f0_max_hz` there) and both invalidate every
  previously extracted `.npy` feature set. Fixing them in the wrong order forces
  users to re-run preprocessing twice. See `- sequencing:` below.
- found-in: 2026-09-03, Colab notebook analysis (hyakuchiki/realtimeDDSP uses 48 kHz default)
- severity: major
- description: The effective pipeline default is 16 kHz. The reference implementation
  `hyakuchiki/realtimeDDSP` (the basis for the Colab notebook and the Neutone
  timbre-transfer use case) defaults to **48 000 Hz** — the professional DAW standard.
  All Neutone plugins operate at 44.1 kHz or 48 kHz.

  16 kHz is speech/telephone quality. For timbre transfer and Neutone DAW plugin export
  (the primary use case of this project), 16 kHz produces audio that is demonstrably
  inferior: frequency content above 8 kHz is aliased away, removing harmonics, air, and
  presence from instruments and voices. Users exporting a Neutone model at 16 kHz will
  hear a muffled, degraded result compared to the source audio.

  The sample rate is also not user-configurable — there is no `sample_rate` parameter in
  the training config, no UI selector, and no backend validation that would surface this
  to the user as a choice.

  > **Correction (2026-09-03 re-analysis).** The original description claimed
  > "`dataset/features.py` uses `sr=16000`" and that the rate is a hardcoded constant
  > there. **That is false.** `dataset/features.py` is already fully parameterised:
  > `extract_f0_parselmouth(audio, sample_rate, …)`, `extract_f0_crepe(audio, sample_rate, …)`,
  > `extract_loudness_db(…, sample_rate, …)` and `compute_features(audio, sample_rate, …)`
  > all take `sample_rate` as an explicit argument. The 16 kHz value is injected by the
  > **call sites and defaults elsewhere**. Fixing `features.py` is therefore *not* part of
  > this bug; fixing its callers is. See the verified hardcoding inventory below.

  **Verified 16 kHz hardcoding inventory (2026-09-03):**

  | File | Location | What is hardcoded |
  |---|---|---|
  | `dataset/io.py` | `load_audio(path, target_sample_rate=16000)` | default resample target |
  | `dataset/io.py` | `resample_audio(..., target_sr=16000)` | default resample target |
  | `dataset/io.py` | `~line 58` | call passing `target_sample_rate=16000` |
  | `dataset/loader.py` | `AUDIO_SAMPLES_PER_FRAME = 160` | frame hop tied to a 10 ms hop **at 16 kHz**; must become `sample_rate // 100` |
  | `server/tasks.py` | `sample_rate=16000` (preprocessing job) | preprocessing rate |
  | `server/tasks.py` | `load_audio(path, target_sample_rate=16000)` | training data load rate |
  | `server/tasks.py` | `torchaudio.save(..., 16000)` | **synthesize output rate** (was missing from the original resolution) |
  | `server/routes/dataset.py` | `librosa.load(str(af), sr=16000, ...)` | waveform-preview rate |
  | `server/routes/reverb.py` | `inject_ir(..., sample_rate=16000)` / `extract_ir(..., sample_rate=16000)` | IR handling rate |
  | `dataset/features.py` | HuBERT content path | **legitimately fixed at 16 kHz** — HuBERT-Soft requires it; must NOT be changed, only isolated behind its own resample |

  Three sub-problems, each with its own fix step:

  **(a) Rate injected by callers, not configurable.** Every entry in the table above
  must read the rate from the run/dataset config instead of a literal. The
  `AUDIO_SAMPLES_PER_FRAME` constant must become rate-derived. The HuBERT path is the
  one deliberate exception and needs an explicit resample-to-16 kHz step so it keeps
  working at a 48 kHz pipeline rate.

  **(b) VRAM baselines calibrated at 16 kHz.** `train/gpu.py::estimate_model_vram()`
  does **not** contain sample-rate or sample-count constants — its `BASE_ESTIMATE_GB`
  values are empirical GB baselines, and the 16 kHz assumption survives only in the
  docstring (`train/gpu.py:263`: "seq_len=2 s @ 16 kHz"). The consequence is unchanged
  and still serious: those baselines were measured at 16 kHz, so at 48 kHz they
  under-report by roughly 3× on the audio-domain terms. The function must gain a
  `sample_rate` parameter and rate-scaled baselines.

  **(c) UI has no sample_rate selector.** Neither `webui/src/views/PreprocessingView.vue`
  nor `webui/src/components/TabCore.vue` exposes a sample rate option (verified
  2026-09-03). Users cannot choose 16 kHz for fast iteration vs. 48 kHz for production
  quality.

- reproduction: Upload any audio file → run preprocessing → inspect extracted `.npy`
  features (F0 frame rate, chunk length) → all calibrated to 16 kHz regardless of
  source sample rate. Export a Neutone model → the model runs at 16 kHz in the DAW
  (AM-radio quality).

- resolution: Three ordered sub-steps.

  > ⚠ **(a) and (b) are ONE atomic change — do not merge (a) without (b).**
  > Sub-step (b) is not optional polish. `train/gpu.py::estimate_model_vram()`
  > currently computes its budget at 16 kHz; the stated **minimum target hardware
  > is an RTX 3060 Laptop (6 GB)**. Shipping (a) alone flips the default to 48 kHz
  > while the estimator still reports 16 kHz figures, so the feasibility check
  > and `batch_size_max` both under-report by ~3× and the wizard will happily
  > green-light a configuration that OOMs on the project's own baseline GPU.
  > That is a worse end state than the current 16 kHz default: today the app is
  > merely low-quality, whereas (a)-without-(b) makes it *broken on the reference
  > hardware*. Either land (a)+(b) together, or gate the 48 kHz default behind
  > (b) landing first.

  **(a) Make sample_rate a first-class pipeline parameter (M2/M3/M4):**

  > **Authoritative scope = the 9-layer threading table in
  > `architecture.md` §"Sample rate pipeline (design decision, BUG-59)".**
  > That table is the single source of truth for this sub-step. The list below is the
  > file-level task breakdown of it; if the two ever disagree, `architecture.md` wins.

  - `dataset/io.py`: `load_audio()` / `resample_audio()` lose their `16000` defaults —
    `target_sample_rate` becomes a **required** argument so no caller can silently
    fall back to 16 kHz.
  - `dataset/loader.py`: replace `AUDIO_SAMPLES_PER_FRAME = 160` with a rate-derived
    hop (`sample_rate // 100` for the 10 ms frame grid); `DDSPDataset` reads
    `sample_rate` from the FeatureCache metadata (`meta.json` alongside the `.npy` files)
    and computes `chunk_length = chunk_seconds * sample_rate`.
  - `dataset/features.py`: **no signature changes needed** (already parameterised).
    Only the HuBERT content path must be isolated behind an explicit
    resample-to-16 kHz, because HuBERT-Soft is fixed at 16 kHz by the model itself.
  - `train/trainer.py`: `TrainingConfig` gains `sample_rate: int = 48000`; used for
    STFT scales, the spectral-loss rate, and the TensorBoard audio-log rate (BUG-66).
  - `model/ddsp_model.py`: `DDSPConfig` gains `sample_rate`; oscillator rate and the
    Nyquist harmonic clamp (`n_harmonics <= sample_rate / (2 * f0_max)`) derive from it.
  - `server/tasks.py`: `run_preprocessing_job()` and `build_training()` pass
    `sample_rate` from `model_config` — **never default silently**. The synthesize
    path's `torchaudio.save(..., 16000)` must use the checkpoint's stored rate.
  - `server/routes/training.py`: `RunCreateRequest` gains `sample_rate: int = 48000`,
    validated against the closed enum `16000 | 22050 | 44100 | 48000` (422 on anything
    else) and **409 on dataset/checkpoint rate mismatch**.
  - `server/routes/dataset.py`: the preprocess endpoint accepts `sample_rate` and
    **persists it into the dataset metadata**; the waveform-preview `librosa.load(sr=…)`
    uses the dataset's stored rate.
  - `server/routes/reverb.py`: `inject_ir` / `extract_ir` take the run's rate.
  - `inference/export.py`: the exported wrapper declares its native rate to the host DAW.
  - `server/presets.py`: add `"sample_rate"` to `PARAM_KEYS`; built-in presets set
    `sample_rate: 48000`.
  - Checkpoints store `sample_rate`; resume with a mismatching value is a 409.

  **(b) Make the VRAM estimator rate-aware (architecture.md + gpu.py):**

  Note the corrected premise: `estimate_model_vram()` holds **no** sample-rate or
  sample-count constants — only empirical `BASE_ESTIMATE_GB` baselines plus a
  docstring stating `seq_len = 2 s @ 16 kHz` (`train/gpu.py:263`). The fix is therefore
  not "recalculate a table of sample counts" but "make the baselines rate-scaled":

  - Add a `sample_rate: int` parameter to `estimate_model_vram()` (and to
    `ParameterBounds` / `batch_size_max` derivation).
  - Scale the audio-domain terms (forward activations, backward gradients, STFT loss)
    linearly with `sample_rate / 16000` for a fixed chunk duration. The
    parameter/optimizer terms do **not** scale.
  - At 48 kHz a 2-second chunk is 96 000 samples (3× the 16 kHz baseline), pushing the
    ~1.3–2.2 GB baseline toward ~3.5–6 GB — see `architecture.md` §"VRAM impact".
  - Recommendation: reduce the default `slice_length` to **1.0 second** at 48 kHz (the
    same choice realtimeDDSP makes), keeping the budget close to the 16 kHz 2-second
    baseline.
  - Update the `architecture.md` VRAM budget section and the `train/gpu.py` docstring
    with the 48 kHz figures and the recommended `slice_length=1.0`.

  **(c) Add the sample_rate selector to the UI — TWO places (M5):**

  > **Placement decision (2026-09-03, ARCHITECT_Openrouter):** the rate is *consumed*
  > at preprocessing time and is baked into the feature cache, but `architecture.md`'s
  > threading table also requires it on the run config with a 409 mismatch guard.
  > Both are therefore needed, with clearly split responsibilities. Binding UI spec:
  > `ui-requirements.md` §"Audio-quality & training-UX controls (BUG-59..67)".

  - `webui/src/views/PreprocessingView.vue` — **authoritative choice.** A `<select>`
    for `sample_rate` with options `16000` ("Fast iteration, low quality"),
    `22050`, `44100` ("CD quality"), `48000` ("DAW standard — recommended").
    Default `48000`. Sent as a form field to `POST /api/datasets/{id}/preprocess`
    and persisted in the dataset metadata. Selecting `16000` shows an inline hint:
    "16 kHz is phone quality — use only for fast experiments".
  - `webui/src/components/TabCore.vue` — **display + guard, not a free choice.**
    Shows the selected dataset's cached rate. If the run config's rate differs, show
    the mismatch warning and a "Re-run preprocessing at N Hz" CTA (this is the UI half
    of the 409 guard). A rate change here without re-preprocessing must be blocked,
    not silently accepted.
  - `webui/src/mocks/fixtures.js`: add `sample_rate: 48000` to all preset fixtures and
    to the dataset/diagnostics fixtures.
  - Vitest: cover the PreprocessingView select, the 16 kHz hint, and the TabCore
    mismatch warning.

- sequencing: **Canonical order is BUG-60 → BUG-61 → BUG-59.** All three write new keys
  into the feature-cache metadata and all three invalidate existing `.npy` features:

  | Bug | New cache key(s) | Invalidates features? |
  |---|---|---|
  | BUG-60 | `f0_min_hz`, `f0_max_hz` | yes — F0 track is re-extracted |
  | BUG-61 | `f0_viterbi` | yes — F0 track is re-extracted (**was missing from this table before the 2026-09-03 re-analysis**) |
  | BUG-59 | `sample_rate` | yes — audio, F0 and loudness all re-extracted |

  Landing BUG-59 first means every dataset must be re-preprocessed for the rate
  change, then re-preprocessed *again* when BUG-60 adds the F0 range, and a *third*
  time when BUG-61 adds the decoder flag. Landing them in the order
  60 → 61 → 59 collapses this into a **single** re-preprocessing pass for the user.

  All three bugs also touch the same functions and surfaces
  (`extract_f0_crepe()`, `extract_f0_parselmouth()`, `compute_features()`,
  `run_preprocessing_job()`, `RunCreateRequest`, `PARAM_KEYS`,
  `webui/src/mocks/fixtures.js`, `PreprocessingView.vue`), so doing them back to back
  in this order also avoids repeated merge conflicts on the same signatures.
  This is why they are one ordered batch in
  `implementation/m20-audio-quality-bugs.md` rather than three independent fixes.

  There is a second reason for this order: BUG-60's F0 range bound is the
  documented mitigation for the YIN/CREPE feature mismatch in BUG-65
  (see `architecture.md` §"Realtime export pitch tracker constraint"), so it is
  a prerequisite for more than just BUG-59.

- history:
  - 2026-09-03 — filed after Colab notebook analysis (realtimeDDSP defaults to 48 kHz).
    User confirmed: sample_rate must be user-configurable, default 48 kHz.
  - 2026-09-03 — ARCHITECT_Openrouter: architectural decision documented in
    `architecture.md` §"Sample rate pipeline" (closed enum, feature-cache coupling
    constraint, 409 guard on rate mismatch, 9-layer threading table).
    Two implementation constraints recorded here: (1) `depends-on` / `sequencing` —
    BUG-60 must land first to avoid a double re-preprocessing pass; (2) sub-steps
    (a) and (b) are atomic —     (a) alone breaks the 6 GB minimum target hardware
    because the VRAM estimator would still be calibrated to 16 kHz.
  - 2026-09-03 — ARCHITECT_Openrouter (re-analysis, code-verified): **three factual
    corrections.** (1) The claim "`dataset/features.py` hardcodes `sr=16000`" is FALSE —
    that module is already fully `sample_rate`-parameterised; the real hardcoding sits
    in `dataset/io.py`, `dataset/loader.py` (`AUDIO_SAMPLES_PER_FRAME = 160`),
    `server/tasks.py` (incl. the previously unlisted `torchaudio.save(..., 16000)`
    synthesize path), `server/routes/dataset.py` and `server/routes/reverb.py` — full
    inventory table added to the description. (2) `train/gpu.py` holds no sample-rate
    constants at all (only a docstring at line 263), so sub-step (b) is reframed as
    "make the estimator rate-aware", not "recalculate a sample-count table"; the
    atomicity warning stands unchanged. (3) The resolution list was narrower than
    `architecture.md`'s own 9-layer threading table (it omitted the dataset preprocess
    endpoint, `DDSPConfig`, `inference/export.py` and the 409 guards) — now aligned,
    with `architecture.md` declared authoritative. Also: sub-step (c) UI placement
    decided (PreprocessingView authoritative + TabCore display/guard), BUG-61 added to
    the sequencing table, and the HuBERT 16 kHz path flagged as a deliberate exception.

## BUG-60 - F0 range (min/max Hz) not configurable — pitch detection degrades without instrument-specific range
- status: open
- milestone: M2 (Dataset prep — preprocessing pipeline)
- affected: M3 (training quality), M4 (backend), M5 (UI)
- blocks: **BUG-59** (do this bug first — both change the feature-cache format;
  the reverse order costs users a second full re-preprocessing pass, see
  BUG-59 `- sequencing:`). Also the documented mitigation for the YIN/CREPE
  feature mismatch in **BUG-65**, and the backend prerequisite for **BUG-67**
  (the pitch-range reference guide is the UX layer over these two inputs).
- found-in: 2026-09-03, Colab notebook analysis (hyakuchiki/realtimeDDSP `original_f0_min`/`original_f0_max`)
- severity: major
- description: Constraining the F0 search range to the instrument's actual pitch range
  dramatically improves detection accuracy — the Colab notebook warns:
  **"Without accurate pitch detection, the model can't learn at all!"**

  For a soprano voice (261–1046 Hz), an over-wide range wastes confidence on octave
  errors and sub-octave noise. For a bass guitar (41–330 Hz), the tracker may confuse
  harmonics with the fundamental.

  > **Correction (2026-09-03 re-analysis).** The original description claimed
  > "`dataset/features.py` calls torchcrepe with default wide range (32–2000 Hz)" and
  > that "there is no `f0_min_hz`/`f0_max_hz` parameter anywhere in
  > `dataset/features.py`". **Both are false.** The extraction layer already supports
  > the range on *both* backends:
  >
  > - `extract_f0_crepe(audio, sample_rate, hop_length, fmin=50.0, fmax=2000.0, device)`
  >   passes `fmin=fmin, fmax=fmax` straight into `torchcrepe.predict()`.
  > - `extract_f0_parselmouth(audio, sample_rate, time_step, f0_min=50.0, f0_max=2000.0)`
  >   passes them as Praat's `pitch_floor` / `pitch_ceiling`.
  >
  > So the defaults are **50–2000 Hz** (not 32–2000), and the extraction functions need
  > no new parameters. The genuine gap is that **nothing above them can set the range**:
  > it is not threaded from REST → tasks → `compute_features()`, not stored in the
  > feature-cache metadata, and not present in any UI or preset.

  **Note the dual-backend requirement.** The project has two F0 backends with
  *different parameter names* (`fmin`/`fmax` for CREPE, `f0_min`/`f0_max` for
  parselmouth). The threading work must set the range on **whichever backend is
  selected** — a fix that only wires up the CREPE path leaves parselmouth users on the
  wide default and is therefore incomplete.

  Verified absent (2026-09-03):
  - `server/routes/training.py` — no `f0_min_hz`/`f0_max_hz` on `RunCreateRequest`
  - `server/tasks.py` — `run_preprocessing_job()` does not accept or forward a range
  - `server/presets.py` — not in `PARAM_KEYS`
  - `webui/src/views/PreprocessingView.vue` — no F0 range inputs (diagnostics only
    *displays* `f0_mean_hz` read-only)
  - `webui/src/components/TabCore.vue` — no F0 range fields
  - `webui/src/mocks/fixtures.js` — not in preset fixtures

  Two sub-problems:

  **(a) Backend: F0 range not threaded from the API down to the extractors.**
  `run_preprocessing_job()` → `compute_features()` → `extract_f0_crepe()` /
  `extract_f0_parselmouth()`: the two leaf functions accept the range, the two callers
  above them do not forward it. The backend also stores no F0 range in the
  feature-cache metadata, so nothing can validate or display it later.

  **(b) Frontend: no F0 range inputs in the preprocessing view.**
  There are no Hz range inputs anywhere in the UI. Users have no way to configure
  this critical parameter.

- reproduction: Run preprocessing on any vocal recording → the tracker uses the wide
  50–2000 Hz default because no caller narrows it → F0 track contains octave errors
  and noise → model trains on wrong pitch targets → poor synthesis quality.

- resolution: Two ordered sub-steps:

  **(a) Thread f0_min_hz / f0_max_hz from the API down to both extractors
  (M2/M4 — server/routes, server/tasks.py, dataset/features.py):**
  - `dataset/features.py::extract_f0_crepe()` / `extract_f0_parselmouth()`:
    **no signature change needed** — they already take `fmin`/`fmax` and
    `f0_min`/`f0_max` respectively. Only the defaults may be aligned (both are
    currently 50/2000).
  - `dataset/features.py::compute_features()`: add `f0_min_hz` / `f0_max_hz`
    parameters and forward them to the **selected** backend, mapping to that
    backend's parameter names (`fmin`/`fmax` for CREPE, `f0_min`/`f0_max` for
    parselmouth). This mapping is the actual missing link.
  - `server/tasks.py::run_preprocessing_job()`: accept `f0_min_hz`/`f0_max_hz` from
    the preprocessing request and pass them into `compute_features()`.
  - `server/routes/dataset.py` preprocess endpoint: accept the two values as request
    fields and **persist them into the dataset/feature-cache metadata** (`meta.json`),
    next to `sample_rate` (BUG-59) and `f0_viterbi` (BUG-61).
  - `server/routes/training.py::RunCreateRequest`: add
    `f0_min_hz: float = 80.0`, `f0_max_hz: float = 1100.0`; validate
    `0 < f0_min_hz < f0_max_hz` and `f0_max_hz < sample_rate / 2` (Nyquist guard).
  - `server/presets.py`: add `f0_min_hz`, `f0_max_hz` to `PARAM_KEYS`;
    built-in presets set `f0_min_hz: 80`, `f0_max_hz: 1100` (safe voice default).
  - The diagnostics endpoint returns both the **requested** range and the **actually
    detected** F0 range, so the UI can warn when the material does not match the
    configured range.

  **(b) Add F0 range inputs to the UI (M5 — PreprocessingView.vue + TabCore.vue):**

  > **Placement correction (2026-09-03 re-analysis).** The original resolution asked
  > for a *training-time override* field in `TabCore.vue` "for cases where training
  > uses a different range than preprocessing". **That is architecturally invalid.**
  > The F0 range is consumed during feature extraction and baked into the feature
  > cache — the training loop reads a finished F0 track and can no longer re-bound it.
  > An override field there would be a no-op control that silently lies to the user.
  > This is exactly the feature-cache coupling rule `architecture.md` states for
  > `sample_rate` (§"Sample rate pipeline" → "Coupling constraint"). TabCore therefore
  > gets **read-only display + a re-run-preprocessing CTA**, never an override.

  - `PreprocessingView.vue`: add two number inputs `f0_min_hz` / `f0_max_hz`
    (default 80/1100) ABOVE the "Run Preprocessing" button, plus the collapsible
    instrument reference panel (BUG-67). Values are sent to
    `POST /api/datasets/{id}/preprocess`. Client-side validation mirrors the backend
    guard (`min < max`, `max < sample_rate / 2`).
  - `TabCore.vue`: **read-only** display of the F0 range that was used during
    preprocessing (from the dataset diagnostics), with a "Re-run preprocessing to
    change" link back to the Preprocessing view. No editable field, no override.
  - `webui/src/mocks/fixtures.js`: add `f0_min_hz: 80`, `f0_max_hz: 1100` to
    all preset fixtures and to the diagnostics fixture.
  - Vitest: cover the PreprocessingView range inputs + validation, and assert the
    TabCore display is non-editable.

  Binding UI spec: `ui-requirements.md`
  §"Audio-quality & training-UX controls (BUG-59..67)".

- history:
  - 2026-09-03 — filed after Colab notebook analysis. "Without accurate pitch
    detection, the model can't learn at all!" — direct quote from the reference
    implementation.
  - 2026-09-03 — ARCHITECT_Openrouter: marked as **blocking BUG-59**. Both bugs
    change the feature-cache format and invalidate existing `.npy` features;
    this one must land first so users re-preprocess once rather than twice.
    Also recorded as prerequisite for BUG-65 (F0 bound is the YIN octave-error
    mitigation) and BUG-67 (UX layer over these inputs).
  - 2026-09-03 — ARCHITECT_Openrouter (re-analysis, code-verified): **three
    corrections.** (1) The claim that no `f0_min`/`f0_max` support exists in
    `dataset/features.py` is FALSE — both backends already accept and use the range
    (`extract_f0_crepe` passes `fmin`/`fmax` into `torchcrepe.predict()`;
    `extract_f0_parselmouth` passes `pitch_floor`/`pitch_ceiling`), and the real
    defaults are 50–2000 Hz, not 32–2000 Hz. The genuine gap is the missing threading
    from REST → `run_preprocessing_job()` → `compute_features()` plus the absent
    feature-cache persistence. (2) The **dual-backend** requirement was missing: the
    two backends use different parameter names, so a CREPE-only fix silently leaves
    parselmouth on the wide default. (3) The proposed **training-time override field in
    TabCore is architecturally invalid** and has been replaced by read-only display +
    a re-run-preprocessing CTA — the range is baked into the feature cache, so an
    override there could not take effect. Nyquist validation guard added.

## BUG-61 - F0 Viterbi smoothing flag not exposed to users — relevant for pitch-slide instruments
- status: open
- milestone: M2 (Dataset prep — preprocessing pipeline)
- affected: M4 (backend), M5 (UI — PreprocessingView)
- batch: part of the single-re-preprocessing batch **BUG-60 → BUG-61 → BUG-59**
  (this bug changes the F0 track and therefore invalidates the feature cache; see
  BUG-59 `- sequencing:`). Plan: `implementation/m20-audio-quality-bugs.md`.
- found-in: 2026-09-03, Colab notebook analysis (realtimeDDSP `f0_viterbi` param)
- severity: minor
- description: The decoder choice controls whether the pitch track is smoothed or raw:

  - **Viterbi:** smoothed pitch trajectory, removes frame-to-frame
    jumps, better for most instruments and sustained tones.
  - **Argmax:** raw per-frame argmax, preserves fast pitch slides and
    glissandos — better for portamento instruments (theremin, fretless bass,
    continuous pitch controllers).

  The Colab notebook exposes this as `f0_viterbi: bool` with guidance: *"Instruments
  with a lot of pitch slides might be better without it."*

  Users have no way to choose: the flag is absent from the API, presets and UI.

  > **Correction (2026-09-03 re-analysis).** The original description said the decoder
  > is "hardcoded in `dataset/features.py` (always Viterbi)". That is imprecise in a
  > way that matters for the fix: `extract_f0_crepe()` passes **no `decoder` argument
  > at all** to `torchcrepe.predict()` (it passes only `model`, `device`,
  > `batch_size`, `return_harmonicity`, `pad`, `hop_length`, `fmin`, `fmax`). The
  > effective behaviour *is* Viterbi, but only because that is **torchcrepe's own
  > default** — there is no local constant to flip. The fix must therefore *add* an
  > explicit `decoder` argument, and it must pin the torchcrepe default assumption in
  > a test so a future upstream default change cannot silently alter our F0 tracks.

  **Dual-backend note.** The Viterbi/argmax distinction exists **only for the CREPE
  backend**. `extract_f0_parselmouth()` uses Praat's own pitch tracker, which has no
  equivalent decoder switch. The flag must therefore be documented and surfaced as
  *CREPE-only*: when the parselmouth backend is selected, the UI control must be
  disabled with an explanatory hint rather than silently ignored.

- reproduction: Run preprocessing on a theremin or fretless bass recording →
  Viterbi smoothing (torchcrepe's default) removes the characteristic glides → model
  trains on a flattened pitch trajectory → synthesis sounds step-quantized, not gliding.

- resolution:
  - `dataset/features.py::extract_f0_crepe()`: add `f0_viterbi: bool = True`
    parameter; pass an **explicit** decoder to torchcrepe
    (`decoder=torchcrepe.decode.viterbi if f0_viterbi else torchcrepe.decode.argmax`).
    Never rely on the upstream default.
  - `dataset/features.py::compute_features()`: propagate `f0_viterbi` to the CREPE
    backend; ignore it (with a logged note) for the parselmouth backend.
  - `server/tasks.py::run_preprocessing_job()`: accept `f0_viterbi` (default `True`)
    and forward it.
  - `server/routes/dataset.py` preprocess endpoint: accept `f0_viterbi` and
    **persist it into the feature-cache metadata** alongside `sample_rate` (BUG-59)
    and the F0 range (BUG-60).
  - `server/presets.py`: add `"f0_viterbi"` to `PARAM_KEYS`; default `True` in
    all built-in presets.
  - `server/routes/training.py::RunCreateRequest`: add `f0_viterbi: bool = True`.
  - `PreprocessingView.vue`: add a checkbox `[x] F0 Viterbi smoothing (recommended)`
    with help text: "Disable for instruments with continuous pitch slides (theremin,
    fretless bass, bowed strings)." Default checked. **Disabled with a hint when the
    parselmouth backend is active** (CREPE-only option).
  - `webui/src/mocks/fixtures.js`: add `f0_viterbi: true` to preset fixtures.
  - Vitest: cover the viterbi checkbox, including the disabled/parselmouth case.
  - Pytest: assert `torchcrepe.predict` receives an explicit `decoder` for both flag
    values (guards against an upstream default change).

  Binding UI spec: `ui-requirements.md`
  §"Audio-quality & training-UX controls (BUG-59..67)".

- history:
  - 2026-09-03 — filed after Colab notebook analysis.
  - 2026-09-03 — ARCHITECT_Openrouter (re-analysis, code-verified): **three
    corrections.** (1) The decoder is not hardcoded locally — `extract_f0_crepe()`
    passes no `decoder` argument at all and merely inherits torchcrepe's Viterbi
    default; the fix must add an explicit argument plus a regression test pinning that
    assumption. (2) The **parselmouth backend has no Viterbi equivalent**, so the flag
    is CREPE-only and the UI control must be disabled (not silently ignored) for
    parselmouth. (3) **This bug invalidates the feature cache** exactly like BUG-59 and
    BUG-60, but was missing from BUG-59's sequencing table — without that, users would
    have faced a *third* full re-preprocessing pass. Now recorded as part of the
    ordered batch BUG-60 → BUG-61 → BUG-59.

## BUG-62 - No pretrained warm-start checkpoint available — limited-range instruments train poorly from scratch
- status: open
- milestone: M3 (Model + training — export/checkpoint)
- affected: M4 (backend), M5 (UI — wizard + TabCore), M6 (bundled assets)
- found-in: 2026-09-03, Colab notebook analysis (realtimeDDSP bundles `data/pretrain_sawnoise.ckpt`)
- severity: minor
- description: The Colab reference notebook bundles a pretrained checkpoint
  `data/pretrain_sawnoise.ckpt` — a generic harmonic+noise DDSP model pre-trained on
  a wide-range sawtooth/noise signal. Users can warm-start training from this checkpoint
  instead of random initialization.

  The practical benefit: instruments with a **limited pitch range** (e.g., bass guitar,
  cello, tuba) confine the harmonic oscillator to a small frequency region. Training
  from random init, the model must discover the harmonic structure from scratch; warm
  starting from a generic harmonic model dramatically reduces training time and improves
  extrapolation quality for pitches outside the dataset range.

  Currently our project:
  1. Has no bundled pretrained checkpoint.
  2. Has no `warm_start_checkpoint` option in the training config API or UI.
  3. The `ckpt` parameter for resume exists (`POST /api/runs/{id}/resume`) but is for
     resuming a specific run — not for warm-starting a new training from a generic
     base model.

  > **Naming decision (2026-09-03 re-analysis).** The original entry used two different
  > names for the same field — `pretrain_ckpt_path` in the description and
  > `warm_start_checkpoint` in the resolution. **Canonical name:
  > `warm_start_checkpoint`** (matches the `Trainer` semantics: weights-only warm init,
  > fresh optimizer — as opposed to `resume`, which restores optimizer state too).
  > `pretrain_ckpt_path` must not appear in code or docs.

  Two sub-steps:

  **(a) Add `warm_start_checkpoint` to the training config + backend.**
  The `TrainingConfig` dataclass and `build_training()` in `server/tasks.py` should
  accept an optional `warm_start_checkpoint`. When set, `Trainer.run()` loads this
  checkpoint BEFORE beginning training (warm init). Only model weights are loaded
  (not optimizer state — the optimizer starts fresh, which is correct for fine-tuning).

  **(b) Provide a pretrained base checkpoint and expose it in the UI.**
  Generate (or obtain) a generic harmonic+noise base checkpoint trained on white-noise
  sweep audio (similar to `pretrain_sawnoise.ckpt`). Add a "Start from pretrained base
  model" toggle to the wizard and to `TabCore.vue`. When toggled on,
  `warm_start_checkpoint` is set to the base-model path; the UI shows a brief
  description of what the base model was trained on.

  > **Asset-hosting decision (2026-09-03, ARCHITECT_Openrouter): download-on-first-run.**
  > The repo uses no git LFS today and adding it for a multi-MB binary would impose an
  > LFS dependency on every clone for an *optional* feature. Instead: the checkpoint is
  > published as a release asset and fetched on first use into a local cache dir
  > (e.g. `WOGD_ASSETS_DIR` / `~/.cache/wogd-ddsp/pretrain_base.pt`), with a SHA-256
  > integrity check. The feature degrades gracefully: if the download fails or the
  > machine is offline, the toggle is disabled with an explanatory hint and training
  > from random init proceeds normally. **This also makes BUG-62 the only Group-B bug
  > with an external-network dependency** — it must therefore never become a
  > prerequisite for any other bug in the batch.

- reproduction: Train on a bass guitar dataset from random initialization → training
  converges slowly and extrapolation above the dataset's highest note produces silence
  or noise instead of a plausible bass tone.

- resolution:

  **(a) Backend warm-start (M3/M4):**
  - `train/trainer.py`: add `warm_start_checkpoint: str | None = None` to
    `TrainingConfig`. At the start of `run()`, if `warm_start_checkpoint` is set and
    no `ckpt` (resume) path is set, call
    `self.model.load_state_dict(torch.load(path)["model_state_dict"], strict=False)`.
    `strict=False` allows partial loading if the warm-start model has different
    architecture params.
  - `server/tasks.py::build_training()`: thread `warm_start_checkpoint` from
    `model_config` to `TrainingConfig`. Default `None`.
  - `server/routes/training.py::RunCreateRequest`: add
    `warm_start_checkpoint: str | None = None`.

  **(b) Base checkpoint asset + UI (M5/M6):**
  - Generate the base checkpoint: train a small DDSP standard model
    (`hidden_size=128`, 10 000 steps) on a deterministic white-noise-sweep signal
    (all pitches 80–1100 Hz, equal loudness). This takes ~10 minutes on GPU.
    **Publish it as a release asset**, not in the repo (see the asset-hosting
    decision above). It must be generated at the **48 kHz** pipeline default
    (BUG-59) — a 16 kHz base checkpoint would be useless for warm-starting a
    48 kHz run, so this sub-step is sequenced **after** BUG-59.
  - Add a fetch-and-cache helper (SHA-256 verified, cached under `WOGD_ASSETS_DIR`)
    plus a `GET /api/assets/pretrain-base/status` endpoint so the UI can tell whether
    the asset is available, downloadable, or unreachable.
  - `WizardModal.vue`: add toggle `[ ] Warm-start from pretrained base model
    (recommended for limited-range instruments)`. Default off. Disabled with a hint
    when the asset is unavailable offline.
  - `TabCore.vue`: add `warm_start_checkpoint` dropdown with options:
    `"None"` / `"Pretrained base model (harmonic sweep)"` / `"Custom checkpoint (pick file)"`.
  - `webui/src/mocks/fixtures.js`: add `warm_start_checkpoint: null` to presets.

  Binding UI spec: `ui-requirements.md`
  §"Audio-quality & training-UX controls (BUG-59..67)".

- history:
  - 2026-09-03 — filed after Colab notebook analysis. The bundled pretrained
    checkpoint is a practical training quality improvement for limited-range
    instruments.
  - 2026-09-03 — ARCHITECT_Openrouter (re-analysis): **two decisions recorded.**
    (1) Naming unified to `warm_start_checkpoint` — the entry previously used
    `pretrain_ckpt_path` in the description and `warm_start_checkpoint` in the
    resolution for the same field. (2) Asset hosting resolved as
    **download-on-first-run** with SHA-256 verification and graceful offline
    degradation, instead of the previously unresolved "git LFS or download" note —
    the repo has no LFS today and this is an optional feature. Also sequenced
    **after BUG-59**, because the base checkpoint must be generated at the 48 kHz
    pipeline default to be usable.

## BUG-63 - max_steps shown without estimated epochs context — users find step counts unintuitive
- status: open
- milestone: M5 (Web UI — TabCore training config)
- affected: M5.3 (TrainingConfigView UX)
- depends-on: **BUG-52** (the diagnostics endpoint must actually be reachable) and
  **BUG-59** (the epoch formula uses `slice_length`, which BUG-59 sub-step (b) changes
  from 2.0 s to 1.0 s at 48 kHz — computing estimates against the old value would
  display numbers that are wrong by 2×). Requires a small backend extension, see
  resolution.
- found-in: 2026-09-03, Colab notebook analysis (notebook warns: "REMINDER: steps ≠ epochs")
- severity: minor
- description: The training config UI (`TabCore.vue`) exposes a `max_steps` number input
  (default 50 000). Training steps are the primary training progress unit in the backend,
  but users familiar with deep-learning training typically think in **epochs** (full passes
  through the dataset). The Colab notebook explicitly warns users about this:
  *"REMINDER: steps = number of epochs × number of samples each epoch"*.

  Currently:
  - The `max_steps` field shows only the raw step count.
  - There is no computed estimate of how many epochs that corresponds to.
  - The user has no intuition for "will 50 000 steps be enough?" without knowing
    their dataset size and batch size.

  Once the dataset has been preprocessed, the chunk count per file is deterministic:
  `chunks_per_file ≈ audio_duration_s / slice_length`. From that:
  `steps_per_epoch ≈ (total_chunks / batch_size)`, and
  `estimated_epochs = max_steps / steps_per_epoch`.

  > **Correction (2026-09-03 re-analysis).** The original text attributed the
  > diagnostics endpoint to "the BUG-60 fix". **That is the wrong bug.** The
  > diagnostics payload was introduced by **BUG-45** and is made *reachable* by
  > **BUG-52** (route-ordering + wrong-API-call fix). BUG-60 only *adds* the F0 range
  > to that payload. More importantly: the endpoint currently returns **no
  > `total_chunks` field at all** — the resolution below assumed data that does not
  > exist, so a backend extension is required before any UI work.

- reproduction: Open Training Config tab → look at the max_steps field →
  "50000 steps" — no context for whether that is 10 epochs or 1000 epochs on the
  selected dataset.

- resolution: One backend step, then the UI step.

  **(a) Backend — expose `total_chunks` in the diagnostics payload (M4, prerequisite):**
  The diagnostics endpoint (`GET /api/datasets/{id}/diagnostics`, BUG-45/BUG-52)
  currently returns per-dataset F0/loudness stats but **no chunk count**. Add
  `total_chunks`, `avg_duration_s` and the `slice_length` actually used to
  `diagnostics.json` when `run_preprocessing_job()` writes it. Without this the UI has
  nothing to compute from.

  **(b) UI — epoch estimate in `TabCore.vue` (M5):**
  - Add a computed `estimatedEpochs` that reads:
    - `totalChunks` from the dataset diagnostics (`apiClient.getDatasetDiagnostics(datasetId)`)
    - `batchSize` from `store.coreParams.batch_size`
    - `maxSteps` from `store.coreParams.max_steps`
    - Formula: `estimatedEpochs = Math.round(maxSteps / Math.max(1, totalChunks / batchSize))`
  - Display below the `max_steps` input: `≈ N epochs on selected dataset`
    (shown only when a dataset is selected and diagnostics are loaded;
    hidden with a tooltip "Select and preprocess a dataset to see epoch estimate"
    otherwise).
  - The display is read-only and purely informational — it does not constrain or
    replace `max_steps`.
  - `webui/src/mocks/fixtures.js`: add a `diagnosticsFixture` with `files_processed: 8,
    total_chunks: 480, avg_duration_s: 4.0, slice_length: 1.0` for mock rendering.
  - Vitest: test that `estimatedEpochs` renders correctly with mock diagnostics and
    stays hidden when no dataset is selected.

  Binding UI spec: `ui-requirements.md`
  §"Audio-quality & training-UX controls (BUG-59..67)".

- history:
  - 2026-09-03 — filed after Colab notebook analysis. Low implementation cost; high
    UX value for new users.
  - 2026-09-03 — ARCHITECT_Openrouter (re-analysis, code-verified): **two corrections.**
    (1) Wrong cross-reference — the diagnostics endpoint comes from BUG-45 and is made
    reachable by BUG-52, not by BUG-60. (2) The resolution assumed a `total_chunks`
    field that the endpoint **does not return**; a backend sub-step (a) has been added
    to emit `total_chunks` / `avg_duration_s` / `slice_length`, and the UI work is now
    explicitly sequenced after it. Also recorded `depends-on: BUG-52, BUG-59` — the
    epoch formula divides by `slice_length`, which BUG-59 changes to 1.0 s at 48 kHz.

## BUG-64 - Export metadata (author, description, is_experimental, model_version) missing from ParamManifest and export UI
- status: open
- milestone: M15 (Parameter Manifest Backend)
- affected: M16 (Parameter Builder UI — export form), M17 (MIDI Synth export)
- found-in: 2026-09-03, Colab notebook analysis (neutone export metadata form)
- severity: minor
- description: The Colab notebook's "Neutone Model Metadata" cell requires the user to
  fill in: `model_name`, `model_author`, `short_description`, `long_description`,
  `is_experimental` (bool), `model_version`. These fields are required by the Neutone
  marketplace for any model submission and are embedded in the `.nm` export file.

  Our M15 `ParamManifest` / `InferenceParam` schema covers inference runtime parameters
  (knob names, min/max/default values) but does **not** include publishing/catalog
  metadata. The `ModelExportView.vue` export form (M16) has export buttons but no fields
  for model name, author, or description.

  Without these fields:
  1. Exported `.nm` files lack the required Neutone marketplace metadata → models cannot
     be submitted to neutone.space.
  2. Users have no way to identify their exported model in their DAW plugin library
     (all models show up with blank names).

  Two sub-steps:

  **(a) Add `ModelCard` dataclass to `model/param_manifest.py` (M15 extension).**
  A `ModelCard` holds the publishing fields: `model_name`, `model_author`,
  `short_description`, `long_description`, `is_experimental: bool = True`,
  `model_version: str = "1.0.0"`. Store it under `state["model_card"]` in the
  checkpoint alongside `param_manifest`. The `ParamManifest` container gets a
  `model_card: ModelCard` field. Default: all strings empty, `is_experimental=True`.
  Old checkpoints without `model_card` generate a default transparently (same
  pattern as `param_manifest` backward compat).

  **(b) Add model card editor to `ModelExportView.vue` (M16 extension).**
  A collapsible "Model Card" section above the export buttons with input fields
  for all `ModelCard` fields. Pre-fills from the checkpoint's stored `model_card`.
  On export (`POST /api/models/{run_id}/{ckpt}/export/neutone`), the form values
  are sent alongside the export request and embedded in the output `.nm` file.

- reproduction: Click "Export → Neutone (.nm)" → downloaded file has no model name,
  author, or description embedded. Loaded in the Neutone plugin, the model shows
  as "DDSP" with no author or description.

- resolution:

  **(a) `model/param_manifest.py` — ModelCard dataclass (M15 extension):**
  ```python
  @dataclass
  class ModelCard:
      model_name: str = ""
      model_author: str = ""
      short_description: str = ""
      long_description: str = ""
      is_experimental: bool = True
      model_version: str = "1.0.0"

      def to_dict(self) -> dict: ...
      @classmethod
      def from_dict(cls, d: dict) -> "ModelCard": ...
  ```
  Add `model_card: ModelCard = field(default_factory=ModelCard)` to `ParamManifest`.
  Update `Trainer.save_checkpoint()` to embed `model_card` in `state["model_card"]`.
  Update `Trainer.load_checkpoint()` to restore it (default `ModelCard()` if absent).
  Add `GET/PUT /api/models/{run_id}/{checkpoint}/model-card` endpoints alongside the
  existing params endpoints in `server/routes/models.py`.
  Tests: `tests/test_param_manifest.py` — round-trip ModelCard, backward compat.

  **(b) `ModelExportView.vue` — Model Card editor section (M16 extension):**
  - Collapsible `<details><summary>Model Card (Neutone metadata)</summary>…</details>`.
  - Fields: `model_name` (text), `model_author` (text), `short_description` (text,
    max 100 chars), `long_description` (textarea, max 500 chars),
    `is_experimental` (checkbox, default checked), `model_version` (text, "1.0.0").
  - On mount: `GET /api/models/{runId}/{ckpt}/model-card` to pre-fill.
  - "Save Model Card" button: `PUT /api/models/{runId}/{ckpt}/model-card`.
  - Both Neutone FX and MIDI Synth export buttons are disabled when `model_name` is
    empty (required field).
  - `webui/src/mocks/fixtures.js`: add `modelCardFixture`.
  - Vitest: test all fields render, save calls PUT, export disabled without name.

  Binding UI spec: `ui-requirements.md`
  §"Audio-quality & training-UX controls (BUG-59..67)".

- history:
  - 2026-09-03 — filed after Colab notebook analysis. Required for Neutone marketplace
    submission; currently completely absent from the export workflow.
  - 2026-09-03 — ARCHITECT_Openrouter (re-analysis, code-verified): **no factual
    corrections needed** — confirmed `model/param_manifest.py` defines only
    `InferenceParam` and `ParamManifest`, with no `ModelCard` dataclass and no
    `model_card` field. This is the only Group-B bug whose analysis survived
    verification unchanged. It is also fully independent of the feature-cache batch
    (BUG-60/61/59), so it can be implemented in parallel. Added the binding
    `ui-requirements.md` pointer for its export-form UI.

## BUG-65 - Neutone realtime export uses CREPE (non-streaming) — must use streaming-compatible pitch tracker (YIN/pYIN)
- status: in-progress
- milestone: M3 (Model + training - realtime export)
- affected: M17 (MIDI Synth VST export), inference/export.py
- progress: sub-step **(a) partially done** - the constraint IS now documented in
  `architecture.md` §"Realtime export pitch tracker constraint (design decision,
  BUG-65)" (line ~580), but the two required cross-references in
  `implementation/m3-model-training.md` §M3.4 and
  `implementation/m17-midi-synth-vst.md` are still **absent** (verified 2026-09-03).
  Sub-step (b) (`inference/yin.py`) is entirely open.
- found-in: 2026-09-03, Colab notebook analysis (realtimeDDSP replaces CREPE with YIN for streaming export)
- severity: major
- description: During training and offline preprocessing, torchcrepe (CREPE-PyTorch) is
  the F0 extractor and produces high-quality pitch tracks. However, CREPE requires a
  **fixed-size buffer** (typically 1024 samples at 16 kHz) and is not streaming
  compatible — it cannot process a single incoming audio frame in real-time with causal
  output.

  For the **Neutone realtime export** path (`inference/export.py::export_neutone`,
  M3.4), the exported TorchScript model must include a real-time pitch extractor that:
  1. Operates causally (no look-ahead beyond the current frame).
  2. Is TorchScript-compatible (no scipy, no numpy, no external process).
  3. Produces an `f0_hz` estimate per audio frame (e.g. 10 ms hop at 48 kHz = 480 samples).

  The reference implementation replaces CREPE with **YIN** (de Cheveigné & Kawahara 2002)
  for the streaming model. YIN is a deterministic, causal autocorrelation-based pitch
  estimator that is straightforward to implement in pure PyTorch and is TorchScript
  compatible.

  Currently `inference/export.py` and the `NeutoneWrapper` TorchScript module (M15)
  do not include any realtime pitch extractor — the wrapper expects `f0_hz` as an
  external input (passed by the calling DAW plugin). This is the correct design for
  the Neutone `NeutoneModel` API (which handles F0 input externally), but it means
  our architecture must be documented clearly: the Neutone plugin passes YIN-extracted
  F0 into our model, not CREPE.

  For the **MIDI Synth export** path (M17), pitch comes from MIDI note-to-Hz
  conversion (no pitch tracker needed at runtime). This path is already correctly
  designed.

  The **Custom VST export** path (M15 — `CustomVSTWrapper`) may embed a runtime
  pitch tracker. If it does, it must use YIN/pYIN, not CREPE.

  Two sub-problems:

  **(a) Architecture undocumented:** The constraint "Neutone export uses YIN, not CREPE,
  for realtime F0" is not documented anywhere in `architecture.md`, M17, or M3.4.
  Developers extending the export path may inadvertently add CREPE, which will fail
  at TorchScript trace time or produce latency incompatible with realtime use.

  **(b) CustomVSTWrapper pitch tracker choice unspecified:** If the Custom VST wrapper
  (M15.7) includes an embedded pitch extractor (for the non-MIDI use case where the
  user feeds audio directly), the choice between YIN, pYIN, and other approaches has
  not been specified or implemented.

- reproduction: Inspect `inference/export.py` and `inference/midi_synth_wrapper.py` →
  no YIN implementation present. The Neutone wrapper expects external F0 (correct for
  the Neutone SDK API, but undocumented). CustomVSTWrapper has no embedded pitch tracker.

- resolution: Two ordered sub-steps:

  **(a) Document the realtime pitch tracker constraint (doc-only, M3 docs):**
  - ✅ **DONE:** `architecture.md` §"Realtime export pitch tracker constraint (design
    decision, BUG-65)" states that CREPE is used only during offline preprocessing
    (training), that any realtime export path must use a streaming-compatible tracker
    (recommended: YIN — causal, TorchScript-compatible), and that the Neutone SDK
    supplies F0 as an input so `NeutoneWrapper` needs no embedded tracker.
  - ⬜ **STILL OPEN:** add the same constraint note to
    `implementation/m3-model-training.md` §M3.4 and
    `implementation/m17-midi-synth-vst.md`. Verified 2026-09-03: neither file mentions
    YIN or CREPE. These are the notes a developer extending the export path would
    actually read, so the sub-step is not complete without them.

  **(b) Implement a TorchScript-compatible YIN module (M3 / inference layer):**
  - `inference/yin.py` (NEW): implement `yin_f0(audio_frame: Tensor, sample_rate: int,
    fmin: float = 80.0, fmax: float = 1100.0) -> Tensor` in pure PyTorch.
    YIN algorithm: difference function → cumulative mean normalized difference →
    absolute threshold → parabolic interpolation. Pure tensor ops, no scipy.
    TorchScript-exportable.
  - `inference/export.py`: reference `yin_f0` in the `CustomVSTWrapper` forward
    method (optional: embed pitch extraction in the VST wrapper for the audio-FX
    non-MIDI use case). The NeutoneWrapper does NOT embed YIN (F0 is an external
    Neutone SDK input).
  - The `fmin`/`fmax` defaults must come from the run's configured F0 range
    (**BUG-60**) rather than being hardcoded — that bound is the documented
    octave-error mitigation for YIN.
  - Tests: `tests/test_yin.py` — unit tests against known-pitch sinusoids at
    48 kHz (e.g., 440 Hz A4, 261 Hz C4, 880 Hz A5); compare YIN output to
    ground-truth within ±2 cents.

- history:
  - 2026-09-03 — filed after Colab notebook analysis (realtimeDDSP replaces CREPE
    with YIN in streaming export). This is a pre-requisite for CustomVSTWrapper
    audio-FX mode to work correctly in realtime.
  - 2026-09-03 — ARCHITECT_Openrouter (re-analysis, verified): status corrected
    `open` → **`in-progress`**. Sub-step (a)'s central claim — "the constraint is not
    documented anywhere in `architecture.md`" — is **no longer true**: that section
    exists. However the mandated notes in `m3-model-training.md` and
    `m17-midi-synth-vst.md` are still missing, so (a) is only partially done and the
    remaining work is now marked per-item. Sub-step (b) re-verified as fully open:
    no `inference/yin.py` and no YIN implementation exist anywhere in the codebase.
    Added the explicit dependency that YIN's `fmin`/`fmax` must be fed from BUG-60's
    configured F0 range instead of hardcoded literals.

## BUG-66 - TensorBoard does not log reconstructed audio (no train_orig/train_resyn comparison)
- status: open
- milestone: M3 (Model + training — TensorBoard logging)
- affected: M5.4 (Training Dashboard monitoring)
- depends-on: **BUG-59.** The resolution's code sketch calls
  `add_audio(..., sample_rate=self.config.sample_rate)`, but `TrainingConfig` has
  **no `sample_rate` field** today (verified 2026-09-03) — that field is introduced by
  BUG-59 sub-step (a). Implementing BUG-66 first would require hardcoding 16 kHz into
  the audio logs, which then silently mislabels every clip once the pipeline moves to
  48 kHz. Land BUG-59 first.
- found-in: 2026-09-03, Colab notebook analysis (realtimeDDSP TensorBoard shows original vs. reconstructed audio)
- severity: minor
- description: The Colab notebook documents a key TensorBoard feature:
  **original vs. reconstructed audio comparison** (`train_orig/n` vs `train_resyn/n`,
  and `val_orig/n` vs `val_resyn/n`). Listening to the reconstruction audio in
  TensorBoard is the primary way to judge whether a DDSP model has converged —
  "the resynthesized audio should sound like the original."

  Our `train/trainer.py::_log_and_checkpoint()` currently logs:
  - Scalar metrics only: `self.writer.add_scalar("train/loss", loss, step_after)`.

  > **Verification closed (2026-09-03 re-analysis).** The original entry carried an
  > open hedge: "(TensorBoard spectrogram images may be logged — verify)". Verified:
  > `add_scalar` is the **only** `SummaryWriter` call in `train/trainer.py` — there are
  > no `add_image` and no `add_audio` calls anywhere in the file. So neither audio
  > **nor** spectrogram images are logged; the gap is slightly larger than filed.

  It does **not** log:
  - `train_orig/0` — a sample of the original input audio.
  - `train_resyn/0` — the reconstructed audio from the model on the same sample.
  - `val_orig/0` — a validation sample.
  - `val_resyn/0` — the model's reconstruction of the validation sample.

  Without these audio logs, the TensorBoard dashboard shows only loss curves.
  The user cannot hear whether the model is actually learning to reconstruct the source
  timbre, which is the most important quality signal for DDSP training.

  The TensorBoard `SummaryWriter.add_audio()` API supports this natively:
  `writer.add_audio(tag, waveform_tensor, global_step, sample_rate)`.

- reproduction: Start a training run → open TensorBoard → Audio tab → empty
  (no audio clips logged). Only the Scalars tab has content (loss curve).

- resolution:
  - In `train/trainer.py::_log_and_checkpoint()`, after the loss is computed
    and logged, also log audio every `checkpoint_interval` steps (or a separate
    configurable `audio_log_interval`, defaulting to `checkpoint_interval`):
    ```python
    if self._writer and step % self.config.checkpoint_interval == 0:
        # log one training sample
        with torch.no_grad():
            resynth = self.model(f0_sample, loudness_sample)
        rate = self.config.sample_rate
        self._writer.add_audio("train_orig/0", audio_sample[0], step, sample_rate=rate)
        self._writer.add_audio("train_resyn/0", resynth[0], step, sample_rate=rate)
    ```
  - For validation: if a validation DataLoader is available, run one inference
    pass on the first validation batch every `checkpoint_interval` steps and log
    `val_orig/0` / `val_resyn/0`.
  - The `train_sample` (f0, loudness, audio) for the audio log should be cached
    from the first batch (deterministic reference sample) so the reconstruction
    quality is comparable across steps. Store as `self._log_sample` after the
    first batch.
  - Memory: log only `[0]` (first item in batch); clip waveform to 3 seconds max
    to keep TensorBoard event files small (`waveform[:, :sample_rate * 3]`).
  - Tests: `tests/test_trainer_logging.py` — mock TensorBoard writer, verify
    `add_audio` is called with correct tags and at correct intervals.

- history:
  - 2026-09-03 — filed after Colab notebook analysis. This is a training quality
    and monitoring gap — the most useful TensorBoard feature for DDSP is missing.
  - 2026-09-03 — ARCHITECT_Openrouter (re-analysis, code-verified): **hedge closed and
    dependency added.** (1) The open "(verify)" note about spectrogram images is
    resolved: `add_scalar("train/loss", ...)` is the only `SummaryWriter` call in
    `train/trainer.py` — no `add_image`, no `add_audio`. (2) Recorded
    `depends-on: BUG-59` — the resolution sketch reads `self.config.sample_rate`, a
    field that does not exist until BUG-59 lands; without it the audio logs would have
    to hardcode 16 kHz and would mislabel every clip after the 48 kHz switch.
    (3) Optional `audio_log_interval` config field noted as part of the same change.

## BUG-67 - No instrument pitch range reference guide in UI — users don't know what f0_min/max to enter
- status: open
- milestone: M5 (Web UI — PreprocessingView)
- affected: BUG-60 (f0 range inputs — this is the UX companion to that bug)
- found-in: 2026-09-03, Colab notebook analysis (notebook links to Wikipedia "Typical pitch ranges")
- severity: minor
- description: Once BUG-60 is fixed (F0 range inputs added to `PreprocessingView.vue`),
  users need guidance on what values to enter. The Colab notebook links to a Wikipedia
  article on typical instrument pitch ranges; without this context, users will leave
  the defaults (32–2000 Hz) or enter arbitrary values, defeating the purpose.

  A practical reference integrated into the UI would cover:
  - Human voices: bass 82–294 Hz, baritone 98–392 Hz, tenor 130–523 Hz,
    mezzo-soprano 196–880 Hz, soprano 261–1046 Hz
  - String instruments: violin 196–3136 Hz, cello 65–1050 Hz, bass guitar 41–330 Hz
  - Wind instruments: flute 261–2093 Hz, trumpet 165–988 Hz, saxophone 103–1175 Hz
  - Common catch-all for voice synthesis: 80–1100 Hz

  The reference should be immediately accessible without leaving the UI — a collapsible
  panel or popover that pre-fills the F0 range inputs when the user selects an instrument.

- reproduction: F0 range inputs added (BUG-60) → user sees two blank number boxes
  → no guidance on what ranges to use → likely to leave defaults.

- resolution:
  - `PreprocessingView.vue`: add a `<details><summary>📏 Instrument Pitch Range
    Reference</summary>…</details>` collapsible panel below the F0 range inputs.
  - The panel renders a table of common instrument ranges with a "Use this range"
    button on each row. Clicking the button fills `f0_min_hz` / `f0_max_hz` inputs.
  - Table structure (inline data, no API call needed):
    ```js
    const PITCH_RANGES = [
      { name: "Bass voice",     min: 82,  max: 294  },
      { name: "Baritone voice", min: 98,  max: 392  },
      { name: "Tenor voice",    min: 130, max: 523  },
      { name: "Alto voice",     min: 175, max: 698  },
      { name: "Soprano voice",  min: 261, max: 1046 },
      { name: "Violin",         min: 196, max: 3136 },
      { name: "Cello",          min: 65,  max: 1050 },
      { name: "Bass guitar",    min: 41,  max: 330  },
      { name: "Flute",          min: 261, max: 2093 },
      { name: "Trumpet",        min: 165, max: 988  },
      { name: "Alto saxophone", min: 103, max: 830  },
      { name: "General voice",  min: 80,  max: 1100 },
    ]
    ```
  - Dependency: BUG-60 must be implemented first (F0 range inputs must exist).
  - Vitest: test that clicking "Use this range" updates the `f0_min_hz`/`f0_max_hz`
    inputs to the expected values.

  Binding UI spec: `ui-requirements.md`
  §"Audio-quality & training-UX controls (BUG-59..67)".

- history:
  - 2026-09-03 — filed after Colab notebook analysis. UX companion to BUG-60;
    implement together in the same PR/task as BUG-60 sub-step (b).
  - 2026-09-03 — ARCHITECT_Openrouter (re-analysis): analysis holds — no factual
    corrections. Two notes: (1) the "Use this range" values must be validated against
    the Nyquist guard introduced with BUG-60 (e.g. Violin's 3136 Hz max is invalid at a
    16 kHz pipeline rate only in combination with a low harmonic ceiling — the guard
    must warn rather than silently clamp). (2) Since this bug edits the same file and
    the same input pair as BUG-60 sub-step (b), the two must be **sequential
    single-file steps**, never parallel subagents.

---

## Open bugs - process/quality regressions found 2026-09-03

## BUG-68 - `server/tasks.py` is committed in an unformatted state - `ruff format --check` fails on a clean checkout
- status: open
- milestone: M4 (Backend, orchestration module)
- affected: Definition of Done for every task (the formatting gate is part of it)
- found-in: 2026-09-03, open-bug re-analysis (ARCHITECT_Openrouter ran the DoD checks
  on a tree with no code changes and the formatting gate still failed)
- severity: minor
- description: `ruff format --check .` reports `server/tasks.py` as needing
  reformatting on a **clean checkout** - the file is committed in an unformatted state,
  not merely dirty in a working tree. The violation is a missing blank line after the
  module docstring (ruff wants one blank line between the closing docstring quotes and
  `from __future__ import annotations`).

  Why this matters beyond cosmetics: `ruff format --check` is one of the mandatory
  Definition-of-Done gates in `AGENTS.md`. With a committed violation in place the gate
  is **red before any work starts**, so every subsequent task either reports a false
  failure or - worse - an agent silently reformats an unrelated file to make the gate
  pass, producing scope-bleed in the diff. It also means the DoD checks were not
  actually run (or not run to completion) for whichever earlier task introduced it.

- reproduction: On a clean checkout with no local modifications, run
  `.venv\Scripts\python.exe -m ruff format --check .` -> "1 file would be reformatted:
  server\tasks.py". `ruff check .` passes, so `ruff check` alone does not surface it.
- resolution: Single-file, mechanical fix - **must be delegated to a DEV/subagent**
  (it is a code edit; the primary agent that found it is ARCHITECT and does not edit
  code):
  - Run `ruff format server/tasks.py` (adds the blank line after the module docstring).
  - No logic change; the diff must be exactly that one blank line. Any additional
    change in that file is out of scope and must be rejected.
  - Verify with `ruff format --check .` -> all files formatted, and `pytest` still green
    (the file is the task-orchestration module, so a full run is warranted).
  - Recommended follow-up (separate task, not this bug): add the formatting gate to
    the pre-commit / post-commit hook path so a committed violation cannot recur.
- history:
  - 2026-09-03 - ARCHITECT_Openrouter: filed during the open-bug re-analysis. Detected
    incidentally: the DoD checks were run against a documentation-only change set
    (`git status` confirmed zero code files modified), yet `ruff format --check` still
    failed - which isolated the violation to committed code rather than to the session's
    own edits. Confirmed pre-existing by checking that `server/tasks.py` has no working
    tree modifications.