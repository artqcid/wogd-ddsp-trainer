# AGENTS.md

## Language Rule

All agent rules, instructions, and agent-facing documentation in this workspace
**must be written in English**. This applies to AGENTS.md, skill files
(`.opencode/skills/**/SKILL.md`), agent system prompts, and any other
agent-facing configuration.

## Mandatory Workflow (single source of truth for ALL agents)

This section is the **single source of truth** for every workflow rule in this
workspace. It applies to all workspace agents. The global agents `build` and
`plan` are NOT workspace-specific and must never receive workspace-specific
prompts or settings.

### Navigation & Knowledge First (MANDATORY — always start here)

Before every task (read/edit/build):

1. **`doc/index.md` — always load first.** The LLM-Wiki catalog links to every
   concept file. Navigate from here to find what you need (architecture, plan,
   checklist, implementation plan, etc.).
2. If the index points to a concept file, read or query it directly.
3. **`query_code_wiki("<symbol>")`** via MCP for code-level symbol lookup.
4. Only if both fail: `query_code_rag(..., format="compact")` + `get_rag_chunk("<id>")`.
5. **`doc/code_wiki.md` must NEVER be loaded via `read()` — MCP query only.**
6. **`doc/ui-requirements.md` — always loaded for UI-/product-relevant tasks.**
   It is the single source of truth for the product/UI requirements and binds
   ALL roles (architecture, implementation, review, tests).

The **MCP-First workflow** section below provides the full RAG tooling reference.

### Todo-first workflow + Autopilot (gated by explicit plan approval)

- **No permission prompts.** All tools are allowed (edit, bash, read, glob,
  grep, list, task, todowrite, question, webfetch, websearch, skill, external_directory).
- **Work outside the workspace is always allowed** without asking.
- **Todo-first workflow (mandatory):** before starting ANY work on a task:
  1. Break the task into concrete, ordered steps.
  2. Create a todo list via `todowrite` with each step marked `pending`.
  3. Present the plan to the user in the response.
  4. **STOP. Wait for explicit user confirmation** ("go", "ok", "ja", "yes",
     "do it", or similar) before executing the first step. No confirmation →
     no execution.
  5. Update todo status to `in_progress` / `completed` as work proceeds.
- **Autopilot applies ONLY AFTER the todo list is confirmed.** Once the user
  has explicitly approved the plan, execution is autonomous: never ask for
  permission again — proceed until the task is complete.

### MCP-First workflow (RAG / Code-Wiki)

The workspace provides a local RAG + Code-Wiki MCP server (`wogd_ddsp`, see
`wogd_ddsp_mcp_server.py`). Tools: `index_project_code`, `query_code_rag`,
`query_code_wiki`, `get_rag_chunk` (called with server prefix, e.g.
`wogd_ddsp_query_code_wiki`).

**MCP-FIRST (no exceptions):**
- `doc/code_wiki.md` must NEVER be loaded via `read()` — query via MCP.
- Every agent with MCP access MUST use `query_code_wiki` / `query_code_rag` / `get_rag_chunk`.
- Project and SDK files should be read only with `offset`/`limit` — never whole files.
- Anything found once via MCP is never searched again.

### Subagent rules

**Autonomy (important):** The todo-first / wait-for-approval workflow applies
ONLY to the primary agent. Subagents do NOT wait for approval — the primary's
delegation prompt IS their "go". A subagent executes its single task
autonomously from start to finish and then returns its report.

**Delegation:**
- Escalate architectural questions upward; delegate small, focused
  implementation/search tasks to subagents (`general`, `explore`).

**Task size & context limits (MANDATORY — subagents have small context windows):**
- Give each subagent ONE small, single-step task only.
- Break large work into a CHAIN of small subagent tasks, not one big task.
- After each subagent returns, the primary agent REVIEWS the result and verifies
  it (reads the diff / runs the relevant check) BEFORE delegating the next step.
- A subagent prompt must contain: the single concrete goal, the exact file(s),
  the specific inputs/constraints, and the required return report.

**Build & test ownership:**
- **Subagents must NEVER build or run tests.** This is always the job of the
  primary agent.
- When a subagent has finished implementing, the **primary agent** takes over
  building and/or running the tests.
- If build or test errors occur, the fix is delegated **back to a subagent**.

**MCP access:**
- **Subagents have MCP access to `wogd_ddsp`** (RAG + Code-Wiki tools:
  `query_code_wiki`, `query_code_rag`, `get_rag_chunk`). They may use these
  directly — the primary agent no longer needs to pre-fetch context.
- **Subagents have access to GitHub MCP read-only tools** (`github_search_code`,
  `github_get_file_contents`, `github_list_commits`, `github_search_repositories`,
  etc.) for analyzing code on GitHub. Write tools remain primary-only.
- **Subagent model:** all subagents (`general`, `explore`, `compaction`) run on
  `opencode/nemotron-3.5-lightning-free` (workspace override in
  `opencode.json`). Keep their tasks small and focused.
- **After a subagent finishes**, the primary agent runs `index_project_code`
  to keep the wiki current (subagents cannot do this themselves).

### Definition of Done

A task is complete only when ALL of the following hold:

