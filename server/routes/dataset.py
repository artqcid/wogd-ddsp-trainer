from __future__ import annotations

import contextlib
import os
import shutil
import uuid
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

ALLOWED_EXTENSIONS = {".wav", ".flac", ".ogg", ".mp3", ".m4a", ".mp4", ".aiff", ".aif"}

router = APIRouter(prefix="/datasets", tags=["datasets"])


def datasets_dir() -> Path:
    env = os.environ.get("WOGD_DATASETS_DIR", "")
    if env:
        return Path(env)
    return Path.cwd() / "datasets"


def _sanitize(name: str) -> str:
    return Path(name).name


def dataset_summary(path: Path) -> dict:
    files = sorted(p.name for p in path.iterdir() if p.is_file())
    status = "uploaded" if files else "empty"
    name_path = path / "name.txt"
    name = path.name
    if name_path.exists():
        with contextlib.suppress(OSError):
            name = name_path.read_text(encoding="utf-8").strip() or name
    return {
        "id": path.name,
        "name": name,
        "status": status,
        "file_count": len(files),
        "files": files,
    }


def dataset_exists(dataset_id: str) -> bool:
    return (datasets_dir() / dataset_id).is_dir()


def _list_datasets() -> list[dict]:
    base = datasets_dir()
    if not base.is_dir():
        return []
    entries = sorted(
        (p for p in base.iterdir() if p.is_dir()),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    return [dataset_summary(p) for p in entries]


@router.post("")
async def upload_dataset(
    files: Annotated[list[UploadFile], File(...)],
    name: Annotated[str, Form()] = "",
) -> dict:
    if not files:
        raise HTTPException(status_code=400, detail="no files provided")

    for f in files:
        ext = Path(f.filename or "").suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"unsupported file type: {f.filename or 'unknown'}",
            )

    dataset_id = str(uuid.uuid4())
    dataset_path = datasets_dir() / dataset_id
    dataset_path.mkdir(parents=True, exist_ok=True)

    for f in files:
        safe_name = _sanitize(f.filename or "unknown")
        dest = dataset_path / safe_name
        with dest.open("wb") as out:
            shutil.copyfileobj(f.file, out)

    return {
        "id": dataset_id,
        "name": name or dataset_id,
        "status": "uploaded",
        "file_count": len(files),
        "files": sorted(_sanitize(f.filename or "unknown") for f in files),
    }


@router.get("")
async def list_datasets() -> list[dict]:
    return _list_datasets()


@router.get("/{dataset_id}")
async def get_dataset(dataset_id: str) -> dict:
    dataset_path = datasets_dir() / dataset_id
    if not dataset_path.is_dir():
        raise HTTPException(status_code=404, detail="dataset not found")
    return dataset_summary(dataset_path)
