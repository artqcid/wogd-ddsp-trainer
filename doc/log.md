# wogd-ddsp-trainer - Chronological Log

_Append-only, newest first. Parseable with `grep "^## "`. Entries use
`**Creation**`, `**Update**` or `**Deprecation**` prefix + linked concept file._

## 2026-08-31 - M1 Scaffold implemented

**Creation:** M1 complete. Repo structure (`dataset/ model/ train/ inference/
server/` + `tests/`), `pyproject.toml`, `.venv` (Python 3.14), webui scaffold
(Vue 3 + Vite + Pinia), VSCode tasks, OSS dependency review. All DoD checks
green (`ruff check`, `ruff format --check`, `pytest`, `vitest`).
- Files: `pyproject.toml`, `webui/` (Vue/Vite/Pinia app, `ApiClient` +
  `MockApiClient` mock-data seam, HealthView, Vitest tests), `tests/`.
- env: torch 2.13.0+cu130 + torchaudio 2.11.0+cu130 installed from
  `download.pytorch.org/whl/cu130` (RTX 3060 detected, mixed precision OK).
- `doc/oss-dependencies.md` — new OSS dependency/license review (M1.6.2);
  all runtime/dev/frontend deps OSI-approved; `neutone_sdk` + `rmvpe`
  flagged as to-verify.
- `doc/bugs.md` — **BUG-1** (neutone_sdk pinned numpy<2.3 no cp314 Windows
  wheel on py3.14; deferred to M3.4).
- `doc/checklist.md` — M1.1-M1.7 marked done.
- `doc/implementation/m1-scaffold.md` — steps marked `[x]` + History
  (torch cu130 install, `pip install -e . --no-deps`, neutone_sdk/rmvpe
  sourcing, ruff excludes `wogd_ddsp_mcp_server.py`).

**Status:** M1 done; checks green; index rebuilt; lint clean.

## 2026-08-31 - Preset management added (FAST/NORMAL/QUALITY + custom)

**Creation:** Added preset management to the docs, placed as early as possible
in the milestone plan (M4 backend + M5 UI).
- `doc/checklist.md` — M4.5 Preset Management (SQLite schema, CRUD, GPU
  constraint validation) + M5.6 Preset Management view + M5.3 preset selector.
- `doc/implementation/m4-backend.md` — M4.5 section (5 steps: SQLite schema,
  built-in seed, CRUD endpoints, constraint clamping, save-from-run) +
  M4.6 expanded tests.
- `doc/implementation/m5-webui.md` — M5.3.2 PresetSaveDialog, M5.4.2 Save
  as Preset button, M5.6 PresetManagerView + sidebar nav.
- `doc/ui-requirements.md` — Section 3: preset management (FAST/NORMAL/
  QUALITY, custom, clamping); added PresetManagerView to component structure.
- `doc/architecture.md` — New "Preset management" section: SQLite schema,
  built-in presets table, constraint flow, REST endpoints.
- `doc/plan.md` — M4 description: "preset management (FAST/NORMAL/QUALITY +
  custom presets, GPU-constraint clamping)".

**Status:** Preset management fully documented across all layers (data model,
backend, UI, requirements, checklist); index rebuilt; lint clean.

## 2026-08-31 - VRAM budget / RTX 3060 6GB constraint

**Update:** Addressed the hardware constraint that all training MUST run on
RTX 3060 Laptop (6 GB VRAM). Analysis shows DDSP is lightweight: total VRAM
~1.3–2.2 GB with batch_size=1, mixed precision, offline feature extraction,
3-scale STFT loss and hidden_size ≤ 512 — leaving 3.8–4.7 GB headroom.
- `doc/architecture.md` — new "GPU detection & VRAM budget" section with
  VRAM budget table, required techniques (mixed precision, offline features,
  batch=1, 3-scale loss, sequence_length ≤ 4 s, hidden_size 256/512), and
  a VRAM tier table for the GPU auto-detection module.
