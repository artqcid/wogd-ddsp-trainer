from __future__ import annotations

import tempfile
from pathlib import Path

import torch
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse

from inference.export_custom_vst import export_custom_vst
from model.param_manifest import ParamManifest, build_default_manifest
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


@router.get("/{run_id}/{checkpoint}/params")
async def get_model_params(run_id: str, checkpoint: str) -> dict[str, object]:
    checkpoint_path = run_checkpoint_dir(run_id) / checkpoint
    if not checkpoint_path.exists() or not checkpoint_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Checkpoint '{run_id}/{checkpoint}' not found",
        )
    try:
        state = torch.load(str(checkpoint_path), map_location="cpu", weights_only=False)
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Checkpoint '{run_id}/{checkpoint}' not found",
        ) from None
    if "param_manifest" in state:
        return state["param_manifest"]
    model_tier = state.get("model_tier", "standard")
    variant_flags = state.get("variant_flags", {})
    manifest = build_default_manifest(model_tier, variant_flags).to_dict()
    return manifest


@router.put("/{run_id}/{checkpoint}/params")
async def put_model_params(run_id: str, checkpoint: str, body: dict) -> dict[str, object]:
    checkpoint_path = run_checkpoint_dir(run_id) / checkpoint
    if not checkpoint_path.exists() or not checkpoint_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Checkpoint '{run_id}/{checkpoint}' not found",
        )
    try:
        manifest = ParamManifest.from_dict(body)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from None
    try:
        state = torch.load(str(checkpoint_path), map_location="cpu", weights_only=False)
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Checkpoint '{run_id}/{checkpoint}' not found",
        ) from None
    state["param_manifest"] = manifest.to_dict()
    torch.save(state, str(checkpoint_path))
    return manifest.to_dict()


@router.post("/{run_id}/{checkpoint}/export/custom-vst")
async def export_custom_vst_endpoint(run_id: str, checkpoint: str) -> FileResponse:
    checkpoint_path = run_checkpoint_dir(run_id) / checkpoint
    if not checkpoint_path.exists() or not checkpoint_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Checkpoint '{run_id}/{checkpoint}' not found",
        )
    try:
        with tempfile.NamedTemporaryFile(suffix=".pt", delete=False) as tmp:
            out_path = tmp.name
        export_custom_vst(str(checkpoint_path), out_path)
        return FileResponse(
            path=out_path,
            media_type="application/octet-stream",
            filename=f"{run_id}-{checkpoint.removesuffix('.pt')}-custom-vst.pt",
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from None
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Export failed: {exc}",
        ) from None
