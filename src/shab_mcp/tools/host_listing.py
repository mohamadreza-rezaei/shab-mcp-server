"""Host listing wizard tools for Shab MCP v0.6."""

from __future__ import annotations

from typing import Any

from shab_mcp.client import ShabAPIClient
from shab_mcp.errors import ShabValidationError, tool_error_payload
from shab_mcp.tools.auth import require_access_token

# Mainweb Routes[*] values used as ?step=
LISTING_STEPS = (
    "type",
    "structure",
    "floor",
    "address",
    "location",
    "distances",
    "spaces",
    "features",
    "shared",
    "pricing",
    "cancellation",
    "rules",
    "images",
    "documents",
    "description",
    "final",
)


def _extract_list(data: Any) -> list[dict[str, Any]]:
    if isinstance(data, list):
        return [x for x in data if isinstance(x, dict)]
    if not isinstance(data, dict):
        return []
    for key in ("records", "houses", "data", "items"):
        val = data.get(key)
        if isinstance(val, list):
            return [x for x in val if isinstance(x, dict)]
    return []


def _slim(obj: Any, *, depth: int = 0) -> Any:
    if depth > 5:
        return None
    if isinstance(obj, list):
        return [_slim(x, depth=depth + 1) for x in obj[:80]]
    if isinstance(obj, dict):
        return {k: _slim(v, depth=depth + 1) for k, v in obj.items() if k not in {"html"}}
    return obj


async def create_host_listing_impl(
    *,
    access_token: str,
    payload: dict[str, Any],
    confirm: bool = False,
) -> dict[str, Any]:
    if not confirm:
        raise ShabValidationError("create_host_listing requires confirm=true.")
    token = require_access_token(access_token)
    if not payload:
        raise ShabValidationError("payload is required (e.g. house type fields from mainweb).")
    async with ShabAPIClient() as api:
        data = await api.store_house(token, payload=payload)
    house_id = None
    if isinstance(data, dict):
        house_id = data.get("id") or data.get("house_id")
    return {
        "ok": True,
        "house_id": house_id,
        "result": _slim(data),
        "next_step": (
            "Call update_host_listing with step in "
            + ", ".join(LISTING_STEPS)
            + ". Binary photos: use Shab UI photo/upload then pass ids in images step."
        ),
        "steps": list(LISTING_STEPS),
    }


async def update_host_listing_impl(
    *,
    access_token: str,
    house_id: int,
    step: str,
    payload: dict[str, Any],
    confirm: bool = False,
) -> dict[str, Any]:
    if not confirm:
        raise ShabValidationError("update_host_listing requires confirm=true.")
    token = require_access_token(access_token)
    if house_id < 1:
        raise ShabValidationError("house_id must be positive.")
    step_key = (step or "").strip().lower()
    if step_key not in LISTING_STEPS:
        raise ShabValidationError(
            f"step must be one of: {', '.join(LISTING_STEPS)}"
        )
    if payload is None:
        raise ShabValidationError("payload is required.")
    async with ShabAPIClient() as api:
        data = await api.update_house(token, house_id, step=step_key, payload=payload)
    return {
        "ok": True,
        "house_id": house_id,
        "step": step_key,
        "result": _slim(data),
    }


async def list_my_houses_impl(*, access_token: str, page: int = 1) -> dict[str, Any]:
    token = require_access_token(access_token)
    async with ShabAPIClient() as api:
        data = await api.list_my_houses(token, page=page)
    houses = []
    for h in _extract_list(data):
        houses.append(
            {
                "id": h.get("id"),
                "title": h.get("title") or h.get("name"),
                "status": h.get("status") or h.get("state"),
                "city": (h.get("location") or {}).get("city")
                if isinstance(h.get("location"), dict)
                else h.get("city"),
                "code": h.get("code") or h.get("unique_code"),
            }
        )
    return {"page": page, "houses": houses or _slim(data)}


async def get_my_house_impl(*, access_token: str, house_id: int) -> dict[str, Any]:
    token = require_access_token(access_token)
    if house_id < 1:
        raise ShabValidationError("house_id must be positive.")
    async with ShabAPIClient() as api:
        data = await api.get_user_house(token, house_id)
    return {"house_id": house_id, "house": _slim(data)}


async def set_house_enabled_impl(
    *,
    access_token: str,
    house_id: int,
    enabled: bool,
    confirm: bool = False,
) -> dict[str, Any]:
    if not confirm:
        raise ShabValidationError("set_house_enabled requires confirm=true.")
    token = require_access_token(access_token)
    if house_id < 1:
        raise ShabValidationError("house_id must be positive.")
    async with ShabAPIClient() as api:
        if enabled:
            data = await api.enable_house(token, house_id)
        else:
            data = await api.delete_or_disable_house(token, house_id)
    return {"ok": True, "house_id": house_id, "enabled": enabled, "result": _slim(data)}


def _safe(fn):  # type: ignore[no-untyped-def]
    async def wrapper(**kwargs: Any) -> dict[str, Any]:
        try:
            return await fn(**kwargs)
        except Exception as exc:
            return tool_error_payload(exc)

    return wrapper


create_host_listing_safe = _safe(create_host_listing_impl)
update_host_listing_safe = _safe(update_host_listing_impl)
list_my_houses_safe = _safe(list_my_houses_impl)
get_my_house_safe = _safe(get_my_house_impl)
set_house_enabled_safe = _safe(set_house_enabled_impl)
