"""Multi-scale spectral loss for DDSP audio training."""

from __future__ import annotations

import torch
import torch.nn as nn
import torch.nn.functional as F


class MultiScaleSpectralLoss(nn.Module):
    """Multi-scale spectral loss combining magnitude and log-magnitude L1, summed across scales.

    Uses torch.stft with specified FFT sizes. Returns a finite scalar loss
    averaged over batch and scales.
    """

    def __init__(
        self,
        fft_sizes: list[int] | None = None,
        n_fft: int | None = None,  # kept for backward compat; fft_sizes takes precedence
    ) -> None:
        super().__init__()
        if fft_sizes is not None:
            self.fft_sizes = list(fft_sizes)
        elif n_fft is not None:
            self.fft_sizes = [n_fft]
        else:
            self.fft_sizes = [512, 1024, 2048]

    def forward(
        self,
        predicted: torch.Tensor,
        target: torch.Tensor,
    ) -> torch.Tensor:
        """Compute multi-scale spectral loss.

        Args:
            predicted: predicted audio, shape (B, T) or (B, 1, T).
            target: target audio, same shape as predicted.

        Returns:
            Scalar loss (mean over batch and scales).
        """
        # Ensure 2D: (B, T)
        if predicted.dim() == 3:
            predicted = predicted.squeeze(1)
        if target.dim() == 3:
            target = target.squeeze(1)

        B, T = predicted.shape
        device = predicted.device
        dtype = predicted.dtype

        total_loss = torch.tensor(0.0, device=device, dtype=dtype)

        for fft_size in self.fft_sizes:
            # STFT with hann window, no padding, centered
            win = torch.hann_window(fft_size, device=device, dtype=dtype)

            pred_spec = torch.stft(
                predicted,
                n_fft=fft_size,
                hop_length=fft_size // 4,
                win_length=fft_size,
                window=win,
                center=True,
                return_complex=True,
            )
            tgt_spec = torch.stft(
                target,
                n_fft=fft_size,
                hop_length=fft_size // 4,
                win_length=fft_size,
                window=win,
                center=True,
                return_complex=True,
            )

            # Magnitude
            pred_mag = torch.abs(pred_spec)
            tgt_mag = torch.abs(tgt_spec)

            # Magnitude L1
            mag_loss = F.l1_loss(pred_mag, tgt_mag)

            # Log-magnitude L1 (with epsilon to avoid log(0))
            eps = 1e-8
            log_pred = torch.log(pred_mag + eps)
            log_tgt = torch.log(tgt_mag + eps)
            log_loss = F.l1_loss(log_pred, log_tgt)

            total_loss = total_loss + mag_loss + log_loss

        # Average over number of scales
        total_loss = total_loss / len(self.fft_sizes)

        # Mean over batch
        total_loss = total_loss.mean()

        return total_loss


def compute_spectral_loss(
    predicted: torch.Tensor,
    target: torch.Tensor,
    fft_sizes: list[int] | None = None,
) -> torch.Tensor:
    """Functional wrapper around MultiScaleSpectralLoss.

    Args:
        predicted: predicted audio, (B, T) or (B, 1, T).
        target: target audio, same shape.
        fft_sizes: list of FFT sizes. Defaults to [512, 1024, 2048].

    Returns:
        Scalar spectral loss.
    """
    if fft_sizes is None:
        fft_sizes = [512, 1024, 2048]

    loss_fn = MultiScaleSpectralLoss(fft_sizes=fft_sizes)
    return loss_fn(predicted, target)
