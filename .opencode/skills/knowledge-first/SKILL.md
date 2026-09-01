---
name: knowledge-first
description: Mandatory navigation workflow — always start every task by loading doc/index.md, then follow the 5-step RAG-first lookup chain before any edit.
---

# Navigation & Knowledge First

## When to use

Load this skill at the START of every task (read/edit/build) to enforce the correct knowledge lookup order. Never skip step 1.

## The lookup chain (MANDATORY)

Before EVERY task, follow these steps in order. Stop at the first step that succeeds.

### Step 1: `doc/index.md` — always load first

The LLM-Wiki catalog links to every concept file, plan, checklist, and implementation plan. Navigate from here to find what you need.

### Step 2: Concept files

If the index points to a concept file, read or query it directly (architecture.md, plan.md, checklist.md, implementation plans, etc.).

### Step 3: Code-Wiki via MCP

Use `query_code_wiki("<symbol>")` via MCP for code-level symbol lookup (classes, functions, methods with file + line numbers).

### Step 4: RAG search (fallback)

Only if steps 1-3 fail: use `query_code_rag(..., format="compact")` to find relevant code chunks, then `get_rag_chunk("<id>")` for full source.

### Step 5: Special files

- `doc/code_wiki.md` must NEVER be loaded via `read()` — MCP query only.
- `doc/ui-requirements.md` — always loaded for UI-/product-relevant tasks. It is the single source of truth for product/UI requirements and binds ALL roles.

## Planning tiers (for milestone work)

Three files drive milestone execution; keep them in sync:

1. **`doc/plan.md`** — meta plan (milestones, decisions, risks). High-level only.
2. **`doc/checklist.md`** — status: which milestone tasks are open/done.
3. **`doc/implementation/mN-*.md`** — granular, ordered steps per milestone (one step = one small, self-contained task) plus append-only `## History` and `## BUGS` reference section.

When working on a milestone, open the matching `doc/implementation/mN-*.md` first. Mark steps `[x]` and append to `## History` as work proceeds.

## MCP-First workflow (no exceptions)

- `doc/code_wiki.md` must NEVER be loaded via `read()` — query via MCP.
- Every agent with MCP access MUST use `query_code_wiki` / `query_code_rag` / `get_rag_chunk`.
- Project and SDK files should be read only with `offset`/`limit` — never whole files.
- Anything found once via MCP is never searched again.