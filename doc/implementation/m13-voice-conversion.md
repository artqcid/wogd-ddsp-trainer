---
type: implementation-plan
status: draft
milestone: M13 - Voice Conversion (HuBERT/ContentVec)
generated:
  by: ARCHITECT-agent
  at: 2026-09-01
stale_after: 2027-06-01
---

# Implementation Plan — M13 Voice Conversion (HuBERT/ContentVec)

_Granular plan for milestone M13. Meta plan: [`../plan.md`](../plan.md);
status: [`../checklist.md`](../checklist.md).
Prerequisite: M11 preferred (latent encoder infrastructure reusable).
Largest milestone in the roadmap — plan for 4–6 sessions._

## Concept summary

Replace the f0+loudness autoencoder conditioning with a **pretrained semantic
content encoder** (HuBERT-Soft or ContentVec). The result is a full
**voice conversion (VC)** system: source speaker's content (phonemes, prosody)
is extracted by the frozen content encoder and re-synthesized with the
**trained target timbre** (the DDSP decoder + synth).

This mirrors the DDSP-SVC architecture, implemented in our own PyTorch stack.

**Signal flow:**
```
Source audio
    ↓
ContentEncoder (HuBERT-Soft / ContentVec, frozen)
    → content_embedding (B, T_frames, 256)
F0 extractor (CREPE/parselmouth, existing)
    → f0 (B, T_frames)
Loudness extractor (librosa, existing)
    → loudness (B, T_frames)
    ↓
[content_embedding + f0_embed + loudness_embed]
    → Decoder (GRU) → synth params → DDSPCore → audio
```

## Constraints

- **HuBERT-Soft memory:** ~360 MB at inference (frozen). Training adds only
  activation memory for the DDSP decoder. Total ~1.9 GB — well within 6 GB.
- **Frozen encoder:** HuBERT-Soft weights are never updated. Only the DDSP
  decoder + synth are trained.
- **Offline feature extraction:** HuBERT-Soft runs once per dataset in the
  preprocessing phase and saves `content_embedding.npy`. Training loads from
  cache — same pattern as f0/loudness.
- **Checkpoint incompatibility:** M13 adds content embedding input dimension.
  Tag `state["use_content_encoder"] = True`.
- **License:** HuBERT-Soft (MIT ✅), ContentVec (MIT ✅). Downloaded via
  `huggingface_hub.hf_hub_download` — no API cost, offline-capable after
  first download.

---

## File map

```
model/content_encoder.py       NEW  — ContentEncoderWrapper (M13.1)
dataset/features.py            MOD  — extract_content_embedding() (M13.2)
dataset/dataset.py             MOD  — DDSPDataset loads content_embedding.npy (M13.2)
model/ddsp_model.py            MOD  — DDSPConfig.use_content_encoder + new input head (M13.3)
train/trainer.py               MOD  — no change needed (loss unchanged) (M13.3)
server/tasks.py                MOD  — pass use_content_encoder to config (M13.4)
server/routes/inference.py     MOD  — VC synthesis endpoint (M13.5)
server/routes/dataset.py       MOD  — trigger content embedding extraction (M13.5)
webui/src/views/VoiceConversionView.vue  NEW  — VC UI (M13.6)
webui/src/router/index.js      MOD  — /voice-conversion route (M13.6)
webui/src/components/Sidebar.vue   MOD  — Voice Conversion nav link (M13.6)
webui/src/api/apiClient.js     MOD  — vc synthesis call (M13.6)
webui/src/mocks/mockApiClient.js   MOD  — mock vc response (M13.6)
tests/test_content_encoder.py  NEW  — content encoder tests (M13.7)
tests/test_vc_pipeline.py      NEW  — end-to-end VC pipeline tests (M13.7)
doc/related-work.md            MOD  — DDSP-SVC section updated (M13.8)
```

---

## M13.1 — `ContentEncoderWrapper` (`model/content_encoder.py` — new)

**Two supported models (user selects in training config):**

| Model | Size | License | HF repo |
|---|---|---|---|
| HuBERT-Soft | ~360 MB | MIT | `bshall/hubert-soft` |
| ContentVec | ~360 MB | MIT | `lengyue233/content-vec-best` |

