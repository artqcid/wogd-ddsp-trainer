"""TensorBoard subprocess lifecycle management (stdlib only)."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from subprocess import DEVNULL


class TensorBoardError(RuntimeError):
    """Raised when TensorBoard startup fails."""


class TensorBoardManager:
    """Manages a TensorBoard subprocess per-instance."""

    def __init__(
        self, logdir: str = "runs", port: int | None = None, executable: str | None = None
    ) -> None:
        self.logdir = logdir
        self.port = int(os.environ.get("WOGD_TB_PORT", 6006)) if port is None else port
        if executable is not None:
            self._executable = executable
        elif shutil.which("tensorboard") is not None:
            self._executable = shutil.which("tensorboard")  # type: ignore[assignment]
        else:
            self._executable = None
            self._use_module = True
            return
        self._use_module = False

    def _build_cmd(self) -> list[str]:
        if self._use_module:
            return [
                sys.executable,
                "-m",
                "tensorboard.main",
                "--logdir",
                self.logdir,
                "--host",
                "127.0.0.1",
                "--port",
                str(self.port),
            ]
        return [
            self._executable,  # type: ignore[arg-type]
            "--logdir",
            self.logdir,
            "--host",
            "127.0.0.1",
            "--port",
            str(self.port),
        ]

    def launch(self) -> None:
        if self.is_running():
            return
        try:
            self._proc: subprocess.Popen[bytes] = subprocess.Popen(
                self._build_cmd(), stdout=DEVNULL, stderr=DEVNULL
            )
        except OSError as exc:
            raise TensorBoardError(f"Failed to launch TensorBoard: {exc}") from exc

    def is_running(self) -> bool:
        return self._proc is not None and self._proc.poll() is None

    def ensure_running(self) -> None:
        if not self.is_running():
            self.launch()

    def stop(self) -> None:
        if self.is_running():
            try:
                self._proc.terminate()
                self._proc.wait(timeout=5)
            except Exception:
                pass

    @property
    def url(self) -> str:
        return f"http://127.0.0.1:{self.port}"


_default_manager: TensorBoardManager | None = None


def get_manager() -> TensorBoardManager:
    global _default_manager
    if _default_manager is None:
        _default_manager = TensorBoardManager()
    return _default_manager
