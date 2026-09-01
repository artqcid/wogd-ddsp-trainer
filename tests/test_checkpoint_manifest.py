import pytest
import torch

from model import DDSPConfig, DDSPModel
from model.param_manifest import ParamManifest
from train import Trainer, TrainingConfig


def _make_trainer(
    tmp_path: pytest.TempPath,
    model_tier: str = "standard",
    variant_flags: dict | None = None,
) -> Trainer:
    model = DDSPModel(DDSPConfig(hidden_size=32, n_harmonics=20))
    model.train()
    config = TrainingConfig(
        device="cpu",
        use_mixed_precision=False,
        log_dir=str(tmp_path / "runs"),
    )
    trainer = Trainer(model, config, model_tier=model_tier, variant_flags=variant_flags)
    return trainer


def test_save_checkpoint_contains_param_manifest(tmp_path: pytest.TempPath) -> None:
    torch.manual_seed(0)
    trainer = _make_trainer(tmp_path)
    cpt_path = str(tmp_path / "c.pt")
    trainer.save_checkpoint(cpt_path)
    state = torch.load(cpt_path, map_location="cpu", weights_only=False)
    assert "param_manifest" in state
    assert state["param_manifest"]["format"] == "wogd-vst-params"
    assert len(state["param_manifest"]["params"]) == 4


def test_save_checkpoint_contains_model_tier(tmp_path: pytest.TempPath) -> None:
    torch.manual_seed(0)
    trainer = _make_trainer(tmp_path, model_tier="engine", variant_flags={"engine": "newt"})
    cpt_path = str(tmp_path / "c.pt")
    trainer.save_checkpoint(cpt_path)
    state = torch.load(cpt_path, map_location="cpu", weights_only=False)
    assert state["model_tier"] == "engine"
    assert "newt" in str(state["variant_flags"])


def test_load_checkpoint_returns_valid_manifest(tmp_path: pytest.TempPath) -> None:
    torch.manual_seed(0)
    trainer = _make_trainer(tmp_path)
    cpt_path = str(tmp_path / "c.pt")
    trainer.save_checkpoint(cpt_path)

    trainer2 = _make_trainer(tmp_path)
    trainer2.load_checkpoint(cpt_path)
    manifest = trainer2.param_manifest
    assert manifest is not None
    assert isinstance(manifest, ParamManifest)
    assert len(manifest.params) == 4


def test_load_old_checkpoint_without_manifest(tmp_path: pytest.TempPath) -> None:
    torch.manual_seed(0)
    model = DDSPModel(DDSPConfig(hidden_size=32, n_harmonics=20))
    config = TrainingConfig(device="cpu", use_mixed_precision=False, log_dir=str(tmp_path / "runs"))
    trainer = Trainer(model, config)
    # Save without param_manifest (old format)
    torch.save(
        {
            "step": 0,
            "model_state_dict": model.state_dict(),
            "optimizer_state_dict": trainer.optimizer.state_dict(),
        },
        str(tmp_path / "old.pt"),
    )
    trainer2 = _make_trainer(tmp_path)
    trainer2.load_checkpoint(str(tmp_path / "old.pt"))
    manifest = trainer2.param_manifest
    assert manifest is not None
    assert len(manifest.params) >= 4


def test_engine_tier_manifest_in_checkpoint(tmp_path: pytest.TempPath) -> None:
    torch.manual_seed(0)
    trainer = _make_trainer(tmp_path, model_tier="engine", variant_flags={"engine": "newt"})
    cpt_path = str(tmp_path / "c.pt")
    trainer.save_checkpoint(cpt_path)
    trainer2 = _make_trainer(tmp_path)
    trainer2.load_checkpoint(cpt_path)
    name = trainer2.param_manifest.params[2].name  # P3
    assert "Tone" in name or "Character" in name
