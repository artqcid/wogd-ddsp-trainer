---
type: standards
title: Coding Standards - Clean Code Developer
description: CCD coding rules and conventions for the wogd-ddsp-trainer project
status: active
generated:
  by: setup
  at: 2026-08-30
stale_after: 2026-12-31
tags: [coding-standards, ccd, conventions, python]
---

# Coding Standards - Clean Code Developer (CCD)

_All coding follows the Clean Code Developer (CCD) value system
(clean-code-developer.de). If a rule must be violated, the violation MUST be
justified in the task summary. Language-neutral; additionally, English is the
project language for identifiers, docstrings and agent-facing material._

## Compliance rule

- The CCD rules below are **binding** for all code in this project.
- If a rule **cannot** be followed in a given task, the agent MUST:
  1. state which rule was violated,
  2. explain why (technical constraint, deadline, platform limitation),
  3. record this justification in the task summary.
- Unjustified violations are not acceptable.

## The CCD value system (all degrees)

### Red degree

1. **DRY (Don't Repeat Yourself)** - no duplicated code/artifacts; extract
   repetitions.
2. **KISS (Keep it simple, stupid)** - prefer the simplest working solution.
3. **Beware of premature optimization** - no optimization without a measured
   bottleneck (profiler); optimize only on customer requirement.
4. **FCoI (Favour Composition over Inheritance)** - prefer composition over
   inheritance; use interfaces/decoupling.
5. **IOSP (Integration Operation Segregation Principle)** - a method contains
   EITHER logic (operation) OR calls to own codebase methods (integration),
   never a mix.
6. **Boy Scout Rule** - leave every code unit better than you found it.
7. **RCA (Root Cause Analysis)** - fix the root cause, not the symptom
   ("five whys").
8. **VCS (Version Control System)** - all code under version control.
9. **Simple refactorings** - apply Extract Method / Rename to clean code smells.
10. **Daily reflection** - reflect daily on whether the rules were followed.

### Orange degree

11. **SLA (Single Level of Abstraction)** - one abstraction level per method.
12. **SRP (Single Responsibility Principle)** - one responsibility per class.
13. **SoC (Separation of Concerns)** - separate orthogonal concerns
    (logging, tracing, caching, persistence).
14. **Source code conventions** - consistent naming + minimal comments
    (comment WHY, not WHAT).
15. **Issue tracking** - every open item is written down.
16. **Automated integration tests** - safety net before changing code.
17. **Read, read, read** - continuous learning (books, blogs).
18. **Reviews** - pair programming / code reviews (second pair of eyes).

### Yellow degree

19. **ISP (Interface Segregation Principle)** - small, cohesive interfaces.
20. **DIP (Dependency Inversion Principle)** - depend on abstractions, not
    implementations; inject dependencies (constructor).
21. **LSP (Liskov Substitution Principle)** - subtypes behave like base type.
22. **Principle of Least Astonishment** - no surprising side effects
    (e.g. no query methods that mutate state).
23. **Information Hiding Principle** - hide internal details behind interfaces.
24. **Automated unit tests** - test single units in isolation.
25. **Mockups** - use test doubles to isolate the system under test.
26. **Code coverage analysis** - measure coverage (aim ~100%, at least 90%).
27. **Participation in professional events** - exchange with other developers.
28. **Complex refactorings** - larger refactorings backed by tests.

### Green degree

29. **OCP (Open/Closed Principle)** - open for extension, closed for
    modification (strategy pattern etc.).
30. **Tell, don't ask** - tell objects what to do; avoid exposing state.
31. **Law of Demeter (LoD)** - "don't talk to strangers"; limit call chains.
32. **CI (Continuous Integration)** - automated build+test on every change.
33. **Static code analysis** - use metrics/analyzers to track changeability.
34. **IoC container** - resolve dependencies via container/locator.
35. **Share experience** - pass on knowledge (talks, blog).
36. **Error measurement** - measure post-delivery defects to improve.

### Blue degree

37. **Design and implementation do not overlap** - architecture describes
    components (black boxes); implementation realizes them.
38. **Implementation reflects design** - physical code organization mirrors
    the architecture.
39. **YAGNI (You Ain't Gonna Need It)** - implement only clearly required
    functionality; decide as late as possible.
40. **Design before implementation** - think/design before coding.
41. **CD (Continuous Delivery)** - automated, repeatable delivery/install.
42. **Iterative development** - small iterations with customer feedback.
43. **Incremental development** - vertical, executable increments.
44. **Component orientation** - black-box components with separate contracts.
45. **Test first** - specify interfaces/semantics via tests (from the outside
    in).

### White degree

- Completes the circle: continuously apply all of the above; iterate back
  through the degrees to deepen practice.

## Project-specific conventions

- **Python:** PEP 8; format with `black` / `ruff format`; lint with
  `ruff check`. Match existing style in files you touch.
- **Web UI:** follow the framework's lint/style conventions (ESLint / Prettier
  for Vue/React + Vite).
- **Tests:** `pytest` for Python/backend/training; Vitest for the web UI.
- Never add comments unless they explain otherwise non-obvious logic.
- Do not commit unless explicitly asked. Keep diffs focused.
- All knowledge sync rules, MCP-first workflow, autopilot and language rules
  from `AGENTS.md` also apply.
