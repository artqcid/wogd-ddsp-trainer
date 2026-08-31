---
type: implementation-plan
status: draft
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

- [ ] **M2.1.1** Implement audio loading (wav via `soundfile`/`librosa`) into a
      float32 tensor. Files: `dataset/io.py`.
      Verify: unit test loads a fixture wav to the expected shape.
- [ ] **M2.1.2** Implement resampling to 16 kHz + mono downmix.
      Files: `dataset/io.py`.
      Verify: unit test asserts `16000` Hz and single channel.
- [ ] **M2.1.3** Implement level normalization (peak or RMS).
      Files: `dataset/io.py`.
      Verify: unit test asserts normalized peak/RMS within bounds.

### M2.2 Feature extraction (offline)

_All features are extracted **once** during preprocessing and saved as `.npy`
files. The training loop loads pre-computed tensors — feature extraction GPU
usage does not compete with training VRAM._

- [ ] **M2.2.1** Implement F0 + confidence extraction via RMVPE (or
      CREPE-PyTorch / parselmouth).
      Files: `dataset/features.py`.
      Verify: unit test with a synthetic sine returns plausible f0 + confidence.
- [ ] **M2.2.2** Implement loudness extraction (A-weighted) via librosa.
      Files: `dataset/features.py`.
      Verify: unit test checks loudness range / dB scale.
- [ ] **M2.2.3** Implement per-feature normalization (scale to `[0,1]`, mirroring
      ddsp `F0LoudnessPreprocessor`).
      Files: `dataset/features.py`.
      Verify: unit test asserts output in `[0,1]`.
- [ ] **M2.2.4** Save extracted features as `.npy` alongside source audio (one
      `.npy` per feature per source file). The dataset loader reads pre-computed
      tensors instead of re-running extractors.
      Files: `dataset/features.py` (export) + `dataset/loader.py` (read).
      Verify: integration test: extracted, saved, reloaded — values match.

### M2.3 Split & caching

- [ ] **M2.3.1** Implement train/validation split (deterministic seed).
      Files: `dataset/split.py`.
      Verify: unit test checks disjoint, reproducible split.
- [ ] **M2.3.2** Implement caching dataset module (PyTorch `DataLoader` /
      on-disk cache).
      Files: `dataset/cache.py`.
      Verify: unit test confirms cache hit on second read.

### M2.4 Tests

- [ ] **M2.4.1** Unit tests for feature extraction (hand-computed expected values
      where possible).
- [ ] **M2.4.2** Unit tests for ingestion/resample/normalize.
- [ ] **M2.4.3** Unit tests for split + caching.

## BUGS

_References only; full records in [`../bugs.md`](../bugs.md)._

- (none)

## History

_Append-only, newest first._

- (none yet)
