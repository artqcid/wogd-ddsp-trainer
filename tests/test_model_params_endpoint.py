import torch
from fastapi.testclient import TestClient

from server.main import app
from server.paths import runs_dir

client = TestClient(app)


def _make_checkpoint(run_id: str) -> str:
    ckpt_dir = runs_dir() / run_id / "checkpoints"
    ckpt_dir.mkdir(parents=True, exist_ok=True)
    path = ckpt_dir / "step-100.pt"
    state = {
        "step": 100,
        "model_state_dict": {},
        "optimizer_state_dict": {},
        "config": {"hidden_size": 32, "n_harmonics": 20},
        "model_tier": "standard",
        "variant_flags": {},
        "param_manifest": {
            "format": "wogd-vst-params",
            "version": "1.0",
            "params": [
                {
                    "slot": 1,
                    "name": "Pitch Shift",
                    "description": "d",
                    "param_type": "continuous",
                    "min_value": -24.0,
                    "max_value": 24.0,
                    "default_value": 0.0,
                    "mapping": "linear",
                    "unit_hint": "semitones",
                    "group": "Pitch",
                    "neutone_slot": 1,
                },
                {
                    "slot": 2,
                    "name": "Loudness",
                    "description": "d",
                    "param_type": "continuous",
                    "min_value": -20.0,
                    "max_value": 20.0,
                    "default_value": 0.0,
                    "mapping": "linear",
                    "unit_hint": "dB",
                    "group": "Loudness",
                    "neutone_slot": 2,
                },
                {
                    "slot": 3,
                    "name": "Noise Level",
                    "description": "d",
                    "param_type": "continuous",
                    "min_value": 0.0,
                    "max_value": 1.0,
                    "default_value": 0.5,
                    "mapping": "linear",
                    "unit_hint": "",
                    "group": "Texture",
                    "neutone_slot": 3,
                },
                {
                    "slot": 4,
                    "name": "Reverb Mix",
                    "description": "d",
                    "param_type": "continuous",
                    "min_value": 0.0,
                    "max_value": 1.0,
                    "default_value": 0.3,
                    "mapping": "linear",
                    "unit_hint": "",
                    "group": "Reverb",
                    "neutone_slot": 4,
                },
            ],
        },
    }
    torch.save(state, str(path))
    return f"{run_id}/step-100.pt"


def test_get_params_returns_manifest(client) -> None:
    _make_checkpoint("test-run-1")
    resp = client.get("/api/models/test-run-1/step-100.pt/params")
    assert resp.status_code == 200
    data = resp.json()
    assert data["format"] == "wogd-vst-params"
    assert len(data["params"]) == 4


def test_get_params_missing_checkpoint(client) -> None:
    resp = client.get("/api/models/missing-run/nonexistent.pt/params")
    assert resp.status_code == 404


def test_get_params_old_checkpoint_defaults(client) -> None:
    ckpt_dir = runs_dir() / "old-run" / "checkpoints"
    ckpt_dir.mkdir(parents=True, exist_ok=True)
    path = ckpt_dir / "step-50.pt"
    torch.save({"step": 50, "model_tier": "standard", "variant_flags": {}}, str(path))
    resp = client.get("/api/models/old-run/step-50.pt/params")
    assert resp.status_code == 200
    data = resp.json()
    assert data["format"] == "wogd-vst-params"
    assert len(data["params"]) == 4


def test_put_params_updates_manifest(client) -> None:
    _make_checkpoint("put-run")
    new_params = [
        {
            "slot": 1,
            "name": "Alpha",
            "description": "a",
            "param_type": "continuous",
            "min_value": 0.0,
            "max_value": 1.0,
            "default_value": 0.5,
            "mapping": "linear",
            "unit_hint": "",
            "group": "",
            "neutone_slot": 1,
        },
        {
            "slot": 2,
            "name": "Beta",
            "description": "b",
            "param_type": "continuous",
            "min_value": 0.0,
            "max_value": 1.0,
            "default_value": 0.5,
            "mapping": "linear",
            "unit_hint": "",
            "group": "",
            "neutone_slot": 2,
        },
    ]
    body = {"format": "wogd-vst-params", "version": "1.0", "params": new_params}
    resp = client.put("/api/models/put-run/step-100.pt/params", json=body)
    assert resp.status_code == 200
    data = resp.json()
    assert data["params"][0]["name"] == "Alpha"

    resp2 = client.get("/api/models/put-run/step-100.pt/params")
    assert resp2.json()["params"][0]["name"] == "Alpha"


