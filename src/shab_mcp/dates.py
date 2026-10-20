"""Gregorian ↔ Jalali helpers for Shab sandbox APIs.

Shab Jalali query params use zero-padded ``YYYY-MM-DD`` (dash separator).
Search uses Unix timestamps aligned to UTC midnight of each calendar day.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

import jdatetime

from shab_mcp.errors import ShabValidationError

TEHRAN = timezone(timedelta(hours=3, minutes=30))


def parse_gregorian(value: str | date, *, field: str = "date") -> date:
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    try:
        return date.fromisoformat(str(value))
    except ValueError as exc:
        raise ShabValidationError(
            f"{field} must be Gregorian YYYY-MM-DD, e.g. '2026-10-25'."
        ) from exc


def to_jalali_api(value: str | date, *, field: str = "date") -> str:
    """Format a Gregorian date as Shab Jalali ``YYYY-MM-DD``."""
    g = parse_gregorian(value, field=field)
    j = jdatetime.date.fromgregorian(date=g)
    return f"{j.year:04d}-{j.month:02d}-{j.day:02d}"


def to_unix_day(value: str | date, *, field: str = "date") -> int:
    """UTC midnight Unix timestamp for the Gregorian calendar day (Shab search)."""
    g = parse_gregorian(value, field=field)
    return int(datetime(g.year, g.month, g.day, tzinfo=timezone.utc).timestamp())


def validate_stay_range(
    check_in: str | date,
    check_out: str | date,
    *,
    max_days_ahead: int = 90,
) -> tuple[date, date]:
    start = parse_gregorian(check_in, field="check_in")
    end = parse_gregorian(check_out, field="check_out")
    today = datetime.now(TEHRAN).date()
    if end <= start:
        raise ShabValidationError("check_out must be after check_in.")
    if start < today:
        raise ShabValidationError("check_in cannot be in the past.")
    if start > today + timedelta(days=max_days_ahead):
        raise ShabValidationError(f"check_in must be within {max_days_ahead} days from today.")
    if end > today + timedelta(days=max_days_ahead):
        raise ShabValidationError(f"check_out must be within {max_days_ahead} days from today.")
    return start, end
