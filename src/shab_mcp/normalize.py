from __future__ import annotations

from typing import Any


def money_amount(value: Any) -> int | None:
    """Extract a Toman integer from Shab money objects or bare numbers."""
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return int(value)
    if isinstance(value, dict):
        for key in ("amount", "price_after_discount", "raw_price"):
            if key in value and value[key] is not None:
                nested = value[key]
                if isinstance(nested, dict):
                    return money_amount(nested)
                try:
                    return int(nested)
                except (TypeError, ValueError):
                    continue
    return None


def clip_text(value: Any, *, limit: int = 800) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    if len(text) <= limit:
        return text
    return text[: limit - 1] + "…"


def feature_labels(features: Any, *, limit: int = 40) -> list[str]:
    labels: list[str] = []
    if not isinstance(features, dict):
        return labels
    filled = features.get("filled_categories") or {}
    if not isinstance(filled, dict):
        return labels
    for items in filled.values():
        if not isinstance(items, list):
            continue
        for item in items:
            if not isinstance(item, dict):
                continue
            if item.get("is_active") in (0, False):
                continue
            label = item.get("feature_label") or item.get("feature_name")
            if label:
                labels.append(str(label))
            if len(labels) >= limit:
                return labels
    return labels


def normalize_search_record(record: dict[str, Any]) -> dict[str, Any]:
    pricing = record.get("pricing") or {}
    location = record.get("location") or {}
    cover = record.get("cover_photo") or {}
    rates = record.get("rates") or {}
    return {
        "id": record.get("id"),
        "title": record.get("title"),
        "type": record.get("type"),
        "location": {
            "city": location.get("city"),
            "province": location.get("province"),
            "village": location.get("village"),
        },
        "rating": rates.get("rank") or record.get("rank"),
        "reviews_count": record.get("reviews"),
        "capacity": record.get("max_accommodates"),
        "rooms": record.get("rooms"),
        "price_per_night": money_amount(
            pricing.get("price_after_discount") or pricing.get("total") or pricing
        ),
        "currency": "Toman",
        "badges": record.get("badges") or [],
        "cover_photo_url": cover.get("thumbnail_absolute_url") or cover.get("absolute_url"),
    }


def normalize_house_detail(data: dict[str, Any]) -> dict[str, Any]:
    location = data.get("location") or {}
    rates = data.get("rates") or {}
    pricing = data.get("pricing") or {}
    rules = (data.get("rules") or {}).get("records") or {}
    spaces = data.get("spaces") or {}
    pictures = data.get("pictures") or []
    photo_urls: list[str] = []
    if isinstance(pictures, list):
        for pic in pictures[:8]:
            if isinstance(pic, dict):
                url = pic.get("thumbnail_absolute_url") or pic.get("absolute_url")
                if url:
                    photo_urls.append(url)

    return {
        "id": data.get("id"),
        "title": data.get("title"),
        "type": data.get("type"),
        "type_label": data.get("type_fa"),
        "description": clip_text(data.get("about"), limit=1200),
        "location": {
            "city": location.get("city"),
            "province": location.get("province"),
            "village": location.get("village"),
            "latitude": location.get("latitude"),
            "longitude": location.get("longitude"),
        },
        "rating": rates.get("rank"),
        "reviews_count": data.get("reviews_count"),
        "capacity": {
            "base": rules.get("accommodates"),
            "max": rules.get("max_accommodates"),
        },
        "rooms": spaces.get("normal_rooms"),
        "beds": spaces.get("bed_space"),
        "is_instant": bool(data.get("is_instant")),
        "price_from": money_amount(pricing.get("price_to_show")),
        "currency": "Toman",
        "checkin_time": rules.get("checkin"),
        "checkout_time": rules.get("checkout"),
        "amenities": feature_labels(data.get("features")),
        "rules_summary": clip_text(rules.get("rules_description"), limit=400),
        "photo_urls": photo_urls,
        "host": {
            "name": (data.get("host") or {}).get("name"),
            "rating": (data.get("host") or {}).get("rate"),
        },
    }


def normalize_calendar(data: dict[str, Any]) -> list[dict[str, Any]]:
    records = data.get("records") if isinstance(data, dict) else data
    nights: list[dict[str, Any]] = []
    if not isinstance(records, dict):
        return nights
    for month_key, days in records.items():
        if not isinstance(days, list):
            continue
        for day in days:
            if not isinstance(day, dict):
                continue
            day_num = day.get("day")
            jalali = f"{month_key}-{int(day_num):02d}" if day_num is not None else None
            nights.append(
                {
                    "jalali_date": jalali,
                    "price": money_amount(day.get("price")),
                    "currency": "Toman",
                    "is_bookable": bool(day.get("is_bookable")),
                    "is_instant": bool(day.get("is_instant")),
                    "is_peak": bool(day.get("is_peak")),
                    "min_nights": day.get("min_book_day"),
                }
            )
    return nights