- `doc/plan.md` — "VRAM budget / RTX 3060 6GB" resolved question added.
- `doc/implementation/m1-scaffold.md` — M1.2.4 step: verify mixed precision
  imports (`torch.cuda.amp.autocast` + `GradScaler`).
- `doc/implementation/m2-dataset-prep.md` — M2.2 section header: "offline";
  M2.2.4 step: save features as `.npy` during preprocessing.
- `doc/implementation/m3-model-training.md` — M3.1.3: configurable STFT
  scales (default 3); M3.2.2: VRAM tier proposal; M3.3.1: mixed precision +
  gradient checkpointing in training step.

**Status:** VRAM constraint documented and traced through all relevant docs;
lint clean.

## 2026-08-31 - Framework decision: PyTorch (drop TensorFlow / magenta/ddsp)

**Update:** Decided the best/most-modern framework now and restructured the
docs accordingly. Evidence: `magenta/ddsp` (TF) is legacy (archived parent
org); the active DDSP/SVC ecosystem is PyTorch (DDSP-SVC, DiffSinger/OpenVPI,
RAVE); **Neutone — our own export target — is PyTorch/TorchScript-only**;
Google steers new generative-AI work to PyTorch/Keras 3/JAX.
- `doc/plan.md` - resolved "DDSP implementation" -> self-owned PyTorch core
  (spec: DDSP paper; refs acids-ircam/ddsp_pytorch + magenta/ddsp); F0 -> RMVPE;
  decision "PyTorch is the framework" + "Export formats" (Neutone/ONNX/
  TorchScript); M3/M8 reworded; output-quality decision no longer TF-bound.
- `doc/architecture.md` - tech stack -> PyTorch + torchaudio; RMVPE F0; export
  Neutone/TorchScript/ONNX; "magenta/ddsp logs" -> "training loop logs".
- `doc/checklist.md` - M1.2 deps (torch/torchaudio/RMVPE/neutone_sdk); M3.1 own
  DDSP core; M3.4 export; M6.5 native PyTorch vocoder; M8 -> "synthesis hacks".
- `doc/ui-requirements.md` - export formats -> Neutone/ONNX/TorchScript;
  realtime target -> Neutone/TorchScript.
- `doc/implementation/m1-m8` - deps, DDSP core (PyTorch), export, M8 reframed
  (feature flags on our own core, not SDK patches).
- `doc/experimental-ddsp.md` / `doc/experimental-sdk-hacking.md` - framework
  refs (tfkl.Layer -> nn.Module); M8 as first-class.
- `doc/related-work.md` - framework table + lessons rewritten (same-framework
  comparison now).
- `README.md`, `AGENTS.md`, `.opencode/agent/BUILD*` - stack -> PyTorch.

**Status:** Framework decision applied consistently; index rebuilt; lint clean.

## 2026-08-31 - README (GitHub-facing summary)

**Creation:** `README.md` - 4-section GitHub-style summary: (1) development +
clone/VSCode workflow (venv, npm, ruff/pytest/vitest, run, VSCode tasks), (2)
installation (placeholder, M6 non-Docker packaging), (3) training usage
(placeholder outline), (4) Apache-2.0 license. Placeholders (`<TODO Mx: ...>`)
mark not-yet-implemented parts.

**Update:** `AGENTS.md` - added a sync rule under "Deterministic Sync Workflow":
`README.md` must be kept in sync whenever a knowledge update lands in `doc/`.

**Status:** README created; sync rule documented; index rebuilt, lint clean.

## 2026-08-31 - Related work (DDSP-SVC) + output-enhancer gap

**Creation:** `doc/related-work.md` - analysis of `yxlllc/DDSP-SVC` (real-time
singing voice conversion, MIT) and its implications: (1) raw DDSP output is not
studio-grade -> post-hoc output enhancer needed; (2) content encoder
(Hubert/ContentVec) as alternative conditioning; (3) real-time requires
splicing logic beyond a TFLite/TF.js export. Verified via the HF mirror +
GitHub repo.

