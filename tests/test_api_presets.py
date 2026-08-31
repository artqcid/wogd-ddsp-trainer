from __future__ import annotations

import json

BOUNDS_KEYS = (
    "hidden_size_min",
    "hidden_size_max",
    "stft_scales_min",
    "stft_scales_max",
    "mixed_precision",
    "gradient_checkpointing",
)

BUILTIN_IDS = {"builtin-fast", "builtin-normal", "builtin-quality"}


def _bounds_body(client):
    r = client.get("/api/presets")
    assert r.status_code == 200
    data = r.json()
    assert "bounds" in data
    return data["bounds"]


def _valid_creation_params(bounds):
    return {
        "hidden_size": bounds["hidden_size_min"],
        "stft_scales": bounds["stft_scales_min"],
        "mixed_precision": bounds["mixed_precision"],
        "gradient_checkpointing": bounds["gradient_checkpointing"],
        "learning_rate": 1e-3,
    }


def _run_payload(bounds):
    return {
        "name": "from-run-source",
        "preset_id": "builtin-fast",
        "params": {
            "hidden_size": bounds["hidden_size_min"],
            "stft_scales": bounds["stft_scales_min"],
            "mixed_precision": bounds["mixed_precision"],
            "gradient_checkpointing": bounds["gradient_checkpointing"],
            "learning_rate": 1e-3,
        },
    }


def test_get_presets_listing(client):
    r = client.get("/api/presets")
    assert r.status_code == 200

    data = r.json()
    assert set(data) >= {"bounds", "gpu", "presets"}

    bounds = data["bounds"]
    assert isinstance(bounds, dict)
    for key in BOUNDS_KEYS:
        assert key in bounds, f"bounds missing key {key!r}"

    presets = data["presets"]
    assert isinstance(presets, list)

    preset_ids = {p["id"] for p in presets}
    assert preset_ids >= BUILTIN_IDS

    for p in presets:
        if p["id"] in BUILTIN_IDS:
            assert p["is_builtin"] is True
            assert "hidden_size" in p["params"]


def test_create_custom_in_bounds(client, fake_runner, db_conn):
    bounds = _bounds_body(client)
    params = _valid_creation_params(bounds)

    r = client.post("/api/presets", json={"name": "in-bounds-1", "params": params})
    assert r.status_code in (200, 201)

    data = r.json()
    assert data["name"] == "in-bounds-1"
    assert data["is_builtin"] is False
    assert isinstance(data["clamped_fields"], list)
    assert data["clamped_fields"] == []
    assert data["params"] == params
    assert data["created_from_run_id"] is None
    assert "id" in data

    by_name = _preset_by_name(db_conn, "in-bounds-1")
    assert by_name is not None
    assert by_name["id"] == data["id"]


def test_create_custom_clamps(client, fake_runner, db_conn):
    bounds = _bounds_body(client)
    params = _valid_creation_params(bounds)
    params["hidden_size"] = bounds["hidden_size_max"] + 100

    r = client.post("/api/presets", json={"name": "clamped-1", "params": params})
    assert r.status_code in (200, 201)

    data = r.json()
    assert data["name"] == "clamped-1"
    assert data["is_builtin"] is False
    assert "hidden_size" in data["clamped_fields"]
    assert data["params"]["hidden_size"] == bounds["hidden_size_max"]

    by_name = _preset_by_name(db_conn, "clamped-1")
    assert by_name is not None
    assert by_name["params"]["hidden_size"] == bounds["hidden_size_max"]


def test_create_duplicate_name_409(client, fake_runner, db_conn):
    bounds = _bounds_body(client)
    params = _valid_creation_params(bounds)

    first = client.post("/api/presets", json={"name": "dup-1", "params": params})
    assert first.status_code in (200, 201)

    second = client.post("/api/presets", json={"name": "dup-1", "params": params})
    assert second.status_code == 409


