"""Parameter manifest dataclasses, validation, and tier-default builders.

Pure Python + stdlib dataclasses. No torch dependency: this module carries
metadata only and is imported by trainer.py, server/routes/model.py,
inference/export.py, etc.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------


@dataclass
class InferenceParam:
    """One VST-style parameter exposed by an inference preset.

    Names <= 30 chars, descriptions <= 150 chars. ``neutone_slot`` is 1-4 or
    None (unused slots are reserved for future extension).
    """

    slot: int
    name: str
    description: str
    param_type: str
    min_value: float
    max_value: float
    default_value: float
    mapping: str = "linear"
    unit_hint: str = ""
    group: str = ""
    neutone_slot: int | None = None

    def __post_init__(self) -> None:
        """Defensive normalisation (not a full validation — use validate_manifest)."""
        self.name = self.name.strip()
        self.description = self.description.strip()
        self.param_type = self.param_type.strip()
        self.mapping = self.mapping.strip()
        self.unit_hint = self.unit_hint.strip()
        self.group = self.group.strip()


@dataclass
class ParamManifest:
    """A complete parameter manifest for a single model tier / variant.

    Validated in ``__post_init__``: unique slots, <= 16 total, unique and
    in-range neutone_slots, name/description length bounds.
    """

    format: str = "wogd-vst-params"
    version: str = "1.0"
    params: list[InferenceParam] = field(default_factory=list)

    def __post_init__(self) -> None:
        errors = validate_manifest(self)
        if errors:
            raise ValueError("Invalid ParamManifest: " + "; ".join(errors))

    @property
    def neutone_params(self) -> list[InferenceParam]:
        """Params bound to a Neutone slot, sorted by slot ascending."""
        return sorted(
            [p for p in self.params if p.neutone_slot is not None],
            key=lambda p: p.neutone_slot,
        )

    @property
    def custom_vst_params(self) -> list[InferenceParam]:
        """All params sorted by slot ascending."""
        return sorted(self.params, key=lambda p: p.slot)

    def to_dict(self) -> dict[str, Any]:
        """Plain-dict serialisation suitable for JSON / cache storage."""
        return {
            "format": self.format,
            "version": self.version,
            "params": [p.__dict__ for p in self.params],  # type: ignore[attr-defined]
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> ParamManifest:
        """Deserialize from a dict previously produced by ``to_dict()``."""
        params = [
            InferenceParam(
                slot=int(p["slot"]),
                name=str(p["name"]),
                description=str(p["description"]),
                param_type=str(p["param_type"]),
                min_value=float(p["min_value"]),
                max_value=float(p["max_value"]),
                default_value=float(p["default_value"]),
                mapping=str(p.get("mapping", "linear")),
                unit_hint=str(p.get("unit_hint", "")),
                group=str(p.get("group", "")),
                neutone_slot=None if p.get("neutone_slot") is None else int(p["neutone_slot"]),
            )
            for p in d.get("params", [])
        ]
        return cls(
            format=str(d.get("format", "wogd-vst-params")),
            version=str(d.get("version", "1.0")),
            params=params,
        )


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

VALID_PARAM_TYPES = frozenset({"continuous", "categorical"})
VALID_MAPPINGS = frozenset({"linear", "log", "exp"})
VALID_NEUTONE_SLOTS = frozenset({1, 2, 3, 4})
MAX_PARAMS = 16


def validate_manifest(m: ParamManifest) -> list[str]:
    """Return a list of error strings (empty == valid).

    Checks: <= 16 params, unique slots, valid neutone_slots (unique and in
    {1,2,3,4}), name length <= 30, description length <= 150, valid
    param_type, valid mapping.
    """
    errors: list[str] = []

    if len(m.params) > MAX_PARAMS:
        errors.append(f"Too many params: {len(m.params)} > {MAX_PARAMS}")

    seen_slots: set[int] = set()
    neutone_values: list[int] = []

    for p in m.params:
        if p.name and len(p.name) > 30:
            errors.append(f"Param name too long ({len(p.name)}>30): {p.name!r}")
        if p.description and len(p.description) > 150:
            errors.append(f"Param description too long ({len(p.description)}>150): {p.name!r}")
        if p.param_type not in VALID_PARAM_TYPES:
            errors.append(f"Invalid param_type {p.param_type!r} for {p.name!r}")
        if p.mapping not in VALID_MAPPINGS:
            errors.append(f"Invalid mapping {p.mapping!r} for {p.name!r}")
        if p.slot in seen_slots:
            errors.append(f"Duplicate slot {p.slot} for {p.name!r}")
        seen_slots.add(p.slot)

        if p.neutone_slot is not None:
            if p.neutone_slot not in VALID_NEUTONE_SLOTS:
                errors.append(
                    f"Invalid neutone_slot {p.neutone_slot!r} for {p.name!r} (must be 1-4)"
                )
            neutone_values.append(p.neutone_slot)

    # unique neutone_slots
    if len(neutone_values) != len(set(neutone_values)):
        seen_neutone: dict[int, list[str]] = {}
        for p in m.params:
            if p.neutone_slot is not None:
                seen_neutone.setdefault(p.neutone_slot, []).append(p.name)
        for slot, names in seen_neutone.items():
            if len(names) > 1:
                errors.append(f"Duplicate neutone_slot {slot} on: {', '.join(names)}")

    return errors


# ---------------------------------------------------------------------------
# Tier-default builder helpers
# ---------------------------------------------------------------------------


def _param(  # noqa: D104
    slot: int,
    name: str,
    description: str,
    param_type: str,
    min_value: float,
    max_value: float,
    default_value: float,
    *,
    mapping: str = "linear",
    unit_hint: str = "",
    group: str = "",
    neutone_slot: int | None = None,
) -> InferenceParam:
    return InferenceParam(
        slot=slot,
        name=name,
        description=description,
        param_type=param_type,
        min_value=min_value,
        max_value=max_value,
        default_value=default_value,
        mapping=mapping,
        unit_hint=unit_hint,
        group=group,
        neutone_slot=neutone_slot,
    )


def _standard_manifest() -> ParamManifest:
    """4-param standard preset, all bound to Neutone slots 1-4."""
    return ParamManifest(
        format="wogd-vst-params",
        version="1.0",
        params=[
            _param(
                1,
                "Pitch Shift",
                "Pitch transposition in semitones",
                "continuous",
                -24.0,
                24.0,
                0.0,
                mapping="linear",
                unit_hint="semitones",
                group="Pitch",
                neutone_slot=1,
            ),
            _param(
                2,
                "Loudness",
                "Output level adjustment",
                "continuous",
                -20.0,
                20.0,
                0.0,
                mapping="linear",
                unit_hint="dB",
                group="Loudness",
                neutone_slot=2,
            ),
            _param(
                3,
                "Noise Level",
                "Background noise mix",
                "continuous",
                0.0,
                1.0,
                0.5,
                mapping="linear",
                unit_hint="",
                group="Texture",
                neutone_slot=3,
            ),
            _param(
                4,
                "Reverb Mix",
                "Reverb wet/dry blend",
                "continuous",
                0.0,
                1.0,
                0.3,
                mapping="linear",
                unit_hint="",
                group="Reverb",
                neutone_slot=4,
            ),
        ],
    )


def _component_manifest() -> ParamManifest:
    """6-param component preset: 4 neutone slots on P1-P4, P5/P6 unmapped."""
    return ParamManifest(
        format="wogd-vst-params",
        version="1.0",
        params=[
            _param(
                1,
                "Pitch Shift",
                "Pitch transposition in semitones",
                "continuous",
                -24.0,
                24.0,
                0.0,
                mapping="linear",
                unit_hint="semitones",
                group="Pitch",
                neutone_slot=1,
            ),
            _param(
                2,
                "Loudness",
                "Output level adjustment",
                "continuous",
                -20.0,
                20.0,
                0.0,
                mapping="linear",
                unit_hint="dB",
                group="Loudness",
                neutone_slot=2,
            ),
            _param(
                3,
                "Harmonic Blend",
                "Harmonic vs noise balance",
                "continuous",
                0.0,
                1.0,
                0.5,
                mapping="linear",
                unit_hint="",
                group="Texture",
                neutone_slot=3,
            ),
            _param(
                4,
                "Noise Blend",
                "Noise texture intensity",
                "continuous",
                0.0,
                1.0,
                0.5,
                mapping="linear",
                unit_hint="",
                group="Texture",
                neutone_slot=4,
            ),
            _param(
                5,
                "Reverb Mix",
                "Reverb wet/dry blend",
                "continuous",
                0.0,
                1.0,
                0.3,
                mapping="linear",
                unit_hint="",
                group="Reverb",
                neutone_slot=None,
            ),
            _param(
                6,
                "Spectral Spread",
                "Spectral width of partials",
                "continuous",
                0.0,
                1.0,
                0.5,
                mapping="linear",
                unit_hint="",
                group="Texture",
                neutone_slot=None,
            ),
        ],
    )


def _fm_hacks_manifest() -> ParamManifest:
    """Hacks variant: FM preset (6 params, P1/P2 neutone, P3-P6 unmapped)."""
    return ParamManifest(
        format="wogd-vst-params",
        version="1.0",
        params=[
            _param(
                1,
                "Pitch Shift",
                "Pitch transposition in semitones",
                "continuous",
                -24.0,
                24.0,
                0.0,
                mapping="linear",
                unit_hint="semitones",
                group="Pitch",
                neutone_slot=1,
            ),
            _param(
                2,
                "Loudness",
                "Output level adjustment",
                "continuous",
                -20.0,
                20.0,
                0.0,
                mapping="linear",
                unit_hint="dB",
                group="Loudness",
                neutone_slot=2,
            ),
            _param(
                3,
                "FM Depth",
                "FM modulation depth",
                "continuous",
                0.0,
                1.0,
                0.3,
                mapping="linear",
                unit_hint="",
                group="FM",
                neutone_slot=None,
            ),
            _param(
                4,
                "FM Ratio",
                "FM operator frequency ratio",
                "continuous",
                0.5,
                4.0,
                2.0,
                mapping="log",
                unit_hint="",
                group="FM",
                neutone_slot=None,
            ),
            _param(
                5,
                "LFO Rate",
                "LFO modulation rate",
                "continuous",
                0.0,
                10.0,
                1.0,
                mapping="linear",
                unit_hint="Hz",
                group="Modulation",
                neutone_slot=None,
            ),
            _param(
                6,
                "LFO Depth",
                "LFO modulation depth",
                "continuous",
                0.0,
                1.0,
                0.5,
                mapping="linear",
                unit_hint="",
                group="Modulation",
                neutone_slot=None,
            ),
        ],
    )


def _wt_hacks_manifest() -> ParamManifest:
    """Hacks variant: Wavetable preset (6 params, P1/P2 neutone, P3-P6 unmapped)."""
    return ParamManifest(
        format="wogd-vst-params",
        version="1.0",
        params=[
            _param(
                1,
                "Pitch Shift",
                "Pitch transposition in semitones",
                "continuous",
                -24.0,
                24.0,
                0.0,
                mapping="linear",
                unit_hint="semitones",
                group="Pitch",
                neutone_slot=1,
            ),
            _param(
                2,
                "Loudness",
                "Output level adjustment",
                "continuous",
                -20.0,
                20.0,
                0.0,
                mapping="linear",
                unit_hint="dB",
                group="Loudness",
                neutone_slot=2,
            ),
            _param(
                3,
                "Wavetable Pos",
                "Wavetable scan position",
                "continuous",
                0.0,
                1.0,
                0.5,
                mapping="linear",
                unit_hint="",
                group="Texture",
                neutone_slot=None,
            ),
            _param(
                4,
                "Noise Level",
                "Background noise mix",
                "continuous",
                0.0,
                1.0,
                0.3,
                mapping="linear",
                unit_hint="",
                group="Texture",
                neutone_slot=None,
            ),
            _param(
                5,
                "Phase Distort",
                "Phase distortion intensity",
                "continuous",
                0.0,
                1.0,
                0.0,
                mapping="linear",
                unit_hint="",
                group="Texture",
                neutone_slot=None,
            ),
            _param(
                6,
                "Harmonic Dirt",
                "Harmonic saturation dirt",
                "continuous",
                0.0,
                1.0,
                0.5,
                mapping="linear",
                unit_hint="",
                group="Texture",
                neutone_slot=None,
            ),
        ],
    )


def _pd_hacks_manifest() -> ParamManifest:
    """Hacks variant: Phase Distortion preset (6 params, P1/P2 neutone, P3/P4 neutone)."""
    return ParamManifest(
        format="wogd-vst-params",
        version="1.0",
        params=[
            _param(
                1,
                "Pitch Shift",
                "Pitch transposition in semitones",
                "continuous",
                -24.0,
                24.0,
                0.0,
                mapping="linear",
                unit_hint="semitones",
                group="Pitch",
                neutone_slot=1,
            ),
            _param(
                2,
                "Loudness",
                "Output level adjustment",
                "continuous",
                -20.0,
                20.0,
                0.0,
                mapping="linear",
                unit_hint="dB",
                group="Loudness",
                neutone_slot=2,
            ),
            _param(
                3,
                "PD Amount",
                "Phase distortion amount",
                "continuous",
                0.0,
                1.0,
                0.5,
                mapping="linear",
                unit_hint="",
                group="Texture",
                neutone_slot=3,
            ),
            _param(
                4,
                "Waveshape",
                "Waveshaping intensity",
                "continuous",
                0.0,
                1.0,
                0.5,
                mapping="linear",
                unit_hint="",
                group="Texture",
                neutone_slot=4,
            ),
        ],
    )


def _engine_manifest(engine: str) -> ParamManifest:
    """Engine-variant preset: 6 params, P1/P2 neutone, P3/P4 neutone, P5/P6 unmapped."""
    engines: dict[str, list[InferenceParam]] = {
        "harmonic": [
            _param(
                1,
                "Pitch Shift",
                "Pitch transposition in semitones",
                "continuous",
                -24.0,
                24.0,
                0.0,
                mapping="linear",
                unit_hint="semitones",
                group="Pitch",
                neutone_slot=1,
            ),
            _param(
                2,
                "Loudness",
                "Output level adjustment",
                "continuous",
                -20.0,
                20.0,
                0.0,
                mapping="linear",
                unit_hint="dB",
                group="Loudness",
                neutone_slot=2,
            ),
            _param(
                3,
                "Harmonic Blend",
                "Harmonic vs noise balance",
                "continuous",
                0.0,
                1.0,
                0.5,
                mapping="linear",
                unit_hint="",
                group="Texture",
                neutone_slot=3,
            ),
            _param(
                4,
                "Noise Blend",
                "Noise texture intensity",
                "continuous",
                0.0,
                1.0,
                0.5,
                mapping="linear",
                unit_hint="",
                group="Texture",
                neutone_slot=4,
            ),
            _param(
                5,
                "Spectral Spread",
                "Spectral width of partials",
                "continuous",
                0.0,
                1.0,
                0.5,
                mapping="linear",
                unit_hint="",
                group="Texture",
                neutone_slot=None,
            ),
            _param(
                6,
                "Brightness",
                "High-frequency brightness",
                "continuous",
                0.0,
                1.0,
                0.5,
                mapping="linear",
                unit_hint="",
                group="Texture",
                neutone_slot=None,
            ),
        ],
        "sinusoidal": [
            _param(
                1,
                "Pitch Shift",
                "Pitch transposition in semitones",
                "continuous",
                -24.0,
                24.0,
                0.0,
                mapping="linear",
                unit_hint="semitones",
                group="Pitch",
                neutone_slot=1,
            ),
            _param(
                2,
                "Loudness",
                "Output level adjustment",
                "continuous",
                -20.0,
                20.0,
                0.0,
                mapping="linear",
                unit_hint="dB",
                group="Loudness",
                neutone_slot=2,
            ),
            _param(
                3,
                "Inharmonicity",
                "Inharmonic partial deviation",
                "continuous",
                0.0,
                1.0,
                0.0,
                mapping="linear",
                unit_hint="",
                group="Texture",
                neutone_slot=3,
            ),
            _param(
                4,
                "Spectral Spread",
                "Spectral width of partials",
                "continuous",
                0.0,
                1.0,
                0.5,
                mapping="linear",
                unit_hint="",
                group="Texture",
                neutone_slot=4,
            ),
            _param(
                5,
                "Partial Density",
                "Density of generated partials",
                "continuous",
                0.5,
                1.0,
                0.8,
                mapping="linear",
                unit_hint="",
                group="Texture",
                neutone_slot=None,
            ),
            _param(
                6,
                "Brightness",
                "High-frequency brightness",
                "continuous",
                0.0,
                1.0,
                0.5,
                mapping="linear",
                unit_hint="",
                group="Texture",
                neutone_slot=None,
            ),
        ],
        "combsub": [
            _param(
                1,
                "Pitch Shift",
                "Pitch transposition in semitones",
                "continuous",
                -24.0,
                24.0,
                0.0,
                mapping="linear",
                unit_hint="semitones",
                group="Pitch",
                neutone_slot=1,
            ),
            _param(
                2,
                "Loudness",
                "Output level adjustment",
                "continuous",
                -20.0,
                20.0,
                0.0,
                mapping="linear",
                unit_hint="dB",
                group="Loudness",
                neutone_slot=2,
            ),
            _param(
                3,
                "Formant Shift",
                "Formant frequency shift",
                "continuous",
                -12.0,
                12.0,
                0.0,
                mapping="linear",
                unit_hint="semitones",
                group="Formant",
                neutone_slot=3,
            ),
            _param(
                4,
                "Brightness",
                "High-frequency brightness",
                "continuous",
                0.0,
                1.0,
                0.5,
                mapping="linear",
                unit_hint="",
                group="Texture",
                neutone_slot=4,
            ),
            _param(
                5,
                "Vowel",
                "Vowel formant position",
                "continuous",
                0.0,
                1.0,
                0.5,
                mapping="linear",
                unit_hint="",
                group="Formant",
                neutone_slot=None,
            ),
            _param(
                6,
                "Roughness",
                "Subband roughness modulation",
                "continuous",
                0.0,
                1.0,
                0.0,
                mapping="linear",
                unit_hint="",
                group="Texture",
                neutone_slot=None,
            ),
        ],
        "newt": [
            _param(
                1,
                "Pitch Shift",
                "Pitch transposition in semitones",
                "continuous",
                -24.0,
                24.0,
                0.0,
                mapping="linear",
                unit_hint="semitones",
                group="Pitch",
                neutone_slot=1,
            ),
            _param(
                2,
                "Loudness",
                "Output level adjustment",
                "continuous",
                -20.0,
                20.0,
                0.0,
                mapping="linear",
                unit_hint="dB",
                group="Loudness",
                neutone_slot=2,
            ),
            _param(
                3,
                "Tone Character",
                "Neural tone character blend",
                "continuous",
                0.0,
                1.0,
                0.5,
                mapping="linear",
                unit_hint="",
                group="Texture",
                neutone_slot=3,
            ),
            _param(
                4,
                "Saturation",
                "Neural saturation intensity",
                "continuous",
                0.0,
                1.0,
                0.5,
                mapping="linear",
                unit_hint="",
                group="Texture",
                neutone_slot=4,
            ),
            _param(
                5,
                "MLP Layer Bias",
                "Hidden layer bias offset",
                "continuous",
                0.0,
                1.0,
                0.5,
                mapping="linear",
                unit_hint="",
                group="Texture",
                neutone_slot=None,
            ),
            _param(
                6,
                "Odd Harmonics",
                "Odd-harmonic emphasis",
                "continuous",
                0.0,
                1.0,
                0.5,
                mapping="linear",
                unit_hint="",
                group="Texture",
                neutone_slot=None,
            ),
        ],
    }
    if engine not in engines:
        raise ValueError(f"Unknown engine variant: {engine!r}")
    return ParamManifest(
        format="wogd-vst-params",
        version="1.0",
        params=engines[engine],
    )


def _advanced_manifest(
    variant_flags: dict[str, Any] | None = None,
) -> ParamManifest:
    """Advanced-tier preset driven by variant_flags.

    Fallback: standard 4-param manifest. Otherwise builds one of:
    - ``use_latent`` with ``latent_dim``: P1/P2 neutone, P3/P4 neutone,
      P5..P(D) timbre latent dims unmapped (capped at 16 total).
    - ``n_voices >= 2``: voice modulation preset (6 params, P1/P2 neutone,
      P3/P4 neutone, P5/P6 unmapped).
    - ``use_content_encoder``: voice conversion preset (6 params, P1/P2
      neutone, P3/P4 neutone, P5/P6 unmapped).
    """
    flags = variant_flags or {}
    use_latent = bool(flags.get("use_latent"))
    latent_dim = int(flags.get("latent_dim", 0))
    n_voices = int(flags.get("n_voices", 1))
    use_content_encoder = bool(flags.get("use_content_encoder"))

    if use_latent and latent_dim >= 2:
        # P1/P2 neutone, P3/P4 neutone, P5..P(latent_dim) unmapped.
        total = min(latent_dim + 2, MAX_PARAMS)  # 2 base + latent dims
        params: list[InferenceParam] = [
            _param(
                1,
                "Pitch Shift",
                "Pitch transposition in semitones",
                "continuous",
                -24.0,
                24.0,
                0.0,
                mapping="linear",
                unit_hint="semitones",
                group="Pitch",
                neutone_slot=1,
            ),
            _param(
                2,
                "Loudness",
                "Output level adjustment",
                "continuous",
                -20.0,
                20.0,
                0.0,
                mapping="linear",
                unit_hint="dB",
                group="Loudness",
                neutone_slot=2,
            ),
            _param(
                3,
                "Timbre Z1",
                "First latent timbre axis",
                "continuous",
                0.0,
                1.0,
                0.5,
                mapping="linear",
                unit_hint="",
                group="Timbre",
                neutone_slot=3,
            ),
            _param(
                4,
                "Timbre Z2",
                "Second latent timbre axis",
                "continuous",
                0.0,
                1.0,
                0.5,
                mapping="linear",
                unit_hint="",
                group="Timbre",
                neutone_slot=4,
            ),
        ]
        for i in range(5, total + 1):
            idx = i - 4  # latent index 3,4,5,...
            params.append(
                _param(
                    i,
                    f"Timbre Z{idx}",
                    f"Latent timbre axis {idx}",
                    "continuous",
                    0.0,
                    1.0,
                    0.5,
                    mapping="linear",
                    unit_hint="",
                    group="Timbre",
                    neutone_slot=None,
                )
            )
        return ParamManifest(
            format="wogd-vst-params",
            version="1.0",
            params=params,
        )

    if n_voices >= 2:
        return ParamManifest(
            format="wogd-vst-params",
            version="1.0",
            params=[
                _param(
                    1,
                    "Pitch Shift",
                    "Pitch transposition in semitones",
                    "continuous",
                    -24.0,
                    24.0,
                    0.0,
                    mapping="linear",
                    unit_hint="semitones",
                    group="Pitch",
                    neutone_slot=1,
                ),
                _param(
                    2,
                    "Loudness",
                    "Output level adjustment",
                    "continuous",
                    -20.0,
                    20.0,
                    0.0,
                    mapping="linear",
                    unit_hint="dB",
                    group="Loudness",
                    neutone_slot=2,
                ),
                _param(
                    3,
                    "Voice Balance",
                    "Balance between voices",
                    "continuous",
                    0.0,
                    1.0,
                    0.5,
                    mapping="linear",
                    unit_hint="",
                    group="Poly",
                    neutone_slot=3,
                ),
                _param(
                    4,
                    "Detune",
                    "Voice detuning in cents",
                    "continuous",
                    -50.0,
                    50.0,
                    0.0,
                    mapping="linear",
                    unit_hint="cts",
                    group="Poly",
                    neutone_slot=4,
                ),
                _param(
                    5,
                    "Voice Spread",
                    "Voice spatial spread",
                    "continuous",
                    0.0,
                    1.0,
                    0.5,
                    mapping="linear",
                    unit_hint="",
                    group="Poly",
                    neutone_slot=None,
                ),
                _param(
                    6,
                    "Unison Width",
                    "Unison detune width",
                    "continuous",
                    0.0,
                    1.0,
                    0.3,
                    mapping="linear",
                    unit_hint="",
                    group="Poly",
                    neutone_slot=None,
                ),
            ],
        )

    if use_content_encoder:
        return ParamManifest(
            format="wogd-vst-params",
            version="1.0",
            params=[
                _param(
                    1,
                    "Pitch Shift",
                    "Pitch transposition in semitones",
                    "continuous",
                    -24.0,
                    24.0,
                    0.0,
                    mapping="linear",
                    unit_hint="semitones",
                    group="Pitch",
                    neutone_slot=1,
                ),
                _param(
                    2,
                    "Loudness",
                    "Output level adjustment",
                    "continuous",
                    -20.0,
                    20.0,
                    0.0,
                    mapping="linear",
                    unit_hint="dB",
                    group="Loudness",
                    neutone_slot=2,
                ),
                _param(
                    3,
                    "Style Transfer",
                    "Voice conversion style intensity",
                    "continuous",
                    0.0,
                    1.0,
                    0.5,
                    mapping="linear",
                    unit_hint="",
                    group="VC",
                    neutone_slot=3,
                ),
                _param(
                    4,
                    "Formant Scale",
                    "Formant scaling factor",
                    "continuous",
                    0.5,
                    1.5,
                    1.0,
                    mapping="log",
                    unit_hint="",
                    group="VC",
                    neutone_slot=4,
                ),
                _param(
                    5,
                    "Breathiness",
                    "Breathiness injection",
                    "continuous",
                    0.0,
                    1.0,
                    0.0,
                    mapping="linear",
                    unit_hint="",
                    group="VC",
                    neutone_slot=None,
                ),
                _param(
                    6,
                    "Speaker Blend",
                    "Speaker identity blend",
                    "continuous",
                    0.0,
                    1.0,
                    0.5,
                    mapping="linear",
                    unit_hint="",
                    group="VC",
                    neutone_slot=None,
                ),
            ],
        )

    return _standard_manifest()


# ---------------------------------------------------------------------------
# Public entrypoint
# ---------------------------------------------------------------------------

_TIER_FACTORIES: dict[str, Any] = {
    "standard": _standard_manifest,
    "component": _component_manifest,
    "hacks": None,  # special-cased below (variant_flags dependent)
    "engine": None,  # special-cased below (variant_flags dependent)
    "advanced": _advanced_manifest,
}


def build_default_manifest(
    model_tier: str,
    variant_flags: dict[str, Any] | None = None,
) -> ParamManifest:
    """Build the default ParamManifest for *model_tier*.

    Dispatches to the correct private factory. Unknown tiers fall back to the
    standard 4-param manifest.

    *variant_flags* is consumed by ``hacks``, ``engine``, and ``advanced``
    tiers (see the private builders for available keys).
    """
    tier = (model_tier or "").strip().lower()

    if tier == "standard":
        return _standard_manifest()
    if tier == "component":
        return _component_manifest()
    if tier == "hacks":
        flags = variant_flags or {}
        fm_depth = float(flags.get("fm_depth", 0))
        wavetable_on = bool(flags.get("wavetable_on", False))
        pd_k = float(flags.get("pd_k", 0))

        if fm_depth and fm_depth > 0:
            return _fm_hacks_manifest()
        if wavetable_on:
            return _wt_hacks_manifest()
        if pd_k > 0:
            return _pd_hacks_manifest()
        return _standard_manifest()

    if tier == "engine":
        flags = variant_flags or {}
        engine = str(flags.get("engine", "harmonic"))
        try:
            return _engine_manifest(engine)
        except ValueError:
            return _standard_manifest()

    if tier == "advanced":
        return _advanced_manifest(variant_flags)

    # Unknown tier -> fallback.
    return _standard_manifest()
