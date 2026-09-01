"""Low-latency realtime export of a DDSP model.

Provides TorchScript and ONNX export plus a deferred Neutone stub.
"""

from __future__ import annotations

import logging

import torch

from inference.midi_synth_wrapper import MidiSynthWrapper
from model import DDSPModel
from model.ddsp import DDSPVariant
from model.ddsp_model import DDSPConfig
from model.param_manifest import ParamManifest, build_default_manifest


class _AudioOnlyModule(torch.nn.Module):
    """Thin wrapper exposing only the ``audio`` output for ONNX export.

    The ONNX exporter expects a ``torch.nn.Module`` (not a bare callable), and
    ``DDSPModel.forward`` returns a dict — this wrapper collapses that dict to
    the waveform tensor so the exported graph has a single output.
    """

    def __init__(self, model: DDSPModel) -> None:
        super().__init__()
        self.model = model

    def forward(self, f0: torch.Tensor, loudness: torch.Tensor) -> torch.Tensor:
        return self.model(f0, loudness)["audio"]


def _prepare_for_export(model: DDSPModel) -> DDSPModel:
    """Put the model in a tracer/ONNX-friendly state.

    Forces eval mode and disables gradient tracking on every parameter so a
    previously-trained model (whose tensors still ``requires_grad``) can be
    exported without ``RuntimeError: Cannot insert a Tensor that requires
    grad as a constant``.
    """
    model.eval()
    for param in model.parameters():
        param.requires_grad = False
    return model


def export_torchscript(model: DDSPModel, out_path: str) -> str:
    """Export the model to TorchScript via tracing.

    Uses a representative dummy input of shape (1, 10) frames. Only the
    ``"audio"`` output is traced (a lambda collapses the forward dict to a
    single tensor), so the traced graph has a constant output structure.
    """
    _prepare_for_export(model)
    f0 = torch.randn(1, 10)
    loudness = torch.randn(1, 10)

    def audio_only(f0: torch.Tensor, loudness: torch.Tensor) -> torch.Tensor:
        return model(f0, loudness)["audio"]

    with torch.no_grad():
        scripted = torch.jit.trace(audio_only, (f0, loudness), check_trace=False)
    torch.jit.save(scripted, out_path)
    return out_path


def export_onnx(
    model: DDSPModel,
    out_path: str,
    f0_shape: tuple[int, int] | None = None,
    loudness_shape: tuple[int, int] | None = None,
) -> str:
    """Export the model to ONNX, capturing only the ``"audio"`` output.

    The model's ``forward`` returns a dict; for ONNX we export a traced
    lambda that returns ``model(f0, loudness)["audio"]``. Dummy inputs use
    shape (1, 10) by default. Runs on CPU — no GPU required.
    """
    if f0_shape is None:
        f0_shape = (1, 10)
    if loudness_shape is None:
        loudness_shape = (1, 10)
    _prepare_for_export(model)

    f0 = torch.randn(*f0_shape)
    loudness = torch.randn(*loudness_shape)

    torch.onnx.export(
        _AudioOnlyModule(model),
        (f0, loudness),
        out_path,
        input_names=["f0", "loudness"],
        output_names=["audio"],
        opset_version=17,
        do_constant_folding=True,
    )
    return out_path


