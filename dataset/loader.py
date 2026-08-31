"""Load precomputed .npy features written by dataset.features.save_features."""

from __future__ import annotations

import os

import numpy as np


def load_features(
    out_dir: str,
    base_name: str,
) -> dict[str, np.ndarray]:
    """Read the three .npy feature files back into a dict (float32).

    Keys: "f0_hz", "f0_confidence", "loudness_db".
    """
    keys = ("f0_hz", "f0_confidence", "loudness_db")
    result: dict[str, np.ndarray] = {}
    for key in keys:
        path = os.path.join(out_dir, f"{base_name}.{key}.npy")
        result[key] = np.load(path).astype(np.float32)
    return result
