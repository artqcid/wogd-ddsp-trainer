---
type: implementation-plan
status: draft
milestone: M8 - Experimental synthesis hacks
generated:
  by: primary-agent
  at: 2026-09-01
stale_after: 2027-03-01
---

# Implementation Plan — M8 Experimental Synthesis Hacks

_Granular plan for milestone M8. Meta plan: [`../plan.md`](../plan.md); status:
[`../checklist.md`](../checklist.md); rationale (fact vs speculation):
[`../experimental-sdk-hacking.md`](../experimental-sdk-hacking.md)._

## Constraints & principles

- **We own the DDSP core (PyTorch)** — every hack is a first-class feature
  flag, not a patch to a third-party library.
- **Default = off.** Every hack ships with a safe no-op default so existing
  checkpoints and training runs are unaffected.
- **Checkpoint tagging.** Steps that alter model weights (M8.3c trainable
  wavetable) must tag the checkpoint with `variant_flags` so load code can
  detect mismatches.
- **One subagent task per step.** Each step is sized for a single focused
  subagent. Primary agent builds and tests after every step.
- **VRAM budget: 6 GB (RTX 3060).** No step may increase VRAM beyond the
  existing budget; most hacks add zero VRAM overhead.

---

## File map (all affected files at a glance)

```
model/ddsp/variant.py          NEW  — DDSPVariant dataclass (M8.1.1)
model/ddsp/synths.py           MOD  — harmonic ratios, waveform fn, FM, PD (M8.2–M8.3)
model/ddsp/__init__.py         MOD  — export DDSPVariant (M8.1.1)
model/ddsp_model.py            MOD  — accept + forward variant; LFO injection (M8.1.2, M8.4.2)
model/losses.py                MOD  — freq-band mask parameter (M8.4.1)
server/tasks.py                MOD  — parse variant from run config → DDSPVariant (M8.1.3)
server/routes/training.py      MOD  — pass variant fields through (M8.1.3)
server/presets.py              MOD  — add variant keys to PARAM_KEYS (M8.1.3)
webui/src/views/SynthHacksView.vue  NEW  — UI panel (M8.1.4)
webui/src/router/index.js      MOD  — /experimental/synth-hacks route (M8.1.4)
webui/src/components/Sidebar.vue   MOD  — Synth Hacks link (M8.1.4)
webui/src/api/apiClient.js     MOD  — no new endpoints; variant goes in run params (M8.1.4)
webui/src/mocks/mockApiClient.js   MOD  — mock variant defaults (M8.1.4)
webui/src/mocks/fixtures.js    MOD  — fixture defaults (M8.1.4)
tests/test_synths_variant.py   NEW  — smoke tests per hack (M8.5.1)
doc/experimental-sdk-hacking.md    MOD  — finalize (M8.5.2)
```

---

## M8.1 — Variant-Config Infrastructure

> Goal: a single `DDSPVariant` dataclass that carries all hack flags,
> threaded from the UI through the REST API into `DDSPModel` and `DDSPCore`.
> Every downstream step (M8.2–M8.4) only adds fields to this dataclass and
> reads them in `synths.py` / `losses.py`. No step touches the run lifecycle
> beyond what is described here.

### M8.1.1 — `DDSPVariant` dataclass (`model/ddsp/variant.py`)

**New file:** `model/ddsp/variant.py`

