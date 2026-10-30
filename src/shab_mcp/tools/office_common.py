"""Shared helpers for office_* tools.

Callers: tools/office_*.py. Affected API: backoffice auth helpers.
User: Implement the plan as specified.
"""

from __future__ import annotations

from typing import Any

from shab_mcp.errors import ShabAuthenticationError, ShabValidationError
from shab_mcp.tools.auth import normalize_mobile


def require_staff_token(staff_token: str | None) -> str:
    token = (staff_token or "").strip()
    if not token:
        raise ShabAuthenticationError(
            "staff_token is required. Call office_login first."
        )
    return token


def require_confirm(confirm: bool, *, action: str) -> None:
    if not confirm:
        raise ShabValidationError(
            f"Refusing {action} without confirm=true. Re-call with confirm=true after user approval."
        )


def extract_access_token(data: Any) -> str | None:
    if not isinstance(data, dict):
        return None
    token = data.get("access_token")
    if token:
        return str(token)
    nested = data.get("data")
    if isinstance(nested, dict) and nested.get("access_token"):
        return str(nested["access_token"])
    return None


def slim_user(data: Any) -> dict[str, Any]:
    if not isinstance(data, dict):
        return {"raw": data}
    user = data.get("user") or data.get("user_info") or data
    if not isinstance(user, dict):
        return {"raw": user}
    return {
        k: user.get(k)
        for k in ("id", "mobile", "name", "first_name", "last_name", "email")
        if user.get(k) is not None
    }


__all__ = [
    "normalize_mobile",
    "require_staff_token",
    "require_confirm",
    "extract_access_token",
    "slim_user",
]
