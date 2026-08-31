"""GPU info and preset+speed validation endpoints (BUG-4)."""

from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter
from pydantic import BaseModel

from server.presets import (
    ParameterBounds,
    clamp_params,
    get_bounds,
)
from train.gpu import suggest_for_host

router = APIRouter(prefix="/host", tags=["host"])

_SPEED_FACTORS = {
    "FAST": {"hidden": 0.50, "scales": "min", "mp": "required", "ckpt": "enabled"},
    "NORMAL": {"hidden": 0.75, "scales": "keep", "mp": "tier", "ckpt": "tier"},
    "QUALITY": {"hidden": 0.90, "scales": "keep", "mp": "tier", "ckpt": "disabled"},
}


class ValidatePresetRequest(BaseModel):
    params: dict
    training_speed: str = "NORMAL"


def apply_speed(params: dict, speed: str, bounds: ParameterBounds) -> dict:
    factor = _SPEED_FACTORS.get(speed, _SPEED_FACTORS["NORMAL"])
    result = dict(params)

    if "hidden_size" in result:
        result["hidden_size"] = int(result["hidden_size"] * factor["hidden"])

    if factor["scales"] == "min":
        result["stft_scales"] = bounds.stft_scales_min
    # "keep" leaves stft_scales unchanged

    if factor["mp"] == "required":
        result["mixed_precision"] = "required"
    elif factor["mp"] == "tier":
        result["mixed_precision"] = bounds.mixed_precision

    if factor["ckpt"] == "enabled":
        result["gradient_checkpointing"] = "enabled"
    elif factor["ckpt"] == "disabled":
        result["gradient_checkpointing"] = "disabled"
    elif factor["ckpt"] == "tier":
        result["gradient_checkpointing"] = bounds.gradient_checkpointing

    return result


@router.get("/info")
def host_info() -> dict:
    return suggest_for_host()


@router.post("/validate-preset")
def validate_preset(req: ValidatePresetRequest) -> dict:
    bounds = get_bounds()
    speed_applied = apply_speed(req.params, req.training_speed, bounds)
    clamped, clamped_fields = clamp_params(speed_applied, bounds)
    return {
        "original_params": req.params,
        "speed_applied_params": speed_applied,
        "clamped_params": clamped,
        "clamped_fields": clamped_fields,
        "bounds": asdict(bounds),
        "training_speed": req.training_speed,
        "fits_gpu": len(clamped_fields) == 0,
    }
