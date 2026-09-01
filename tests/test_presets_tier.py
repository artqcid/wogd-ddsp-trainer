from __future__ import annotations

from server.presets import (
    ADVANCED_KEYS,
    ENGINE_KEYS,
    PARAM_KEYS,
    VARIANT_KEYS,
    build_builtin_presets,
    clamp_params,
)
from train.gpu import ParameterBounds, propose_parameters


def test_build_builtin_presets_standard() -> None:
    bounds = propose_parameters(6.0)
    presets = build_builtin_presets(bounds, tier="standard")
    assert len(presets) == 3
    for p in presets:
        assert p["model_tier"] == "standard"
        assert p["name"] in ("FAST", "NORMAL", "QUALITY")


def test_build_builtin_presets_engine() -> None:
    bounds = propose_parameters(6.0)
    presets = build_builtin_presets(bounds, tier="engine")
    assert len(presets) == 3
    for p in presets:
        assert p["model_tier"] == "engine"


def test_build_builtin_presets_ids_differ_by_tier() -> None:
    bounds = propose_parameters(6.0)
    standard_ids = {p["id"] for p in build_builtin_presets(bounds, tier="standard")}
    engine_ids = {p["id"] for p in build_builtin_presets(bounds, tier="engine")}
    assert standard_ids.isdisjoint(engine_ids)


def test_variant_keys_not_in_param_keys() -> None:
    for key in VARIANT_KEYS:
        assert key not in PARAM_KEYS


def test_engine_keys_not_in_param_keys() -> None:
    for key in ENGINE_KEYS:
        assert key not in PARAM_KEYS


def test_advanced_keys_are_param_keys() -> None:
    # ADVANCED_KEYS were added to PARAM_KEYS in M11-M13 by design
    for key in ADVANCED_KEYS:
        assert key in PARAM_KEYS


def test_variant_keys_not_clamped() -> None:
    bounds = ParameterBounds(
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
    )
    params = {
        "hidden_size": 128,
        "n_harmonics": 30,
        "n_filter_banks": 20,
        "stft_scales": 3,
        "mixed_precision": "required",
        "gradient_checkpointing": "enabled",
        "learning_rate": 0.001,
        "waveform": "square",
        "fm_depth": 50.0,
        "engine": "newt",
        "use_latent": True,
        "n_voices": 4,
    }
    clamped, flags = clamp_params(params, bounds)
    for key in VARIANT_KEYS:
        if key in params:
            assert clamped[key] == params[key], f"{key} should not be clamped"
    for key in ENGINE_KEYS:
        if key in params:
            assert clamped[key] == params[key], f"{key} should not be clamped"
    for key in ADVANCED_KEYS:
        if key in params:
            assert clamped[key] == params[key], f"{key} should not be clamped"
    assert "waveform" not in flags
    assert "engine" not in flags
    assert "use_latent" not in flags
