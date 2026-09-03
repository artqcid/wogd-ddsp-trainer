"""SQLite persistence layer for the M4 web backend.

Creates and manages the presets, runs, synthesis_jobs and meta tables.
Uses stdlib sqlite3 only. Callers are responsible for committing transactions.
"""

from __future__ import annotations

import json
import sqlite3
import typing
from contextlib import suppress
from pathlib import Path


def get_db_path() -> Path:
    """Return the database path (see :func:`server.paths.db_path`)."""
    from server.paths import db_path

    return db_path()


def connect(path: Path | None = None) -> sqlite3.Connection:
    """Open (or create) the database and set row_factory to sqlite3.Row."""
    target: Path = path if path is not None else get_db_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    conn: sqlite3.Connection = sqlite3.connect(target)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    """Create all required tables if they do not exist."""
    cur: sqlite3.Cursor = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS presets (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            is_builtin INTEGER NOT NULL DEFAULT 0,
            params TEXT NOT NULL,
            created_from_run_id TEXT,
            model_tier TEXT NOT NULL DEFAULT 'standard',
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS runs (
            run_id TEXT PRIMARY KEY,
            name TEXT,
            status TEXT NOT NULL DEFAULT 'pending',
            config_json TEXT NOT NULL DEFAULT '{}',
            created_from_preset TEXT,
            dataset_id TEXT,
            model_tier TEXT NOT NULL DEFAULT 'standard',
            error TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now')),
            stop_requested INTEGER NOT NULL DEFAULT 0,
            current_step INTEGER NOT NULL DEFAULT 0,
            last_loss REAL
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS synthesis_jobs (
            job_id TEXT PRIMARY KEY,
            run_id TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            params_json TEXT NOT NULL DEFAULT '{}',
            artifact_path TEXT,
            error TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now'))
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT)
        """
    )

    _migrate_columns(conn)


def _migrate_columns(conn: sqlite3.Connection) -> None:
    """Add columns that newer schema versions require (safe for existing DBs)."""
    cur = conn.cursor()
    for table, col, col_def in [
        ("runs", "error", "TEXT"),
        ("synthesis_jobs", "error", "TEXT"),
        ("runs", "current_step", "INTEGER NOT NULL DEFAULT 0"),
        ("runs", "last_loss", "REAL"),
    ]:
        with suppress(sqlite3.OperationalError):
            cur.execute(f"ALTER TABLE {table} ADD COLUMN {col} {col_def}")
    _migrate_add_model_tier(cur)
    _migrate_drop_presets_name_unique(cur)


def _migrate_drop_presets_name_unique(cur: sqlite3.Cursor) -> None:
    """Drop the legacy ``UNIQUE(name)`` constraint from the presets table.

    Pre-M14 databases were created with ``name TEXT NOT NULL UNIQUE``; since the
    per-tier builtin presets reuse the same names (FAST/NORMAL/QUALITY) across
    all tiers, seeding the additional tiers fails with a UNIQUE constraint
    violation on those legacy databases. SQLite cannot ALTER a column
    constraint away, so the table is rebuilt without it (data preserved).
    """
    unique = [row for row in cur.execute("PRAGMA index_list(presets)") if row[3] == "u"]
    if not unique:
        return
    with suppress(sqlite3.OperationalError):
        cur.execute("PRAGMA foreign_keys = OFF")
        cur.execute("ALTER TABLE presets RENAME TO presets_old")
        cur.execute(
            """
            CREATE TABLE presets (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                is_builtin INTEGER NOT NULL DEFAULT 0,
                params TEXT NOT NULL,
                created_from_run_id TEXT,
                model_tier TEXT NOT NULL DEFAULT 'standard',
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
            """
        )
        cur.execute(
            """
            INSERT INTO presets (id, name, is_builtin, params, created_from_run_id,
                                 model_tier, created_at, updated_at)
            SELECT id, name, is_builtin, params, created_from_run_id,
                   COALESCE(model_tier, 'standard'), created_at, updated_at
            FROM presets_old
            """
        )
        cur.execute("DROP TABLE presets_old")


def _migrate_add_model_tier(cur: sqlite3.Cursor) -> None:
    """Add model_tier column to presets and runs if not already present."""
    for table in ("presets", "runs"):
        cur.execute(f"PRAGMA table_info({table})")
        cols = {row[1] for row in cur.fetchall()}
        if "model_tier" not in cols:
            cur.execute(
                f"ALTER TABLE {table} ADD COLUMN model_tier TEXT NOT NULL DEFAULT 'standard'"
            )


def _bool(row: sqlite3.Row, key: str) -> bool:
    """Convert an INTEGER column to Python bool."""
    return bool(row[key])


def _dict(row: sqlite3.Row, key: str) -> dict:
    """Parse a JSON TEXT column into a dict."""
    raw: str = row[key]
    if raw is None or raw == "":
        return {}
    return json.loads(raw)


def _parse_preset(row: sqlite3.Row) -> dict:
    """Turn a presets Row into a public dict."""
    return {
        "id": row["id"],
        "name": row["name"],
        "is_builtin": _bool(row, "is_builtin"),
        "params": _dict(row, "params"),
        "created_from_run_id": row["created_from_run_id"],
        "model_tier": row["model_tier"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def _parse_run(row: sqlite3.Row) -> dict:
    """Turn a runs Row into a public dict."""
    return {
        "run_id": row["run_id"],
        "name": row["name"],
        "status": row["status"],
        "config": _dict(row, "config_json"),
        "created_from_preset": row["created_from_preset"],
        "dataset_id": row["dataset_id"],
        "model_tier": row["model_tier"],
        "error": row["error"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
        "stop_requested": _bool(row, "stop_requested"),
        "current_step": int(row["current_step"] or 0),
        "last_loss": row["last_loss"],
    }


def _parse_synthjob(row: sqlite3.Row) -> dict:
    """Turn a synthesis_jobs Row into a public dict."""
    return {
        "job_id": row["job_id"],
        "run_id": row["run_id"],
        "status": row["status"],
        "params": _dict(row, "params_json"),
        "artifact_path": row["artifact_path"],
        "error": row["error"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


# ---------------------------------------------------------------------------
# Presets
# ---------------------------------------------------------------------------


def preset_create(
    conn: sqlite3.Connection,
    id: str,
    name: str,
    is_builtin: bool,
    params: dict,
    created_from_run_id: str | None = None,
    model_tier: str = "standard",
) -> None:
    """Insert a new presets row."""
    cur: sqlite3.Cursor = conn.cursor()
    cur.execute(
        """
        INSERT INTO presets (id, name, is_builtin, params, created_from_run_id, model_tier)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            id,
            name,
            int(is_builtin),
            json.dumps(params),
            created_from_run_id,
            model_tier,
        ),
    )


def preset_all(conn: sqlite3.Connection) -> list[dict]:
    """Return all presets as a list of public dicts."""
    cur: sqlite3.Cursor = conn.cursor()
    cur.execute("SELECT * FROM presets")
    return [_parse_preset(row) for row in cur.fetchall()]


def preset_get(conn: sqlite3.Connection, preset_id: str) -> dict | None:
    """Return a single presets by id, or None."""
    cur: sqlite3.Cursor = conn.cursor()
    cur.execute("SELECT * FROM presets WHERE id = ?", (preset_id,))
    row: sqlite3.Row | None = cur.fetchone()
    if row is None:
        return None
    return _parse_preset(row)


def preset_by_name(conn: sqlite3.Connection, name: str) -> dict | None:
    """Return a single presets by name (first match), or None."""
    cur: sqlite3.Cursor = conn.cursor()
    cur.execute("SELECT * FROM presets WHERE name = ?", (name,))
    row: sqlite3.Row | None = cur.fetchone()
    if row is None:
        return None
    return _parse_preset(row)


def preset_by_name_and_tier(conn: sqlite3.Connection, name: str, tier: str) -> dict | None:
    """Return a single presets by (name, model_tier) composite, or None."""
    cur: sqlite3.Cursor = conn.cursor()
    cur.execute("SELECT * FROM presets WHERE name = ? AND model_tier = ?", (name, tier))
    row: sqlite3.Row | None = cur.fetchone()
    if row is None:
        return None
    return _parse_preset(row)


def preset_update(
    conn: sqlite3.Connection,
    preset_id: str,
    *,
    name: str | None = None,
    params: dict | None = None,
) -> bool:
    """Update optional name/params fields and bump updated_at.

    Returns True if a row was affected.
    """
    set_parts: list[str] = []
    values: list[typing.Any] = []

    if name is not None:
        set_parts.append("name = ?")
        values.append(name)

    if params is not None:
        set_parts.append("params = ?")
        values.append(json.dumps(params))

    if not set_parts:
        return False

    set_parts.append("updated_at = datetime('now')")
    values.append(preset_id)

    cur: sqlite3.Cursor = conn.cursor()
    query: str = f"UPDATE presets SET {', '.join(set_parts)} WHERE id = ?"
    cur.execute(query, values)
    return cur.rowcount > 0


def preset_delete(conn: sqlite3.Connection, preset_id: str) -> bool:
    """Delete a presets by id.

    Returns True if a row was affected.
    """
    cur: sqlite3.Cursor = conn.cursor()
    cur.execute("DELETE FROM presets WHERE id = ?", (preset_id,))
    return cur.rowcount > 0


def preset_delete_custom_all(conn: sqlite3.Connection) -> int:
    """Delete all non-builtin presets and return the rowcount."""
    cur: sqlite3.Cursor = conn.cursor()
    cur.execute("DELETE FROM presets WHERE is_builtin = 0")
    return cur.rowcount


# ---------------------------------------------------------------------------
# Runs
# ---------------------------------------------------------------------------


def run_create(
    conn: sqlite3.Connection,
    run_id: str,
    name: str | None,
    config: dict,
    dataset_id: str | None = None,
    created_from_preset: str | None = None,
    model_tier: str = "standard",
) -> None:
    """Insert a new run row."""
    cur: sqlite3.Cursor = conn.cursor()
    cur.execute(
        """
        INSERT INTO runs (run_id, name, config_json, dataset_id, created_from_preset, model_tier)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            run_id,
            name,
            json.dumps(config),
            dataset_id,
            created_from_preset,
            model_tier,
        ),
    )


def run_get(conn: sqlite3.Connection, run_id: str) -> dict | None:
    """Return a single run by run_id, or None."""
    cur: sqlite3.Cursor = conn.cursor()
    cur.execute("SELECT * FROM runs WHERE run_id = ?", (run_id,))
    row: sqlite3.Row | None = cur.fetchone()
    if row is None:
        return None
    return _parse_run(row)


def run_all(conn: sqlite3.Connection) -> list[dict]:
    """Return all runs as a list of public dicts."""
    cur: sqlite3.Cursor = conn.cursor()
    cur.execute("SELECT * FROM runs")
    return [_parse_run(row) for row in cur.fetchall()]


def run_set_status(conn: sqlite3.Connection, run_id: str, status: str) -> None:
    """Update run status and bump updated_at."""
    cur: sqlite3.Cursor = conn.cursor()
    cur.execute(
        """
        UPDATE runs SET status = ?, updated_at = datetime('now') WHERE run_id = ?
        """,
        (status, run_id),
    )


def run_set_stop_requested(conn: sqlite3.Connection, run_id: str, flag: bool) -> None:
    """Set the stop_requested flag on a run."""
    cur: sqlite3.Cursor = conn.cursor()
    cur.execute(
        """
        UPDATE runs SET stop_requested = ?, updated_at = datetime('now') WHERE run_id = ?
        """,
        (int(flag), run_id),
    )


def run_is_stop_requested(conn: sqlite3.Connection, run_id: str) -> bool:
    """Return the stop_requested flag for a run."""
    cur: sqlite3.Cursor = conn.cursor()
    cur.execute(
        "SELECT stop_requested FROM runs WHERE run_id = ?",
        (run_id,),
    )
    row: sqlite3.Row | None = cur.fetchone()
    if row is None:
        return False
    return bool(row["stop_requested"])


def run_delete(conn: sqlite3.Connection, run_id: str) -> bool:
    """Delete a run by run_id.

    Returns True if a row was affected.
    """
    cur: sqlite3.Cursor = conn.cursor()
    cur.execute("DELETE FROM runs WHERE run_id = ?", (run_id,))
    return cur.rowcount > 0


def run_set_error(conn: sqlite3.Connection, run_id: str, error: str) -> None:
    """Set the error field on a run."""
    cur: sqlite3.Cursor = conn.cursor()
    cur.execute(
        "UPDATE runs SET error = ?, updated_at = datetime('now') WHERE run_id = ?",
        (error, run_id),
    )


def run_update_progress(
    conn: sqlite3.Connection,
    run_id: str,
    current_step: int,
    last_loss: float | None,
) -> None:
    """Update the live training progress columns for a run."""
    cur: sqlite3.Cursor = conn.cursor()
    cur.execute(
        "UPDATE runs SET current_step = ?, last_loss = ?,"
        " updated_at = datetime('now') WHERE run_id = ?",
        (current_step, last_loss, run_id),
    )


# ---------------------------------------------------------------------------
# Synthesis jobs
# ---------------------------------------------------------------------------


def synth_create(
    conn: sqlite3.Connection,
    job_id: str,
    run_id: str,
    params: dict,
) -> None:
    """Insert a new synthesis job row."""
    cur: sqlite3.Cursor = conn.cursor()
    cur.execute(
        """
        INSERT INTO synthesis_jobs (job_id, run_id, params_json)
        VALUES (?, ?, ?)
        """,
        (job_id, run_id, json.dumps(params)),
    )


def synth_get(conn: sqlite3.Connection, job_id: str) -> dict | None:
    """Return a single synthesis job by job_id, or None."""
    cur: sqlite3.Cursor = conn.cursor()
    cur.execute("SELECT * FROM synthesis_jobs WHERE job_id = ?", (job_id,))
    row: sqlite3.Row | None = cur.fetchone()
    if row is None:
        return None
    return _parse_synthjob(row)


def synth_update(
    conn: sqlite3.Connection,
    job_id: str,
    *,
    status: str | None = None,
    artifact_path: str | None = None,
    error: str | None = None,
) -> None:
    """Update optional status/artifact_path/error fields and bump updated_at."""
    set_parts: list[str] = []
    values: list[typing.Any] = []

    if status is not None:
        set_parts.append("status = ?")
        values.append(status)

    if artifact_path is not None:
        set_parts.append("artifact_path = ?")
        values.append(artifact_path)

    if error is not None:
        set_parts.append("error = ?")
        values.append(error)

    if not set_parts:
        return

    set_parts.append("updated_at = datetime('now')")
    values.append(job_id)

    cur: sqlite3.Cursor = conn.cursor()
    query: str = f"UPDATE synthesis_jobs SET {', '.join(set_parts)} WHERE job_id = ?"
    cur.execute(query, values)


# ---------------------------------------------------------------------------
# Meta
# ---------------------------------------------------------------------------


def meta_get(conn: sqlite3.Connection, key: str) -> str | None:
    """Return the value for a meta key, or None."""
    cur: sqlite3.Cursor = conn.cursor()
    cur.execute("SELECT value FROM meta WHERE key = ?", (key,))
    row: sqlite3.Row | None = cur.fetchone()
    if row is None:
        return None
    return row["value"]


def meta_set(conn: sqlite3.Connection, key: str, value: str) -> None:
    """Insert or replace a meta key/value pair."""
    cur: sqlite3.Cursor = conn.cursor()
    cur.execute(
        """
        INSERT INTO meta (key, value) VALUES (?, ?)
        ON CONFLICT(key) DO UPDATE SET value = excluded.value
        """,
        (key, value),
    )
