"""Preset logic for the M4 backend.

Built-in seeding, GPU-constraint validation/clamping, and hardware-change
detection.  Pure stdlib + project modules (train.gpu, server.db); no torch
import here.
"""

from __future__ import annotations

import json
from dataclasses import asdict

from server.db import (
    meta_get,
    meta_set,
    preset_all,
    preset_by_name,
    preset_create,
    preset_update,
)
from train.gpu import (
    ParameterBounds,
    detect_gpus,
    propose_parameters,
    propose_presets,
    vram_tier,
)

PARAM_KEYS: tuple = (
    "hidden_size",
    "stft_scales",
    "mixed_precision",
    "gradient_checkpointing",
    "learning_rate",
)
ALLOWED_MIXED_PRECISION = ("required", "recommended", "optional")
ALLOWED_CHECKPOINTING = ("enabled", "optional", "disabled")
LEARNING_RATE_MIN = 1e-6
LEARNING_RATE_MAX = 1e-1
DEFAULT_LEARNING_RATE = 1e-3


def get_bounds() -> ParameterBounds:
    """Largest GPU total VRAM -> propose_parameters(); no GPU -> 6.0 baseline."""
    gpus = detect_gpus()
    if gpus:
        total_vram = max(g["total_vram_gb"] for g in gpus)
        return propose_parameters(total_vram)
    return propose_parameters(6.0)


def get_gpu_summary() -> dict:
    """Return GPU list (detect_gpus) and vram_tier of largest GPU, or None."""
    gpus = detect_gpus()
    tier: str | None = None
    if gpus:
        total_vram = max(g["total_vram_gb"] for g in gpus)
        tier = vram_tier(total_vram)
    return {"gpus": gpus, "tier": tier}


def bounds_to_dict(bounds: ParameterBounds) -> dict:
    """Convert ParameterBounds to a plain dict."""
    return asdict(bounds)


def clamp_params(params: dict, bounds: ParameterBounds) -> tuple[dict, list[str]]:
    """Clamp bounded keys and return (clamped_params, clamped_fields).

    Only the bounded keys are touched; other keys are preserved unchanged and
    never flagged.  A missing bounded key is left absent unless it is
    learning_rate (which defaults to DEFAULT_LEARNING_RATE when missing).
    """
    clamped: dict = dict(params)
    flags: list[str] = []

    if "hidden_size" in clamped:
        try:
            value = int(clamped["hidden_size"])
        except (ValueError, TypeError):
            value = bounds.hidden_size_min
            flags.append("hidden_size")
        else:
            if value < bounds.hidden_size_min:
                value = bounds.hidden_size_min
                flags.append("hidden_size")
            elif value > bounds.hidden_size_max:
                value = bounds.hidden_size_max
                flags.append("hidden_size")
            clamped["hidden_size"] = value
    else:
        # missing -> leave absent (no default), no flag
        pass

    if "stft_scales" in clamped:
        try:
            value = int(clamped["stft_scales"])
        except (ValueError, TypeError):
            value = bounds.stft_scales_min
            flags.append("stft_scales")
        else:
            if value < bounds.stft_scales_min:
                value = bounds.stft_scales_min
                if "stft_scales" not in flags:
                    flags.append("stft_scales")
            elif value > bounds.stft_scales_max:
                value = bounds.stft_scales_max
                if "stft_scales" not in flags:
                    flags.append("stft_scales")
            clamped["stft_scales"] = value
    else:
        pass

    if "mixed_precision" in clamped:
        value = clamped["mixed_precision"]
        if value not in ALLOWED_MIXED_PRECISION:
            clamped["mixed_precision"] = bounds.mixed_precision
            flags.append("mixed_precision")

    if "gradient_checkpointing" in clamped:
        value = clamped["gradient_checkpointing"]
        if value not in ALLOWED_CHECKPOINTING:
            clamped["gradient_checkpointing"] = bounds.gradient_checkpointing
            flags.append("gradient_checkpointing")

    if "learning_rate" in clamped:
        try:
            value = float(clamped["learning_rate"])
        except (ValueError, TypeError):
            value = DEFAULT_LEARNING_RATE
            flags.append("learning_rate")
        else:
            if value < LEARNING_RATE_MIN:
                value = LEARNING_RATE_MIN
                if "learning_rate" not in flags:
                    flags.append("learning_rate")
            elif value > LEARNING_RATE_MAX:
                value = LEARNING_RATE_MAX
                if "learning_rate" not in flags:
                    flags.append("learning_rate")
            clamped["learning_rate"] = value
    else:
        clamped["learning_rate"] = DEFAULT_LEARNING_RATE
        flags.append("learning_rate")

    return clamped, flags


def build_builtin_presets(bounds: ParameterBounds) -> list[dict]:
    """Produce built-in FAST/NORMAL/QUALITY preset dicts from *bounds*."""
    preset_params = propose_presets(bounds)
    lr = DEFAULT_LEARNING_RATE
    return [
        {
            "id": "builtin-fast",
            "name": "FAST",
            "is_builtin": True,
            "params": {**preset_params["FAST"], "learning_rate": lr},
            "created_from_run_id": None,
        },
        {
            "id": "builtin-normal",
            "name": "NORMAL",
            "is_builtin": True,
            "params": {**preset_params["NORMAL"], "learning_rate": lr},
            "created_from_run_id": None,
        },
        {
            "id": "builtin-quality",
            "name": "QUALITY",
            "is_builtin": True,
            "params": {**preset_params["QUALITY"], "learning_rate": lr},
            "created_from_run_id": None,
        },
    ]


def seed_builtin_presets(conn, bounds: ParameterBounds) -> int:
    """Insert missing built-in presets; commit after all; return inserted count."""
    inserted = 0
    for preset in build_builtin_presets(bounds):
        if preset_by_name(conn, preset["name"]) is None:
            preset_create(
                conn,
                id=preset["id"],
                name=preset["name"],
                is_builtin=preset["is_builtin"],
                params=preset["params"],
                created_from_run_id=preset["created_from_run_id"],
            )
            inserted += 1
    conn.commit()
    return inserted


def with_clamp_status(preset: dict, bounds: ParameterBounds) -> dict:
    """Return the preset dict with a ``clamped_fields`` entry."""
    clamped_fields = clamp_params(preset["params"], bounds)[1]
    return {**preset, "clamped_fields": clamped_fields}


def reclamp_all_custom(conn, bounds: ParameterBounds) -> list[str]:
    """Clamp all custom presets; update changed ones; commit; return updated ids."""
    updated: list[str] = []
    for preset in preset_all(conn):
        if preset["is_builtin"]:
            continue
        clamped_params, clamped_fields = clamp_params(preset["params"], bounds)
        if clamped_fields:
            preset_update(conn, preset["id"], params=clamped_params)
            updated.append(preset["id"])
    conn.commit()
    return updated


def compute_hardware_fingerprint() -> str:
    """Stable JSON fingerprint of GPU name + total VRAM, or "no-gpu"."""
    gpus = detect_gpus()
    if not gpus:
        return "no-gpu"
    data = [{"name": g["name"], "total_vram_gb": g["total_vram_gb"]} for g in gpus]
    return json.dumps(data, sort_keys=True)


def check_hardware_change(conn) -> tuple[bool, str]:
    """Persist new fingerprint; return (changed, fingerprint)."""
    fp = compute_hardware_fingerprint()
    stored = meta_get(conn, "hardware_fingerprint")
    meta_set(conn, "hardware_fingerprint", fp)
    conn.commit()
    changed = stored != fp
    return changed, fp
