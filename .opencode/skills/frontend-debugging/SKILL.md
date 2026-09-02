# Skill: frontend-debugging

## When to use

Load this skill whenever a frontend build fails or a Vue/JS runtime error occurs.
Also load proactively before editing any `.vue` file if the last build was failing.

---

## Mandatory Debugging Protocol (no skipping steps)

When `npm run build`, `npx vite build`, or `npm run test` fails in `webui/`:

### Step 1 — `git diff` FIRST (always)

```pwsh
git diff webui/src/views/AffectedView.vue
```

This takes 2 seconds and shows exactly what changed since the last working commit.
A stray `</div>`, a missing closing tag, or a wrong line — visible immediately.
**If the diff shows the cause → fix it, done. Skip steps 2–4.**

### Step 2 — Run the linter

```pwsh
cd webui && npm run lint
# or target a single file:
cd webui && npx eslint src/views/AffectedView.vue
```

ESLint with `eslint-plugin-vue` reports template parse errors with exact line and
column numbers (e.g. `284:3  error  Parsing error: x-invalid-end-tag`).
**If the linter pinpoints the error → fix only that line. Skip steps 3–4.**

### Step 3 — `git restore` + targeted single fix

If step 1 or 2 identified a bad edit:

```pwsh
git restore webui/src/views/AffectedView.vue
```

Then re-apply **only** the intended change in a single, minimal edit. Never
accumulate multiple speculative fixes in one pass.

### Step 4 — Read the file (last resort, with offset/limit)

Only if steps 1–3 did not locate the error: read the relevant section of the
file (`offset`/`limit`, not the whole file). Focus on the area indicated by
the build error's line number ± 20 lines.

---

## Hard Rules (non-negotiable)

### No custom parsers
Never write Python scripts, custom HTML parsers, regex tag-stacks, or depth
counters to diagnose syntax errors. These tools do not understand Vue template
syntax (`v-if`, `{{ }}`, `v-for`) and produce unreliable results.
Use `npm run lint` instead — it calls the actual Vue parser.

### No speculative multi-fix loops
Never add or remove multiple `</div>` tags in sequence hoping one is correct.
Each incorrect guess compounds the nesting error. Use `git restore` to reset
and apply one precise fix.

### Fix one thing at a time
One edit → one build check → one lint check. Never batch structural HTML
changes across multiple files in a single subagent pass.

### Rollback on second failure
If a fix introduces a new build error:
```pwsh
git restore <file>
```
Then restart from step 1 with the restored file.

---

## Quick Reference: Vue Template Errors

| Vite error message | Likely cause | ESLint rule | Fix strategy |
|---|---|---|---|
| `Invalid end tag` at line N | Extra `</div>` without matching open | `vue/no-parsing-error` | `git diff` → remove stray tag |
| `Element is missing end tag` at line N | Opened `<div>` without closing | `vue/html-end-tags` | `git diff` → add missing `</div>` |
| `Parsing error: x-invalid-end-tag` | Same as above, reported by ESLint | `vue/no-parsing-error` | ESLint line number → direct fix |
| `Unexpected token` in JS block | Syntax error in `<script setup>` | ESLint base rules | Check the JS expression at the reported line |

---

## Toolchain Reference

| Command | Purpose |
|---|---|
| `cd webui && npm run lint` | Lint all `src/` Vue + JS files |
| `cd webui && npx eslint src/views/Foo.vue` | Lint a single file |
| `cd webui && npm run lint:fix` | Auto-fix fixable issues (formatting, hyphenation) |
| `cd webui && npm run build` | Production build (final check) |
| `git diff webui/src/...` | Show uncommitted changes |
| `git restore webui/src/...` | Discard uncommitted changes in a file |
