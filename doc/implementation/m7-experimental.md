---
type: implementation-plan
status: in-progress
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

## Impact analysis (2026-08-31)

_Cross-stack impact of each M7 feature on presets, GPU, config, REST, UI and
backward compatibility. See [`../architecture.md`](../architecture.md) for the
current constraints._

### M7.0 Output Enhancer — Impact: LOW
- **Presets:** kein Impact (Post-Processing, kein Training-Parameter).
- **GPU/VRAM:** ~+1 GB bei Inference (separate Stufe). Mit RTX 3060 6 GB noch
  im Budget (DDSP ~0.5 GB + Enhancer ~1 GB).
- **Trainingsloop:** kein Impact (greift erst nach Training in `inference/`).
- **Backward-Komp.:** voll gegeben — `enhance: bool` Flag, default `false`.
- **REST API:** optionaler `enhance`-Parameter auf `POST /api/inference/synthesize`.
- **Empfehlung:** kann sofort, niedrigstes Risiko.

### M7.1 F0/pitch-curve Override — Impact: MEDIUM
- **Presets:** kein Impact (Preprocessing, kein Trainingsparameter).
- **GPU/VRAM:** kein Impact (CPU-only Canvas + numpy).
- **FeatureCache:** neues Key-Schema für Override-Dateien (`f0_override.npy`).
- **DataLoader:** nutzt M3.6 — Override optional, wenn nicht vorhanden läuft
  CREPE wie bisher.
- **UI:** neue isolierte Komponenten `F0Editor.vue` + `F0RulesPanel.vue`.
- **Empfehlung:** parallel zu M7.0 machbar.

### M7.2 DDSP Component Mixer — Impact: HIGH (cross-stack)
- **ParameterBounds MUSS erweitert werden:** aktuell nur `hidden_size`,
  `stft_scales`, `mixed_precision`, `gradient_checkpointing`. Es fehlen
  `n_harmonics_min/max` und `n_filter_banks_min/max`.
- **GPU-Bounds-Tabelle:** neue VRAM-Tier-Mappings nötig.
- **Built-in Presets:** müssen `n_harmonics` und `n_filter_banks` bekommen
  → Schema-Change analog zu BUG-5 (backend- + frontend-seitig).
- **DDSPConfig:** `n_harmonics: int = 60` existiert, aber `n_filter_banks`
  muss als Config-Parameter durchgereicht werden (aktuell hardcoded in
  `FilteredNoiseSynth`).
- **Checkpoints:** Model-Config ändert sich — Load muss fehlende Felder tolerieren.
- **Empfehlung:** aufwändigster Punkt, zuletzt angehen.

### M7.3 IR Injection — Impact: depends on M7.3.0 decision
- **Option A** (trainable IR conv): **bricht Checkpoint-Kompatibilität** —
  `SimpleReverb` wird durch `nn.Parameter` IR ersetzt. Alte Checkpoints nicht
  ladbar.
- **Option B** (fixed kernel tauschen): harmlos, kein Architektur-Change.
- **Presets:** kein Impact.
- **GPU/VRAM:** vernachlässigbar.
- **Empfehlung:** M7.3.0 Research zuerst, dann Option B als schnellen Einstieg.

### Ordering (implemented in this sequence)

| Priority | Feature | Grund |
|---|---|---|
| 1 | M7.0 (Output Enhancer) | Lowest risk, clean isolation, hörbarer Nutzen |
| 2 | M7.3.0 (Research SimpleReverb) | Blocking decision für M7.3 |
| 3 | M7.1 (F0-Editor) | Kein GPU/Preset-Impact |
| 4 | M7.3.1-3 (IR Injection) | Nach M7.3.0-Entscheid |
| 5 | M7.2 (Component Mixer) | Aufwändigster Punkt (ParameterBounds + Migration) |

## Steps

> **Prerequisites for M7 (must be completed first):**
> - M3.6 (real DataLoader) must be done before M7.1 F0-override can work
>   correctly on real multi-file datasets.
> - M7.0 Output Enhancer (see below) is independent and can be done in parallel
>   with M7.1–M7.4.
> - For M7.3 IR Injection: see the research step M7.3.0 — the current
>   `SimpleReverb` is a fixed FIR filter with no trainable parameters. IR
>   injection only makes sense if the reverb is made trainable. This must be
>   clarified before M7.3 is implemented.

### M7.0 Output Enhancer (deferred from M6.5)

_Moved from M6.5 to M7 (decision recorded in `checklist.md` and
`implementation/m6-polish.md`). Independent of M7.1–M7.4; can be worked on
in parallel._

- [x] **M7.0.1** **[RESEARCH]** Evaluate NSF-HiFiGAN integration options:
      - Option A: Use the original NSF-HiFiGAN PyTorch implementation as a
        post-processing step after DDSP rendering (offline only).
      - Option B: Train a lightweight vocoder jointly with the DDSP model.
      - Option C: Use a pre-trained HiFiGAN/BigVGAN checkpoint as a fixed
        post-processor.
      Document the decision in `architecture.md` and `experimental-ddsp.md`.
      Consider VRAM budget: the enhancer must fit on 6 GB alongside DDSP
      inference (Option A is most likely feasible).
- [x] **M7.0.2** **[IMPLEMENT — after M7.0.1]** Integrate the chosen enhancer
      as an optional post-processing step in `inference/render.py`.
      Files: `inference/render.py`, potentially `inference/enhancer.py`.
      Verify: renders a short audio clip through DDSP + enhancer without error.
- [x] **M7.0.3** **[IMPLEMENT]** Wire the enhancer toggle into the UI:
      add an "Apply output enhancer" checkbox to `InferencePlaygroundView.vue`
      and `ModelExportView.vue`.
      Files: `webui/src/views/InferencePlaygroundView.vue`,
             `webui/src/views/ModelExportView.vue`.
- [x] **M7.0.4** Tests + docs for the output enhancer pipeline.

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

- [ ] **M7.3.0** **[RESEARCH — blocker for M7.3.1–M7.3.3]** Clarify whether
      `SimpleReverb` needs to become a trainable module before IR injection is
      useful. The current `SimpleReverb` is a fixed FIR comb filter with no
      `nn.Parameter` — it has no learnable impulse response to inject into or
      export. Two options:
      - Option A: Replace `SimpleReverb` with a trainable IR conv (`nn.Parameter`
        of length N, e.g. 16000 samples) so the reverb "learns" the room. IR
        injection then freezes this parameter to a provided `.wav`. IR extraction
        reads the parameter back.
      - Option B: Keep `SimpleReverb` as-is; the "IR injection" just replaces
        the fixed kernel with a user-provided one. "Export" dumps the fixed kernel.
        Simpler but less interesting musically.
      Document the decision before starting M7.3.1. Impact: Option A requires
      changes to `model/ddsp/synths.py` and `model/ddsp_model.py`.
      Files (research only): `doc/experimental-ddsp.md`, `doc/architecture.md`.
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

- **2026-08-31** — M7.0.1–4 implemented (Output Enhancer):
  - M7.0.1: Vocos chosen as primary (MIT, pip-installable, HF from_pretrained), BigVGAN fallback, identity fallback.
  - M7.0.2: `inference/enhancer.py` (OutputEnhancer with 3 backends) + wired through `inference/render.py` (enhance param).
  - M7.0.3: UI checkbox in InferencePlaygroundView.vue + REST param in server/routes/inference.py + server/tasks.py pass-through.
  - M7.0.4: 7 new tests (identity fallback, shape preservation, enhance flag, default False). All 163 pytest + 23 vitest green.
  - Wiki index updated (852 symbols), ruff format clean.