def test_put_params_too_many_fails(client) -> None:
    _make_checkpoint("too-many-run")
    many = [
        {
            "slot": i,
            "name": f"P{i}",
            "description": "d",
            "param_type": "continuous",
            "min_value": 0.0,
            "max_value": 1.0,
            "default_value": 0.5,
            "mapping": "linear",
            "unit_hint": "",
            "group": "",
            "neutone_slot": None,
        }
        for i in range(1, 18)
    ]
    body = {"format": "wogd-vst-params", "version": "1.0", "params": many}
    resp = client.put("/api/models/too-many-run/step-100.pt/params", json=body)
    assert resp.status_code == 422


def test_put_params_missing_checkpoint(client) -> None:
    body = {"format": "wogd-vst-params", "version": "1.0", "params": []}
    resp = client.put("/api/models/no-run/no.pt/params", json=body)
    assert resp.status_code == 404


def test_export_custom_vst_endpoint_returns_file(client) -> None:
    from model.ddsp_model import DDSPConfig, DDSPModel

    _make_checkpoint("export-run-1")
    model = DDSPModel(DDSPConfig(hidden_size=32, n_harmonics=20))
    ckpt_dir = runs_dir() / "export-run-1" / "checkpoints"
    ckpt_dir.mkdir(parents=True, exist_ok=True)
    state = {
        "step": 100,
        "model_state_dict": model.state_dict(),
        "optimizer_state_dict": {},
        "config": {"hidden_size": 32, "n_harmonics": 20, "n_noise_bins": 32},
        "model_tier": "standard",
        "variant_flags": {},
        "param_manifest": {
            "format": "wogd-vst-params",
            "version": "1.0",
            "params": [
                {
                    "slot": 1,
                    "name": "Pitch Shift",
                    "description": "d",
                    "param_type": "continuous",
                    "min_value": -24.0,
                    "max_value": 24.0,
                    "default_value": 0.0,
                    "mapping": "linear",
                    "unit_hint": "semitones",
                    "group": "Pitch",
                    "neutone_slot": 1,
                },
                {
                    "slot": 2,
                    "name": "Loudness",
                    "description": "d",
                    "param_type": "continuous",
                    "min_value": -20.0,
                    "max_value": 20.0,
                    "default_value": 0.0,
                    "mapping": "linear",
                    "unit_hint": "dB",
                    "group": "Loudness",
                    "neutone_slot": 2,
                },
                {
                    "slot": 3,
                    "name": "Noise Level",
                    "description": "d",
                    "param_type": "continuous",
                    "min_value": 0.0,
                    "max_value": 1.0,
                    "default_value": 0.5,
                    "mapping": "linear",
                    "unit_hint": "",
                    "group": "Texture",
                    "neutone_slot": 3,
                },
                {
                    "slot": 4,
                    "name": "Reverb Mix",
                    "description": "d",
                    "param_type": "continuous",
                    "min_value": 0.0,
                    "max_value": 1.0,
                    "default_value": 0.3,
                    "mapping": "linear",
                    "unit_hint": "",
                    "group": "Reverb",
                    "neutone_slot": 4,
                },
            ],
        },
    }
    torch.save(state, str(ckpt_dir / "step-100.pt"))
    resp = client.post("/api/models/export-run-1/step-100.pt/export/custom-vst")
    assert resp.status_code == 200
    assert len(resp.content) > 0


def test_export_custom_vst_endpoint_missing_checkpoint(client) -> None:
    resp = client.post("/api/models/no-run/no.pt/export/custom-vst")
    assert resp.status_code == 404
