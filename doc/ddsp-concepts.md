---
type: concept
status: stable
generated:
  by: wiki-update
  at: 2026-08-31
description: Domain background on DDSP (Differentiable Digital Signal Processing) - definition, signal flow, synthesis modules, training/loss, limitations
stale_after: 2026-12-31
---

# DDSP Concepts (Domain Background)

_Background knowledge for the DDSP-based synthesis in this project. Complements
[`architecture.md`](./architecture.md) (project pipeline) and
[`plan.md`](./plan.md) (milestones/decisions)._

## Definition & core idea

DDSP (Differentiable Digital Signal Processing) is a machine-learning framework
for neural audio synthesis, first introduced in 2020 by Google Magenta (paper
by Jesse Engel et al.). Instead of generating audio sample-by-sample from
nothing (like black-box models such as WaveNet), DDSP uses classic,
physically-motivated DSP modules - oscillators, filters, reverb - that are made
fully differentiable so a neural network can learn to control their parameters
via standard backpropagation. Advantages: extreme data efficiency (often less
than 13 minutes of audio suffice for training), high model interpretability and
direct control of musical parameters such as pitch and loudness.

## Signal flow (modified autoencoder)

The DDSP signal flow is typically built as a modified autoencoder:

1. **Feature extraction (encoder):** instead of processing raw audio, the
   system extracts primary control signals - typically the fundamental
   frequency (f0 / pitch) and the loudness contour.
2. **Network (decoder):** a neural net maps these control signals onto hundreds
   of detailed synthesizer parameters per frame.
3. **Synthesis (DSP chain):** the predicted parameters drive the differentiable
   synthesis modules that generate the final audio.

## Differentiable synthesis modules (DSP components)

- **Harmonic additive synthesizer:** sums sine waves (harmonics) whose
  frequencies are integer multiples of the fundamental frequency (f0) to shape
  the timbre of tonal instruments.
- **Filtered noise synthesizer:** passes white noise through time-varying
  filters to model noisy components (such as the scratch of a bow).
- **Differentiable reverb:** convolves the synthesized signal with a learned
  impulse response (IR) to reproduce the original room characteristics of the
  training audio. The IR can also be injected/frozen for de-reverberation and
  "inverse acoustic compensation" hacks (see `experimental-ddsp.md`).

## Training & loss functions

Training primarily uses the **multi-scale spectral loss (MSS loss)**. Because
the model does not need to reproduce the exact audio waveform, the loss
compares spectrograms of the generated and original audio at several
resolutions (window sizes).

**Data requirement:** the standard DDSP model needs clean, monophonic
(single-voice) audio material. Polyphonic audio leads to pitch-tracking errors
in the standard model, because the harmonic oscillator relies on a single
unambiguous fundamental frequency (f0). This motivates the monophonic data
constraints reflected in the UI requirements.

## Applications

The primary application is **timbre transfer**: a user sings a melody, DDSP
extracts pitch and loudness and re-synthesizes the melody with the timbre of a
trained instrument. Related applications are neural audio plugins (VSTs) for
real-time synthesis in digital audio workstations (DAWs) and pitch-to-MIDI
control. In this project the relevant application is speech synthesis, exposed
through the playground/inference views.

- Voice conversion (SVC): [`related-work.md`](./related-work.md) analyzes
  DDSP-SVC (real-time singing voice conversion) as a reference architecture.

## Polyphony

Standard DDSP is strictly monophonic: one fundamental frequency (f0) drives one
harmonic oscillator bank. **PolyDDSP** extends this to *N* parallel DDSP voices,
each driven by its own f0 track extracted by a multi-pitch tracker. The outputs
are summed and normalised to mono audio.

### Voice assignment strategy

- **Shared decoder weights (default):** a single `DDSPModel` instance is called
  *N* times, once per voice. This uses N× less VRAM than independent decoders
  and is suitable for most use cases on consumer GPUs (RTX 3060 6 GB).
- **Independent decoders:** each voice has its own `DDSPModel` with separate
  weights, allowing voices to specialise per timbre or register. VRAM
  consumption scales linearly with N.

### VRAM implications

| N voices | hidden_size=256 | hidden_size=128 |
|----------|----------------|----------------|
| 1        | ~1.3 GB        | ~0.7 GB        |
| 2        | ~2.5 GB        | ~1.3 GB        |
| 4        | ~5 GB (tight)  | ~2.5 GB        |

- Recommended maximum: N = 2–3 for RTX 3060 6 GB.
- At N ≥ 4, reduce `hidden_size` to 128 or use gradient checkpointing.

### Multi-pitch tracker

PolyDDSP uses **torchcrepe in top-K candidate mode**: CREPE returns 256 pitch
candidates per frame; the K highest-confidence candidates are assigned to the N
voices. Unvoiced frames are set to 0.0 Hz. The tracker runs offline during
dataset preprocessing and is not invoked during training.

### Configuration

- `n_voices` (int, default 1): number of parallel DDSP voices.
- `n_voices_independent` (bool, default False): use independent decoders per
  voice. Hard-clamped to ≤ 4 to protect VRAM.

### Checkpoint compatibility

Checkpoints with different `n_voices` are incompatible and trigger a
`ValueError` on load. The checkpoint is tagged with `state["n_voices"] = N`.

## Limitations

- Pitch-tracking quality during preprocessing is a bottleneck; with too-noisy
  audio the encoder fails.
- Alternatives such as RAVE (Realtime Audio Variational autoEncoder) work via
  adversarial training on latent-space representations instead of pure DSP
  control and can handle polyphonic material more flexibly.
- The creative *misuse* of the monophonic/polyphonic constraints (polyphony
  glitch, IR injection, and SDK-level rewriting) is explored in
  [`experimental-ddsp.md`](./experimental-ddsp.md) (M7) and
  [`experimental-sdk-hacking.md`](./experimental-sdk-hacking.md) (M8).
