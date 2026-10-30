"""Office followups + easy login link.

Callers: server.py. Affected API: followup/*, house support-status, easy/login-link.
User: Implement the plan as specified.
"""

from __future__ import annotations

from typing import Any

from shab_mcp.client.office_api import OfficeAPIClient
from shab_mcp.errors import tool_error_payload
from shab_mcp.tools.office_common import (
    normalize_mobile,
    require_confirm,
    require_staff_token,
)


def _safe(fn):  # type: ignore[no-untyped-def]
    async def wrapper(**kwargs: Any) -> dict[str, Any]:
        try:
            return await fn(**kwargs)
        except Exception as exc:
            return tool_error_payload(exc)

    return wrapper


async def office_list_checkin_followups_impl(
    *, staff_token: str, page: int = 1
) -> dict[str, Any]:
    token = require_staff_token(staff_token)
    async with OfficeAPIClient() as api:
        data = await api.list_checkin_followups(token, {"page": page})
    return {"ok": True, "result": data}


async def office_update_checkin_followup_impl(
    *, staff_token: str, reservation_id: int, payload: dict[str, Any]
) -> dict[str, Any]:
    token = require_staff_token(staff_token)
    async with OfficeAPIClient() as api:
        data = await api.update_checkin_followup(token, reservation_id, payload)
    return {"ok": True, "result": data}


async def office_list_cancellation_followups_impl(
    *, staff_token: str, page: int = 1
) -> dict[str, Any]:
    token = require_staff_token(staff_token)
    async with OfficeAPIClient() as api:
        data = await api.list_cancellation_followups(token, {"page": page})
    return {"ok": True, "result": data}


async def office_list_review_followups_impl(
    *, staff_token: str, page: int = 1
) -> dict[str, Any]:
    token = require_staff_token(staff_token)
    async with OfficeAPIClient() as api:
        data = await api.list_review_followups(token, {"page": page})
    return {"ok": True, "result": data}


async def office_set_house_support_status_impl(
    *, staff_token: str, confirm: bool = False, payload: dict[str, Any]
) -> dict[str, Any]:
    require_confirm(confirm, action="office_set_house_support_status")
    token = require_staff_token(staff_token)
    async with OfficeAPIClient() as api:
        data = await api.set_house_support_status(token, payload)
    return {"ok": True, "result": data}


async def office_generate_easy_login_link_impl(
    *,
    staff_token: str,
    user_id: int,
    agent_mobile: str,
    confirm: bool = False,
) -> dict[str, Any]:
    require_confirm(confirm, action="office_generate_easy_login_link")
    token = require_staff_token(staff_token)
    mobile = normalize_mobile(agent_mobile)
    async with OfficeAPIClient() as api:
        data = await api.easy_login_link(token, user_id, mobile)
    link = None
    if isinstance(data, dict):
        link = data.get("link")
        nested = data.get("data")
        if link is None and isinstance(nested, dict):
            link = nested.get("link")
    return {
        "ok": True,
        "link": link,
        "result": data,
        "message": (
            "Browser/SMS handoff link for human use. "
            "For MCP act-as-user sandbox tools use office_impersonate_user (v2)."
        ),
    }


office_list_checkin_followups_safe = _safe(office_list_checkin_followups_impl)
office_update_checkin_followup_safe = _safe(office_update_checkin_followup_impl)
office_list_cancellation_followups_safe = _safe(office_list_cancellation_followups_impl)
office_list_review_followups_safe = _safe(office_list_review_followups_impl)
office_set_house_support_status_safe = _safe(office_set_house_support_status_impl)
office_generate_easy_login_link_safe = _safe(office_generate_easy_login_link_impl)
