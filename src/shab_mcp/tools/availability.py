from __future__ import annotations

from typing import Any

from shab_mcp.client import ShabAPIClient
from shab_mcp.dates import to_jalali_api, validate_stay_range
from shab_mcp.errors import ShabValidationError, tool_error_payload
from shab_mcp.normalize import normalize_calendar, normalize_proforma


async def check_availability_impl(
    *,
    accommodation_id: int,
    check_in: str,
    check_out: str,
    guests: int = 2,
) -> dict[str, Any]:
    if accommodation_id < 1:
        raise ShabValidationError("accommodation_id must be a positive integer.")
    if guests < 1:
        raise ShabValidationError("guests must be >= 1.")

    start, end = validate_stay_range(check_in, check_out)
    jalali_in = to_jalali_api(start, field="check_in")
    jalali_out = to_jalali_api(end, field="check_out")

    async with ShabAPIClient() as api:
        calendar_data = await api.get_house_calendar(
            accommodation_id,
            from_date=jalali_in,
            to_date=jalali_out,
        )
        quote = await api.get_proforma(
            house_id=accommodation_id,
            checkin=jalali_in,
            checkout=jalali_out,
            guests_count=guests,
        )

    nights = normalize_calendar(calendar_data or {})
    stay_nights = [n for n in nights if n.get("jalali_date") and n["jalali_date"] < jalali_out]
    unavailable = [n["jalali_date"] for n in stay_nights if not n.get("is_bookable")]
    available = len(unavailable) == 0 and len(stay_nights) > 0

    return {
        "accommodation_id": accommodation_id,
        "check_in": check_in,
        "check_out": check_out,
        "check_in_jalali": jalali_in,
        "check_out_jalali": jalali_out,
        "guests": guests,
        "available": available,
        "unavailable_nights": unavailable,
        "nights": stay_nights,
        "quote": normalize_proforma(quote or {}),
        "currency": "Toman",
    }


async def check_availability_safe(**kwargs: Any) -> dict[str, Any]:
    try:
        return await check_availability_impl(**kwargs)
    except Exception as exc:
        return tool_error_payload(exc)
