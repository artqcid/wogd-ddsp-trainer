---
type: implementation-plan
status: draft
milestone: M11 - Latent Space & Morphing
generated:
  by: ARCHITECT-agent
  at: 2026-09-01
stale_after: 2027-06-01
---

# Implementation Plan — M11 Latent Space & Morphing

_Granular plan for milestone M11. Meta plan: [`../plan.md`](../plan.md);
status: [`../checklist.md`](../checklist.md).
Prerequisite: M9 complete (engine dispatch infrastructure in place).
Can be developed in parallel with M10._

## Concept summary

Introduce an explicit, continuous latent vector `z` (VAE-style) between the
feature encoder and the decoder. This enables:

1. **Checkpoint morphing** — interpolate `z_A` and `z_B` from two trained
   models and render the blend.
2. **Random sampling** — sample `z ~ N(0,1)` to generate novel textures
   never heard in training data.
3. **Latent steering** — per-dimension sliders in the UI to explore the
   latent space manually.
4. **Latent-space visualisation** — PCA/t-SNE projection of training-set
   latents displayed as a 2D scatter in the UI.

**Architecture change:** adds a small GRU encoder that maps `(f0, loudness)`
→ `(μ, σ)`, and the reparameterisation trick `z = μ + ε·σ`. The decoder then
receives `[f0, loudness, z_upsampled]` instead of just `[f0, loudness]`.
This is a **breaking change** to the model architecture; M11 checkpoints
are not compatible with M1–M10 standard checkpoints.

## Constraints

- **VRAM:** encoder GRU (~50–100 MB activations) + z concatenation. Still
  within 6 GB budget at `hidden_size=256`.
- **β-VAE balancing:** KL weight β must start small (β ≈ 0.0001) and ramp
  up to prevent posterior collapse. Add a `kl_beta_schedule` to
  `TrainingConfig`.
- **Checkpoint incompatibility:** M11 adds encoder weights and a modified
  decoder input. Tag `state["latent"] = True`.
- **Inference mode distinction:** at inference time, `z` can come from
  (a) the encoder run on input audio, (b) manual interpolation, or
  (c) random sampling. The inference route must support all three.

---

## File map

```
model/encoder.py               NEW  — GRU encoder → (μ, σ) (M11.1)
model/ddsp_model.py            MOD  — VAE mode: z concat + KL loss output (M11.2)
model/ddsp_model.py            MOD  — DDSPConfig.use_latent bool flag (M11.2)
train/trainer.py               MOD  — β-VAE loss term + kl_beta_schedule (M11.3)
train/config.py                MOD  — kl_beta, kl_warmup_steps in TrainingConfig (M11.3)
server/tasks.py                MOD  — pass use_latent + kl_beta to configs (M11.4)
server/routes/inference.py     MOD  — morphing endpoint POST /api/inference/morph (M11.5)
webui/src/views/MorphingView.vue    NEW  — Morphing UI (M11.6)
webui/src/views/LatentExploreView.vue  NEW  — Latent steering + scatter (M11.7)
webui/src/router/index.js      MOD  — two new routes (M11.6, M11.7)
webui/src/components/Sidebar.vue   MOD  — two new links (M11.6, M11.7)
webui/src/api/apiClient.js     MOD  — morph endpoint (M11.5)
webui/src/mocks/mockApiClient.js   MOD  — mock morph response (M11.5)
tests/test_latent.py           NEW  — VAE + morphing tests (M11.8)
doc/experimental-ddsp.md       MOD  — latent space section (M11.9)
```

---

## M11.1 — `GRUEncoder` (`model/encoder.py` — new)

```python
class GRUEncoder(nn.Module):
    """Maps per-frame (f0, loudness) features to a Gaussian latent distribution.

    Returns (μ, log_σ²) for the reparameterisation trick.
    """

    def __init__(self, input_dim: int = 2, hidden_size: int = 128, latent_dim: int = 32) -> None:
        super().__init__()
        self.gru = nn.GRU(input_dim, hidden_size, batch_first=True)
        self.mu_head = nn.Linear(hidden_size, latent_dim)
        self.logvar_head = nn.Linear(hidden_size, latent_dim)

    def forward(self, f0: Tensor, loudness: Tensor) -> tuple[Tensor, Tensor]:
        # features: (B, T_frames, 2)
        features = torch.stack([f0, loudness], dim=-1)
        gru_out, _ = self.gru(features)  # (B, T_frames, hidden)
        mu = self.mu_head(gru_out)  # (B, T_frames, latent_dim)
        logvar = self.logvar_head(gru_out)  # (B, T_frames, latent_dim)
        return mu, logvar
```

