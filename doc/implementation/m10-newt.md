---
type: implementation-plan
status: draft
milestone: M10 - Neural Waveshaping Unit (NEWT)
generated:
  by: ARCHITECT-agent
  at: 2026-09-01
stale_after: 2027-06-01
---

# Implementation Plan — M10 Neural Waveshaping Unit (NEWT)

_Granular plan for milestone M10. Meta plan: [`../plan.md`](../plan.md);
status: [`../checklist.md`](../checklist.md).
Prerequisite: M9 complete (engine dispatch infrastructure in place).
Reference paper: Hayes et al. "Neural Waveshaping Synthesis", ISMIR 2021
(arXiv:2107.05050)._

## Concept summary

The **NEWT (Neural Waveshaping Unit)** replaces the additive harmonic
synthesizer with a lightweight MLP that uses periodic (sine) activations to
learn a **nonlinear transfer function** directly in the waveform domain.
A deterministic sawtooth oscillator provides the excitation signal; the NEWT
maps it through the learned nonlinearity, shaped per frame by an affine
transform (gain + bias) from the decoder.

Key advantages over `HarmonicOscillatorSynth`:
- Only ~260k parameters for the NEWT itself (vs. n_harmonics × hidden_size).
- **Real-time capable on CPU** — critical for Neutone export.
- Arbitrary timbre evolutions: the NEWT can produce timbres no harmonic bank
  can express (strongly inharmonic, clipped, distorted, formant-rich).
- Differentiable end-to-end; trains with the same MSS loss.

`engine="newt"` extends the M9 engine dispatch; no changes to the harmonic
or combsub pipelines.

## Constraints

- VRAM: NEWT is *smaller* than `HarmonicOscillatorSynth` — no VRAM regression.
- Checkpoint-incompatible with `engine="harmonic"` checkpoints (different
  parameter set). Tag `state["engine"] = "newt"`.
- Sine activations in the NEWT require **careful weight initialisation**
  (from the NEWT paper: `w ~ U(-1/fan_in, 1/fan_in)` for hidden layers,
  first layer scaled by 30). Failure to initialise correctly → local minima.
- FastNEWT optimisation (grouped convolution) is optional (M10.5); the
  standard MLP is sufficient for offline training.

---

## File map

```
model/ddsp/newt.py             NEW  — NEWTUnit + SawtoothExciter (M10.1, M10.2)
model/ddsp/variant.py          MOD  — engine="newt" added to Literal (M10.3)
model/ddsp/__init__.py         MOD  — export NEWTUnit, SawtoothExciter (M10.1)
model/ddsp_model.py            MOD  — NEWT decoder head + engine dispatch (M10.4)
server/tasks.py                MOD  — pass engine="newt" to DDSPConfig (M10.4)
webui/src/views/SynthHacksView.vue  MOD  — "NEWT" engine option in dropdown (M10.5)
webui/src/mocks/fixtures.js    MOD  — newt fixture default (M10.5)
tests/test_newt.py             NEW  — smoke tests (M10.6)
doc/experimental-sdk-hacking.md    MOD  — NEWT section (M10.7)
```

---

## M10.1 — `SawtoothExciter` (`model/ddsp/newt.py` — new)

**Concept:** a deterministic, parameter-free sawtooth oscillator at f0.
The sawtooth provides a harmonically rich signal (all integer partials at
equal amplitude); the NEWT then shapes its spectrum.

```python
class SawtoothExciter(nn.Module):
    """Deterministic sawtooth oscillator at f0. No learnable parameters."""

    def forward(
        self,
        f0: Tensor,           # (B, T_frames) Hz
        sample_rate: int,
        hop_length: int,
    ) -> Tensor:              # (B, T_audio) in [-1, 1]
        B, T_frames = f0.shape
        device, dtype = f0.device, f0.dtype
        T_audio = (T_frames - 1) * hop_length + 1

        # Phase increments: f0 / sample_rate per sample
        phase_inc = f0 / sample_rate                           # (B, T_frames)
        phase_per_frame = phase_inc * hop_length               # (B, T_frames)
        phase_frames = torch.cumsum(phase_per_frame, dim=1) % 1.0  # (B, T_frames)

        # Upsample to audio rate
        phase_audio = F.interpolate(
            phase_frames.unsqueeze(1), size=T_audio, mode="linear", align_corners=False
        ).squeeze(1)  # (B, T_audio)

        # Sawtooth: 2 * (phase % 1) - 1
        return 2.0 * (phase_audio % 1.0) - 1.0
```

