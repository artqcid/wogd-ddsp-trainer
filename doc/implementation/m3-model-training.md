---
type: implementation-plan
status: draft
milestone: M3 - Model + training
generated:
  by: primary-agent
  at: 2026-08-31
stale_after: 2026-12-31
---

# Implementation Plan - M3 Model + training

_Granular plan for milestone M3. Meta plan: [`../plan.md`](../plan.md); status:
[`../checklist.md`](../checklist.md); architecture:
[`../architecture.md`](../architecture.md)._

## How to use

- Each step below is one small, self-contained task (approx. one subagent task).
- Work in order; mark `[x]` and record every step in `## History`.
- Bugs: full record only in [`../bugs.md`](../bugs.md); reference by `BUG-<id>`.
- Tests run on CPU with fixed seeds (see `test-strategy.md`).

## Steps

### M3.1 Model + losses

- [x] **M3.1.1** Build the self-owned DDSP core: harmonic oscillator +
      filtered-noise + reverb synth (PyTorch `nn.Module`).
      Files: `model/ddsp/`.
      Verify: forward pass produces audio of expected shape.
- [x] **M3.1.2** Wire the decoder (GRU) conditioned on f0/loudness.
      Files: `model/ddsp_model.py`.
      Verify: outputs `amplitudes`, `harmonic_distribution`, magnitudes.
- [x] **M3.1.3** Implement the multi-scale spectral loss (PyTorch). Default
      config: 3 scales `[512, 1024, 2048]` (VRAM-efficient). The number of
      scales must be configurable from the GPU auto-detection module (see
      `architecture.md` VRAM tier table).
      Files: `model/losses.py`.
      Verify: loss returns a finite scalar.
- [x] **M3.1.4** **[IMPLEMENT]** Add `n_noise_bins: int = 32` to `DDSPConfig`
      so the parameter is persisted in checkpoints and can be restored on resume.
      Update `DDSPModel.__init__` to read `n_noise_bins` from `config` instead of
      the current hardcoded default.
      Files: `model/ddsp_model.py`.
      Verify: checkpoint save+load round-trip with a non-default `n_noise_bins`
      value succeeds without error.

### M3.2 GPU detection

- [x] **M3.2.1** Detect available GPUs (`torch.cuda`).
      Files: `train/gpu.py`.
      Verify: unit test (skip without GPU) reports devices.
- [x] **M3.2.2** Analyze GPU (VRAM) and propose optimal training parameters.
      Map VRAM to parameter tier (see `architecture.md`): hidden size, STFT
      scale count, mixed precision on/off, gradient checkpointing on/off.
      Files: `train/gpu.py`.
      Verify: unit test returns a sane suggestion dict for the host's GPU.

### M3.3 Training loop

- [x] **M3.3.1** Implement the training step (optimizer + loss + mixed
      precision). Use `torch.cuda.amp.autocast` + `GradScaler` for VRAM
      efficiency. Support gradient checkpointing on the encoder (controlled
      by GPU detection tier).
      Files: `train/trainer.py`.
      Verify: smoke test runs a few steps on GPU (or CPU fallback).
- [x] **M3.3.2** Implement checkpointing + resume.
      Files: `train/trainer.py`.
      Verify: test saves + reloads a checkpoint.
- [x] **M3.3.3** Write metrics/logs to TensorBoard.
      Files: `train/trainer.py`.
      Verify: smoke test emits an event file.

### M3.4 Inference & export

- [x] **M3.4.1** Offline render from a checkpoint (condition on f0/loudness).
      Files: `inference/render.py`.
      Verify: produces non-empty audio.
- [x] **M3.4.2** Low-latency realtime export (Neutone/TorchScript, ONNX).
      Files: `inference/export.py`.
      Verify: exports a loadable artifact.

### M3.5 Tests

- [x] **M3.5.1** Model forward test (CPU, fixed seed).
- [x] **M3.5.2** Loss test (finite, decreases on synthetic case).
- [x] **M3.5.3** Training smoke test (few steps, checkpoint save/reload).
- [x] **M3.5.4** Inference/export smoke test.

### M3.6 DataLoader (open — required for real training)

_This step was identified as a gap during the M1–M6 review (2026-08-31). The
`Trainer.run()` method and `server/tasks.py::build_tensors()` only operate on a
single pre-loaded tensor batch. Real multi-file dataset training is not yet wired
up. This step must be completed before M7 experimental features can work
correctly._

- [x] **M3.6.1** **[RESEARCH]** Decide the DataLoader contract: should
      `Trainer` accept a `torch.utils.data.DataLoader` or should `build_tensors`
      iterate over the `FeatureCache`? Considerations: chunked audio (seq_len ≤ 4 s
      @ 16 kHz), per-file f0/loudness alignment, shuffle across files,
      reproducible seed. Document the decision in `architecture.md`.
      Files (research only, no code): `architecture.md`.
