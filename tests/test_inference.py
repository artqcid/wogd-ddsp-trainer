import os
from dataclasses import asdict

import pytest
import torch

from inference import (
    export_neutone,
    export_onnx,
    export_torchscript,
    load_model_from_checkpoint,
    render,
    render_to_file,
)
from model import DDSPConfig, DDSPModel


def _model_and_inputs(
    tmp_path: pytest.TempPath,
) -> tuple[DDSPModel, torch.Tensor, torch.Tensor, str]:
    model = DDSPModel(DDSPConfig(hidden_size=32, n_harmonics=20))
    model.eval()
    f0 = torch.full((1, 16), 220.0)
    loudness = torch.rand(1, 16).log()
    cpt_path = os.path.join(str(tmp_path), "cpt.pt")
    torch.save(
        {
            "model_state_dict": model.state_dict(),
            "step": 3,
            "config": asdict(model.config),
        },
        cpt_path,
    )
    return model, f0, loudness, cpt_path


def test_load_model_from_checkpoint(tmp_path: pytest.TempPath) -> None:
    _, f0, loudness, cpt_path = _model_and_inputs(tmp_path)
    loaded = load_model_from_checkpoint(cpt_path)
    loaded.eval()
    out = loaded(f0, loudness)
    assert "audio" in out
    audio = out["audio"]
    assert audio.isfinite().all()
    assert audio.numel() > 0


def test_render_returns_audio_and_sr(tmp_path: pytest.TempPath) -> None:
    model, f0, loudness, _cpt_path = _model_and_inputs(tmp_path)
    audio, sr = render(model, f0, loudness)
    assert sr == 16000
    assert audio.dim() == 1
    assert audio.numel() > 0
    assert audio.isfinite().all()


def test_render_to_file(tmp_path: pytest.TempPath) -> None:
    model, f0, loudness, _cpt_path = _model_and_inputs(tmp_path)
    out_path = str(tmp_path / "out.wav")
    written = render_to_file(model, f0, loudness, out_path)
    assert written == out_path
    assert os.path.exists(out_path)
    assert os.path.getsize(out_path) > 0


def test_export_torchscript(tmp_path: pytest.TempPath) -> None:
    model, _f0, _loudness, _cpt_path = _model_and_inputs(tmp_path)
    out_path = str(tmp_path / "m.pt")
    saved = export_torchscript(model, out_path)
    assert saved == out_path
    assert os.path.exists(out_path)
    loaded = torch.jit.load(out_path)
    out = loaded(_torch_input(), _torch_input())
    assert isinstance(out, torch.Tensor)
    assert out.numel() > 0
    assert torch.isfinite(out).all()


def test_export_onnx(tmp_path: pytest.TempPath) -> None:
    model, f0, loudness, _cpt_path = _model_and_inputs(tmp_path)
    import onnx

    out_path = str(tmp_path / "m.onnx")
    saved = export_onnx(model, out_path, f0_shape=f0.shape, loudness_shape=loudness.shape)
    assert saved == out_path
    assert os.path.exists(out_path)
    assert os.path.getsize(out_path) > 0
    try:
        onnx.load(out_path)
    except Exception as exc:  # pragma: no cover - validation-only
        pytest.fail(f"onnx.load failed for {out_path}: {exc}")


def test_export_neutone_raises() -> None:
    with pytest.raises(NotImplementedError):
        export_neutone(DDSPModel(DDSPConfig()), "x")


def _torch_input() -> torch.Tensor:
    return torch.full((1, 16), 220.0)
