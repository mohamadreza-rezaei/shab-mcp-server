"""Host dashboard, finance, and host-profile tools for Shab MCP v0.8."""

from __future__ import annotations

from typing import Any

from shab_mcp.client import ShabAPIClient
from shab_mcp.errors import ShabValidationError, tool_error_payload
from shab_mcp.tools.auth import require_access_token


def _slim(obj: Any, *, depth: int = 0) -> Any:
    if depth > 5:
        return None
    if isinstance(obj, list):
        return [_slim(x, depth=depth + 1) for x in obj[:100]]
    if isinstance(obj, dict):
        return {k: _slim(v, depth=depth + 1) for k, v in obj.items() if k not in {"html"}}
    return obj


async def get_host_dashboard_impl(*, access_token: str) -> dict[str, Any]:
    token = require_access_token(access_token)
    async with ShabAPIClient() as api:
        glance = await api.get_host_dashboard_glance(token)
        notices = None
        performance = None
        try:
            notices = await api.get_host_dashboard_notices(token)
        except Exception:
            notices = None
        try:
            performance = await api.get_host_performance(token)
        except Exception:
            performance = None
    return {
        "at_a_glance": _slim(glance),
        "notices": _slim(notices),
        "performance": _slim(performance),
    }


async def list_unanswered_reviews_impl(*, access_token: str) -> dict[str, Any]:
    token = require_access_token(access_token)
    async with ShabAPIClient() as api:
        data = await api.get_unanswered_reviews(token)
    return {"reviews": _slim(data)}


async def get_my_host_profile_impl(*, access_token: str) -> dict[str, Any]:
    token = require_access_token(access_token)
    async with ShabAPIClient() as api:
        data = await api.get_host_profile(token)
    return {"host_profile": _slim(data)}


async def update_my_host_profile_impl(
    *, access_token: str, payload: dict[str, Any], confirm: bool = False
) -> dict[str, Any]:
    if not confirm:
        raise ShabValidationError("update_my_host_profile requires confirm=true.")
    token = require_access_token(access_token)
    if not payload:
        raise ShabValidationError("payload is required.")
    async with ShabAPIClient() as api:
        data = await api.update_host_profile(token, payload=payload)
    return {"ok": True, "host_profile": _slim(data)}


async def list_host_payments_impl(*, access_token: str, page: int = 1) -> dict[str, Any]:
    token = require_access_token(access_token)
    async with ShabAPIClient() as api:
        data = await api.get_profile_payments(token, page=page)
    return {"page": page, "payments": _slim(data), "currency": "Toman"}


async def list_host_transactions_impl(*, access_token: str, page: int = 1) -> dict[str, Any]:
    token = require_access_token(access_token)
    async with ShabAPIClient() as api:
        data = await api.get_profile_transactions(token, page=page)
    return {"page": page, "transactions": _slim(data), "currency": "Toman"}


async def list_host_checkouts_impl(*, access_token: str, page: int = 1) -> dict[str, Any]:
    token = require_access_token(access_token)
    async with ShabAPIClient() as api:
        data = await api.get_profile_checkouts(token, page=page)
    return {"page": page, "checkouts": _slim(data), "currency": "Toman"}


async def list_withdraw_requests_impl(*, access_token: str) -> dict[str, Any]:
    token = require_access_token(access_token)
    async with ShabAPIClient() as api:
        data = await api.get_withdraw_requests(token)
    return {"withdraw_requests": _slim(data), "currency": "Toman"}


async def get_settlement_type_impl(*, access_token: str) -> dict[str, Any]:
    token = require_access_token(access_token)
    async with ShabAPIClient() as api:
        data = await api.get_settlement_type(token)
    return {"settlement": _slim(data)}


async def get_host_statistics_impl(*, access_token: str) -> dict[str, Any]:
    token = require_access_token(access_token)
    async with ShabAPIClient() as api:
        overall = await api.get_overall_statistics(token)
        sales = None
        try:
            sales = await api.get_sale_statistics(token)
        except Exception:
            sales = None
    return {"overall": _slim(overall), "sales": _slim(sales), "currency": "Toman"}


async def get_house_statistics_impl(*, access_token: str, house_id: int) -> dict[str, Any]:
    token = require_access_token(access_token)
    if house_id < 1:
        raise ShabValidationError("house_id must be positive.")
    async with ShabAPIClient() as api:
        data = await api.get_house_statistics(token, house_id)
    return {"house_id": house_id, "statistics": _slim(data), "currency": "Toman"}


def _safe(fn):  # type: ignore[no-untyped-def]
    async def wrapper(**kwargs: Any) -> dict[str, Any]:
        try:
            return await fn(**kwargs)
        except Exception as exc:
            return tool_error_payload(exc)

    return wrapper


get_host_dashboard_safe = _safe(get_host_dashboard_impl)
list_unanswered_reviews_safe = _safe(list_unanswered_reviews_impl)
get_my_host_profile_safe = _safe(get_my_host_profile_impl)
update_my_host_profile_safe = _safe(update_my_host_profile_impl)
list_host_payments_safe = _safe(list_host_payments_impl)
list_host_transactions_safe = _safe(list_host_transactions_impl)
list_host_checkouts_safe = _safe(list_host_checkouts_impl)
list_withdraw_requests_safe = _safe(list_withdraw_requests_impl)
get_settlement_type_safe = _safe(get_settlement_type_impl)
get_host_statistics_safe = _safe(get_host_statistics_impl)
get_house_statistics_safe = _safe(get_house_statistics_impl)
