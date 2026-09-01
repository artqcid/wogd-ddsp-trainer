---
type: implementation-plan
status: draft
milestone: M9 - Alternative synthesizer engines
generated:
  by: ARCHITECT-agent
  at: 2026-09-01
stale_after: 2027-06-01
---

# Implementation Plan — M9 Alternative Synthesizer Engines

_Granular plan for milestone M9. Meta plan: [`../plan.md`](../plan.md);
status: [`../checklist.md`](../checklist.md).
Prerequisite: M8 complete (DDSPVariant infrastructure in place)._

## Constraints & principles

- M8's `DDSPVariant` and `DDSPCore` infrastructure is the foundation.
  M9 extends `DDSPVariant.engine` to select among three synth backends.
- **Engine-specific checkpoints.** A checkpoint saved with `engine="sinusoidal"`
  cannot be loaded into a model built with `engine="harmonic"`. The checkpoint
  writer must tag `state["engine"]`.
- **VRAM budget: 6 GB (RTX 3060).** `CombSubSynth` and `SinusoidalSynth`
  are comparable in size to `HarmonicOscillatorSynth`; no VRAM regression
  expected.
- **One subagent task per step.** Primary agent builds and tests after each
  group.

---

## File map

```
model/ddsp/variant.py          MOD  — add engine field (M9.1)
model/ddsp/sinusoidal.py       NEW  — SinusoidalSynth (M9.2)
model/ddsp/combsub.py          NEW  — CombSubSynth (M9.3)
model/ddsp/noise_colored.py    NEW  — pink/brown noise source (M9.4)
model/ddsp/synths.py           MOD  — granular noise option (M9.5)
model/ddsp/__init__.py         MOD  — export new synths (M9.2–M9.5)
model/ddsp_model.py            MOD  — engine-dispatch in DDSPModel.__init__ (M9.6)
server/tasks.py                MOD  — pass engine field to DDSPConfig (M9.6)
webui/src/views/SynthHacksView.vue  MOD  — engine selector dropdown (M9.7)
webui/src/mocks/fixtures.js    MOD  — engine fixture defaults (M9.7)
tests/test_synths_engines.py   NEW  — smoke tests per engine (M9.8)
doc/experimental-sdk-hacking.md    MOD  — engine section (M9.9)
```

---

## M9.1 — Extend `DDSPVariant` with `engine` field

**File:** `model/ddsp/variant.py`

Add field to `DDSPVariant`:
```python
engine: Literal["harmonic", "sinusoidal", "combsub"] = "harmonic"
```

- `"harmonic"` → existing `HarmonicOscillatorSynth` (standard, no-op default).
- `"sinusoidal"` → new `SinusoidalSynth` with freely learned frequencies.
- `"combsub"` → new `CombSubSynth` (comb-filter subtractive, DDSP-SVC style).

`is_default()` must be updated to include `engine == "harmonic"`.

**Checkpoint tag:** `state["engine"] = variant.engine` must be written by
`DDSPModel.save_checkpoint` (add in M9.6).

---

## M9.2 — `SinusoidalSynth` (`model/ddsp/sinusoidal.py` — new)

**Concept:** Unlike `HarmonicOscillatorSynth` which constrains partial
frequencies to integer multiples of f0, `SinusoidalSynth` receives
**freely learned frequencies** per partial from a dedicated decoder head.
This enables inharmonic instruments (bells, xylophones, metal plates) where
the Harmonic model would require very large inharmonic-ratio arrays.

**Decoder head change required (see M9.6):** when `engine="sinusoidal"`,
the model needs an additional output head:
```
sinusoidal_freqs_out: nn.Linear(hidden_size, n_partials)  → sigmoid → [0, nyquist]
```
The `harmonic_distribution_out` head is repurposed as `sinusoidal_amps_out`.

**Module signature:**
```python
class SinusoidalSynth(nn.Module):
    def forward(
        self,
        amplitudes: Tensor,      # (B, T_frames, N_partials)
        frequencies: Tensor,     # (B, T_frames, N_partials) in Hz
        sample_rate: int,
        hop_length: int,
    ) -> Tensor:                 # (B, T_audio)
```

**Implementation:** identical phase-accumulation approach as
`HarmonicOscillatorSynth` but `harmonic_freqs = frequencies` (given directly,
not computed from f0 × ratio). The `_apply_waveform` helper from M8.3.1 can
be reused for waveform shaping.