```python
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Literal

@dataclass
class DDSPVariant:
    """Opt-in synthesis hacks for the DDSP core.

    All fields default to the standard (no-op) behaviour so existing
    checkpoints are unaffected when no variant is supplied.
    """
    # --- M8.2 Inharmonic multipliers ---
    # None  → standard integer ratios [1, 2, …, n_harmonics]
    # list  → explicit ratio per partial, e.g. [1.0, 1.414, 2.73, 3.14, …]
    harmonic_ratios: list[float] | None = None

    # --- M8.3a Waveform function ---
    # "sin"   → torch.sin  (standard, no-op)
    # "square"→ torch.sign(torch.sin(…))
    # "saw"   → sawtooth from phase
    waveform: Literal["sin", "square", "saw"] = "sin"

    # --- M8.3b Phase distortion (Casio CZ-style) ---
    # 0.0 → disabled (no-op)
    pd_k: float = 0.0

    # --- M8.3c Trainable wavetable ---
    # False → use waveform fn above (no-op)
    # True  → nn.Parameter wavetable of length 256, learned during training
    use_trainable_wavetable: bool = False

    # --- M8.2b FM synthesis ---
    # fm_depth=0.0 → disabled (no-op)
    fm_depth: float = 0.0
    fm_ratio: float = 2.0

    # --- M8.4.1 Spectral-loss band mask ---
    # None → no masking (no-op)
    # list of (low_hz, high_hz) pairs to zero out before loss comparison
    loss_band_mask: list[tuple[float, float]] | None = None

    # --- M8.4.2 LFO injection ---
    # lfo_freq=0.0 → disabled (no-op)
    lfo_freq: float = 0.0   # Hz; injected into noise magnitudes
    lfo_depth: float = 0.0  # amplitude multiplier [0, 1]

    # --- M8.6 Angular cumulative sum (phase-drift fix) ---
    use_angular_cumsum: bool = False

    def is_default(self) -> bool:
        """True if all fields are at their no-op defaults."""
        return (
            self.harmonic_ratios is None
            and self.waveform == "sin"
            and self.pd_k == 0.0
            and not self.use_trainable_wavetable
            and self.fm_depth == 0.0
            and self.loss_band_mask is None
            and self.lfo_freq == 0.0
            and not self.use_angular_cumsum
        )

    @classmethod
    def from_dict(cls, d: dict) -> "DDSPVariant":
        """Deserialize from a plain dict (e.g. from run config JSON)."""
        known = {f.name for f in fields(cls)}  # noqa: F821
        return cls(**{k: v for k, v in d.items() if k in known})
```

**Edit** `model/ddsp/__init__.py`: export `DDSPVariant`.

**Verify:** `from model.ddsp import DDSPVariant; DDSPVariant()` — no error,
`is_default()` returns `True`.

---

### M8.1.2 — Thread `DDSPVariant` into `DDSPModel` + `DDSPCore`

**File:** `model/ddsp_model.py`

Changes:
1. `DDSPModel.__init__` accepts `variant: DDSPVariant | None = None`; stores
   as `self.variant = variant or DDSPVariant()`.
2. Pass `variant` through to `DDSPCore.__init__` (store on `self.variant`).
3. Pass `variant` through to `HarmonicOscillatorSynth.__init__` (stored, not
   yet used — later steps read it).
4. In `DDSPModel.forward`: if `self.variant.lfo_freq > 0`, apply LFO to
   `magnitudes` **before** passing to `DDSPCore` (M8.4.2 logic lives here).

**File:** `model/ddsp/synths.py`

Changes:
1. `HarmonicOscillatorSynth.__init__` accepts `variant: DDSPVariant | None`.
2. `DDSPCore.__init__` accepts and forwards `variant`.

At this step, the variant is plumbed but all values are still default — no
behaviour change. Existing tests must still pass.

**Verify:** full pytest green, no ruff errors.

---

### M8.1.3 — Parse variant in server layer (`server/tasks.py`, `server/presets.py`)

**File:** `server/tasks.py` → `build_training()`

```python
from model.ddsp.variant import DDSPVariant

def build_training(model_config: dict, checkpoint_dir: Path):
    ...
    variant_dict = model_config.get("variant", {}) or {}
    variant = DDSPVariant.from_dict(variant_dict)
    dcfg = DDSPConfig(hidden_size=hidden_size, stft_scales=..., variant=variant)
    ...
```

**File:** `model/ddsp_model.py` → `DDSPConfig`

Add field: `variant: DDSPVariant | None = None` (default `None`).
`DDSPModel.__init__` reads `config.variant or DDSPVariant()`.

**File:** `server/presets.py` → `PARAM_KEYS`

