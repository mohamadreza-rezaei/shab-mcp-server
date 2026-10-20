from __future__ import annotations

from typing import Any


class ShabError(Exception):
    """Normalized error surfaced to MCP tools / agents."""

    code: str = "SHAB_UPSTREAM_ERROR"

    def __init__(self, message: str, *, details: Any = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {"error": self.code, "message": self.message}
        if self.details is not None:
            payload["details"] = self.details
        return payload


class ShabValidationError(ShabError):
    code = "SHAB_VALIDATION_ERROR"


class ShabNotFoundError(ShabError):
    code = "SHAB_NOT_FOUND"


class ShabRateLimitedError(ShabError):
    code = "SHAB_RATE_LIMITED"


class ShabTimeoutError(ShabError):
    code = "SHAB_TIMEOUT"


class ShabUpstreamUnavailableError(ShabError):
    code = "SHAB_UPSTREAM_UNAVAILABLE"


class ShabUpstreamError(ShabError):
    code = "SHAB_UPSTREAM_ERROR"


def tool_error_payload(exc: Exception) -> dict[str, Any]:
    if isinstance(exc, ShabError):
        return exc.to_dict()
    return {"error": "SHAB_UPSTREAM_ERROR", "message": str(exc) or "Unexpected error"}
