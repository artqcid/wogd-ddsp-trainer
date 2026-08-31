from __future__ import annotations

import shutil
from pathlib import Path
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse

from server.db import connect, synth_create, synth_get
from server.tasks import TaskRunner, get_task_runner, runs_dir

router = APIRouter(prefix="/inference", tags=["inference"])


def _sanitized_filename(filename: str) -> str:
    """Return only the final path component of *filename* (no directory traversal)."""
    return Path(filename).name


@router.post("/synthesize", status_code=status.HTTP_202_ACCEPTED)
async def synthesize(
    run_id: str = Form(...),
    pitch_shift: float = Form(0.0),
    loudness_shift: float = Form(0.0),
    audio: Annotated[UploadFile | None, File()] = None,
    *,
    runner: Annotated[TaskRunner, Depends(get_task_runner)],
) -> dict:
    job_id = str(uuid4())
    params = {
        "run_id": run_id,
        "pitch_shift": pitch_shift,
        "loudness_shift": loudness_shift,
        "seed": 0,
    }

    conn = connect()
    try:
        if audio is not None:
            src_ext = Path(_sanitized_filename(audio.filename or "")).suffix
            out_dir = Path(runs_dir()) / run_id / "synthesis"
            out_dir.mkdir(parents=True, exist_ok=True)
            src_path = out_dir / f"{job_id}.src{src_ext}"
            with src_path.open("wb") as dst:
                shutil.copyfileobj(audio.file, dst)

        synth_create(conn, job_id, run_id, params)
        conn.commit()

        task_id = runner.submit_synthesis(job_id)
    finally:
        conn.close()

    return {"job_id": job_id, "status": "pending", "task_id": task_id}


@router.get("/jobs/{job_id}", status_code=status.HTTP_200_OK)
async def get_job(job_id: str) -> dict:
    conn = connect()
    try:
        job = synth_get(conn, job_id)
        if job is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="job not found")

        artifact_url = (
            f"/api/inference/artifacts/{job_id}" if job["status"] == "completed" else None
        )
        return {
            "job_id": job["job_id"],
            "run_id": job["run_id"],
            "status": job["status"],
            "created_at": job["created_at"],
            "updated_at": job["updated_at"],
            "artifact_url": artifact_url,
        }
    finally:
        conn.close()


@router.get("/artifacts/{job_id}")
async def get_artifact(job_id: str) -> FileResponse:
    conn = connect()
    try:
        job = synth_get(conn, job_id)
        if job is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="job not found")

        artifact_path: str | None = job.get("artifact_path")
        if job["status"] != "completed":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="job not completed")
        if not artifact_path or not Path(artifact_path).is_file():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="artifact not found")

        return FileResponse(
            path=artifact_path,
            media_type="audio/wav",
            filename=Path(artifact_path).name,
        )
    finally:
        conn.close()