**Update:**
- `doc/plan.md` - M3 note + new "Output quality" decision: post-hoc enhancer
  (vocoder/shallow-diffusion) scoped in M6, TF-compatible.
- `doc/checklist.md` - M6 split into M6.1-M6.5; new **M6.5** output enhancer.
- `doc/implementation/m6-polish.md` - new M6.5 enhancer step group.
- `doc/implementation/m7-experimental.md` - "Future directions" note (shallow
  diffusion -> M6.5).
- `doc/ddsp-concepts.md` - Applications pointer to related-work.
- `doc/index.md` - registered `related-work.md`.

**Status:** Enhancer gap captured; related-work reference added; index rebuilt;
lint clean.

## 2026-08-31 - Three-tier planning + M7/M8 milestones + UI rework

**Update:** Established the three-tier planning model (meta plan -> checklist ->
granular implementation plans) and added experimental milestones M7/M8.
- `doc/plan.md` - M3 reordered (GPU detection before the training loop); M7
  (experimental sound design / Musique Concrète) and M8 (experimental SDK
  hacking) milestones added; F0/feature-extraction question clarified to
  `f0_hz` + `f0_confidence` + `loudness_db` (verified against
  `ddsp/training/preprocessing.py`).
- `doc/checklist.md` - added YAML frontmatter; M2.1/M2.2 fixed (level
  normalization; features corrected to f0/confidence/loudness, no "harmonic
  amplitude"/"aperiodicity"); M3 reordered (GPU detection = M3.2, before the
  training loop); M5 split into M5.1-M5.6 (app shell + 4 view groups + tests);
  M7 and M8 sections added.
- `doc/architecture.md` - dataset/model feature-extraction wording corrected
  (harmonic amplitude/aperiodicity are decoder outputs, not features).
- `doc/workspace-workflow.md` - removed the stale `/ws` (WebSocket) Vite proxy
  (contradicted the no-WebSocket TensorBoard doctrine).
- `doc/ui-requirements.md` - reworked: app shell (dark SPA + sidebar 4 nav
  groups + top bar), granular views grouped by navigation, corrected export
  formats (SavedModel/TF.js/TFLite/Neutone; no PyTorch/ONNX), realtime target =
  TF.js/TFLite (not VST), M7 experimental sections (F0 editor two-tier,
  component mixer, reverb IR injection + extractor), Wavesurfer.js dependency.
- `AGENTS.md` - added "Planning tiers" + "Bug tracking" workflow sections;
  fixed stale PyTorch/Vue-React stack description.
- `.opencode/agent/*.md` - fixed stale PyTorch/WebSocket-SSE references
  (ARCHITECT x2, BUILD x2).

**Creation:**
- `doc/bugs.md` - canonical bug ledger (single source of truth; `BUG-<id>`
  entries, `next_id` counter).
- `doc/experimental-ddsp.md` - M7 knowledge base (Musique Concrète + IR
  injection; fact-vs-speculation tagged, verified against magenta/ddsp source).
- `doc/experimental-sdk-hacking.md` - M8 knowledge base (4 SDK hacks;
  fact-vs-speculation tagged).
- `doc/implementation/m1-scaffold.md` .. `m8-experimental-sdk-hacking.md` - 8
  granular implementation-plan files (small steps + `## History` + `## BUGS`).

**Status:** Three-tier model + milestones M1-M8 in place; docs consistent;
index rebuilt; lint clean.

## 2026-08-31 - Stack decisions applied (magenta/ddsp, TensorBoard doctrine, licensing)

