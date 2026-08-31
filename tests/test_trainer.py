import pytest
import torch

from model import DDSPConfig, DDSPModel
from train import Trainer, TrainingConfig


def _make_trainer(
    tmp_path: pytest.TempPath, max_steps: int = 1000
) -> tuple[Trainer, torch.Tensor, torch.Tensor, torch.Tensor]:
    model = DDSPModel(DDSPConfig(hidden_size=32, n_harmonics=20))
    model.train()
    config = TrainingConfig(
        device="cpu",
        use_mixed_precision=False,
        log_dir=str(tmp_path / "runs"),
        max_steps=max_steps,
    )
    trainer = Trainer(model, config)
    f0 = torch.full((1, 16), 220.0)
    loudness = torch.rand(1, 16).log()
    audio = model(f0, loudness)["audio"]
    target = torch.randn_like(audio)
    return trainer, f0, loudness, target


def test_train_step_returns_loss_and_step(tmp_path: pytest.TempPath) -> None:
    torch.manual_seed(0)
    trainer, f0, loudness, target = _make_trainer(tmp_path)
    out = trainer.train_step(f0, loudness, target)
    assert set(out.keys()) >= {"loss", "step"}
    assert isinstance(out["loss"], float)
    assert out["loss"] == float(out["loss"])  # finite
    assert out["step"] >= 0


def test_train_step_reduces_loss(tmp_path: pytest.TempPath) -> None:
    torch.manual_seed(0)
    trainer, f0, loudness, _ = _make_trainer(tmp_path)
    target = torch.zeros_like(trainer.model(f0, loudness)["audio"])
    first = trainer.train_step(f0, loudness, target)
    for _ in range(80):
        trainer.train_step(f0, loudness, target)
    last = trainer.train_step(f0, loudness, target)
    assert last["loss"] < first["loss"]


def test_checkpoint_save_load_roundtrip(tmp_path: pytest.TempPath) -> None:
    torch.manual_seed(0)
    trainer, f0, loudness, target = _make_trainer(tmp_path)
    trainer.train_step(f0, loudness, target)
    trainer.train_step(f0, loudness, target)
    cpt_path = str(tmp_path / "c.pt")
    trainer.save_checkpoint(cpt_path)

    loaded_model = DDSPModel(DDSPConfig(hidden_size=32, n_harmonics=20))
    loaded_model.train()
    loaded_config = TrainingConfig(
        device="cpu",
        use_mixed_precision=False,
        log_dir=str(tmp_path / "runs2"),
    )
    loaded_trainer = Trainer(loaded_model, loaded_config)
    loaded_trainer.load_checkpoint(cpt_path)
    loaded_out = loaded_trainer.train_step(f0, loudness, target)
    assert loaded_out["step"] >= 2


def test_resume_returns_step(tmp_path: pytest.TempPath) -> None:
    torch.manual_seed(0)
    trainer, f0, loudness, target = _make_trainer(tmp_path)
    trainer.train_step(f0, loudness, target)
    trainer.train_step(f0, loudness, target)
    cpt_path = str(tmp_path / "c.pt")
    trainer.save_checkpoint(cpt_path)
    step = trainer.resume(cpt_path)
    assert isinstance(step, int)
    assert step >= 2


def test_run_returns_stats(tmp_path: pytest.TempPath) -> None:
    torch.manual_seed(0)
    trainer, f0, loudness, target = _make_trainer(tmp_path, max_steps=3)
    trainer._checkpoint_dir = str(tmp_path)
    out = trainer.run(f0, loudness, target)
    assert set(out.keys()) >= {"steps", "final_loss"}
    assert out["steps"] == 3
    assert isinstance(out["final_loss"], float)
    runs_dir = tmp_path / "runs"
    assert runs_dir.is_dir()
    events = list(runs_dir.glob("events.out.tfevents.*"))
    assert len(events) > 0


def test_train_step_no_mixed_precision_on_cpu(tmp_path: pytest.TempPath) -> None:
    torch.manual_seed(0)
    model = DDSPModel(DDSPConfig(hidden_size=32, n_harmonics=20))
    model.train()
    config = TrainingConfig(
        device="cpu",
        use_mixed_precision=True,
        log_dir=str(tmp_path / "runs"),
    )
    trainer = Trainer(model, config)
    f0 = torch.full((1, 16), 220.0)
    loudness = torch.rand(1, 16).log()
    target = torch.randn_like(model(f0, loudness)["audio"])
    out = trainer.train_step(f0, loudness, target)
    assert out["loss"] == float(out["loss"])
