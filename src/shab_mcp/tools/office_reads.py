"""Office read tools (users, reserves, houses, chat, notes).

Callers: server.py. Affected API: backoffice GET user|reserve|house|chat|notes.
User: Implement the plan as specified.
"""

from __future__ import annotations

from typing import Any

from shab_mcp.client.office_api import OfficeAPIClient
from shab_mcp.errors import tool_error_payload
from shab_mcp.tools.office_common import require_staff_token


def _params(**kwargs: Any) -> dict[str, Any]:
    return {k: v for k, v in kwargs.items() if v is not None}


async def office_search_users_impl(
    *, staff_token: str, q: str | None = None, page: int = 1
) -> dict[str, Any]:
    token = require_staff_token(staff_token)
    async with OfficeAPIClient() as api:
        data = await api.search_users(token, _params(q=q, search=q, page=page))
    return {"ok": True, "result": data}


async def office_get_user_impl(*, staff_token: str, user_id: int) -> dict[str, Any]:
    token = require_staff_token(staff_token)
    async with OfficeAPIClient() as api:
        data = await api.get_user(token, user_id)
    return {"ok": True, "user": data}


async def office_get_user_stats_impl(*, staff_token: str, user_id: int) -> dict[str, Any]:
    token = require_staff_token(staff_token)
    async with OfficeAPIClient() as api:
        data = await api.get_user_stats(token, user_id)
    return {"ok": True, "stats": data}


async def office_search_reserves_impl(
    *, staff_token: str, q: str | None = None, page: int = 1
) -> dict[str, Any]:
    token = require_staff_token(staff_token)
    async with OfficeAPIClient() as api:
        data = await api.search_reserves(token, _params(q=q, search=q, page=page))
    return {"ok": True, "result": data}


async def office_get_reserve_impl(*, staff_token: str, reserve_id: int) -> dict[str, Any]:
    token = require_staff_token(staff_token)
    async with OfficeAPIClient() as api:
        data = await api.get_reserve(token, reserve_id)
    return {"ok": True, "reserve": data}


async def office_get_reserve_chat_impl(*, staff_token: str, reserve_id: int) -> dict[str, Any]:
    token = require_staff_token(staff_token)
    async with OfficeAPIClient() as api:
        data = await api.get_reserve_chat(token, reserve_id)
    return {"ok": True, "chat": data}


async def office_get_reserve_transitions_impl(
    *, staff_token: str, reserve_id: int
) -> dict[str, Any]:
    token = require_staff_token(staff_token)
    async with OfficeAPIClient() as api:
        data = await api.get_reserve_transitions(token, reserve_id)
    return {"ok": True, "transitions": data}


async def office_search_houses_impl(
    *, staff_token: str, q: str | None = None, page: int = 1
) -> dict[str, Any]:
    token = require_staff_token(staff_token)
    async with OfficeAPIClient() as api:
        data = await api.search_houses(token, _params(q=q, search=q, page=page))
    return {"ok": True, "result": data}


async def office_get_house_impl(*, staff_token: str, house_id: int) -> dict[str, Any]:
    token = require_staff_token(staff_token)
    async with OfficeAPIClient() as api:
        data = await api.get_house(token, house_id)
    return {"ok": True, "house": data}


async def office_list_chats_impl(*, staff_token: str, page: int = 1) -> dict[str, Any]:
    token = require_staff_token(staff_token)
    async with OfficeAPIClient() as api:
        data = await api.list_chats(token, _params(page=page))
    return {"ok": True, "result": data}


async def office_list_notes_impl(*, staff_token: str, page: int = 1) -> dict[str, Any]:
    token = require_staff_token(staff_token)
    async with OfficeAPIClient() as api:
        data = await api.list_notes(token, _params(page=page))
    return {"ok": True, "result": data}


async def office_get_notes_impl(
    *, staff_token: str, note_type: str, model_id: int
) -> dict[str, Any]:
    token = require_staff_token(staff_token)
    async with OfficeAPIClient() as api:
        data = await api.get_notes(token, note_type, model_id)
    return {"ok": True, "notes": data}


def _safe(fn):  # type: ignore[no-untyped-def]
    async def wrapper(**kwargs: Any) -> dict[str, Any]:
        try:
            return await fn(**kwargs)
        except Exception as exc:
            return tool_error_payload(exc)

    return wrapper


office_search_users_safe = _safe(office_search_users_impl)
office_get_user_safe = _safe(office_get_user_impl)
office_get_user_stats_safe = _safe(office_get_user_stats_impl)
office_search_reserves_safe = _safe(office_search_reserves_impl)
office_get_reserve_safe = _safe(office_get_reserve_impl)
office_get_reserve_chat_safe = _safe(office_get_reserve_chat_impl)
office_get_reserve_transitions_safe = _safe(office_get_reserve_transitions_impl)
office_search_houses_safe = _safe(office_search_houses_impl)
office_get_house_safe = _safe(office_get_house_impl)
office_list_chats_safe = _safe(office_list_chats_impl)
office_list_notes_safe = _safe(office_list_notes_impl)
office_get_notes_safe = _safe(office_get_notes_impl)
