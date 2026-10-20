from __future__ import annotations

from typing import Any

from shab_mcp.client import ShabAPIClient
from shab_mcp.errors import ShabValidationError, tool_error_payload
from shab_mcp.normalize import normalize_destinations


async def search_destinations_impl(query: str) -> dict[str, Any]:
    phrase = (query or "").strip()
    if len(phrase) < 2:
        raise ShabValidationError("query needs at least 2 characters, e.g. 'رامسر'.")

    async with ShabAPIClient() as api:
        try:
            house_payload = await api.house_suggestions(phrase)
        except Exception:
            house_payload = None
        try:
            region_payload = await api.region_suggestions(phrase)
        except Exception:
            region_payload = None

    destinations = normalize_destinations(house_payload)
    if region_payload:
        for item in normalize_destinations(region_payload):
            if all(d.get("name") != item.get("name") or d.get("type") != item.get("type") for d in destinations):
                destinations.append(item)

    return {"query": phrase, "destinations": destinations[:30]}


async def search_destinations_safe(query: str) -> dict[str, Any]:
    try:
        return await search_destinations_impl(query)
    except Exception as exc:
        return tool_error_payload(exc)
