"""Guest profile tools for Shab MCP v0.5."""

from __future__ import annotations

from typing import Any

from shab_mcp.client import ShabAPIClient
from shab_mcp.errors import ShabValidationError, tool_error_payload
from shab_mcp.tools.auth import require_access_token


def _extract_list(data: Any) -> list[dict[str, Any]]:
    if isinstance(data, list):
        return [x for x in data if isinstance(x, dict)]
    if not isinstance(data, dict):
        return []
    for key in ("records", "discounts", "bookmarks", "data", "items"):
        val = data.get(key)
        if isinstance(val, list):
            return [x for x in val if isinstance(x, dict)]
    return []


def _slim(obj: Any, *, depth: int = 0) -> Any:
    if depth > 4:
        return None
    if isinstance(obj, list):
        return [_slim(x, depth=depth + 1) for x in obj[:50]]
    if isinstance(obj, dict):
        return {k: _slim(v, depth=depth + 1) for k, v in obj.items() if k not in {"html", "links"}}
    return obj


async def get_user_profile_impl(*, access_token: str) -> dict[str, Any]:
    token = require_access_token(access_token)
    async with ShabAPIClient() as api:
        data = await api.get_current_user(token)
    return {"user": _slim(data)}


async def update_user_profile_impl(
    *,
    access_token: str,
    email: str | None = None,
    gender: str | None = None,
    tel: str | None = None,
    birthdate: str | None = None,
    about_me: str | None = None,
    living_city: str | None = None,
    living_province: str | None = None,
    address: str | None = None,
    confirm: bool = False,
) -> dict[str, Any]:
    if not confirm:
        raise ShabValidationError("update_user_profile requires confirm=true.")
    token = require_access_token(access_token)
    payload = {
        k: v
        for k, v in {
            "email": email,
            "gender": gender,
            "tel": tel,
            "birthdate": birthdate,
            "about_me": about_me,
            "living_city": living_city,
            "living_province": living_province,
            "address": address,
        }.items()
        if v is not None
    }
    if not payload:
        raise ShabValidationError("Provide at least one profile field to update.")
    async with ShabAPIClient() as api:
        data = await api.update_user(token, payload=payload)
    return {"ok": True, "user": _slim(data)}


async def list_bookmarks_impl(*, access_token: str, page: int = 1, per_page: int = 20) -> dict[str, Any]:
    token = require_access_token(access_token)
    async with ShabAPIClient() as api:
        data = await api.list_bookmarks(token, page=page, per_page=per_page)
    records = _extract_list(data)
    slim_records = []
    for r in records:
        slim_records.append(
            {
                "id": r.get("id"),
                "title": r.get("title") or r.get("name"),
                "city": (r.get("location") or {}).get("city") if isinstance(r.get("location"), dict) else r.get("city"),
                "price": (r.get("pricing") or {}).get("price_after_discount") if isinstance(r.get("pricing"), dict) else None,
                "cover": (r.get("cover_photo") or r.get("photos") or {}).get("url")
                if isinstance(r.get("cover_photo") or r.get("photos"), dict)
                else None,
            }
        )
    return {"page": page, "bookmarks": slim_records or _slim(data)}


async def toggle_bookmark_impl(*, access_token: str, accommodation_id: int, confirm: bool = False) -> dict[str, Any]:
    if not confirm:
        raise ShabValidationError("toggle_bookmark requires confirm=true.")
    if accommodation_id < 1:
        raise ShabValidationError("accommodation_id must be positive.")
    token = require_access_token(access_token)
    async with ShabAPIClient() as api:
        data = await api.toggle_bookmark(token, house_id=accommodation_id)
    return {"ok": True, "accommodation_id": accommodation_id, "result": _slim(data)}


async def list_discounts_impl(*, access_token: str) -> dict[str, Any]:
    token = require_access_token(access_token)
    async with ShabAPIClient() as api:
        data = await api.list_discounts(token)
    return {"discounts": _slim(_extract_list(data) or data), "currency": "Toman"}


def _safe(fn):  # type: ignore[no-untyped-def]
    async def wrapper(**kwargs: Any) -> dict[str, Any]:
        try:
            return await fn(**kwargs)
        except Exception as exc:
            return tool_error_payload(exc)

    return wrapper


get_user_profile_safe = _safe(get_user_profile_impl)
update_user_profile_safe = _safe(update_user_profile_impl)
list_bookmarks_safe = _safe(list_bookmarks_impl)
toggle_bookmark_safe = _safe(toggle_bookmark_impl)
list_discounts_safe = _safe(list_discounts_impl)
