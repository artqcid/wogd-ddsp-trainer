"""Low-latency realtime export of a DDSP model.

Provides TorchScript and ONNX export plus a deferred Neutone stub.
"""

from __future__ import annotations

import torch

from model import DDSPModel


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


def export_neutone(model: DDSPModel, out_path: str) -> str:
    """Stub — Neutone plugin export is deferred.

    The Neutone SDK does not yet ship a Python 3.14 / CUDA 12 wheel for this
    project, so the real export path is intentionally left unimplemented. When
    the SDK becomes available this stub should be replaced with a proper
    ``neutone``-based export.
    """
    raise NotImplementedError(
        "Neutone export is deferred: the Neutone SDK does not yet provide "
        "a cp314/CUDA wheel for this project."
    )
