from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI, HTTPException

from server.db import connect, init_db
from server.presets import (
    check_hardware_change,
    get_bounds,
    reclamp_all_custom,
    seed_builtin_presets,
)
from server.routes import dataset, inference, model, presets, training
from server.tensorboard import get_manager

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    conn = connect()
    init_db(conn)
    conn.commit()

    bounds = get_bounds()
    seeded = seed_builtin_presets(conn, bounds)
    logger.info("seeded %s built-in presets", seeded)

    changed, fp = check_hardware_change(conn)
    if changed:
        updated = reclamp_all_custom(conn, bounds)
        logger.info(
            "hardware change detected (fp=%s), re-clamped presets: %s",
            fp,
            updated,
        )
    conn.close()

    yield

    with suppress(Exception):
        get_manager().stop()
    logger.info("tensorboard stopped")


app = FastAPI(
    title="wogd-ddsp-trainer",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(model.router, prefix="/api")
app.include_router(dataset.router, prefix="/api")
app.include_router(training.router, prefix="/api")
app.include_router(inference.router, prefix="/api")
app.include_router(presets.router, prefix="/api")


@app.get("/")
def root():
    return {"service": "wogd-ddsp-trainer", "status": "ok"}


@app.get("/api/tensorboard")
def tensorboard():
    try:
        manager = get_manager()
        manager.ensure_running()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return {"url": manager.url, "running": True, "port": manager.port}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="127.0.0.1",
        port=int(os.environ.get("WOGD_SERVER_PORT", "8000")),
    )