```python
class ContentEncoderWrapper(nn.Module):
    """Frozen pretrained content encoder (HuBERT-Soft or ContentVec).

    Extracts semantic content embeddings from raw audio. Weights are never
    updated; call .eval() and set requires_grad_(False) at init.
    """

    def __init__(
        self,
        model_name: Literal["hubert_soft", "content_vec"] = "hubert_soft",
        cache_dir: str | None = None,
    ) -> None:
        super().__init__()
        self.model_name = model_name
        self._model = self._load(model_name, cache_dir)
        self._model.eval()
        self._model.requires_grad_(False)

    def _load(self, name: str, cache_dir: str | None):
        from huggingface_hub import hf_hub_download

        if name == "hubert_soft":
            # HuBERT-Soft: bshall/hubert-soft, model.pt
            path = hf_hub_download("bshall/hubert-soft", "hubert-soft.pt", cache_dir=cache_dir)
            import torch

            return torch.hub.load(
                "bshall/hubert-soft:main", "hubert_soft", path=path, trust_repo=True
            )
        elif name == "content_vec":
            # ContentVec: use torchaudio or direct checkpoint load
            raise NotImplementedError("ContentVec loader TBD in M13.1")
        raise ValueError(f"Unknown content encoder: {name}")

    @torch.no_grad()
    def forward(self, audio: Tensor, sample_rate: int = 16000) -> Tensor:
        """Extract content embeddings.

        Args:
            audio: (B, T_audio) waveform, normalised to [-1, 1].
            sample_rate: must be 16000 for HuBERT-Soft.

        Returns:
            content: (B, T_frames_hub, 256) — HuBERT frame rate is 50 Hz
                     (320 samples/frame at 16 kHz).
        """
        return self._model.units(audio)  # API varies by model; adapt
```

**Note:** HuBERT-Soft outputs at 50 Hz (320-sample hop). Our DDSP frames
are at `sample_rate / frame_size = 16000 / 128 = 125 Hz`. A resampling step
(linear interpolation over the time axis) aligns the two rates.

**Resample helper:**
```python
def resample_content(content: Tensor, target_frames: int) -> Tensor:
    """Interpolate content embedding time axis to target_frames."""
    # content: (B, T_hub, D) → (B, D, T_hub) → interpolate → (B, D, T_target)
    return F.interpolate(
        content.transpose(1, 2),
        size=target_frames,
        mode="linear",
        align_corners=False,
    ).transpose(1, 2)
```

**Verify (requires network access for first download):**
```python
enc = ContentEncoderWrapper("hubert_soft")
audio = torch.randn(1, 16000)
emb = enc(audio, 16000)
assert emb.shape[-1] == 256
assert torch.isfinite(emb).all()
```

---

## M13.2 — Offline content embedding extraction

**File:** `dataset/features.py`

Add function `extract_content_embedding`:
```python
def extract_content_embedding(
    audio: np.ndarray,
    sample_rate: int,
    model_name: str = "hubert_soft",
    target_frames: int | None = None,
    cache_dir: str | None = None,
) -> np.ndarray:
    """Extract and optionally resample HuBERT/ContentVec embeddings.

    Returns:
        embedding: (T_frames, 256) numpy array.
    """
    encoder = ContentEncoderWrapper(model_name, cache_dir=cache_dir)
    audio_t = torch.from_numpy(audio).float().unsqueeze(0)
    with torch.no_grad():
        emb = encoder(audio_t, sample_rate)  # (1, T_hub, 256)
    if target_frames is not None:
        emb = resample_content(emb, target_frames)
    return emb.squeeze(0).numpy()  # (T_frames, 256)
```

Save as `content_embedding.npy` alongside `f0_hz.npy` and `loudness_db.npy`
in the feature cache.

**File:** `dataset/dataset.py` → `DDSPDataset.__getitem__`

If `content_embedding.npy` exists, load it and return in the item dict:
```python
if (cache_path / "content_embedding.npy").exists():
    content = np.load(cache_path / "content_embedding.npy")
    item["content_embedding"] = torch.from_numpy(content[start:end]).float()
else:
    item["content_embedding"] = None
```

---

## M13.3 — Content encoder conditioning in `DDSPModel`

**File:** `model/ddsp_model.py`

**`DDSPConfig` fields:**
```python
use_content_encoder: bool = False
content_encoder_name: Literal["hubert_soft", "content_vec"] = "hubert_soft"
content_dim: int = 256  # HuBERT output dim
```

**`DDSPModel.__init__`** when `use_content_encoder=True`:
```python
# GRU input: content_dim + 1 (f0) + 1 (loudness)
# Projection from content_dim to a smaller space first to save VRAM:
self.content_proj = nn.Linear(config.content_dim, 64)
input_dim = 64 + 2    # projected content + f0 + loudness
self.gru = nn.GRU(input_size=input_dim, hidden_size=config.hidden_size, ...)
```

**`DDSPModel.forward`** when `use_content_encoder=True`:
```python
# content_embedding: (B, T_frames, content_dim) — pre-extracted, from dataset
if content_embedding is not None:
    content_proj = F.relu(self.content_proj(content_embedding))  # (B, T, 64)
    features = torch.cat([content_proj, f0.unsqueeze(-1), loudness.unsqueeze(-1)], dim=-1)
else:
    features = torch.stack([f0, loudness], dim=-1)
```

The `content_embedding` argument is optional — when `None`, fall back to
f0+loudness only (backward compatible inference path).

**Checkpoint tag:**
`state["use_content_encoder"] = True`
`state["content_encoder_name"] = config.content_encoder_name`

---

## M13.4 — Server-layer wiring