**Update:** Applied the project-owner answers to the `plan.md` open questions
across plan, architecture, UI requirements and checklist.
- `doc/plan.md` - milestones M3-M5 reworded (`magenta/ddsp` TensorFlow, FastAPI
  + Celery/Redis, TensorBoard, GPU-parameter suggestions); "Open questions"
  replaced with "Resolved questions"; decisions added: `magenta/ddsp` is
  mandatory (PyTorch out of scope), TF-native preprocessing ("pure-torch"
  superseded), local GPU auto-detection + parameter suggestions, offline +
  realtime model support, TensorBoard monitoring doctrine (control-panel UI,
  no custom charts, no WebSocket/SSE loss streaming), Vue 3 + Vite + Pinia
  confirmed (not React), OSI-only open-source licensing + Apache-2.0,
  thirdParty/venv-first dependency sourcing.
- `doc/architecture.md` - tech stack switched to TensorFlow 2.x + magenta/ddsp
  + crepe + librosa/soundfile + FastAPI + Celery/Redis + TensorBoard; removed
  PyTorch/torchaudio and WebSocket status streaming; added "Training monitoring
  (TensorBoard doctrine)" and "GPU detection" sections; inference now includes
  realtime export (TF.js/TFLite).
- `doc/ui-requirements.md` - coupling rules: REST + TensorBoard iframe only
  (WS/SSE dropped, no custom charts); section 4 rewritten as "Training
  monitoring (TensorBoard doctrine)"; GPU parameter suggestions in training
  config; export formats now TF/SavedModel/TF.js/TFLite/Neutone (PyTorch
  formats dropped); removed LossChart/SpectrogramCompare.
- `doc/checklist.md` - M1: TF/ddsp/Celery/Redis deps, Vue-Pinia scaffold, new
  **M1.6** LICENSE + OSS dependency review, **M1.7** thirdParty/venv sourcing;
  M3: magenta/ddsp model + losses, TensorBoard metrics, offline + realtime
  export, new **M3.5** GPU detection + parameter suggestions; M4: Celery + Redis
  REST job management (no WebSocket), new **M4.4** TensorBoard provisioning;
  M5: GPU suggestions + TensorBoard dashboard + realtime exports.

**Creation:** `LICENSE` - Apache-2.0 (open-source publication friendly, matches
the magenta/ddsp ecosystem).

**Status:** Decisions applied consistently; index rebuilt, lint clean.

## 2026-08-31 - M6 no-Docker + mandatory VSCode task set

**Update:** Removed Docker from the roadmap (decision).
- `doc/plan.md` - M6 now reads "packaging (non-Docker), docs, performance,
  error handling"; added decisions "No Docker" and "Mandatory VSCode task set
  from the start": `build-debug`, `build-release`, `e2e-test`,
  `start-application-debug`, `start-application-release`.
- `doc/checklist.md` - new **M1.5** `.vscode/tasks.json` with the VSCode task
  set (as soon as the M1 build process/artifacts exist); **M6.1** changed to
  non-Docker packaging.

**Creation:** `.vscode/tasks.json` - scaffold with the five required VSCode
tasks (build-debug, build-release, e2e-test, start-application-debug,
start-application-release) wired to the planned uvicorn/Vite/venv commands;
refined when the build process lands.

**Status:** Plan + checklist + tasks scaffold done; index rebuilt, lint clean.

## 2026-08-31 - DDSP domain background concept file

**Creation:** `doc/ddsp-concepts.md` - DDSP domain background knowledge
(translated to English per the language rule): definition/core idea, signal
flow (modified autoencoder), differentiable synthesis modules (harmonic
additive / filtered noise / differentiable reverb), training & multi-scale
spectral loss, monophonic data requirement, applications (timbre transfer,
VSTs) and limitations/extensions (PolyDDSP, RAVE). Merged from six German
background chunks; complements `architecture.md` (project pipeline) and
`plan.md` (decisions).

**Update:** `doc/index.md` - new "Domain Knowledge" category registering
`ddsp-concepts.md`.

**Status:** Concept file + index entries done; index rebuilt, lint clean.

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
