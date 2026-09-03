---
type: implementation-plan
status: draft
milestone: M20 - Audio quality & training UX bug batch (BUG-59..67)
generated:
  by: ARCHITECT_Openrouter
  at: 2026-09-03
stale_after: 2027-06-01
---

# Implementation Plan — M20 Audio Quality & Training UX Batch

_Granular plan for the BUG-59..67 batch (Group B). Meta plan:
[`../plan.md`](../plan.md); status: [`../checklist.md`](../checklist.md); full bug
records: [`../bugs.md`](../bugs.md) (single source of truth — never duplicate them
here); binding UI spec: [`../ui-requirements.md`](../ui-requirements.md)
§"Audio-quality & training-UX controls (BUG-59..67)".
Prerequisite: M19 (`m19-bug-fixes.md`) — the SPA/training lifecycle must work before
audio-quality work is testable end to end._

---

## Goal

Nine open bugs (BUG-59..67) move the project from "16 kHz speech-quality prototype"
to "48 kHz production-quality DDSP trainer with usable pitch-tracking controls".

**Central architectural insight:** three of the nine bugs (BUG-59, BUG-60, BUG-61) all
write new keys into the feature-cache metadata and all invalidate every previously
extracted `.npy` feature set. Executed in the wrong order they force the user through
**three** full re-preprocessing passes. Executed as one ordered batch in the order
**BUG-60 → BUG-61 → BUG-59** they collapse into **one** pass. That ordering is the
single most important constraint in this plan.

A second constraint is a hard safety gate: BUG-59 sub-step (a) — flipping the pipeline
to 48 kHz — must **never** land without sub-step (b), the rate-aware VRAM estimator.
(a) alone makes the feasibility check under-report by ~3× and the wizard will
green-light configurations that OOM on the project's own minimum target hardware
(RTX 3060 Laptop, 6 GB). See the atomicity warning in `bugs.md` BUG-59 §resolution.

---

## Dependency graph

```
Phase 1 — feature-cache batch (ONE re-preprocessing pass, strict order)

M20.1  BUG-60  F0 range backend        ──> M20.2  BUG-60  F0 range UI
                                            │
M20.3  BUG-61  viterbi backend         ──> M20.4  BUG-61  viterbi UI
                                            │
M20.5  BUG-67  pitch-range panel       ────┘  (same file as M20.2 — sequential)

M20.6  BUG-59a sample_rate threading   ──┐
M20.7  BUG-59b rate-aware VRAM         ──┴─ ATOMIC: never ship .6 without .7
                                            │
M20.8  BUG-59c sample_rate UI          ────┘

Phase 2 — independent of the cache batch

M20.9   BUG-64  ModelCard backend      ──> M20.10 BUG-64  ModelCard UI
M20.11  BUG-65a YIN doc notes          ──> M20.12 BUG-65b inference/yin.py
M20.13  BUG-63a total_chunks backend   ──> M20.14 BUG-63b epoch hint UI
M20.15  BUG-66  TensorBoard audio      ─── requires M20.6 (config.sample_rate)
M20.16  BUG-62a warm-start backend     ──> M20.17 BUG-62b asset + UI
```

**Rationale for the order:** Phase 1 is ordered purely to protect the user from
repeated re-preprocessing. Within it, each bug's backend step precedes its UI step so
the UI is never built against a non-existent field. Phase 2 bugs are independent of
the feature cache; BUG-66 and BUG-62 are the exceptions — both consume
`config.sample_rate` / the 48 kHz default and therefore sit after M20.6.

---

## Steps

### Phase 1 — feature-cache batch

#### M20.1 — BUG-60a: thread the F0 range down to both trackers

**Files:** `dataset/features.py`, then `server/tasks.py`, then
`server/routes/dataset.py`, then `server/routes/training.py`, then
`server/presets.py` — **one file per subagent, sequential**.

Note the corrected premise: `extract_f0_crepe()` and `extract_f0_parselmouth()`
**already accept** the range (`fmin`/`fmax` and `f0_min`/`f0_max` respectively, both
defaulting to 50/2000). The missing link is `compute_features()`, which does not accept
or forward the range, and the layers above it.

