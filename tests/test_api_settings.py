from __future__ import annotations

import os
import unittest.mock as _um
from pathlib import Path
from typing import Any

from fastapi import status

from server.paths import _migrate_from_cwd


def _clear_env(monkeypatch: Any) -> None:
    """Remove the WOGD_DATA_DIR override so live persistence is exercised.

    WOGD_DB_PATH stays set (from the conftest) so the DB is at a known temp
    location; WOGD_DATA_DIR must be absent so data_dir() reads the persisted
    DB value (env has higher precedence).
    """
    monkeypatch.delenv("WOGD_DATA_DIR", raising=False)


def test_get_settings(client: Any) -> None:
    resp = client.get("/api/settings")
    assert resp.status_code == status.HTTP_200_OK
    body = resp.json()
    assert body["install_dir"]
    assert body["data_dir"]
    assert body["db_path"]
    assert body["datasets_dir"] == str(Path(body["data_dir"]) / "datasets")
    assert body["runs_dir"] == str(Path(body["data_dir"]) / "runs")


def test_update_settings_persists_and_creates_dirs(
    client: Any, monkeypatch: Any, tmp_path: Any
) -> None:
    _clear_env(monkeypatch)
    new_root = tmp_path / "newdata"
    resp = client.put("/api/settings", json={"data_dir": str(new_root)})
    assert resp.status_code == status.HTTP_200_OK
    body = resp.json()
    assert body["data_dir"] == str(new_root)
    assert Path(body["datasets_dir"]).is_dir()
    assert Path(body["runs_dir"]).is_dir()
    assert body["data_is_default"] is False


def test_update_settings_migrates_datasets(client: Any, monkeypatch: Any, tmp_path: Any) -> None:
    from server.routes.dataset import datasets_dir

    _clear_env(monkeypatch)
    first = datasets_dir()
    first.mkdir(parents=True, exist_ok=True)
    (first / "ds_existing").mkdir(parents=True, exist_ok=True)

    new_root = tmp_path / "migrated"
    resp = client.put("/api/settings", json={"data_dir": str(new_root)})
    assert resp.status_code == status.HTTP_200_OK
    assert (new_root / "datasets" / "ds_existing").is_dir()


def test_update_settings_rejects_relative_path(client: Any) -> None:
    resp = client.put("/api/settings", json={"data_dir": "relative/path"})
    assert resp.status_code == status.HTTP_400_BAD_REQUEST


def test_update_settings_reset_to_default(client: Any, monkeypatch: Any, tmp_path: Any) -> None:
    _clear_env(monkeypatch)
    new_root = tmp_path / "custom"
    put = client.put("/api/settings", json={"data_dir": str(new_root)})
    assert put.status_code == status.HTTP_200_OK
    assert put.json()["data_dir"] == str(new_root)

    reset = client.put("/api/settings", json={"data_dir": None})
    assert reset.status_code == status.HTTP_200_OK
    assert reset.json()["data_is_default"] is True

    # once reset, the env (still absent) is not the source; data_dir must no
    # longer point at the custom root.
    assert os.environ.get("WOGD_DATA_DIR") is None


def test_migrate_from_cwd_copies_old_datasets(tmp_path: Any, monkeypatch: Any) -> None:
    """Best-effort migration of old cwd-relative datasets/runs on first boot."""
    root = tmp_path / "app"
    (root / "datasets").mkdir(parents=True)
    (root / "datasets" / "old.wav").write_bytes(b"x")
    (root / "runs" / "old").mkdir(parents=True)
    (root / "runs" / "old" / "a.pt").write_bytes(b"y")

    new_root = tmp_path / "newdata"
    new_root.mkdir()

    monkeypatch.chdir(root)
    with _um.patch("server.paths.install_dir", return_value=root):
        _migrate_from_cwd(new_root)

    assert (new_root / "datasets" / "old.wav").exists()
    assert not (root / "datasets" / "old.wav").exists()
    assert (new_root / "runs" / "old" / "a.pt").exists()
