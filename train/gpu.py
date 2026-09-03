"""GPU detection and VRAM-based training parameter proposal.

:noindex:
"""

from __future__ import annotations

from dataclasses import dataclass

import torch


def detect_gpus() -> list[dict]:
    """Enumerate CUDA devices.

    Returns a list of dicts, each with ``index``, ``name``,
    ``total_vram_gb``, and ``available_vram_gb`` (float or ``None``).
    If no CUDA is available, returns ``[]``.
    """
    if not torch.cuda.is_available():
        return []
    gpus: list[dict] = []
    for idx in range(torch.cuda.device_count()):
        props = torch.cuda.get_device_properties(idx)
        total_bytes = props.total_memory
        total_gb = total_bytes / 1e9
        try:
            available_bytes = torch.cuda.mem_get_info(idx)[0]
        except torch.cuda.Error:
            available_bytes = None
        available_gb: float | None = None
        if available_bytes is not None:
            available_gb = available_bytes / 1e9
        gpus.append(
            {
                "index": idx,
                "name": torch.cuda.get_device_name(idx),
                "total_vram_gb": total_gb,
                "available_vram_gb": available_gb,
            }
        )
    return gpus


def vram_tier(total_vram_gb: float) -> str:
    """Map total VRAM in GB to a tier string.

    Bounds (inclusive):
        * ``< 4``  → ``"low"``
        * ``4 ≤ x < 8`` → ``"mid"``
        * ``8 ≤ x < 12`` → ``"high"``
        * ``≥ 12`` → ``"ultra"``
    """
    if total_vram_gb < 4:
        return "low"
    if total_vram_gb < 8:
        return "mid"
    if total_vram_gb < 12:
        return "high"
    return "ultra"


@dataclass(frozen=True)
class ParameterBounds:
    """Proposed training parameter bounds for a VRAM tier.

    All fields are typed and have sensible defaults for a tier. The
    ``hidden_size_min`` / ``hidden_size_max`` pair defines the allowed
    hidden size range; ``stft_scales_min`` / ``stft_scales_max`` define
    the allowed STFT scale range. ``max_hidden`` is a convenience alias
    for ``hidden_size_max``.
    """

    hidden_size_min: int
    hidden_size_max: int
    n_harmonics_min: int
    n_harmonics_max: int
    n_filter_banks_min: int
    n_filter_banks_max: int
    stft_scales_min: int
    stft_scales_max: int
    mixed_precision: str  # one of: required, recommended, optional
    gradient_checkpointing: str  # one of: enabled, optional, disabled
    batch_size_max: int

    @property
    def max_hidden(self) -> int:
        return self.hidden_size_max


def _bounds_for_tier(tier: str, total_vram_gb: float = 6.0) -> ParameterBounds:
    """Return the authoritative bound set for a tier (from architecture.md).

    ``batch_size_max`` is computed dynamically from ``total_vram_gb``
    (baseline: ``int(total_vram_gb * 32 / 6)``, i.e. 32 at 6 GB,
    capped at 128). Table (VRAM, hidden size, STFT scales, checkpointing,
    mixed precision):
        * low   (<4 GB)    128 or 256        3              enabled  required
        * mid   (4-8 GB)   256 or 512        3              optional required
        * high  (8-12 GB)  512              5              disabled recommended
        * ultra (>=12 GB)  512-1024         5-8            disabled optional
    """
    batch_size_max = min(128, max(2, int(total_vram_gb * 32 / 6)))
    table: dict[str, ParameterBounds] = {
        "low": ParameterBounds(
            hidden_size_min=128,
            hidden_size_max=256,
            n_harmonics_min=20,
            n_harmonics_max=60,
            n_filter_banks_min=16,
            n_filter_banks_max=32,
            stft_scales_min=3,
            stft_scales_max=3,
            mixed_precision="required",
            gradient_checkpointing="enabled",
            batch_size_max=batch_size_max,
        ),
        "mid": ParameterBounds(
            hidden_size_min=256,
            hidden_size_max=512,
            n_harmonics_min=20,
            n_harmonics_max=60,
            n_filter_banks_min=16,
            n_filter_banks_max=32,
            stft_scales_min=3,
            stft_scales_max=3,
            mixed_precision="required",
            gradient_checkpointing="optional",
            batch_size_max=batch_size_max,
        ),
        "high": ParameterBounds(
            hidden_size_min=512,
            hidden_size_max=512,
            n_harmonics_min=20,
            n_harmonics_max=80,
            n_filter_banks_min=16,
            n_filter_banks_max=48,
            stft_scales_min=5,
            stft_scales_max=5,
            mixed_precision="recommended",
            gradient_checkpointing="disabled",
            batch_size_max=batch_size_max,
        ),
        "ultra": ParameterBounds(
            hidden_size_min=512,
            hidden_size_max=1024,
            n_harmonics_min=20,
            n_harmonics_max=120,
            n_filter_banks_min=16,
            n_filter_banks_max=64,
            stft_scales_min=5,
            stft_scales_max=8,
            mixed_precision="optional",
            gradient_checkpointing="disabled",
            batch_size_max=batch_size_max,
        ),
    }
    return table[tier]


def propose_parameters(total_vram_gb: float) -> ParameterBounds:
    """Propose training parameter bounds for the given total VRAM in GB.

    Returns a :class:`ParameterBounds` derived from the VRAM tier that
    ``total_vram_gb`` falls into. ``batch_size_max`` is computed dynamically
    from the VRAM value.
    """
    tier = vram_tier(total_vram_gb)
    return _bounds_for_tier(tier, total_vram_gb)


