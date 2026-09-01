---
name: post-task-sync
description: Run after every completed task to keep Docs, RAG/Wiki MCP, and README in sync. Includes wiki lint, changelog, and index update.
---

# Post-Task Sync

## When to use

Load this skill AFTER every completed task but BEFORE reporting done. It is the deterministic sync that keeps all knowledge stores consistent.

## Why

All project knowledge must be kept in sync across stores with clear roles:

1. **Docs (`doc/`)** — LLM-Wiki (primary storage). `doc/index.md` (catalog), `doc/log.md` (changelog), individual concept files with YAML frontmatter.
2. **RAG/Wiki MCP (`wogd_ddsp`)** — Search/symbol layer over `doc/` + source code.

## Sync workflow

### 1. RAG index

Run `index_project_code` via MCP so the wiki database + `doc/code_wiki.md` symbol index reflect the latest code.

### 2. Wiki lint

Run `pwsh doc/lint.ps1` and check for:
- **Orphan pages**: every file in `doc/` (excluding `archive/`) should be listed in `doc/index.md`.
- **Duplicate index entries**: grep `index.md` for duplicate links.
- **Stale claims**: for each file with `stale_after:` in frontmatter, check if `today >= stale_after`. If stale, add a `! STALE` warning to the entry in `index.md` and flag for human review.
- **Contradictions**: identify claims about the SAME feature that differ across files. When found, determine the actual truth from the code and update the outdated file.
- **Cross-reference health**: files marked `status: deprecated` should have a redirect note or be moved to `archive/`.
- **Gleanings**: after any significant analysis or debugging session, file the findings back into the wiki (new concept file or update to an existing one).

### 3. Changelog

Append a new entry to `doc/log.md` (newest first) with:
- Date stamp
- What was done (feature, bugfix, refactor)
- Subagent task_ids for implemented steps

### 4. README sync

Keep the repo-root `README.md` in sync: whenever a knowledge update lands in `doc/` (milestones, workflow, install/training usage), reflect it in `README.md` too (it is the GitHub-facing summary).

### 5. Drift resolution

If drift is detected between stores, resolve by treating `doc/` as the authoritative source and updating RAG from it.

## Checklist

- [ ] `index_project_code` ran
- [ ] `pwsh doc/lint.ps1` all clean
- [ ] `doc/log.md` entry appended
- [ ] `README.md` in sync (if applicable)