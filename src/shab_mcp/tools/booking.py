"""Booking tools for Shab MCP v0.2.

Importers/callers: server.py registers create_booking, calculate_invoice, get_payment_link.
Affected API: POST reserve, POST invoice/calculate, GET payment/gateways, GET invoice/{id}/show.
Schemas: Jalali checkin/checkout on create; invoice_id + discount_code; payment_url handoff.
User instruction: "Implement the plan as specified" (book + discount + pay link, no IPG).
"""

from __future__ import annotations

from typing import Any

from shab_mcp.client import ShabAPIClient
from shab_mcp.config import get_settings
from shab_mcp.dates import to_jalali_api, validate_stay_range
from shab_mcp.errors import ShabValidationError, tool_error_payload
from shab_mcp.normalize import normalize_gateways, normalize_invoice_calculate
from shab_mcp.tools.auth import require_access_token


async def create_booking_impl(
    *,
    access_token: str,
    accommodation_id: int,
    check_in: str,
    check_out: str,
    guests: int = 2,
    confirm: bool = False,
) -> dict[str, Any]:
    if not confirm:
        raise ShabValidationError(
            "create_booking requires confirm=true after the user explicitly agrees to book."
        )
    if accommodation_id < 1:
        raise ShabValidationError("accommodation_id must be a positive integer.")
    if guests < 1:
        raise ShabValidationError("guests must be >= 1.")

    token = require_access_token(access_token)
    start, end = validate_stay_range(check_in, check_out)
    jalali_in = to_jalali_api(start, field="check_in")
    jalali_out = to_jalali_api(end, field="check_out")

    async with ShabAPIClient() as api:
        data = await api.create_reserve(
            token,
            house_id=accommodation_id,
            checkin=jalali_in,
            checkout=jalali_out,
            guests_count=guests,
        )

    payload = data if isinstance(data, dict) else {}
    return {
        "ok": True,
        "reserve_id": payload.get("reserve_id"),
        "invoice_id": payload.get("invoice_id"),
        "is_instant": bool(payload.get("is_instant")),
        "last_state": payload.get("last_state"),
        "check_in": check_in,
        "check_out": check_out,
        "check_in_jalali": jalali_in,
        "check_out_jalali": jalali_out,
        "guests": guests,
        "accommodation_id": accommodation_id,
        "next_step": (
            "Call calculate_invoice (optional discount), then get_payment_link. "
            "If last_state is pending host approval, payment may wait until the host accepts."
        ),
    }


async def calculate_invoice_impl(
    *,
    access_token: str,
    invoice_id: str,
    discount_code: str | None = None,
    use_credit: bool = False,
    prepay_total_fee: bool = False,
) -> dict[str, Any]:
    token = require_access_token(access_token)
    inv = (invoice_id or "").strip()
    if not inv:
        raise ShabValidationError("invoice_id is required (from create_booking).")

    async with ShabAPIClient() as api:
        data = await api.calculate_invoice(
            token,
            invoice_id=inv,
            discount_code=(discount_code or "").strip() or None,
            use_credit=use_credit,
            prepay_total_fee=prepay_total_fee,
        )

    result = normalize_invoice_calculate(data)
    result["discount_code"] = (discount_code or "").strip() or None
    result["use_credit"] = use_credit
    result["next_step"] = "Call get_payment_link with reserve_id and invoice_id."
    return result


async def get_payment_link_impl(
    *,
    access_token: str,
    reserve_id: str,
    invoice_id: str,
) -> dict[str, Any]:
    token = require_access_token(access_token)
    rid = (reserve_id or "").strip()
    iid = (invoice_id or "").strip()
    if not rid or not iid:
        raise ShabValidationError("reserve_id and invoice_id are required.")

    settings = get_settings()
    web = settings.shab_web_base_url.rstrip("/")

    async with ShabAPIClient() as api:
        gateways_raw = await api.get_payment_gateways(token, rid)
        invoice_raw = None
        try:
            invoice_raw = await api.get_invoice(token, iid)
        except Exception:
            invoice_raw = None

    amount = None
    if isinstance(invoice_raw, dict):
        calc = normalize_invoice_calculate(invoice_raw)
        amount = calc.get("prepayment") or calc.get("total")

    # Mainweb route after create reserve: /order-tracking/{invoice_id}/show
    # (shab-mainweb useHouse.redirectToInvoice / trips reserve cards).
    payment_url = f"{web}/order-tracking/{iid}/show"

    return {
        "payment_url": payment_url,
        "reserve_id": rid,
        "invoice_id": iid,
        "amount": amount,
        "currency": "Toman",
        "gateways": normalize_gateways(gateways_raw),
        "instruction": (
            "Open payment_url (order-tracking page) in a browser, apply discount if needed, "
            "and complete card payment on Shab/IPG. MCP cannot enter card details. "
            "After paying, poll get_booking or list_trips."
        ),
    }


async def create_booking_safe(**kwargs: Any) -> dict[str, Any]:
    try:
        return await create_booking_impl(**kwargs)
    except Exception as exc:
        return tool_error_payload(exc)


async def calculate_invoice_safe(**kwargs: Any) -> dict[str, Any]:
    try:
        return await calculate_invoice_impl(**kwargs)
    except Exception as exc:
        return tool_error_payload(exc)


async def get_payment_link_safe(**kwargs: Any) -> dict[str, Any]:
    try:
        return await get_payment_link_impl(**kwargs)
    except Exception as exc:
        return tool_error_payload(exc)
