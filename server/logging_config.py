"""Logging configuration for wogd-ddsp-trainer.

Two modes:
- ``debug``: StreamHandler at DEBUG level (verbose terminal output).
- ``release``: RotatingFileHandler at INFO level (persistent) + StreamHandler
  at WARNING level (quiet terminal).

Log files go to ``<data_dir>/logs/`` with mode-specific names
(``app-debug.log`` / ``app-release.log``), rotated at midnight, 7-day retention.

Mode is read from the ``WOGD_MODE`` environment variable (``"debug"`` or
``"release"``). Defaults to ``"release"`` when absent.
"""

from __future__ import annotations

import logging
import os
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path


def _data_dir() -> Path:
    """Resolve the effective data dir without importing server.paths at module load."""
    local = os.environ.get("LOCALAPPDATA")
    if local:
        return Path(local) / "wogd-ddsp-trainer"
    return Path.cwd()


def _log_dir() -> Path:
    d = _data_dir() / "logs"
    d.mkdir(parents=True, exist_ok=True)
    return d


def setup_logging() -> None:
    """Configure the root logger based on ``WOGD_MODE``.

    Call once at application startup (before any module emits log messages).
    Idempotent: repeated calls are no-ops.
    """
    if logging.getLogger().hasHandlers():
        return

    mode = os.environ.get("WOGD_MODE", "release").strip().lower()
    is_debug = mode == "debug"

    log_dir = _log_dir()
    log_file = log_dir / ("app-debug.log" if is_debug else "app-release.log")

    file_handler = TimedRotatingFileHandler(
        str(log_file),
        when="midnight",
        backupCount=7,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG if is_debug else logging.INFO)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG if is_debug else logging.WARNING)

    formatter = logging.Formatter(
        "%(asctime)s  %(levelname)-8s  %(name)s:%(lineno)d  %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    root = logging.getLogger()
    root.setLevel(logging.DEBUG if is_debug else logging.INFO)
    root.addHandler(file_handler)
    root.addHandler(console_handler)

    logging.getLogger("server").debug(
        "logging initialised: mode=%s file=%s", mode, log_file
    )