"""Office act-as-user (v2) — short-lived user token for sandbox tools.

Callers: server.py. Affected API: POST user/{id}/easy/login-token; sandbox auth/logout.
User: Implement the plan as specified.
"""

from __future__ import annotations

from typing import Any

from shab_mcp.client.office_api import OfficeAPIClient
from shab_mcp.client.shab_api import ShabAPIClient
from shab_mcp.errors import ShabAuthenticationError, tool_error_payload
from shab_mcp.tools.office_common import (
    extract_access_token,
    normalize_mobile,
    require_confirm,
    require_staff_token,
    slim_user,
)


def _safe(fn):  # type: ignore[no-untyped-def]
    async def wrapper(**kwargs: Any) -> dict[str, Any]:
        try:
            return await fn(**kwargs)
        except Exception as exc:
            return tool_error_payload(exc)

    return wrapper


async def office_impersonate_user_impl(
    *,
    staff_token: str,
    user_id: int,
    confirm: bool = False,
    agent_mobile: str | None = None,
) -> dict[str, Any]:
    require_confirm(confirm, action="office_impersonate_user")
    token = require_staff_token(staff_token)
    mobile = normalize_mobile(agent_mobile) if agent_mobile else None
    async with OfficeAPIClient() as api:
        data = await api.easy_login_token(token, user_id, mobile)
    access = extract_access_token(data)
    if not access and isinstance(data, dict):
        access = data.get("access_token")
    if not access:
        raise ShabAuthenticationError(
            "Impersonation API did not return access_token. "
            "Ensure shab-api exposes POST user/{id}/easy/login-token."
        )
    user = slim_user(data.get("user") if isinstance(data, dict) else data)
    return {
        "ok": True,
        "access_token": access,
        "agent_id": data.get("agent_id") if isinstance(data, dict) else None,
        "expires_at": data.get("expires_at") if isinstance(data, dict) else None,
        "user": user,
        "audit": {
            "action": "office_impersonate_user",
            "target_user_id": user_id,
        },
        "message": (
            "Short-lived user access_token for sandbox guest/host tools only. "
            "Keep using staff_token for office_* tools. Call office_end_impersonation when done."
        ),
    }


async def office_end_impersonation_impl(*, access_token: str) -> dict[str, Any]:
    token = (access_token or "").strip()
    if not token:
        raise ShabAuthenticationError("access_token (impersonated user) is required.")
    async with ShabAPIClient() as api:
        await api.logout(token)
    return {
        "ok": True,
        "message": "Impersonated user token revoked via sandbox logout.",
        "audit": {"action": "office_end_impersonation"},
    }


office_impersonate_user_safe = _safe(office_impersonate_user_impl)
office_end_impersonation_safe = _safe(office_end_impersonation_impl)
