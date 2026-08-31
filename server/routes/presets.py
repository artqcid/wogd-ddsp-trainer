from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from server.db import (
    connect,
    preset_all,
    preset_by_name,
    preset_create,
    preset_delete,
    preset_get,
    preset_update,
    run_get,
)
from server.presets import (
    bounds_to_dict,
    build_builtin_presets,
    clamp_params,
    get_bounds,
    get_gpu_summary,
    with_clamp_status,
)

router = APIRouter(prefix="/presets", tags=["presets"])


class PresetCreateRequest(BaseModel):
    name: str
    params: dict


class PresetUpdateRequest(BaseModel):
    name: str | None = None
    params: dict | None = None


class FromRunRequest(BaseModel):
    name: str | None = None


@router.get("")
def get_presets() -> dict[str, Any]:
    bounds = get_bounds()
    conn = connect()
    try:
        builtins = [with_clamp_status(p, bounds) for p in build_builtin_presets(bounds)]
        user_presets = [
            with_clamp_status(p, bounds) for p in preset_all(conn) if not p["is_builtin"]
        ]
        return {
            "bounds": bounds_to_dict(bounds),
            "gpu": get_gpu_summary(),
            "presets": builtins + user_presets,
        }
    finally:
        conn.close()


@router.post("")
def create_preset(body: PresetCreateRequest) -> dict[str, Any]:
    bounds = get_bounds()
    conn = connect()
    try:
        if preset_by_name(conn, body.name):
            raise HTTPException(status_code=409, detail="preset name already exists")
        clamped, fields = clamp_params(body.params, bounds)
        preset_id = str(uuid.uuid4())
        preset_create(conn, preset_id, body.name, False, clamped)
        conn.commit()
        return {
            "id": preset_id,
            "name": body.name,
            "is_builtin": False,
            "params": clamped,
            "created_from_run_id": None,
            "clamped_fields": fields,
        }
    finally:
        conn.close()


@router.put("/{preset_id}")
def update_preset(preset_id: str, body: PresetUpdateRequest) -> dict[str, Any]:
    bounds = get_bounds()
    conn = connect()
    try:
        p = preset_get(conn, preset_id)
        if p is None:
            raise HTTPException(status_code=404, detail="preset not found")
        if p["is_builtin"]:
            raise HTTPException(status_code=403, detail="built-in presets are read-only")
        if body.params is not None:
            clamped, fields = clamp_params(body.params, bounds)
        else:
            clamped, fields = p["params"], []
        preset_update(conn, preset_id, name=body.name, params=clamped)
        conn.commit()
        updated = preset_get(conn, preset_id)
        assert updated is not None
        updated["clamped_fields"] = fields
        return updated
    finally:
        conn.close()


@router.delete("/{preset_id}")
def delete_preset(preset_id: str) -> dict[str, Any]:
    conn = connect()
    try:
        p = preset_get(conn, preset_id)
        if p is None:
            raise HTTPException(status_code=404, detail="preset not found")
        if p["is_builtin"]:
            raise HTTPException(status_code=403, detail="built-in presets are read-only")
        preset_delete(conn, preset_id)
        conn.commit()
        return {}
    finally:
        conn.close()


@router.post("/from-run/{run_id}")
def create_from_run(run_id: str, body: FromRunRequest) -> dict[str, Any]:
    bounds = get_bounds()
    conn = connect()
    try:
        run = run_get(conn, run_id)
        if run is None:
            raise HTTPException(status_code=404, detail="run not found")
        params = {k: v for k, v in run["config"].items()}
        clamped, fields = clamp_params(params, bounds)
        name = body.name or f"Run {run_id}"
        if preset_by_name(conn, name):
            raise HTTPException(status_code=409, detail="preset name already exists")
        preset_id = str(uuid.uuid4())
        preset_create(conn, preset_id, name, False, clamped, created_from_run_id=run_id)
        conn.commit()
        return {
            "id": preset_id,
            "name": name,
            "is_builtin": False,
            "params": clamped,
            "created_from_run_id": run_id,
            "clamped_fields": fields,
        }
    finally:
        conn.close()
