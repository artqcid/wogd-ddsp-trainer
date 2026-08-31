---
type: implementation-plan
status: implemented
milestone: M2 - Dataset prep
generated:
  by: primary-agent
  at: 2026-08-31
stale_after: 2026-12-31
---

# Implementation Plan - M2 Dataset prep

_Granular plan for milestone M2. Meta plan: [`../plan.md`](../plan.md); status:
[`../checklist.md`](../checklist.md); architecture:
[`../architecture.md`](../architecture.md)._

## How to use

- Each step below is one small, self-contained task (approx. one subagent task).
- Work in order; mark `[x]` and record every step in `## History`.
- Bugs: full record only in [`../bugs.md`](../bugs.md); reference by `BUG-<id>`.
- Features extracted are `f0_hz`, `f0_confidence`, `loudness_db` (no
  "harmonic amplitude"/"aperiodicity" - those are decoder outputs; see
  `architecture.md`).

## Steps

### M2.1 Ingestion

- [x] **M2.1.1** Implement audio loading (wav via `soundfile`/`librosa`) into a
      float32 tensor. Files: `dataset/io.py`.
      Verify: unit test loads a fixture wav to the expected shape.
- [x] **M2.1.2** Implement resampling to 16 kHz + mono downmix.
      Files: `dataset/io.py`.
      Verify: unit test asserts `16000` Hz and single channel.
- [x] **M2.1.3** Implement level normalization (peak or RMS).
      Files: `dataset/io.py`.
      Verify: unit test asserts normalized peak/RMS within bounds.

### M2.2 Feature extraction (offline)

_All features are extracted **once** during preprocessing and saved as `.npy`
files. The training loop loads pre-computed tensors — feature extraction GPU
usage does not compete with training VRAM._

- [x] **M2.2.1** Implement F0 + confidence extraction via RMVPE (or
      CREPE-PyTorch / parselmouth).
      Files: `dataset/features.py`.
      Verify: unit test with a synthetic sine returns plausible f0 + confidence.
- [x] **M2.2.2** Implement loudness extraction (A-weighted) via librosa.
      Files: `dataset/features.py`.
      Verify: unit test checks loudness range / dB scale.
- [x] **M2.2.3** Implement per-feature normalization (scale to `[0,1]`, mirroring
      ddsp `F0LoudnessPreprocessor`).
      Files: `dataset/features.py`.
      Verify: unit test asserts output in `[0,1]`.
- [x] **M2.2.4** Save extracted features as `.npy` alongside source audio (one
      `.npy` per feature per source file). The dataset loader reads pre-computed
      tensors instead of re-running extractors.
      Files: `dataset/features.py` (export) + `dataset/loader.py` (read).
      Verify: integration test: extracted, saved, reloaded — values match.

### M2.3 Split & caching

- [x] **M2.3.1** Implement train/validation split (deterministic seed).
      Files: `dataset/split.py`.
      Verify: unit test checks disjoint, reproducible split.
- [x] **M2.3.2** Implement caching dataset module (PyTorch `DataLoader` /
      on-disk cache).
      Files: `dataset/cache.py`.
      Verify: unit test confirms cache hit on second read.

### M2.4 Tests

- [x] **M2.4.1** Unit tests for feature extraction (hand-computed expected values
      where possible).
- [x] **M2.4.2** Unit tests for ingestion/resample/normalize.
- [x] **M2.4.3** Unit tests for split + caching.

## BUGS

_References only; full records in [`../bugs.md`](../bugs.md)._

- **Loudness A-weighting (open question):** `features.py` uses `librosa.feature.rms()`
  → dB conversion, but `architecture.md` and `ui-requirements.md` describe
  `loudness_db` as "A-weighted". The DDSP reference uses A-weighted loudness
  (`librosa.A_weighting`) to approximate human loudness perception. This is not
  a tracked BUG (no BUG-id yet) but must be clarified before M7:
  - If A-weighting is required for correct DDSP conditioning, update
    `dataset/features.py::extract_loudness()` to apply `librosa.A_weighting`.
  - If RMS-dB is an intentional simplification, update the documentation in
    `architecture.md` and `ui-requirements.md` to reflect this.
  **Action required:** decision + implementation or doc correction. File as BUG-id
  when actioned.

## History

_Append-only, newest first._

- **2026-08-31 — M2 implemented** (primary agent, parallel subagent delegation):
  - M2.1 `dataset/io.py` (load/resample/mono/normalize + `process_audio_file`)
    + `tests/test_io.py`.
  - M2.2 `dataset/features.py` (F0-extractor **factory**: `get_f0_extractor`
    CREPE-PyTorch primary / parselmouth fallback; loudness; per-feature
    normalize; `.npy` export) + `dataset/loader.py` + `tests/test_features.py`.
  - M2.3 `dataset/split.py` (deterministic local-RNG split) + `dataset/cache.py`
    (on-disk `FeatureCache` + `cached_feature_loader`) + tests.
  - **F0 decision (per user architecture recommendation):** CREPE-PyTorch
    (`torchcrepe`) primary/ML extractor for training/datasets (GPU);
    parselmouth lightweight CPU fallback for fast unit-tests/CI/UI preview.
    Never use CREPE in unit tests (model download → non-deterministic); tests
    are parselmouth-only. Recorded also in `architecture.md` + `oss-dependencies.md`.
  - Dependencies added to `pyproject.toml`: `torchcrepe==0.0.24`,
    `praat-parselmouth==0.4.7` (both install cleanly on py3.14; parselmouth via
    native cp314 wheel).
  - All checks green: `pytest` 36 passed, `ruff check` clean, `ruff format --check` clean.
  - Fix round (delegated back to subagents): factory call-signature mismatch
    (`compute_features` passed `hop_length` to parselmouth), loudness `ref=np.max`
    → `ref=1.0` (absolute dB, cross-file comparable), `FeatureCache.load` key-name
    recovery, split test RNG/logic corrections, ruff import/format cleanup.