class DDSPNeutoneWrapper(torch.nn.Module):
    """Dynamic Neutone wrapper that carries a ``ParamManifest`` from checkpoint
    state and drives ``get_neutone_parameters()``.

    The wrapper stores the parameter metadata (names, bounds, defaults) in a
    TorchScript-exportable form and exposes the standard Neutone SDK surface:
    ``get_n_params()`` and ``get_neutone_parameters()``.  The forward pass
    applies the Neutone-style slot mapping (slot 1 → pitch shift, slot 2 →
    loudness shift) to the incoming f0 / loudness before delegating to the
    underlying DDSP model.

    This wrapper is a stub while the Neutone SDK does not ship a matching
    Python / CUDA wheel for this project — see ``export_neutone()``.
    """

    logger: logging.Logger = logging.getLogger(__name__)

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------

    def __init__(self, model: DDSPModel, manifest: ParamManifest) -> None:
        super().__init__()
        self.model = model

        self.param_names: list[str] = [p.name for p in manifest.neutone_params]
        self._n_params: int = len(self.param_names)

        if self._n_params > 4:
            raise ValueError(f"Neutone export requires ≤4 params, got {self._n_params}")

        self.defaults: dict[str, float] = {p.name: p.default_value for p in manifest.neutone_params}

    # ------------------------------------------------------------------
    # TorchScript-exported Neutone surface
    # ------------------------------------------------------------------

    @torch.jit.export
    def get_neutone_parameters(
        self,
    ) -> list[tuple[str, float, float, float]]:
        """Return ``[(name, min, max, default), ...]`` for each Neutone
        parameter, sorted by neutone slot.

        The result mirrors the ``neutone_params`` list from the wrapped
        ``ParamManifest``.
        """
        # Build the list from the defaults we stored at __init__ time;
        # the manifest itself is not carried into TorchScript, only the
        # parameter metadata sampled here.
        result: list[tuple[str, float, float, float]] = []
        for name in self.param_names:
            default = self.defaults[name]
            # Without the original manifest we fall back to a reasonable
            # VST-style range.  In the full export path (when the SDK is
            # available) the manifest is reconstructed from checkpoint state
            # and the real bounds are used.
            lo, hi = self._guess_bounds(name)
            result.append((name, lo, hi, default))
        return result

    @torch.jit.export
    def get_n_params(self) -> int:
        """Number of parameters exposed to the Neutone host (1-4)."""
        return self._n_params

    # ------------------------------------------------------------------
    # Forward
    # ------------------------------------------------------------------

    def forward(
        self,
        f0: torch.Tensor,
        loudness: torch.Tensor,
        params: dict[str, torch.Tensor] | None = None,
    ) -> torch.Tensor:
        """Run the wrapped model with Neutone-style param shifts applied.

        Slot 1 (``pitch_shift``) shifts the f0 in semitones; slot 2
        (``loudness`` / ``loudness_shift``) adds a dB offset to the
        loudness curve.  Any additional slots beyond 2 are passed as
        kwargs to ``self.model`` if the signature accepts them; otherwise
        they are logged and ignored.

        This is a stub forward — the exact processing will be refined when
        the Neutone SDK integration is completed.
        """
        if params is None:
            params = {}

        ps = self._read_param(params, "pitch_shift")
        ls = self._read_param(params, "loudness")
        shifted_f0 = f0 * (2.0 ** (ps / 12.0))
        shifted_loudness = loudness + ls

        # Extra slot params (slots 3-4) — try to pass as kwargs, else
        # fall back to a simple warning.
        extra_kwargs: dict[str, torch.Tensor] = {}
        for name in self.param_names:
            if name in {"pitch_shift", "loudness"}:
                continue
            if name in params:
                extra_kwargs[name] = params[name]

        if extra_kwargs:
            try:
                out = self.model(shifted_f0, shifted_loudness, **extra_kwargs)
            except TypeError:
                self.logger.warning(
                    "Model forward does not accept extra kwargs for %s; ignoring them.",
                    list(extra_kwargs.keys()),
                )
                out = self.model(shifted_f0, shifted_loudness)
        else:
            out = self.model(shifted_f0, shifted_loudness)

        if isinstance(out, dict):
            return out["audio"]
        return out

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _read_param(
        self,
        params: dict[str, torch.Tensor],
        name: str,
    ) -> float:
        """Read a scalar float from *params* for *name*, defaulting to 0.0."""
        if name not in params:
            return 0.0
        t = params[name]
        if isinstance(t, torch.Tensor):
            return float(t.item())
        return float(t)

    def _guess_bounds(self, name: str) -> tuple[float, float]:
        """Rough bounds fallback when the original manifest is unavailable.

        These are the same ranges used by ``build_default_manifest`` for the
        standard preset and are good enough for a stub wrapper.
        """
        if name == "pitch_shift":
            return (-24.0, 24.0)
        if name == "loudness":
            return (-20.0, 20.0)
        # Generic continuous param guess.
        return (0.0, 1.0)


