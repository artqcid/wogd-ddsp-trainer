import pytest

from inference.export import DDSPNeutoneWrapper
from model.ddsp_model import DDSPConfig, DDSPModel
from model.param_manifest import InferenceParam, ParamManifest


def _make_model() -> DDSPModel:
    return DDSPModel(DDSPConfig(hidden_size=32, n_harmonics=20))


def _make_manifest(n_neutone: int = 4) -> ParamManifest:
    params = [
        InferenceParam(1, "Pitch Shift", "d", "continuous", -24.0, 24.0, 0.0, neutone_slot=1),
        InferenceParam(2, "Loudness", "d", "continuous", -20.0, 20.0, 0.0, neutone_slot=2),
    ]
    if n_neutone >= 3:
        params.append(
            InferenceParam(3, "Harmonic Blend", "d", "continuous", 0.0, 1.0, 0.5, neutone_slot=3)
        )
    if n_neutone >= 4:
        params.append(
            InferenceParam(4, "Noise Blend", "d", "continuous", 0.0, 1.0, 0.5, neutone_slot=4)
        )
    return ParamManifest(params=params)


def test_wrapper_with_standard_manifest_returns_correct_param_count() -> None:
    model = _make_model()
    manifest = _make_manifest(4)
    wrapper = DDSPNeutoneWrapper(model, manifest)
    assert wrapper.get_n_params() == 4


def test_wrapper_param_names_match_manifest() -> None:
    model = _make_model()
    manifest = _make_manifest(4)
    wrapper = DDSPNeutoneWrapper(model, manifest)
    params = wrapper.get_neutone_parameters()
    names = [p[0] for p in params]
    assert "Pitch Shift" in names
    assert "Harmonic Blend" in names


def test_wrapper_with_5_neutone_slots_raises_value_error() -> None:
    model = _make_model()
    params = [
        InferenceParam(1, "A", "d", "continuous", 0, 1, 0.5, neutone_slot=1),
        InferenceParam(2, "B", "d", "continuous", 0, 1, 0.5, neutone_slot=2),
        InferenceParam(3, "C", "d", "continuous", 0, 1, 0.5, neutone_slot=3),
        InferenceParam(4, "D", "d", "continuous", 0, 1, 0.5, neutone_slot=4),
        InferenceParam(5, "E", "d", "continuous", 0, 1, 0.5, neutone_slot=1),  # duplicate slot
    ]
    # neutone_params returns [A(1), B(2), C(3), D(4), E(1)] -> 5 items -> ValueError
    with pytest.raises(ValueError):
        DDSPNeutoneWrapper(model, ParamManifest(params=params))


def test_wrapper_forward_returns_audio_tensor() -> None:
    model = _make_model()
    manifest = _make_manifest(4)
    wrapper = DDSPNeutoneWrapper(model, manifest)
    import torch

    f0 = torch.randn(1, 10)
    loudness = torch.randn(1, 10)
    out = wrapper.forward(f0, loudness)
    assert isinstance(out, torch.Tensor)
    assert out.dim() >= 1


def test_export_neutone_still_raises() -> None:
    from inference.export import export_neutone

    model = _make_model()
    with pytest.raises(NotImplementedError):
        export_neutone(model, "/tmp/out.nm")