**Reparameterisation trick** (in `DDSPModel.forward`):
```python
eps = torch.randn_like(mu)
z = mu + eps * torch.exp(0.5 * logvar)  # (B, T_frames, latent_dim)
```

At inference time with `sample_z=False`: `z = mu` (deterministic, no noise).

**Verify:**
```python
enc = GRUEncoder()
mu, logvar = enc(f0, loudness)
assert mu.shape == logvar.shape == (1, 32, 32)
assert torch.isfinite(mu).all()
```

---

## M11.2 — VAE mode in `DDSPModel`

**File:** `model/ddsp_model.py`

**`DDSPConfig` field:**
```python
use_latent: bool = False
latent_dim: int = 32
```

**`DDSPModel.__init__`** when `use_latent=True`:
```python
self.encoder = GRUEncoder(hidden_size=config.hidden_size // 2,
                           latent_dim=config.latent_dim)
# Decoder input grows by latent_dim
input_dim = 2 + config.latent_dim    # f0 + loudness + z
self.gru = nn.GRU(input_size=input_dim, ...)
```

**`DDSPModel.forward`:**
```python
if self.config.use_latent:
    mu, logvar = self.encoder(f0, loudness)
    if self.training:
        z = mu + torch.randn_like(mu) * torch.exp(0.5 * logvar)
    else:
        z = mu  # deterministic at inference
    features = torch.stack([f0, loudness], dim=-1)
    features = torch.cat([features, z], dim=-1)  # (B, T, 2+latent_dim)
else:
    features = torch.stack([f0, loudness], dim=-1)

gru_out, _ = self.gru(features)
...
```

**Return dict extended:**
```python
return {
    ...,
    "mu": mu if self.config.use_latent else None,
    "logvar": logvar if self.config.use_latent else None,
}
```

**Checkpoint tag:** `state["use_latent"] = True`, `state["latent_dim"] = config.latent_dim`.

---

## M11.3 — β-VAE loss term in `Trainer`

**File:** `train/trainer.py`

After computing `mss_loss`, add KL term when `use_latent=True`:
```python
if self.config.kl_beta > 0.0 and "mu" in out and out["mu"] is not None:
    mu, logvar = out["mu"], out["logvar"]
    # KL divergence: -0.5 * sum(1 + logvar - mu² - exp(logvar))
    kl = -0.5 * (1 + logvar - mu.pow(2) - logvar.exp()).mean()
    # Linear warmup of β
    step_ratio = min(1.0, self.step / max(1, self.config.kl_warmup_steps))
    effective_beta = self.config.kl_beta * step_ratio
    loss = mss_loss + effective_beta * kl
else:
    loss = mss_loss
```

**File:** `train/config.py` → `TrainingConfig`:
```python
kl_beta: float = 0.0  # 0 = disabled (standard MSS loss)
kl_warmup_steps: int = 1000  # steps to ramp β from 0 to kl_beta
```

**Recommended starting value:** `kl_beta=0.0001` with `kl_warmup_steps=2000`.

---

## M11.4 — Server-layer wiring

**File:** `server/tasks.py` → `build_training`:
```python
use_latent = model_config.get("use_latent", False)
latent_dim = int(model_config.get("latent_dim", 32))
kl_beta = float(model_config.get("kl_beta", 0.0001))
kl_warmup = int(model_config.get("kl_warmup_steps", 2000))

dcfg = DDSPConfig(..., use_latent=use_latent, latent_dim=latent_dim)
tcfg = TrainingConfig(..., kl_beta=kl_beta if use_latent else 0.0, kl_warmup_steps=kl_warmup)
```

Add `"use_latent"`, `"latent_dim"`, `"kl_beta"`, `"kl_warmup_steps"` to
`server/presets.py` `PARAM_KEYS`.

---

## M11.5 — Morphing endpoint (`server/routes/inference.py`)

**New endpoint:** `POST /api/inference/morph`

```
Body (JSON):
{
  "run_id_a": "uuid-a",
  "run_id_b": "uuid-b",
  "alpha": 0.5,              // interpolation weight [0, 1]
  "source_audio": base64,    // optional; if absent, use z~N(0,1)
  "pitch_shift": 0,
  "loudness_shift": 0
}
```

**Logic:**
1. Load checkpoint A and B (must both have `use_latent=True` and same
   `latent_dim`).
2. Run encoder on `source_audio` → `z_a = μ_A(source)` and
   `z_b = μ_B(source)`.
   If no source audio → `z_a = z_b = 0` (use mean of prior).
3. Interpolate: `z = alpha * z_a + (1 - alpha) * z_b`.
4. Run decoder of model A with the interpolated `z`.
5. Return rendered audio as WAV.

