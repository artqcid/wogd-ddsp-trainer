from __future__ import annotations

import os
import tempfile
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

# Set default env vars into a per-process temp dir BEFORE any server.* import.
_test_dir = tempfile.mkdtemp(prefix="wogd_test_")
os.environ.setdefault("WOGD_DB_PATH", os.path.join(_test_dir, "test.db"))
os.environ.setdefault("WOGD_RUNS_DIR", os.path.join(_test_dir, "runs"))
os.environ.setdefault("WOGD_DATASETS_DIR", os.path.join(_test_dir, "datasets"))

from server.main import app  # noqa: E402 -- needs env setdefault above
from server.tasks import get_task_runner  # noqa: E402 -- needs env setdefault above

# ---------------------------------------------------------------------------
# Fake task runner for the dependency override
# ---------------------------------------------------------------------------


class FakeTaskRunner:
    submitted_training: list[str]
    submitted_synthesis: list[str]

    def __init__(self) -> None:
        self.submitted_training = []
        self.submitted_synthesis = []

    def submit_training(self, run_id: str) -> str:
        self.submitted_training.append(run_id)
        return f"t-{run_id}"

    def submit_synthesis(self, job_id: str) -> str:
        self.submitted_synthesis.append(job_id)
        return f"s-{job_id}"


# ---------------------------------------------------------------------------
# Dependency override — installed once at import time
# ---------------------------------------------------------------------------

# A single FakeTaskRunner instance is shared across all tests via the override.
_shared_runner = FakeTaskRunner()
app.dependency_overrides[get_task_runner] = lambda: _shared_runner


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="function")
def fake_runner() -> Generator[FakeTaskRunner]:
    """Module-singleton FakeTaskRunner; clears submitted_* lists before yield."""
    runner = _shared_runner
    # A single module-level instance is reused across tests, but we reset its
    # lists per test so each test sees a clean state.
    runner.submitted_training.clear()
    runner.submitted_synthesis.clear()
    yield runner
    runner.submitted_training.clear()
    runner.submitted_synthesis.clear()


@pytest.fixture(scope="function")
def tmp_env(tmp_path: str) -> Generator[None]:
    """Set WOGD_DB_PATH, WOGD_RUNS_DIR, WOGD_DATASETS_DIR from tmp_path."""
    os.environ["WOGD_DB_PATH"] = os.path.join(str(tmp_path), "test.db")
    os.environ["WOGD_RUNS_DIR"] = os.path.join(str(tmp_path), "runs")
    os.environ["WOGD_DATASETS_DIR"] = os.path.join(str(tmp_path), "datasets")
    yield


@pytest.fixture(scope="function")
def client(tmp_env: None) -> Generator[TestClient]:
    """TestClient wrapping app; lifespan seeds sqlite + builtins."""
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="function")
def db_conn(tmp_env: None) -> Generator:
    """Direct db connection using the same per-test paths as client."""
    from server import db

    conn = db.connect()
    yield conn
    conn.close()
