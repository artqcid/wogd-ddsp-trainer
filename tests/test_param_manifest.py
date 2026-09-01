import pytest

from model.param_manifest import (
    InferenceParam,
    ParamManifest,
    build_default_manifest,
    validate_manifest,
)


def _standard_params() -> list[InferenceParam]:
    return [
        InferenceParam(1, "Pitch Shift", "desc", "continuous", -24.0, 24.0, 0.0, neutone_slot=1),
        InferenceParam(2, "Loudness", "desc", "continuous", -20.0, 20.0, 0.0, neutone_slot=2),
        InferenceParam(3, "Noise Level", "desc", "continuous", 0.0, 1.0, 0.5, neutone_slot=3),
        InferenceParam(4, "Reverb Mix", "desc", "continuous", 0.0, 1.0, 0.3, neutone_slot=4),
    ]


# ---------------------------------------------------------------------------
# Round-trip to_dict / from_dict
# ---------------------------------------------------------------------------


def test_to_dict_from_dict_roundtrip() -> None:
    m = ParamManifest(params=_standard_params())
    d = m.to_dict()
    m2 = ParamManifest.from_dict(d)
    assert m2.format == m.format
    assert m2.version == m.version
    assert len(m2.params) == len(m.params)
    for a, b in zip(m2.params, m.params, strict=True):
        assert a.slot == b.slot
        assert a.name == b.name


# ---------------------------------------------------------------------------
# Properties: neutone_params / custom_vst_params
# ---------------------------------------------------------------------------


def test_neutone_params_returns_only_neutone_bound_sorted() -> None:
    params = [
        InferenceParam(5, "Reverb Mix", "d", "continuous", 0, 1, 0.3, neutone_slot=None),
        InferenceParam(1, "Pitch Shift", "d", "continuous", -24, 24, 0, neutone_slot=1),
        InferenceParam(2, "Loudness", "d", "continuous", -20, 20, 0, neutone_slot=2),
    ]
    m = ParamManifest(params=params)
    neutone = m.neutone_params
    assert len(neutone) == 2
    assert neutone[0].slot == 1
    assert neutone[1].slot == 2


def test_custom_vst_params_returns_all_sorted_by_slot() -> None:
    params = [
        InferenceParam(5, "Reverb Mix", "d", "continuous", 0, 1, 0.3, neutone_slot=None),
        InferenceParam(1, "Pitch Shift", "d", "continuous", -24, 24, 0, neutone_slot=1),
        InferenceParam(3, "Harmonic Blend", "d", "continuous", 0, 1, 0.5, neutone_slot=3),
    ]
    m = ParamManifest(params=params)
    allp = m.custom_vst_params
    assert len(allp) == 3
    assert [p.slot for p in allp] == [1, 3, 5]


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def test_validation_duplicate_slots() -> None:
    params = [
        InferenceParam(1, "A", "d", "continuous", 0, 1, 0.5, neutone_slot=1),
        InferenceParam(1, "B", "d", "continuous", 0, 1, 0.5, neutone_slot=2),
    ]
    with pytest.raises(ValueError, match="Duplicate slot"):
        ParamManifest(params=params)


def test_validation_too_many_params() -> None:
    params = [InferenceParam(i, f"P{i}", "d", "continuous", 0, 1, 0.5) for i in range(1, 18)]
    with pytest.raises(ValueError, match="Too many"):
        ParamManifest(params=params)


def test_validation_name_too_long() -> None:
    p = InferenceParam(1, "X" * 31, "d", "continuous", 0, 1, 0.5)
    with pytest.raises(ValueError, match="too long"):
        ParamManifest(params=[p])


def test_validation_invalid_neutone_slot() -> None:
    p = InferenceParam(1, "A", "d", "continuous", 0, 1, 0.5, neutone_slot=5)
    with pytest.raises(ValueError):
        ParamManifest(params=[p])


def test_validation_duplicate_neutone_slot() -> None:
    params = [
        InferenceParam(1, "A", "d", "continuous", 0, 1, 0.5, neutone_slot=1),
        InferenceParam(2, "B", "d", "continuous", 0, 1, 0.5, neutone_slot=1),
    ]
    with pytest.raises(ValueError, match="Duplicate neutone_slot"):
        ParamManifest(params=params)


