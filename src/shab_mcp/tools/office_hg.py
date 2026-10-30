"""Host & Guest office extras — reviews, financials, withdraws.

Callers: server.py. Affected API: review, financial/edit-host-and-guest-records, withdraw-requests.
User: Implement the plan as specified.
"""

from __future__ import annotations

from typing import Any

from shab_mcp.client.office_api import OfficeAPIClient
from shab_mcp.errors import tool_error_payload
from shab_mcp.tools.office_common import require_confirm, require_staff_token


def _safe(fn):  # type: ignore[no-untyped-def]
    async def wrapper(**kwargs: Any) -> dict[str, Any]:
        try:
            return await fn(**kwargs)
        except Exception as exc:
            return tool_error_payload(exc)

    return wrapper


async def office_list_reviews_impl(
    *, staff_token: str, page: int = 1, q: str | None = None
) -> dict[str, Any]:
    token = require_staff_token(staff_token)
    params = {k: v for k, v in {"page": page, "q": q, "search": q}.items() if v is not None}
    async with OfficeAPIClient() as api:
        data = await api.list_reviews(token, params)
    return {"ok": True, "result": data}


async def office_update_review_impl(
    *, staff_token: str, review_id: int, payload: dict[str, Any]
) -> dict[str, Any]:
    token = require_staff_token(staff_token)
    async with OfficeAPIClient() as api:
        data = await api.update_review(token, review_id, payload)
    return {"ok": True, "result": data}


async def office_edit_host_guest_financials_impl(
    *, staff_token: str, confirm: bool = False, payload: dict[str, Any]
) -> dict[str, Any]:
    require_confirm(confirm, action="office_edit_host_guest_financials")
    token = require_staff_token(staff_token)
    async with OfficeAPIClient() as api:
        data = await api.edit_host_guest_financials(token, payload)
    return {"ok": True, "result": data}


async def office_list_withdraw_requests_impl(
    *, staff_token: str, page: int = 1
) -> dict[str, Any]:
    token = require_staff_token(staff_token)
    async with OfficeAPIClient() as api:
        data = await api.list_withdraw_requests(token, {"page": page})
    return {"ok": True, "result": data}


async def office_review_withdraw_impl(
    *,
    staff_token: str,
    request_id: int,
    status: str,
    confirm: bool = False,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    require_confirm(confirm, action="office_review_withdraw")
    token = require_staff_token(staff_token)
    async with OfficeAPIClient() as api:
        data = await api.review_withdraw(token, request_id, status, payload)
    return {"ok": True, "result": data}


office_list_reviews_safe = _safe(office_list_reviews_impl)
office_update_review_safe = _safe(office_update_review_impl)
office_edit_host_guest_financials_safe = _safe(office_edit_host_guest_financials_impl)
office_list_withdraw_requests_safe = _safe(office_list_withdraw_requests_impl)
office_review_withdraw_safe = _safe(office_review_withdraw_impl)
