"""Custom VST export for the WOGD DDSP trainer.

Produces a TorchScript-compiled ``.pt`` file that a custom VST plugin can load
at runtime. The exported artifact contains:

- A scripted ``CustomVSTWrapper`` around a ``DDSPModel`` that exposes
  ``forward(f0, loudness) -> audio``.
- A JSON-encoded ``ParamManifest`` embedded as a plain-string buffer so the
  plugin can read parameter metadata (name, range, default, Neutone slot, etc.)
  without needing the Python ``model.param_manifest`` module at plugin-build
  time.

The wrapper enforces the Custom VST constraint of **≤ 16 exposed parameters**
at construction time and raises ``ValueError`` otherwise. Old checkpoints that
do not carry a ``param_manifest`` entry still work: a default manifest is built
from the saved model tier and variant flags.
"""

from __future__ import annotations

import json

import torch
import torch.nn as nn

from model.ddsp_model import DDSPConfig, DDSPModel
from model.param_manifest import ParamManifest, build_default_manifest


class CustomVSTWrapper(nn.Module):
    """Wrapper that bundles a DDSPModel with a ParamManifest.

    The forward pass delegates to the model. The manifest is stored as a
    plain Python attribute and serialised into the checkpoint state so it
    survives save/load round-trips.
    """

    def __init__(self, model: nn.Module, manifest: ParamManifest) -> None:
        super().__init__()
        self.model = model
        self._n_params = len(manifest.params)
        if self._n_params > 16:
            raise ValueError(f"Custom VST supports ≤16 params, got {self._n_params}")
        self.param_manifest_json = json.dumps(manifest.to_dict())

    def forward(self, f0: torch.Tensor, loudness: torch.Tensor) -> torch.Tensor:
        return self.model(f0, loudness)["audio"]

    def get_param_manifest_json(self) -> str:
        return self.param_manifest_json

    def get_n_params(self) -> int:
        return self._n_params


def export_custom_vst(checkpoint_path: str, output_path: str) -> str:
    state = torch.load(checkpoint_path, map_location="cpu", weights_only=False)

    if "param_manifest" in state:
        manifest = ParamManifest.from_dict(state["param_manifest"])
    else:
        manifest = build_default_manifest(
            state.get("model_tier", "standard"),
            state.get("variant_flags", {}),
        )

    config = state["config"]
    if isinstance(config, dict):
        config = DDSPConfig(**config)
    _variant = getattr(config, "variant", None)
    model = DDSPModel(config=config, variant=_variant)
    if "model_state_dict" in state:
        model.load_state_dict(state["model_state_dict"])
    model.eval()

    wrapper = CustomVSTWrapper(model, manifest)

    f0 = torch.randn(1, 10)
    loudness = torch.randn(1, 10)
    with torch.no_grad():
        scripted = torch.jit.trace(wrapper, (f0, loudness), check_trace=False)
    torch.jit.save(scripted, output_path)
    return output_path
