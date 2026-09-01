import json
from pathlib import Path

import pytest
import torch

from inference.export_custom_vst import CustomVSTWrapper, export_custom_vst
from model.ddsp_model import DDSPConfig, DDSPModel
from model.param_manifest import InferenceParam, ParamManifest, build_default_manifest


def test_custom_vst_wrapper_create_and_query() -> None:
    model = DDSPModel(DDSPConfig(hidden_size=32, n_harmonics=20))
    manifest = build_default_manifest("standard", {})
    wrapper = CustomVSTWrapper(model, manifest)
    assert wrapper.get_n_params() == 4
    parsed = json.loads(wrapper.get_param_manifest_json())
    assert parsed["format"] == "wogd-vst-params"
    assert len(parsed["params"]) == 4


def test_custom_vst_wrapper_get_n_params() -> None:
    model = DDSPModel(DDSPConfig(hidden_size=32, n_harmonics=20))
    manifest = build_default_manifest("standard", {})
    wrapper = CustomVSTWrapper(model, manifest)
    assert wrapper.get_n_params() == 4


def test_custom_vst_wrapper_with_17_params_raises() -> None:
    model = DDSPModel(DDSPConfig(hidden_size=32, n_harmonics=20))
    params = [InferenceParam(i, f"P{i}", "d", "continuous", 0, 1, 0.5) for i in range(1, 18)]
    with pytest.raises(ValueError, match="16"):
        CustomVSTWrapper(model, ParamManifest(params=params))


def test_export_custom_vst_traced_file(tmp_path: Path) -> None:
    model = DDSPModel(DDSPConfig(hidden_size=32, n_harmonics=20))
    manifest = build_default_manifest("standard", {})
    ckpt_path = str(tmp_path / "model.pt")
    state = {
        "model_state_dict": model.state_dict(),
        "config": {"hidden_size": 32, "n_harmonics": 20, "n_noise_bins": 32},
        "param_manifest": manifest.to_dict(),
    }
    torch.save(state, ckpt_path)

    out_path = str(tmp_path / "custom_vst.pt")
    result = export_custom_vst(ckpt_path, out_path)
    assert result == out_path

    loaded = torch.jit.load(out_path)
    f0 = torch.randn(1, 10)
    loudness = torch.randn(1, 10)
    audio = loaded(f0, loudness)
    assert isinstance(audio, torch.Tensor)
    assert audio.numel() > 0
