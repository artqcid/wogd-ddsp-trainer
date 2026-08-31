"""Unit tests for model — DDSPModel forward contracts, determinism, config knobs. CPU only, fixed seed."""

from __future__ import annotations

import torch

from model import DDSPConfig, DDSPModel


def test_forward_returns_keys_and_shapes() -> None:
    torch.manual_seed(0)
    model = DDSPModel(DDSPConfig())
    f0 = torch.full((2, 16), 220.0)
    loudness = torch.rand(2, 16).log()
    out = model(f0, loudness)

    assert set(out.keys()) == {"amplitudes", "harmonic_distribution", "magnitudes", "audio"}

    assert out["amplitudes"].shape == (2, 16, 60)
    assert out["harmonic_distribution"].shape == (2, 16, 60)
    assert out["magnitudes"].shape == (2, 16, 32)
    assert out["audio"].shape == (2, 1921)  # (T-1)*frame_size + 1

    for name, tensor in out.items():
        assert torch.isfinite(tensor).all(), f"{name} not all finite"


def test_harmonic_distribution_softmaxes_to_one() -> None:
    torch.manual_seed(0)
    model = DDSPModel(DDSPConfig())
    f0 = torch.full((2, 8), 220.0)
    loudness = torch.rand(2, 8).log()
    out = model(f0, loudness)

    row_sums = out["harmonic_distribution"].sum(dim=-1)
    expected = torch.ones_like(row_sums)
    torch.testing.assert_allclose(row_sums, expected, atol=1e-5)


def test_deterministic_forward() -> None:
    torch.manual_seed(0)
    model = DDSPModel(DDSPConfig())
    f0 = torch.full((1, 12), 220.0)
    loudness = torch.rand(1, 12).log()
    out_a = model(f0, loudness)

    torch.manual_seed(0)
    model2 = DDSPModel(DDSPConfig())
    out_b = model2(f0, loudness)

    assert torch.equal(out_a["audio"], out_b["audio"]), "audio not bitwise identical across runs"


def test_custom_config() -> None:
    torch.manual_seed(0)
    model = DDSPModel(DDSPConfig(n_harmonics=100, hidden_size=128))
    f0 = torch.full((1, 8), 220.0)
    loudness = torch.rand(1, 8).log()
    out = model(f0, loudness)

    assert out["amplitudes"].shape[-1] == 100
    assert out["harmonic_distribution"].shape[-1] == 100
    assert torch.isfinite(out["audio"]).all()


def test_forward_cpu_no_gpu_hardcode() -> None:
    torch.manual_seed(0)
    model = DDSPModel(DDSPConfig())
    f0 = torch.full((1, 8), 220.0)
    loudness = torch.rand(1, 8).log()
    out = model(f0, loudness)

    audio = out["audio"]
    assert audio.device.type == "cpu"
    assert torch.isfinite(audio).all()
