---
type: implementation-plan
status: draft
milestone: M19 - SPA / training lifecycle bug-fix batch (BUG-52..58)
generated:
  by: ARCHITECT_Openrouter
  at: 2026-09-03
stale_after: 2027-06-01
---

# Implementation Plan — M19 SPA / Training Lifecycle Bug-Fix Batch

_Granular plan for the BUG-52..58 batch. Meta plan: [`../plan.md`](../plan.md);
status: [`../checklist.md`](../checklist.md); full bug records:
[`../bugs.md`](../bugs.md) (single source of truth — never duplicate them here).
Prerequisite: M4 (REST backend), M5 (Web UI), M18 (RestApiClient)._

---

## Goal

Seven open bugs (BUG-52..58) block the end-to-end training workflow in the SPA.
All seven already have full architectural resolution plans in `bugs.md`; this
file turns those into an ordered, one-file-per-step task list that BUILD/DEV can
execute with the mandated single-file subagent delegation pattern.

**Central architectural insight:** four of the seven bugs (BUG-54/55/56/58) are
symptoms of one missing component — an application-level run-state store. The
`trainingRunStore` design is documented in
[`../architecture.md`](../architecture.md) §"SPA run-state management".
It must be built **once, first** (step M19.3); the four dependent fixes then
become small consumers of it.

---

## Dependency graph

```
M19.1  BUG-53  router fix          ──┐
                                     ├──> M19.2  BUG-54  sessionStorage
M19.2  BUG-54  store persistence   ──┘

M19.3  trainingRunStore (NEW)      ──┬──> M19.5  BUG-55  button lifecycle
                                     ├──> M19.6  BUG-56  dashboard resilience
                                     └──> M19.8  BUG-58  resume from wizard

M19.4  BUG-52  preprocessing       ─── independent (backend + api client)
M19.7  BUG-57  clean abort         ─── independent (backend only, trainer.py)
```

**Rationale for the order:** BUG-53 is a one-line critical fix that removes the
page reload which *causes* BUG-54 — fixing it first makes BUG-54 testable.
`trainingRunStore` is the shared prerequisite for three UI bugs, so it lands
before any of them. The two backend-only fixes (BUG-52b, BUG-57) are
independent and can run in parallel with the UI chain.---

## Steps

### M19.1 — BUG-53: fix the training dashboard route push

**File:** `webui/src/views/TrainingConfigView.vue` (single file)

Line 110 pushes the hardcoded path `'/training-dashboard'`, which is not a
registered route — the browser performs a real HTTP navigation instead of an
SPA transition. Replace with the **named route** `{ name: 'training' }` as
defined in `webui/src/router/index.js`. Keep the existing 1200 ms `setTimeout`
(it is a deliberate UX affordance so the success message is visible).

While in the file, audit every other `router.push()` call and convert any
remaining hardcoded path strings to named routes — this is what prevents the
class of bug from recurring.

**Verification:** `vitest` green; manually confirm no full page reload occurs
after a successful training start.

### M19.2 — BUG-54: sessionStorage backup for wizard state

**File:** `webui/src/stores/modelConfig.js` (single file)

Defence in depth — M19.1 removes the accidental navigation, but F5 or a dev HMR
reload still wipes the in-memory store. Three changes in this one file:

- `state()` factory reads `wizardCompleted` and `activeTier` back from
  `sessionStorage` on initialization.
- `setTierFromWizard()` writes both keys after setting store state.
- `resetToWizard()` clears both keys.

Exact code sketch is in `bugs.md` BUG-54 §resolution. Note the constraint
recorded there: this pattern must not break Vitest — `sessionStorage` is unset
in the mock environment, so `wizardCompleted` still defaults to `false` as the
existing tests expect.

**Verification:** `vitest` green (existing wizard tests must still pass
unchanged — that is the regression signal).

### M19.3 — `trainingRunStore`: the shared run-state store

**File:** `webui/src/stores/trainingRun.js` (**NEW** — single file)

The foundation for M19.5, M19.6 and M19.8. Build it standalone with its own
unit tests before any consumer touches it.

State: `activeRunId`, `activeRunStatus`, `activeRunError`, plus the cached
`runs` list that M19.6 needs to suppress its empty-state flash.

Actions: `checkActiveRun(apiClient)`, `setActiveRun(runId, status, error)`,
`stopActiveRun(apiClient)`, `persistToSession()`, `restoreFromSession()`.

Full state shape and action signatures: `architecture.md` §"SPA run-state
management" and `bugs.md` BUG-55 §resolution.

**Verification:** new `webui/src/tests/trainingRun.test.js` — store actions
against `MockApiClient`; `vitest` green.

### M19.4 — BUG-52: preprocessing diagnostics reachable again

Two independent sub-fixes, **one file each — do NOT combine into one subagent**.

