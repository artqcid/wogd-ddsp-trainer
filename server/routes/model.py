from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException, status

from server.tasks import run_checkpoint_dir, runs_dir

router = APIRouter(prefix="/models", tags=["models"])


def _entry_from_checkpoint(run_id: str, path: Path) -> dict[str, object] | None:
    filename = path.name
    try:
        step = int(filename.removeprefix("step-").removesuffix(".pt"))
    except (ValueError, TypeError):
        return None

    stat = path.stat()
    return {
        "model_id": f"{run_id}/{filename}",
        "run_id": run_id,
        "step": step,
        "checkpoint": filename,
        "path": str(path),
        "size_bytes": stat.st_size,
        "updated_at": str(stat.st_mtime),
    }


def scan_models() -> list[dict[str, object]]:
    runs = runs_dir()
    if not runs.exists():
        return []

    result: list[dict[str, object]] = []
    for run_dir in runs.iterdir():
        if not run_dir.is_dir():
            continue
        run_id = run_dir.name
        ckpt_dir = run_checkpoint_dir(run_id)
        if not ckpt_dir.exists():
            continue
        for path in ckpt_dir.iterdir():
            if not path.is_file():
                continue
            if not (path.name.startswith("step-") and path.name.endswith(".pt")):
                continue
            entry = _entry_from_checkpoint(run_id, path)
            if entry is not None:
                result.append(entry)

    result.sort(key=lambda e: float(e["updated_at"]), reverse=True)
    return result


def get_model(model_id: str) -> dict[str, object] | None:
    parts = model_id.split("/", 1)
    if len(parts) != 2:
        return None
    run_id, checkpoint = parts
    path = run_checkpoint_dir(run_id) / checkpoint
    if path.exists() and path.is_file():
        return _entry_from_checkpoint(run_id, path)
    return None


@router.get("")
async def list_models() -> list[dict[str, object]]:
    return scan_models()


@router.get("/{run_id}/{checkpoint}")
async def read_model(run_id: str, checkpoint: str) -> dict[str, object]:
    model_id = f"{run_id}/{checkpoint}"
    entry = get_model(model_id)
    if entry is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model '{model_id}' not found",
        )
    return entry
