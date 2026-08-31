"""IR injection / extraction for SimpleReverb (Option B — fixed kernel swap).

Functions here operate on an already-instantiated SimpleReverb module by
replacing or reading its `kernel` buffer. No checkpoint changes needed.
"""

from __future__ import annotations

import logging
from pathlib import Path

import soundfile as sf
import torch

from model.ddsp.synths import SimpleReverb

logger = logging.getLogger(__name__)


def inject_ir(
    reverb: SimpleReverb,
    ir_path: str | Path,
    sample_rate: int = 16000,
) -> None:
    """Replace SimpleReverb's kernel buffer with a user-provided IR.

    Loads the .wav IR, resamples to `sample_rate`, normalises peak to 0 dB,
    and crops/pads to match the current kernel length.

    Args:
        reverb: An instantiated SimpleReverb module.
        ir_path: Path to a .wav impulse response file.
        sample_rate: Target sample rate (must match the reverb module).
    """
    ir_path = Path(ir_path)
    if not ir_path.exists():
        raise FileNotFoundError(f"IR file not found: {ir_path}")

    data, sr = sf.read(str(ir_path))
    if data.ndim > 1:
        data = data.mean(axis=1)  # mono

    # Resample to target sample rate
    if sr != sample_rate:
        data_t = torch.from_numpy(data).float().unsqueeze(0).unsqueeze(0)
        new_len = int(len(data) * sample_rate / sr)
        data_t = torch.nn.functional.interpolate(
            data_t, size=new_len, mode="linear", align_corners=False
        )
        data = data_t.squeeze().numpy()

    # Normalise peak to 0 dB
    max_val = max(abs(data.min()), abs(data.max()))
    if max_val > 0:
        data = data / max_val

    target_len = reverb.kernel.shape[0]
    if len(data) > target_len:
        data = data[:target_len]
    elif len(data) < target_len:
        data = torch.tensor(
            data.tolist() + [0.0] * (target_len - len(data)),
            dtype=reverb.kernel.dtype,
        )

    if isinstance(data, torch.Tensor):
        new_kernel = data
    else:
        new_kernel = torch.tensor(data, dtype=reverb.kernel.dtype)
    reverb.register_buffer("kernel", new_kernel)
    logger.info(
        "IR injected: %s -> kernel[%d] (resampled %d->%d Hz)",
        ir_path.name,
        target_len,
        sr,
        sample_rate,
    )


def extract_ir(
    reverb: SimpleReverb,
    out_path: str | Path,
    sample_rate: int = 16000,
) -> str:
    """Save SimpleReverb's current kernel buffer as a .wav file.

    Args:
        reverb: An instantiated SimpleReverb module.
        out_path: Output .wav path.
        sample_rate: Sample rate for the output file.

    Returns:
        The absolute path of the written file.
    """
    out_path = Path(out_path)
    kernel = reverb.kernel.detach().cpu().numpy()

    sf.write(str(out_path), kernel, sample_rate)
    abs_path = str(out_path.resolve())
    logger.info("IR extracted: kernel[%d] -> %s (%d Hz)", len(kernel), abs_path, sample_rate)
    return abs_path
