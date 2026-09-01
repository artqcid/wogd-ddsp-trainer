---
type: implementation-plan
status: draft
milestone: M12 - PolyDDSP (Polyphony)
generated:
  by: ARCHITECT-agent
  at: 2026-09-01
stale_after: 2027-06-01
---

# Implementation Plan — M12 PolyDDSP (Polyphony)

_Granular plan for milestone M12. Meta plan: [`../plan.md`](../plan.md);
status: [`../checklist.md`](../checklist.md).
Prerequisite: M11 complete (or M9 minimum — engine dispatch in place)._

## Concept summary

Standard DDSP is strictly monophonic: one f0 → one harmonic oscillator.
PolyDDSP extends this to **N parallel DDSP voices**, each driven by its own
f0 track, extracted by a multi-pitch tracker. The outputs are summed.

Use cases:
- Train on orchestral chords, choir, multi-instrument recordings.
- Creative misuse: train on a string quartet with `n_voices=4` — the model
  tries to reconstruct polyphony with N independent oscillator banks.
- Harmonic morphing across voices via per-voice loudness scaling.

## Constraints

- **VRAM:** N voices × ~500 MB activations each. At `hidden_size=256`:
  N=2 → ~2.5 GB (safe), N=4 → ~5 GB (tight on 6 GB), N=4 with
  `hidden_size=128` → ~2.5 GB (safe). Recommend max N=2–3 for RTX 3060.
- **Multi-pitch tracker dependency:** `basic-pitch` (Spotify, Apache-2.0,
  TensorFlow/ONNX backend) is the primary candidate. Must run offline
  (preprocessing phase only, not during training). Dependency research
  required before M12.1.
- **Checkpoint incompatibility:** N voices changes model shape. Tag
  `state["n_voices"] = N`.
- **Shared vs. independent weights:** shared decoder weights across voices
  (one decoder, called N times) or N independent decoders. Shared is
  simpler and uses N× less VRAM; independent decoders can specialise
  per voice. Default: **shared weights** (more practical on 6 GB).

---

## File map

```
dataset/multi_pitch.py         NEW  — multi-pitch extraction wrapper (M12.1)
dataset/features.py            MOD  — call multi-pitch extractor, save N f0 tracks (M12.2)
dataset/dataset.py             MOD  — DDSPDataset yields N f0 tracks (M12.2)
model/polyddsp_model.py        NEW  — PolyDDSPModel wrapping N voices (M12.3)
model/ddsp_model.py            MOD  — DDSPConfig.n_voices field (M12.3)
server/tasks.py                MOD  — PolyDDSPModel when n_voices > 1 (M12.4)
server/presets.py              MOD  — n_voices in PARAM_KEYS (M12.4)
webui/src/views/TrainingConfigView.vue  MOD  — n_voices input (M12.5)
webui/src/views/PreprocessingView.vue   MOD  — multi-pitch track display (M12.5)
webui/src/mocks/fixtures.js    MOD  — n_voices fixture (M12.5)
tests/test_polyddsp.py         NEW  — smoke tests (M12.6)
doc/ddsp-concepts.md           MOD  — polyphony section (M12.7)
```

---

## M12.1 — Multi-pitch tracker wrapper (`dataset/multi_pitch.py` — new)

**Dependency research (pre-implementation task):**
Before writing code, verify `basic-pitch` availability:
```bash
pip show basic-pitch   # check if already installed
python -c "import basic_pitch; print(basic_pitch.__version__)"
```

If `basic-pitch` is not available or introduces a TF dependency that
conflicts with the PyTorch-only rule, fallback options:
- `crepe-polyphonic` (does not exist as a pip package — ruled out).
- `librosa.pyin` (monophonic only — not suitable).
- `torchaudio.functional.detect_pitch_frequency` (monophonic — not suitable).
- **`partitura` + `madmom`** (beat/pitch tracking, GPL — ruled out by
  OSI-only rule).
- **Manual harmonic stacking** — run CREPE N times on the N strongest
  harmonic layers extracted via NMF. Slow but dependency-free.
- **`torchcrepe` with frequency candidate tracking** — run crepe and return
  the top-N pitch candidates per frame (already produces multiple
  candidates; threshold by confidence).

**Recommended fallback if basic-pitch conflicts:** use `torchcrepe` in
multi-candidate mode. The tracker returns the top-K f0 candidates per
frame; assign the highest-confidence one to voice 1, second to voice 2, etc.

**Module signature (engine-agnostic):**
```python
def extract_multi_pitch(
    audio: np.ndarray,
    sample_rate: int,
    n_voices: int,
    hop_length: int,
    method: Literal["basic_pitch", "torchcrepe_topk"] = "torchcrepe_topk",
) -> np.ndarray:
    """Extract N f0 tracks from polyphonic audio.

    Returns:
        f0_tracks: (N, T_frames) array of f0 values in Hz.
                   Unvoiced frames set to 0.0.
    """
```

**Verify:**
```python
f0_tracks = extract_multi_pitch(audio, 16000, n_voices=2, hop_length=128)
assert f0_tracks.shape == (2, T_frames)
assert (f0_tracks >= 0).all()
```

---

## M12.2 — Dataset pipeline extension

**File:** `dataset/features.py`

When `n_voices > 1`, call `extract_multi_pitch` instead of single-voice
CREPE. Save result as `f0_hz_voices.npy` shape `(N, T_frames)` alongside
the existing `f0_hz.npy` (kept for backward compat).

