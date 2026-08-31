---
type: implementation-plan
status: draft
milestone: M6 - Polish
generated:
  by: primary-agent
  at: 2026-08-31
stale_after: 2026-12-31
---

# Implementation Plan - M6 Polish

_Granular plan for milestone M6. Meta plan: [`../plan.md`](../plan.md); status:
[`../checklist.md`](../checklist.md); workflow:
[`../workspace-workflow.md`](../workspace-workflow.md)._

## How to use

- Each step below is one small, self-contained task (approx. one subagent task).
- Work in order; mark `[x]` and record every step in `## History`.
- Bugs: full record only in [`../bugs.md`](../bugs.md); reference by `BUG-<id>`.

## Steps

### M6.1 Packaging (non-Docker)

- [ ] **M6.1.1** Build a wheel / local distribution for the backend
      (`pyproject.toml` packaging).
- [ ] **M6.1.2** Build the frontend production bundle (`vite build`).
- [ ] **M6.1.3** Document the local install/run path (no Docker).

### M6.2 Docs

- [ ] **M6.2.1** Finalize docs: architecture, workflow, UI requirements,
      implementation plans up-to-date.

### M6.3 Error handling

- [ ] **M6.3.1** Backend error handling (REST error envelope, worker failures).
- [ ] **M6.3.2** UI error surfaces (toasts/empty states).

### M6.4 Performance

- [ ] **M6.4.1** Profile the training loop + inference; optimize measured
      bottlenecks only (CCD: no premature optimization).

### M6.5 Output enhancer

- [ ] **M6.5.1** Integrate a native PyTorch vocoder enhancer (NSF-HiFiGAN) to
      lift raw DDSP output quality.
- [ ] **M6.5.2** (Optional/experimental) shallow-diffusion post-processing.
- [ ] **M6.5.3** Enhancer tests + docs.

## BUGS

_References only; full records in [`../bugs.md`](../bugs.md)._

- (none)

## History

_Append-only, newest first._

- (none yet)
