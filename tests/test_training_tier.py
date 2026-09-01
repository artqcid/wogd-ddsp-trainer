from __future__ import annotations

from pathlib import Path

import pytest

from server.tasks import build_training


def _standard_config() -> dict:
    return {
        "hidden_size": 256,
        "stft_scales": 3,
        "mixed_precision": "required",
        "gradient_checkpointing": "enabled",
        "learning_rate": 0.001,
        "max_steps": 10,
        "device": "cpu",
    }


def test_build_training_standard_has_default_variant(tmp_path: Path) -> None:
    tcfg, dcfg, loss_fn = build_training(_standard_config(), tmp_path)
    assert dcfg.variant is not None
    assert dcfg.variant.waveform == "sin"
    assert dcfg.n_voices == 1
    assert dcfg.use_latent is False


def test_build_training_hacks_parses_variant(tmp_path: Path) -> None:
    config = _standard_config()
    config["model_tier"] = "hacks"
    config["variant"] = {"waveform": "square", "fm_depth": 50.0}
    tcfg, dcfg, loss_fn = build_training(config, tmp_path)
    assert dcfg.variant.waveform == "square"
    assert dcfg.variant.fm_depth == 50.0


def test_build_training_advanced_parses_n_voices(tmp_path: Path) -> None:
    config = _standard_config()
    config["model_tier"] = "advanced"
    config["n_voices"] = 2
    config["use_latent"] = True
    tcfg, dcfg, loss_fn = build_training(config, tmp_path)
    assert dcfg.n_voices == 2
    assert dcfg.use_latent is True


def test_build_training_standard_ignores_advanced_fields(tmp_path: Path) -> None:
    config = _standard_config()
    config["model_tier"] = "standard"
    config["n_voices"] = 4
    config["use_latent"] = True
    config["use_content_encoder"] = True
    tcfg, dcfg, loss_fn = build_training(config, tmp_path)
    assert dcfg.n_voices == 1
    assert dcfg.use_latent is False


def test_build_training_missing_advanced_fields_no_error(tmp_path: Path) -> None:
    config = _standard_config()
    config["model_tier"] = "advanced"
    del config["learning_rate"]
    with pytest.raises(KeyError):
        build_training(config, tmp_path)


def test_build_training_missing_new_fields_defaults_standard(tmp_path: Path) -> None:
    config = _standard_config()
    config.pop("model_tier", None)
    tcfg, dcfg, loss_fn = build_training(config, tmp_path)
    assert dcfg.n_voices == 1
    assert dcfg.use_latent is False


def test_build_training_engine_tier_parses_variant(tmp_path: Path) -> None:
    config = _standard_config()
    config["model_tier"] = "engine"
    config["variant"] = {"waveform": "saw"}
    tcfg, dcfg, loss_fn = build_training(config, tmp_path)
    assert dcfg.variant.waveform == "saw"
