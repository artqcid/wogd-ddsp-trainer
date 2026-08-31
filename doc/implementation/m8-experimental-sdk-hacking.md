---
type: implementation-plan
status: draft
milestone: M8 - Experimental synthesis hacks
generated:
  by: primary-agent
  at: 2026-08-31
stale_after: 2026-12-31
---

# Implementation Plan - M8 Experimental synthesis hacks

_Granular plan for milestone M8. Meta plan: [`../plan.md`](../plan.md); status:
[`../checklist.md`](../checklist.md); rationale (fact vs speculation):
[`../experimental-sdk-hacking.md`](../experimental-sdk-hacking.md)._

## How to use

- Each step below is one small, self-contained task (approx. one subagent task).
- Work in order; mark `[x]` and record every step in `## History`.
- Bugs: full record only in [`../bugs.md`](../bugs.md); reference by `BUG-<id>`.
- **We own the DDSP core (PyTorch), so these hacks are first-class feature
  flags, not patches to an external SDK.** Keep each hack opt-in so the base
  pipeline stays reproducible.

## Steps

### M8.1 Hack infrastructure

- [ ] **M8.1.1** Add feature flags / variant config to our own DDSP core
      (opt-in hacks). Files: `model/ddsp/`.
- [ ] **M8.1.2** Wire variant selection to the UI/config (choose the hacked
      synth). Files: `server/`, `webui/`.

### M8.2 Inharmonic multipliers (bell hack)

- [ ] **M8.2.1** Make the harmonic ratios configurable (inharmonic values) in
      the harmonic synthesizer. Files: `model/ddsp/harmonic.py`.
      Verify: smoke render sounds metallic.

### M8.3 Wavetable exchange (dirt factor)

- [ ] **M8.3.1** Replace the `sin` waveform with square/sawtooth/noisy wavetable.
      Files: `model/ddsp/harmonic.py`.
- [ ] **M8.3.2** Expose the waveform choice via variant config.

### M8.4 Loss & decoder hacks

- [ ] **M8.4.1** Add a frequency-band mask to the spectral loss.
      Files: `model/losses.py`.
- [ ] **M8.4.2** Inject an LFO into the decoder->synth path.
      Files: `model/ddsp_model.py`.

### M8.5 Docs + tests

- [ ] **M8.5.1** Smoke tests per hack (CPU, small input).
- [ ] **M8.5.2** Finalize docs (`experimental-sdk-hacking.md` stays
      authoritative).

## BUGS

_References only; full records in [`../bugs.md`](../bugs.md)._

- (none)

## History

_Append-only, newest first._

- (none yet)
