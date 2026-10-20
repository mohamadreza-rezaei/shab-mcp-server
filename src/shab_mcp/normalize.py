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


def normalize_proforma(data: dict[str, Any]) -> dict[str, Any]:
    finalized = data.get("finalized_price") or {}
    details = data.get("details_of_price") or {}
    return {
        "is_instant": bool(data.get("is_instant")),
        "total_price": money_amount(
            finalized.get("without_discount_code") or finalized.get("with_discount_code")
        ),
        "prepayment": money_amount(finalized.get("prepayment")),
        "currency": "Toman",
        "base_price": money_amount(details.get("base")),
        "extra_guests_fee": money_amount((details.get("extra_person") or {}).get("amount")),
        "extra_guests_count": (details.get("extra_person") or {}).get("count"),
    }


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