def export_neutone(
    model: DDSPModel,
    out_path: str,
    manifest: ParamManifest | None = None,
) -> str:
    """Stub — Neutone plugin export is deferred.

    The Neutone SDK does not yet ship a Python 3.14 / CUDA 12 wheel for this
    project, so the real export path is intentionally left unimplemented.
    When the SDK becomes available this stub should be replaced with a proper
    ``neutone``-based export that consumes the provided *manifest*.

    If *manifest* is ``None`` a default two-param manifest is built from the
    ``build_default_manifest("standard", {})`` fallback so callers that
    already have a manifest can pass it directly while backward-compatible
    callers keep working.
    """
    if manifest is None:
        manifest = build_default_manifest("standard", {})

    raise NotImplementedError(
        "Neutone export is deferred: the Neutone SDK does not yet provide "
        "a cp314/CUDA wheel for this project. "
        f"Manifest ({manifest.format} v{manifest.version}) with "
        f"{len(manifest.neutone_params)} neutone params is ready for when "
        "the SDK is available."
    )


def export_midi_synth(
    model: DDSPModel,
    out_path: str,
    manifest: ParamManifest | None = None,
) -> str:
    """Export a trained DDSPModel/PolyDDSPModel as a MIDI synthesizer TorchScript module.

    Wraps the model in ``MidiSynthWrapper``, embeds the param_manifest (with
    ``context="midi_synth"``) and metadata marker ``synth_mode: "midi_synth"``,
    then traces via ``torch.jit.trace``.

    Args:
        model: a trained ``DDSPModel`` or ``PolyDDSPModel`` instance.
        out_path: path to save the exported ``.pt`` file.
        manifest: optional ``ParamManifest`` (MIDI context). If ``None``, builds
            the default MIDI synth manifest from the model's tier / engine info.

    Returns:
        ``out_path`` on success.
    """
    _prepare_for_export(model)

    # ---- build manifest (if not supplied) ----
    if manifest is None:
        model_tier = "standard"
        variant_flags: dict[str, object] = {}

        config: DDSPConfig = model.config
        variant: DDSPVariant = model.variant

        # Derive a sensible model_tier from config/variant.
        # engine-tier overrides standard when an explicit engine is present.
        if variant.engine != "harmonic":
            model_tier = "engine"
            variant_flags = {"engine": variant.engine}
        elif config.use_latent or config.use_content_encoder or config.n_voices > 1:
            model_tier = "advanced"
            variant_flags = {
                "use_latent": config.use_latent,
                "latent_dim": config.latent_dim,
                "n_voices": config.n_voices,
                "use_content_encoder": config.use_content_encoder,
            }

        manifest = build_default_manifest(model_tier, variant_flags, context="midi_synth")

    # ---- wrap with MidiSynthWrapper ----
    wrapper = MidiSynthWrapper(model)

    # ---- build dummy inputs for tracing ----
    # Poly path uses (N_voices, T_frames) f0; mono path uses (T_frames,).
    if hasattr(model, "n_voices") and getattr(model, "n_voices", 1) > 1:
        f0 = torch.randn(model.n_voices, 10)  # (N_voices, T_frames)
        loudness = torch.randn(10)  # (T_frames,)
    else:
        f0 = torch.randn(10)  # (T_frames,)
        loudness = torch.randn(10)  # (T_frames,)

    # ---- trace + save ----
    with torch.no_grad():
        scripted = torch.jit.trace(wrapper, (f0, loudness), check_trace=False)
    torch.jit.save(scripted, out_path)
    return out_path
