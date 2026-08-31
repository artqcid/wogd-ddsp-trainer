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
    stft_scales_min: int
    stft_scales_max: int
    mixed_precision: str  # one of: required, recommended, optional
    gradient_checkpointing: str  # one of: enabled, optional, disabled

    @property
    def max_hidden(self) -> int:
        return self.hidden_size_max


def _bounds_for_tier(tier: str) -> ParameterBounds:
    """Return the authoritative bound set for a tier (from architecture.md).

    Table (VRAM, hidden size, STFT scales, checkpointing, mixed precision):
        * low   (<4 GB)    128 or 256        3              enabled  required
        * mid   (4-8 GB)   256 or 512        3              optional required
        * high  (8-12 GB)  512              5              disabled recommended
        * ultra (>=12 GB)  512-1024         5-8            disabled optional
    """
    table: dict[str, ParameterBounds] = {
        "low": ParameterBounds(
            hidden_size_min=128,
            hidden_size_max=256,
            stft_scales_min=3,
            stft_scales_max=3,
            mixed_precision="required",
            gradient_checkpointing="enabled",
        ),
        "mid": ParameterBounds(
            hidden_size_min=256,
            hidden_size_max=512,
            stft_scales_min=3,
            stft_scales_max=3,
            mixed_precision="required",
            gradient_checkpointing="optional",
        ),
        "high": ParameterBounds(
            hidden_size_min=512,
            hidden_size_max=512,
            stft_scales_min=5,
            stft_scales_max=5,
            mixed_precision="recommended",
            gradient_checkpointing="disabled",
        ),
        "ultra": ParameterBounds(
            hidden_size_min=512,
            hidden_size_max=1024,
            stft_scales_min=5,
            stft_scales_max=8,
            mixed_precision="optional",
            gradient_checkpointing="disabled",
        ),
    }
    return table[tier]


def propose_parameters(total_vram_gb: float) -> ParameterBounds:
    """Propose training parameter bounds for the given total VRAM in GB.

    Returns a :class:`ParameterBounds` derived from the VRAM tier that
    ``total_vram_gb`` falls into.
    """
    tier = vram_tier(total_vram_gb)
    return _bounds_for_tier(tier)


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
    ``gradient_checkpointing``, and ``vram_usage_target``
    (``0.25``, ``0.50``, or ``1.0``).
    """
    max_hidden = bounds.max_hidden
    min_scales = bounds.stft_scales_min
    max_scales = bounds.stft_scales_max

    fast: dict = {
        "hidden_size": int(max_hidden * 0.25),
        "stft_scales": min_scales,
        "mixed_precision": "required",
        "gradient_checkpointing": "enabled",
        "vram_usage_target": 0.25,
    }
    normal: dict = {
        "hidden_size": int(max_hidden * 0.50),
        "stft_scales": min_scales,
        "mixed_precision": "required",
        "gradient_checkpointing": bounds.gradient_checkpointing,
        "vram_usage_target": 0.50,
    }
    quality: dict = {
        "hidden_size": max_hidden,
        "stft_scales": max_scales,
        "mixed_precision": bounds.mixed_precision,
        "gradient_checkpointing": "disabled",
        "vram_usage_target": 1.0,
    }
    return {
        "FAST": fast,
        "NORMAL": normal,
        "QUALITY": quality,
    }


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
