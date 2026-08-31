from __future__ import annotations

import shutil
from pathlib import Path
from typing import Annotated
from uuid import uuid4

import torch
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse

from inference.render import load_model_from_checkpoint
from model.reverb_injection import extract_ir, inject_ir
from server.db import connect, run_get
from server.tasks import TaskRunner, get_task_runner, latest_checkpoint, runs_dir

router = APIRouter(prefix="/reverb", tags=["reverb"])


@router.post("/ir-inject", status_code=status.HTTP_202_ACCEPTED)
async def ir_inject(
    run_id: str = Form(...),
    ir: Annotated[UploadFile, File(...)] = None,
    *,
    runner: Annotated[TaskRunner, Depends(get_task_runner)],
) -> dict:
    if ir is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="IR file required")

    conn = connect()
    try:
        run = run_get(conn, run_id)
        if run is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="run not found")

        ckpt_path = latest_checkpoint(run_id)
        if ckpt_path is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="no checkpoint found")

        model = load_model_from_checkpoint(str(ckpt_path))
        reverb = model.core.reverb

        ir_ext = Path(ir.filename or "").suffix.lower()
        if ir_ext not in {".wav", ".ogg", ".flac", ".mp3"}:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"unsupported IR format: {ir_ext}",
            )

        out_dir = Path(runs_dir()) / run_id / "reverb"
        out_dir.mkdir(parents=True, exist_ok=True)
        ir_path = out_dir / f"{uuid4().hex}.wav"
        with ir_path.open("wb") as dst:
            shutil.copyfileobj(ir.file, dst)

        inject_ir(reverb, str(ir_path), sample_rate=16000)

        state = {
            "config": model.config.__dict__ if hasattr(model.config, "__dict__") else {},
            "model_state_dict": model.state_dict(),
        }
        torch.save(state, str(ckpt_path))

        return {"status": "ok", "run_id": run_id}
    finally:
        conn.close()


@router.get("/ir-extract/{run_id}")
async def ir_extract(run_id: str) -> FileResponse:
    conn = connect()
    try:
        run = run_get(conn, run_id)
        if run is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="run not found")

        ckpt_path = latest_checkpoint(run_id)
        if ckpt_path is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="no checkpoint found")

        model = load_model_from_checkpoint(str(ckpt_path))
        reverb = model.core.reverb

        tmp_path = Path(runs_dir()) / run_id / "reverb" / f"extracted_{uuid4().hex}.wav"
        tmp_path.parent.mkdir(parents=True, exist_ok=True)
        extract_ir(reverb, str(tmp_path), sample_rate=16000)

        return FileResponse(
            path=str(tmp_path),
            media_type="audio/wav",
            filename=tmp_path.name,
        )
    finally:
        conn.close()
