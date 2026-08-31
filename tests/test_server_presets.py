from __future__ import annotations

from server.db import connect, init_db, preset_create
from server.presets import (
    bounds_to_dict,
    build_builtin_presets,
    check_hardware_change,
    clamp_params,
    get_bounds,
    reclamp_all_custom,
    seed_builtin_presets,
    with_clamp_status,
)
from train.gpu import ParameterBounds, propose_parameters


def _bounds() -> ParameterBounds:
    return propose_parameters(6.0)


def _clamp_cases(bounds: ParameterBounds) -> list[dict]:
    return [
        {
            "hidden_size": bounds.hidden_size_min - 1,
            "stft_scales": bounds.stft_scales_min,
            "mixed_precision": "required",
            "gradient_checkpointing": "enabled",
            "learning_rate": 1e-3,
        },
        {
            "hidden_size": bounds.hidden_size_max + 1,
            "stft_scales": bounds.stft_scales_max,
            "mixed_precision": "required",
            "gradient_checkpointing": "enabled",
            "learning_rate": 1e-3,
        },
    ]


def test_get_bounds_returns_parameterbounds():
    bounds = get_bounds()
    assert isinstance(bounds, ParameterBounds)
    assert isinstance(bounds.hidden_size_min, int)
    assert isinstance(bounds.hidden_size_max, int)
    assert isinstance(bounds.stft_scales_min, int)
    assert isinstance(bounds.stft_scales_max, int)
    assert isinstance(bounds.mixed_precision, str)
    assert isinstance(bounds.gradient_checkpointing, str)


def test_bounds_to_dict_contains_expected_keys():
    bounds = _bounds()
    data = bounds_to_dict(bounds)
    assert isinstance(data, dict)
    for key in (
        "hidden_size_min",
        "hidden_size_max",
        "stft_scales_min",
        "stft_scales_max",
        "mixed_precision",
        "gradient_checkpointing",
    ):
        assert key in data


def test_clamp_hidden_below_min():
    bounds = _bounds()
    params = {"hidden_size": bounds.hidden_size_min - 10, "learning_rate": 1e-3}
    clamped, flags = clamp_params(params, bounds)
    assert clamped["hidden_size"] == bounds.hidden_size_min
    assert "hidden_size" in flags


def test_clamp_hidden_above_max():
    bounds = _bounds()
    params = {"hidden_size": bounds.hidden_size_max + 10, "learning_rate": 1e-3}
    clamped, flags = clamp_params(params, bounds)
    assert clamped["hidden_size"] == bounds.hidden_size_max
    assert "hidden_size" in flags


def test_clamp_stft_scales_below_min():
    bounds = _bounds()
    params = {
        "hidden_size": bounds.hidden_size_min,
        "stft_scales": bounds.stft_scales_min - 1,
        "learning_rate": 1e-3,
    }
    clamped, flags = clamp_params(params, bounds)
    assert clamped["stft_scales"] == bounds.stft_scales_min
    assert "stft_scales" in flags


def test_clamp_mixed_precision_invalid_falls_back():
    bounds = _bounds()
    params = {
        "hidden_size": bounds.hidden_size_min,
        "mixed_precision": "nope",
        "learning_rate": 1e-3,
    }
    clamped, flags = clamp_params(params, bounds)
    assert clamped["mixed_precision"] == bounds.mixed_precision
    assert "mixed_precision" in flags


def test_clamp_gradient_checkpointing_invalid_falls_back():
    bounds = _bounds()
    params = {
        "hidden_size": bounds.hidden_size_min,
        "gradient_checkpointing": "nope",
        "learning_rate": 1e-3,
    }
    clamped, flags = clamp_params(params, bounds)
    assert clamped["gradient_checkpointing"] == bounds.gradient_checkpointing
    assert "gradient_checkpointing" in flags


def test_clamp_learning_rate_missing_defaults_and_flags():
    bounds = _bounds()
    params = {"hidden_size": bounds.hidden_size_min}
    clamped, flags = clamp_params(params, bounds)
    assert clamped["learning_rate"] == 1e-3
    assert "learning_rate" in flags


def test_clamp_learning_rate_below_min():
    bounds = _bounds()
    params = {"hidden_size": bounds.hidden_size_min, "learning_rate": 1e-9}
    clamped, flags = clamp_params(params, bounds)
    assert clamped["learning_rate"] == 1e-6
    assert "learning_rate" in flags


