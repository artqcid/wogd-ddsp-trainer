---
type: concept
status: draft
generated:
  by: primary-agent
  at: 2026-08-31
description: Experimental DDSP synthesis hacks on our own PyTorch core - rationale for milestone M8; fact-vs-speculation tagged
stale_after: 2026-12-31
tags: [ddsp, experimental, synthesis-hacks, m8, pytorch]
---

# Experimental DDSP - Synthesis Hacks (M8)

_Knowledge base for milestone **M8** (experimental synthesis hacks). We own the
DDSP core in PyTorch, so these hacks are first-class feature flags rather than
patches to an external SDK. Milestone scope:
[`checklist.md`](./checklist.md) (M8) and
[`implementation/m8-experimental-sdk-hacking.md`](./implementation/m8-experimental-sdk-hacking.md)
(granular steps)._

## Fact-vs-speculation legend

- `[Architektur-Fakt]` — a fact about the DDSP architecture; verified against
  the reference implementation `magenta/ddsp` (`main` branch, read 2026-08-31).
  DDSP concepts are framework-agnostic; our own core mirrors them in PyTorch.
- `[Logische Erweiterung]` — a reasonable deduction, not empirically confirmed.
- `[Spekulation]` — an educated guess about model behaviour; treat as an
  experiment, not a guaranteed result.

The architectural anchors below are factual; the described *sound effects* are
logical deductions unless marked otherwise.

---

## 1. Inharmonic multipliers (the "bell" hack)

- **Architecture:** the harmonic synthesizer generates overtones by multiplying
  the fundamental frequency (`f0`) by integers. `[Architektur-Fakt]` — reference
  `magenta/ddsp` `core.py` `get_harmonic_frequencies` uses
  `f_ratios = linspace(1, n_harmonics)`; our core mirrors this.
- **Hack:** make the multiplier array configurable with inharmonic values (e.g.
  `1.0, 1.414, 2.73, 3.14`).
- **Result:** the model must reconstruct training audio (e.g. speech) with an
  unnatural, metallic oscillator bank; the result keeps the speech rhythm but
  sounds cast in bronze, like a bell or gong. `[Spekulation]`.

## 2. Wavetable exchange (the "dirt" factor)

- **Architecture:** the harmonic synthesizer calls `sin()` at the lowest level
  to generate pure sine waves. `[Architektur-Fakt]` — reference `magenta/ddsp`
  builds `wavs = tf.sin(phases)`; ours uses `torch.sin`. DDSP also has a native
  `Wavetable` and `Sinusoidal` synth concept.
- **Hack:** replace `sin` with another curve - square wave (`sign(sin)`),
  sawtooth, or a tiny noisy wavetable sample.
- **Result:** the network steers hundreds of overtone-rich square waves; even
  soft training data yields raw, chiptune-like or industrial textures because
  the sharp edges cannot be trained away. `[Spekulation]`.

## 3. Frequency-band blindness (loss-function hacking)

- **Architecture:** the multi-scale spectral loss compares original and
  generated audio over the full spectrum via FFT at multiple scales.
  `[Architektur-Fakt]` — reference `magenta/ddsp` `SpectralLoss` uses
  `fft_sizes=(2048,...,64)`.
- **Hack:** multiply specific frequency bands by zero before the error is
  computed (e.g. everything between 200 Hz and 2 kHz).
- **Result:** the model becomes blind to the mid-range and generates erratic
  parameters there (no penalty), while bass and treble still match - producing
  algorithmic noise/whistling in the mids: a glitch aesthetic. `[Spekulation]`.

## 4. Hardcoded LFO injection (decoder bypass)

- **Architecture:** the decoder (GRU) outputs clean, frame-wise amplitudes and
  harmonic/noise magnitudes to the synthesizer. `[Architektur-Fakt]` —
  reference `magenta/ddsp` `RnnFcDecoder` (`rnn_type='gru'`) outputs `amps` and
  `harmonic_distribution`.
- **Hack:** inject a hard mathematical modulation directly in the graph before
  the synthesizer, e.g. multiply the noise magnitudes by a fast LFO
  (`torch.sin(time_steps * high_freq)`).
- **Result:** the network must fight an unavoidable amplitude modulation to hit
  the target; it tries to generate phase shifts to cancel the LFO, producing
  stuttering, granular, tearing audio artefacts. `[Spekulation]`.

---

## Practical notes

- `[Architektur-Fakt]` — because we own the core (PyTorch), each hack is a
  configurable feature flag, not a source patch to a third-party library. This
  makes the hacks trivially combinable and reversible.
- Licensing: `magenta/ddsp` and `acids-ircam/ddsp_pytorch` are Apache-2.0, so
  using them as spec references is fine (OSI-only rule). `[Architektur-Fakt]`.
- These hacks are a deeper intervention than M7 (which uses the core as-is);
  keep M7 and M8 changes isolated (separate variants) so the base pipeline
  remains reproducible. `[Logische Erweiterung]`.

## References

- `checklist.md` - M8 open tasks.
- `implementation/m8-experimental-sdk-hacking.md` - granular implementation steps.
- `experimental-ddsp.md` - M7 (uses the core as-is).
- `ddsp-concepts.md` - DDSP background.