**Nyquist normalization:** frequencies above `sample_rate / 2` must be
zeroed (amplitude set to 0) to avoid aliasing. Add a mask:
```python
nyquist_mask = (frequencies < sample_rate / 2).float()
amplitudes = amplitudes * nyquist_mask
```

**Verify (CPU smoke):**
```python
freqs = torch.rand(1, 32, 16) * 4000 + 100  # 100–4100 Hz
amps = torch.rand(1, 32, 16)
out = SinusoidalSynth()(amps, freqs, 16000, 128)
assert out.shape == (1, 31 * 128 + 1)
assert torch.isfinite(out).all()
```

---

## M9.3 — `CombSubSynth` (`model/ddsp/combsub.py` — new)

**Concept:** DDSP-SVC's "combsub" topology: a comb-filter generates a
harmonic excitation signal (voiced) or filtered noise (unvoiced), then a
time-varying subtractive filter shapes the spectrum. Particularly good for
vocal formants and speech-like sounds.

**Reference:** `yxlllc/DDSP-SVC` `combsub.py` (MIT). Use as a spec
reference; implement in our PyTorch style (no fork).

**Signal flow:**
```
f0 + voiced_flag
    ↓
CombFilter (voiced) OR Noise (unvoiced)  → excitation (B, T_audio)
    ↓
Time-varying spectral envelope filter    → shaped (B, T_audio)
    ↓
(optional) SimpleReverb
    ↓
Audio output
```

**Comb filter:** generate a pulse train at f0 rate by computing a
rectangular window positioned at integer multiples of `1/f0` in time.
Implemented via phase modulo:
```python
phase_inc = f0 / sample_rate  # (B, T_frames)
phase = torch.cumsum(phase_inc, dim=1) % 1.0
pulse = (phase < pulse_width).float() * 2 - 1  # bipolar pulse
```
Upsampled to audio rate via `F.interpolate`.

**Spectral envelope filter:** the decoder outputs `n_fir_taps` magnitude
bins. Apply as a frequency-domain filter via short FFT convolution
(overlap-add), or simplify to a per-frame gain applied to fixed-bandwidth
bands (similar to current `FilteredNoiseSynth`).

**Voiced/unvoiced flag:** take `f0_confidence` from features; threshold at
0.5 — above = voiced (comb), below = noise excitation. The flag can also
be a learned output from the decoder.

**Decoder head changes (M9.6):** when `engine="combsub"`, the decoder
needs:
- `comb_magnitudes_out: nn.Linear(hidden_size, n_fir_taps)` — spectral shape
- `voiced_out: nn.Linear(hidden_size, 1)` → sigmoid → voiced probability

**Module signature:**
```python
class CombSubSynth(nn.Module):
    def __init__(self, n_fir_taps: int = 64, sample_rate: int = 16000,
                 hop_length: int = 128, pulse_width: float = 0.1) -> None: ...

    def forward(
        self,
        comb_magnitudes: Tensor,  # (B, T_frames, n_fir_taps)
        f0: Tensor,               # (B, T_frames) Hz
        voiced: Tensor,           # (B, T_frames) in [0, 1]
        n_samples: int,
    ) -> Tensor:                  # (B, T_audio)
```

**Verify (CPU smoke):**
```python
synth = CombSubSynth(n_fir_taps=32)
mags = torch.rand(1, 32, 32)
f0 = torch.full((1, 32), 220.0)
voiced = torch.ones(1, 32)
out = synth(mags, f0, voiced, n_samples=31 * 128 + 1)
assert torch.isfinite(out).all()
```

---

## M9.4 — Colored noise source (`model/ddsp/noise_colored.py` — new)

**Concept:** replace white Gaussian noise in `FilteredNoiseSynth` with
pink (1/f) or brown (1/f²) noise for warmer or darker textures.

**Implementation:** shape white noise in the frequency domain before
returning to time domain.

