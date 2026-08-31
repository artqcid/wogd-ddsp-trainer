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

`next_id: 5`

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

## Open bugs

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