def normalize_proforma(data: dict[str, Any], *, prefer_discount: bool = False) -> dict[str, Any]:
    finalized = data.get("finalized_price") or {}
    details = data.get("details_of_price") or {}
    if prefer_discount:
        total = money_amount(
            finalized.get("with_discount_code") or finalized.get("without_discount_code")
        )
    else:
        total = money_amount(
            finalized.get("without_discount_code") or finalized.get("with_discount_code")
        )
    return {
        "is_instant": bool(data.get("is_instant")),
        "total_price": total,
        "prepayment": money_amount(finalized.get("prepayment")),
        "currency": "Toman",
        "base_price": money_amount(details.get("base")),
        "extra_guests_fee": money_amount((details.get("extra_person") or {}).get("amount")),
        "extra_guests_count": (details.get("extra_person") or {}).get("count"),
    }


def normalize_photos(data: Any, *, limit: int = 24) -> list[dict[str, Any]]:
    photos: list[dict[str, Any]] = []
    records = data
    if isinstance(data, dict):
        records = data.get("records") or data.get("photos") or data.get("pictures") or data
    if not isinstance(records, list):
        return photos
    for pic in records[:limit]:
        if not isinstance(pic, dict):
            continue
        url = (
            pic.get("absolute_url")
            or pic.get("thumbnail_absolute_url")
            or pic.get("url")
            or pic.get("path")
        )
        if not url:
            continue
        photos.append(
            {
                "url": url,
                "thumbnail_url": pic.get("thumbnail_absolute_url") or pic.get("thumbnail_url"),
                "caption": clip_text(pic.get("caption") or pic.get("title"), limit=120),
            }
        )
    return photos


def normalize_reviews(data: Any, *, limit: int = 10) -> dict[str, Any]:
    records = data
    pagination: dict[str, Any] = {}
    if isinstance(data, dict):
        records = data.get("records") or data.get("reviews") or data.get("data") or []
        pagination = data.get("pagination") or {}
    items: list[dict[str, Any]] = []
    if isinstance(records, list):
        for rev in records[:limit]:
            if not isinstance(rev, dict):
                continue
            guest = rev.get("guest") or rev.get("user") or {}
            items.append(
                {
                    "rating": rev.get("rate") or rev.get("rating") or rev.get("rank"),
                    "comment": clip_text(
                        rev.get("comment") or rev.get("body") or rev.get("text"), limit=500
                    ),
                    "created_at": rev.get("created_at") or rev.get("date"),
                    "guest_name": guest.get("name") if isinstance(guest, dict) else None,
                }
            )
    return {
        "reviews": items,
        "page": pagination.get("current_page"),
        "total": pagination.get("total"),
    }


def normalize_search_filters(data: Any) -> dict[str, Any]:
    """Slim amenity/feature filter catalog for agents."""
    if not isinstance(data, dict):
        return {"amenities": [], "raw_keys": []}
    amenities: list[dict[str, Any]] = []
    candidates: list[Any] = []
    for key in ("features", "amenities", "feature_categories", "filters"):
        val = data.get(key)
        if val is not None:
            candidates.append(val)
    if isinstance(data.get("filters"), dict):
        for key in ("features", "amenities"):
            if data["filters"].get(key) is not None:
                candidates.append(data["filters"][key])

    def add_feature(item: dict[str, Any]) -> None:
        code = item.get("name") or item.get("code") or item.get("slug") or item.get("id")
        label = item.get("feature_label") or item.get("label") or item.get("title") or item.get("fa")
        if code is None and label is None:
            return
        amenities.append({"code": str(code) if code is not None else None, "label": label})

    for block in candidates:
        if isinstance(block, list):
            for item in block:
                if isinstance(item, dict):
                    add_feature(item)
        elif isinstance(block, dict):
            for items in block.values():
                if isinstance(items, list):
                    for item in items:
                        if isinstance(item, dict):
                            add_feature(item)
                elif isinstance(items, dict):
                    add_feature(items)

    seen: set[str] = set()
    unique: list[dict[str, Any]] = []
    for a in amenities:
        key = str(a.get("code") or a.get("label") or "")
        if not key or key in seen:
            continue
        seen.add(key)
        unique.append(a)
        if len(unique) >= 80:
            break
    return {"amenities": unique, "hint": "Pass amenity codes as amenities[] on search_accommodations."}


def normalize_user_summary(data: Any) -> dict[str, Any]:
    if not isinstance(data, dict):
        return {}
    user = data.get("user") if isinstance(data.get("user"), dict) else data
    return {
        "id": user.get("id") or user.get("uid") or user.get("public_uid"),
        "name": user.get("name") or user.get("full_name"),
        "mobile": user.get("mobile"),
    }


