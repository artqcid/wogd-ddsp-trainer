from __future__ import annotations

from unittest.mock import patch

from train.gpu import VRAMEstimate, estimate_model_vram


def test_estimate_standard() -> None:
    est = estimate_model_vram("standard")
    assert est.peak_gb == 2.2
    assert est.warning is None


def test_estimate_advanced_no_addons() -> None:
    est = estimate_model_vram("advanced", n_voices=1)
    assert est.peak_gb == 2.35
    assert est.warning is None


def test_estimate_advanced_latent() -> None:
    est = estimate_model_vram("advanced", use_latent=True)
    assert est.peak_gb == 2.50
    assert est.warning is None


def test_estimate_advanced_content_encoder() -> None:
    est = estimate_model_vram("advanced", use_content_encoder=True)
    assert est.peak_gb == 2.71
    assert est.warning is None


def test_estimate_advanced_n3() -> None:
    est = estimate_model_vram("advanced", n_voices=3)
    assert est.peak_gb == 7.05
    assert est.warning is not None


def test_estimate_advanced_n3_all() -> None:
    est = estimate_model_vram("advanced", n_voices=3, use_latent=True, use_content_encoder=True)
    assert est.peak_gb > 7.0
    assert est.warning is not None


def test_estimate_non_advanced_ignores_params() -> None:
    expected = {"standard": 2.2, "component": 2.25, "hacks": 2.3, "engine": 2.35}
    for tier, peak_gb in expected.items():
        est = estimate_model_vram(tier, n_voices=3, use_latent=True, use_content_encoder=True)
        assert est.peak_gb == peak_gb, f"{tier}: expected {peak_gb}, got {est.peak_gb}"
        assert est.warning is None


def test_estimate_vram_returns_peak_gb() -> None:
    """Verify VRAMEstimate is a proper dataclass with peak_gb."""
    est = estimate_model_vram("standard")
    assert isinstance(est, VRAMEstimate)
    assert isinstance(est.peak_gb, float)


def test_gpu_feasibility_endpoint_returns_tier_feasibility() -> None:
    from fastapi.testclient import TestClient

    from server.main import app

    client = TestClient(app)
    with patch("train.gpu.detect_gpus", return_value=[]):
        resp = client.get("/api/gpu/feasibility")
    assert resp.status_code == 200
    data = resp.json()
    assert "tier_feasibility" in data
    tf = data["tier_feasibility"]
    for tier in ("standard", "component", "hacks", "engine", "advanced"):
        assert tier in tf
        assert "fits" in tf[tier]
        assert "estimated_gb" in tf[tier]
        assert "estimated_gb" in tf[tier] is not None
    assert "worst_case_gb" in tf["advanced"]
    assert "worst_case_warning" in tf["advanced"]
    # BUG-10: verify total_gb and free_gb are present
    assert "total_gb" in data
    assert "free_gb" in data
    assert data["total_gb"] == data["available_gb"]


def test_gpu_feasibility_advanced_n3_does_not_fit() -> None:
    from fastapi.testclient import TestClient

    from server.main import app

    client = TestClient(app)
    with patch("train.gpu.detect_gpus", return_value=[]):
        resp = client.get("/api/gpu/feasibility?model_tier=advanced&n_voices=3")
    assert resp.status_code == 200
    data = resp.json()
    assert data["fits"] is False
