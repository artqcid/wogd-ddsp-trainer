from __future__ import annotations

from typing import Any

from fastapi import APIRouter

router = APIRouter(prefix="/gpu", tags=["gpu"])


@router.get("/feasibility")
def gpu_feasibility(
    model_tier: str = "standard",
    n_voices: int = 1,
    use_latent: bool = False,
    use_content_encoder: bool = False,
) -> dict[str, Any]:
    """Return VRAM feasibility for the requested config + all five tiers.

    ``available_gb`` is set to ``total_gb`` (training is GPU-exclusive, so
    the total VRAM is the correct budget value, not the momentary free
    amount).  Both ``total_gb`` and ``free_gb`` are also returned separately
    for informative display.
    """
    from train.gpu import detect_gpus, estimate_model_vram

    gpus = detect_gpus()
    total_gb = max(
        (g["total_vram_gb"] for g in gpus),
        default=6.0,
    )
    free_gb = max(
        (g["available_vram_gb"] or g["total_vram_gb"] for g in gpus),
        default=6.0,
    )

    est = estimate_model_vram(model_tier, n_voices, use_latent, use_content_encoder)

    ALL_TIERS = ("standard", "component", "hacks", "engine", "advanced")
    tier_feasibility = {}
    for t in ALL_TIERS:
        e = estimate_model_vram(t)
        tier_feasibility[t] = {
            "fits": e.peak_gb <= total_gb,
            "estimated_gb": e.peak_gb,
            "warning": e.warning,
        }
    e_adv = estimate_model_vram("advanced", n_voices=3)
    tier_feasibility["advanced"]["worst_case_gb"] = e_adv.peak_gb
    tier_feasibility["advanced"]["worst_case_warning"] = e_adv.warning

    return {
        "fits": est.peak_gb <= total_gb,
        "estimated_gb": est.peak_gb,
        "available_gb": round(total_gb, 2),
        "total_gb": round(total_gb, 2),
        "free_gb": round(free_gb, 2),
        "warning": est.warning,
        "tier_feasibility": tier_feasibility,
    }
