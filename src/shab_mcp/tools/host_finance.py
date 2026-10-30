"""Host dashboard, finance, and host-profile tools for Shab MCP v0.8."""

from __future__ import annotations

from typing import Any

from shab_mcp.client import ShabAPIClient
from shab_mcp.errors import ShabValidationError, tool_error_payload
from shab_mcp.tools.auth import require_access_token


def _extract_list(data: Any) -> list[dict[str, Any]]:
    if isinstance(data, list):
        return [x for x in data if isinstance(x, dict)]
    if not isinstance(data, dict):
        return []
    for key in ("records", "transactions", "payments", "checkouts", "data", "items"):
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


async def get_host_dashboard_impl(*, access_token: str) -> dict[str, Any]:
    token = require_access_token(access_token)
    async with ShabAPIClient() as api:
        glance = await api.get_host_dashboard_glance(token)
        notices = await api.get_host_dashboard_notices(token)
        performance = await api.get_host_dashboard_performance(token)
    return {
        "at_a_glance": _slim(glance),
        "notices": _slim(notices),
        "performance": _slim(performance),
        "currency": "Toman",
    }


async def list_unanswered_reviews_impl(*, access_token: str) -> dict[str, Any]:
    token = require_access_token(access_token)
    async with ShabAPIClient() as api:
        data = await api.get_unanswered_reviews(token)
    return {"reviews": _slim(_extract_list(data) or data)}


async def get_host_profile_settings_impl(*, access_token: str) -> dict[str, Any]:
    token = require_access_token(access_token)
    async with ShabAPIClient() as api:
        data = await api.get_host_profile_settings(token)
    return {"host_profile": _slim(data)}


async def update_host_profile_settings_impl(
    *, access_token: str, payload: dict[str, Any], confirm: bool = False
) -> dict[str, Any]:
    if not confirm:
        raise ShabValidationError("update_host_profile_settings requires confirm=true.")
    token = require_access_token(access_token)
    if not payload:
        raise ShabValidationError("payload is required.")
    async with ShabAPIClient() as api:
        data = await api.update_host_profile_settings(token, payload=payload)
    return {"ok": True, "host_profile": _slim(data)}


async def list_host_checkouts_impl(*, access_token: str, page: int = 1) -> dict[str, Any]:
    token = require_access_token(access_token)
    async with ShabAPIClient() as api:
        data = await api.list_checkouts(token, page=page)
    return {"page": page, "checkouts": _slim(_extract_list(data) or data), "currency": "Toman"}


async def list_host_transactions_impl(*, access_token: str, page: int = 1) -> dict[str, Any]:
    token = require_access_token(access_token)
    async with ShabAPIClient() as api:
        data = await api.list_transactions(token, page=page)
    return {
        "page": page,
        "transactions": _slim(_extract_list(data) or data),
        "currency": "Toman",
    }


async def get_host_transaction_impl(
    *, access_token: str, financial_id: str
) -> dict[str, Any]:
    token = require_access_token(access_token)
    fid = (financial_id or "").strip()
    if not fid:
        raise ShabValidationError("financial_id is required.")
    async with ShabAPIClient() as api:
        data = await api.get_transaction(token, fid)
    return {"financial_id": fid, "transaction": _slim(data), "currency": "Toman"}


async def list_host_payments_impl(*, access_token: str, page: int = 1) -> dict[str, Any]:
    token = require_access_token(access_token)
    async with ShabAPIClient() as api:
        data = await api.list_payments(token, page=page)
    return {"page": page, "payments": _slim(_extract_list(data) or data), "currency": "Toman"}


async def get_settlement_type_impl(*, access_token: str) -> dict[str, Any]:
    token = require_access_token(access_token)
    async with ShabAPIClient() as api:
        data = await api.get_settlement_type(token)
    return {"settlement": _slim(data)}


async def set_settlement_type_impl(
    *, access_token: str, payload: dict[str, Any], confirm: bool = False
) -> dict[str, Any]:
    if not confirm:
        raise ShabValidationError("set_settlement_type requires confirm=true.")
    token = require_access_token(access_token)
    if not payload:
        raise ShabValidationError("payload is required.")
    async with ShabAPIClient() as api:
        data = await api.set_settlement_type(token, payload=payload)
    return {"ok": True, "settlement": _slim(data)}


async def list_withdraw_requests_impl(*, access_token: str, page: int = 1) -> dict[str, Any]:
    token = require_access_token(access_token)
    async with ShabAPIClient() as api:
        data = await api.list_withdraw_requests(token, page=page)
    return {"page": page, "withdraw_requests": _slim(_extract_list(data) or data)}


async def list_credit_transactions_impl(
    *, access_token: str, page: int = 1
) -> dict[str, Any]:
    token = require_access_token(access_token)
    async with ShabAPIClient() as api:
        data = await api.list_credit_transactions(token, page=page)
    return {
        "page": page,
        "credit_transactions": _slim(_extract_list(data) or data),
        "currency": "Toman",
    }


def _safe(fn):  # type: ignore[no-untyped-def]
    async def wrapper(**kwargs: Any) -> dict[str, Any]:
        try:
            return await fn(**kwargs)
        except Exception as exc:
            return tool_error_payload(exc)

    return wrapper


get_host_dashboard_safe = _safe(get_host_dashboard_impl)
list_unanswered_reviews_safe = _safe(list_unanswered_reviews_impl)
get_host_profile_settings_safe = _safe(get_host_profile_settings_impl)
update_host_profile_settings_safe = _safe(update_host_profile_settings_impl)
list_host_checkouts_safe = _safe(list_host_checkouts_impl)
list_host_transactions_safe = _safe(list_host_transactions_impl)
get_host_transaction_safe = _safe(get_host_transaction_impl)
list_host_payments_safe = _safe(list_host_payments_impl)
get_settlement_type_safe = _safe(get_settlement_type_impl)
set_settlement_type_safe = _safe(set_settlement_type_impl)
list_withdraw_requests_safe = _safe(list_withdraw_requests_impl)
list_credit_transactions_safe = _safe(list_credit_transactions_impl)
