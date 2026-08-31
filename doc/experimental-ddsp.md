---
type: concept
status: draft
generated:
  by: primary-agent
  at: 2026-08-31
description: Experimental DDSP sound design (Musique Concrete) - rationale for milestone M7; fact-vs-speculation tagged
stale_after: 2026-12-31
tags: [ddsp, experimental, musique-concrete, m7, sound-design]
---

# Experimental DDSP - Musique Concrète & Creative Sound Design

_Knowledge base for milestone **M7** (experimental sound design). Describes why
and how to use DDSP not as an instrument-clone tool but as a creative
synthesizer. Milestone scope: [`checklist.md`](./checklist.md) (M7) and
[`implementation/m7-experimental.md`](./implementation/m7-experimental.md)
(granular steps)._

## Fact-vs-speculation legend

Every claim is tagged to distinguish verified architecture from deduction:

- `[Architektur-Fakt]` — verified against the DDSP architecture as implemented
  in the `magenta/ddsp` source (`main` branch, read 2026-08-31); DDSP concepts
  are framework-agnostic. This project implements its **own PyTorch core**;
  `magenta/ddsp` is a spec reference only.
- `[Logische Erweiterung]` — a reasonable deduction from the architecture, not
  empirically confirmed.
- `[Spekulation]` — an educated guess about model behaviour on out-of-domain
  data; treat as an experiment, not a guaranteed result.

## Background

Standard DDSP usage copies a realistic instrument (violin -> saxophone).
Feeding the system deliberately "wrong" or opening the architecture produces
glitchy or hyperreal textures. This is the goal of M7.

---

## Part 1 - Creative UI features (experimental sound design)

### 1. F0 / Pitch-curve override

- *Problem:* DDSP requires a fundamental frequency (`f0`) to drive the harmonic
  oscillator. Musique Concrète material (breaking glass, wind, creaking doors)
  often has no clear pitch; the pitch tracker (RMVPE/CREPE) will hallucinate a
  random pitch. `[Architektur-Fakt]` — the F0 source is `f0_hz` +
  `f0_confidence` (RMVPE or CREPE-PyTorch/parselmouth).
- *Feature:* an F0 editor (canvas) in the preprocessing UI. The user can delete
  the extracted pitch curve and draw arbitrary static or wildly fluctuating
  curves, forcing the model to map noise onto specific pitches.
  `[Logische Erweiterung]`.

### 2. Architecture weighting - noise vs. harmonics

- *Principle:* DDSP has two synthesis modules: a *Harmonic* additive
  synthesizer (tonal) and a *FilteredNoise* synthesizer (noise/breath).
  `[Architektur-Fakt]` — the reference implementation (`magenta/ddsp`
  `synths.py`) has `Harmonic` ("bank of harmonic sinusoidal oscillators") and
  `FilteredNoise` ("filtering white noise"); our PyTorch core mirrors these.
- *Feature:* sliders to weight the complexity of each module before training.
  For Musique Concrète: disable the harmonic oscillator (0 harmonics) and give
  the noise synthesizer many filter banks; the model then learns textures from
  filtered white noise only. `[Logische Erweiterung]`.

### 3. Reverb impulse-response (IR) extractor

- *Principle:* DDSP learns the room acoustics of the training material via a
  differentiable impulse response in the reverb module. `[Architektur-Fakt]` —
  the reverb module (reference: `magenta/ddsp` `effects.py` `Reverb`) learns a
  single dataset-wide IR as a trainable weight; in our PyTorch core this is an
  `nn.Module` with a trainable IR buffer.
- *Feature:* an "export reverb IR" button. After training on material recorded
  in a specific room, download the learned IR as `.wav` and reuse it as
  convolution reverb in a DAW. `[Logische Erweiterung]`.

---

## Part 2 - Creative training hacks (breaking the rules)

### 1. The "polyphony glitch"

- *Rule:* DDSP is monophonic only. `[Architektur-Fakt]` — the harmonic
  oscillator relies on a single unambiguous f0; see `ddsp-concepts.md`.
- *Hack:* deliberately train on highly polyphonic material (orchestral chord,
  traffic, multiple speakers).
- *Effect:* the encoder jumps rapidly between candidate f0s; the network
  attempts to reproduce polyphonic chaos with a single monophonic oscillator,
  yielding alien, bubbling or rapidly arpeggiating glitches. `[Spekulation]`.

### 2. Extreme cross-synthesis (timbre mismatch)

- *Rule:* transfer maps pitch/loudness of a source (e.g. voice) onto a trained
  target model (e.g. violin).
- *Hack:* train on hard, percussive concrete sounds (jackhammer), then use a
  slow, soft source (operatic soprano) as inference input.
- *Effect:* the network squeezes hard metallic overtones into a soft, flowing
  loudness profile, producing hybrid drones. `[Spekulation]`.

### 3. Loudness inversion / threshold hacking

- *Hack:* invert or limit the input loudness curve at inference (gate effect or
  a flat "brick" profile) via the UI.
- *Effect:* the DSP modules are forced into regimes never seen in training,
  producing strong digital distortion and new overtones. `[Spekulation]`.

---

## Part 3 - Frozen reverb / IR injection

Injecting a fixed impulse response into the trainable reverb is one of the most
powerful architectural interventions.

### Technical mechanism

- `[Architektur-Fakt]` — DDSP modules are differentiable layers (in our PyTorch
  core: `nn.Module`). A module's weights can be loaded at init and excluded
  from gradient updates (freeze / `requires_grad_(False)`).
- `[Architektur-Fakt]` — the reverb module supports exactly this: a trainable IR
  (learned) or a frozen IR injected as a fixed `.wav` tensor. The dry-signal
  masking (first IR sample zeroed) must be respected.
- The loss still compares the full chain output (synth -> injected IR) with the
  original audio. `[Architektur-Fakt]` — the multi-scale spectral loss compares
  the generated vs. target audio.

### Clean use-case - targeted de-reverberation

- *Problem:* if training audio has heavy room sound (cello in a church), the
  network tends to bake room resonances into the harmonic synthesizer, so the
  dry synth sounds washed-out. `[Logische Erweiterung]`.
- *Solution:* inject the (near-)exact room IR frozen into training.
- *Result:* the network is relieved - the rigid DSP block at the end already
  adds the room correctly, so the loss forces the oscillators to train
  perfectly dry. Turning the reverb off afterwards isolates the instrument.
  `[Logische Erweiterung]`.

### Musique Concrète hack - inverse acoustic compensation

- *What happens with a deliberately wrong IR:* train a clean, dry voice, but
  force the end-of-chain reverb to use the IR of a metal bucket, a guitar
  distortion cabinet or a long spring reverb (frozen IR). `[Spekulation]`.
- *Effect:* the network tries to reproduce the clean voice at the end of the
  chain and therefore pre-distorts the harmonic/noise synthesizer - it must
  generate the acoustic inverse of the bucket so that the output still
  approximates the clean voice. `[Spekulation]`.
- *Sound-design payoff:* detach the reverb module after training and render only
  the raw synthesizer; the result is a strange, anti-resonant, warped version of
  the source - a new texture created by an AI trying to acoustically "fight" an
  inappropriate room. `[Spekulation]`.

## References

- `checklist.md` - M7 open tasks.
- `implementation/m7-experimental.md` - granular implementation steps.
- `experimental-sdk-hacking.md` - M8 (rewriting the synth core, a deeper level
  of intervention).
- `ddsp-concepts.md` - DDSP background (signal flow, DSP modules, monophonic
  constraint).
