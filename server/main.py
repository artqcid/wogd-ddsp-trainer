from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager, suppress
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from server.db import connect, init_db
from server.errors import install_handlers
from server.presets import (
    check_hardware_change,
    get_bounds,
    reclamp_all_custom,
    seed_builtin_presets,
)
from server.routes import dataset, gpu, host, inference, model, presets, reverb, settings, training
from server.tensorboard import get_manager

logger = logging.getLogger(__name__)

FRONTEND_DIST = Path(__file__).resolve().parents[1] / "webui" / "dist"


def mount_frontend(app: FastAPI, dist: Path) -> None:
    """Serve the production frontend build from `dist` (SPA).

    Non-API routes fall back to the SPA entry point so client-side routing
    works. Used by the VSCode `start-application-release` task; disabled during
    development so Vite (dev server) owns the frontend.
    """
    app.mount(
        "/assets",
        StaticFiles(directory=dist / "assets"),
        name="assets",
    )

    @app.get("/", include_in_schema=False)
    def index() -> FileResponse:
        return FileResponse(dist / "index.html")

    @app.get("/{_:path}", include_in_schema=False)
    def spa_fallback(_: str) -> FileResponse:
        return FileResponse(dist / "index.html")


@asynccontextmanager
async def lifespan(app: FastAPI):
    from server.paths import ensure_data_dirs

    ensure_data_dirs()
    conn = connect()
    init_db(conn)
    conn.commit()

    bounds = get_bounds()
    ALL_TIERS = ("standard", "component", "hacks", "engine", "advanced")
    for tier in ALL_TIERS:
        seeded = seed_builtin_presets(conn, bounds, tier=tier)
        if seeded:
            logger.info("seeded %s built-in %s presets", seeded, tier)

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
app.include_router(settings.router, prefix="/api")
app.include_router(gpu.router, prefix="/api")
app.include_router(host.router, prefix="/api")
app.include_router(reverb.router, prefix="/api")

install_handlers(app)

# When enabled, serve the production frontend build from `webui/dist` (used by
# the VSCode `start-application-release` task). Disabled during development so
# Vite (dev server) owns the frontend.
_SERVE_STATIC = os.environ.get("WOGD_SERVE_STATIC", "0") == "1"

if _SERVE_STATIC and FRONTEND_DIST.is_dir():
    mount_frontend(app, FRONTEND_DIST)


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
