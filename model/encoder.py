import torch
import torch.nn as nn
from torch import Tensor


class GRUEncoder(nn.Module):
    """Maps per-frame (f0, loudness) features to a Gaussian latent distribution.

    Returns (mu, logvar) for the reparameterisation trick.
    """

    def __init__(self, input_dim: int = 2, hidden_size: int = 128, latent_dim: int = 32) -> None:
        super().__init__()
        self.gru = nn.GRU(input_dim, hidden_size, batch_first=True)
        self.mu_head = nn.Linear(hidden_size, latent_dim)
        self.logvar_head = nn.Linear(hidden_size, latent_dim)

    def forward(self, f0: Tensor, loudness: Tensor) -> tuple[Tensor, Tensor]:
        features = torch.stack([f0, loudness], dim=-1)
        gru_out, _ = self.gru(features)
        mu = self.mu_head(gru_out)
        logvar = self.logvar_head(gru_out)
        return mu, logvar
