from __future__ import annotations

from typing import Any

from shab_mcp.client import ShabAPIClient
from shab_mcp.dates import to_unix_day, validate_stay_range
from shab_mcp.errors import ShabNotFoundError, ShabValidationError, tool_error_payload
from shab_mcp.normalize import (
    normalize_house_detail,
    normalize_photos,
    normalize_reviews,
    normalize_search_filters,
    normalize_search_record,
)


def _build_search_params(
    *,
    destination: str | None = None,
    province: str | None = None,
    check_in: str | None = None,
    check_out: str | None = None,
    guests: int = 2,
    page: int = 1,
    per_page: int = 10,
    min_price: int | None = None,
    max_price: int | None = None,
    accommodation_type: str | None = None,
    is_instant: bool | None = None,
    bedroom_count: int | None = None,
    bed_count: int | None = None,
    amenities: list[str] | None = None,
    sort_by: str | None = None,
    min_latitude: float | None = None,
    max_latitude: float | None = None,
    min_longitude: float | None = None,
    max_longitude: float | None = None,
    user_latitude: float | None = None,
    user_longitude: float | None = None,
    from_map_nearby: bool | None = None,
    place_id: str | None = None,
    include_pagination: bool = True,
) -> tuple[list[tuple[str, Any]], str, str]:
    if guests < 1:
        raise ShabValidationError("guests must be >= 1.")
    if page < 1:
        raise ShabValidationError("page must be >= 1.")
    per_page = max(1, min(per_page, 24))

    params: list[tuple[str, Any]] = [("guests", guests)]
    if include_pagination:
        params.extend([("page", page), ("perpage", per_page)])

    dest = (destination or "").strip()
    if dest:
        params.append(("city[]", dest))

    prov = (province or "").strip()
    if prov:
        params.append(("province[]", prov))

    if check_in or check_out:
        if not (check_in and check_out):
            raise ShabValidationError("Provide both check_in and check_out, or neither.")
        validate_stay_range(check_in, check_out)
        params.append(("checkin_timestamp", to_unix_day(check_in, field="check_in")))
        params.append(("checkout_timestamp", to_unix_day(check_out, field="check_out")))

    if min_price is not None:
        params.append(("min_price", max(0, int(min_price) // 1000)))
    if max_price is not None:
        params.append(("max_price", max(0, int(max_price) // 1000)))
    if accommodation_type:
        params.append(("type[]", accommodation_type))
    if is_instant is not None:
        params.append(("is_instant", 1 if is_instant else 0))
    if bedroom_count is not None:
        if bedroom_count < 0:
            raise ShabValidationError("bedroom_count must be >= 0.")
        params.append(("bedroom_count", bedroom_count))
    if bed_count is not None:
        if bed_count < 0:
            raise ShabValidationError("bed_count must be >= 0.")
        params.append(("bed_count", bed_count))
    if amenities:
        for code in amenities:
            c = (code or "").strip()
            if c:
                params.append(("features[]", c))

    sort = (sort_by or "").strip().lower()
    if sort == "price_desc":
        params.append(("is_descending[price]", "1"))
    elif sort == "price_asc":
        params.append(("is_descending[price]", "0"))
    elif sort == "rating":
        params.append(("is_descending[rate]", "1"))
    elif sort:
        raise ShabValidationError("sort_by must be one of: price_asc, price_desc, rating.")

    bbox = (min_latitude, max_latitude, min_longitude, max_longitude)
    if any(v is not None for v in bbox):
        if any(v is None for v in bbox):
            raise ShabValidationError(
                "Provide all four bbox coords: min_latitude, max_latitude, min_longitude, max_longitude."
            )
        params.append(("co_ordinates[min_latitude]", min_latitude))
        params.append(("co_ordinates[max_latitude]", max_latitude))
        params.append(("co_ordinates[min_longitude]", min_longitude))
        params.append(("co_ordinates[max_longitude]", max_longitude))

    if user_latitude is not None and user_longitude is not None:
        params.append(("user_co_ordinates[latitude]", user_latitude))
        params.append(("user_co_ordinates[longitude]", user_longitude))
    elif user_latitude is not None or user_longitude is not None:
        raise ShabValidationError("Provide both user_latitude and user_longitude, or neither.")

    if from_map_nearby:
        params.append(("from_map_nearby", 1))

    pid = (place_id or "").strip()
    if pid:
        params.append(("place_id", pid))

    return params, dest, prov


async def search_accommodations_impl(
    *,
    destination: str | None = None,
    province: str | None = None,
    check_in: str | None = None,
    check_out: str | None = None,
    guests: int = 2,
    page: int = 1,
    per_page: int = 10,
    min_price: int | None = None,
    max_price: int | None = None,
    accommodation_type: str | None = None,
    is_instant: bool | None = None,
    bedroom_count: int | None = None,
    bed_count: int | None = None,
    amenities: list[str] | None = None,
    sort_by: str | None = None,
    min_latitude: float | None = None,
    max_latitude: float | None = None,
    min_longitude: float | None = None,
    max_longitude: float | None = None,
    user_latitude: float | None = None,
    user_longitude: float | None = None,
    from_map_nearby: bool | None = None,
    place_id: str | None = None,
) -> dict[str, Any]:
    params, dest, prov = _build_search_params(
        destination=destination,
        province=province,
        check_in=check_in,
        check_out=check_out,
        guests=guests,
        page=page,
        per_page=per_page,
        min_price=min_price,
        max_price=max_price,
        accommodation_type=accommodation_type,
        is_instant=is_instant,
        bedroom_count=bedroom_count,
        bed_count=bed_count,
        amenities=amenities,
        sort_by=sort_by,
        min_latitude=min_latitude,
        max_latitude=max_latitude,
        min_longitude=min_longitude,
        max_longitude=max_longitude,
        user_latitude=user_latitude,
        user_longitude=user_longitude,
        from_map_nearby=from_map_nearby,
        place_id=place_id,
    )

    async with ShabAPIClient() as api:
        data = await api.search_houses(params)

    records = data.get("records") if isinstance(data, dict) else None
    results = [normalize_search_record(r) for r in records or [] if isinstance(r, dict)]
    pagination = (data or {}).get("pagination") if isinstance(data, dict) else {}
    return {
        "destination": dest or None,
        "province": prov or None,
        "check_in": check_in,
        "check_out": check_out,
        "guests": guests,
        "bedroom_count": bedroom_count,
        "amenities": amenities or None,
        "bbox": {
            "min_latitude": min_latitude,
            "max_latitude": max_latitude,
            "min_longitude": min_longitude,
            "max_longitude": max_longitude,
        }
        if min_latitude is not None
        else None,
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


async def list_search_filters_impl() -> dict[str, Any]:
    async with ShabAPIClient() as api:
        data = await api.get_search_filters()
    return normalize_search_filters(data or {})


async def get_accommodation_photos_impl(accommodation_id: int) -> dict[str, Any]:
    if accommodation_id < 1:
        raise ShabValidationError("accommodation_id must be a positive integer.")

    async with ShabAPIClient() as api:
        data = await api.get_house_photos(accommodation_id)

    photos = normalize_photos(data)
    return {
        "accommodation_id": accommodation_id,
        "count": len(photos),
        "photos": photos,
    }


async def get_accommodation_reviews_impl(
    accommodation_id: int,
    *,
    page: int = 1,
) -> dict[str, Any]:
    if accommodation_id < 1:
        raise ShabValidationError("accommodation_id must be a positive integer.")
    if page < 1:
        raise ShabValidationError("page must be >= 1.")

    async with ShabAPIClient() as api:
        data = await api.get_house_reviews(accommodation_id, page=page)

    normalized = normalize_reviews(data)
    return {
        "accommodation_id": accommodation_id,
        **normalized,
    }


async def list_neighbourhoods_impl(*, city: str | None = None) -> dict[str, Any]:
    async with ShabAPIClient() as api:
        data = await api.get_neighbourhoods(city=(city or "").strip() or None)

    records = data
    if isinstance(data, dict):
        records = data.get("records") or data.get("neighbourhoods") or data.get("data") or []
    items: list[dict[str, Any]] = []
    if isinstance(records, list):
        for n in records[:50]:
            if not isinstance(n, dict):
                continue
            items.append(
                {
                    "id": n.get("id"),
                    "name": n.get("name") or n.get("title"),
                    "city": n.get("city"),
                }
            )
    return {"city": (city or "").strip() or None, "neighbourhoods": items}


async def get_similar_accommodations_impl(accommodation_id: int) -> dict[str, Any]:
    if accommodation_id < 1:
        raise ShabValidationError("accommodation_id must be a positive integer.")

    async with ShabAPIClient() as api:
        data = await api.get_similar_houses(accommodation_id)

    records = data
    if isinstance(data, dict):
        records = data.get("records") or data.get("houses") or data.get("data") or []
    results = [normalize_search_record(r) for r in records or [] if isinstance(r, dict)]
    return {"accommodation_id": accommodation_id, "results": results[:12], "currency": "Toman"}


async def count_accommodations_impl(**kwargs: Any) -> dict[str, Any]:
    params, dest, prov = _build_search_params(include_pagination=False, **kwargs)
    async with ShabAPIClient() as api:
        data = await api.count_houses(params)

    total = data
    if isinstance(data, dict):
        total = data.get("count") or data.get("total") or data.get("houses_count") or data
    return {
        "destination": dest or None,
        "province": prov or None,
        "count": total if isinstance(total, int) else None,
        "raw": data if not isinstance(total, int) else None,
    }


async def get_landing_tehran_impl() -> dict[str, Any]:
    async with ShabAPIClient() as api:
        data = await api.get_landing_tehran()
    # Slim: pass through common keys only
    if not isinstance(data, dict):
        return {"landing": data}
    out: dict[str, Any] = {"title": data.get("title") or data.get("name")}
    for key in ("filters", "categories", "banners", "records"):
        if key in data:
            out[key] = data[key]
    if not out.get("filters") and not out.get("categories"):
        out["data_keys"] = list(data.keys())[:20]
    return out


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


async def list_search_filters_safe() -> dict[str, Any]:
    try:
        return await list_search_filters_impl()
    except Exception as exc:
        return tool_error_payload(exc)


async def get_accommodation_photos_safe(accommodation_id: int) -> dict[str, Any]:
    try:
        return await get_accommodation_photos_impl(accommodation_id)
    except Exception as exc:
        return tool_error_payload(exc)


async def get_accommodation_reviews_safe(
    accommodation_id: int,
    page: int = 1,
) -> dict[str, Any]:
    try:
        return await get_accommodation_reviews_impl(accommodation_id, page=page)
    except Exception as exc:
        return tool_error_payload(exc)


async def list_neighbourhoods_safe(**kwargs: Any) -> dict[str, Any]:
    try:
        return await list_neighbourhoods_impl(**kwargs)
    except Exception as exc:
        return tool_error_payload(exc)


async def get_similar_accommodations_safe(accommodation_id: int) -> dict[str, Any]:
    try:
        return await get_similar_accommodations_impl(accommodation_id)
    except Exception as exc:
        return tool_error_payload(exc)


async def count_accommodations_safe(**kwargs: Any) -> dict[str, Any]:
    try:
        return await count_accommodations_impl(**kwargs)
    except Exception as exc:
        return tool_error_payload(exc)


async def get_landing_tehran_safe() -> dict[str, Any]:
    try:
        return await get_landing_tehran_impl()
    except Exception as exc:
        return tool_error_payload(exc)