```python
def _pink_noise(n: int, device, dtype) -> Tensor:
    """Generate pink noise (1/f spectrum) of length n."""
    white = torch.randn(n, device=device, dtype=dtype)
    fft = torch.fft.rfft(white)
    freqs = torch.fft.rfftfreq(n, device=device, dtype=dtype)
    freqs[0] = 1.0  # avoid division by zero at DC
    pink_filter = 1.0 / freqs.sqrt()
    fft = fft * pink_filter
    return torch.fft.irfft(fft, n=n)


def _brown_noise(n: int, device, dtype) -> Tensor:
    """Generate brown noise (1/f² spectrum) of length n."""
    white = torch.randn(n, device=device, dtype=dtype)
    fft = torch.fft.rfft(white)
    freqs = torch.fft.rfftfreq(n, device=device, dtype=dtype)
    freqs[0] = 1.0
    brown_filter = 1.0 / freqs
    fft = fft * brown_filter
    return torch.fft.irfft(fft, n=n)
```

**Extend `DDSPVariant`:**
```python
noise_color: Literal["white", "pink", "brown"] = "white"
```

**Extend `FilteredNoiseSynth.forward`:** branch on `variant.noise_color`
to select which buffer to use. Pre-compute and register all three as
`register_buffer` at init so the device/dtype transfer is handled by
PyTorch's state_dict machinery.

**Verify:**
```python
for color in ("white", "pink", "brown"):
    v = DDSPVariant(noise_color=color)
    synth = FilteredNoiseSynth(variant=v)
    out = synth(mags, n_samples=1024)
    assert torch.isfinite(out).all()
```

---

## M9.5 — Granular noise option (`model/ddsp/synths.py`)

**Concept:** instead of reading the deterministic `noise_buffer` at offset 0,
introduce a per-frame grain offset — a small random jitter on the buffer
read position to create granular texture.

**Extend `DDSPVariant`:**
```python
noise_grain_jitter: float = 0.0  # max jitter in frames; 0.0 = off
```

**Implementation in `FilteredNoiseSynth.forward`:** when
`variant.noise_grain_jitter > 0`, compute a random integer offset per batch
item in `[0, jitter_samples)` and slice the buffer accordingly:
```python
jitter_samples = int(variant.noise_grain_jitter * hop_length)
if jitter_samples > 0:
    offset = torch.randint(0, jitter_samples, (B,))
    # slice per batch item — use a loop (B is always 1 in training)
    noise_slices = [self.noise_buffer[offset[i] : offset[i] + n_samples] for i in range(B)]
    noise = torch.stack(noise_slices, dim=0).to(device=device, dtype=dtype)
else:
    noise = self.noise_buffer[:n_samples].unsqueeze(0).expand(B, -1)
    noise = noise.to(device=device, dtype=dtype)
```

Note: the loop is acceptable since `B=1` in all training scenarios.

**Verify:**
```python
v = DDSPVariant(noise_grain_jitter=2.0)
synth = FilteredNoiseSynth(variant=v)
out1 = synth(mags, n_samples=1024)
out2 = synth(mags, n_samples=1024)
assert not torch.allclose(out1, out2)  # jitter produces different outputs
```

---

## M9.6 — Engine dispatch in `DDSPModel` + `DDSPCore`

**File:** `model/ddsp_model.py`

When `variant.engine != "harmonic"`, `DDSPModel.__init__` must:

1. **Instantiate the correct synth** in place of `HarmonicOscillatorSynth`
   inside `DDSPCore` (or bypass `DDSPCore` entirely and build the pipeline
   manually for cleaner separation).

2. **Add the correct output heads:**

   | engine | heads added | heads removed |
   |---|---|---|
   | `"harmonic"` | (standard: amplitude, distribution, noise) | — |
   | `"sinusoidal"` | `sinusoidal_freqs_out` (Linear → sigmoid → Hz) | distribution_out repurposed as amps |
   | `"combsub"` | `comb_magnitudes_out`, `voiced_out` | amplitude_out, distribution_out |

3. **Tag checkpoint:**
   ```python
   state["engine"] = self.variant.engine
   ```

4. **Load-time check** (`load_checkpoint`): if `state.get("engine", "harmonic")
   != self.variant.engine` → raise `ValueError` with clear message.

**`DDSPConfig` field:**
```python
engine: Literal["harmonic", "sinusoidal", "combsub"] = "harmonic"
```
(Derived from `variant.engine` in `build_training`.)

**`server/tasks.py` → `build_training`:**
```python
dcfg = DDSPConfig(
    hidden_size=hidden_size,
    stft_scales=...,
    engine=variant.engine,
)
```

**Verify:** instantiate each engine variant, run a forward pass, run
`.backward()` — all finite, no crashes.

---

## M9.7 — UI: Engine selector in `SynthHacksView.vue`

