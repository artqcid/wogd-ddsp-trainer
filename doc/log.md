# wogd-ddsp-trainer - Chronological Log

_Append-only, newest first. Parseable with `grep "^## "`. Entries use
`**Creation**`, `**Update**` or `**Deprecation**` prefix + linked concept file._

## 2026-08-31 - Central UI requirements for all agents

**Creation:** `doc/ui-requirements.md` - single source of truth for the
product/UI requirements, applicable to ALL workspace agents regardless of
role. Adapted from a DDSP frontend prompt (procedural "ANWEISUNG ZUM
VORGEHEN" section removed). Contains coupling rules (REST/WebSocket/SSE
decoupling, Vue 3 + Vite + Pinia, mandatory mock-data seam), the six DDSP
domain phases (data ingestion, preprocessing feedback, training config,
real-time monitoring, inference/playground, model export), additional
milestone views (dataset manager M5.1, run lifecycle M4.2), target component
structure and acceptance criteria.

**Update:**
- `AGENTS.md` - mandatory `doc/ui-requirements.md` load step in the
  Navigation & Knowledge First workflow + Quick facts entry.
- `doc/index.md` - registered `ui-requirements.md` under Architecture & Design.
- `.opencode/agent/*.md` - role-specific deviations added to ARCHITECT (x2),
  BUILD (x2), DEV (x2), DEV_JUNIOR (x1) referencing `doc/ui-requirements.md`.

**Status:** Central spec + pointers + role deviations done; index rebuilt,
lint clean.

## 2026-08-30 - CCD-Standards, Teststrategie, Workflow, Projekt-Agents

**Update:** Übernahmen aus `wogd-vst-netsdrstation` für dieses Projekt:
- `doc/coding-standards.md` - volles CCD-Wertesystem (alle Grade) + Compliance-Regel.
- `doc/test-strategy.md` - automated-first, Test-Pyramide, Coverage, Mock-Strategie.
- `doc/workspace-workflow.md` - venv/ruff/pytest/uvicorn/Vite + Hot-Reload.
- `.opencode/agent/*.md` - Projekt-Agents (ARCHITECT/BUILD/DEV/DEV_JUNIOR +
  OpenRouter-Varianten) mit DDSP/Python/Vue-Prompts, überschreiben die globalen
  VST-spezifischen Agents; primaries nutzen den AGENTS.md-Workflow (Autopilot
  erst nach Todo-Bestätigung).
- `opencode.json` - Subagent-Overrides: `general`/`explore`/`compaction` auf
  `opencode/nemotron-3.5-lightning-free`; `wogd_ddsp_*`-RAG-Erlaubnisse für
  general/explore. Globale Modell-Configs unverändert.
- `AGENTS.md` - Role & Delegation Model + Subagent-Modell dokumentiert.

**Status:** Docs + Agents + Config angelegt; Index neu gebaut, lint clean.

## 2026-08-30 - RAG/MCP renamed to wogd_ddsp

**Update:** Renamed the RAG + MCP tooling to consistently use `wogd_ddsp`:
- `wogd_mcp_server.py` -> `wogd_ddsp_mcp_server.py`; server name `WOGD_DDSP-Assistant`.
- MCP server key `mcp.wogd_rag` -> `mcp.wogd_ddsp` (tools `wogd_ddsp_query_code_*`).
- DB `wogd_rag.db` -> `wogd_ddsp.db`; chunk ID prefix `wogd_` -> `wogd_ddsp_`.
- References updated in `opencode.json`, `AGENTS.md`, `.ragignore`, `.gitignore`.

**Status:** Rename complete; index rebuilt, wiki regenerated, lint clean.

## 2026-08-30 - LLM-Wiki + RAG/MCP setup

**Creation:** Initialized the LLM-Wiki (`doc/`), the RAG/Code-Wiki MCP server
(`wogd_ddsp_mcp_server.py`, `wogd_ddsp` in `opencode.json`), `.ragignore`,
`.gitignore`, `opencode.json` and this `doc/` wiki. Adapted from the
`netsdr_rag` solution of the `wogd-vst-netsdrstation` project for this
Python + Web-UI DDSP training app.

**Changes:**
- `wogd_ddsp_mcp_server.py` - RAG + Code-Wiki MCP server; languages:
  Python/C++/MD (structural) + TS/JS/Vue/HTML/CSS/JSON (generic line chunks);
  `wogd_ddsp_` chunk IDs; DB `wogd_ddsp.db`.
- `doc/architecture.md`, `doc/plan.md`, `doc/checklist.md`, `doc/index.md`,
  `doc/log.md` - wiki scaffold for the web UI DDSP training app.

**Status:** Scaffold created; codebase otherwise empty (M1 pending approval).