- [x] **M3.6.2** **[IMPLEMENT]** Implement a `DDSPDataset` (PyTorch `Dataset`)
      that reads all `*.npy` feature files from a `FeatureCache` directory,
      chunks them into fixed-length frames, and returns `(f0, loudness,
      audio_chunk)` triples. Seed-reproducible.
      Files: `dataset/loader.py` (extend or add `DDSPDataset`).
      Verify: unit test iterates at least one epoch over a synthetic 3-file cache.
- [x] **M3.6.3** **[IMPLEMENT]** Wire `DDSPDataset` into `Trainer.run()`: accept
      an optional `DataLoader` argument; when provided, iterate over real batches
      instead of the fixed dummy tensors.
      Files: `train/trainer.py`.
      Verify: smoke test with `DDSPDataset` + `DataLoader` runs 10 steps without
      error on CPU.
- [x] **M3.6.4** **[IMPLEMENT]** Wire `DDSPDataset` into
      `server/tasks.py::build_tensors()` / `run_training_job`: replace the
      16-frame dummy fallback with a proper DataLoader-driven loop. Add a
      `logging.warning` (never silent fallback) when no cache is found.
      Files: `server/tasks.py`.
      Verify: backend training test with a real cache fixture.

## BUGS

_References only; full records in [`../bugs.md`](../bugs.md)._

- (none)

## History

_Append-only, newest first._

- **2026-08-31 — M3 tests green (8 -> 0 failures).** All M3 unit/integration
  tests now pass: `pytest` 77 passed (1 GPU-skipped), `ruff check` + `ruff
  format --check` clean on app+tests. Primary-agent delegation (subagent
  task_ids in parentheses):
  - **assert_allclose API:** `atol`-only calls raised `ValueError` on PyTorch
    2.x; added `rtol` to `test_losses.py` (2x) + `test_model.py` (1x)
    (`ses_fa9def0d4ffeplbmlHgJhZ8hou`).
  - **Forward determinism:** `FilteredNoiseSynth` consumed the global RNG each
    `forward` -> bit-different audio per call. First fixed with a per-call
    `torch.Generator` (`ses_fa9dedba2ffeyf08iV8H9FO5q8`), then (for ONNX
    exportability) refactored to a registered deterministic `noise_buffer`
    (slice in forward; generator only in `__init__`) so no `CustomObjArgument`
    leaks into the FX graph (`ses_fa9d4b448ffeKvgjwGK6X7LyKK`).
    `test_deterministic_forward` + `test_export_onnx` green.
  - **Checkpoint config mismatch:** `load_model_from_checkpoint` built the
    default (large) model, failing on small checkpoints. Now persists
    `config` (via `dataclasses.asdict`) in `Trainer.save_checkpoint` and
    rebuilds the model from it in the loader (checkpoint-written test also
    saves config). `test_load_model_from_checkpoint` green
    (`ses_fa9dc81eaffeeajr7AijoK5QYl` + retry).
  - **TorchScript export:** `SimpleReverb`'s dynamic Python control flow
    (Python-bool + in-place scatter) broke tracing. Rewrote as a fixed
    kernel buffer + `F.conv1d(..., padding="same")` (static/traceable);
    separate dtype-fix for the kernel index tensor
    (`ses_fa9d798acffe6dPaBwZf6xRIEE`, `ses_fa9d924d7ffeqhY8lc7b5bvoZk`).
    Also fixed the export test, which wrongly expected a dict key from
    `torch.jit.load` (the traced artifact returns a single audio tensor)
    (`ses_fa9d65ab1ffektGDwNFLSel0Ba`).
  - **`render_to_file` / torchcodec:** torchaudio 2.11 routes WAV writing
    through uninstalled `torchcodec`; switched to the already-declared
    `soundfile` (`_sf.write`, channels-first->frames-first transpose)
    (`ses_fa9d650c8ffeByiymYDxxz5LqG`).
  - **`train_step_reduces_loss` flakiness:** 2 steps vs a random-noise target
    never decreased reliably; switched to a fixed zero target over 80 steps
    (loss genuinely shrinks toward silence) (`ses_fa9dec99effeKz3tfbgfThfh81`).
  - **Ruff clean-up of pre-existing M3 test files:** E501 long docstrings /
    I001 import order / format in `test_gpu.py`, `test_losses.py`,
    `test_model.py` (`ses_fa9d318f5ffeTFyUF7tDNuJLbR`).

  Note: the D-subagent's first `SimpleReverb` rewrite hit the workspace's
  known small-context tool-abort failure mode (`Duplicate tool_call_id`,
  cancelled tasks) and left partially-broken code (`torch.clamp(int,int,
  tensor)`, 2-tuple `conv1d` padding); caught during primary verification and
  re-delegated. This is the M(3) test-verification gap from the earlier
  unexecuted test generation — not a scope regression of M3.1-M3.4, which
  were already committed in b22572c.
