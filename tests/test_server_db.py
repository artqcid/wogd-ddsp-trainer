from __future__ import annotations

import pathlib
import sqlite3

import pytest

from server.db import (
    connect,
    init_db,
    meta_get,
    meta_set,
    preset_all,
    preset_by_name,
    preset_create,
    preset_delete,
    preset_get,
    preset_update,
    run_all,
    run_create,
    run_delete,
    run_get,
    run_is_stop_requested,
    run_set_status,
    run_set_stop_requested,
    synth_create,
    synth_get,
    synth_update,
)


@pytest.fixture
def db(tmp_path: pathlib.Path) -> sqlite3.Connection:
    path: pathlib.Path = tmp_path / "test.db"
    conn: sqlite3.Connection = connect(path)
    init_db(conn)
    conn.commit()
    yield conn
    conn.close()


def test_init_db_idempotent(tmp_path: pathlib.Path) -> None:
    path: pathlib.Path = tmp_path / "idempotent.db"
    conn: sqlite3.Connection = connect(path)
    init_db(conn)
    init_db(conn)
    conn.commit()
    conn.close()


def test_preset_roundtrip(db: sqlite3.Connection) -> None:
    preset_id: str = "preset-1"
    name: str = "Test Preset"
    is_builtin: bool = False
    params: dict = {"bandwidth": 2.0, "pitch_peaks": True}
    created_from_run_id: str | None = "run-abc"

    preset_create(
        db,
        id=preset_id,
        name=name,
        is_builtin=is_builtin,
        params=params,
        created_from_run_id=created_from_run_id,
    )
    db.commit()

    by_id: dict | None = preset_get(db, preset_id)
    assert by_id is not None
    assert by_id["id"] == preset_id
    assert by_id["name"] == name
    assert by_id["is_builtin"] is is_builtin
    assert by_id["params"] == params
    assert by_id["created_from_run_id"] == created_from_run_id

    by_name: dict | None = preset_by_name(db, name)
    assert by_name is not None
    assert by_name["id"] == preset_id

    all_presets: list[dict] = preset_all(db)
    assert len(all_presets) == 1
    assert all_presets[0]["id"] == preset_id

    updated: bool = preset_update(db, preset_id, name="Updated Preset", params={"bandwidth": 3.0})
    assert updated is True
    db.commit()

    refreshed: dict | None = preset_get(db, preset_id)
    assert refreshed is not None
    assert refreshed["name"] == "Updated Preset"
    assert refreshed["params"] == {"bandwidth": 3.0}
    assert refreshed["is_builtin"] is False
    assert refreshed["created_from_run_id"] == "run-abc"

    deleted: bool = preset_delete(db, preset_id)
    assert deleted is True
    db.commit()

    assert preset_get(db, preset_id) is None
    assert preset_all(db) == []


def test_run_roundtrip(db: sqlite3.Connection) -> None:
    run_id: str = "run-1"
    name: str | None = "Training Run"
    config: dict = {"learning_rate": 0.001, "epochs": 50}
    dataset_id: str | None = "ds-1"
    created_from_preset: str | None = "preset-1"

    run_create(
        db,
        run_id=run_id,
        name=name,
        config=config,
        dataset_id=dataset_id,
        created_from_preset=created_from_preset,
    )
    db.commit()

    got: dict | None = run_get(db, run_id)
    assert got is not None
    assert got["run_id"] == run_id
    assert got["name"] == name
    assert got["status"] == "pending"
    assert got["config"] == config
    assert got["dataset_id"] == dataset_id
    assert got["created_from_preset"] == created_from_preset
    assert got["stop_requested"] is False

    all_runs: list[dict] = run_all(db)
    assert len(all_runs) == 1
    assert all_runs[0]["run_id"] == run_id

    run_set_status(db, run_id, "training")
    db.commit()
    assert run_get(db, run_id)["status"] == "training"

    run_set_stop_requested(db, run_id, True)
    db.commit()
    assert run_is_stop_requested(db, run_id) is True
    assert run_get(db, run_id)["stop_requested"] is True

    deleted: bool = run_delete(db, run_id)
    assert deleted is True
    db.commit()

    assert run_get(db, run_id) is None
    assert run_all(db) == []


def test_synth_roundtrip(db: sqlite3.Connection) -> None:
    job_id: str = "job-1"
    run_id: str = "run-1"
    params: dict = {"note": "C4", "velocity": 0.8}

    synth_create(db, job_id=job_id, run_id=run_id, params=params)
    db.commit()

    got: dict | None = synth_get(db, job_id)
    assert got is not None
    assert got["job_id"] == job_id
    assert got["run_id"] == run_id
    assert got["status"] == "pending"
    assert got["params"] == params
    assert got["artifact_path"] is None

    synth_update(db, job_id, status="done", artifact_path="/tmp/out.wav")
    db.commit()

    refreshed: dict | None = synth_get(db, job_id)
    assert refreshed is not None
    assert refreshed["status"] == "done"
    assert refreshed["artifact_path"] == "/tmp/out.wav"
    assert refreshed["params"] == params


def test_meta_upsert(db: sqlite3.Connection) -> None:
    key: str = "version"
    value1: str = "0.1.0"
    value2: str = "0.2.0"

    meta_set(db, key, value1)
    db.commit()
    assert meta_get(db, key) == value1

    meta_set(db, key, value2)
    db.commit()
    assert meta_get(db, key) == value2

    assert meta_get(db, "missing-key") is None