**File:** `dataset/dataset.py` → `DDSPDataset`

When loading a multi-voice dataset:
- Return `f0_voices: (N, T_frames)` tensor per chunk.
- If the dataset has no `f0_hz_voices.npy` (single-voice legacy), expand
  `f0_hz` to `(1, T_frames)` and pad with zeros for remaining voices.

---

## M12.3 — `PolyDDSPModel` (`model/polyddsp_model.py` — new)

**Architecture:** one shared `DDSPModel` (or N independent if
`n_voices_independent=True`) called N times, one per voice. Outputs summed.

```python
class PolyDDSPModel(nn.Module):
    """N-voice polyphonic DDSP model.

    Shared decoder weights across all voices by default.
    Each voice receives its own f0 track; loudness is shared.
    """

    def __init__(self, config: DDSPConfig, n_voices: int = 2, independent: bool = False) -> None:
        super().__init__()
        self.n_voices = n_voices
        if independent:
            self.voices = nn.ModuleList([DDSPModel(config) for _ in range(n_voices)])
        else:
            self.shared_voice = DDSPModel(config)
            self.voices = None

    def forward(self, f0_voices: Tensor, loudness: Tensor) -> dict[str, Tensor]:
        # f0_voices: (B, N, T_frames)
        # loudness:  (B, T_frames) — shared across all voices
        audio_sum = None
        for i in range(self.n_voices):
            model = self.voices[i] if self.voices else self.shared_voice
            f0_i = f0_voices[:, i, :]  # (B, T_frames)
            out_i = model(f0_i, loudness)
            if audio_sum is None:
                audio_sum = out_i["audio"]
            else:
                audio_sum = audio_sum + out_i["audio"]
        return {"audio": audio_sum / self.n_voices}  # normalise
```

**`DDSPConfig` field:**
```python
n_voices: int = 1  # 1 = standard monophonic
n_voices_independent: bool = False
```

**Checkpoint tag:** `state["n_voices"] = config.n_voices`.

---

## M12.4 — Server-layer wiring

**File:** `server/tasks.py` → `build_training`:
```python
n_voices = int(model_config.get("n_voices", 1))
dcfg = DDSPConfig(..., n_voices=n_voices)
# Instantiate PolyDDSPModel when n_voices > 1
if n_voices > 1:
    model = PolyDDSPModel(dcfg, n_voices=n_voices)
else:
    model = DDSPModel(dcfg)
```

**File:** `server/presets.py`: add `"n_voices"` to `PARAM_KEYS`.
Clamp: `1 ≤ n_voices ≤ 4` (hard cap to protect VRAM).

---

## M12.5 — UI changes

**File:** `webui/src/views/TrainingConfigView.vue`

Add "Polyphony" section (shown only when advanced mode is active):
- `n_voices` number input: 1–4 (default 1, warning at > 2 for 6 GB GPU).
- `n_voices_independent` checkbox (default off).
- VRAM warning: "N voices × ~500 MB. Reduce hidden_size if VRAM is tight."

**File:** `webui/src/views/PreprocessingView.vue`

When `n_voices > 1`: show N parallel F0-confidence waveforms in the
waveform inspector (one per voice, stacked vertically with voice label).

---

## M12.6 — Tests (`tests/test_polyddsp.py` — new)

| Test name | Covers |
|---|---|
| `test_multi_pitch_shape` | M12.1: f0_tracks shape (N, T) |
| `test_multi_pitch_nonneg` | M12.1: no negative f0 |
| `test_dataset_multi_voice_yields_correct_shape` | M12.2: DDSPDataset yields (N, T) |
| `test_polyddsp_shared_forward` | M12.3: shared weights, 2 voices, finite |
| `test_polyddsp_independent_forward` | M12.3: independent weights, 2 voices |
| `test_polyddsp_backward` | M12.3: backward ok, grads non-None |
| `test_polyddsp_checkpoint_tag` | M12.3: state["n_voices"] set |
| `test_polyddsp_mismatch_raises` | M12.3: loading 2-voice ckpt into 1-voice raises |
| `test_n_voices_clamp` | M12.4: server clamps n_voices to [1,4] |

Total: 9 pytest.

---

## M12.7 — Docs

Update `doc/ddsp-concepts.md`:
- Add "Polyphony" section: voice assignment strategy, VRAM implications,
  PolyDDSP reference.

---

## Execution order

```
M12.1  Multi-pitch tracker (dependency check first!)
M12.2  Dataset pipeline: f0_hz_voices.npy + DDSPDataset update
  ↓ primary: build + test dataset
M12.3  PolyDDSPModel
  ↓ primary: build + unit test
M12.4  Server-layer wiring
M12.5  UI: n_voices controls + multi-F0 display
  ↓ primary: vitest
M12.6  tests/test_polyddsp.py
M12.7  Docs
  ↓ primary: full pytest + vitest + ruff + wiki sync
```

Total: **7 subagent steps** + 3 primary checkpoints.

---

## BUGS

_References only; full records in [`../bugs.md`](../bugs.md)._

- (none)

## History

_Append-only, newest first._

- **2026-09-01** — M12 implemented: multi_pitch.py (STFT peak-picking), features.py/loader.py poly extensions, PolyDDSPModel, server wiring (tasks.py + presets.py), UI (n_voices input + multi-F0 display), tests (9/9 pytest + vitest), docs.
- **2026-09-01** — Initial granular step breakdown written by ARCHITECT agent.
