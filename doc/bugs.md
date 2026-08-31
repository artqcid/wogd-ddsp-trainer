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

`next_id: 3`

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
