---
name: subagent-safety
description: Enforce scope pinning, abort-safety, and primary diff-check for subagent delegations. Load this skill before delegating any subagent task.
---

# Subagent Safety Rules

## When to use

Load this skill immediately BEFORE writing any subagent delegation prompt. It enforces the three safety rules that protect against scope-bleed and context-loss when subagent tool calls abort mid-task.

## The three rules (B, C, D)

### B — One file per subagent task

A delegation targets a **SINGLE file** by default. When a fix must touch several files, run sequential single-file subagents with a primary verification pass in between — do not hand multiple files to one subagent.

### C — Abort => STOP

If a tool call fails or is aborted (e.g. `Duplicate tool_call_id`, `Tool execution aborted`, `Task cancelled`), the subagent MUST stop immediately, NOT retry by switching scope/files, and report the abort to the primary (never invent constraints back). The primary then re-delegates the step. A subagent never performs corrective edits on files outside the one it was assigned.

### D — Primary diff check every step

After each subagent, the primary reads the diff and confirms exactly the assigned files changed and no merge markers / out-of-scope edits slipped in — BEFORE testing or delegating the next step. This is the safety net that catches abort-induced scope-bleed.

## Task size & context limits

- Give each subagent ONE small, single-step task only.
- Break large work into a CHAIN of small subagent tasks, not one big task.
- After each subagent returns, the primary agent REVIEWS the result and verifies it (reads the diff / runs the relevant check) BEFORE delegating the next step.
- A subagent prompt must contain: the single concrete goal, the exact file(s), the specific inputs/constraints, and the required return report.

## Autonomy rule

The todo-first / wait-for-approval workflow applies ONLY to the primary agent. Subagents do NOT wait for approval — the primary's delegation prompt IS their "go". A subagent executes its single task autonomously from start to finish and then returns its report.

## Build & test ownership

- Subagents must NEVER build or run tests. This is always the job of the primary agent.
- When a subagent finishes implementing, the primary agent takes over building and/or running the tests.
- If build or test errors occur, the fix is delegated back to a subagent.

## Pre-delegation checklist

1. Does the task target a SINGLE file? If not, split it.
2. Does the prompt contain: goal + file(s) + constraints + return report spec?
3. Is the task small enough for a single subagent context window?

## Post-delegation checklist

1. Read the diff — did only the assigned file change?
2. No merge markers or out-of-scope imports slipped in?
3. BUILD/TEST before next delegation.