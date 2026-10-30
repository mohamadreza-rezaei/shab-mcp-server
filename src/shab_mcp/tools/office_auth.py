"""Office staff auth tools (backoffice login).

Callers: server.py. Affected API: POST auth/login|logout, GET bootstrap.
Schemas: mobile 09…, password, staff_token Bearer.
User instruction: Implement the plan as specified, it is attached for your reference.
"""

from __future__ import annotations

from typing import Any

from shab_mcp.client.office_api import OfficeAPIClient
from shab_mcp.errors import ShabAuthenticationError, ShabValidationError, tool_error_payload
from shab_mcp.tools.office_common import (
    extract_access_token,
    normalize_mobile,
    require_staff_token,
    slim_user,
)


async def office_login_impl(*, mobile: str, password: str) -> dict[str, Any]:
    normalized = normalize_mobile(mobile)
    if not (password or "").strip():
        raise ShabValidationError("password is required for office_login.")
    async with OfficeAPIClient() as api:
        data = await api.login(normalized, password)
    token = extract_access_token(data)
    if not token:
        raise ShabAuthenticationError(
            "Login succeeded but no access_token returned. "
            "Check SHAB_API_ORIGIN is non-stateful for Bearer tokens."
        )
    return {
        "ok": True,
        "staff_token": token,
        "user": slim_user(data),
        "message": (
            "Authenticated as staff. Pass staff_token to office_* tools. "
            "Treat the token as a secret."
        ),
    }


async def office_logout_impl(*, staff_token: str) -> dict[str, Any]:
    token = require_staff_token(staff_token)
    async with OfficeAPIClient() as api:
        await api.logout(token)
    return {"ok": True, "message": "Staff logged out; staff_token revoked."}


async def office_bootstrap_impl(*, staff_token: str) -> dict[str, Any]:
    token = require_staff_token(staff_token)
    async with OfficeAPIClient() as api:
        data = await api.bootstrap(token)
    permissions = None
    user_info = None
    if isinstance(data, dict):
        user_info = data.get("user_info") or data.get("user")
        permissions = data.get("permissions") or data.get("permission")
    return {
        "ok": True,
        "user": slim_user(user_info or data),
        "permissions": permissions,
        "bootstrap": data,
    }


async def office_auth_status_impl(*, staff_token: str) -> dict[str, Any]:
    token = require_staff_token(staff_token)
    async with OfficeAPIClient() as api:
        data = await api.bootstrap(token)
    user_info = data.get("user_info") if isinstance(data, dict) else None
    return {"authenticated": True, "user": slim_user(user_info or data)}


async def office_login_safe(**kwargs: Any) -> dict[str, Any]:
    try:
        return await office_login_impl(**kwargs)
    except Exception as exc:
        return tool_error_payload(exc)


async def office_logout_safe(**kwargs: Any) -> dict[str, Any]:
    try:
        return await office_logout_impl(**kwargs)
    except Exception as exc:
        return tool_error_payload(exc)


async def office_bootstrap_safe(**kwargs: Any) -> dict[str, Any]:
    try:
        return await office_bootstrap_impl(**kwargs)
    except Exception as exc:
        return tool_error_payload(exc)


async def office_auth_status_safe(**kwargs: Any) -> dict[str, Any]:
    try:
        return await office_auth_status_impl(**kwargs)
    except Exception as exc:
        return tool_error_payload(exc)