def test_validation_valid_manifest_passes() -> None:
    m = ParamManifest(params=_standard_params())
    errs = validate_manifest(m)
    assert errs == []


def test_validation_raises_on_construct() -> None:
    bad = InferenceParam(1, "A", "d", "continuous", 0, 1, 0.5, neutone_slot=99)
    with pytest.raises(ValueError, match="Invalid"):
        ParamManifest(params=[bad])


# ---------------------------------------------------------------------------
# Tier-default builders — slot counts and neutone assignments
# ---------------------------------------------------------------------------


def test_standard_manifest_4_params_all_neutone() -> None:
    m = build_default_manifest("standard", {})
    assert len(m.params) == 4
    assert len(m.neutone_params) == 4
    assert m.neutone_params[0].name == "Pitch Shift"
    assert m.neutone_params[3].name == "Reverb Mix"


def test_component_manifest_6_params_4_neutone() -> None:
    m = build_default_manifest("component", {})
    assert len(m.params) == 6
    assert len(m.neutone_params) == 4
    assert m.params[2].name == "Harmonic Blend"
    assert m.params[5].name == "Spectral Spread"
    assert m.params[5].neutone_slot is None


def test_hacks_fm_manifest() -> None:
    m = build_default_manifest("hacks", {"fm_depth": 0.5})
    assert len(m.params) >= 4
    names = [p.name for p in m.params]
    assert "FM Depth" in names
    assert "FM Ratio" in names


def test_hacks_wavetable_manifest() -> None:
    m = build_default_manifest("hacks", {"wavetable_on": True})
    names = [p.name for p in m.params]
    assert "Wavetable Pos" in names
    assert "Phase Distort" in names


def test_hacks_pd_manifest() -> None:
    m = build_default_manifest("hacks", {"pd_k": 1.0})
    names = [p.name for p in m.params]
    assert "PD Amount" in names
    assert "Waveshape" in names


def test_hacks_fallback_standard() -> None:
    m = build_default_manifest("hacks", {})
    assert len(m.params) == 4
    assert len(m.neutone_params) == 4


def test_engine_newt_manifest() -> None:
    m = build_default_manifest("engine", {"engine": "newt"})
    names = [p.name for p in m.params]
    assert "Tone Character" in names
    assert "Saturation" in names
    assert "Odd Harmonics" in names


def test_engine_sinusoidal_manifest() -> None:
    m = build_default_manifest("engine", {"engine": "sinusoidal"})
    names = [p.name for p in m.params]
    assert "Inharmonicity" in names
    assert "Partial Density" in names


def test_engine_combsub_manifest() -> None:
    m = build_default_manifest("engine", {"engine": "combsub"})
    names = [p.name for p in m.params]
    assert "Formant Shift" in names
    assert "Vowel" in names


def test_engine_harmonic_is_standard() -> None:
    m = build_default_manifest("engine", {"engine": "harmonic"})
    assert len(m.params) >= 4
    assert m.params[0].name == "Pitch Shift"


def test_engine_unknown_fallback() -> None:
    m = build_default_manifest("engine", {"engine": "foobar"})
    assert len(m.params) == 4


def test_advanced_vae_manifest_reasonable() -> None:
    m = build_default_manifest("advanced", {"use_latent": True, "latent_dim": 8})
    assert 4 <= len(m.params) <= 16
    assert len(m.neutone_params) >= 2
    names = [p.name for p in m.params]
    assert "Timbre Z1" in names
    assert "Timbre Z6" in names


def test_advanced_poly_manifest() -> None:
    m = build_default_manifest("advanced", {"n_voices": 3})
    names = [p.name for p in m.params]
    assert "Voice Balance" in names
    assert "Detune" in names


def test_advanced_vc_manifest() -> None:
    m = build_default_manifest("advanced", {"use_content_encoder": True})
    names = [p.name for p in m.params]
    assert "Style Transfer" in names
    assert "Formant Scale" in names


def test_advanced_fallback_standard() -> None:
    m = build_default_manifest("advanced", {})
    assert len(m.params) == 4
    assert len(m.neutone_params) == 4


def test_unknown_tier_falls_back_to_standard() -> None:
    m = build_default_manifest("bogus", {})
    assert len(m.params) == 4