**Verify:**
```python
f0 = torch.full((1, 32), 220.0)
out = SawtoothExciter()(f0, 16000, 128)
assert out.shape == (1, 31 * 128 + 1)
assert out.min() >= -1.0 and out.max() <= 1.0
assert torch.isfinite(out).all()
```

---

## M10.2 — `NEWTUnit` (`model/ddsp/newt.py` — continued)

**Architecture:**
```
excitation (B, T_audio) + gain (B, T_audio) + bias (B, T_audio)
    ↓
x = excitation * gain + bias           ← affine transform per sample
    ↓
NEWT MLP: x → [sin activation layers] → output (B, T_audio)
    ↓
output * output_gain                   ← learned output scale
```

**MLP design (from paper):**
- Input: scalar (1 value per sample)
- Hidden: 4 layers × 32 units, `sin` activation
- Output: 1 scalar, `tanh` activation
- Weight init: first layer `w ~ U(-π, π)` (scale = 30 × 1/fan_in),
  subsequent layers `w ~ U(-1/√fan_in, 1/√fan_in)`

**Per-frame conditioning (affine transform):**
The decoder produces `gain` and `bias` per frame (shape `(B, T_frames)`).
Upsample to audio rate before applying. This is how the NEWT varies its
timbre over time.

```python
class NEWTUnit(nn.Module):
    def __init__(self, n_hidden: int = 32, n_layers: int = 4) -> None:
        super().__init__()
        layers = [nn.Linear(1, n_hidden)]
        for _ in range(n_layers - 1):
            layers.append(nn.Linear(n_hidden, n_hidden))
        layers.append(nn.Linear(n_hidden, 1))
        self.layers = nn.ModuleList(layers)
        self._init_weights()

    def _init_weights(self) -> None:
        # First layer: scale = 30 (from NEWT paper)
        nn.init.uniform_(self.layers[0].weight, -torch.pi, torch.pi)
        for layer in self.layers[1:-1]:
            fan_in = layer.weight.shape[1]
            bound = 1.0 / fan_in ** 0.5
            nn.init.uniform_(layer.weight, -bound, bound)

    def forward(
        self,
        excitation: Tensor,   # (B, T_audio)
        gain: Tensor,         # (B, T_audio) — upsampled from frames
        bias: Tensor,         # (B, T_audio) — upsampled from frames
    ) -> Tensor:              # (B, T_audio)
        x = excitation * gain + bias       # (B, T_audio)
        x = x.unsqueeze(-1)                # (B, T_audio, 1)
        for i, layer in enumerate(self.layers[:-1]):
            x = torch.sin(layer(x))
        x = torch.tanh(self.layers[-1](x))
        return x.squeeze(-1)               # (B, T_audio)
```

**Verify:**
```python
unit = NEWTUnit()
exc  = torch.randn(1, 1024)
gain = torch.ones(1, 1024)
bias = torch.zeros(1, 1024)
out  = unit(exc, gain, bias)
assert out.shape == (1, 1024)
assert torch.isfinite(out).all()
# Backward
loss = out.mean()
loss.backward()
assert all(p.grad is not None for p in unit.parameters())
```

---

## M10.3 — Extend `DDSPVariant.engine`

**File:** `model/ddsp/variant.py`

```python
engine: Literal["harmonic", "sinusoidal", "combsub", "newt"] = "harmonic"
```

Also add NEWT-specific tuning parameters:
```python
newt_n_hidden: int = 32     # MLP hidden units per layer
newt_n_layers: int = 4      # MLP depth
```

---

## M10.4 — Engine dispatch in `DDSPModel` for NEWT

**File:** `model/ddsp_model.py`

When `variant.engine == "newt"`:

1. **Replace harmonic synth with NEWT pipeline:**
   ```python
   self.sawtooth   = SawtoothExciter()
   self.newt       = NEWTUnit(n_hidden=variant.newt_n_hidden,
                               n_layers=variant.newt_n_layers)
   ```