def test_update_custom_preset(client, fake_runner, db_conn):
    bounds = _bounds_body(client)
    params = _valid_creation_params(bounds)

    create = client.post(
        "/api/presets",
        json={"name": "update-me-1", "params": params},
    )
    assert create.status_code in (200, 201)
    preset_id = create.json()["id"]

    new_params = _valid_creation_params(bounds)
    new_params["hidden_size"] = bounds["hidden_size_max"] + 100

    update = client.put(
        f"/api/presets/{preset_id}",
        json={"params": new_params},
    )
    assert update.status_code == 200

    updated = update.json()
    assert updated["params"]["hidden_size"] == bounds["hidden_size_max"]
    assert "hidden_size" in updated["clamped_fields"]

    builtin = client.put(
        "/api/presets/builtin-fast",
        json={"params": {"hidden_size": bounds["hidden_size_min"]}},
    )
    assert builtin.status_code == 403

    unknown = client.put(
        "/api/presets/does-not-exist",
        json={"params": {"hidden_size": bounds["hidden_size_min"]}},
    )
    assert unknown.status_code == 404


def test_delete_custom_preset(client, fake_runner, db_conn):
    bounds = _bounds_body(client)
    params = _valid_creation_params(bounds)

    create = client.post(
        "/api/presets",
        json={"name": "delete-me-1", "params": params},
    )
    assert create.status_code in (200, 201)
    preset_id = create.json()["id"]

    delete = client.delete(f"/api/presets/{preset_id}")
    assert delete.status_code == 200

    after = _preset_by_name(db_conn, "delete-me-1")
    assert after is None

    list_after = client.get("/api/presets")
    assert list_after.status_code == 200
    after_ids = {p["id"] for p in list_after.json()["presets"]}
    assert preset_id not in after_ids

    delete_again = client.delete(f"/api/presets/{preset_id}")
    assert delete_again.status_code == 404

    builtin = client.delete("/api/presets/builtin-fast")
    assert builtin.status_code == 403

    unknown = client.delete("/api/presets/does-not-exist")
    assert unknown.status_code == 404


def test_create_preset_from_run(client, fake_runner, db_conn):
    bounds = _bounds_body(client)

    run_create = client.post("/api/runs", json=_run_payload(bounds))
    assert run_create.status_code in (200, 201)
    run_data = run_create.json()
    run_id = run_data["run_id"]

    name = f"from-run-{run_id}"
    from_run = client.post(
        f"/api/presets/from-run/{run_id}",
        json={"name": name},
    )
    assert from_run.status_code in (200, 201)

    created = from_run.json()
    assert created["name"] == name
    assert created["is_builtin"] is False
    assert created["created_from_run_id"] == run_id
    assert "id" in created
    assert "clamped_fields" in created

    by_id = _preset_by_id(db_conn, created["id"])
    assert by_id is not None
    assert by_id["created_from_run_id"] == run_id

    unknown = client.post(
        "/api/presets/from-run/does-not-exist",
        json={"name": "nope"},
    )
    assert unknown.status_code == 404


def _preset_by_name(conn, name):
    cur = conn.execute(
        "SELECT id, name, is_builtin, params, created_from_run_id FROM presets WHERE name = ?",
        (name,),
    )
    row = cur.fetchone()
    if row is None:
        return None
    return {
        "id": row[0],
        "name": row[1],
        "is_builtin": row[2],
        "params": json.loads(row[3]) if row[3] else {},
        "created_from_run_id": row[4],
    }


def _preset_by_id(conn, preset_id):
    cur = conn.execute(
        "SELECT id, name, is_builtin, params, created_from_run_id FROM presets WHERE id = ?",
        (preset_id,),
    )
    row = cur.fetchone()
    if row is None:
        return None
    return {
        "id": row[0],
        "name": row[1],
        "is_builtin": row[2],
        "params": json.loads(row[3]) if row[3] else {},
        "created_from_run_id": row[4],
    }
