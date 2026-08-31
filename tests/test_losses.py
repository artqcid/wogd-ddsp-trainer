"""Unit tests for spectral losses — MultiScaleSpectralLoss + compute_spectral_loss.
Deterministic, CPU only."""

from __future__ import annotations

import torch

from model import MultiScaleSpectralLoss, compute_spectral_loss


def test_loss_finite_scalar() -> None:
    torch.manual_seed(0)
    loss_fn = MultiScaleSpectralLoss()
    a = torch.rand(1, 4096).uniform_(-1.0, 1.0)
    b = torch.rand(1, 4096).uniform_(-1.0, 1.0)
    loss = loss_fn(a, b)

    assert loss.shape == torch.Size([])
    assert torch.isfinite(loss).all()


def test_loss_default_scales_match_config() -> None:
    default = MultiScaleSpectralLoss()
    assert getattr(default, "fft_sizes", None) is not None
    # The public API exposes the default scales; assert the documented defaults.
    if hasattr(default, "fft_sizes"):
        assert list(default.fft_sizes) == [512, 1024, 2048]

    custom = MultiScaleSpectralLoss(fft_sizes=[256, 512])
    a = torch.rand(1, 4096).uniform_(-1.0, 1.0)
    b = torch.rand(1, 4096).uniform_(-1.0, 1.0)
    loss = custom(a, b)
    assert loss.shape == torch.Size([])
    assert torch.isfinite(loss).all()


def test_identical_inputs_zero() -> None:
    torch.manual_seed(0)
    loss_fn = MultiScaleSpectralLoss()
    a = torch.rand(1, 4096).uniform_(-1.0, 1.0)
    loss = loss_fn(a, a)

    # Identical signals should yield ~0 loss under L1 mag/log-mag criteria.
    assert loss.item() < 1e-3


def test_loss_greater_than_zero_for_different() -> None:
    torch.manual_seed(0)
    loss_fn = MultiScaleSpectralLoss()
    a = torch.zeros(1, 4096)
    b = torch.ones(1, 4096) * 0.5
    loss = loss_fn(a, b)

    assert loss.item() > 0.0


def test_compute_spectral_loss_equals_module() -> None:
    torch.manual_seed(0)
    a = torch.rand(1, 4096).uniform_(-1.0, 1.0)
    b = torch.rand(1, 4096).uniform_(-1.0, 1.0)

    direct = compute_spectral_loss(a, b)
    module = MultiScaleSpectralLoss()(a, b)

    torch.testing.assert_allclose(direct, module, atol=1e-6, rtol=1e-7)


def test_compute_spectral_loss_custom_scales() -> None:
    torch.manual_seed(0)
    a = torch.rand(1, 4096).uniform_(-1.0, 1.0)
    b = torch.rand(1, 4096).uniform_(-1.0, 1.0)

    direct = compute_spectral_loss(a, b, fft_sizes=[256, 512])
    module = MultiScaleSpectralLoss(fft_sizes=[256, 512])(a, b)

    torch.testing.assert_allclose(direct, module, atol=1e-6, rtol=1e-7)
