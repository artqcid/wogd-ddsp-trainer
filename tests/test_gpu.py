"""Unit tests for train.suggest — GPU detection, vram tiers, parameter presets.
CPU-only deterministic; CUDA tests are guarded with @pytest.mark.skipif."""

from __future__ import annotations

import pytest
import torch

from train import (
    ParameterBounds,
    detect_gpus,
    propose_parameters,
    propose_presets,
    suggest_for_host,
    vram_tier,
)

# ---------------------------------------------------------------------------
# vram_tier boundary semantics
# ---------------------------------------------------------------------------
# Tier mapping (from architecture.md):
#   <4.0  : "low"
#   4.0..<8.0  : mid   (4.0 inclusive → mid)
#   8.0..<12.0 : high  (8.0 inclusive → high)
#   >=12.0 : ultra
# ---------------------------------------------------------------------------


def test_vram_tier_low() -> None:
    assert vram_tier(2.0) == "low"
    assert vram_tier(0.0) == "low"
    assert vram_tier(3.9) == "low"


def test_vram_tier_mid() -> None:
    assert vram_tier(4.0) == "mid"
    assert vram_tier(5.0) == "mid"
    assert vram_tier(7.9) == "mid"


def test_vram_tier_high() -> None:
    assert vram_tier(8.0) == "high"
    assert vram_tier(10.0) == "high"
    assert vram_tier(11.9) == "high"


def test_vram_tier_ultra() -> None:
    assert vram_tier(12.0) == "ultra"
    assert vram_tier(20.0) == "ultra"
    assert vram_tier(64.0) == "ultra"


@pytest.mark.parametrize(
    "vram,expected",
    [
        (2.0, "low"),
        (4.0, "mid"),
        (8.0, "high"),
        (12.0, "ultra"),
    ],
)
def test_vram_tier_roundtrip(vram: float, expected: str) -> None:
    assert vram_tier(vram) == expected


# ---------------------------------------------------------------------------
# propose_parameters — tier → ParameterBounds
# ---------------------------------------------------------------------------


def test_propose_parameters_low() -> None:
    b = propose_parameters(2.0)
    assert b.hidden_size_min == 128
    assert b.hidden_size_max == 256
    assert b.stft_scales_min == 3
    assert b.stft_scales_max == 3
    assert b.mixed_precision == "required"
    assert b.gradient_checkpointing == "enabled"
    assert b.max_hidden == 256


def test_propose_parameters_mid() -> None:
    b = propose_parameters(6.0)
    assert b.hidden_size_min == 256
    assert b.hidden_size_max == 512
    assert b.max_hidden == 512
    assert b.stft_scales_min == 3
    assert b.stft_scales_max == 3
    assert b.mixed_precision == "required"
    assert b.gradient_checkpointing == "optional"


def test_propose_parameters_high() -> None:
    b = propose_parameters(10.0)
    assert b.hidden_size_min == 512
    assert b.hidden_size_max == 512
    assert b.stft_scales_min == 5
    assert b.stft_scales_max == 5
    assert b.mixed_precision == "recommended"
    assert b.gradient_checkpointing == "disabled"


def test_propose_parameters_ultra() -> None:
    b = propose_parameters(16.0)
    assert b.hidden_size_min == 512
    assert b.hidden_size_max == 1024
    assert b.stft_scales_min == 5
    assert b.stft_scales_max == 8
    assert b.mixed_precision == "optional"
    assert b.gradient_checkpointing == "disabled"


# ---------------------------------------------------------------------------
# propose_presets — FAST / NORMAL / QUALITY relative to vram
# ---------------------------------------------------------------------------


def test_propose_presets_vram_relative() -> None:
    bounds = propose_parameters(6.0)  # mid → max_hidden=512
    presets = propose_presets(bounds)

    assert set(presets.keys()) == {"FAST", "NORMAL", "QUALITY"}

    # hidden_size scalings relative to max_hidden at: 0.25 / 0.5 / 1.0
    assert presets["FAST"]["hidden_size"] == int(bounds.hidden_size_max * 0.25)  # 128
    assert presets["NORMAL"]["hidden_size"] == int(bounds.hidden_size_max * 0.5)  # 256
    assert presets["QUALITY"]["hidden_size"] == bounds.hidden_size_max  # 512

    assert presets["FAST"]["gradient_checkpointing"] == "enabled"
    assert presets["NORMAL"]["gradient_checkpointing"] == "optional"
    assert presets["QUALITY"]["gradient_checkpointing"] == "disabled"

    # vram_usage_target explicit enum
    assert presets["FAST"]["vram_usage_target"] == 0.25
    assert presets["NORMAL"]["vram_usage_target"] == 0.50
    assert presets["QUALITY"]["vram_usage_target"] == 1.0