Key requirement: `compute_features()` must map the range onto **whichever backend is
selected** — a CREPE-only fix silently leaves parselmouth users on the wide default.
Persist `f0_min_hz`/`f0_max_hz` into the feature-cache metadata; add the Nyquist
validation (`f0_max_hz < sample_rate / 2`) at the REST layer.

**Verification:** `pytest` — assert both backends receive the configured range; assert
the Nyquist guard returns 422.

#### M20.2 — BUG-60b: F0 range inputs in the preprocessing view

**File:** `webui/src/views/PreprocessingView.vue` (single file)
**Depends on:** M20.1

Two number inputs (defaults 80/1100) above the "Run Preprocessing" button, with
client-side validation mirroring the backend guard. Per `ui-requirements.md` §7.2 an
invalid combination **disables** the Run button with an inline reason — never a silent
clamp.

**Do not** add an editable F0 range to `TabCore.vue`. The originally filed
"training-time override" was withdrawn as architecturally invalid (the range is baked
into the feature cache); TabCore gets read-only display only, in M20.8.

**Verification:** `vitest` — inputs render, validation blocks submit, values reach the
preprocess call.

#### M20.3 — BUG-61a: explicit viterbi/argmax decoder

**Files:** `dataset/features.py`, then `server/tasks.py`, then
`server/routes/dataset.py`, then `server/routes/training.py`, then
`server/presets.py` — **one file per subagent, sequential**.

`extract_f0_crepe()` currently passes **no** `decoder` argument and merely inherits
torchcrepe's Viterbi default. Add `f0_viterbi: bool = True` and pass an **explicit**
decoder. `compute_features()` forwards it to the CREPE backend and logs that it is
ignored for parselmouth (which has no equivalent switch). Persist `f0_viterbi` in the
feature-cache metadata.

**Verification:** `pytest` — assert `torchcrepe.predict` receives an explicit `decoder`
for both flag values. This test is the guard against an upstream default change
silently altering our F0 tracks.

#### M20.4 — BUG-61b: viterbi checkbox

**File:** `webui/src/views/PreprocessingView.vue` (single file)
**Depends on:** M20.3, M20.2 (same file — sequence, never parallel)

Checkbox default checked, with the pitch-slide help text. **CREPE-only:** disabled with
an explanatory hint when the parselmouth backend is active — visibly disabled, not
hidden and not silently ignored (`ui-requirements.md` §7.3).

**Verification:** `vitest` — checkbox renders; assert the disabled state on the
parselmouth backend.

#### M20.5 — BUG-67: instrument pitch-range reference panel

**File:** `webui/src/views/PreprocessingView.vue` (single file)
**Depends on:** M20.2 (same file — sequence, never parallel)

Collapsible `<details>` panel below the F0 range inputs with the inline
`PITCH_RANGES` table and a "Use this range" action per row. Inline data, no API call.
A range that would violate the Nyquist guard must surface the same warning as M20.2.

**Verification:** `vitest` — clicking "Use this range" updates both inputs.

#### M20.6 — BUG-59a: thread `sample_rate` through every layer

**Files (one per subagent, sequential):** `dataset/io.py`, `dataset/loader.py`,
`dataset/features.py`, `model/ddsp_model.py`, `train/trainer.py`, `server/tasks.py`,
`server/routes/dataset.py`, `server/routes/training.py`, `server/routes/reverb.py`,
`inference/export.py`, `server/presets.py`.

**Authoritative scope is the 9-layer threading table in `architecture.md`
§"Sample rate pipeline"** — not this list, which is only its file breakdown.

Corrected premise: `dataset/features.py` is **already** rate-parameterised. The 16 kHz
value is injected by callers and defaults; the verified hardcoding inventory is in
`bugs.md` BUG-59 §description. Three easily-missed items:

- `dataset/loader.py`'s `AUDIO_SAMPLES_PER_FRAME = 160` is a 10 ms hop **at 16 kHz** and
  must become rate-derived (`sample_rate // 100`).
- `server/tasks.py`'s synthesize path calls `torchaudio.save(..., 16000)` — it must use
  the checkpoint's stored rate.
- The **HuBERT content path is legitimately fixed at 16 kHz** (HuBERT-Soft requires it)
  and must be isolated behind its own resample, not converted.

