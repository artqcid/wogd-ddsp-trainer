from __future__ import annotations

import contextlib
import json
import logging
import shutil
import uuid
from pathlib import Path
from typing import Annotated

import numpy as np
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {".wav", ".flac", ".ogg", ".mp3", ".m4a", ".mp4", ".aiff", ".aif"}
PREPROCESSED_SENTINEL = "_preprocessed"

router = APIRouter(prefix="/datasets", tags=["datasets"])


def datasets_dir() -> Path:
    """Return the datasets output folder under the effective data root."""
    from server.paths import datasets_dir as _paths_datasets_dir

    return _paths_datasets_dir()


def _sanitize(name: str) -> str:
    return Path(name).name


def dataset_summary(path: Path) -> dict:
    files = sorted(
        p.name for p in path.iterdir() if p.is_file() and p.suffix.lower() in ALLOWED_EXTENSIONS
    )
    status: str
    if (path / PREPROCESSED_SENTINEL).exists():
        status = "preprocessed"
    elif files:
        status = "uploaded"
    else:
        status = "empty"
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

    if name:
        name_path = dataset_path / "name.txt"
        name_path.write_text(name.strip(), encoding="utf-8")

    logger.info(
        "upload_dataset: id=%s name=%s files=%d", dataset_id, name or dataset_id, len(files)
    )
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


@router.get("/{dataset_id}/{filename}")
async def get_dataset_file(dataset_id: str, filename: str) -> FileResponse:
    """Serve an individual audio file from a dataset directory."""
    dataset_path = datasets_dir() / dataset_id
    if not dataset_path.is_dir():
        raise HTTPException(status_code=404, detail="dataset not found")
    file_path = dataset_path / _sanitize(filename)
    if not file_path.is_file():
        raise HTTPException(status_code=404, detail="file not found")
    if file_path.suffix.lower() not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="file type not allowed")
    return FileResponse(str(file_path))


@router.post("/{dataset_id}/f0-override/{filename}")
async def upload_f0_override(
    dataset_id: str,
    filename: str,
    f0_override: Annotated[UploadFile, File(...)],
) -> dict:
    """Upload a per-file F0 override (.npy, 1-D float32, F0 in Hz, not normalized)."""
    if not dataset_exists(dataset_id):
        raise HTTPException(status_code=404, detail="dataset not found")

    safe_name = _sanitize(filename)

    try:
        arr = np.load(f0_override.file, allow_pickle=False)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"failed to load .npy: {exc}") from exc

    if arr.dtype != np.float32:
        try:
            arr = arr.astype(np.float32)
        except Exception as exc:
            raise HTTPException(
                status_code=400,
                detail=f"override must be convertible to float32: {exc}",
            ) from exc

    if arr.ndim != 1:
        raise HTTPException(
            status_code=400,
            detail=f"override must be 1-D, got ndim={arr.ndim}",
        )

    dataset_path = datasets_dir() / dataset_id
    out_path = dataset_path / f"{safe_name}.f0_override.npy"
    np.save(out_path, arr, allow_pickle=False)

    return {
        "status": "ok",
        "file": f"{safe_name}.f0_override.npy",
        "length": int(arr.size),
    }


@router.delete("/{dataset_id}/f0-override/{filename}")
async def delete_f0_override(dataset_id: str, filename: str) -> dict:
    """Delete a per-file F0 override (.f0_override.npy) for the given dataset."""
    if not dataset_exists(dataset_id):
        raise HTTPException(status_code=404, detail="dataset not found")

    safe_name = _sanitize(filename)
    out_path = datasets_dir() / dataset_id / f"{safe_name}.f0_override.npy"

    if not out_path.exists():
        raise HTTPException(status_code=404, detail="f0_override file not found")

    out_path.unlink()

    return {"status": "deleted"}