**M19.4a — File:** `webui/src/api/restApiClient.js`
Line ~352: `preprocessDataset()` calls `POST …/extract-content` (HuBERT
content-embedding only; never writes `diagnostics.json`). Change the URL to
`POST …/preprocess` — the full async F0+loudness pipeline that does write it.
The mock's response shape is already compatible.

**M19.4b — File:** `server/routes/dataset.py`
Move the `get_dataset_diagnostics` handler (lines ~318–329) to **above**
`get_dataset_file` (line ~130). FastAPI matches in registration order, so the
`/{dataset_id}/{filename}` wildcard currently shadows `/{dataset_id}/diagnostics`
and returns 404.

**Architectural rule to apply while in the file:** every specific
`GET /{dataset_id}/X` route must be registered before the generic
`/{dataset_id}/{filename}` wildcard. Apply this to the whole file, not just the
diagnostics route.

**Verification:** `pytest` green; `GET /api/datasets/{id}/diagnostics` returns
200; the 404 storm in the server console is gone.

### M19.5 — BUG-55: training button lifecycle

**File:** `webui/src/views/TrainingConfigView.vue` (single file)
**Depends on:** M19.3

Replace the local `isSubmitting`-only button with a computed state driven by the
**backend** run status from `trainingRunStore`:

| Store status | Label | Enabled | Click action |
|---|---|---|---|
| `running` | `⏹ Stop Training` | yes | `stopActiveRun()` |
| `pending` | `⏳ Starting...` | no | — |
| `failed` | `❌ Training Failed` | no | — (show `activeRunError` inline) |
| _none_ | `▶ Start Training` | yes | `handleStartTraining()` |

Also: `onMounted()` calls `checkActiveRun(apiClient)`; `_doStartRun()` calls
`setActiveRun(...)` on success before navigating; the start action is **gated** —
if status is `running` or `pending`, show "Training already running — stop it
first" instead of issuing a duplicate `POST /api/runs`.

**Verification:** `vitest` — assert all four button states render; assert the
duplicate-start guard blocks a second submit.

### M19.6 — BUG-56: dashboard survives tab switches

**File:** `webui/src/views/TrainingDashboardView.vue` (single file)
**Depends on:** M19.3

Three changes (note the analysis correction recorded in `bugs.md`: the immediate
`loadRuns()` on mount **is** already present — there is no 5 s reconnect gap;
do not "fix" that):

1. **Empty-state flash** — read the cached `runs` from `trainingRunStore` so the
   last-known list renders immediately while the API call is in flight.
2. **Reload recovery** — call `restoreFromSession()` in `onMounted`; if an
   `activeRunId` is found, suppress the empty state and start polling before the
   first API response lands.
3. **Stale TensorBoard iframe** — add an `iframeKey` ref bound as `:key` on the
   iframe and increment it in `onActivated()`, forcing a DOM rebuild (and thus
   an iframe reload) each time the user returns to the tab.

**Verification:** `vitest` — assert no empty-state render while loading; assert
`iframeKey` increments on activation.

### M19.6b — `<KeepAlive>` wrapper for the dashboard route

**File:** `webui/src/App.vue` (single file)
**Depends on:** M19.6

`onActivated()` only fires for a cached component, so M19.6's iframe refresh
requires the dashboard to be kept alive across SPA navigation. Wrap the
`RouterView` so the `/training` route component is cached.

**Verification:** `vitest` green; navigating away and back does not remount the
dashboard (polling is not torn down) but does reload the iframe.

### M19.7 — BUG-57: clean training abort saves a final checkpoint

**File:** `train/trainer.py` (single file)

The stop check sits at the **start** of each iteration, so the last
`train_step()` always completed — but `_log_and_checkpoint()` only saved if
`step % checkpoint_interval == 0`. A run stopped between intervals therefore
resumes many steps behind. Add an explicit final save after the loop exits when
the stop event is set, in **both** branches (data_loader and single-batch).
Code sketch: `bugs.md` BUG-57 §resolution (1).

Confirmed by that analysis: `save_checkpoint()` already stores `step`,
`model_state_dict`, `optimizer_state_dict`, `config`, `param_manifest`,
`model_tier`, `variant_flags` — sufficient for exact resume. No cooldown or
finalization pass is needed; the last gradient update is valid.

> **Removed step — M19.7b (`server/tasks.py` watcher exit fix).** The
> 2026-09-03 re-analysis verified that `_watch_stop_request()` already `break`s out
> of its loop immediately after `stop_event.set()` (`server/tasks.py:417-419`), so the
> "watcher spin" it was meant to fix does not exist. The sub-fix is withdrawn in
> `bugs.md` BUG-57 §resolution (2). **Do not edit `server/tasks.py` for BUG-57.**

**Verification:** `pytest` — new regression test: stop a run between checkpoint
intervals, assert a checkpoint exists at the final step and that resume starts
from it.

### M19.8 — BUG-58: resume path in wizard + dashboard CTA

**File:** `webui/src/components/WizardModal.vue` (single file)
**Depends on:** M19.3