Also: closed-enum validation (422), the 409 dataset/checkpoint mismatch guards, and
`sample_rate` stored in checkpoints.

**Verification:** `pytest` — end-to-end preprocessing at 48 kHz; 422 on an
out-of-enum rate; 409 on a dataset/run rate mismatch; HuBERT path still functional.

#### M20.7 — BUG-59b: rate-aware VRAM estimator

**File:** `train/gpu.py` (single file), then `doc/architecture.md`
**ATOMIC with M20.6 — must be merged together or M20.6 gated behind this.**

Corrected premise: `estimate_model_vram()` contains **no** sample-rate or sample-count
constants — only empirical `BASE_ESTIMATE_GB` baselines plus a docstring stating
`seq_len = 2 s @ 16 kHz` (line ~263). So this is not "recalculate a table" but "make
the baselines rate-scaled":

- add a `sample_rate` parameter to `estimate_model_vram()` and the `batch_size_max` /
  `ParameterBounds` derivation;
- scale the audio-domain terms (forward activations, backward gradients, STFT loss)
  by `sample_rate / 16000`; parameter/optimizer terms do **not** scale;
- adopt the recommended default `slice_length = 1.0 s` at 48 kHz;
- update the `architecture.md` VRAM budget section and the `gpu.py` docstring.

**Verification:** `pytest` — assert the 48 kHz estimate exceeds the 16 kHz estimate for
identical params; assert a 6 GB card is correctly reported as infeasible for the
configurations that would OOM.

#### M20.8 — BUG-59c: sample-rate UI (selector + guard)

**Files:** `webui/src/views/PreprocessingView.vue` (selector), then
`webui/src/components/TabCore.vue` (read-only display + mismatch guard), then
`webui/src/mocks/fixtures.js` — **one file per subagent, sequential**.
**Depends on:** M20.6 + M20.7. PreprocessingView also sequences after M20.5.

Per `ui-requirements.md` §7.1 and §8.1/§8.2: the selector is **authoritative in
PreprocessingView only**; TabCore shows the dataset's cached rate read-only plus the
mismatch warning and "Re-run preprocessing at N Hz" CTA (the UI half of the 409 guard).
Also add the §7.5 re-preprocessing confirmation for all three cache parameters.

**Verification:** `vitest` — selector renders with the 16 kHz hint; TabCore renders the
mismatch warning and blocks start; no editable rate field exists in TabCore.

### Phase 2 — independent bugs

#### M20.9 — BUG-64a: `ModelCard` dataclass

**Files:** `model/param_manifest.py`, then `train/trainer.py` (checkpoint embed +
restore), then `server/routes/models.py` (GET/PUT `model-card`) — one per subagent.

`ModelCard(model_name, model_author, short_description, long_description,
is_experimental=True, model_version="1.0.0")` plus
`model_card: ModelCard = field(default_factory=ModelCard)` on `ParamManifest`.
Old checkpoints without `model_card` must generate a default transparently — same
backward-compat pattern already used for `param_manifest`.

**Verification:** `pytest` — ModelCard round-trip; old-checkpoint backward compat.

#### M20.10 — BUG-64b: model card editor

**File:** `webui/src/views/ModelExportView.vue` (single file)
**Depends on:** M20.9

Collapsible "Model Card (Neutone metadata)" section above the export buttons; both
export buttons disabled while `model_name` is empty, with the reason shown inline
(`ui-requirements.md` §9).

**Verification:** `vitest` — all fields render; save issues PUT; export disabled
without a name.

#### M20.11 — BUG-65a: finish the YIN documentation

**Files:** `doc/implementation/m3-model-training.md`, then
`doc/implementation/m17-midi-synth-vst.md`.

`architecture.md` §"Realtime export pitch tracker constraint" already exists — this
step only adds the two missing cross-references (verified absent 2026-09-03). These are
the files a developer extending the export path actually reads, which is why BUG-65
stays `in-progress` until they exist.

**Verification:** `pwsh doc/lint.ps1` clean; both files mention the CREPE-offline /
YIN-realtime split.

#### M20.12 — BUG-65b: TorchScript-compatible YIN

**File:** `inference/yin.py` (**NEW** — single file), then `inference/export.py`.
**Depends on:** M20.1 (the `fmin`/`fmax` defaults must come from the configured F0
range, not hardcoded literals).

