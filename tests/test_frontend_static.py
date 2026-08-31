from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from server.main import mount_frontend


def test_mount_frontend_serves_index_and_assets(tmp_path: Path) -> None:
    dist = tmp_path / "dist"
    assets = dist / "assets"
    assets.mkdir(parents=True)
    (dist / "index.html").write_text("<html>app</html>", encoding="utf-8")
    (assets / "app.js").write_text("console.log(1)", encoding="utf-8")

    app = FastAPI()
    mount_frontend(app, dist)

    with TestClient(app) as client:
        index = client.get("/")
        assert index.status_code == 200
        assert index.headers["content-type"] == "text/html; charset=utf-8"
        assert "<html>app</html>" in index.text

        asset = client.get("/assets/app.js")
        assert asset.status_code == 200
        assert asset.text == "console.log(1)"

        fallback = client.get("/some/client/route")
        assert fallback.status_code == 200
        assert "<html>app</html>" in fallback.text
