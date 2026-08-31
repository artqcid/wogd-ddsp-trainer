from __future__ import annotations

import uuid
from typing import Any

from fastapi import status


def _wav_bytes() -> bytes:
    return b"\x00\x01\x02\x03"


def _mp3_bytes() -> bytes:
    return b"\xff\xe0\x00\x00"


def _upload_files(
    client: Any, *file_tuples: tuple[str, bytes, str], name: str | None = None
) -> dict[str, Any]:
    """POST /api/datasets; returns parsed JSON body."""
    resp = _upload_files_raw(client, *file_tuples, name=name)
    return resp.json()


def _upload_files_raw(
    client: Any, *file_tuples: tuple[str, bytes, str], name: str | None = None
) -> Any:
    """POST /api/datasets returning the raw response; multipart list-of-triples."""
    files = [("files", tup) for tup in file_tuples]
    data = {"name": name} if name is not None else {}
    return client.post("/api/datasets", files=files, data=data)


def test_upload_multiple_files(client: Any, fake_runner: Any) -> None:
    resp = _upload_files_raw(
        client,
        ("a.wav", _wav_bytes(), "audio/wav"),
        ("b.mp3", _mp3_bytes(), "audio/mpeg"),
    )

    assert resp.status_code == status.HTTP_200_OK
    body = resp.json()
    assert body["status"] == "uploaded"
    assert body["file_count"] == 2
    assert body["files"] == ["a.wav", "b.mp3"]

    dataset_id = body["id"]
    assert isinstance(dataset_id, str)
    try:
        uuid.UUID(dataset_id)
    except ValueError as exc:
        raise AssertionError(f"dataset id is not a valid uuid: {dataset_id!r}") from exc

    assert fake_runner.submitted_training == []
    assert fake_runner.submitted_synthesis == []


def test_upload_rejects_unsupported_extension(client: Any, fake_runner: Any) -> None:
    resp = _upload_files_raw(client, ("x.txt", b"hello", "text/plain"))

    assert resp.status_code == status.HTTP_400_BAD_REQUEST
    body = resp.json()
    assert body["error"]["message"] == "unsupported file type: x.txt"
    assert body["error"]["code"] == "BAD_REQUEST"

    assert fake_runner.submitted_training == []
    assert fake_runner.submitted_synthesis == []


def test_upload_missing_files(client: Any, fake_runner: Any) -> None:
    resp = client.post("/api/datasets", files=[], data={})

    assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    assert fake_runner.submitted_training == []
    assert fake_runner.submitted_synthesis == []


def test_list_datasets_empty(client: Any) -> None:
    resp = client.get("/api/datasets")

    assert resp.status_code == status.HTTP_200_OK
    body = resp.json()
    assert isinstance(body, list)
    assert body == []


def test_list_datasets_after_upload(client: Any, fake_runner: Any) -> None:
    upload_resp = _upload_files_raw(
        client,
        ("sample.wav", _wav_bytes(), "audio/wav"),
    )
    assert upload_resp.status_code == status.HTTP_200_OK
    created = upload_resp.json()

    list_resp = client.get("/api/datasets")
    assert list_resp.status_code == status.HTTP_200_OK
    items = list_resp.json()
    assert isinstance(items, list)
    assert len(items) >= 1

    match = next(item for item in items if item["id"] == created["id"])
    assert match["name"] == created["name"]
    assert match["file_count"] == created["file_count"]
    assert match["files"] == created["files"]


def test_get_dataset_detail(client: Any, fake_runner: Any) -> None:
    upload_resp = _upload_files_raw(
        client,
        ("x.wav", _wav_bytes(), "audio/wav"),
        ("y.flac", b"\x00\x01\x02", "audio/flac"),
    )
    assert upload_resp.status_code == status.HTTP_200_OK
    dataset_id = upload_resp.json()["id"]

    detail_resp = client.get(f"/api/datasets/{dataset_id}")
    assert detail_resp.status_code == status.HTTP_200_OK
    detail = detail_resp.json()
    assert detail["id"] == dataset_id
    assert detail["files"] == ["x.wav", "y.flac"]

    missing_resp = client.get("/api/datasets/999999")
    assert missing_resp.status_code == status.HTTP_404_NOT_FOUND
    assert missing_resp.json()["error"]["message"] == "dataset not found"
    assert missing_resp.json()["error"]["code"] == "NOT_FOUND"


def test_dataset_name_unique(client: Any, fake_runner: Any) -> None:
    first_resp = _upload_files_raw(
        client,
        ("a.wav", _wav_bytes(), "audio/wav"),
        name="shared-name",
    )
    assert first_resp.status_code == status.HTTP_200_OK

    second_resp = _upload_files_raw(
        client,
        ("b.wav", _wav_bytes(), "audio/wav"),
        name="shared-name",
    )

    if second_resp.status_code == status.HTTP_409_CONFLICT:
        second_body = second_resp.json()
        assert second_body["error"]["message"] == "dataset name already exists"
        assert second_body["error"]["code"] == "CONFLICT"
        return

    assert second_resp.status_code == status.HTTP_200_OK
    second_body = second_resp.json()
    assert second_body["name"] == "shared-name"