Pure-PyTorch `yin_f0(audio_frame, sample_rate, fmin, fmax)`: difference function →
cumulative mean normalized difference → absolute threshold → parabolic interpolation.
No scipy, no numpy. `CustomVSTWrapper` may embed it; `NeutoneWrapper` must **not**
(the Neutone SDK supplies F0 externally).

**Verification:** `pytest tests/test_yin.py` — known-pitch sinusoids at 48 kHz
(440 / 261 / 880 Hz) within ±2 cents; TorchScript trace succeeds.

#### M20.13 — BUG-63a: expose `total_chunks` in diagnostics

**File:** `server/tasks.py` (single file)
**Depends on:** M19.4 (BUG-52 — the diagnostics endpoint must be reachable at all)

`run_preprocessing_job()` must write `total_chunks`, `avg_duration_s` and the
`slice_length` actually used into `diagnostics.json`. The originally filed resolution
assumed these fields already existed; they do not.

**Verification:** `pytest` — diagnostics payload contains all three keys.

#### M20.14 — BUG-63b: estimated-epochs hint

**File:** `webui/src/components/TabCore.vue` (single file)
**Depends on:** M20.13, and sequences after M20.8 (same file)

Read-only `≈ N epochs on selected dataset` below `max_steps`; hidden with the tooltip
when no dataset/diagnostics are available. Purely informational — never constrains
`max_steps` (`ui-requirements.md` §8.3).

**Verification:** `vitest` — renders with mock diagnostics, hidden without a dataset.

#### M20.15 — BUG-66: TensorBoard audio logging

**File:** `train/trainer.py` (single file)
**Depends on:** M20.6 — `self.config.sample_rate` does not exist before it.

Log `train_orig/0` / `train_resyn/0` (and the `val_*` pair when a validation loader
exists) every `audio_log_interval` (default `checkpoint_interval`). Cache a
deterministic reference sample from the first batch as `self._log_sample` so
reconstruction quality is comparable across steps. Log only batch item `[0]` and clip
to 3 seconds to keep event files small.

Verified context: `add_scalar` is currently the **only** `SummaryWriter` call in the
file — there are no `add_image` calls either, so spectrogram logging is equally absent
(optional follow-up, not in scope here).

**Verification:** `pytest tests/test_trainer_logging.py` — mock writer; assert
`add_audio` tags and intervals.

#### M20.16 — BUG-62a: warm-start backend

**Files:** `train/trainer.py`, then `server/tasks.py`, then
`server/routes/training.py` — one per subagent.

Canonical field name is **`warm_start_checkpoint`** (`pretrain_ckpt_path` must not
appear anywhere). Weights-only load with `strict=False` at the start of `run()`, only
when no resume `ckpt` is set; the optimizer starts fresh — that is correct for
fine-tuning and is what distinguishes warm-start from resume.

**Verification:** `pytest` — warm start loads weights and leaves optimizer state fresh;
resume still restores optimizer state.

#### M20.17 — BUG-62b: base checkpoint asset + UI

**Files:** asset fetch helper + `GET /api/assets/pretrain-base/status`, then
`webui/src/components/WizardModal.vue`, then `webui/src/components/TabCore.vue`.
**Depends on:** M20.16 and M20.6 (the base checkpoint must be generated at the 48 kHz
default to be usable), and sequences after M20.14 for TabCore.

**Asset hosting decision: download-on-first-run**, not git LFS — the repo uses no LFS
and this is an optional feature. Published as a release asset, fetched into a local
cache (`WOGD_ASSETS_DIR`) with SHA-256 verification. Graceful degradation is mandatory:
offline or failed download ⇒ the toggle is **disabled with an explanatory hint** and
training from random init proceeds normally (`ui-requirements.md` §8.4).

**Verification:** `pytest` — SHA mismatch is rejected; missing asset degrades instead
of raising. `vitest` — toggle disabled when the status endpoint reports unavailable.

---

## Execution order (flat)

