---
type: implementation-plan
status: draft
milestone: M7 - Experimental sound design (Musique Concrète)
generated:
  by: primary-agent
  at: 2026-08-31
stale_after: 2026-12-31
---

# Implementation Plan - M7 Experimental sound design

_Granular plan for milestone M7. Meta plan: [`../plan.md`](../plan.md); status:
[`../checklist.md`](../checklist.md); rationale (fact vs speculation):
[`../experimental-ddsp.md`](../experimental-ddsp.md); UI:
[`../ui-requirements.md`](../ui-requirements.md)._

## How to use

- Each step below is one small, self-contained task (approx. one subagent task).
- Work in order; mark `[x]` and record every step in `## History`.
- Bugs: full record only in [`../bugs.md`](../bugs.md); reference by `BUG-<id>`.
- **Experimental:** these features are non-binding for M1-M6 and must not break
  the core pipeline; isolate them behind feature flags / separate paths.

## Steps

### M7.1 F0/pitch-curve override editor (two-tier)

- [ ] **M7.1.1** Backend: allow a per-file custom F0 curve (override CREPE).
      Files: `dataset/features.py` (override path), `server/routes/dataset.py`.
- [ ] **M7.1.2** File-level inspector: canvas overlay on the waveform
      (draw / smooth / erase / randomize). Files: `webui/src/components/F0Editor.vue`.
- [ ] **M7.1.3** Backend: global dataset transformation rules (quantization to
      a scale, chaos/noise injection, pitch inversion).
      Files: `dataset/transforms.py`.
- [ ] **M7.1.4** Global rules UI panel (apply to whole dataset).
      Files: `webui/src/components/F0RulesPanel.vue`.

### M7.2 DDSP component mixer

- [ ] **M7.2.1** Backend: expose harmonics-vs-noise complexity config
      (`n_harmonics`, `n_filter_banks`). Files: `model/ddsp_model.py`.
- [ ] **M7.2.2** UI sliders for the mixer. Files: `webui/src/components/ComponentMixer.vue`.

### M7.3 Reverb IR injection + extractor

- [ ] **M7.3.1** Backend: load a `.wav` IR and inject it into the (frozen)
      reverb module. Files: `model/reverb_injection.py`.
- [ ] **M7.3.2** Backend: extract the learned IR as `.wav`.
      Files: `model/reverb_injection.py`.
- [ ] **M7.3.3** UI: IR upload + freeze toggle + "export IR" button.
      Files: `webui/src/components/ReverbInjection.vue`.

### M7.4 Tests + docs

- [ ] **M7.4.1** Tests for F0 override + global rules.
- [ ] **M7.4.2** Tests for mixer + IR injection/extraction.
- [ ] **M7.4.3** Finalize docs (`experimental-ddsp.md` stays authoritative).

### Future directions (not in scope)

- [ ] Shallow-diffusion post-processing (output-quality enhancer) - see
      [`../related-work.md`](../related-work.md) and checklist M6.5.

## BUGS

_References only; full records in [`../bugs.md`](../bugs.md)._

- (none)

## History

_Append-only, newest first._

- (none yet)
