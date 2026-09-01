import torch
import torch.nn as nn
import torch.nn.functional as F
from torch import Tensor


class SawtoothExciter(nn.Module):
    """Deterministic sawtooth oscillator at f0. No learnable parameters."""

    def forward(
        self,
        f0: Tensor,
        sample_rate: int,
        hop_length: int,
    ) -> Tensor:
        B, T_frames = f0.shape
        T_audio = (T_frames - 1) * hop_length + 1

        phase_inc = f0 / sample_rate
        phase_per_frame = phase_inc * hop_length
        phase_frames = torch.cumsum(phase_per_frame, dim=1) % 1.0

        phase_audio = F.interpolate(
            phase_frames.unsqueeze(1), size=T_audio, mode="linear", align_corners=False
        ).squeeze(1)

        return 2.0 * (phase_audio % 1.0) - 1.0


class NEWTUnit(nn.Module):
    def __init__(self, n_hidden: int = 32, n_layers: int = 4) -> None:
        super().__init__()
        layers = [nn.Linear(1, n_hidden)]
        for _ in range(n_layers - 1):
            layers.append(nn.Linear(n_hidden, n_hidden))
        layers.append(nn.Linear(n_hidden, 1))
        self.layers = nn.ModuleList(layers)
        self._init_weights()

    def _init_weights(self) -> None:
        nn.init.uniform_(self.layers[0].weight, -torch.pi, torch.pi)
        for layer in self.layers[1:-1]:
            fan_in = layer.weight.shape[1]
            bound = 1.0 / fan_in**0.5
            nn.init.uniform_(layer.weight, -bound, bound)

    def forward(
        self,
        excitation: Tensor,
        gain: Tensor,
        bias: Tensor,
    ) -> Tensor:
        x = excitation * gain + bias
        x = x.unsqueeze(-1)
        for layer in self.layers[:-1]:
            x = torch.sin(layer(x))
        x = torch.tanh(self.layers[-1](x))
        return x.squeeze(-1)