```
M20.1   BUG-60a   features/tasks/routes/presets   F0 range threading (both backends)
M20.2   BUG-60b   PreprocessingView.vue           F0 range inputs + validation
M20.3   BUG-61a   features/tasks/routes/presets   explicit viterbi/argmax decoder
M20.4   BUG-61b   PreprocessingView.vue           viterbi checkbox (CREPE-only)
M20.5   BUG-67    PreprocessingView.vue           pitch-range reference panel
M20.6   BUG-59a   11 files, see step              sample_rate threading
M20.7   BUG-59b   gpu.py + architecture.md        rate-aware VRAM  [ATOMIC with M20.6]
M20.8   BUG-59c   PreprocessingView/TabCore/mocks sample_rate selector + guard
M20.9   BUG-64a   param_manifest/trainer/models   ModelCard dataclass
M20.10  BUG-64b   ModelExportView.vue             model card editor
M20.11  BUG-65a   m3 + m17 plans                  YIN doc cross-references
M20.12  BUG-65b   inference/yin.py (NEW)          TorchScript YIN
M20.13  BUG-63a   server/tasks.py                 total_chunks in diagnostics
M20.14  BUG-63b   TabCore.vue                     estimated-epochs hint
M20.15  BUG-66    train/trainer.py                TensorBoard audio logging
M20.16  BUG-62a   trainer/tasks/routes            warm_start_checkpoint
M20.17  BUG-62b   asset helper + Wizard + TabCore base model download + toggle
```

**Delegation constraints (AGENTS.md):** one file per subagent task; the primary agent
reads the diff after every step before delegating the next; subagents never build or
run tests — the primary owns `ruff`, `pytest`, `vitest`.

**Sequencing warnings:**

- `PreprocessingView.vue` is edited by M20.2, M20.4, M20.5 and M20.8 — strictly
  sequential, never parallel.
- `TabCore.vue` is edited by M20.8, M20.14 and M20.17 — strictly sequential.
- `dataset/features.py`, `server/tasks.py`, `server/routes/training.py` and
  `server/presets.py` are each touched by M20.1, M20.3 and M20.6 — the Phase 1 order is
  mandatory, and re-running these steps out of order will conflict on the same
  signatures.
- **M20.6 must not ship without M20.7.** Flipping the default to 48 kHz while the VRAM
  estimator is still calibrated to 16 kHz makes the app *broken on its own reference
  hardware* (RTX 3060 Laptop 6 GB), which is worse than the current low-quality state.

---

## Definition of Done for this batch

- All nine bugs marked `fixed` in `bugs.md` with a resolution note and a `history`
  entry (status values are limited to `open|in-progress|fixed|verified`).
- BUG-65 additionally requires both doc cross-references to exist before it may leave
  `in-progress`.
- `ruff check` + `ruff format --check` clean.
- `pytest` green, including the new `tests/test_yin.py`, the explicit-decoder
  regression test and the rate-aware VRAM assertions.
- `vitest` green, including the new PreprocessingView and TabCore coverage.
- A single re-preprocessing pass is sufficient for a user upgrading across the whole
  batch — verified manually on one dataset.
- 48 kHz training verified to run (or be correctly reported as infeasible) on the
  6 GB reference GPU.
- `index_project_code` run; `pwsh doc/lint.ps1` clean.
- `doc/log.md` appended (newest first) referencing the bugs by ID only.

---

## BUGS

Fixed by this plan: BUG-59, BUG-60, BUG-61, BUG-62, BUG-63, BUG-64, BUG-65, BUG-66,
BUG-67.

Prerequisite batch (Group A, SPA/training lifecycle): BUG-52..58 — see
[`m19-bug-fixes.md`](./m19-bug-fixes.md). BUG-63 specifically depends on the BUG-52
diagnostics fix landing first.

---

## History

- 2026-09-03 — ARCHITECT_Openrouter: plan created during the open-bug re-analysis.
  Group B previously had **no** implementation plan (only `bugs.md` sub-steps), unlike
  Group A which had `m19-bug-fixes.md`. Ordering derived from the newly discovered
  constraint that BUG-61 also invalidates the feature cache — it was missing from
  BUG-59's sequencing table, which would have cost users a third re-preprocessing
  pass. Steps reflect the code-verified corrections recorded in `bugs.md` (features.py
  already rate-parameterised; `fmin`/`fmax` already reach both trackers; no `decoder`
  argument passed at all; `gpu.py` has no rate constants; diagnostics has no
  `total_chunks`). No code changed.