**File:** `server/tasks.py` → `build_training`:
```python
use_ce = bool(model_config.get("use_content_encoder", False))
ce_name = model_config.get("content_encoder_name", "hubert_soft")
dcfg = DDSPConfig(..., use_content_encoder=use_ce, content_encoder_name=ce_name)
```

**File:** `server/presets.py`: add `"use_content_encoder"`,
`"content_encoder_name"` to `PARAM_KEYS` (passed through unchanged; not
clamped).

---

## M13.5 — VC inference endpoint

**New endpoint:** `POST /api/inference/voice-convert`

```
Body (multipart):
  run_id: str          — trained model (must have use_content_encoder=True)
  source_audio: file   — source speaker audio (the "content donor")
  pitch_shift: float   — optional semitone shift (default 0)
  loudness_shift: float — optional dB shift (default 0)
```

**Logic:**
1. Load checkpoint; verify `use_content_encoder=True`.
2. Extract content embedding from `source_audio` using the model's
   `content_encoder_name`.
3. Extract f0 + loudness from `source_audio` (existing pipeline).
4. Apply `pitch_shift` to f0.
5. Run `DDSPModel.forward(f0, loudness, content_embedding=emb)`.
6. Apply output enhancer if enabled (reuses M7.0 `OutputEnhancer`).
7. Return WAV (async job pattern: 202 + poll).

**Dataset-side trigger:** add a button "Extract Content Embeddings" in the
preprocessing UI → `POST /api/datasets/{id}/extract-content` →
Celery task runs `extract_content_embedding` for all files in the dataset.
This is a one-time offline step; the result is cached.

---

## M13.6 — `VoiceConversionView.vue` (new)

UI panel sections:
1. **Model selection** — dropdown filtered to `use_content_encoder=True`
   models (badge shown on model cards).
2. **Source audio** — upload panel (same waveform display as inference
   playground, Wavesurfer.js).
3. **Pitch shift** — semitone slider (−12 to +12).
4. **Loudness shift** — dB slider (−12 to +12).
5. **Convert** button → POST to voice-convert endpoint → poll job.
6. **A/B player** — compare original source with VC output
   (reuse `ABComparisonPlayer.vue`).
7. Info callout: "The target timbre comes from the trained model. The
   source content (speech/melody) comes from the uploaded audio."

Sidebar link: "Voice Conversion" under "Inference" nav group.

---

## M13.7 — Tests

### `tests/test_content_encoder.py` (new)

| Test name | Covers |
|---|---|
| `test_content_encoder_offline` | M13.1: CPU smoke, mock HuBERT output (skip if no network) |
| `test_resample_content_shape` | M13.1: resample_content output shape |
| `test_extract_content_embedding_shape` | M13.2: (T_frames, 256) |
| `test_dataset_loads_content_embedding` | M13.2: DDSPDataset item has content |

### `tests/test_vc_pipeline.py` (new)

| Test name | Covers |
|---|---|
| `test_ddsp_model_with_content_forward` | M13.3: content conditioning, finite |
| `test_ddsp_model_with_content_backward` | M13.3: backward, grads ok |
| `test_ddsp_model_content_none_fallback` | M13.3: None content → f0+loudness path |
| `test_checkpoint_tag_content_encoder` | M13.3: state has use_content_encoder |
| `test_vc_endpoint_mock` | M13.5: mock runner, 202 response |
| `test_vc_view_renders` | M13.6: vitest |

Total: 10 pytest + 1 vitest.

---

## M13.8 — Docs

Update `doc/related-work.md`:
- Add "M13 implementation notes": how our VC pipeline differs from DDSP-SVC
  (our own DDSP core, no combsub, offline content extraction).

---

## Execution order

```
M13.1  ContentEncoderWrapper     (model/content_encoder.py)
M13.2  Offline extraction        (dataset/features.py, dataset/dataset.py)
  ↓ primary: build + unit test (mock HuBERT output)
M13.3  Content conditioning in DDSPModel
  ↓ primary: build + test
M13.4  Server-layer wiring       (server/tasks.py, server/presets.py)
M13.5  VC inference endpoint     (server/routes/inference.py, server/routes/dataset.py)
  ↓ primary: integration test
M13.6  VoiceConversionView.vue   (webui/)
  ↓ primary: vitest
M13.7a tests/test_content_encoder.py
M13.7b tests/test_vc_pipeline.py
M13.8  Docs
  ↓ primary: full pytest + vitest + ruff + wiki sync
```

Total: **9 subagent steps** + 4 primary checkpoints.

---

## BUGS

_References only; full records in [`../bugs.md`](../bugs.md)._

- (none)

## History

_Append-only, newest first._

- **2026-09-01** — M13 implemented: ContentEncoderWrapper (mock/real HuBERT), extract_content_embedding, DDSPModel content conditioning, server wiring (tasks.py + presets.py), VC endpoint + extract-content endpoint, VoiceConversionView.vue + router + sidebar + api mocks, 10 pytest, related-work.md docs.
- **2026-09-01** — Initial granular step breakdown written by ARCHITECT agent.
