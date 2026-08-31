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

- [ ] **M3.1.1** Build the self-owned DDSP core: harmonic oscillator +
      filtered-noise + reverb synth (PyTorch `nn.Module`).
      Files: `model/ddsp/`.
      Verify: forward pass produces audio of expected shape.
- [ ] **M3.1.2** Wire the decoder (GRU) conditioned on f0/loudness.
      Files: `model/ddsp_model.py`.
      Verify: outputs `amplitudes`, `harmonic_distribution`, magnitudes.
- [ ] **M3.1.3** Implement the multi-scale spectral loss (PyTorch). Default
      config: 3 scales `[512, 1024, 2048]` (VRAM-efficient). The number of
      scales must be configurable from the GPU auto-detection module (see
      `architecture.md` VRAM tier table).
      Files: `model/losses.py`.
      Verify: loss returns a finite scalar.

### M3.2 GPU detection

- [ ] **M3.2.1** Detect available GPUs (`torch.cuda`).
      Files: `train/gpu.py`.
      Verify: unit test (skip without GPU) reports devices.
- [ ] **M3.2.2** Analyze GPU (VRAM) and propose optimal training parameters.
      Map VRAM to parameter tier (see `architecture.md`): hidden size, STFT
      scale count, mixed precision on/off, gradient checkpointing on/off.
      Files: `train/gpu.py`.
      Verify: unit test returns a sane suggestion dict for the host's GPU.

### M3.3 Training loop

- [ ] **M3.3.1** Implement the training step (optimizer + loss + mixed
      precision). Use `torch.cuda.amp.autocast` + `GradScaler` for VRAM
      efficiency. Support gradient checkpointing on the encoder (controlled
      by GPU detection tier).
      Files: `train/trainer.py`.
      Verify: smoke test runs a few steps on GPU (or CPU fallback).
- [ ] **M3.3.2** Implement checkpointing + resume.
      Files: `train/trainer.py`.
      Verify: test saves + reloads a checkpoint.
- [ ] **M3.3.3** Write metrics/logs to TensorBoard.
      Files: `train/trainer.py`.
      Verify: smoke test emits an event file.

### M3.4 Inference & export

- [ ] **M3.4.1** Offline render from a checkpoint (condition on f0/loudness).
      Files: `inference/render.py`.
      Verify: produces non-empty audio.
- [ ] **M3.4.2** Low-latency realtime export (Neutone/TorchScript, ONNX).
      Files: `inference/export.py`.
      Verify: exports a loadable artifact.

### M3.5 Tests

- [ ] **M3.5.1** Model forward test (CPU, fixed seed).
- [ ] **M3.5.2** Loss test (finite, decreases on synthetic case).
- [ ] **M3.5.3** Training smoke test (few steps, checkpoint save/reload).
- [ ] **M3.5.4** Inference/export smoke test.

## BUGS

_References only; full records in [`../bugs.md`](../bugs.md)._

- (none)

## History

_Append-only, newest first._

- (none yet)