Add a conditional **Step 0 "Choose Path"** in front of the tier grid. On mount,
check `GET /api/runs` for `stopped`/`failed` runs:

- If none exist → skip Step 0 entirely, start at Step 1 (current behaviour
  preserved exactly).
- If any exist → show two cards: **"▶ Start New Training"** (proceeds to the
  existing Step 1) and **"↩ Resume Existing Training"** (lists the stopped/failed
  runs with name, tier, dataset, last step, last loss; selecting one calls
  `POST /api/runs/{id}/resume`, then `setActiveRun()`, closes the wizard and
  navigates to `/training`).

**Verification:** `vitest` — assert Step 0 is absent when no resumable runs
exist (the backward-compatibility case) and present when they do.

### M19.8b — dashboard `hasLoaded` ref + resume CTA

**File:** `webui/src/views/TrainingDashboardView.vue` (single file)
**Depends on:** M19.6 (same file — sequence them, never parallel)

Add a `hasLoaded` ref set to `true` after `listRuns()` returns; gate the
empty-state on `hasLoaded && runs.length === 0`. This separates "truly no runs"
from "still loading", which is the misleading flash recorded in the BUG-58
analysis correction.

Optional improvement from that same analysis: a prominent "Resume Training" CTA
card above the run list when any run is `stopped`/`failed`, so the user does not
have to open a card to find the existing per-card Resume button.

**Verification:** `vitest` — assert the empty state does not render while
loading.

---

## Execution order (flat)

```
M19.1   BUG-53    TrainingConfigView.vue      router named route
M19.2   BUG-54    modelConfig.js              sessionStorage backup
M19.3   —         trainingRun.js (NEW)        shared run-state store
M19.4a  BUG-52a   restApiClient.js            /preprocess endpoint
M19.4b  BUG-52b   dataset.py                  route ordering
M19.5   BUG-55    TrainingConfigView.vue      button lifecycle
M19.6   BUG-56    TrainingDashboardView.vue   cache + session + iframeKey
M19.6b  BUG-56    App.vue                     KeepAlive wrapper
M19.7a  BUG-57a   trainer.py                  save-on-stop
M19.8   BUG-58a   WizardModal.vue             Step 0 resume path
M19.8b  BUG-58b   TrainingDashboardView.vue   hasLoaded + CTA
```

_(M19.7b `tasks.py` watcher exit was removed on 2026-09-03 — verified non-bug.)_

**Delegation constraints (AGENTS.md):** one file per subagent task; the primary
agent reads the diff after every step before delegating the next; subagents
never build or run tests — the primary owns `ruff`, `pytest`, `vitest`.

**Sequencing warning:** M19.1 and M19.5 both edit `TrainingConfigView.vue`, and
M19.6 and M19.8b both edit `TrainingDashboardView.vue`. These pairs must run
**sequentially**, never as parallel subagents, or the second will clobber the
first.

---

## Definition of Done for this batch

- All seven bugs marked `fixed` in `bugs.md` with a resolution note and a
  `history` entry (status values are limited to
  `open|in-progress|fixed|verified`).
- `ruff check` + `ruff format --check` clean.
- `pytest` green, including the new BUG-57 save-on-stop regression test.- `vitest` green, including the new `trainingRun.test.js`.
- `index_project_code` run; `pwsh doc/lint.ps1` clean.
- `doc/log.md` appended (newest first) referencing the bugs by ID only.
- Manual retest of the MT-A4 training path end to end: wizard → start → stop →
  resume, with no page reload and no lost store state.

---

## BUGS

Fixed by this plan: BUG-52, BUG-53, BUG-54, BUG-55, BUG-56, BUG-57, BUG-58.

Not in scope (Group B, audio quality & training UX): BUG-59 … BUG-67 — these now
have their own plan, [`m20-audio-quality-bugs.md`](./m20-audio-quality-bugs.md).
Note the cross-batch dependency: **M20.13 (BUG-63) requires M19.4 (BUG-52)** to land
first, because the epoch estimate reads the diagnostics endpoint that BUG-52 makes
reachable.

---

## History

- 2026-09-03 — ARCHITECT_Openrouter: plan created. Derived from the
  architectural analyses already recorded in `bugs.md` for BUG-52..58 and the
  `trainingRunStore` design in `architecture.md`. Ordered so the shared store
  lands before its three consumers and the critical one-line router fix lands
  first. No code changed.
- 2026-09-03 — ARCHITECT_Openrouter (open-bug re-analysis): **step M19.7b removed.**
  Code verification showed `server/tasks.py:417-419` already `break`s out of the
  watcher loop right after `stop_event.set()`, so the "watcher spin" the step targeted
  does not exist. BUG-57 is now a single-file fix (`train/trainer.py`) and
  `server/tasks.py` is explicitly out of scope. All other M19 steps re-verified
  against the current code and confirmed still valid. Added the cross-batch
  dependency note to M20. No code changed.
