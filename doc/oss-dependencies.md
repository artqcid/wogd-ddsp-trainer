---
type: reference
title: OSS Dependency Review (M1.6.2)
description: License review of runtime + dev + frontend dependencies, confirming OSI-only compliance
status: active
generated:
  by: primary-agent
  at: 2026-08-31
stale_after: 2026-12-31
tags: [licensing, oss, dependencies, review]
---

# OSS Dependency Review

_Covers milestone M1.6.2: confirm every dependency is OSI-approved OSS (nothing
that requires paid licenses or blocks public release). The project is licensed
Apache-2.0. See [`plan.md`](./plan.md) (licensing decision) and
[`implementation/m1-scaffold.md`](./implementation/m1-scaffold.md)._

## Rule

Every runtime, dev and frontend dependency must be OSI-approved open source.
Vendored components (e.g. inside torch) are fine as long as they are
OSI-licensed; nothing may require a paid license or prohibit the project's
Apache-2.0 public release.

## Python runtime

| Package | License (SPDX) | OSI? | Notes |
|---|---|---|---|
| torch | Apache-2.0 AND Apache-2.0 WITH LLVM-exception AND BSD-2-Clause AND BSD-3-Clause AND BSL-1.0 AND MIT | yes | BSL-1.0 = Boost, OSI-approved |
| torchaudio | BSD-3-Clause (matches torch) | yes | built against torch's stable ABI |
| numpy | BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0 | yes | all OSI |
| librosa | ISC | yes | |
| soundfile | BSD-3-Clause | yes | `libsndfile` binding |
| fastapi | MIT | yes | |
| uvicorn | BSD-3-Clause | yes | |
| celery | BSD-3-Clause | yes | |
| redis (redis-py) | MIT | yes | |
| rmvpe (GitHub) | to-verify | pending | see M1.7; canonical PyTorch repo's license must be confirmed |
| neutone_sdk | LGPL + "Other/Proprietary" classifier | **verify** | **deferred from M1; resolve before M3.4 (export)** — see below |
| onnxruntime (if via rmvpe) | MIT | yes | only if rmvpe requires it |

## Python dev

| Package | License (SPDX) | OSI? |
|---|---|---|
| ruff | MIT | yes |
| pytest | MIT | yes |
| pytest-cov | MIT | yes |

## Web / frontend

| Package | License (SPDX) | OSI? |
|---|---|---|
| vue | MIT | yes |
| vite | MIT | yes |
| pinia | MIT | yes |
| vitest | MIT | yes |
| wavesurfer.js | BSD-3-Clause | yes |
| axios (planned) | MIT | yes |

## Action items

1. **rmvpe (M1.7):** confirm the exact upstream repo + its license before
   first use in M2 (feature extraction).
2. **neutone_sdk (M3.4):** metadata lists `License: LGPL` with an
   `Other/Proprietary License` classifier. Confirm the effective license of the
   `neutone_sdk` PyPI package (and the Neutone SDK / Qosmos codebase) before
   adopting it as an export dependency. If it is not clearly OSI-approved, plan
   the export path (M3.4) around TorchScript/ONNX directly instead.
