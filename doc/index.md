# wogd-ddsp-trainer - Knowledge Index

_Karpathy-style LLM-Wiki catalog. Each entry: link + 1-line summary + category.
This is the deterministic entry point for LLM agents and humans navigating the
codebase knowledge. Update this index whenever a new concept file is added,
removed or renamed._

_See `log.md` for the chronological append-only changelog._

---

## Architecture & Design
- [`architecture.md`](./architecture.md) - System architecture: DDSP pipeline, dataset prep, model, training loop, web backend + UI, tech stack
- [`ui-requirements.md`](./ui-requirements.md) - UI/product requirements: applies to ALL agents; DDSP phases, coupling rules, mock-data seam, component structure
- [`coding-standards.md`](./coding-standards.md) - Coding standards: Clean Code Developer (CCD) value system + compliance rule

## Operations & Quality
- [`test-strategy.md`](./test-strategy.md) - Test strategy: automated-first, test pyramid, coverage, mocking strategy (pytest/vitest)
- [`workspace-workflow.md`](./workspace-workflow.md) - Setup/run/workflow: venv, ruff/pytest, uvicorn, Vite hot-reload

## Plans & Roadmap
- [`plan.md`](./plan.md) - Draft plan: milestones M1-M6, open questions/risks, decisions
- [`checklist.md`](./checklist.md) - Open tasks only (short descriptions); the source of truth for "what's next"

## Wiki Meta
- [`code_wiki.md`](./code_wiki.md) - Auto-generated symbol index (MCP-only, never read directly)
- [`log.md`](./log.md) - Chronological append-only changelog (newest first)
