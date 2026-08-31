from __future__ import annotations

import shutil
from typing import Annotated, Any
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from server.db import (
    connect,
    preset_get,
    run_all,
    run_create,
    run_delete,
    run_get,
    run_set_status,
    run_set_stop_requested,
)
from server.presets import bounds_to_dict, clamp_params, get_bounds
from server.tasks import TaskRunner, get_task_runner, run_checkpoint_dir, runs_dir

router = APIRouter(prefix="/runs", tags=["runs"])


class RunCreateRequest(BaseModel):
    name: str
    dataset_id: str | None = None
    preset_id: str | None = None
    params: dict | None = None


class ValidateRequest(BaseModel):
    preset_id: str | None = None
    params: dict | None = None


def _effective_params(conn: Any, preset_id: str | None, params: dict | None) -> dict[str, Any]:
    if preset_id is not None:
        preset = preset_get(conn, preset_id)
        if preset is None:
            raise HTTPException(status_code=404, detail=f"preset not found: {preset_id}")
        base = preset.get("params", {}) or {}
    else:
        base = {}
    if params:
        base = {**base, **params}
    return base or {}


def _clamp_params(
    conn: Any, preset_id: str | None, params: dict | None
) -> tuple[dict[str, Any], list[str]]:
    effective = _effective_params(conn, preset_id, params)
    bounds = get_bounds()
    clamped, clamped_fields = clamp_params(effective, bounds)
    return clamped, clamped_fields


@router.post("/validate")
def validate(req: ValidateRequest) -> dict[str, Any]:
    conn = connect()
    try:
        clamped, clamped_fields = _clamp_params(conn, req.preset_id, req.params)
        bounds = get_bounds()
        return {
            "params": clamped,
            "clamped_fields": clamped_fields,
            "bounds": bounds_to_dict(bounds),
        }
    finally:
        conn.close()


@router.post("")
def create_run(
    req: RunCreateRequest,
    runner: Annotated[TaskRunner, Depends(get_task_runner)],
) -> dict[str, Any]:
    conn = connect()
    try:
        clamped, clamped_fields = _clamp_params(conn, req.preset_id, req.params)
        config = clamped
        run_id = str(uuid4())
        run_dir = runs_dir() / run_id
        run_dir.mkdir(parents=True, exist_ok=True)

        run_create(
            conn,
            run_id,
            req.name,
            config,
            req.dataset_id,
            created_from_preset=req.preset_id,
        )
        conn.commit()

        task_id = runner.submit_training(run_id)
        return {
            "run_id": run_id,
            "name": req.name,
            "status": "pending",
            "task_id": task_id,
            "config": config,
            "clamped_fields": clamped_fields,
        }
    finally:
        conn.close()


@router.get("")
def list_runs() -> dict[str, Any]:
    conn = connect()
    try:
        runs = run_all(conn)
        rows = []
        for run in runs:
            run_id = run["run_id"]
            ckpt_dir = run_checkpoint_dir(run_id)
            ckpt_count = 0
            latest_step: int | None = None
            if ckpt_dir.exists():
                for p in ckpt_dir.glob("step-*.pt"):
                    ckpt_count += 1
                    try:
                        step = int(p.stem.split("-", 1)[1])
                    except (ValueError, IndexError):
                        continue
                    if latest_step is None or step > latest_step:
                        latest_step = step
            rows.append({**run, "checkpoint_count": ckpt_count, "latest_step": latest_step})
        return {"runs": rows}
    finally:
        conn.close()


@router.get("/{run_id}")
def get_run(run_id: str) -> dict[str, Any]:
    conn = connect()
    try:
        run = run_get(conn, run_id)
        if run is None:
            raise HTTPException(status_code=404, detail="run not found")
        ckpt_dir = run_checkpoint_dir(run_id)
        checkpoints: list[str] = []
        latest_step: int | None = None
        if ckpt_dir.exists():
            for p in ckpt_dir.glob("step-*.pt"):
                checkpoints.append(p.name)
                try:
                    step = int(p.stem.split("-", 1)[1])
                except (ValueError, IndexError):
                    continue
                if latest_step is None or step > latest_step:
                    latest_step = step
        return {"run": {**run}, "checkpoints": checkpoints, "latest_step": latest_step}
    finally:
        conn.close()


@router.post("/{run_id}/stop")
def stop_run(run_id: str) -> dict[str, Any]:
    conn = connect()
    try:
        run = run_get(conn, run_id)
        if run is None:
            raise HTTPException(status_code=404, detail="run not found")
        status = run["status"]
        if status in {"running", "pending", "stopping"}:
            run_set_stop_requested(conn, run_id, True)
            if status == "running":
                run_set_status(conn, run_id, "stopping")
            else:
                run_set_status(conn, run_id, "stopped")
            conn.commit()
        updated = run_get(conn, run_id)
        if updated is None:
            raise HTTPException(status_code=500, detail="run disappeared after update")
        return updated
    finally:
        conn.close()


@router.post("/{run_id}/resume")
def resume_run(
    run_id: str,
    runner: Annotated[TaskRunner, Depends(get_task_runner)],
) -> dict[str, Any]:
    conn = connect()
    try:
        run = run_get(conn, run_id)
        if run is None:
            raise HTTPException(status_code=404, detail="run not found")
        status = run["status"]
        if status not in {"stopped", "failed", "completed"}:
            raise HTTPException(
                status_code=409,
                detail=f"run not resumable in state {status}",
            )
        run_set_stop_requested(conn, run_id, False)
        run_set_status(conn, run_id, "pending")
        conn.commit()
        task_id = runner.submit_training(run_id)
        updated = run_get(conn, run_id)
        if updated is None:
            raise HTTPException(status_code=500, detail="run disappeared after update")
        return {**updated, "task_id": task_id}
    finally:
        conn.close()


@router.delete("/{run_id}")
def delete_run(run_id: str) -> None:
    conn = connect()
    try:
        run = run_get(conn, run_id)
        if run is None:
            raise HTTPException(status_code=404, detail="run not found")
        run_delete(conn, run_id)
        conn.commit()
        shutil.rmtree(runs_dir() / run_id, ignore_errors=True)
    finally:
        conn.close()