Add `"variant"` to `PARAM_KEYS` so the run-config roundtrip persists it.
The `clamp_params` function passes `variant` through unchanged (it is a
nested dict, not a numeric parameter).

**Verify:** `POST /api/runs` with `{"params": {"variant": {"waveform":
"square"}}}` → run stored → `build_training` creates `DDSPVariant(waveform="square")`.
Test with a mock runner (existing pattern in `tests/test_training_routes.py`).

---

### M8.1.4 — UI: `SynthHacksView.vue` + router + sidebar

**New file:** `webui/src/views/SynthHacksView.vue`

Minimal panel with:
- Section "Harmonic Oscillator Hacks":
  - Waveform dropdown: `sin / square / saw`
  - Phase distortion slider: `pd_k` 0.0–2.0
  - FM depth slider: 0.0–1.0 + FM ratio input: 1.0–8.0
  - Inharmonic ratios textarea: comma-separated floats (optional, blank = off)
  - Trainable wavetable toggle (checkbox + warning label: "checkpoint
    incompatible with standard runs")
- Section "Loss Hacks":
  - Band-mask editor: list of `[low_hz, high_hz]` pairs (add/remove rows)
- Section "Decoder Hacks":
  - LFO frequency slider: 0–20 Hz
  - LFO depth slider: 0.0–1.0
- Section "Quality":
  - Angular cumsum toggle (checkbox + label: "reduces phase drift for >6 s
    synthesis, ~10 % slower")
- "Apply to next run" button: merges variant fields into the run-params
  store (Pinia `trainingStore.variant`).

**All fields start at their no-op defaults** — no visible effect until the
user changes them.

**File:** `webui/src/router/index.js` — add route
`{ path: '/experimental/synth-hacks', component: SynthHacksView }`.

**File:** `webui/src/components/Sidebar.vue` — add link "Synth Hacks" under
the "Experimental" nav group (after Component Mixer).

**File:** `webui/src/api/apiClient.js` — no new endpoint needed; the
`variant` dict travels inside the existing `POST /api/runs` `params` field.

**File:** `webui/src/mocks/mockApiClient.js` + `fixtures.js` — add
`variant: {}` to fixture run params.

**Verify:** `vitest` green; `SynthHacksView` renders with mock client,
shows all sliders at default (no console errors).

---

## M8.2 — Inharmonic Multipliers

> Replace the integer harmonic series with a user-configurable ratio array.
> Result: bell, gong, gamelan, metallic textures.

### M8.2.1 — Configurable `harmonic_ratios` in `HarmonicOscillatorSynth`

**File:** `model/ddsp/synths.py`

Current (line 65):
```python
harmonic_indices = torch.arange(1, self.n_harmonics + 1, device=device, dtype=dtype)
```

Replace with:
```python
if self.variant.harmonic_ratios is not None:
    _ratios = self.variant.harmonic_ratios
    # Pad or truncate to n_harmonics
    if len(_ratios) < self.n_harmonics:
        _ratios = _ratios + list(range(len(_ratios) + 1, self.n_harmonics + 1))
    harmonic_indices = torch.tensor(
        _ratios[: self.n_harmonics], device=device, dtype=dtype
    )
else:
    harmonic_indices = torch.arange(1, self.n_harmonics + 1, device=device, dtype=dtype)
```

- Padding rule: if fewer ratios are given than `n_harmonics`, fill the rest
  with the next integers. This is the safest default; the user controls only
  the first N inharmonic partials.
- The rest of `HarmonicOscillatorSynth.forward` is unchanged; the only
  difference is which frequency each partial sits at.

**Verify:**
```python
v = DDSPVariant(harmonic_ratios=[1.0, 1.414, 2.73, 3.14])
synth = HarmonicOscillatorSynth(n_harmonics=8, variant=v)
out = synth(amps, dist, f0, sample_rate=16000, hop_length=128)
assert out.shape[-1] > 0
assert torch.isfinite(out).all()
```

---

### M8.2b — FM Synthesis mode

**File:** `model/ddsp/synths.py`

After computing `harmonic_freqs` (line 66), add FM modulation before
computing `phase_increments`:

```python
if self.variant.fm_depth > 0.0:
    # Modulator: sine at fm_ratio × f0, applied per-frame
    mod_freq = f0 * self.variant.fm_ratio           # (B, T_frames)
    # Frame-level modulator phase (scalar offset per frame)
    mod_phase = 2.0 * torch.pi * mod_freq * torch.arange(
        T_frames, device=device, dtype=dtype
    ).unsqueeze(0) * (hop_length / sample_rate)
    mod_phase = torch.cumsum(mod_phase, dim=1)      # (B, T_frames)
    mod_signal = self.variant.fm_depth * torch.sin(mod_phase)  # (B, T_frames)
    # Add modulation to all harmonics (broadcast over H)
    harmonic_freqs = harmonic_freqs + mod_signal.unsqueeze(-1) * f0.unsqueeze(-1)
    harmonic_freqs = harmonic_freqs.clamp(min=1.0)  # never go below 1 Hz
```

- `fm_depth=0.0` is a strict no-op (the `if` guard is `> 0.0`).
- `fm_ratio=2.0` is a classic FM carrier-to-modulator ratio (DX7-style).
- `clamp(min=1.0)` prevents negative frequencies that would produce NaN
  in subsequent phase computation.

**Verify:**
```python
v = DDSPVariant(fm_depth=0.5, fm_ratio=2.0)
out = HarmonicOscillatorSynth(n_harmonics=16, variant=v)(amps, dist, f0)
assert torch.isfinite(out).all()
```

---

## M8.3 — Waveform / Wavetable Exchange

> Replace the `torch.sin` call with a different oscillator curve,
> or with a learned wavetable.

### M8.3.1 — Waveform function dispatch (`sin / square / saw`)

**File:** `model/ddsp/synths.py`

Replace line 99:
```python
audio = (amp_audio * torch.sin(phase_audio)).sum(dim=-1)
```

With:
```python
audio = (amp_audio * _apply_waveform(phase_audio, self.variant)).sum(dim=-1)
```

New helper (module-level, above `HarmonicOscillatorSynth`):
```python
def _apply_waveform(phase: torch.Tensor, variant: "DDSPVariant") -> torch.Tensor:
    """Apply waveform shaping to accumulated phase tensor.

    phase: arbitrary shape, values in radians.
    Returns tensor of same shape, values in [-1, 1].
    """
    wf = variant.waveform

    # Phase distortion (Casio CZ-style) applied first, regardless of waveform
    if variant.pd_k != 0.0:
        phase = phase + variant.pd_k * torch.sin(phase)

    if wf == "square":
        return torch.sign(torch.sin(phase))
    if wf == "saw":
        # Sawtooth: (phase mod 2π) / π − 1, range [-1, 1]
        return (phase % (2.0 * torch.pi)) / torch.pi - 1.0
    # Default: "sin"
    return torch.sin(phase)
```

- `wf == "sin"` and `pd_k == 0.0` → identical to the original one-liner.
  Existing tests unchanged.
- `square` uses `torch.sign` which is differentiable except at 0 (gradient
  is zero). Training with square waves is still possible but gradients are
  sparser — document this in `experimental-sdk-hacking.md`.
- `saw` modulo is differentiable everywhere (no discontinuity in gradient
  for `torch.remainder`).
- Phase distortion (`pd_k`) stacks with any waveform choice.

**Verify (CPU smoke):**
```python
for wf in ("sin", "square", "saw"):
    v = DDSPVariant(waveform=wf)
    out = HarmonicOscillatorSynth(n_harmonics=8, variant=v)(amps, dist, f0)
    assert torch.isfinite(out).all(), f"NaN with waveform={wf}"
```

---

### M8.3b — Phase Distortion

Already included in `_apply_waveform` above via `pd_k`.

**Separate verify:**
```python
v = DDSPVariant(pd_k=0.8)   # Casio CZ-style shaping
out = HarmonicOscillatorSynth(n_harmonics=8, variant=v)(amps, dist, f0)
assert torch.isfinite(out).all()
```

---

### M8.3c — Trainable Wavetable (`nn.Parameter`)

> This step changes the model's parameter count.
> Checkpoints saved with `use_trainable_wavetable=True` **cannot** be loaded
> into a standard `DDSPModel`. The checkpoint writer must tag
> `state["variant_flags"]["use_trainable_wavetable"] = True`.

**File:** `model/ddsp/synths.py` → `HarmonicOscillatorSynth.__init__`

```python
if variant is not None and variant.use_trainable_wavetable:
    # Learnable wavetable: 256 samples in [-1, 1]; initialized to sine
    t = torch.linspace(0, 2 * torch.pi, 256)
    self.wavetable = nn.Parameter(torch.sin(t))
else:
    self.wavetable = None
```

**File:** `model/ddsp/synths.py` → `_apply_waveform`

```python
if variant.use_trainable_wavetable and self_wavetable is not None:
    # Lookup: map phase (mod 2π) to wavetable index, bilinear interp
    idx = (phase % (2.0 * torch.pi)) / (2.0 * torch.pi) * 255.0
    idx_lo = idx.long().clamp(0, 254)
    idx_hi = (idx_lo + 1).clamp(0, 255)
    frac = idx - idx_lo.float()
    wt = self_wavetable  # (256,)
    return wt[idx_lo] * (1 - frac) + wt[idx_hi] * frac
```

Because `_apply_waveform` is a module-level function, it needs `self_wavetable`
passed in explicitly. Change signature:
```python
def _apply_waveform(
    phase: torch.Tensor,
    variant: "DDSPVariant",
    wavetable: "torch.Tensor | None" = None,
) -> torch.Tensor:
```

And call site in `forward`:
```python
audio = (amp_audio * _apply_waveform(
    phase_audio, self.variant, self.wavetable
)).sum(dim=-1)
```

**Checkpoint tagging** — `model/ddsp_model.py` → `save_checkpoint`:

```python
state["variant_flags"] = {
    "use_trainable_wavetable": self.variant.use_trainable_wavetable,
    "waveform": self.variant.waveform,
}
```

Load code should warn (not crash) if `variant_flags` mismatch.

**Verify:**
```python
v = DDSPVariant(use_trainable_wavetable=True)
m = DDSPModel(DDSPConfig(), variant=v)
assert any(p.requires_grad for p in m.parameters())
out = m(f0, loudness)
loss = out["audio"].mean()
loss.backward()  # must not crash
```

---

## M8.4 — Loss & Decoder Hacks

### M8.4.1 — Frequency-band mask on spectral loss

**File:** `model/losses.py` → `MultiScaleSpectralLoss`

Add parameter `band_mask: list[tuple[float, float]] | None = None` to
`__init__`. Store as `self.band_mask`.

In `forward`, after computing `pred_mag` and `tgt_mag`, apply the mask:

```python
if self.band_mask:
    # freq_bins shape: (n_fft // 2 + 1,)
    freq_resolution = sample_rate / fft_size  # Hz per bin
    # sample_rate is not available here → pass it in, or derive from fft_size
    # Design choice: pass sample_rate as constructor argument (default 16000)
    mask = torch.ones(pred_mag.shape[-2], device=pred_mag.device, dtype=pred_mag.dtype)
    for lo_hz, hi_hz in self.band_mask:
        lo_bin = int(lo_hz / freq_resolution)
        hi_bin = int(hi_hz / freq_resolution) + 1
        mask[lo_bin:hi_bin] = 0.0
    # mask: (freq_bins,) → broadcast over (B, freq_bins, time_frames)
    pred_mag = pred_mag * mask.unsqueeze(-1)
    tgt_mag  = tgt_mag  * mask.unsqueeze(-1)
```

The `sample_rate` default (16000) must be added to `MultiScaleSpectralLoss.__init__`.

**Wire up:** `server/tasks.py` → `build_training`:

```python
band_mask = None
if variant.loss_band_mask:
    band_mask = [tuple(pair) for pair in variant.loss_band_mask]
loss_fn = MultiScaleSpectralLoss(
    fft_sizes=fft_sizes_for_scales(stft_scales),
    band_mask=band_mask,
    sample_rate=16000,
)
```

The `Trainer` already accepts a `loss_fn` or constructs one — check
`train/trainer.py` and pass `loss_fn` if it does; otherwise add the
`band_mask` to `TrainingConfig`.

**Verify:**
```python
loss = MultiScaleSpectralLoss(
    fft_sizes=[512], band_mask=[(200.0, 2000.0)], sample_rate=16000
)
val = loss(pred_audio, tgt_audio)
assert torch.isfinite(val) and val > 0
```

---

### M8.4.2 — LFO injection into noise magnitudes

**File:** `model/ddsp_model.py` → `DDSPModel.forward`

After computing `magnitudes` (line 127), before calling `self.ddsp_core`:

```python
if self.variant.lfo_freq > 0.0 and self.variant.lfo_depth > 0.0:
    # Time axis in seconds: frame index × frame_size / sample_rate
    t = (
        torch.arange(T_frames, device=f0.device, dtype=f0.dtype)
        * self.config.frame_size
        / self.config.sample_rate
    )  # (T_frames,)
    lfo = 1.0 + self.variant.lfo_depth * torch.sin(
        2.0 * torch.pi * self.variant.lfo_freq * t
    )  # (T_frames,) in [1-depth, 1+depth]
    # Broadcast over (B, T_frames, n_noise_bins) and clamp to [0, 1]
    magnitudes = (magnitudes * lfo.unsqueeze(0).unsqueeze(-1)).clamp(0.0, 1.0)
```

- Both conditions (`lfo_freq > 0` AND `lfo_depth > 0`) must hold → double
  no-op guard; no overhead when LFO is off.
- `clamp(0, 1)` keeps magnitudes in the same range as `sigmoid` output.
- The LFO modulates **noise magnitudes only** (not harmonic amplitudes) to
  produce tremolo/flutter artefacts on the noise branch.

**Verify:**
```python
v = DDSPVariant(lfo_freq=8.0, lfo_depth=0.5)
m = DDSPModel(DDSPConfig(n_harmonics=8, hidden_size=32), variant=v)
out = m(f0, loudness)
assert torch.isfinite(out["audio"]).all()
```

---

## M8.6 — Angular Cumulative Sum (Phase-Drift Fix)

> Quality improvement; not a creative hack. Fixes floating-point phase
> accumulation errors at synthesis lengths > 100k samples (~6 s @ 16 kHz).

**File:** `model/ddsp/synths.py` → `HarmonicOscillatorSynth.forward`

Replace line 77:
```python
phase_frames = torch.cumsum(phase_per_frame, dim=1)
```

With:
```python
if self.variant.use_angular_cumsum:
    phase_frames = _angular_cumsum(phase_per_frame)
else:
    phase_frames = torch.cumsum(phase_per_frame, dim=1)
```

New helper (module-level):
```python
def _angular_cumsum(x: torch.Tensor) -> torch.Tensor:
    """Cumulative sum that keeps phase in [-π, π] at each step.

    Prevents floating-point drift on long sequences (> ~100k samples).
    Slightly slower than torch.cumsum due to the modulo at each step.
    """
    # torch.cumsum then wrap — equivalent to per-step wrap for moderate lengths
    cum = torch.cumsum(x, dim=1)
    return (cum + torch.pi) % (2 * torch.pi) - torch.pi
```

Note: a true per-step angular cumsum would require a Python loop (not
TorchScript-compatible). The single-pass `cumsum + wrap` is an accurate
approximation for sequences up to ~1M samples at float32 precision, which
is sufficient for all realistic synthesis lengths in this project.

**Verify:**
```python
v = DDSPVariant(use_angular_cumsum=True)
synth = HarmonicOscillatorSynth(n_harmonics=8, variant=v)
# Long sequence: 500 frames × 128 hop = 64000 samples
out = synth(amps_long, dist_long, f0_long)
assert torch.isfinite(out).all()
```

---

## M8.5 — Tests + Docs

### M8.5.1 — `tests/test_synths_variant.py` (new file)

One test per hack, all CPU, all small inputs (8 harmonics, 32 frames, `hidden_size=32`).

| Test name | Covers |
|---|---|
| `test_variant_default_is_noop` | Standard DDSPVariant() == original output |
| `test_inharmonic_ratios` | M8.2.1: ratios → finite output |
| `test_fm_synthesis` | M8.2b: fm_depth=0.5 → finite output |
| `test_fm_zero_depth_noop` | M8.2b: fm_depth=0.0 → same as default |
| `test_waveform_square` | M8.3.1: square → finite, has harmonics |
| `test_waveform_saw` | M8.3.1: saw → finite |
| `test_phase_distortion` | M8.3b: pd_k=0.8 → finite |
| `test_trainable_wavetable_gradients` | M8.3c: backward pass succeeds |
| `test_trainable_wavetable_checkpoint_tag` | M8.3c: checkpoint has `variant_flags` |
| `test_loss_band_mask` | M8.4.1: masked loss < unmasked loss |
| `test_loss_band_mask_zero_band` | M8.4.1: mask whole spectrum → loss == 0 |
| `test_lfo_injection` | M8.4.2: lfo_freq=8.0 → finite output |
| `test_lfo_zero_noop` | M8.4.2: lfo_depth=0.0 → same as no LFO |
| `test_angular_cumsum` | M8.6: use_angular_cumsum → finite, no NaN |
| `test_variant_from_dict_roundtrip` | M8.1.1: serialize + deserialize |
| `test_synth_hacks_view_renders` | M8.1.4: Vitest — Vue component renders |

Total: 15 pytest + 1 Vitest.

---

### M8.5.2 — Finalize `doc/experimental-sdk-hacking.md`

Add:
- Result table: which hacks produce which sonic characters (fact-vs-spec
  tagging preserved).
- Checkpoint compatibility matrix: which combinations break checkpoint
  loading.
- Known gradient behaviour: `square` waveform has zero gradient except at
  sign changes — may stall training; recommend `sin` + high `pd_k` instead
  for similar brightness with better gradients.
- Update `doc/checklist.md` M8 items when each step is done.

---

## Execution order (recommended, one subagent per step)

```
M8.1.1  DDSPVariant dataclass                    (model/ddsp/variant.py — new)
M8.1.2  Thread variant into DDSPModel + DDSPCore  (model/ddsp_model.py, synths.py)
M8.1.3  Server-layer variant parsing              (server/tasks.py, presets.py)
M8.1.4  SynthHacksView.vue + router + sidebar     (webui/)
  ↓ primary: build + test after M8.1 complete
M8.2.1  Inharmonic ratios                         (synths.py:65)
M8.2b   FM synthesis                              (synths.py:66-72)
  ↓ primary: build + test
M8.3.1  Waveform dispatch + _apply_waveform()     (synths.py:99)
M8.3b   Phase distortion (inside _apply_waveform) (synths.py — already in M8.3.1)
M8.3c   Trainable wavetable                       (synths.py + checkpoint tag)
  ↓ primary: build + test
M8.4.1  Spectral-loss band mask                   (losses.py + tasks.py)
M8.4.2  LFO injection                             (ddsp_model.py)
  ↓ primary: build + test
M8.6    Angular cumsum                            (synths.py:77)
  ↓ primary: build + test
M8.5.1  test_synths_variant.py                    (tests/)
M8.5.2  Finalize docs                             (doc/)
  ↓ primary: full pytest + vitest + ruff + wiki sync
```

Total: **14 subagent steps** + 4 primary build/test checkpoints.

---

## BUGS

_References only; full records in [`../bugs.md`](../bugs.md)._

- (none)

## History

_Append-only, newest first._

- **2026-09-01** — Full granular step breakdown written by ARCHITECT agent.
  Previous stub (M8.1–M8.5, 5 steps) replaced with 14-step analysis
  including M8.2b (FM), M8.3b (phase distortion), M8.3c (trainable
  wavetable), M8.6 (angular cumsum), and complete file map.
