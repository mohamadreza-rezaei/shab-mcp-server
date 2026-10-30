"""Host calendar, pricing, and host-side reserves for Shab MCP v0.7."""

from __future__ import annotations

from typing import Any

from shab_mcp.client import ShabAPIClient
from shab_mcp.errors import ShabValidationError, tool_error_payload
from shab_mcp.normalize import normalize_booking_summary
from shab_mcp.tools.auth import require_access_token


def _extract_list(data: Any) -> list[dict[str, Any]]:
    if isinstance(data, list):
        return [x for x in data if isinstance(x, dict)]
    if not isinstance(data, dict):
        return []
    for key in ("records", "days", "calendar", "houses", "data", "items"):
        val = data.get(key)
        if isinstance(val, list):
            return [x for x in val if isinstance(x, dict)]
    return []


def _slim(obj: Any, *, depth: int = 0) -> Any:
    if depth > 5:
        return None
    if isinstance(obj, list):
        return [_slim(x, depth=depth + 1) for x in obj[:120]]
    if isinstance(obj, dict):
        return {k: _slim(v, depth=depth + 1) for k, v in obj.items() if k not in {"html"}}
    return obj


async def get_host_calendar_impl(
    *,
    access_token: str,
    house_id: int,
    from_date: str,
    to_date: str,
) -> dict[str, Any]:
    token = require_access_token(access_token)
    if house_id < 1:
        raise ShabValidationError("house_id must be positive.")
    fd, td = (from_date or "").strip(), (to_date or "").strip()
    if not fd or not td:
        raise ShabValidationError("from_date and to_date are required (Jalali YYYY-MM-DD).")
    async with ShabAPIClient() as api:
        data = await api.get_host_calendar(token, house_id, from_date=fd, to_date=td)
    return {
        "house_id": house_id,
        "from_date": fd,
        "to_date": td,
        "calendar": _slim(data),
    }


async def update_host_calendar_impl(
    *,
    access_token: str,
    house_id: int,
    payload: dict[str, Any],
    confirm: bool = False,
) -> dict[str, Any]:
    if not confirm:
        raise ShabValidationError("update_host_calendar requires confirm=true.")
    token = require_access_token(access_token)
    if house_id < 1:
        raise ShabValidationError("house_id must be positive.")
    if not payload:
        raise ShabValidationError(
            "payload required (e.g. {action, dates} or price fields + dates)."
        )
    async with ShabAPIClient() as api:
        data = await api.edit_house_calendar(token, house_id, payload=payload)
    return {"ok": True, "house_id": house_id, "result": _slim(data)}


async def get_house_pricing_impl(
    *, access_token: str, house_ids: list[int]
) -> dict[str, Any]:
    token = require_access_token(access_token)
    ids = [int(x) for x in (house_ids or []) if int(x) > 0]
    if not ids:
        raise ShabValidationError("house_ids must be a non-empty list.")
    async with ShabAPIClient() as api:
        data = await api.get_house_pricing(token, house_ids=ids)
    return {"house_ids": ids, "pricing": _slim(data), "currency": "Toman"}


async def update_house_pricing_impl(
    *,
    access_token: str,
    house_prices: list[dict[str, Any]],
    confirm: bool = False,
) -> dict[str, Any]:
    if not confirm:
        raise ShabValidationError("update_house_pricing requires confirm=true.")
    token = require_access_token(access_token)
    if not house_prices:
        raise ShabValidationError("house_prices list is required.")
    async with ShabAPIClient() as api:
        data = await api.store_house_pricing(token, house_prices=house_prices)
    return {"ok": True, "result": _slim(data)}


async def get_price_suggestion_impl(
    *, access_token: str, house_id: int, dates: list[str]
) -> dict[str, Any]:
    token = require_access_token(access_token)
    if house_id < 1:
        raise ShabValidationError("house_id must be positive.")
    if not dates:
        raise ShabValidationError("dates list (Jalali YYYY-MM-DD) is required.")
    async with ShabAPIClient() as api:
        data = await api.get_price_suggestion(token, house_id, dates=dates)
    return {"house_id": house_id, "dates": dates, "suggestion": _slim(data), "currency": "Toman"}


async def list_host_reserves_impl(
    *, access_token: str, page: int = 1
) -> dict[str, Any]:
    token = require_access_token(access_token)
    async with ShabAPIClient() as api:
        data = await api.list_reserves(token, page=page, reserve_type="host")
    trips = [normalize_booking_summary(r) for r in _extract_list(data)]
    return {"page": page, "reserves": trips, "role": "host"}


async def get_booking_guest_impl(*, access_token: str, reserve_id: str) -> dict[str, Any]:
    token = require_access_token(access_token)
    rid = (reserve_id or "").strip()
    if not rid:
        raise ShabValidationError("reserve_id is required.")
    async with ShabAPIClient() as api:
        data = await api.get_reserve_guest(token, rid)
    return {"reserve_id": rid, "guest": _slim(data)}


def _safe(fn):  # type: ignore[no-untyped-def]
    async def wrapper(**kwargs: Any) -> dict[str, Any]:
        try:
            return await fn(**kwargs)
        except Exception as exc:
            return tool_error_payload(exc)

    return wrapper


get_host_calendar_safe = _safe(get_host_calendar_impl)
update_host_calendar_safe = _safe(update_host_calendar_impl)
get_house_pricing_safe = _safe(get_house_pricing_impl)
update_house_pricing_safe = _safe(update_house_pricing_impl)
get_price_suggestion_safe = _safe(get_price_suggestion_impl)
list_host_reserves_safe = _safe(list_host_reserves_impl)
get_booking_guest_safe = _safe(get_booking_guest_impl)
