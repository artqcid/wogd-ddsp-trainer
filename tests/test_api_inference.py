from __future__ import annotations

from fastapi import status

from server.db import synth_update
from server.tasks import runs_dir


def _run_id() -> str:
    return "test-run"


def _wav_bytes() -> bytes:
    """Minimal valid-ish WAV for coverage of artifact round-trips."""
    return b"".join(
        [
            b"RIFF",
            b"\x00\x00\x00\x00",
            b"WAVE",
            b"fmt ",
            b"\x10\x00\x00\x00",
            b"\x01\x00",
            b"\x01\x00",
            b"\x44\xac\x00\x00",
            b"\x88\x58\x01\x00",
            b"\x02\x00",
            b"\x10\x00",
            b"data",
            b"\x00\x00\x00\x00",
        ]
    )


def test_synthesize_submits_job(client, fake_runner):
    response = client.post(
        "/api/inference/synthesize",
        files={"audio": ("input.wav", _wav_bytes(), "audio/wav")},
        data={"run_id": _run_id()},
    )

    assert response.status_code == status.HTTP_202_ACCEPTED
    payload = response.json()
    job_id = payload["job_id"]
    assert isinstance(job_id, str) and job_id
    assert payload["task_id"] == f"s-{job_id}"
    assert payload["status"] == "pending"
    assert job_id in fake_runner.submitted_synthesis


def test_synthesize_without_audio_returns_202(client):
    response = client.post(
        "/api/inference/synthesize",
        data={"run_id": _run_id()},
    )

    assert response.status_code == status.HTTP_202_ACCEPTED
    payload = response.json()
    assert payload["task_id"].startswith("s-")


def test_get_job_pending_then_completed(client, db_conn):
    post = client.post(
        "/api/inference/synthesize",
        files={"audio": ("input.wav", _wav_bytes(), "audio/wav")},
        data={"run_id": _run_id()},
    )
    assert post.status_code == status.HTTP_202_ACCEPTED
    job_id = post.json()["job_id"]

    pending = client.get(f"/api/inference/jobs/{job_id}")
    assert pending.status_code == status.HTTP_200_OK
    assert pending.json()["status"] == "pending"
    assert pending.json()["artifact_url"] is None

    artifact_path = runs_dir() / _run_id() / "synthesis" / f"{job_id}.wav"
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_path.write_bytes(_wav_bytes())

    synth_update(
        db_conn,
        job_id,
        status="completed",
        artifact_path=str(artifact_path),
    )
    db_conn.commit()

    completed = client.get(f"/api/inference/jobs/{job_id}")
    assert completed.status_code == status.HTTP_200_OK
    body = completed.json()
    assert body["status"] == "completed"
    assert body["artifact_url"] == f"/api/inference/artifacts/{job_id}"


def test_get_job_unknown_404(client):
    response = client.get("/api/inference/jobs/does-not-exist")
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_artifact_before_complete_409(client):
    post = client.post(
        "/api/inference/synthesize",
        files={"audio": ("input.wav", _wav_bytes(), "audio/wav")},
        data={"run_id": _run_id()},
    )
    assert post.status_code == status.HTTP_202_ACCEPTED
    job_id = post.json()["job_id"]

    response = client.get(f"/api/inference/artifacts/{job_id}")
    assert response.status_code == status.HTTP_409_CONFLICT


def test_artifact_unknown_404(client):
    response = client.get("/api/inference/artifacts/does-not-exist")
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_artifact_after_complete_200(client, db_conn):
    post = client.post(
        "/api/inference/synthesize",
        files={"audio": ("input.wav", _wav_bytes(), "audio/wav")},
        data={"run_id": _run_id()},
    )
    assert post.status_code == status.HTTP_202_ACCEPTED
    job_id = post.json()["job_id"]

    artifact_path = runs_dir() / _run_id() / "synthesis" / f"{job_id}.wav"
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    written = _wav_bytes()
    artifact_path.write_bytes(written)

    synth_update(
        db_conn,
        job_id,
        status="completed",
        artifact_path=str(artifact_path),
    )
    db_conn.commit()

    response = client.get(f"/api/inference/artifacts/{job_id}")
    assert response.status_code == status.HTTP_200_OK
    assert response.content == written