@router.post("/{dataset_id}/extract-content")
async def extract_content(
    dataset_id: str,
    model_name: str = Form("hubert_soft"),
) -> dict:
    """Trigger offline content embedding extraction for all files in a dataset."""
    if not dataset_exists(dataset_id):
        raise HTTPException(status_code=404, detail="dataset not found")

    dataset_path = datasets_dir() / dataset_id
    import librosa

    from dataset.features import extract_content_embedding

    audio_files = sorted(
        p for p in dataset_path.iterdir() if p.is_file() and p.suffix.lower() in ALLOWED_EXTENSIONS
    )

    if not audio_files:
        raise HTTPException(status_code=400, detail="no audio files in dataset")

    logger.info(
        "extract_content start: dataset_id=%s model=%s files=%d",
        dataset_id,
        model_name,
        len(audio_files),
    )

    for af in audio_files:
        try:
            audio, sr = librosa.load(str(af), sr=16000, mono=True)
            target_frames = len(audio) // 256 + 1
            emb = extract_content_embedding(
                audio, sr, model_name=model_name, target_frames=target_frames
            )
            out_path = dataset_path / f"{af.stem}.content_embedding.npy"
            np.save(out_path, emb, allow_pickle=False)
        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail=f"failed to extract content for {af.name}: {exc}",
            ) from exc

    (dataset_path / PREPROCESSED_SENTINEL).touch()

    logger.info(
        "extract_content done: dataset_id=%s files_processed=%d", dataset_id, len(audio_files)
    )
    return {"status": "ok", "dataset_id": dataset_id, "files_processed": len(audio_files)}


@router.post("/{dataset_id}/preprocess")
async def preprocess_dataset(dataset_id: str) -> dict:
    """Submit a full async DDSP preprocessing pipeline job for a dataset.

    Extracts F0, loudness, and raw audio for all audio files; writes results
    into FeatureCache (train/val splits) so DDSPDataset can load them.
    Returns immediately with a job reference; poll GET /{dataset_id} for status.
    """
    if not dataset_exists(dataset_id):
        raise HTTPException(status_code=404, detail="dataset not found")

    from server.tasks import run_preprocessing_job

    task = run_preprocessing_job.apply_async(args=[dataset_id])

    logger.info("preprocess_dataset: submitted task_id=%s dataset_id=%s", task.id, dataset_id)
    return {
        "status": "queued",
        "dataset_id": dataset_id,
        "task_id": task.id,
    }


@router.delete("/{dataset_id}")
async def delete_dataset(dataset_id: str, force: bool = False) -> dict:
    """Delete a dataset directory and all its contents.

    Returns 409 if active training runs reference this dataset (unless force=True).
    """
    dataset_path = datasets_dir() / dataset_id
    if not dataset_path.is_dir():
        raise HTTPException(status_code=404, detail="dataset not found")

    # BUG-42: cascade check — warn if active runs reference this dataset
    if not force:
        from server.db import connect, run_all

        conn = connect()
        try:
            runs = run_all(conn)
            active_runs = [
                r
                for r in runs
                if r.get("dataset_id") == dataset_id
                and r.get("status") in {"pending", "running", "stopping"}
            ]
        finally:
            conn.close()
        if active_runs:
            raise HTTPException(
                status_code=409,
                detail=(
                    f"Dataset is referenced by {len(active_runs)} active run(s): "
                    f"{[r['run_id'] for r in active_runs]}. "
                    "Stop all runs first or use ?force=true."
                ),
            )

    shutil.rmtree(str(dataset_path))
    logger.info("delete_dataset: id=%s path=%s", dataset_id, dataset_path)
    return {"status": "deleted", "dataset_id": dataset_id}


@router.get("/{dataset_id}/diagnostics")
async def get_dataset_diagnostics(dataset_id: str) -> dict:
    if not dataset_exists(dataset_id):
        raise HTTPException(status_code=404, detail="dataset not found")

    diag_path = datasets_dir() / dataset_id / "diagnostics.json"
    if diag_path.is_file():
        try:
            data = json.loads(diag_path.read_text(encoding="utf-8"))
        except Exception:
            data = None
        return {"dataset_id": dataset_id, "diagnostics": data}
    return {"dataset_id": dataset_id, "diagnostics": None}
