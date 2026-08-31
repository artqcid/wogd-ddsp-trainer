from __future__ import annotations

from fastapi.testclient import TestClient

from server.tasks import runs_dir

# ---------------------------------------------------------------------------
# Validate
# ---------------------------------------------------------------------------


def test_validate_in_bounds(client: TestClient) -> None:
    r = client.post(
        "/api/runs/validate",
        json={
            "params": {
                "hidden_size": 256,
                "stft_scales": 3,
                "learning_rate": 1e-3,
                "mixed_precision": "required",
                "gradient_checkpointing": "enabled",
            }
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body["clamped_fields"] == []
    assert body["params"]["hidden_size"] == 256


def test_validate_clamps_out_of_bounds(client: TestClient) -> None:
    r = client.post(
        "/api/runs/validate",
        json={"params": {"hidden_size": 99999, "stft_scales": 3}},
    )
    assert r.status_code == 200
    body = r.json()
    assert "hidden_size" in body["clamped_fields"]
    assert body["params"]["hidden_size"] == body["bounds"]["hidden_size_max"]


# ---------------------------------------------------------------------------
# Create / list / get
# ---------------------------------------------------------------------------


def test_create_run_records_task(client: TestClient, fake_runner: object) -> None:
    r = client.post(
        "/api/runs",
        json={
            "name": "test-run",
            "preset_id": "builtin-normal",
        },
    )
    assert r.status_code == 200
    body = r.json()
    run_id = body["run_id"]
    assert body["name"] == "test-run"
    assert body["status"] == "pending"
    assert body["task_id"].startswith("t-")
    assert run_id in fake_runner.submitted_training  # type: ignore[arg-type]


def test_get_run_reports_checkpoints(client: TestClient) -> None:
    r = client.post(
        "/api/runs",
        json={"name": "ckpt-run", "preset_id": "builtin-normal"},
    )
    assert r.status_code == 200
    run_id = r.json()["run_id"]

    ckpt_dir = runs_dir() / run_id / "checkpoints"
    ckpt_dir.mkdir(parents=True, exist_ok=True)
    (ckpt_dir / "step-500.pt").write_bytes(b"")
    (ckpt_dir / "step-1000.pt").write_bytes(b"")

    detail = client.get(f"/api/runs/{run_id}")
    assert detail.status_code == 200
    db = detail.json()
    assert len(db["checkpoints"]) == 2
    assert db["latest_step"] == 1000


def test_list_runs(client: TestClient) -> None:
    r = client.post(
        "/api/runs",
        json={"name": "list-run", "preset_id": "builtin-normal"},
    )
    assert r.status_code == 200
    run_id = r.json()["run_id"]

    listed = client.get("/api/runs")
    assert listed.status_code == 200
    rows = listed.json()["runs"]
    found = [row for row in rows if row["run_id"] == run_id]
    assert len(found) == 1
    assert found[0]["checkpoint_count"] == 0


# ---------------------------------------------------------------------------
# Stop / resume
# ---------------------------------------------------------------------------


def test_stop_pending_run(client: TestClient) -> None:
    r = client.post(
        "/api/runs",
        json={"name": "stop-pending", "preset_id": "builtin-normal"},
    )
    assert r.status_code == 200
    run_id = r.json()["run_id"]

    stopped = client.post(f"/api/runs/{run_id}/stop")
    assert stopped.status_code == 200
    assert stopped.json()["status"] == "stopped"


def test_resume_stopped_run(client: TestClient, fake_runner: object) -> None:
    r = client.post(
        "/api/runs",
        json={"name": "resume-stopped", "preset_id": "builtin-normal"},
    )
    assert r.status_code == 200
    run_id = r.json()["run_id"]

    client.post(f"/api/runs/{run_id}/stop")
    resumed = client.post(f"/api/runs/{run_id}/resume")
    assert resumed.status_code == 200
    assert resumed.json()["status"] == "pending"
    assert fake_runner.submitted_training == [run_id, run_id]  # type: ignore[comparison-overlap,arg-type]


def test_resume_running_run_409(client: TestClient, db_conn: object) -> None:
    r = client.post(
        "/api/runs",
        json={"name": "resume-running", "preset_id": "builtin-normal"},
    )
    assert r.status_code == 200
    run_id = r.json()["run_id"]

    from server.db import run_set_status

    run_set_status(db_conn, run_id, "running")  # type: ignore[assignment]
    db_conn.commit()

    resumed = client.post(f"/api/runs/{run_id}/resume")
    assert resumed.status_code == 409


def test_delete_run(client: TestClient) -> None:
    r = client.post(
        "/api/runs",
        json={"name": "delete-me", "preset_id": "builtin-normal"},
    )
    assert r.status_code == 200
    run_id = r.json()["run_id"]
    ckpt_dir = runs_dir() / run_id / "checkpoints"
    ckpt_dir.mkdir(parents=True, exist_ok=True)

    deleted = client.delete(f"/api/runs/{run_id}")
    assert deleted.status_code == 200

    afterward = client.get(f"/api/runs/{run_id}")
    assert afterward.status_code == 404
    assert not ckpt_dir.exists()


# ---------------------------------------------------------------------------
# Validation error on missing required field
# ---------------------------------------------------------------------------


def test_invalid_params_422(client: TestClient) -> None:
    r = client.post("/api/runs", json={})
    assert r.status_code == 422
