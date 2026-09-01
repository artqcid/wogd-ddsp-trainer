# wogd-ddsp-trainer - Knowledge Index

_Karpathy-style LLM-Wiki catalog. Each entry: link + 1-line summary + category.
This is the deterministic entry point for LLM agents and humans navigating the
codebase knowledge. Update this index whenever a new concept file is added,
removed or renamed._

_See `log.md` for the chronological append-only changelog._

---

## Architecture & Design
- [`architecture.md`](./architecture.md) - System architecture: DDSP pipeline, dataset prep, model, training loop, web backend + UI, tech stack, M14 model tier system + backend extensions
- [`ui-requirements.md`](./ui-requirements.md) - UI/product requirements: applies to ALL agents; app shell, 4 view groups, coupling rules, mock-data seam, TensorBoard doctrine, M14 Dual-Mode Training UI (Wizard + Power-User Tabs)
- [`parameter-handling.md`](./parameter-handling.md) - Input parameter dynamics: Zwei-Schicht-Modell (Training-Config vs. Inferenz), Neutone hard-limit 4, Custom-VST 16-param, GUI ModelParameterBuilder, tier-spezifische Defaults, ParamManifest-Schema
- [`coding-standards.md`](./coding-standards.md) - Coding standards: Clean Code Developer (CCD) value system + compliance rule

## Domain Knowledge
- [`ddsp-concepts.md`](./ddsp-concepts.md) - DDSP background: definition, signal flow, DSP modules, training/loss, limitations
- [`experimental-ddsp.md`](./experimental-ddsp.md) - M7 knowledge base: Musique Concrète + reverb IR injection (fact-vs-speculation tagged)
- [`experimental-sdk-hacking.md`](./experimental-sdk-hacking.md) - M8 knowledge base: synthesis hacks on our own core (fact-vs-speculation tagged)
- [`related-work.md`](./related-work.md) - Reference: DDSP-SVC (real-time voice conversion) and its implications

## Plans & Roadmap
- [`plan.md`](./plan.md) - Meta plan: milestones M1-M14, resolved questions/decisions, risks
- [`checklist.md`](./checklist.md) - Status: open tasks per milestone (short); source of truth for "what's next"
- [`bugs.md`](./bugs.md) - Canonical bug ledger (single source of truth; `BUG-<id>` entries)
- [`implementation/m1-scaffold.md`](./implementation/m1-scaffold.md) - M1 granular steps + history
- [`implementation/m2-dataset-prep.md`](./implementation/m2-dataset-prep.md) - M2 granular steps + history
- [`implementation/m3-model-training.md`](./implementation/m3-model-training.md) - M3 granular steps + history
- [`implementation/m4-backend.md`](./implementation/m4-backend.md) - M4 granular steps + history
- [`implementation/m5-webui.md`](./implementation/m5-webui.md) - M5 granular steps + history
- [`implementation/m6-polish.md`](./implementation/m6-polish.md) - M6 granular steps + history
- [`implementation/m7-experimental.md`](./implementation/m7-experimental.md) - M7 granular steps + history
- [`implementation/m8-experimental-sdk-hacking.md`](./implementation/m8-experimental-sdk-hacking.md) - M8 granular steps + history
- [`implementation/m9-alternative-synth-engines.md`](./implementation/m9-alternative-synth-engines.md) - M9 granular steps (Sinusoidal, CombSub, colored noise, granular noise)
- [`implementation/m10-newt.md`](./implementation/m10-newt.md) - M10 granular steps (Neural Waveshaping Unit, SawtoothExciter)
- [`implementation/m11-latent-space.md`](./implementation/m11-latent-space.md) - M11 granular steps (VAE encoder, β-VAE loss, morphing, latent steering)
- [`implementation/m12-polyddsp.md`](./implementation/m12-polyddsp.md) - M12 granular steps (PolyDDSP, multi-pitch tracker, N-voice model)
- [`implementation/m13-voice-conversion.md`](./implementation/m13-voice-conversion.md) - M13 granular steps (HuBERT/ContentVec, VC pipeline, VoiceConversionView)
- [`implementation/m14-dual-mode-ui.md`](./implementation/m14-dual-mode-ui.md) - M14 granular steps: Backend-first (DB, gpu.py, presets, tasks, feasibility endpoint) then Frontend (Wizard, Tabs, Banner, store)
- [`implementation/m15-param-manifest.md`](./implementation/m15-param-manifest.md) - M15 granular steps: ParamManifest dataclass + tier-default builders, checkpoint embedding, REST GET/PUT params, dynamic Neutone wrapper, CustomVSTWrapper + export endpoint, N-param synthesize
- [`implementation/m16-param-builder-ui.md`](./implementation/m16-param-builder-ui.md) - M16 granular steps: ParamCard, ModelParameterBuilder, NeutoneSlotPanel (drag & drop), ModelExportView dual-export, InferencePlaygroundView dynamic N-param sliders
- [`implementation/m17-midi-synth-vst.md`](./implementation/m17-midi-synth-vst.md) - M17 feasibility analysis + granular steps: MidiSynthWrapper, MIDI-synth export, Usage Mode wizard step, MIDI Preview, tier-specific synth hints

## Operations & Quality
- [`handbook.md`](./handbook.md) - User manual (German): training operation only — quick start (standard model), complex models per tier, full parameter reference
- [`manual-test-protokoll.md`](./manual-test-protokoll.md) - Manual test protocol (English): end-to-end training acceptance tests, ordered from simplest (standard) to most complex (component → hacks → engine → advanced) model training; representative cases for complex tiers
- [`test-strategy.md`](./test-strategy.md) - Test strategy: automated-first, test pyramid, coverage, mocking strategy (pytest/vitest)
- [`workspace-workflow.md`](./workspace-workflow.md) - Setup/run/workflow: venv, ruff/pytest, uvicorn, Vite hot-reload
- [`oss-dependencies.md`](./oss-dependencies.md) - OSS dependency/license review (M1.6.2): every dep OSI-approved, neutone_sdk/rmvpe flagged

## Wiki Meta
- [`code_wiki.md`](./code_wiki.md) - Auto-generated symbol index (MCP-only, never read directly)
- [`log.md`](./log.md) - Chronological append-only changelog (newest first)

---

## Three-tier planning model

1. **`plan.md`** = meta plan (milestones, decisions, risks).
2. **`checklist.md`** = status: which milestone tasks are open/done.
3. **`implementation/mN-*.md`** = granular, ordered steps per milestone (one
   step = one small task) + append-only history + a `## BUGS` reference section.

Bugs are recorded in full only in **`bugs.md`**; everything else references
them by `BUG-<id>`. See `AGENTS.md` for the mandatory workflow.
