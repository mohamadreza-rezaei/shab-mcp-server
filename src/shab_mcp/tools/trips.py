"""Trips and host tools for Shab MCP v0.2.

Importers/callers: server.py registers list_trips, get_booking, get_booking_host,
get_host_profile.
Affected API: GET reserve, reserve/trips, reserve/{id}, reserve/{id}/host, profile/{user}.
Schemas: access_token required for trips; public user_id for host profile.
User instruction: "Implement the plan as specified" (trips + host contact/profile).
"""

from __future__ import annotations

from typing import Any

from shab_mcp.client import ShabAPIClient
from shab_mcp.errors import ShabValidationError, tool_error_payload
from shab_mcp.normalize import (
    normalize_booking_summary,
    normalize_host_contact,
    normalize_host_profile,
)
from shab_mcp.tools.auth import require_access_token


def _extract_list(data: Any) -> list[dict[str, Any]]:
    if isinstance(data, list):
        return [x for x in data if isinstance(x, dict)]
    if not isinstance(data, dict):
        return []
    for key in ("records", "trips", "reserves", "data", "items"):
        val = data.get(key)
        if isinstance(val, list):
            return [x for x in val if isinstance(x, dict)]
    return []


async def list_trips_impl(*, access_token: str, page: int = 1) -> dict[str, Any]:
    token = require_access_token(access_token)
    if page < 1:
        raise ShabValidationError("page must be >= 1.")

    async with ShabAPIClient() as api:
        try:
            data = await api.list_trips(token, page=page)
        except Exception:
            data = await api.list_reserves(token, page=page)

    trips = [normalize_booking_summary(r) for r in _extract_list(data)]
    pagination = data.get("pagination") if isinstance(data, dict) else {}
    return {
        "page": (pagination or {}).get("current_page", page),
        "total": (pagination or {}).get("total"),
        "trips": trips,
        "currency": "Toman",
    }


async def get_booking_impl(*, access_token: str, reserve_id: str) -> dict[str, Any]:
    token = require_access_token(access_token)
    rid = (reserve_id or "").strip()
    if not rid:
        raise ShabValidationError("reserve_id is required.")

    async with ShabAPIClient() as api:
        data = await api.get_reserve(token, rid)

    summary = normalize_booking_summary(data)
    summary["raw_status_fields"] = {
        "last_state": (data or {}).get("last_state") if isinstance(data, dict) else None,
        "status": (data or {}).get("status") if isinstance(data, dict) else None,
    }
    return summary


async def get_booking_host_impl(*, access_token: str, reserve_id: str) -> dict[str, Any]:
    token = require_access_token(access_token)
    rid = (reserve_id or "").strip()
    if not rid:
        raise ShabValidationError("reserve_id is required.")

    async with ShabAPIClient() as api:
        data = await api.get_reserve_host(token, rid)

    return {
        "reserve_id": rid,
        "host": normalize_host_contact(data),
        "note": "Host phone is available only when the reservation state allows guest contact.",
    }


async def get_host_profile_impl(*, user_id: str) -> dict[str, Any]:
    uid = (user_id or "").strip()
    if not uid:
        raise ShabValidationError("user_id (public host uid) is required.")

    async with ShabAPIClient() as api:
        data = await api.get_public_profile(uid)

    return normalize_host_profile(data)


async def list_trips_safe(**kwargs: Any) -> dict[str, Any]:
    try:
        return await list_trips_impl(**kwargs)
    except Exception as exc:
        return tool_error_payload(exc)


async def get_booking_safe(**kwargs: Any) -> dict[str, Any]:
    try:
        return await get_booking_impl(**kwargs)
    except Exception as exc:
        return tool_error_payload(exc)


async def get_booking_host_safe(**kwargs: Any) -> dict[str, Any]:
    try:
        return await get_booking_host_impl(**kwargs)
    except Exception as exc:
        return tool_error_payload(exc)


async def get_host_profile_safe(**kwargs: Any) -> dict[str, Any]:
    try:
        return await get_host_profile_impl(**kwargs)
    except Exception as exc:
        return tool_error_payload(exc)