def propose_presets(bounds: ParameterBounds) -> dict[str, dict]:
    """Return the built-in FAST / NORMAL / QUALITY presets relative to *bounds*.

    VRAM-relative rules (from architecture.md / parameter proposal logic):

    * **FAST**    – hidden = floor(max_hidden * 0.25), scales = min of tier,
                    mixed precision = Required, checkpointing = Enabled.
    * **NORMAL**  – hidden = floor(max_hidden * 0.50), scales = min of tier,
                    mixed precision = Required, checkpointing = tier default.
    * **QUALITY** – hidden = max_hidden, scales = max of tier,
                    mixed precision = tier default, checkpointing = Disabled.

    Each returned dict contains the keys
    ``hidden_size``, ``stft_scales``, ``mixed_precision``,
    ``gradient_checkpointing``, ``n_harmonics``, ``n_filter_banks``,
    ``batch_size``, and ``vram_usage_target``
    (``0.25``, ``0.50``, or ``1.0``).
    """
    max_hidden = bounds.max_hidden
    min_scales = bounds.stft_scales_min
    max_scales = bounds.stft_scales_max
    batch_size_max = bounds.batch_size_max

    fast: dict = {
        "hidden_size": int(max_hidden * 0.25),
        "stft_scales": min_scales,
        "mixed_precision": "required",
        "gradient_checkpointing": "enabled",
        "vram_usage_target": 0.25,
        "n_harmonics": bounds.n_harmonics_min,
        "n_filter_banks": bounds.n_filter_banks_min,
        "batch_size": max(1, int(batch_size_max * 0.25)),
    }
    normal: dict = {
        "hidden_size": int(max_hidden * 0.50),
        "stft_scales": min_scales,
        "mixed_precision": "required",
        "gradient_checkpointing": bounds.gradient_checkpointing,
        "vram_usage_target": 0.50,
        "n_harmonics": int((bounds.n_harmonics_min + bounds.n_harmonics_max) * 0.5),
        "n_filter_banks": int((bounds.n_filter_banks_min + bounds.n_filter_banks_max) * 0.5),
        "batch_size": max(1, int(batch_size_max * 0.50)),
    }
    quality: dict = {
        "hidden_size": max_hidden,
        "stft_scales": max_scales,
        "mixed_precision": bounds.mixed_precision,
        "gradient_checkpointing": "disabled",
        "vram_usage_target": 1.0,
        "n_harmonics": bounds.n_harmonics_max,
        "n_filter_banks": bounds.n_filter_banks_max,
        "batch_size": batch_size_max,
    }
    return {
        "FAST": fast,
        "NORMAL": normal,
        "QUALITY": quality,
    }


@dataclass
class VRAMEstimate:
    """Lightweight VRAM accounting for a model configuration.

    ``peak_gb`` is the estimated peak VRAM in GB.
    ``warning`` is a human-readable message when the estimate exceeds a
    known threshold (e.g. PolyDDSP N>2 on 6 GB), or ``None``.
    """

    peak_gb: float
    warning: str | None = None


BASE_ESTIMATE_GB: dict[str, float] = {
    "standard": 2.2,
    "component": 2.25,
    "hacks": 2.3,
    "engine": 2.35,
    "advanced": 2.35,
}


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
        component (+component mixer)    +0.05 GB
        hacks     (+DDSP variants)      +0.10 GB
        engine    (+alt synth engines)  +0.15 GB
        advanced  (+engine + optional)  +0.15 GB + advanced overheads below
        use_latent (+GRUEncoder/VAE)    +0.15 GB
        use_content_encoder (+HuBERT)   +0.36 GB
        PolyDDSP N voices               baseline x N

    Tier keys not in ``BASE_ESTIMATE_GB`` fall back to 2.2 GB.
    """
    baseline_gb = BASE_ESTIMATE_GB.get(model_tier, 2.2)
    overhead = 0.0
    warning = None

    if model_tier == "advanced":
        if use_latent:
            overhead += 0.15
        if use_content_encoder:
            overhead += 0.36
        if n_voices > 1:
            overhead += baseline_gb * (n_voices - 1)

    peak = baseline_gb + overhead

    if peak > 6.0:
        warning = (
            f"Estimated {peak:.1f} GB exceeds 6 GB — "
            f"recommend a GPU with at least {int(peak) + 1} GB VRAM."
        )

    return VRAMEstimate(peak_gb=round(peak, 2), warning=warning)


def suggest_for_host() -> dict:
    """Return a host summary for the local machine.

    If no GPU is present the result has ``gpus: []`` and ``None`` for
    ``tier``, ``bounds``, and ``presets``. Otherwise the largest GPU's
    total VRAM is used to derive the tier, bounds, and presets.
    """
    gpus = detect_gpus()
    if not gpus:
        return {
            "gpus": [],
            "tier": None,
            "bounds": None,
            "presets": None,
        }
    largest = max(gpus, key=lambda g: g["total_vram_gb"])
    total_vram = largest["total_vram_gb"]
    tier = vram_tier(total_vram)
    bounds = propose_parameters(total_vram)
    presets = propose_presets(bounds)
    return {
        "gpus": gpus,
        "tier": tier,
        "bounds": bounds,
        "presets": presets,
    }
