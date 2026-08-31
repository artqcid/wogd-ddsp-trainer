"""Deterministic train/validation splits for file/item lists."""

from __future__ import annotations

import random


def split_dataset(
    items: list,
    val_fraction: float = 0.2,
    seed: int = 42,
) -> tuple[list, list]:
    """Deterministically split items into (train, val) using a local RNG.

    The split is reproducible and does not perturb the global random state.
    ``val_fraction`` must be in the open interval ``(0, 1)`` for a real split.
    Edge behaviour: ``val_fraction <= 0`` returns an empty validation set;
    ``val_fraction >= 1`` returns an empty training set (all items in val).
    """
    rng = random.Random(seed)
    indices = list(range(len(items)))
    rng.shuffle(indices)

    if val_fraction <= 0.0:
        val_count = 0
    elif val_fraction >= 1.0:
        val_count = len(items)
    else:
        val_count = round(len(items) * val_fraction)

    val_idx = set(indices[:val_count])
    train: list = []
    val: list = []
    for idx, item in enumerate(items):
        if idx in val_idx:
            val.append(item)
        else:
            train.append(item)
    return train, val


def split_file_list(
    paths: list[str],
    seed: int = 42,
    val_fraction: float = 0.2,
) -> dict[str, list[str]]:
    """Convenience wrapper returning ``{"train": [...], "val": [...]}``."""
    train, val = split_dataset(paths, val_fraction=val_fraction, seed=seed)
    return {"train": train, "val": val}
