---
type: implementation-plan
status: draft
milestone: M14 - Dual-Mode Training UI + Backend Tier System
generated:
  by: ARCHITECT-agent
  at: 2026-09-01
stale_after: 2027-06-01
---

# Implementation Plan — M14 Dual-Mode Training UI + Backend Tier System

_Granular plan for milestone M14. Meta plan: [`../plan.md`](../plan.md);
status: [`../checklist.md`](../checklist.md).
Full spec:
[`../ui-requirements.md`](../ui-requirements.md#dual-mode-training-ui-m14),
[`../architecture.md`](../architecture.md#model-tier-system--dual-mode-ui-m14).
Prerequisite: none (M8–M13 are parallel; M14 is infrastructure)._

## Constraints & principles

- **Backend-first.** All Phase 1 backend steps must be complete and tested
  before any Phase 2 frontend work begins. The frontend depends on
  `GET /api/gpu/feasibility` and the `model_tier` fields in the REST API.
- **No breaking changes.** Every new field uses `model_config.get(key, default)`
  or `DEFAULT 'standard'` in SQL. Existing runs, presets, checkpoints, and
  tests must remain green throughout.
- **One subagent per step.** Each step is sized for a single focused subagent.
  Primary agent builds and runs checks after every step.
- **VRAM budget: 6 GB.** The tier system itself adds zero VRAM. The
  `estimate_model_vram()` function is a lightweight accounting layer, not
  ML code.
- **Mock-data seam (mandatory).** Every frontend component must render with
  `MockApiClient` + fixtures. A component is not done until its Vitest covers
  all render states.

---

## File map

```
Phase 0 — Design System (prerequisite for all Phase 2 work)
webui/index.html                        MOD  — Inter + JetBrains Mono font links (M14.2.0-A)
webui/src/style.css                     NEW  — global design tokens incl. tier colors, reset, utilities (M14.2.0-B)
webui/src/main.js                       MOD  — import './style.css' (M14.2.0-C)
webui/src/App.vue                       MOD  — remove scoped :root, update shell layout (M14.2.0-D)
webui/src/components/Sidebar.vue        MOD  — modern nav: gradient brand, icons, active glow (M14.2.0-E)
webui/src/components/TopBar.vue         MOD  — pill badges, GPU chip, tier badge (M14.2.0-F)
webui/src/utils/tierColors.js           NEW  — tier identity color utility + Vitest (M14.2.0-H)
tests/tierColors.test.js                NEW  — Vitest for tierColors utility (M14.2.0-H)

Phase 1 — Backend
train/gpu.py                       MOD  — VRAMEstimate + estimate_model_vram (M14.1.1)
server/db.py                       MOD  — model_tier column + migration (M14.1.2)
server/presets.py                  MOD  — VARIANT/ENGINE/ADVANCED_KEYS, tier-aware seed (M14.1.3)
server/routes/training.py          MOD  — model_tier in requests, validate response, resume guard (M14.1.4)
server/tasks.py                    MOD  — tier-aware build_training (M14.1.5)
server/routes/host.py              MOD  — GET /api/gpu/feasibility endpoint (M14.1.6)
tests/test_gpu_feasibility.py      NEW  — pytest: estimate_model_vram + endpoint (M14.1.7)
tests/test_presets_tier.py         NEW  — pytest: tier-aware preset logic (M14.1.8)
tests/test_training_tier.py        NEW  — pytest: tier-aware build_training + resume guard (M14.1.9)

Phase 2 — Frontend
webui/src/stores/modelConfig.js    NEW  — Pinia modelConfig store (M14.2.1)
webui/src/mocks/fixtures.js        MOD  — tier_feasibility fixture + model_tier on presets (M14.2.2)
webui/src/mocks/mockApiClient.js   MOD  — getGpuFeasibility() mock (M14.2.2)
webui/src/components/ModelTierCard.vue       NEW  (M14.2.3)
webui/src/components/GpuFeasibilityBanner.vue NEW  (M14.2.4)
webui/src/components/WizardModal.vue         NEW  (M14.2.5)
webui/src/components/TabCore.vue             NEW  (M14.2.6)
webui/src/components/TabComponent.vue        NEW  (M14.2.6)
webui/src/components/TabHacks.vue            NEW  (M14.2.6)
webui/src/components/TabEngine.vue           NEW  (M14.2.6)
webui/src/components/TabAdvanced.vue         NEW  (M14.2.6)
webui/src/views/TrainingConfigView.vue       MOD  — tab-wrapper + wizard (M14.2.7)
webui/src/views/PresetManagerView.vue        MOD  — model_tier filter (M14.2.8)
tests/  (vitest)                   MOD  — M14.2.9 test suite
```

---

## Phase 0 — Design System (prerequisite for all Phase 2 work)

> **Goal:** Replace the current GitHub-Dark-Clone visual style with a modern
> AI-dashboard design language. All design tokens, global utilities, and shell
> components land in a single step so every subsequent Phase 2 component
> inherits them automatically. No backend changes. No Vitest breakage
> (existing selectors are `data-testid`-based and CSS-independent).
>
> **Design reference:** Shasanko Das — *AI Content Creation & Analytics SaaS
> Dashboard – Dark Mode UI/UX* (Dribbble shot 27444658 / Muzli Aug 2026).
> Key traits to adopt: deep indigo-black backgrounds, Indigo/Violet primary
> accent, Cyan secondary accent, glass-morphism cards with `border-radius:
> 16px`, gradient active states with inward glow, Inter variable font,
> pill-shaped status badges, generous spacing.

### M14.2.0 — Design System: tokens, global CSS, shell upgrade

**This step is a prerequisite for M14.2.1–M14.2.9.** Complete and verify
(`vitest` green, visual review in browser) before proceeding.

---

#### M14.2.0-A — `webui/index.html`: font imports

Add inside `<head>` before the closing tag:

```html
<!-- Inter: primary UI font (weights 300–700, variable font) -->
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link
  href="https://fonts.googleapis.com/css2?family=Inter:ital,opsz,wght@0,14..32,300..700;1,14..32,300..700&display=swap"
  rel="stylesheet"
/>
<!-- JetBrains Mono: code/numeric values (VRAM numbers, step counters) -->
<link
  href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500&display=swap"
  rel="stylesheet"
/>
```

Also update `<title>`:

```html
<title>WOGD DDSP Trainer</title>
```

---

#### M14.2.0-B — `webui/src/style.css` (new global file)

Create `webui/src/style.css`. This is the **single source of truth** for all
design tokens. Every scoped component style that needs a color, radius, shadow
or spacing value must reference a CSS custom property defined here — never
hard-code values in component styles.

Full file content:

```css
/* ============================================================
   WOGD DDSP Trainer — Global Design System
   Design reference: Shasanko Das AI Dashboard (Dribbble 27444658)
   ============================================================ */

/* ── 1. CSS Custom Properties (Design Tokens) ─────────────── */
:root {
  /* --- Backgrounds (deep indigo-black palette) --- */
  --bg-base:          #07080F;   /* Deepest — page/body base */
  --bg-primary:       #0C0E1A;   /* Main content area */
  --bg-secondary:     #111425;   /* Sidebar, card surfaces */
  --bg-tertiary:      #181C30;   /* Inputs, hover states, active items */
  --bg-elevated:      #1D2238;   /* Modals, dropdowns, popovers */
  --bg-glass:         rgba(255, 255, 255, 0.03); /* Glass overlay */
  --bg-glass-border:  rgba(255, 255, 255, 0.06); /* Glass border */

  /* --- Text --- */
  --text-primary:     #ECEEFF;   /* Near-white with blue tint */
  --text-secondary:   #8892BB;   /* Subdued — labels, hints */
  --text-muted:       #4A527A;   /* Very subdued — placeholders, captions */
  --text-on-accent:   #FFFFFF;   /* Text on filled accent backgrounds */

  /* --- Primary Accent: Indigo/Violet (AI, model, training) --- */
  --accent:           #6366F1;   /* Indigo-500 */
  --accent-light:     #818CF8;   /* Indigo-400 — hover, active text */
  --accent-dark:      #4F46E5;   /* Indigo-600 — pressed, gradient end */
  --accent-glow:      rgba(99, 102, 241, 0.35);
  --accent-subtle:    rgba(99, 102, 241, 0.12);
  --accent-subtle-hover: rgba(99, 102, 241, 0.20);

  /* --- Secondary Accent: Cyan (audio, waveform, inference) --- */
  --accent-2:         #06B6D4;   /* Cyan-500 */
  --accent-2-light:   #22D3EE;   /* Cyan-400 */
  --accent-2-dark:    #0891B2;   /* Cyan-600 */
  --accent-2-glow:    rgba(6, 182, 212, 0.30);
  --accent-2-subtle:  rgba(6, 182, 212, 0.10);

  /* --- Semantic colors --- */
  --success:          #10B981;   /* Emerald-500 */
  --success-subtle:   rgba(16, 185, 129, 0.12);
  --warning:          #F59E0B;   /* Amber-500 */
  --warning-subtle:   rgba(245, 158, 11, 0.12);
  --error:            #EF4444;   /* Red-500 */
  --error-subtle:     rgba(239, 68, 68, 0.12);
  --info:             #3B82F6;   /* Blue-500 */
  --info-subtle:      rgba(59, 130, 246, 0.12);

  /* --- Borders --- */
  --border:           rgba(255, 255, 255, 0.07);
  --border-strong:    rgba(255, 255, 255, 0.13);
  --border-accent:    rgba(99, 102, 241, 0.45);
  --border-accent-2:  rgba(6, 182, 212, 0.40);

  /* --- Shadows --- */
  --shadow-xs:   0 1px 2px rgba(0, 0, 0, 0.5);
  --shadow-sm:   0 2px 8px rgba(0, 0, 0, 0.45);
  --shadow-md:   0 4px 20px rgba(0, 0, 0, 0.55);
  --shadow-lg:   0 8px 40px rgba(0, 0, 0, 0.60);
  --shadow-glow: 0 0 28px var(--accent-glow);
  --shadow-glow-2: 0 0 24px var(--accent-2-glow);
  --shadow-card: 0 2px 12px rgba(0, 0, 0, 0.4), inset 0 1px 0 rgba(255, 255, 255, 0.04);

  /* --- Radii --- */
  --radius-xs:   4px;
  --radius-sm:   8px;
  --radius-md:   12px;
  --radius-lg:   16px;
  --radius-xl:   20px;
  --radius-pill: 999px;

  /* --- Spacing scale (base 4px) --- */
  --space-1:  4px;
  --space-2:  8px;
  --space-3:  12px;
  --space-4:  16px;
  --space-5:  20px;
  --space-6:  24px;
  --space-8:  32px;
  --space-10: 40px;
  --space-12: 48px;

  /* --- Typography --- */
  --font-sans:  'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  --font-mono:  'JetBrains Mono', 'Fira Code', 'Cascadia Code', monospace;

  --text-xs:    0.6875rem;  /* 11px */
  --text-sm:    0.75rem;    /* 12px */
  --text-base:  0.875rem;   /* 14px */
  --text-md:    1rem;       /* 16px */
  --text-lg:    1.125rem;   /* 18px */
  --text-xl:    1.25rem;    /* 20px */
  --text-2xl:   1.5rem;     /* 24px */

  --weight-light:   300;
  --weight-normal:  400;
  --weight-medium:  500;
  --weight-semi:    600;
  --weight-bold:    700;

  /* --- Transitions --- */
  --transition-fast:   100ms ease;
  --transition-base:   160ms ease;
  --transition-slow:   260ms ease;

  /* --- Z-index layers --- */
  --z-base:    0;
  --z-raised:  10;
  --z-overlay: 100;
  --z-modal:   200;
  --z-toast:   300;

  /* --- Sidebar --- */
  --sidebar-width:       220px;
  --sidebar-collapsed:   60px;

  /* --- TopBar --- */
  --topbar-height:       52px;

  /* ── Tier identity colors ───────────────────────────────────
     Each tier owns a unique signal color used on: active-tab
     indicator, tab label, Wizard tier card border/icon,
     ModelTierCard header, GpuFeasibilityBanner tier chip,
     TopBar tier badge. --accent (Indigo) is NOT repurposed
     for tiers — it stays the global interactive/nav accent.
     ─────────────────────────────────────────────────────────── */

  /* standard — Emerald: familiar, safe entry point */
  --tier-standard:        #10B981;
  --tier-standard-subtle: rgba(16, 185, 129, 0.12);
  --tier-standard-glow:   rgba(16, 185, 129, 0.30);

  /* component — Sky/Cyan: precision, sliders, fine-tuning */
  --tier-component:        #06B6D4;
  --tier-component-subtle: rgba(6, 182, 212, 0.12);
  --tier-component-glow:   rgba(6, 182, 212, 0.30);

  /* hacks — Amber: experimental, caution, creative risk */
  --tier-hacks:        #F59E0B;
  --tier-hacks-subtle: rgba(245, 158, 11, 0.12);
  --tier-hacks-glow:   rgba(245, 158, 11, 0.30);

  /* engine — Violet: power, alternative architecture */
  --tier-engine:        #8B5CF6;
  --tier-engine-subtle: rgba(139, 92, 246, 0.12);
  --tier-engine-glow:   rgba(139, 92, 246, 0.30);

  /* advanced — Rose: expert-only, high VRAM, danger zone */
  --tier-advanced:        #F43F5E;
  --tier-advanced-subtle: rgba(244, 63, 94, 0.12);
  --tier-advanced-glow:   rgba(244, 63, 94, 0.30);
}

/* ── 2. Reset & Base ───────────────────────────────────────── */
*, *::before, *::after {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

html {
  height: 100%;
  font-size: 16px;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-rendering: optimizeLegibility;
}

body {
  height: 100%;
  background: var(--bg-base);
  color: var(--text-primary);
  font-family: var(--font-sans);
  font-size: var(--text-base);
  font-weight: var(--weight-normal);
  line-height: 1.6;
  overflow: hidden; /* SPA: scroll handled per-view */
}

#app {
  height: 100%;
  display: flex;
  flex-direction: column;
}

/* ── 3. Typography Utilities ───────────────────────────────── */
h1, h2, h3, h4, h5, h6 {
  font-weight: var(--weight-semi);
  line-height: 1.3;
  color: var(--text-primary);
}

h2 { font-size: var(--text-xl); }
h3 { font-size: var(--text-md); }
h4 { font-size: var(--text-base); }

.text-xs      { font-size: var(--text-xs); }
.text-sm      { font-size: var(--text-sm); }
.text-base    { font-size: var(--text-base); }
.text-muted   { color: var(--text-muted); }
.text-secondary { color: var(--text-secondary); }
.text-accent  { color: var(--accent-light); }
.text-mono    { font-family: var(--font-mono); }
.label        { font-size: var(--text-xs); font-weight: var(--weight-medium);
                text-transform: uppercase; letter-spacing: 0.06em;
                color: var(--text-secondary); }

/* ── 4. Card System ────────────────────────────────────────── */
.card {
  background: var(--bg-secondary);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: var(--space-6);
  box-shadow: var(--shadow-card);
  transition: border-color var(--transition-base), box-shadow var(--transition-base);
}

.card:hover {
  border-color: var(--border-strong);
  box-shadow: var(--shadow-md);
}

.card-accent {
  border-color: var(--border-accent);
  box-shadow: var(--shadow-card), 0 0 0 1px rgba(99, 102, 241, 0.15);
}

.card-header {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  margin-bottom: var(--space-5);
  padding-bottom: var(--space-4);
  border-bottom: 1px solid var(--border);
}

.card-header h3 {
  font-size: var(--text-base);
  font-weight: var(--weight-semi);
  color: var(--text-primary);
  margin: 0;
}

.card-icon {
  width: 32px;
  height: 32px;
  border-radius: var(--radius-sm);
  background: var(--accent-subtle);
  color: var(--accent-light);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1rem;
  flex-shrink: 0;
}

.card-icon.cyan  { background: var(--accent-2-subtle); color: var(--accent-2); }
.card-icon.green { background: var(--success-subtle);  color: var(--success); }
.card-icon.amber { background: var(--warning-subtle);  color: var(--warning); }

/* ── 5. Button System ──────────────────────────────────────── */
button, .btn {
  font-family: var(--font-sans);
  font-size: var(--text-base);
  font-weight: var(--weight-medium);
  border-radius: var(--radius-md);
  border: none;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  padding: 0.5625rem var(--space-4);
  transition: transform var(--transition-fast), box-shadow var(--transition-base),
              background var(--transition-base), color var(--transition-base),
              border-color var(--transition-base);
  user-select: none;
  white-space: nowrap;
  text-decoration: none;
}

.btn-primary {
  background: linear-gradient(135deg, var(--accent) 0%, var(--accent-dark) 100%);
  color: var(--text-on-accent);
  box-shadow: 0 4px 14px var(--accent-glow);
}

.btn-primary:hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 22px var(--accent-glow);
}

.btn-primary:active {
  transform: translateY(0);
  box-shadow: 0 2px 8px var(--accent-glow);
}

.btn-primary:disabled {
  opacity: 0.45;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.btn-secondary {
  background: transparent;
  color: var(--text-secondary);
  border: 1px solid var(--border-strong);
}

.btn-secondary:hover {
  background: var(--bg-tertiary);
  color: var(--text-primary);
  border-color: var(--accent);
}

.btn-ghost {
  background: transparent;
  color: var(--text-secondary);
  border: none;
  padding: var(--space-2) var(--space-3);
}

.btn-ghost:hover {
  background: var(--bg-tertiary);
  color: var(--text-primary);
}

.btn-cyan {
  background: linear-gradient(135deg, var(--accent-2) 0%, var(--accent-2-dark) 100%);
  color: var(--text-on-accent);
  box-shadow: 0 4px 14px var(--accent-2-glow);
}

.btn-cyan:hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 22px var(--accent-2-glow);
}

.btn-sm {
  font-size: var(--text-sm);
  padding: var(--space-1) var(--space-3);
  border-radius: var(--radius-sm);
}

.btn-lg {
  font-size: var(--text-md);
  padding: 0.75rem var(--space-6);
  border-radius: var(--radius-lg);
}

/* ── 6. Badge / Pill System ────────────────────────────────── */
.badge {
  display: inline-flex;
  align-items: center;
  gap: var(--space-1);
  padding: 3px var(--space-3);
  border-radius: var(--radius-pill);
  font-size: var(--text-xs);
  font-weight: var(--weight-medium);
  white-space: nowrap;
}

.badge-success { background: var(--success-subtle); color: var(--success); }
.badge-warning { background: var(--warning-subtle); color: var(--warning); }
.badge-error   { background: var(--error-subtle);   color: var(--error);   }
.badge-info    { background: var(--info-subtle);     color: var(--info);    }
.badge-accent  { background: var(--accent-subtle);   color: var(--accent-light); }
.badge-cyan    { background: var(--accent-2-subtle); color: var(--accent-2); }
.badge-muted   { background: rgba(255,255,255,0.06); color: var(--text-secondary); }

.badge-dot::before {
  content: '';
  display: inline-block;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: currentColor;
}

/* ── 7. Form Elements ──────────────────────────────────────── */
.form-group {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  margin-bottom: var(--space-4);
}

.form-group label,
.form-label {
  font-size: var(--text-xs);
  font-weight: var(--weight-medium);
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--text-secondary);
}

input[type="text"],
input[type="number"],
input[type="email"],
input[type="password"],
select,
textarea {
  font-family: var(--font-sans);
  font-size: var(--text-base);
  color: var(--text-primary);
  background: var(--bg-tertiary);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  padding: 0.5625rem var(--space-3);
  width: 100%;
  outline: none;
  transition: border-color var(--transition-base), box-shadow var(--transition-base),
              background var(--transition-base);
  appearance: none;
}

input:focus, select:focus, textarea:focus {
  border-color: var(--accent);
  background: var(--bg-elevated);
  box-shadow: 0 0 0 3px var(--accent-subtle);
}

input::placeholder, textarea::placeholder {
  color: var(--text-muted);
}

select {
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16'%3E%3Cpath fill='%238892BB' d='M4 6l4 4 4-4'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 10px center;
  background-size: 16px;
  padding-right: 2rem;
  cursor: pointer;
}

input[type="range"] {
  -webkit-appearance: none;
  appearance: none;
  width: 100%;
  height: 4px;
  border-radius: var(--radius-pill);
  background: var(--bg-tertiary);
  border: none;
  padding: 0;
  cursor: pointer;
}

input[type="range"]::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: var(--accent);
  box-shadow: 0 0 8px var(--accent-glow);
  cursor: pointer;
  transition: transform var(--transition-fast);
}

input[type="range"]::-webkit-slider-thumb:hover {
  transform: scale(1.2);
}

input[type="checkbox"] {
  width: 16px;
  height: 16px;
  border-radius: var(--radius-xs);
  border: 1px solid var(--border-strong);
  background: var(--bg-tertiary);
  cursor: pointer;
  accent-color: var(--accent);
  flex-shrink: 0;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--text-base);
  color: var(--text-primary);
  cursor: pointer;
  user-select: none;
}

/* Radio group */
.radio-group {
  display: flex;
  gap: var(--space-3);
  flex-wrap: wrap;
}

.radio-option {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-3) var(--space-4);
  background: var(--bg-tertiary);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  cursor: pointer;
  font-size: var(--text-base);
  color: var(--text-secondary);
  transition: border-color var(--transition-base), background var(--transition-base),
              color var(--transition-base);
}

.radio-option:has(input:checked) {
  border-color: var(--border-accent);
  background: var(--accent-subtle);
  color: var(--accent-light);
}

.radio-option input[type="radio"] {
  accent-color: var(--accent);
  width: 14px;
  height: 14px;
}

/* ── 8. Tab System ─────────────────────────────────────────── */
.tab-bar {
  display: flex;
  gap: 2px;
  background: var(--bg-tertiary);
  border-radius: var(--radius-md);
  padding: 3px;
  border: 1px solid var(--border);
}

.tab-btn {
  flex: 1;
  padding: var(--space-2) var(--space-4);
  border-radius: var(--radius-sm);
  border: none;
  background: transparent;
  color: var(--text-secondary);
  font-size: var(--text-sm);
  font-weight: var(--weight-medium);
  cursor: pointer;
  transition: background var(--transition-base), color var(--transition-base),
              box-shadow var(--transition-base);
  white-space: nowrap;
}

.tab-btn:hover:not(.tab-btn--disabled) {
  background: var(--bg-elevated);
  color: var(--text-primary);
}

.tab-btn--active {
  background: var(--accent-subtle);
  color: var(--accent-light);
  box-shadow: inset 0 0 0 1px var(--border-accent);
}

.tab-btn--disabled {
  opacity: 0.35;
  cursor: not-allowed;
}

.tab-content {
  padding-top: var(--space-6);
}

/* ── 9. Modal / Overlay System ─────────────────────────────── */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(7, 8, 15, 0.75);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: var(--z-modal);
  padding: var(--space-6);
}

.modal-box {
  background: var(--bg-secondary);
  border: 1px solid var(--border-strong);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-lg), 0 0 60px rgba(99, 102, 241, 0.12);
  width: 100%;
  max-width: 640px;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.modal-box--wide { max-width: 860px; }

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-5) var(--space-6);
  border-bottom: 1px solid var(--border);
  flex-shrink: 0;
}

.modal-header h2 {
  font-size: var(--text-lg);
  font-weight: var(--weight-semi);
  margin: 0;
}

.modal-body {
  flex: 1;
  overflow-y: auto;
  padding: var(--space-6);
}

.modal-footer {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: var(--space-3);
  padding: var(--space-4) var(--space-6);
  border-top: 1px solid var(--border);
  flex-shrink: 0;
}

/* ── 10. Separator / Divider ───────────────────────────────── */
.divider {
  height: 1px;
  background: var(--border);
  margin: var(--space-4) 0;
}

/* ── 11. Scrollbar (WebKit) ────────────────────────────────── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.12);
  border-radius: var(--radius-pill);
}
::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.22);
}

/* ── 12. Focus visible (accessibility) ────────────────────── */
:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
  border-radius: var(--radius-xs);
}

/* ── 13. Selection ─────────────────────────────────────────── */
::selection {
  background: var(--accent-subtle);
  color: var(--accent-light);
}

/* ── 14. Gradient text utility ─────────────────────────────── */
.gradient-text {
  background: linear-gradient(135deg, var(--accent-light) 0%, var(--accent-2) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

/* ── 15. Glow utilities ────────────────────────────────────── */
.glow-accent  { box-shadow: var(--shadow-glow); }
.glow-cyan    { box-shadow: var(--shadow-glow-2); }

/* ── 16. Section layout utility ────────────────────────────── */
.section {
  margin-bottom: var(--space-6);
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-5);
}

.section-title {
  font-size: var(--text-lg);
  font-weight: var(--weight-semi);
  color: var(--text-primary);
}

/* ── 17. Grid utilities ────────────────────────────────────── */
.grid-2 { display: grid; grid-template-columns: repeat(2, 1fr); gap: var(--space-4); }
.grid-3 { display: grid; grid-template-columns: repeat(3, 1fr); gap: var(--space-4); }
.grid-4 { display: grid; grid-template-columns: repeat(4, 1fr); gap: var(--space-4); }

/* ── 18. Inline flex utils ─────────────────────────────────── */
.flex     { display: flex; }
.flex-col { display: flex; flex-direction: column; }
.items-center  { align-items: center; }
.justify-between { justify-content: space-between; }
.gap-2 { gap: var(--space-2); }
.gap-3 { gap: var(--space-3); }
.gap-4 { gap: var(--space-4); }
```

---

#### M14.2.0-C — `webui/src/main.js`: import global CSS

Add as the **first import** in `main.js`:

```js
import './style.css'   // ← add this as line 1
import { createApp } from 'vue'
// ... rest unchanged
```

---

#### M14.2.0-D — `webui/src/App.vue`: remove scoped `:root`, update shell layout

Replace the entire `<style scoped>` block. The `:root` variables move to
`style.css`; the shell layout uses the new token names:

```vue
<style scoped>
.app-shell {
  display: flex;
  height: 100vh;
  background: var(--bg-base);
  color: var(--text-primary);
  font-family: var(--font-sans);
  overflow: hidden;
}

.app-sidebar {
  width: var(--sidebar-width);
  flex-shrink: 0;
  z-index: var(--z-raised);
}

.app-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  background: var(--bg-primary);
}

.app-topbar {
  height: var(--topbar-height);
  flex-shrink: 0;
  z-index: var(--z-raised);
}

.app-content {
  flex: 1;
  padding: var(--space-6);
  overflow-y: auto;
}
</style>
```

---

#### M14.2.0-E — `webui/src/components/Sidebar.vue`: modern navigation

Replace the entire `<template>` and `<style scoped>` (keep the `<script
setup>` unchanged):

**Template changes:**
- Add a gradient logo mark (SVG waveform icon + gradient text app name)
- Add single-character emoji/icon before each nav group label
- Add a thin gradient line between nav groups
- Bottom: a version/build badge

```vue
<template>
  <nav class="sidebar">

    <!-- Brand -->
    <div class="sidebar-brand">
      <div class="sidebar-brand-icon">
        <!-- Simple waveform SVG mark -->
        <svg width="22" height="22" viewBox="0 0 22 22" fill="none">
          <path d="M1 11 Q3 5 5 11 Q7 17 9 11 Q11 5 13 11 Q15 17 17 11 Q19 5 21 11"
                stroke="url(#wg)" stroke-width="2" stroke-linecap="round" fill="none"/>
          <defs>
            <linearGradient id="wg" x1="0" y1="0" x2="22" y2="0" gradientUnits="userSpaceOnUse">
              <stop offset="0%" stop-color="#6366F1"/>
              <stop offset="100%" stop-color="#06B6D4"/>
            </linearGradient>
          </defs>
        </svg>
      </div>
      <span class="sidebar-brand-name gradient-text">WOGD</span>
      <span class="sidebar-brand-sub">DDSP Trainer</span>
    </div>

    <!-- Nav groups -->
    <div class="sidebar-scroll">

      <div class="sidebar-group">
        <div class="sidebar-group-label">
          <span class="sidebar-group-icon">🗄</span> Dataset
        </div>
        <ul class="sidebar-links">
          <li><RouterLink to="/datasets"          class="sidebar-link">Upload &amp; Ingestion</RouterLink></li>
          <li><RouterLink to="/datasets/manager"  class="sidebar-link">Dataset Manager</RouterLink></li>
          <li><RouterLink to="/datasets/preprocess" class="sidebar-link">Preprocessing</RouterLink></li>
        </ul>
      </div>

      <div class="sidebar-divider"></div>

      <div class="sidebar-group">
        <div class="sidebar-group-label">
          <span class="sidebar-group-icon">🧠</span> Model
        </div>
        <ul class="sidebar-links">
          <li><RouterLink to="/model" class="sidebar-link">Training Config</RouterLink></li>
        </ul>
      </div>

      <div class="sidebar-divider"></div>

      <div class="sidebar-group">
        <div class="sidebar-group-label">
          <span class="sidebar-group-icon">📊</span> Training
        </div>
        <ul class="sidebar-links">
          <li><RouterLink to="/training" class="sidebar-link">Dashboard</RouterLink></li>
        </ul>
      </div>

      <div class="sidebar-divider"></div>

      <div class="sidebar-group">
        <div class="sidebar-group-label">
          <span class="sidebar-group-icon">🎙</span> Inference
        </div>
        <ul class="sidebar-links">
          <li><RouterLink to="/inference" class="sidebar-link">Playground</RouterLink></li>
          <li><RouterLink to="/export"    class="sidebar-link">Model Export</RouterLink></li>
          <li><RouterLink to="/presets"   class="sidebar-link">Presets</RouterLink></li>
        </ul>
      </div>

      <div class="sidebar-divider"></div>

      <div class="sidebar-group">
        <div class="sidebar-group-label">
          <span class="sidebar-group-icon">🔬</span> Experimental
        </div>
        <ul class="sidebar-links">
          <li><RouterLink to="/experimental/reverb"   class="sidebar-link">Reverb IR</RouterLink></li>
          <li><RouterLink to="/experimental/f0-editor" class="sidebar-link">F0 Editor</RouterLink></li>
          <li><RouterLink to="/experimental/mixer"    class="sidebar-link">Component Mixer</RouterLink></li>
        </ul>
      </div>

    </div><!-- end sidebar-scroll -->

    <!-- Footer -->
    <div class="sidebar-footer">
      <RouterLink to="/settings" class="sidebar-link sidebar-link--settings">
        ⚙ Settings
      </RouterLink>
    </div>

  </nav>
</template>
```

**Style block:**

```vue
<style scoped>
.sidebar {
  height: 100vh;
  width: var(--sidebar-width);
  background: linear-gradient(180deg, var(--bg-secondary) 0%, var(--bg-primary) 100%);
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* --- Brand --- */
.sidebar-brand {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-4) var(--space-4);
  border-bottom: 1px solid var(--border);
  flex-shrink: 0;
}

.sidebar-brand-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  background: var(--accent-subtle);
  border-radius: var(--radius-sm);
  flex-shrink: 0;
}

.sidebar-brand-name {
  font-size: var(--text-md);
  font-weight: var(--weight-bold);
  letter-spacing: -0.02em;
  line-height: 1;
}

.sidebar-brand-sub {
  display: none; /* shown only on hover/wide variant; hide for now */
}

/* --- Scroll area --- */
.sidebar-scroll {
  flex: 1;
  overflow-y: auto;
  padding: var(--space-3) 0;
}

/* --- Group --- */
.sidebar-group {
  padding: var(--space-1) 0;
}

.sidebar-group-label {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-4);
  font-size: var(--text-xs);
  font-weight: var(--weight-semi);
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--text-muted);
}

.sidebar-group-icon {
  font-size: 0.875rem;
  line-height: 1;
}

.sidebar-divider {
  height: 1px;
  margin: var(--space-2) var(--space-4);
  background: var(--border);
}

/* --- Links --- */
.sidebar-links {
  list-style: none;
  margin: 0;
  padding: 0;
}

.sidebar-link {
  display: flex;
  align-items: center;
  padding: 0.5rem var(--space-4);
  color: var(--text-secondary);
  text-decoration: none;
  font-size: var(--text-base);
  font-weight: var(--weight-normal);
  border-left: 2px solid transparent;
  transition: background var(--transition-base), color var(--transition-base),
              border-color var(--transition-base), box-shadow var(--transition-base);
  border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
  margin-right: var(--space-2);
}

.sidebar-link:hover {
  background: var(--bg-tertiary);
  color: var(--text-primary);
}

.sidebar-link.router-link-active {
  background: var(--accent-subtle);
  color: var(--accent-light);
  border-left-color: var(--accent);
  font-weight: var(--weight-medium);
  box-shadow: inset 0 0 16px rgba(99, 102, 241, 0.08);
}

/* --- Footer --- */
.sidebar-footer {
  border-top: 1px solid var(--border);
  padding: var(--space-3) 0;
  flex-shrink: 0;
}

.sidebar-link--settings {
  color: var(--text-muted);
  font-size: var(--text-sm);
}

.sidebar-link--settings:hover {
  color: var(--text-secondary);
}
</style>
```

---

#### M14.2.0-F — `webui/src/components/TopBar.vue`: pill badges, GPU chip, tier badge

Replace the entire component (script, template, style). Keep the same logic,
upgrade the visual layer. **New in this revision:** a persistent **tier badge**
shows the active model tier in its signal color on every view — so the user
always sees which model complexity is active, not just inside Training Config.

**Template:**

```vue
<template>
  <header class="topbar">

    <div class="topbar-left">
      <div class="topbar-breadcrumb text-secondary text-sm">
        {{ currentSection }}
      </div>
    </div>

    <div class="topbar-right">
      <!-- Active tier badge — visible on ALL views; uses tier signal color -->
      <span
        v-if="activeTier"
        class="topbar-tier-badge text-xs text-mono"
        :style="tierBadgeStyle"
        data-testid="tier-badge"
        :title="`Active model tier: ${tierLabel(activeTier)}`"
      >
        {{ tierIcon(activeTier) }} {{ tierLabel(activeTier) }}
      </span>

      <!-- Backend status -->
      <span
        :class="['badge', 'badge-dot', healthBadgeClass]"
        :title="healthLabel"
        data-testid="backend-status"
      >
        {{ healthLabel }}
      </span>

      <!-- TensorBoard status -->
      <span
        :class="['badge', 'badge-dot', tbBadgeClass]"
        :title="tbLabel"
        data-testid="tb-status"
      >
        {{ tbLabel }}
      </span>

      <!-- GPU chip (shown when GPU detected) -->
      <span
        v-if="gpuChip"
        class="badge badge-muted topbar-gpu-chip text-mono"
        data-testid="gpu-chip"
        :title="gpuChip.tooltip"
      >
        🖥 {{ gpuChip.label }}
      </span>

      <!-- Version -->
      <span v-if="version" class="topbar-version text-muted text-xs text-mono">
        v{{ version }}
      </span>
    </div>

  </header>
</template>
```

**Script:**

```vue
<script setup>
import { ref, computed, onMounted, inject } from 'vue'
import { useRoute } from 'vue-router'
import { useModelConfigStore } from '@/stores/modelConfig'
import { tierColor, tierLabel, tierIcon } from '@/utils/tierColors'

const apiClient = inject('apiClient')
const route     = useRoute()
const modelConfig = useModelConfigStore()
const version   = ref(null)
const healthOk  = ref(null)
const tbRunning = ref(null)
const gpuInfo   = ref(null)

// Active tier from Pinia store (null when Wizard not yet completed)
const activeTier = computed(() => modelConfig.activeTier)

// Tier badge: subtle-opacity background + full-color border + full-color text
const tierBadgeStyle = computed(() => {
  if (!activeTier.value) return {}
  const color = tierColor(activeTier.value)
  return {
    '--_tier-color': color,
    color:           color,
    background:      `color-mix(in srgb, ${color} 12%, transparent)`,
    borderColor:     `color-mix(in srgb, ${color} 50%, transparent)`,
  }
})

const SECTION_MAP = {
  '/datasets':                   'Dataset & Preprocessing',
  '/datasets/manager':           'Dataset Manager',
  '/datasets/preprocess':        'Preprocessing',
  '/model':                      'Training Config',
  '/training':                   'Training Dashboard',
  '/inference':                  'Inference Playground',
  '/export':                     'Model Export',
  '/presets':                    'Presets',
  '/experimental/reverb':        'Experimental › Reverb IR',
  '/experimental/f0-editor':     'Experimental › F0 Editor',
  '/experimental/mixer':         'Experimental › Component Mixer',
  '/settings':                   'Settings',
}
const currentSection = computed(() => SECTION_MAP[route.path] ?? 'WOGD DDSP Trainer')

const healthBadgeClass = computed(() => {
  if (healthOk.value === null) return 'badge-muted'
  return healthOk.value ? 'badge-success' : 'badge-error'
})
const healthLabel = computed(() => {
  if (healthOk.value === null) return 'Backend…'
  return healthOk.value ? 'Backend: ok' : 'Backend: error'
})

const tbBadgeClass = computed(() => {
  if (tbRunning.value === null) return 'badge-muted'
  return tbRunning.value ? 'badge-success' : 'badge-warning'
})
const tbLabel = computed(() => {
  if (tbRunning.value === null) return 'TensorBoard…'
  return tbRunning.value ? 'TensorBoard' : 'TensorBoard: off'
})

const gpuChip = computed(() => {
  if (!gpuInfo.value?.gpus?.length) return null
  const g = gpuInfo.value.gpus[0]
  const vram = g.total_vram_gb ? `${g.total_vram_gb.toFixed(0)} GB` : ''
  const name = g.name?.replace('NVIDIA GeForce ', '') ?? 'GPU'
  return {
    label: vram ? `${name} · ${vram}` : name,
    tooltip: `${g.name} — ${vram} VRAM · Tier: ${gpuInfo.value.tier ?? 'unknown'}`,
  }
})

onMounted(async () => {
  if (!apiClient) return
  try {
    const h = await apiClient.health()
    version.value = h.version ?? null
    healthOk.value = h.ok ?? false
  } catch { healthOk.value = false }
  try {
    const tb = await apiClient.getTensorboard()
    tbRunning.value = !!tb.running
  } catch { tbRunning.value = false }
  try {
    gpuInfo.value = await apiClient.getHostInfo()
  } catch { /* optional */ }
})
</script>
```

**Style:**

```vue
<style scoped>
.topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 var(--space-6);
  height: var(--topbar-height);
  background: var(--bg-secondary);
  border-bottom: 1px solid var(--border);
  flex-shrink: 0;
  gap: var(--space-4);
}

.topbar-left {
  display: flex;
  align-items: center;
  min-width: 0;
}

.topbar-breadcrumb {
  font-weight: var(--weight-medium);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.topbar-right {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  flex-shrink: 0;
}

/* Tier badge — inherits color via inline style (--_tier-color) */
.topbar-tier-badge {
  display: inline-flex;
  align-items: center;
  gap: var(--space-1);
  padding: 2px var(--space-2);
  border-radius: var(--radius-pill);
  border: 1px solid transparent;   /* filled by inline style */
  font-weight: var(--weight-medium);
  font-size: var(--text-xs);
  white-space: nowrap;
  transition: opacity var(--transition-base);
}

.topbar-gpu-chip {
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  font-size: var(--text-xs);
}

.topbar-version {
  padding-left: var(--space-2);
  border-left: 1px solid var(--border);
}
</style>
```

---

#### M14.2.0-G — Vitest: verify no breakage

Run `vitest` after completing M14.2.0-A through M14.2.0-F. All existing tests
must remain green. The design changes are CSS-only and do not touch any
`data-testid` selectors. If any test fails it is due to a structural template
change (e.g. removed element) — fix before proceeding.

Expected result: **all existing Vitest pass; no new tests needed for M14.2.0-A–F**.

---

#### M14.2.0-H — `webui/src/utils/tierColors.js` (new utility)

Create `webui/src/utils/tierColors.js`. No external dependencies.

This utility is imported by `TopBar.vue` (M14.2.0-F), and later by
`ModelTierCard.vue` (M14.2.3), `WizardModal.vue` (M14.2.5),
`TabCore.vue` (M14.2.6), `GpuFeasibilityBanner.vue` (M14.2.4).
It must never be imported in any backend or server file.

```js
// webui/src/utils/tierColors.js
/**
 * Tier identity color system.
 *
 * Each tier has a unique signal color applied consistently across:
 * - TopBar tier badge (every view)
 * - Wizard ModelTierCard border + icon tint
 * - Tab bar active-tab indicator + label
 * - GpuFeasibilityBanner per-tier chip
 * - Disabled tab tooltip tier name
 *
 * Colors are defined as CSS custom properties in style.css :root.
 * tierColor() resolves the live computed value at runtime via
 * getComputedStyle — never hardcode hex values in components.
 */

export const TIER_META = {
  standard:  { label: 'Standard',  token: '--tier-standard',  icon: '🟢' },
  component: { label: 'Component', token: '--tier-component', icon: '🔵' },
  hacks:     { label: 'Hacks',     token: '--tier-hacks',     icon: '🟡' },
  engine:    { label: 'Engine',    token: '--tier-engine',    icon: '🟣' },
  advanced:  { label: 'Advanced',  token: '--tier-advanced',  icon: '🔴' },
}

/**
 * Returns the resolved hex/rgb color string for a tier from the live
 * CSS custom properties. Falls back to --text-muted for unknown tiers.
 * Must be called in a browser context (document must exist).
 */
export function tierColor(tier) {
  return getComputedStyle(document.documentElement)
    .getPropertyValue(TIER_META[tier]?.token ?? '--text-muted')
    .trim()
}

/** Returns the human-readable label for a tier (e.g. 'Standard'). */
export function tierLabel(tier) { return TIER_META[tier]?.label ?? tier }

/** Returns the emoji indicator for compact display (e.g. '🟢'). */
export function tierIcon(tier)  { return TIER_META[tier]?.icon  ?? '⚪' }

/** Returns all tier keys in ascending complexity order. */
export const TIER_ORDER = ['standard', 'component', 'hacks', 'engine', 'advanced']

/**
 * Returns true when candidateTier >= requiredTier in complexity order.
 * Used by tab-bar to determine disabled state.
 */
export function tierAtLeast(candidateTier, requiredTier) {
  return TIER_ORDER.indexOf(candidateTier) >= TIER_ORDER.indexOf(requiredTier)
}
```

**Vitest for this step** (`tests/tierColors.test.js`):

```js
import { describe, it, expect } from 'vitest'
import { TIER_META, TIER_ORDER, tierLabel, tierIcon, tierAtLeast } from '@/utils/tierColors'

describe('tierColors', () => {
  it('has all 5 tiers in TIER_META', () => {
    expect(Object.keys(TIER_META)).toHaveLength(5)
  })

  it('TIER_ORDER has 5 entries in correct order', () => {
    expect(TIER_ORDER).toEqual(['standard', 'component', 'hacks', 'engine', 'advanced'])
  })

  it('tierLabel returns correct labels', () => {
    expect(tierLabel('standard')).toBe('Standard')
    expect(tierLabel('advanced')).toBe('Advanced')
    expect(tierLabel('unknown')).toBe('unknown')
  })

  it('tierIcon returns emoji', () => {
    expect(tierIcon('standard')).toBe('🟢')
    expect(tierIcon('unknown')).toBe('⚪')
  })

  it('tierAtLeast: engine >= component', () => {
    expect(tierAtLeast('engine', 'component')).toBe(true)
  })

  it('tierAtLeast: standard < hacks', () => {
    expect(tierAtLeast('standard', 'hacks')).toBe(false)
  })

  it('tierAtLeast: advanced >= advanced', () => {
    expect(tierAtLeast('advanced', 'advanced')).toBe(true)
  })
})
```

---

## Phase 1 — Backend

### M14.1.1 — `train/gpu.py`: `VRAMEstimate` + `estimate_model_vram()`

**File:** `train/gpu.py`

Add after `propose_presets()`:

```python
@dataclass
class VRAMEstimate:
    """Lightweight VRAM accounting for a model configuration.

    ``peak_gb`` is the estimated peak VRAM in GB.
    ``warning`` is a human-readable message when the estimate exceeds a
    known threshold (e.g. PolyDDSP N>2 on 6 GB), or ``None``.
    """

    peak_gb: float
    warning: str | None = None


def estimate_model_vram(
    model_tier: str,
    n_voices: int = 1,
    use_latent: bool = False,
    use_content_encoder: bool = False,
) -> VRAMEstimate:
    """Estimate peak VRAM in GB for a given model configuration.

    Base figures from architecture.md VRAM budget table
    (batch_size=1, seq_len=2 s @ 16 kHz, mixed precision, 3-scale STFT):

        baseline (standard DDSP)        ~2.2 GB
        use_latent (+GRUEncoder/VAE)    +0.15 GB
        use_content_encoder (+HuBERT)   +0.36 GB
        PolyDDSP N voices               baseline × N

    All tiers from 'standard' through 'engine' have the same baseline;
    'advanced' activates the optional overhead params.
    """
    BASELINE_GB = 2.2
    overhead = 0.0
    warning = None

    if model_tier == "advanced":
        if use_latent:
            overhead += 0.15
        if use_content_encoder:
            overhead += 0.36
        if n_voices > 1:
            overhead += BASELINE_GB * (n_voices - 1)

    peak = BASELINE_GB + overhead

    if peak > 6.0:
        warning = (
            f"Estimated {peak:.1f} GB exceeds 6 GB — "
            f"recommend a GPU with at least {int(peak) + 1} GB VRAM."
        )

    return VRAMEstimate(peak_gb=round(peak, 2), warning=warning)
```

**VRAM constraint:** function is pure Python arithmetic — zero GPU usage.

---

### M14.1.2 — `server/db.py`: `model_tier` column migration

**File:** `server/db.py`

1. In `init_db()`, add `model_tier TEXT NOT NULL DEFAULT 'standard'` to both
   `CREATE TABLE IF NOT EXISTS presets` and `CREATE TABLE IF NOT EXISTS runs`.

2. Add a migration helper called from `init_db()` after the `CREATE TABLE`
   statements:

```python
def _migrate_add_model_tier(cur: sqlite3.Cursor) -> None:
    """Add model_tier column to presets and runs if not already present.

    Safe to call on existing databases: uses sqlite3 PRAGMA table_info
    to detect the column before attempting ALTER TABLE.
    """
    for table in ("presets", "runs"):
        cur.execute(f"PRAGMA table_info({table})")
        cols = {row[1] for row in cur.fetchall()}
        if "model_tier" not in cols:
            cur.execute(
                f"ALTER TABLE {table} ADD COLUMN model_tier TEXT NOT NULL DEFAULT 'standard'"
            )
```

Call `_migrate_add_model_tier(cur)` at the end of `init_db()` before
`conn.commit()`.

**No data loss:** `DEFAULT 'standard'` means all existing rows silently
inherit the standard tier.

---

### M14.1.3 — `server/presets.py`: tier-aware keys + seed

**File:** `server/presets.py`

Add after `PARAM_KEYS`:

```python
# Tier-specific param keys (not VRAM-bounded; validated, not clamped)
VARIANT_KEYS: tuple = (  # M8 DDSPVariant fields
    "waveform",
    "harmonic_ratios",
    "fm_depth",
    "fm_ratio",
    "pd_k",
    "use_lfo",
    "lfo_freq",
    "lfo_depth",
    "use_trainable_wavetable",
    "use_angular_cumsum",
    "band_mask_low_hz",
    "band_mask_high_hz",
)
ENGINE_KEYS: tuple = (  # M9/M10 engine fields
    "engine",  # "harmonic" | "sinusoidal" | "combsub" | "newt"
    "noise_color",  # "white" | "pink" | "brown"
    "noise_grain_jitter",
    "newt_hidden_size",
    "newt_n_layers",
)
ADVANCED_KEYS: tuple = (  # M11–M13 advanced fields
    "use_latent",
    "latent_dim",
    "kl_beta",
    "n_voices",
    "use_content_encoder",
    "content_encoder_name",
)
```

Change `build_builtin_presets()` signature:

```python
def build_builtin_presets(bounds: ParameterBounds, tier: str = "standard") -> list[dict]:
```

Add `"model_tier": tier` to each preset dict.

Change `seed_builtin_presets()`:

```python
def seed_builtin_presets(conn, bounds: ParameterBounds, tier: str = "standard") -> int:
    inserted = 0
    for preset in build_builtin_presets(bounds, tier=tier):
        # Composite lookup: (name, model_tier) pair must be unique
        existing = preset_by_name_and_tier(conn, preset["name"], tier)
        if existing is None:
            preset_create(conn, ..., model_tier=tier)
            inserted += 1
    conn.commit()
    return inserted
```

Add `preset_by_name_and_tier(conn, name, tier)` query to `server/db.py` and
update `preset_create()` to accept `model_tier` parameter.

**Existing callers** pass no `tier` → default `'standard'` → identical
behaviour.

---

### M14.1.4 — `server/routes/training.py`: tier fields + validate + resume guard

**File:** `server/routes/training.py`

```python
class RunCreateRequest(BaseModel):
    name: str
    dataset_id: str | None = None
    preset_id: str | None = None
    params: dict | None = None
    model_tier: str = "standard"  # NEW — default preserves all existing callers


class ValidateRequest(BaseModel):
    preset_id: str | None = None
    params: dict | None = None
    model_tier: str = "standard"  # NEW
```

In `validate()` response, add:

```python
preset_tier = preset.get("model_tier", "standard") if preset else "standard"
model_tier_mismatch = preset_tier != req.model_tier
return {
    "params": clamped,
    "clamped_fields": clamped_fields,
    "bounds": bounds_to_dict(bounds),
    "model_tier_mismatch": model_tier_mismatch,  # NEW
}
```

In `create_run()`, store `model_tier` in the run record:

```python
run_create(
    conn,
    run_id,
    req.name,
    config,
    req.dataset_id,
    created_from_preset=req.preset_id,
    model_tier=req.model_tier,
)  # NEW
```

Update `run_create()` in `server/db.py` to accept and persist `model_tier`.

In `resume_run()`, add checkpoint-tier guard:

```python
run = run_get(conn, run_id)
stored_tier = run.get("model_tier", "standard")
latest = latest_checkpoint(run_id)
if latest is not None:
    ckpt = torch.load(latest, map_location="cpu", weights_only=True)
    ckpt_tier = ckpt.get("variant_flags", {}).get("model_tier", "standard")
    if ckpt_tier != stored_tier:
        raise HTTPException(
            status_code=409,
            detail=f"checkpoint_tier_mismatch: run={stored_tier}, checkpoint={ckpt_tier}",
        )
```

---

### M14.1.5 — `server/tasks.py`: tier-aware `build_training()`

**File:** `server/tasks.py`

In `build_training(model_config, checkpoint_dir)`:

```python
model_tier = model_config.get("model_tier", "standard")

# --- Tier: hacks / engine / advanced → DDSPVariant (M8) ---
if model_tier in ("hacks", "engine", "advanced"):
    from model.ddsp.variant import DDSPVariant

    variant = DDSPVariant.from_dict(model_config.get("variant", {}))
else:
    from model.ddsp.variant import DDSPVariant

    variant = DDSPVariant()  # all-default no-op

# --- Tier: engine / advanced → engine field (M9/M10) ---
engine = model_config.get("engine", "harmonic")

# --- Tier: advanced → latent / poly / VC (M11–M13) ---
use_latent = bool(model_config.get("use_latent", False))
latent_dim = int(model_config.get("latent_dim", 32))
kl_beta = float(model_config.get("kl_beta", 1.0))
n_voices = int(model_config.get("n_voices", 1))
use_content_encoder = bool(model_config.get("use_content_encoder", False))
content_encoder_name = model_config.get("content_encoder_name", "hubert-soft")
```

Pass `variant`, `engine`, and advanced fields into `DDSPConfig` only when the
corresponding milestone's model classes exist (guard with `hasattr(DDSPConfig,
'variant')` until M8 is implemented). Until then they are parsed but silently
ignored — this way M14.1.5 can land before M8–M13 code is written.

---

### M14.1.6 — `server/routes/host.py`: `GET /api/gpu/feasibility`

**File:** `server/routes/host.py`

```python
@router.get("/feasibility")
def gpu_feasibility(
    model_tier: str = "standard",
    n_voices: int = 1,
    use_latent: bool = False,
    use_content_encoder: bool = False,
) -> dict[str, Any]:
    """Return VRAM feasibility for the requested config + all five tiers."""
    from train.gpu import estimate_model_vram, detect_gpus

    gpus = detect_gpus()
    available_gb = max((g["available_vram_gb"] or g["total_vram_gb"] for g in gpus), default=6.0)

    # Current config estimate
    est = estimate_model_vram(model_tier, n_voices, use_latent, use_content_encoder)

    # All-tier summary (default params: n_voices=1, no latent, no CE)
    ALL_TIERS = ("standard", "component", "hacks", "engine", "advanced")
    tier_feasibility = {}
    for t in ALL_TIERS:
        e = estimate_model_vram(t)
        tier_feasibility[t] = {
            "fits": e.peak_gb <= available_gb,
            "estimated_gb": e.peak_gb,
            "warning": e.warning,
        }
    # For 'advanced' also compute worst-case (N=3)
    e_adv = estimate_model_vram("advanced", n_voices=3)
    tier_feasibility["advanced"]["worst_case_gb"] = e_adv.peak_gb
    tier_feasibility["advanced"]["worst_case_warning"] = e_adv.warning

    return {
        "fits": est.peak_gb <= available_gb,
        "estimated_gb": est.peak_gb,
        "available_gb": round(available_gb, 2),
        "warning": est.warning,
        "tier_feasibility": tier_feasibility,
    }
```

Register route prefix: the existing `router = APIRouter(prefix="/host")` in
`host.py` means the endpoint is reachable at `GET /api/host/feasibility`.
Alternatively, a new `APIRouter(prefix="/gpu")` in a new `server/routes/gpu.py`
gives the cleaner path `GET /api/gpu/feasibility`. **Decision: new file
`server/routes/gpu.py`** — keeps `host.py` focused on host-info.

Mount in `server/main.py`:

```python
from server.routes import gpu as gpu_routes

app.include_router(gpu_routes.router, prefix="/api")
```

---

### M14.1.7 — `tests/test_gpu_feasibility.py`

**File:** `tests/test_gpu_feasibility.py` (new)

Test cases:
- `estimate_model_vram("standard")` → `VRAMEstimate(peak_gb=2.2, warning=None)`
- `estimate_model_vram("advanced", n_voices=1)` → `VRAMEstimate(2.2, None)`
- `estimate_model_vram("advanced", use_latent=True)` → `VRAMEstimate(2.35, None)`
- `estimate_model_vram("advanced", use_content_encoder=True)` → `VRAMEstimate(2.56, None)`
- `estimate_model_vram("advanced", n_voices=3)` → `peak_gb=6.6`, warning set
- `estimate_model_vram("advanced", n_voices=3, use_latent=True, use_content_encoder=True)` → peak > 7.0, warning set
- `GET /api/gpu/feasibility` (no GPU mock) → response has `tier_feasibility` with all 5 tiers
- `GET /api/gpu/feasibility?model_tier=advanced&n_voices=3` → `fits=False` on 6 GB mock

---

### M14.1.8 — `tests/test_presets_tier.py`

**File:** `tests/test_presets_tier.py` (new)

Test cases:
- `build_builtin_presets(bounds, tier="standard")` → 3 presets with `model_tier="standard"`
- `build_builtin_presets(bounds, tier="engine")` → 3 presets with `model_tier="engine"`
- `seed_builtin_presets()` twice: second call inserts 0 (idempotent)
- `seed_builtin_presets()` for `"standard"` then `"engine"`: total 6 rows, no collision
- `clamp_params()` with `VARIANT_KEYS`/`ENGINE_KEYS`/`ADVANCED_KEYS` mixed in → only `PARAM_KEYS` are clamped

---

### M14.1.9 — `tests/test_training_tier.py`

**File:** `tests/test_training_tier.py` (new)

Test cases:
- `build_training({...standard params...}, ckpt_dir)` → `DDSPConfig` has default variant
- `build_training({...hacks params, model_tier="hacks"...}, ckpt_dir)` → variant parsed
- `build_training({...advanced params, model_tier="advanced", n_voices=2...}, ckpt_dir)` → `n_voices=2` extracted
- `build_training({model_tier="standard"}, ckpt_dir)` with missing new fields → no KeyError
- `POST /api/runs/{id}/resume` with mismatched checkpoint tier → HTTP 409

---

## Phase 2 — Frontend

### M14.2.1 — `webui/src/stores/modelConfig.js`

**File:** `webui/src/stores/modelConfig.js` (new)

```js
import { defineStore } from 'pinia'

export const useModelConfigStore = defineStore('modelConfig', {
  state: () => ({
    activeTier: null,           // null = wizard not yet completed
    wizardCompleted: false,
    gpuFeasibility: null,       // response from GET /api/gpu/feasibility
    selectedPreset: null,
    targetMode: 'offline',
    coreParams: {
      learning_rate: 0.001,
      batch_size: 1,
      epochs: 100,
      decoder_type: 'gru',
      use_reverb: true,
    },
    componentParams: { n_harmonics: 60, n_filter_banks: 32 },
    hacksVariant: {},           // DDSPVariant fields (M8)
    engineParams: { engine: 'harmonic', noise_color: 'white',
                    newt_hidden_size: 64, newt_n_layers: 4 },
    advancedParams: {
      use_latent: false, latent_dim: 32, kl_beta: 1.0,
      n_voices: 1,
      use_content_encoder: false, content_encoder_name: 'hubert-soft',
    },
  }),
  getters: {
    isFeasible: (state) => state.gpuFeasibility?.fits ?? true,
    currentTierFeasibility: (state) =>
      state.gpuFeasibility?.tier_feasibility ?? {},
  },
  actions: {
    setTierFromWizard(tier, preset, targetMode) {
      this.activeTier = tier
      this.wizardCompleted = true
      this.selectedPreset = preset
      this.targetMode = targetMode
    },
    async checkFeasibility(apiClient) {
      const p = this.advancedParams
      this.gpuFeasibility = await apiClient.getGpuFeasibility({
        model_tier: this.activeTier ?? 'standard',
        n_voices: p.n_voices,
        use_latent: p.use_latent,
        use_content_encoder: p.use_content_encoder,
      })
    },
    resetToWizard() {
      this.activeTier = null
      this.wizardCompleted = false
    },
  },
})
```

---

### M14.2.2 — Mock fixtures + `mockApiClient.js`

**File:** `webui/src/mocks/fixtures.js`

Add `tierFeasibilityFixture`:

```js
export const tierFeasibilityFixture = {
  fits: true,
  estimated_gb: 2.2,
  available_gb: 4.1,
  warning: null,
  tier_feasibility: {
    standard:  { fits: true,  estimated_gb: 2.2, warning: null },
    component: { fits: true,  estimated_gb: 2.4, warning: null },
    hacks:     { fits: true,  estimated_gb: 2.4, warning: null },
    engine:    { fits: true,  estimated_gb: 2.2, warning: null },
    advanced:  { fits: false, estimated_gb: 6.6,
                 warning: 'PolyDDSP N=3 requires ~6.6 GB (8 GB GPU recommended)',
                 worst_case_gb: 7.1, worst_case_warning: '...' },
  },
}
```

Add `model_tier: 'standard'` to all existing preset fixtures.

**File:** `webui/src/mocks/mockApiClient.js`

Add method:

```js
async getGpuFeasibility(_params) {
  return tierFeasibilityFixture
}
```

---

### M14.2.3 — `ModelTierCard.vue`

**Props:** `tier` (string), `label` (string), `description` (string),
`icon` (string), `feasibility` (`{ fits, estimated_gb, warning }`),
`selected` (bool), `disabled` (bool).

**Emits:** `select` (tier string).

Renders: icon, label, short description, GPU badge (`✓ fits X.X GB` /
`⚠ needs Y GB`), selected state (border highlight), disabled state
(greyed, cursor-not-allowed, no emit).

---

### M14.2.4 — `GpuFeasibilityBanner.vue`

**Props:** none (reads from `useModelConfigStore` + injects `apiClient`).

**Three render states** (all must be covered by Vitest):
1. `no-gpu` — "No GPU detected — training will run on CPU (slow)."
2. `fits` — green: "GPU · X GB available · current config ~Y.Y GB ✓"
3. `warning` — amber: "GPU · X GB available · current config ~Y.Y GB ⚠ [message]"

Watches `activeTier`, `advancedParams.n_voices`, `advancedParams.use_latent`,
`advancedParams.use_content_encoder` → calls `checkFeasibility()` on change.

---

### M14.2.5 — `WizardModal.vue`

**Step 1 — Model Tier:**
Renders a 2×3 grid of `ModelTierCard` components. Data sourced from
`gpuFeasibility.tier_feasibility` (fetched on modal open via
`checkFeasibility()`). "Skip" link at bottom-left closes modal and sets
`activeTier = 'standard'`, `wizardCompleted = true`.

**Step 2 — Quality / Preset:**
Three quality cards (FAST / NORMAL / QUALITY) showing `estimated_gb` from
`tier_feasibility[activeTier]` scaled by preset factor (0.25 / 0.50 / 1.0).
Optional "Load custom preset" selector filtered to `model_tier = activeTier`.

**Step 3 — Target Mode:**
Two radio options: Offline / Studio, Realtime / Low-Latency. Short export
format note per option.

On "Start Training Setup ✓": calls `setTierFromWizard(tier, preset, targetMode)`,
emits `complete`, closes modal.

Reopenable: parent `TrainingConfigView` shows "⚙ Reconfigure Model" button
that calls `resetToWizard()`.

---

### M14.2.6 — Tab components (`TabCore`, `TabComponent`, `TabHacks`, `TabEngine`, `TabAdvanced`)

Each tab component:
- Reads/writes the relevant slice of `useModelConfigStore`.
- Is a pure render component (no direct API calls; all data via store + props).
- Has a `data-testid` on every interactive element for Vitest.

**`TabCore.vue`:** preset selector (filtered to `activeTier`), learning rate,
batch size, epochs, decoder type dropdown, reverb toggle, "Save as Preset"
button.

**`TabComponent.vue`:** n_harmonics slider (range from `bounds.n_harmonics_min`
to `bounds.n_harmonics_max`), n_filter_banks slider, link button to
`ComponentMixerView`.

**`TabHacks.vue`:** waveform dropdown (sin/square/saw), FM depth/ratio sliders,
phase distortion `pd_k`, LFO toggle + freq/depth, trainable wavetable toggle,
angular cumsum toggle, loss band-mask Hz range. Link button to SynthHacksView
for full controls.

**`TabEngine.vue`:** engine dropdown (harmonic / sinusoidal / combsub / newt),
conditional NEWT controls (hidden_size, n_layers) shown when `engine === 'newt'`,
noise color selector shown for combsub/sinusoidal.

**`TabAdvanced.vue`:** VAE section (`use_latent` toggle, `latent_dim`, `kl_beta`),
PolyDDSP section (`n_voices` number input with VRAM cost indicator), Voice
Conversion section (`use_content_encoder` toggle, `content_encoder_name`
dropdown). Each section's VRAM cost badge updates reactively via the store.

---

### M14.2.7 — `TrainingConfigView.vue` refactor

**Structural change:** the view becomes a thin wrapper:
1. Imports and renders `GpuFeasibilityBanner` at the top.
2. Shows `WizardModal` when `!wizardCompleted` (via `v-if`).
3. Renders tab bar with five tabs; tabs with tier > `activeTier` get
   `disabled` class + `aria-disabled="true"`.
4. Renders the active tab component in the content area via `<component :is>`.
5. "⚙ Reconfigure Model" button in the view header calls `resetToWizard()`.
6. "▶ Start Training" button at the bottom assembles the full config from all
   store slices and calls `apiClient.startRun(config)`.

All existing `data-testid` attributes on the form fields are migrated to the
respective Tab component so existing Vitest selectors continue to work.

---

### M14.2.8 — `PresetManagerView.vue`: `model_tier` filter

Add a `<select>` dropdown above the preset list:

```
All tiers | Standard | Component | Hacks | Engine | Advanced
```

On change, calls `apiClient.listPresets({ model_tier: selectedFilter })`.
`mockApiClient.listPresets` already supports the `model_tier` query param
after M14.2.2 (filter applied client-side on the fixture array).

---

### M14.2.9 — Vitest suite

**Tests to add / extend:**

- `WizardModal.spec.js` — step 1→2→3 complete flow; skip link; reopen after reset.
- `GpuFeasibilityBanner.spec.js` — 3 render states (no-gpu / fits / warning).
- `ModelTierCard.spec.js` — fits/warn/disabled/selected states; emit on click.
- `TabCore.spec.js`, `TabComponent.spec.js`, `TabHacks.spec.js`,
  `TabEngine.spec.js`, `TabAdvanced.spec.js` — each renders with mock store
  state; interactive controls update store.
- `TrainingConfigView.spec.js` (extend existing) — tab switching; disabled tab
  tooltip; wizard reopens on "Reconfigure"; "Start Training" assembles full
  config.
- `PresetManagerView.spec.js` (extend existing) — model_tier filter changes
  preset list.

All tests use `MockApiClient` + fixtures; no backend required.

---

## History

_Append-only. Add entries as steps are completed._

<!-- Steps will be logged here as work proceeds. -->

## BUGS

_Bug references only (full records in [`doc/bugs.md`](../bugs.md)):_

- **BUG-10** — Training Config zeigt falschen freien GPU-VRAM-Wert (`available_gb`). Status: open.
  - Ursache: `server/routes/gpu.py::gpu_feasibility()` liefert `available_vram_gb`
    (`torch.cuda.mem_get_info()` — Momentaufnahme), nicht `total_vram_gb`. Beim
    App-Start ist der CUDA-Kontext bereits initialisiert (~1-2 GB reserviert),
    sodass der angezeigte Wert zu niedrig ist.
  - Fix-Vorschlag: `gpu_feasibility()` soll `total_vram_gb` für `available_gb`
    verwenden (Training läuft exklusiv auf der GPU; total ist der maßgebliche
    Budgetwert). `GpuFeasibilityBanner.vue` Label von „X GB available" auf
    „X GB total" anpassen. Beide Felder (`total_gb`, `free_gb`) im Response
    liefern für künftige Anzeige.

- **BUG-11** — Wizard-Tier-Auswahl: `Advanced` nicht anwählbar, obwohl VRAM-Bedarf
  erst durch Quality-Auswahl festgelegt wird. Status: open.
  - Ursache: `WizardModal.vue` setzt `:disabled="!tierFeasibility[t.tier]?.fits"` auf
    die Tier-Card. `fits` basiert auf dem `estimated_gb` des Default-Presets (NORMAL,
    1.0×factor), nicht auf dem Minimum (FAST, 0.25×). Da `available_gb` durch BUG-10
    zu niedrig ist, ist `advanced` pauschal gesperrt, bevor der Nutzer überhaupt eine
    Quality wählen konnte.
  - Fix-Vorschlag (zweiteilig):
    1. BUG-10 zuerst beheben (korrekte `available_gb`).
    2. `WizardModal.vue`: Tier-Cards nie per `:disabled` sperren. Warnung-Badge bleibt
       sichtbar. Feasibility-Prüfung auf **Step 2 (Quality-Auswahl)** verlagern: jede
       Quality-Card zeigt ihren VRAM-Bedarf (`vramFactor × estimated_gb`) und wird
       disabled/warn markiert, wenn dieser Wert `available_gb` überschreitet. Nur wenn
       **alle** Qualitäten eines Tiers die GPU überschreiten, kann optional eine
       Gesamt-Warnung im Step-1-Badge erscheinen — aber kein `disabled`.
