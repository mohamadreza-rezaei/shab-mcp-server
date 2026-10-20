from __future__ import annotations

from typing import Any

from shab_mcp.client import ShabAPIClient
from shab_mcp.dates import to_unix_day, validate_stay_range
from shab_mcp.errors import ShabNotFoundError, ShabValidationError, tool_error_payload
from shab_mcp.normalize import normalize_house_detail, normalize_search_record


async def search_accommodations_impl(
    *,
    destination: str | None = None,
    check_in: str | None = None,
    check_out: str | None = None,
    guests: int = 2,
    page: int = 1,
    per_page: int = 10,
    min_price: int | None = None,
    max_price: int | None = None,
    accommodation_type: str | None = None,
    is_instant: bool | None = None,
) -> dict[str, Any]:
    if guests < 1:
        raise ShabValidationError("guests must be >= 1.")
    if page < 1:
        raise ShabValidationError("page must be >= 1.")
    per_page = max(1, min(per_page, 24))

    params: list[tuple[str, Any]] = [
        ("page", page),
        ("perpage", per_page),
        ("guests", guests),
    ]

    dest = (destination or "").strip()
    if dest:
        params.append(("city[]", dest))

    if check_in or check_out:
        if not (check_in and check_out):
            raise ShabValidationError("Provide both check_in and check_out, or neither.")
        validate_stay_range(check_in, check_out)
        params.append(("checkin_timestamp", to_unix_day(check_in, field="check_in")))
        params.append(("checkout_timestamp", to_unix_day(check_out, field="check_out")))

    # Shab search min/max price are in 1000-Toman units.
    if min_price is not None:
        params.append(("min_price", max(0, int(min_price) // 1000)))
    if max_price is not None:
        params.append(("max_price", max(0, int(max_price) // 1000)))
    if accommodation_type:
        params.append(("type[]", accommodation_type))
    if is_instant is not None:
        params.append(("is_instant", 1 if is_instant else 0))

    async with ShabAPIClient() as api:
        data = await api.search_houses(params)

    records = data.get("records") if isinstance(data, dict) else None
    results = [normalize_search_record(r) for r in records or [] if isinstance(r, dict)]
    pagination = (data or {}).get("pagination") if isinstance(data, dict) else {}
    return {
        "destination": dest or None,
        "check_in": check_in,
        "check_out": check_out,
        "guests": guests,
        "page": pagination.get("current_page", page),
        "total": pagination.get("total"),
        "currency": "Toman",
        "results": results,
    }


async def get_accommodation_impl(accommodation_id: int) -> dict[str, Any]:
    if accommodation_id < 1:
        raise ShabValidationError("accommodation_id must be a positive integer.")

    async with ShabAPIClient() as api:
        data = await api.get_house(accommodation_id)

    if not data:
        raise ShabNotFoundError(f"Accommodation {accommodation_id} was not found.")
    return normalize_house_detail(data)


async def search_accommodations_safe(**kwargs: Any) -> dict[str, Any]:
    try:
        return await search_accommodations_impl(**kwargs)
    except Exception as exc:
        return tool_error_payload(exc)


async def get_accommodation_safe(accommodation_id: int) -> dict[str, Any]:
    try:
        return await get_accommodation_impl(accommodation_id)
    except Exception as exc:
        return tool_error_payload(exc)
