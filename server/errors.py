"""Lightweight REST error envelope for the wogd-ddsp-trainer web backend.

Provides a stable JSON envelope for all HTTP errors and a handler for
unhandled exceptions (500s). Routes may raise :class:`ApiError` or the
standard ``fastapi.HTTPException``; both are rendered into the same envelope.
"""

from __future__ import annotations

import typing

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

if typing.TYPE_CHECKING:
    from starlette.types import ASGIApp


# ---------------------------------------------------------------------------
# Mapping: HTTP status code -> stable error code string
# ---------------------------------------------------------------------------

_CODE_FOR_STATUS: dict[int, str] = {
    400: "BAD_REQUEST",
    401: "UNAUTHENTICATED",
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    405: "METHOD_NOT_ALLOWED",
    409: "CONFLICT",
    422: "VALIDATION_ERROR",
    429: "TOO_MANY_REQUESTS",
    500: "INTERNAL_ERROR",
    502: "BAD_GATEWAY",
    503: "SERVICE_UNAVAILABLE",
}


def _code_for(status: int) -> str:
    return _CODE_FOR_STATUS.get(status, "UNKNOWN_ERROR")


# ---------------------------------------------------------------------------
# ApiError  (routes may raise this for a typed, envelope-ready error)
# ---------------------------------------------------------------------------


class ApiError(Exception):
    """Raised by routes to return a typed REST error.

    Example: ``raise ApiError(404, "NOT_FOUND", "dataset not found")``.
    """

    def __init__(
        self,
        status_code: int,
        error_code: str,
        message: str,
        *,
        details: dict | None = None,
    ) -> None:
        self.status_code = status_code
        self.error_code = error_code
        self.message = message
        self.details = details or {}

    def to_dict(self) -> dict:
        body: dict = {"error": {"code": self.error_code, "message": self.message}}
        if self.details:
            body["error"]["details"] = self.details
        return body


# ---------------------------------------------------------------------------
# Convenience constructors
# ---------------------------------------------------------------------------


def not_found(message: str = "resource not found", *, details: dict | None = None) -> ApiError:
    return ApiError(404, "NOT_FOUND", message, details=details)


def bad_request(message: str, *, details: dict | None = None) -> ApiError:
    return ApiError(400, "BAD_REQUEST", message, details=details)


def conflict(message: str, *, details: dict | None = None) -> ApiError:
    return ApiError(409, "CONFLICT", message, details=details)


class InternalError(ApiError):
    """500 — should normally be raised only by the fallback handler."""

    def __init__(self, message: str = "internal server error") -> None:
        super().__init__(500, "INTERNAL_ERROR", message)


# ---------------------------------------------------------------------------
# Exception handlers (registered in main.py)
# ---------------------------------------------------------------------------


def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Render a FastAPI HTTPException into the stable envelope."""
    body = {
        "error": {
            "code": _code_for(exc.status_code),
            "message": exc.detail or _CODE_FOR_STATUS.get(exc.status_code, "error"),
        }
    }
    return JSONResponse(status_code=exc.status_code, content=body)


def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Render any unhandled exception as a 500 INTERNAL_ERROR.

    In production this should not leak tracebacks. We keep the message
    generic and log the real exception server-side.
    """
    # Log the real exception server-side (import lazily to avoid circular
    # imports at module load time).
    try:
        import logging
    except Exception:
        logging = None  # type: ignore[assignment]

    if logging is not None:
        logger = logging.getLogger("server")
        logger.exception("unhandled exception: %s", exc)

    message = "internal server error"
    if isinstance(exc, ApiError):
        message = exc.message
    elif isinstance(exc, HTTPException):
        message = exc.detail or message

    body = {"error": {"code": _code_for(500), "message": message}}
    return JSONResponse(status_code=500, content=body)


def install_handlers(app: ASGIApp) -> None:  # pragma: no cover - wired in main
    """Register the error handlers on a FastAPI/Starlette application."""
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