**Async job** (202 + poll pattern, same as existing synthesis jobs).

---

## M11.6 — `MorphingView.vue` (new)

UI panel:
- Model A / Model B dropdowns (from model registry).
- Source audio upload (optional).
- Alpha slider: 0.0 → 1.0 (live preview disabled; "Render Blend" button).
- Audio player for result.
- Warning banner: "Both models must be trained with Latent Space enabled."

---

## M11.7 — `LatentExploreView.vue` (new)

Two sub-panels:

**Latent Steering:**
- Load a model (latent-enabled only).
- Per-dimension sliders (up to 32 dims, grouped in rows of 8).
- "Render" button → POST /api/inference/morph with `alpha=1` and manually
  constructed `z` vector.

**Latent Scatter (optional, low priority):**
- Backend endpoint `GET /api/inference/latent-pca/{run_id}` runs PCA
  on the training-set μ vectors → returns 2D points.
- Vue canvas renders scatter; click on a point → render that z.

---

## M11.8 — Tests (`tests/test_latent.py` — new)

| Test name | Covers |
|---|---|
| `test_gru_encoder_shape` | M11.1: μ, logvar shapes |
| `test_gru_encoder_finite` | M11.1: no NaN |
| `test_reparameterisation_training` | M11.2: z != μ during training |
| `test_reparameterisation_inference` | M11.2: z == μ during eval |
| `test_model_latent_forward` | M11.2: full forward, finite audio |
| `test_model_latent_backward` | M11.2: backward, no NaN grads |
| `test_kl_loss_nonzero` | M11.3: KL term > 0 for non-zero μ |
| `test_kl_warmup` | M11.3: effective_beta grows with step |
| `test_checkpoint_tag_latent` | M11.2: state["use_latent"] == True |
| `test_morph_endpoint_mock` | M11.5: mock runner returns job |
| `test_morphing_view_renders` | M11.6: vitest |

Total: 10 pytest + 1 vitest.

---

## M11.9 — Docs

Update `doc/experimental-ddsp.md`:
- Add "Latent Space" section: architecture diagram, β-VAE collapse warning,
  morphing workflow.

---

## Execution order

```
M11.1  GRUEncoder               (model/encoder.py)
M11.2  VAE mode in DDSPModel     (model/ddsp_model.py)
  ↓ primary: build + unit test
M11.3  β-VAE loss in Trainer     (train/trainer.py, train/config.py)
M11.4  Server-layer wiring       (server/tasks.py, server/presets.py)
  ↓ primary: build + integration test
M11.5  Morphing endpoint         (server/routes/inference.py)
M11.6  MorphingView.vue          (webui/)
M11.7  LatentExploreView.vue     (webui/)
  ↓ primary: vitest
M11.8  tests/test_latent.py
M11.9  Docs
  ↓ primary: full pytest + vitest + ruff + wiki sync
```

Total: **9 subagent steps** + 3 primary checkpoints.

---

## BUGS

_References only; full records in [`../bugs.md`](../bugs.md)._

- (none)

## History

_Append-only, newest first._

- **2026-09-01** — M11 implemented by DEV agent. All 9 steps complete.
  Parallel batches: Batch 1 (3 subagents: encoder.py, presets PARAM_KEYS, docs),
  Batch 2 (2 subagents: ddsp_model.py VAE, trainer.py KL loss),
  Batch 3 (2 subagents: tasks.py wiring, inference.py morph endpoint),
  Batch 4 (2 subagents: MorphingView.vue, LatentExploreView.vue),
  Batch 5 (1 subagent: tests/test_latent.py).
  Subagent IDs: `ses_fa4748fd2ffebavA3c72dCTcJF` (M11.1),
  `ses_fa474750fffeAsoG9SaTgCczl9` (M11.4b), `ses_fa4743e77ffeYyQVcSHAG9Q0Sm` (M11.9),
  `ses_fa4735302ffeqs5buh6z2aDyml` (M11.2), `ses_fa47326caffenr9Z80dLDlsApp` (M11.3),
  `ses_fa46fcf2dffenuHAOzUr4GD3Ia` (M11.4a), `ses_fa46f8c2cffeVI59hiKYrxVFzS` (M11.5),
  `ses_fa46c312cffeU45gxOuyRDgPvP` (M11.6), `ses_fa46b8080ffeSg56FEDcVn5MH6` (M11.7),
  `ses_fa46a900dffeZFV9TWO8YpH1F1` (M11.8).
  233/233 pytest + 1 skipped, 23/23 vitest, ruff clean (only pre-existing sync-wiki.py issues).
- **2026-09-01** — Initial granular step breakdown written by ARCHITECT agent.
