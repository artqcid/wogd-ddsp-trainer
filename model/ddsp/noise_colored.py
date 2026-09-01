import torch


def _pink_noise(n: int, device, dtype) -> torch.Tensor:
    """Generate pink noise (1/f spectrum) of length n."""
    white = torch.randn(n, device=device, dtype=dtype)
    fft = torch.fft.rfft(white)
    freqs = torch.fft.rfftfreq(n, device=device, dtype=dtype)
    freqs[0] = 1.0  # avoid division by zero at DC
    pink_filter = 1.0 / freqs.sqrt()
    fft = fft * pink_filter
    signal = torch.fft.irfft(fft, n=n)
    rms = signal.pow(2).mean().sqrt().clamp(min=1e-8)
    return signal / rms


def _brown_noise(n: int, device, dtype) -> torch.Tensor:
    """Generate brown noise (1/f² spectrum) of length n."""
    white = torch.randn(n, device=device, dtype=dtype)
    fft = torch.fft.rfft(white)
    freqs = torch.fft.rfftfreq(n, device=device, dtype=dtype)
    freqs[0] = 1.0
    brown_filter = 1.0 / freqs
    fft = fft * brown_filter
    signal = torch.fft.irfft(fft, n=n)
    rms = signal.pow(2).mean().sqrt().clamp(min=1e-8)
    return signal / rms