def test_propose_presets_low_max_hidden_128() -> None:
    bounds = propose_parameters(2.0)  # low → max_hidden=256
    presets = propose_presets(bounds)

    assert presets["FAST"]["hidden_size"] == 64  # 256 * 0.25
    assert presets["NORMAL"]["hidden_size"] == 128
    assert presets["QUALITY"]["hidden_size"] == 256


def test_propose_presets_ultra_max_hidden_1024() -> None:
    bounds = propose_parameters(16.0)  # ultra → max_hidden=1024
    presets = propose_presets(bounds)

    assert presets["FAST"]["hidden_size"] == 256  # 1024 * 0.25
    assert presets["NORMAL"]["hidden_size"] == 512  # 1024 * 0.5
    assert presets["QUALITY"]["hidden_size"] == 1024


# ---------------------------------------------------------------------------
# _bounds_for_tier — n_harmonics / n_filter_banks fields
# ---------------------------------------------------------------------------


def test_bounds_n_harmonics_low() -> None:
    b = propose_parameters(2.0)
    assert b.n_harmonics_min == 20
    assert b.n_harmonics_max == 60
    assert b.n_filter_banks_min == 16
    assert b.n_filter_banks_max == 32


def test_bounds_n_harmonics_ultra() -> None:
    b = propose_parameters(16.0)
    assert b.n_harmonics_min == 20
    assert b.n_harmonics_max == 120
    assert b.n_filter_banks_min == 16
    assert b.n_filter_banks_max == 64


def test_propose_presets_include_n_harmonics() -> None:
    bounds = propose_parameters(6.0)
    presets = propose_presets(bounds)
    for name in ("FAST", "NORMAL", "QUALITY"):
        assert "n_harmonics" in presets[name]
        assert "n_filter_banks" in presets[name]


# ---------------------------------------------------------------------------
# detect_gpus — guarded
# ---------------------------------------------------------------------------


@pytest.mark.skipif(torch.cuda.is_available(), reason="requires no GPU")
def test_detect_gpus_no_cuda() -> None:
    gpus = detect_gpus()
    assert isinstance(gpus, list)
    assert gpus == []


@pytest.mark.skipif(not torch.cuda.is_available(), reason="requires GPU")
def test_detect_gpus_with_cuda() -> None:
    gpus = detect_gpus()
    assert isinstance(gpus, list)
    assert len(gpus) > 0

    for g in gpus:
        assert set(g.keys()) == {"index", "name", "total_vram_gb", "available_vram_gb"}
        assert isinstance(g["index"], int)
        assert isinstance(g["name"], str)
        assert isinstance(g["total_vram_gb"], (int, float))
        assert g["total_vram_gb"] > 0
        assert g["available_vram_gb"] is None or (
            isinstance(g["available_vram_gb"], (int, float)) and g["available_vram_gb"] >= 0
        )


# ---------------------------------------------------------------------------
# suggest_for_host — composite shape
# ---------------------------------------------------------------------------


def test_suggest_for_host_shape() -> dict:
    result = suggest_for_host()

    # Top-level always present.
    assert set(result.keys()) == {"gpus", "tier", "bounds", "presets"}

    if result["gpus"] is not None and len(result["gpus"]) > 0:
        assert set(result["tier"]) == {"low", "mid", "high", "ultra"} or result["tier"] in {
            "low",
            "mid",
            "high",
            "ultra",
        }
        assert result["bounds"] is not None
        assert isinstance(result["bounds"], ParameterBounds)
        assert set(result["presets"].keys()) == {"FAST", "NORMAL", "QUALITY"}
    else:
        # No GPU path: all None.
        assert all(
            v is None for v in (result["gpus"], result["tier"], result["bounds"], result["presets"])
        )

    return result


def test_suggest_for_host_gpus_shape_when_available() -> None:
    result = suggest_for_host()
    if result["gpus"] is None:
        pytest.skip("no GPUs available in this environment")

    gpus = result["gpus"]
    assert isinstance(gpus, list)
    assert len(gpus) > 0
    for g in gpus:
        assert set(g.keys()) == {"index", "name", "total_vram_gb", "available_vram_gb"}
        assert g["total_vram_gb"] > 0

    assert result["tier"] in {"low", "mid", "high", "ultra"}
    assert isinstance(result["bounds"], ParameterBounds)
    assert set(result["presets"].keys()) == {"FAST", "NORMAL", "QUALITY"}
