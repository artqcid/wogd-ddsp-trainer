"""Tests for dataset.transforms — pitch quantization, noise injection, pitch inversion."""

from __future__ import annotations

import numpy as np

from dataset.transforms import inject_noise, invert_pitch, quantize_to_scale


def test_quantize_chromatic() -> None:
    f0 = np.array([220.0, 440.0, 880.0], dtype=np.float32)
    result = quantize_to_scale(f0, base_freq=220.0, scale="chromatic")
    assert result.shape == f0.shape
    assert np.allclose(result[0], 220.0, atol=1.0)  # A3
    assert np.allclose(result[1], 440.0, atol=1.0)  # A4
    assert np.all(result > 0)


def test_quantize_major() -> None:
    f0 = np.array([250.0, 300.0, 500.0], dtype=np.float32)
    result = quantize_to_scale(f0, base_freq=220.0, scale="major")
    assert result.shape == f0.shape
    assert np.all(result > 0)


def test_quantize_preserves_unvoiced() -> None:
    f0 = np.array([0.0, 220.0, 0.0, 440.0], dtype=np.float32)
    result = quantize_to_scale(f0, scale="chromatic")
    assert result[0] == 0.0
    assert result[2] == 0.0
    assert result[1] > 0


def test_inject_noise_shape() -> None:
    f0 = np.full(100, 440.0, dtype=np.float32)
    result = inject_noise(f0, noise_std=10.0, probability=0.5, seed=42)
    assert result.shape == f0.shape
    assert np.all(result >= 0)


def test_inject_noise_zero_prob() -> None:
    f0 = np.full(100, 440.0, dtype=np.float32)
    result = inject_noise(f0, probability=0.0)
    assert np.array_equal(result, f0)


def test_inject_noise_deterministic() -> None:
    f0 = np.full(100, 440.0, dtype=np.float32)
    r1 = inject_noise(f0, seed=123)
    r2 = inject_noise(f0, seed=123)
    assert np.array_equal(r1, r2)


def test_invert_pitch() -> None:
    f0 = np.array([220.0, 440.0, 660.0], dtype=np.float32)
    result = invert_pitch(f0, pivot_freq=440.0)
    assert result[0] > result[1]  # low becomes high
    assert np.isclose(result[1], 440.0, atol=1.0)  # pivot unchanged
    assert result[2] < result[1]  # high becomes low


def test_invert_pitch_preserves_unvoiced() -> None:
    f0 = np.array([0.0, 440.0, 0.0], dtype=np.float32)
    result = invert_pitch(f0, pivot_freq=440.0)
    assert result[0] == 0.0
    assert result[2] == 0.0