2. **Add NEWT-specific decoder heads** (replace amplitude + distribution):
   ```python
   self.newt_gain_out = nn.Linear(config.hidden_size, 1)   # → sigmoid → gain
   self.newt_bias_out = nn.Linear(config.hidden_size, 1)   # → tanh → bias
   ```

3. **Forward pass for NEWT:**
   ```python
   gain_frames = torch.sigmoid(self.newt_gain_out(hidden)).squeeze(-1)  # (B, T_frames)
   bias_frames = torch.tanh(self.newt_bias_out(hidden)).squeeze(-1)     # (B, T_frames)

   # Upsample to audio rate
   gain_audio = F.interpolate(gain_frames.unsqueeze(1), size=n_samples, mode="linear",
                               align_corners=False).squeeze(1)
   bias_audio = F.interpolate(bias_frames.unsqueeze(1), size=n_samples, mode="linear",
                               align_corners=False).squeeze(1)

   excitation = self.sawtooth(f0, self.config.sample_rate, self.config.frame_size)
   harmonic_audio = self.newt(excitation, gain_audio, bias_audio)
   ```

4. Noise branch + reverb unchanged; mixed as before.

5. **Checkpoint tag:** `state["engine"] = "newt"`.

**`server/tasks.py`:** `build_training` reads `variant.engine` → sets
`dcfg.engine = "newt"`.

**Verify:** full DDSPModel forward + backward, CPU, `hidden_size=32`.

---

## M10.5 — UI: NEWT option in `SynthHacksView.vue`

**File:** `webui/src/views/SynthHacksView.vue`

Add `"NEWT (neural waveshaping)"` to the engine dropdown.
Add NEWT-specific controls (shown only when `engine === "newt"`):
- Hidden units per layer: number input (8–128, default 32)
- MLP depth: number input (2–8, default 4)
- Warning: "NEWT checkpoints are not compatible with harmonic/combsub runs."

**Verify:** vitest green; controls show/hide based on engine selection.

---

## M10.6 — Tests (`tests/test_newt.py` — new)

| Test name | Covers |
|---|---|
| `test_sawtooth_shape` | M10.1: correct output shape |
| `test_sawtooth_range` | M10.1: values in [-1, 1] |
| `test_sawtooth_frequency` | M10.1: zero crossings match f0 (approximate) |
| `test_newt_forward` | M10.2: finite output |
| `test_newt_backward` | M10.2: backward succeeds, all grads non-None |
| `test_newt_init_weights` | M10.2: first layer weights in [-π, π] |
| `test_ddsp_model_newt_forward` | M10.4: full model forward, finite audio |
| `test_ddsp_model_newt_backward` | M10.4: backward, grads ok |
| `test_ddsp_model_newt_checkpoint_tag` | M10.4: state has engine="newt" |
| `test_ddsp_model_newt_mismatch_raises` | M10.4: loading newt ckpt into harmonic raises |
| `test_newt_view_renders` | M10.5: vitest — SynthHacksView with NEWT option |

Total: 10 pytest + 1 vitest.

---

## M10.7 — Docs

Update `doc/experimental-sdk-hacking.md`:
- Add "NEWT" section with architecture diagram, paper citation, and
  weight-init note.
- Checkpoint compatibility table: NEWT column.

---

## Execution order

```
M10.1  SawtoothExciter          (model/ddsp/newt.py)
M10.2  NEWTUnit                 (model/ddsp/newt.py)
  ↓ primary: build + unit test
M10.3  DDSPVariant.engine += "newt" + tuning params
M10.4  Engine dispatch in DDSPModel
  ↓ primary: build + test
M10.5  UI: NEWT engine option
  ↓ primary: vitest
M10.6  tests/test_newt.py
M10.7  Docs
  ↓ primary: full pytest + vitest + ruff + wiki sync
```

Total: **7 subagent steps** + 3 primary checkpoints.

---

## BUGS

_References only; full records in [`../bugs.md`](../bugs.md)._

- (none)

## History

_Append-only, newest first._

- **2026-09-01** — Initial granular step breakdown written by ARCHITECT agent.
