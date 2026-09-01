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

## M13 Implementation Notes

Our voice conversion (VC) pipeline mirrors the DDSP-SVC architecture, implemented
in our own PyTorch stack. Key differences:

- **DDSP core:** We use our own `DDSPModel` + `DDSPCore` (harmonic oscillator, filtered
noise, reverb) instead of the DDSP-SVC `CombSubSynth` comb-filter subtractive model.
This gives us full control over the synthesis engine.
- **Content encoder:** HuBERT-Soft (MIT, `bshall/hubert-soft`) extracts 256-dim
semantic embeddings at 50 Hz (320-sample hop at 16 kHz). These are linearly
interpolated to match our DDSP frame rate (125 Hz, 128-sample hop).
- **Offline extraction:** Content embeddings are extracted once per dataset during
preprocessing and cached as `content_embedding.npy`, identical to the existing
`f0_hz.npy` / `loudness_db.npy` pattern.
- **Frozen encoder:** The content encoder weights are never updated during training.
Only the DDSP decoder + synth are trained, keeping VRAM usage low (~1.9 GB total
with HuBERT loaded).
- **Conditioning:** The projected content embedding (256→64 via linear) is concatenated
with f0 and loudness as the GRU input. This replaces the f0+loudness-only
conditioning from the standard DDSP autoencoder.
- **Signal flow:** `ContentEncoder → (content, f0, loudness) → GRU decoder →
DDSP synth params → audio`.

### Use cases

- **Timbre transfer:** Train on target speaker A, run inference with source speaker
B's audio → output sounds like A saying B's words.
- **Cross-language VC:** Content encoder captures phoneme-agnostic prosody, enabling
conversion across languages.
- **Creative misuse:** Train on sung audio and convert spoken content → melodic voice
synthesis.

### Dependencies

- `huggingface_hub` (already installed) for downloading HuBERT-Soft weights.
- ContentVec (`lengyue233/content-vec-best`, MIT) is declared but not yet implemented.
