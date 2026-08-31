---
type: concept
status: draft
generated:
  by: primary-agent
  at: 2026-08-31
description: Related work - DDSP-SVC (real-time singing voice conversion) and its implications for wogd-ddsp-trainer
stale_after: 2026-12-31
tags: [related-work, ddsp-svc, voice-conversion, reference, framework-decision]
---

# Related Work - DDSP-SVC

_Analysis of [yxlllc/DDSP-SVC](https://github.com/yxlllc/DDSP-SVC) (MIT) - a
real-time singing-voice-conversion (SVC) system built on DDSP - and what it
means for this project. This analysis motivated the framework decision to use
**PyTorch** (see `plan.md`). Complements [`ddsp-concepts.md`](./ddsp-concepts.md)
(domain background) and [`architecture.md`](./architecture.md) (our pipeline)._

## What it is

DDSP-SVC is a real-time, end-to-end singing voice conversion system. It reuses
the DDSP *idea*, reimplements it in **PyTorch**, and pairs it with a pretrained
content encoder (HubertSoft / ContentVec) and a vocoder-based enhancer
(NSF-HiFiGAN). Newer versions add a "shallow diffusion" post-processor.

## Architectural differences vs. our project

| Aspect | DDSP-SVC | wogd-ddsp-trainer |
|---|---|---|
| Framework | PyTorch (DDSP reimplemented) | PyTorch + torchaudio (self-owned DDSP core) |
| Conditioning | pretrained content encoder (Hubert/ContentVec) + F0 | autoencoder: `f0_hz` + `loudness_db` |
| Synthesizer | "combsub" (comb/subtractive) + "sins" (sinusoid additive) | harmonic + filtered-noise (+ reverb) |
| Output quality | raw DDSP output low -> vocoder enhancer / shallow diffusion | vocoder enhancer scoped in M6.5 |
| F0 extraction | parselmouth (default), crepe, harvest, dio, rmvpe | RMVPE (or CREPE-PyTorch/parselmouth) |
| Real-time | sliding window + crossfade + SOLA / phase-vocoder splicing | Neutone/TorchScript + ONNX export |
| Extras | multi-speaker, `export_onnx.py`, VST forks | single-timbre; Neutone/ONNX/TorchScript |

## Why this motivated the PyTorch decision

1. **`magenta/ddsp` (TensorFlow) is legacy**: the parent `magenta` org is
   archived; "will ddsp be updated?" (Jan 2025) is unanswered. The active DDSP
   ecosystem (DDSP-SVC, DiffSinger/OpenVPI, RAVE) is PyTorch.
2. **Neutone - our own export target - is PyTorch/TorchScript-only.** The
   `neutone_sdk` wraps only PyTorch models; a TF stack could not produce the
   Neutone export listed in `ui-requirements.md`.
3. **The enhancer path is PyTorch-native**: NSF-HiFiGAN and shallow diffusion
   are PyTorch; with PyTorch we use them directly (M6.5) instead of needing a
   "TF-compatible" port.

## Lessons for wogd-ddsp-trainer

1. **Raw DDSP output is not studio-grade.** DDSP-SVC explicitly notes "the
   original synthesis quality of DDSP is not ideal" and lifts it with a
   pretrained vocoder enhancer (NSF-HiFiGAN) or shallow diffusion. A post-hoc
   output enhancer is scoped in M6.5.
2. **Content encoder instead of f0+loudness.** For voice conversion the de-facto
   standard is a pretrained semantic encoder (Hubert/ContentVec) as input, not
   the autoencoder. A candidate experimental extension for M7/M8 (fits
   naturally with PyTorch).
3. **Real-time != export.** True real-time requires splicing logic (sliding
   window, crossfade, SOLA/phase-vocoder). Our M5 realtime target must account
   for this beyond a mere TorchScript/ONNX export.

## Other relevant points

- Confirms our M7/M8 direction: alternative synth topologies (combsub/sins) and
  multiple F0 extractors mirror our "component mixer" (M7) and "synthesis
  hacks" (M8). Note `magenta/ddsp` already ships `Wavetable`/`Sinusoidal`
  natively (concepts we mirror).
- MIT license - OSI-approved, usable as reference/inspiration (no fork needed).
- Multi-speaker + speaker mixing (`-mix`) - possible future extension.
- `flask_api.py` / `webui.py` - REST/UI reference for our M4/M5.

## References

- [`checklist.md`](./checklist.md) - M6.5 output enhancer.
- [`implementation/m6-polish.md`](./implementation/m6-polish.md) - enhancer steps.
- [`ddsp-concepts.md`](./ddsp-concepts.md) - DDSP background.
