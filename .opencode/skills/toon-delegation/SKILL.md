---
name: toon-delegation
description: Enforce the TOON serialization rule for subagent delegation prompts (AGENTS.md mandatory convention). Load this skill immediately BEFORE writing any Task-tool delegation prompt; it applies the TOON checklist + format templates so every delegation prompt bundles structured payloads into a fenced ```toon block instead of prose lists.
---

# TOON Delegation Enforcement

## When to use

Load this skill (via the skill tool) immediately before writing ANY subagent
delegation prompt (Task tool, any subagent type). It is the guard that makes
TOON strict compliance instead of an intention.

## The rule (AGENTS.md)

- TOON is a **mandatory** serialization convention for structured, uniform
  payloads inside delegation prompts.
- It never changes data/logic — only how the prompt is written.

## Use TOON for

- file lists with attributes (`path` + `lines` + `name` + `kind`)
- signature / parameter tables
- API / symbol index arrays
- named-key mappings
- config key/value lists
- any repeating / normalized row data (`{key,val}:` records)

## Do NOT use TOON for

- free-text instructions / natural-language guidance (stay Markdown)
- prose context
- **any code body** — full source always travels as plain fenced code
  (```` ```python ```` / ```` ```cpp ```` etc.), never via TOON; RAG snippets
  come verbatim from `get_rag_chunk` (text)

## TOON block syntax

````
```toon
<name> <{key,val}>:
  key1  val_a1  val_b1  val_c1
  key2  val_a2  val_b2  val_c2
```
````

Whitespace-aligned table rows. First row is the `<name> {key,val}:` header,
following rows are records. One semantic group per block; several blocks are
fine.

## Pass-through rule

If the data was already produced by the RAG output filter
(`query_code_rag`, `format="toon"`) or a `get_rag_chunk`-style payload, embed
that TOON block verbatim — never re-encode manually.

## Pre-delegation checklist (ALL must hold)

1. Structured/uniform payload present? → extracted into one or more
   ```toon blocks; no prose-table duplicate beside them.
2. Natural-language instructions / context? → brief Markdown outside TOON.
3. Code bodies? → plain fenced code, never TOON.
4. Prompt stays compact (small subagent context): single goal, single file
   scope, exact inputs/constraints, required return report.
5. No structured payload fell through as prose bullets.

## Minimal template

```
Goal: <one sentence>. File(s): <exact path>.
Context: <2-3 sentences max>.
```toon
<structured payloads>
```
Instructions / constraints: <short Markdown bullets or sentences>.
Return: <exact deliverable>.
```

## Self-check on finish

Re-read the written prompt before sending:

- contains a rowy / uniform / repeating list outside a ```toon block → rewrite;
- contains code inside a ```toon block → rewrite (code must be plain fenced);
- is longer than needed for a small-context subagent → trim.