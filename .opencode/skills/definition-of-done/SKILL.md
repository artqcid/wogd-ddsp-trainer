---
name: definition-of-done
description: Mandatory completion checklist for every task. A task is complete only when all checks pass: process proof, lint, tests, wiki sync, and changelog.
---

# Definition of Done

## When to use

Load this skill at the END of any task, before marking it complete. Every work item (feature, bugfix, refactor) MUST pass ALL five checks before the primary agent declares it done.

## The five checks

### 1. Process proof (mandatory, non-negotiable)

The primary agent's final report MUST contain:
- (a) The plan-approval quote or paraphrase from the user (the explicit "go"/"ok"/"ja"/"yes" message)
- (b) For every implemented step, the `task_id` of the subagent that did the work

Exceptions (no mandatory delegation): documentation edits under `doc/` and config edits under `.opencode/`, `~/.config/opencode/`, and `opencode.json`.

### 2. Project checks pass

Run ALL of these and verify they succeed:
- `ruff check` (Python lint)
- `ruff format --check` (Python formatting)
- `pytest` (Python tests) — all green
- `vitest` (web UI tests) — all green

### 3. Wiki current

`index_project_code` ran (via MCP tool) — the RAG database and `doc/code_wiki.md` symbol index reflect the latest code.

### 4. Wiki lint clean

`pwsh doc/lint.ps1` ran without new issues (orphan pages, stale claims, contradictions, duplicates).

### 5. Changelog updated

`doc/log.md` appended with a changelog entry (newest first) describing what was done.

## Verification template

```
1. Process proof: ✓ (user approved via "<quote>")
2. ruff/pytest/vitest: ✓ (<N> passed)
3. index_project_code: ✓
4. doc/lint.ps1: ✓ (all clean)
5. doc/log.md: ✓ (entry appended)
```

## Self-check

- Did you append to `doc/log.md`?
- Did you run `index_project_code`?
- Did you run `pwsh doc/lint.ps1`?
- Did you include the user's approval quote and subagent task_ids in the report?