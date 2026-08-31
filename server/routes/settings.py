"""REST settings endpoints (M6.1).

Exposes the effective path configuration (install dir, data root, DB, output
folders) and allows the *data directory* (the "Sammelwurzel") to be changed
live. Only the data directory is user-mutable at runtime; the install dir and
DB path are fixed.
"""

from __future__ import annotations

import shutil
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from server.paths import (
    data_dir,
    default_data_dir,
    ensure_data_dirs,
    persist_data_dir,
    settings_summary,
)

router = APIRouter(prefix="/settings", tags=["settings"])

_MIGRATE = ("datasets", "runs")


class SettingsUpdate(BaseModel):
    data_dir: str | None = None


def _migrate_content(old_root: Path, new_root: Path) -> None:
    """Move datasets/runs from *old_root* into *new_root* when absent there."""
    for name in _MIGRATE:
        src = old_root / name
        if not src.is_dir():
            continue
        dst = new_root / name
        if dst.exists():
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dst))


@router.get("")
def get_settings() -> dict:
    return settings_summary()


@router.put("")
def update_settings(req: SettingsUpdate) -> dict:
    if req.data_dir is None:
        # Reset to the platform default.
        persist_data_dir(None)
        ensure_data_dirs()
        return settings_summary()

    target = Path(req.data_dir).expanduser()
    if not target.is_absolute():
        raise HTTPException(status_code=400, detail="data_dir must be an absolute path")

    old_root = data_dir()
    try:
        target.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise HTTPException(status_code=400, detail=f"cannot create data_dir: {exc}") from exc

    _migrate_content(old_root, target)
    persist_data_dir(str(target))
    ensure_data_dirs()
    return settings_summary()


@router.get("/defaults")
def get_defaults() -> dict:
    return {
        "default_data_dir": str(default_data_dir()),
        "current_data_dir": str(data_dir()),
    }