1. **Process proof (mandatory, non-negotiable):** the primary agent's final
   report MUST contain (a) the plan-approval quote or paraphrase from the user
   (the explicit "go"/"ok"/"ja"/"yes" message), and (b) for every implemented
   step, the `task_id` of the subagent that did the work. The only exceptions
   to mandatory delegation are: documentation edits under `doc/` and config
   edits under `.opencode/`, `~/.config/opencode/`, and `opencode.json`.
2. Passes the project checks:
   - `ruff check` (Python lint), `ruff format --check` (Python formatting)
   - `pytest` (Python tests) and `vitest` (web UI tests) green.
3. `index_project_code` ran (wiki current).
4. `pwsh doc/lint.ps1` ran without new issues.
5. `doc/log.md` appended with a changelog entry (newest first).

**Post-Task Sync (after each completed task):**
- Run `index_project_code` so the wiki stays current.
- Run `pwsh doc/lint.ps1` to check for orphan pages, stale claims,
  duplicate entries and contradictions.
- If not possible (no MCP access): explicitly report that sync is pending.

## Project Overview

`wogd-ddsp-trainer` is a **web UI training application for DDSP-based speech
synthesis models**. It exposes a browser UI to prepare datasets, configure and
run DDSP training, monitor progress, and synthesize/inference vocal output.
Python backend (PyTorch, FastAPI) + web frontend (Vue/React + Vite).
Full detail: `doc/architecture.md`.

## Role & Delegation Model

Primary agents form a responsibility hierarchy (defined in
`.opencode/agent/`; models may differ per variant):

- **ARCHITECT / ARCHITECT_Openrouter** — decides and validates architectural
  questions (module boundaries, DDSP/training/dataflow, backend-UI interface).
- **BUILD / BUILD_Openrouter** — senior dev; considers every change
  project-wide and owns the checks (`ruff`, `pytest`, `vitest`).
- **DEV / DEV_OpenRouter** — implements the assigned task, stays scoped.
- **DEV_JUNIOR_Openrouter** — small, well-defined, self-contained tasks.

All primary agents follow the `AGENTS.md` workflow: todo-first plan, then
autopilot only after explicit plan approval. Subagents (`general`, `explore`,
`compaction`) run on `opencode/nemotron-3.5-lightning-free` with `wogd_ddsp`
RAG access (see `opencode.json`).

## Wiki Lint Workflow (runs on every Post-Task Sync)

The lint script `pwsh doc/lint.ps1` runs automatically as part of every
Post-Task Sync. It can also be run manually at any time. It checks:

1. **Orphan pages**: every file in `doc/` (excluding `archive/`) should be
   listed in `doc/index.md`.
2. **Duplicate index entries**: grep `index.md` for duplicate links.
3. **Stale claims**: for each file with `stale_after:` in frontmatter, check if
   `today >= stale_after`. If stale, add a `! STALE` warning to the entry in
   `index.md` and flag for human review.
4. **Contradictions**: identify claims about the SAME feature that differ across
   files. When found, determine the actual truth from the code and update the
   outdated file.
5. **Cross-reference health**: files marked `status: deprecated` should have a
   redirect note or be moved to `archive/`.
6. **Gleanings**: after any significant analysis or debugging session, file the
   findings back into the wiki (new concept file or update to an existing one).

## Knowledge-Sync (Docs <-> RAG/Wiki MCP)

All project knowledge is ALWAYS kept in sync across stores with clear roles:

1. **Docs (`doc/`)** — LLM-Wiki (primary storage). `doc/index.md` (catalog),
   `doc/log.md` (changelog), individual concept files with YAML frontmatter.
   This is the **compiled knowledge artifact** — agents navigate here first.
2. **RAG/Wiki MCP (`wogd_ddsp`)** — Search/symbol layer over `doc/` + source code.
   Run `index_project_code` after every change so the wiki stays current.

**Deterministic Sync Workflow:**
- After every completed task: update `doc/log.md` + `doc/index.md` + run
  `index_project_code`.
- If drift is detected between stores, resolve by treating `doc/` as the
  authoritative source and updating RAG from it.

## Quick facts

- RAG MCP server: `wogd_ddsp_mcp_server.py`; registered in `opencode.json` under
  `mcp.wogd_ddsp` (venv python: `.venv\Scripts\python.exe`).
- **Primary navigation:** `doc/index.md` (LLM-Wiki catalog, first place to look).
- Checklist: `doc/checklist.md` (open tasks, short descriptions).
- Chronological log: `doc/log.md` (append-only, newest first).
- Draft plan: `doc/plan.md`.
- UI/product requirements: `doc/ui-requirements.md` (binds ALL roles; DDSP phases, coupling, mock-data seam).
- Detailed knowledge: `doc/architecture.md` (read directly).
- Coding rules: `doc/coding-standards.md`.
- Test strategy: `doc/test-strategy.md`.
- Workflow (venv/run/hot-reload): `doc/workspace-workflow.md`.
- Auto-generated knowledge: `doc/code_wiki.md` (ONLY via MCP, never read directly).
- `wogd_ddsp.db` is runtime-only (`.gitignore`).

## Global rules

- `~/.config/opencode/rules/no-auto-commit.md`: no git commits/pushes/PRs
  without explicit user request.