def normalize_booking_summary(data: Any) -> dict[str, Any]:
    if not isinstance(data, dict):
        return {}
    house = data.get("house") or {}
    return {
        "reserve_id": data.get("reserve_id") or data.get("id") or data.get("tiny_id"),
        "invoice_id": data.get("invoice_id") or (data.get("invoice") or {}).get("id"),
        "status": data.get("last_state") or data.get("status") or data.get("state"),
        "is_instant": bool(data.get("is_instant")),
        "check_in": data.get("checkin") or data.get("check_in"),
        "check_out": data.get("checkout") or data.get("check_out"),
        "guests": data.get("guests_count") or data.get("guests"),
        "house": {
            "id": house.get("id") if isinstance(house, dict) else data.get("house_id"),
            "title": house.get("title") if isinstance(house, dict) else None,
        },
        "total_price": money_amount(
            data.get("total_price")
            or data.get("price")
            or (data.get("invoice") or {}).get("prepayment")
        ),
        "currency": "Toman",
    }


def normalize_host_profile(data: Any) -> dict[str, Any]:
    if not isinstance(data, dict):
        return {}
    return {
        "id": data.get("id") or data.get("uid") or data.get("public_uid"),
        "name": data.get("name") or data.get("full_name"),
        "is_verified_host": bool(data.get("is_verified_host") or data.get("is_host")),
        "about": clip_text(data.get("about_me") or data.get("about"), limit=600),
        "response_rate": data.get("response_rate") or data.get("host_response_rate"),
        "rating": data.get("rate") or data.get("rating"),
    }


def normalize_host_contact(data: Any) -> dict[str, Any]:
    if not isinstance(data, dict):
        return {}
    host = data.get("host") if isinstance(data.get("host"), dict) else data
    return {
        "name": host.get("name"),
        "mobile": host.get("mobile") or host.get("phone"),
        "id": host.get("id") or host.get("uid") or host.get("public_uid"),
    }


def normalize_invoice_calculate(data: Any) -> dict[str, Any]:
    if not isinstance(data, dict):
        return {}
    invoice = data.get("invoice") if isinstance(data.get("invoice"), dict) else data
    return {
        "invoice_id": invoice.get("id") or invoice.get("tiny_id") or data.get("invoice_id"),
        "prepayment": money_amount(invoice.get("prepayment") or data.get("prepayment")),
        "total": money_amount(invoice.get("total") or data.get("total")),
        "discount_applied": bool(
            data.get("discount_applied")
            or invoice.get("discount_code")
            or data.get("discount_code")
        ),
        "currency": "Toman",
    }


def normalize_gateways(data: Any) -> list[dict[str, Any]]:
    records = data
    if isinstance(data, dict):
        records = data.get("records") or data.get("gateways") or data.get("data") or []
    out: list[dict[str, Any]] = []
    if not isinstance(records, list):
        return out
    for g in records:
        if not isinstance(g, dict):
            continue
        out.append(
            {
                "id": g.get("id"),
                "name": g.get("name") or g.get("title") or g.get("label"),
            }
        )
    return out


def normalize_destinations(payload: Any) -> list[dict[str, Any]]:
    destinations: list[dict[str, Any]] = []
    seen: set[tuple[Any, Any]] = set()

    def add(item: dict[str, Any], *, source: str) -> None:
        name = item.get("name")
        dtype = item.get("type")
        key = (name, dtype)
        if not name or key in seen:
            return
        seen.add(key)
        province = item.get("province_name")
        if province is None and isinstance(item.get("province"), dict):
            province = item["province"].get("name")
        destinations.append(
            {
                "id": item.get("id"),
                "name": name,
                "type": dtype,
                "type_label": item.get("type_label"),
                "province": province,
                "houses_count": item.get("houses_count"),
                "source": source,
                "search": {
                    "city": [name] if dtype == "city" else None,
                    "province": [name] if dtype == "province" else ([province] if province else None),
                },
            }
        )

    if isinstance(payload, list):
        for item in payload:
            if isinstance(item, dict):
                add(item, source="region_suggestions")
        return destinations

    if isinstance(payload, dict):
        for key in ("regions", "near_regions"):
            for item in payload.get(key) or []:
                if isinstance(item, dict):
                    add(item, source="house_suggestions")
        for item in payload.get("houses") or []:
            if isinstance(item, dict):
                destinations.append(
                    {
                        "id": item.get("id"),
                        "name": item.get("title") or item.get("name"),
                        "type": "house",
                        "type_label": "اقامتگاه",
                        "province": None,
                        "houses_count": None,
                        "source": "house_suggestions",
                        "search": {"accommodation_id": item.get("id")},
                    }
                )
    return destinations
