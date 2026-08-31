"""Unit tests for dataset.split — deterministic train/validation splits."""

from __future__ import annotations

import numpy as np

from dataset.split import split_dataset, split_file_list

# ---------------------------------------------------------------------------
# split_dataset
# ---------------------------------------------------------------------------


def test_split_dataset_disjoint_and_covers_all() -> None:
    items = list(range(100))
    train, val = split_dataset(items, val_fraction=0.2, seed=42)
    assert len(train) == 80
    assert len(val) == 20
    assert set(train).isdisjoint(val)
    assert set(train).union(val) == set(items)


def test_split_dataset_reproducible_same_seed() -> None:
    items = list(range(100))
    first = split_dataset(items, val_fraction=0.2, seed=123)
    second = split_dataset(items, val_fraction=0.2, seed=123)
    assert first == second


def test_split_dataset_different_seed_changes_order() -> None:
    items = list(range(100))
    a = split_dataset(items, val_fraction=0.2, seed=1)
    b = split_dataset(items, val_fraction=0.2, seed=2)
    assert a != b


def test_split_dataset_local_rng_does_not_touch_global() -> None:
    items = list(range(10))
    before_rng = np.random.default_rng(0)
    global_before = int(before_rng.integers(0, 1_000_000))
    _ = split_dataset(items, val_fraction=0.3, seed=7)
    after_rng = np.random.default_rng(0)
    global_after = int(after_rng.integers(0, 1_000_000))
    assert global_before == global_after


def test_split_dataset_val_fraction_zero_returns_empty_val() -> None:
    items = list(range(25))
    train, val = split_dataset(items, val_fraction=0.0, seed=1)
    assert len(train) == 25
    assert val == []


def test_split_dataset_val_fraction_one_returns_empty_train() -> None:
    items = list(range(25))
    train, val = split_dataset(items, val_fraction=1.0, seed=1)
    assert train == []
    assert len(val) == 25


def test_split_dataset_val_fraction_negative_is_treated_as_zero() -> None:
    items = list(range(25))
    train, val = split_dataset(items, val_fraction=-0.5, seed=1)
    assert len(train) == 25
    assert val == []


def test_split_dataset_val_fraction_over_one_is_treated_as_all_val() -> None:
    items = list(range(25))
    train, val = split_dataset(items, val_fraction=1.5, seed=1)
    assert train == []
    assert len(val) == 25


def test_split_dataset_empty_input() -> None:
    train, val = split_dataset([], val_fraction=0.2, seed=42)
    assert train == []
    assert val == []


# ---------------------------------------------------------------------------
# split_file_list
# ---------------------------------------------------------------------------


def test_split_file_list_returns_dict_keys_train_val() -> None:
    paths = [f"/x/{i}.wav" for i in range(10)]
    out = split_file_list(paths, seed=42, val_fraction=0.2)
    assert set(out.keys()) == {"train", "val"}
    combined = out["train"] + out["val"]
    assert sorted(combined) == sorted(paths)
    assert set(out["train"]).isdisjoint(out["val"])


def test_split_file_list_disjoint_and_reproducible() -> None:
    paths = [f"/x/{i}.wav" for i in range(50)]
    a = split_file_list(paths, seed=7, val_fraction=0.3)
    b = split_file_list(paths, seed=7, val_fraction=0.3)
    assert a == b
    assert set(a["train"]).isdisjoint(a["val"])
    assert len(a["train"]) + len(a["val"]) == len(paths)
