# wogd-ddsp-trainer - Knowledge Index

_Karpathy-style LLM-Wiki catalog. Each entry: link + 1-line summary + category.
This is the deterministic entry point for LLM agents and humans navigating the
codebase knowledge. Update this index whenever a new concept file is added,
removed or renamed._

_See `log.md` for the chronological append-only changelog._

---

## Architecture & Design
- [`architecture.md`](./architecture.md) - System architecture: DDSP pipeline, dataset prep, model, training loop, web backend + UI, tech stack
- [`ui-requirements.md`](./ui-requirements.md) - UI/product requirements: applies to ALL agents; app shell, 4 view groups, coupling rules, mock-data seam, TensorBoard doctrine
- [`coding-standards.md`](./coding-standards.md) - Coding standards: Clean Code Developer (CCD) value system + compliance rule

## Domain Knowledge
- [`ddsp-concepts.md`](./ddsp-concepts.md) - DDSP background: definition, signal flow, DSP modules, training/loss, limitations
- [`experimental-ddsp.md`](./experimental-ddsp.md) - M7 knowledge base: Musique Concrète + reverb IR injection (fact-vs-speculation tagged)
- [`experimental-sdk-hacking.md`](./experimental-sdk-hacking.md) - M8 knowledge base: synthesis hacks on our own core (fact-vs-speculation tagged)
- [`related-work.md`](./related-work.md) - Reference: DDSP-SVC (real-time voice conversion) and its implications

## Plans & Roadmap
- [`plan.md`](./plan.md) - Meta plan: milestones M1-M8, resolved questions/decisions, risks
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

## Operations & Quality
- [`test-strategy.md`](./test-strategy.md) - Test strategy: automated-first, test pyramid, coverage, mocking strategy (pytest/vitest)
- [`workspace-workflow.md`](./workspace-workflow.md) - Setup/run/workflow: venv, ruff/pytest, uvicorn, Vite hot-reload

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
