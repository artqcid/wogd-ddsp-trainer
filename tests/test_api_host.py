"""Tests for /api/host endpoints (GPU info + preset validation)."""

from __future__ import annotations


def _valid_preset() -> dict:
    return {
        "hidden_size": 512,
        "stft_scales": 3,
        "mixed_precision": "required",
        "gradient_checkpointing": "optional",
        "learning_rate": 0.001,
    }


def _over_limit_preset() -> dict:
    return {
        "hidden_size": 1024,
        "stft_scales": 5,
        "mixed_precision": "off",
        "gradient_checkpointing": "off",
        "learning_rate": 0.001,
    }


# ---- GET /api/host/info ----


def test_host_info_returns_expected_keys(client):
    resp = client.get("/api/host/info")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, dict)
    assert "gpus" in data
    assert "tier" in data
    assert "bounds" in data
    assert "presets" in data
    assert isinstance(data["gpus"], list)
    assert len(data["gpus"]) >= 1
    gpu = data["gpus"][0]
    assert "name" in gpu
    assert "total_vram_gb" in gpu


def test_host_info_presets_has_speed_keys(client):
    resp = client.get("/api/host/info")
    assert resp.status_code == 200
    data = resp.json()
    presets = data["presets"]
    for speed in ("FAST", "NORMAL", "QUALITY"):
        assert speed in presets
        assert "hidden_size" in presets[speed]
        assert "vram_usage_target" in presets[speed]


def test_host_info_tier_is_string(client):
    resp = client.get("/api/host/info")
    assert resp.status_code == 200
    assert isinstance(resp.json()["tier"], str)


# ---- POST /api/host/validate-preset ----


def test_validate_preset_valid_fits_gpu(client):
    resp = client.post(
        "/api/host/validate-preset",
        json={"params": _valid_preset(), "training_speed": "NORMAL"},
    )
    assert resp.status_code == 200
    data = resp.json()
    # hidden_size=512, NORMAL 0.75x -> 384 (within 256-512) -> no clamping
    assert data["fits_gpu"] is True
    assert data["clamped_fields"] == []


def test_validate_preset_over_limit_fits_gpu_false(client):
    resp = client.post(
        "/api/host/validate-preset",
        json={"params": _over_limit_preset(), "training_speed": "NORMAL"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["fits_gpu"] is False
    assert isinstance(data["clamped_fields"], list)
    assert len(data["clamped_fields"]) >= 1
    assert "hidden_size" in data["clamped_fields"]


def test_validate_preset_returns_all_keys(client):
    resp = client.post(
        "/api/host/validate-preset",
        json={"params": _valid_preset(), "training_speed": "FAST"},
    )
    assert resp.status_code == 200
    data = resp.json()
    expected_keys = {
        "original_params",
        "speed_applied_params",
        "clamped_params",
        "clamped_fields",
        "bounds",
        "training_speed",
        "fits_gpu",
    }
    assert set(data.keys()) == expected_keys
    assert data["training_speed"] == "FAST"


def test_validate_preset_bounds_keys(client):
    resp = client.post(
        "/api/host/validate-preset",
        json={"params": _valid_preset(), "training_speed": "NORMAL"},
    )
    assert resp.status_code == 200
    data = resp.json()
    bounds = data["bounds"]
    assert isinstance(bounds, dict)
    for key in ("hidden_size_min", "hidden_size_max", "stft_scales_min", "stft_scales_max"):
        assert key in bounds


def test_validate_preset_speed_applied_hidden_size_reduced(client):
    """FAST 0.5 on hidden_size=512 -> speed_applied should be 256."""
    params = {
        "hidden_size": 512,
        "stft_scales": 3,
        "mixed_precision": "required",
        "gradient_checkpointing": "optional",
    }
    resp = client.post(
        "/api/host/validate-preset",
        json={"params": params, "training_speed": "FAST"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["speed_applied_params"]["hidden_size"] == 256


def test_validate_preset_speed_applied_no_floor(client):
    """Speed factor alone (no floor to bounds min) should show raw value."""
    params = {
        "hidden_size": 64,
        "stft_scales": 3,
        "mixed_precision": "required",
        "gradient_checkpointing": "optional",
        "learning_rate": 0.001,
    }
    resp = client.post(
        "/api/host/validate-preset",
        json={"params": params, "training_speed": "FAST"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["speed_applied_params"]["hidden_size"] == 32


def test_validate_preset_missing_speed_defaults_normal(client):
    resp = client.post(
        "/api/host/validate-preset",
        json={"params": _valid_preset()},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["training_speed"] == "NORMAL"


def test_validate_preset_original_params_unchanged(client):
    params = _valid_preset()
    resp = client.post(
        "/api/host/validate-preset",
        json={"params": params, "training_speed": "QUALITY"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["original_params"] == params


def test_validate_preset_over_limit_clamped_params_different(client):
    """When over limit, clamped_params should differ from speed_applied."""
    resp = client.post(
        "/api/host/validate-preset",
        json={"params": _over_limit_preset(), "training_speed": "NORMAL"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["speed_applied_params"] != data["clamped_params"]
    for field in data["clamped_fields"]:
        if field in data["speed_applied_params"]:
            assert data["speed_applied_params"][field] != data["clamped_params"][field]
