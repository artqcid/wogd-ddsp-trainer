"""Central location/path resolution for the wogd-ddsp-trainer app.

Windows-convention layout (M6.1):

- ``install_dir`` — where the application code lives. In development that is the
  repository root; after a real installation it is the install directory (e.g.
  ``C:\\Program Files\\wogd-ddsp-trainer``). Effectively read-only at runtime.
- ``data_dir``    — the "Sammelwurzel": the single data root that holds the
  ``datasets/`` and ``runs/`` output folders and (by default) the SQLite DB.
  It follows the Windows convention "user data lives under the user profile",
  i.e. ``%LOCALAPPDATA%\\wogd-ddsp-trainer``, identical in development and
  after installation. It is the only location a user may change live (REST).

Precedence for ``data_dir`` (highest first):

1. ``WOGD_DATA_DIR`` environment variable (tests / advanced users).
2. Value persisted in the SQLite ``meta`` table (key ``data_dir``), set via
   ``PUT /api/settings``.
3. Platform default: ``%LOCALAPPDATA%\\wogd-ddsp-trainer``.

The SQLite DB itself lives at a *stable* bootstrap location — env
``WOGD_DB_PATH`` or ``<default data root>/wogd-trainer.db`` — so that the app can
always find it (and read the persisted ``data_dir``) before the datasets/runs
folders move. Datasets and runs always resolve under the *effective* ``data_dir``.
"""

from __future__ import annotations

import os
from pathlib import Path

APP_NAME = "wogd-ddsp-trainer"
META_DATA_DIR = "data_dir"


def install_dir() -> Path:
    """Return the directory holding the application code (repo root / install dir)."""
    return Path(__file__).resolve().parents[1]


def _platform_data_root() -> Path:
    """Return the OS-appropriate per-user data root.

    Windows: ``%LOCALAPPDATA%\\wogd-ddsp-trainer``. Fallbacks for non-Windows
    (Linux/macOS) use the XDG data dir or the install dir so behavior stays sane.
    """
    if os.name == "nt":
        local = os.environ.get("LOCALAPPDATA")
        if local:
            return Path(local) / APP_NAME
    xdg = os.environ.get("XDG_DATA_HOME")
    if xdg:
        return Path(xdg) / APP_NAME
    if os.name == "posix":
        home = os.environ.get("HOME")
        if home:
            return Path(home) / ".local" / "share" / APP_NAME
    return install_dir() / "data"


def default_data_dir() -> Path:
    """Return the default data root (no env / no persisted override)."""
    return _platform_data_root()


def db_path() -> Path:
    """Return the stable database location.

    Env ``WOGD_DB_PATH`` wins; otherwise the database lives at the default data
    root. This location does NOT move when the user changes ``data_dir`` so the
    app can always bootstrap (read the persisted ``data_dir``) on startup.
    """
    env = os.environ.get("WOGD_DB_PATH")
    if env:
        return Path(env)
    return default_data_dir() / "wogd-trainer.db"


def _persisted_data_dir() -> Path | None:
    """Read the persisted ``data_dir`` override from the DB meta table, if any."""
    from server.db import connect  # local import to avoid a hard cycle

    try:
        conn = connect()
        try:
            from server.db import meta_get

            value = meta_get(conn, META_DATA_DIR)
        finally:
            conn.close()
    except Exception:
        return None
    if not value:
        return None
    return Path(value)


def data_dir() -> Path:
    """Return the effective data root (env override > persisted > default)."""
    env = os.environ.get("WOGD_DATA_DIR")
    if env:
        return Path(env)
    persisted = _persisted_data_dir()
    if persisted is not None:
        return persisted
    return default_data_dir()


def datasets_dir() -> Path:
    """Return the datasets output folder under the effective data root."""
    return data_dir() / "datasets"


def runs_dir() -> Path:
    """Return the runs output folder under the effective data root."""
    return data_dir() / "runs"


def ensure_data_dirs() -> None:
    """Create the effective data root subfolders if missing."""
    d = data_dir()
    (d / "datasets").mkdir(parents=True, exist_ok=True)
    (d / "runs").mkdir(parents=True, exist_ok=True)
    _migrate_from_cwd(d)


def _migrate_from_cwd(new_root: Path) -> None:
    """Best-effort one-time migration of old cwd-relative datasets/runs.

    During development the effective data root moved from ``cwd/`` (the repo
    root) to ``%LOCALAPPDATA%\\wogd-ddsp-trainer``. If the process' cwd is the
    app root and it still contains ``datasets/`` or ``runs/`` that the new data
    root does not, move them over once (guarded by a marker file).
    """
    if Path.cwd() != install_dir():
        return
    for name in ("datasets", "runs"):
        src = Path.cwd() / name
        dst = new_root / name
        if not src.is_dir():
            continue
        if dst.exists() and any(dst.iterdir()):
            continue  # target already has content; leave it
        try:
            dst.mkdir(parents=True, exist_ok=True)
            for child in src.iterdir():
                import shutil

                shutil.move(str(child), str(dst / child.name))
            marker = dst / ".wogd-migrated"
            marker.touch()
        except OSError:
            pass


def persist_data_dir(value: str | None) -> None:
    """Persist (or clear, when ``None``) the ``data_dir`` override in DB meta."""
    from server.db import connect, meta_get, meta_set

    conn = connect()
    try:
        if value is None:
            if meta_get(conn, META_DATA_DIR) is not None:
                meta_set(conn, META_DATA_DIR, "")
        else:
            meta_set(conn, META_DATA_DIR, value)
        conn.commit()
    finally:
        conn.close()


def settings_summary() -> dict:
    """Return the effective path configuration for the REST settings endpoint."""
    return {
        "install_dir": str(install_dir()),
        "data_dir": str(data_dir()),
        "db_path": str(db_path()),
        "datasets_dir": str(datasets_dir()),
        "runs_dir": str(runs_dir()),
        "data_is_default": data_dir() == default_data_dir(),
    }
