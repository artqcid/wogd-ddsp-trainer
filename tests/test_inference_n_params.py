import json

from fastapi import status


def test_synthesize_old_style_params(client, fake_runner):
    response = client.post(
        "/api/inference/synthesize",
        data={"run_id": "test-run", "pitch_shift": 2.0, "loudness_shift": -3.0},
    )
    assert response.status_code == status.HTTP_202_ACCEPTED
    payload = response.json()
    assert payload["status"] == "pending"
    assert "job_id" in payload


def test_synthesize_with_extra_params_json(client, fake_runner):
    extra = json.dumps({"fm_depth": 0.7, "lfo_rate": 2.0})
    response = client.post(
        "/api/inference/synthesize",
        data={
            "run_id": "test-run",
            "pitch_shift": 1.0,
            "loudness_shift": 0.0,
            "params": extra,
        },
    )
    assert response.status_code == status.HTTP_202_ACCEPTED
    payload = response.json()
    assert payload["status"] == "pending"
    assert "job_id" in payload


def test_synthesize_invalid_json_does_not_crash(client, fake_runner):
    response = client.post(
        "/api/inference/synthesize",
        data={
            "run_id": "test-run",
            "pitch_shift": 0.0,
            "loudness_shift": 0.0,
            "params": "not-json",
        },
    )
    assert response.status_code == status.HTTP_202_ACCEPTED
