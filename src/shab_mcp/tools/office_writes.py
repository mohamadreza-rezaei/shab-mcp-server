"""Office write tools — reserves, refunds, notifications, notes.

Callers: server.py. Affected API: backoffice reserve/payment/notification/notes.
User: Implement the plan as specified.
"""

from __future__ import annotations

from typing import Any

from shab_mcp.client.office_api import OfficeAPIClient
from shab_mcp.errors import ShabValidationError, tool_error_payload
from shab_mcp.tools.office_common import require_confirm, require_staff_token


def _safe(fn):  # type: ignore[no-untyped-def]
    async def wrapper(**kwargs: Any) -> dict[str, Any]:
        try:
            return await fn(**kwargs)
        except Exception as exc:
            return tool_error_payload(exc)

    return wrapper


async def office_change_reserve_status_impl(
    *,
    staff_token: str,
    reservation_id: int,
    transition: str,
    confirm: bool = False,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    require_confirm(confirm, action="office_change_reserve_status")
    token = require_staff_token(staff_token)
    body = {"reservation_id": reservation_id, "transition": transition}
    if payload:
        body.update(payload)
    async with OfficeAPIClient() as api:
        data = await api.change_reserve_status(token, body)
    return {"ok": True, "result": data}


async def office_cancel_reserve_impl(
    *,
    staff_token: str,
    reserve_id: int,
    confirm: bool = False,
    reason: str | None = None,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    require_confirm(confirm, action="office_cancel_reserve")
    token = require_staff_token(staff_token)
    body: dict[str, Any] = dict(payload or {})
    if reason:
        body["reason"] = reason
    async with OfficeAPIClient() as api:
        data = await api.cancel_reserve(token, reserve_id, body)
    return {"ok": True, "result": data}


async def office_tag_reserve_impl(
    *, staff_token: str, reservation_id: int, tag: str, payload: dict[str, Any] | None = None
) -> dict[str, Any]:
    token = require_staff_token(staff_token)
    body = {"tag": tag, **(payload or {})}
    async with OfficeAPIClient() as api:
        data = await api.tag_reserve(token, reservation_id, body)
    return {"ok": True, "result": data}


async def office_search_payments_impl(
    *, staff_token: str, q: str | None = None, page: int = 1
) -> dict[str, Any]:
    token = require_staff_token(staff_token)
    params = {k: v for k, v in {"q": q, "search": q, "page": page}.items() if v is not None}
    async with OfficeAPIClient() as api:
        data = await api.search_payments(token, params)
    return {"ok": True, "result": data}


async def office_refund_payment_impl(
    *,
    staff_token: str,
    payment_id: int,
    confirm: bool = False,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    require_confirm(confirm, action="office_refund_payment")
    token = require_staff_token(staff_token)
    async with OfficeAPIClient() as api:
        data = await api.refund_payment(token, payment_id, payload)
    return {"ok": True, "result": data}


async def office_list_message_templates_impl(*, staff_token: str) -> dict[str, Any]:
    token = require_staff_token(staff_token)
    async with OfficeAPIClient() as api:
        data = await api.list_message_templates(token)
    return {"ok": True, "templates": data}


async def office_send_notification_impl(
    *,
    staff_token: str,
    confirm: bool = False,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    require_confirm(confirm, action="office_send_notification")
    token = require_staff_token(staff_token)
    if not payload:
        raise ShabValidationError("payload is required for office_send_notification.")
    async with OfficeAPIClient() as api:
        data = await api.send_notification(token, payload)
    return {"ok": True, "result": data}


async def office_add_note_impl(
    *, staff_token: str, payload: dict[str, Any]
) -> dict[str, Any]:
    token = require_staff_token(staff_token)
    async with OfficeAPIClient() as api:
        data = await api.add_note(token, payload)
    return {"ok": True, "result": data}


office_change_reserve_status_safe = _safe(office_change_reserve_status_impl)
office_cancel_reserve_safe = _safe(office_cancel_reserve_impl)
office_tag_reserve_safe = _safe(office_tag_reserve_impl)
office_search_payments_safe = _safe(office_search_payments_impl)
office_refund_payment_safe = _safe(office_refund_payment_impl)
office_list_message_templates_safe = _safe(office_list_message_templates_impl)
office_send_notification_safe = _safe(office_send_notification_impl)
office_add_note_safe = _safe(office_add_note_impl)