**File:** `webui/src/views/SynthHacksView.vue` (already created in M8.1.4)

Add at the top of the "Harmonic Oscillator Hacks" section:

```html
<label>Synthesis Engine</label>
<select v-model="variant.engine">
  <option value="harmonic">Harmonic (standard)</option>
  <option value="sinusoidal">Sinusoidal (free partials)</option>
  <option value="combsub">CombSub (vocal formants)</option>
</select>
<p class="warning" v-if="variant.engine !== 'harmonic'">
  ⚠ Engine-specific checkpoint — not compatible with standard runs.
</p>
```

Add `noise_color` dropdown and `noise_grain_jitter` slider in the "Noise
Branch" subsection.

**Fixtures + mocks:** add `engine: "harmonic"`, `noise_color: "white"`,
`noise_grain_jitter: 0` to default fixture variant dict.

**Verify:** `vitest` green; engine warning shows when non-harmonic selected.

---

## M9.8 — Tests (`tests/test_synths_engines.py` — new)

| Test name | Covers |
|---|---|
| `test_sinusoidal_synth_forward` | M9.2: finite output, correct shape |
| `test_sinusoidal_nyquist_mask` | M9.2: partials above nyquist zeroed |
| `test_combsub_voiced` | M9.3: voiced mode, finite |
| `test_combsub_unvoiced` | M9.3: unvoiced (noise) mode, finite |
| `test_noise_pink` | M9.4: pink noise, finite |
| `test_noise_brown` | M9.4: brown noise, finite |
| `test_noise_grain_jitter_varies` | M9.5: two calls differ when jitter > 0 |
| `test_engine_harmonic_default` | M9.6: DDSPModel with harmonic == original |
| `test_engine_sinusoidal_forward` | M9.6: DDSPModel with sinusoidal, backward ok |
| `test_engine_combsub_forward` | M9.6: DDSPModel with combsub, backward ok |
| `test_engine_checkpoint_tag` | M9.6: saved state has `engine` key |
| `test_engine_mismatch_raises` | M9.6: loading combsub ckpt into harmonic model raises |

Total: 12 pytest + 1 vitest (engine-selector renders).

---

## M9.9 — Docs

Update `doc/experimental-sdk-hacking.md`:
- Add "Alternative Engines" section with signal-flow diagrams.
- Checkpoint compatibility table extended with engine column.

Update `doc/checklist.md` M9 items as steps complete.

---

## Execution order

```
M9.1   Extend DDSPVariant.engine + noise_color + noise_grain_jitter
M9.2   SinusoidalSynth (model/ddsp/sinusoidal.py)
M9.3   CombSubSynth    (model/ddsp/combsub.py)
M9.4   Colored noise   (model/ddsp/noise_colored.py)
M9.5   Granular noise  (model/ddsp/synths.py)
  ↓ primary: build + test
M9.6   Engine dispatch in DDSPModel + checkpoint tag
  ↓ primary: build + test
M9.7   UI: engine selector + noise controls
  ↓ primary: vitest
M9.8   tests/test_synths_engines.py
M9.9   Docs
  ↓ primary: full pytest + vitest + ruff + wiki sync
```

Total: **9 subagent steps** + 3 primary checkpoints.

---

## BUGS

_References only; full records in [`../bugs.md`](../bugs.md)._

- (none)

## History

_Append-only, newest first._

- **2026-09-01** — M9.1–M9.9 implemented by BUILD agent.
  - M9.1: engine/noise_color/noise_grain_jitter fields on DDSPVariant
  - M9.2: SinusoidalSynth (model/ddsp/sinusoidal.py)
  - M9.3: CombSubSynth (model/ddsp/combsub.py)
  - M9.4: _pink_noise/_brown_noise (model/ddsp/noise_colored.py)
  - M9.5: colored noise + granular jitter in FilteredNoiseSynth
  - M9.6: engine dispatch in DDSPCore + DDSPModel __init__/forward/checkpoint
  - M9.7: SynthHacksView.vue with engine/noise/color/jitter controls
  - M9.8: 12 pytest tests (test_synths_engines.py)
  - M9.9: docs + checklist update
  - Also: M8.1.1 (DDSPVariant dataclass), M8.1.2 (plumb into synths+model), M8.1.4 (UI shell) completed.
- **2026-09-01** — Initial granular step breakdown written by ARCHITECT agent.