def test_clamp_learning_rate_above_max():
    bounds = _bounds()
    params = {"hidden_size": bounds.hidden_size_min, "learning_rate": 0.5}
    clamped, flags = clamp_params(params, bounds)
    assert clamped["learning_rate"] == 1e-1
    assert "learning_rate" in flags


def test_valid_params_produce_no_flags():
    bounds = _bounds()
    params = {
        "hidden_size": bounds.hidden_size_min,
        "stft_scales": bounds.stft_scales_min,
        "mixed_precision": "required",
        "gradient_checkpointing": "enabled",
        "learning_rate": 1e-3,
    }
    clamped, flags = clamp_params(params, bounds)
    assert clamped == params
    assert flags == []


def test_valid_params_with_learning_rate_no_flags():
    bounds = _bounds()
    params = {
        "hidden_size": bounds.hidden_size_min,
        "stft_scales": bounds.stft_scales_min,
        "mixed_precision": "required",
        "gradient_checkpointing": "enabled",
        "learning_rate": 1e-4,
    }
    clamped, flags = clamp_params(params, bounds)
    assert clamped == params
    assert flags == []


def test_build_builtin_presets_structure():
    bounds = _bounds()
    presets = build_builtin_presets(bounds)
    assert len(presets) == 3

    names = {p["name"] for p in presets}
    assert names == {"FAST", "NORMAL", "QUALITY"}

    ids = {p["id"] for p in presets}
    expected_ids = {"builtin-fast", "builtin-normal", "builtin-quality"}
    assert ids == expected_ids

    for preset in presets:
        assert preset["is_builtin"] is True
        assert preset["created_from_run_id"] is None
        params = preset["params"]
        assert "hidden_size" in params
        assert "learning_rate" in params


def test_seed_builtin_presets_first_call_inserts(tmp_path):
    conn = connect(tmp_path / "test_presets.db")
    init_db(conn)
    bounds = _bounds()
    inserted = seed_builtin_presets(conn, bounds)
    assert inserted == 3
    conn.close()


def test_seed_builtin_presets_second_call_inserted_zero(tmp_path):
    conn = connect(tmp_path / "test_presets.db")
    init_db(conn)
    bounds = _bounds()
    seed_builtin_presets(conn, bounds)
    inserted = seed_builtin_presets(conn, bounds)
    assert inserted == 0
    conn.close()


def test_with_clamp_status_adds_clamped_fields():
    bounds = _bounds()
    preset = {
        "id": "some-preset",
        "name": "some-preset",
        "is_builtin": False,
        "params": {"hidden_size": bounds.hidden_size_min - 5},
        "created_from_run_id": None,
    }
    result = with_clamp_status(preset, bounds)
    assert "clamped_fields" in result
    assert isinstance(result["clamped_fields"], list)
    assert "hidden_size" in result["clamped_fields"]


def test_reclamp_all_custom_updates_out_of_bounds(tmp_path):
    conn = connect(tmp_path / "test_reclamp.db")
    init_db(conn)
    bounds = _bounds()

    preset_create(
        conn,
        id="custom-out-of-bounds",
        name="custom-out-of-bounds",
        is_builtin=False,
        params={
            "hidden_size": bounds.hidden_size_max + 10,
            "stft_scales": bounds.stft_scales_min,
            "mixed_precision": "required",
            "gradient_checkpointing": "enabled",
            "learning_rate": 1e-3,
        },
    )
    inserted_ids = reclamp_all_custom(conn, bounds)
    assert inserted_ids == ["custom-out-of-bounds"]

    conn.close()


def test_reclamp_all_custom_skips_builtin(tmp_path):
    conn = connect(tmp_path / "test_reclamp.db")
    init_db(conn)
    bounds = _bounds()

    preset_create(
        conn,
        id="custom-out-of-bounds",
        name="custom-out-of-bounds",
        is_builtin=False,
        params={
            "hidden_size": bounds.hidden_size_max + 10,
            "stft_scales": bounds.stft_scales_min,
            "mixed_precision": "required",
            "gradient_checkpointing": "enabled",
            "learning_rate": 1e-3,
        },
    )
    seed_builtin_presets(conn, bounds)
    updated = reclamp_all_custom(conn, bounds)
    assert "custom-out-of-bounds" in updated
    assert "builtin-fast" not in updated
    conn.close()


def test_fingerprint_change_first_check_returns_changed(tmp_path):
    conn = connect(tmp_path / "test_fp.db")
    init_db(conn)
    changed, fp = check_hardware_change(conn)
    assert changed is True

    changed2, fp2 = check_hardware_change(conn)
    assert changed2 is False
    assert fp == fp2
    conn.close()
