"""Guest lifecycle tools for Shab MCP v0.4: cancel, chat, reviews, status transitions."""

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
    for key in ("records", "messages", "chats", "reasons", "transitions", "data", "items"):
        val = data.get(key)
        if isinstance(val, list):
            return [x for x in val if isinstance(x, dict)]
    return []


def _slim(obj: Any, *, depth: int = 0) -> Any:
    if depth > 4:
        return None
    if isinstance(obj, list):
        return [_slim(x, depth=depth + 1) for x in obj[:50]]
    if isinstance(obj, dict):
        drop = {"meta", "links", "html", "raw"}
        return {k: _slim(v, depth=depth + 1) for k, v in obj.items() if k not in drop}
    return obj


async def list_cancellation_reasons_impl(*, access_token: str, reserve_id: str) -> dict[str, Any]:
    token = require_access_token(access_token)
    rid = (reserve_id or "").strip()
    if not rid:
        raise ShabValidationError("reserve_id (tiny id) is required.")
    async with ShabAPIClient() as api:
        data = await api.get_cancellation_reasons(token, rid)
    reasons = _extract_list(data) if not isinstance(data, list) else [
        x for x in data if isinstance(x, dict)
    ]
    if not reasons and isinstance(data, dict):
        reasons = _extract_list(data.get("reasons") or data)
    return {"reserve_id": rid, "reasons": _slim(reasons or data)}


async def get_cancellation_penalty_impl(
    *, access_token: str, reserve_id: str, reason_id: int
) -> dict[str, Any]:
    token = require_access_token(access_token)
    rid = (reserve_id or "").strip()
    if not rid:
        raise ShabValidationError("reserve_id is required.")
    if reason_id < 1:
        raise ShabValidationError("reason_id must be a positive integer.")
    async with ShabAPIClient() as api:
        data = await api.get_cancellation_penalty(token, rid, reason_id=reason_id)
    payload = data if isinstance(data, dict) else {"raw": data}
    return {
        "reserve_id": rid,
        "reason_id": reason_id,
        "penalty": _slim(payload),
        "currency": "Toman",
        "next_step": "Call cancel_booking with the same reason_id and confirm=true.",
    }


async def cancel_booking_impl(
    *,
    access_token: str,
    reserve_id: str,
    reason_id: int,
    description: str | None = None,
    accepted_penalty: int | None = None,
    confirm: bool = False,
) -> dict[str, Any]:
    if not confirm:
        raise ShabValidationError(
            "cancel_booking requires confirm=true after showing the cancellation penalty."
        )
    token = require_access_token(access_token)
    rid = (reserve_id or "").strip()
    if not rid:
        raise ShabValidationError("reserve_id is required.")
    if reason_id < 1:
        raise ShabValidationError("reason_id must be a positive integer.")
    async with ShabAPIClient() as api:
        data = await api.cancel_reserve(
            token,
            rid,
            reason_id=reason_id,
            description=(description or "").strip() or None,
            accepted_penalty=accepted_penalty,
        )
    return {"ok": True, "reserve_id": rid, "result": _slim(data)}


async def get_eligible_transitions_impl(*, access_token: str, reserve_id: str) -> dict[str, Any]:
    token = require_access_token(access_token)
    rid = (reserve_id or "").strip()
    if not rid:
        raise ShabValidationError("reserve_id is required.")
    async with ShabAPIClient() as api:
        data = await api.get_eligible_transitions(token, rid)
    transitions = data if isinstance(data, list) else _extract_list(data)
    if not transitions and isinstance(data, dict):
        transitions = data.get("transitions") or data.get("eligible") or data
    return {"reserve_id": rid, "transitions": _slim(transitions)}


async def change_booking_status_impl(
    *,
    access_token: str,
    reserve_id: str,
    transition: str,
    reason: str | None = None,
    dates: list[str] | None = None,
    confirm: bool = False,
) -> dict[str, Any]:
    if not confirm:
        raise ShabValidationError(
            "change_booking_status requires confirm=true (e.g. ABH accept, RBH reject)."
        )
    token = require_access_token(access_token)
    rid = (reserve_id or "").strip()
    code = (transition or "").strip()
    if not rid or not code:
        raise ShabValidationError("reserve_id and transition are required.")
    async with ShabAPIClient() as api:
        data = await api.change_reserve_status(
            token, rid, transition=code, reason=reason, dates=dates
        )
    return {"ok": True, "reserve_id": rid, "transition": code, "result": _slim(data)}


async def reject_booking_impl(
    *, access_token: str, reserve_id: str, confirm: bool = False
) -> dict[str, Any]:
    if not confirm:
        raise ShabValidationError("reject_booking requires confirm=true.")
    token = require_access_token(access_token)
    rid = (reserve_id or "").strip()
    if not rid:
        raise ShabValidationError("reserve_id is required.")
    async with ShabAPIClient() as api:
        data = await api.reject_reserve_guest(token, body={"reserve_id": rid})
    return {"ok": True, "reserve_id": rid, "result": _slim(data)}


async def list_chats_impl(*, access_token: str, page: int = 1) -> dict[str, Any]:
    token = require_access_token(access_token)
    async with ShabAPIClient() as api:
        data = await api.list_chats(token, page=page)
    return {"page": page, "chats": _slim(_extract_list(data) or data)}


async def get_chat_thread_impl(
    *, access_token: str, reserve_id: str, page: int = 1
) -> dict[str, Any]:
    token = require_access_token(access_token)
    rid = (reserve_id or "").strip()
    if not rid:
        raise ShabValidationError("reserve_id is required.")
    async with ShabAPIClient() as api:
        data = await api.get_reserve_chat(token, rid, page=page)
    messages = _extract_list(data)
    return {
        "reserve_id": rid,
        "page": page,
        "messages": _slim(messages or data),
        "note": "REST poll only; no Pusher. Re-call to refresh.",
    }


async def send_chat_message_impl(
    *, access_token: str, reserve_id: str, text: str, confirm: bool = False
) -> dict[str, Any]:
    if not confirm:
        raise ShabValidationError("send_chat_message requires confirm=true.")
    token = require_access_token(access_token)
    rid = (reserve_id or "").strip()
    body = (text or "").strip()
    if not rid or not body:
        raise ShabValidationError("reserve_id and text are required.")
    async with ShabAPIClient() as api:
        data = await api.send_chat_message(token, reserve_id=rid, text=body)
    return {"ok": True, "reserve_id": rid, "result": _slim(data)}


async def mark_chat_seen_impl(
    *, access_token: str, reserve_id: str, message_id: str
) -> dict[str, Any]:
    token = require_access_token(access_token)
    rid = (reserve_id or "").strip()
    mid = (message_id or "").strip()
    if not rid or not mid:
        raise ShabValidationError("reserve_id and message_id are required.")
    async with ShabAPIClient() as api:
        data = await api.mark_chat_seen(token, rid, mid)
    return {"ok": True, "reserve_id": rid, "message_id": mid, "result": _slim(data)}


async def get_review_for_reservation_impl(*, access_token: str, reserve_id: str) -> dict[str, Any]:
    token = require_access_token(access_token)
    rid = (reserve_id or "").strip()
    if not rid:
        raise ShabValidationError("reserve_id is required.")
    async with ShabAPIClient() as api:
        data = await api.get_review_reservation(token, rid)
    return {"reserve_id": rid, "review": _slim(data)}


async def submit_review_impl(
    *,
    access_token: str,
    reserve_id: str,
    step: int,
    host: int | None = None,
    value: int | None = None,
    accuracy: int | None = None,
    cleanliness: int | None = None,
    accessibility: int | None = None,
    suggest: int | None = None,
    positives: list[str] | None = None,
    negatives: list[str] | None = None,
    description: str | None = None,
    anonymous: bool | None = None,
    private_message: str | None = None,
    confirm: bool = False,
) -> dict[str, Any]:
    """Submit one review wizard step (1=points, 2=positives, 3=negatives, 4=description)."""
    if not confirm:
        raise ShabValidationError("submit_review requires confirm=true.")
    token = require_access_token(access_token)
    rid = (reserve_id or "").strip()
    if not rid:
        raise ShabValidationError("reserve_id is required.")
    if step not in {1, 2, 3, 4}:
        raise ShabValidationError("step must be 1 (points), 2 (positives), 3 (negatives), or 4 (description).")
    body: dict[str, Any] = {"reservation_id": rid, "step": step}
    if step == 1:
        for key, val in (
            ("host", host),
            ("value", value),
            ("accuracy", accuracy),
            ("cleanliness", cleanliness),
            ("accessibility", accessibility),
            ("suggest", suggest),
        ):
            if val is not None:
                body[key] = val
    elif step == 2 and positives is not None:
        body["positives"] = positives
    elif step == 3 and negatives is not None:
        body["negatives"] = negatives
    elif step == 4:
        if description is not None:
            body["description"] = description
        if anonymous is not None:
            body["anonymous"] = anonymous
        if private_message is not None:
            body["private_message"] = private_message
    async with ShabAPIClient() as api:
        data = await api.store_review(token, payload=body)
    return {"ok": True, "reserve_id": rid, "step": step, "result": _slim(data)}


async def comment_on_review_impl(
    *,
    access_token: str,
    review_id: str,
    comment: str,
    confirm: bool = False,
) -> dict[str, Any]:
    if not confirm:
        raise ShabValidationError("comment_on_review requires confirm=true.")
    token = require_access_token(access_token)
    rid = (review_id or "").strip()
    text = (comment or "").strip()
    if not rid or not text:
        raise ShabValidationError("review_id and comment are required.")
    async with ShabAPIClient() as api:
        data = await api.store_review_comment(
            token, payload={"review_id": rid, "comment": text}
        )
    return {"ok": True, "review_id": rid, "result": _slim(data)}


async def list_my_reviews_impl(*, access_token: str, page: int = 1) -> dict[str, Any]:
    token = require_access_token(access_token)
    async with ShabAPIClient() as api:
        data = await api.list_my_reviews(token, page=page)
    return {"page": page, "reviews": _slim(_extract_list(data) or data)}


def _safe(fn):  # type: ignore[no-untyped-def]
    async def wrapper(**kwargs: Any) -> dict[str, Any]:
        try:
            return await fn(**kwargs)
        except Exception as exc:
            return tool_error_payload(exc)

    return wrapper


list_cancellation_reasons_safe = _safe(list_cancellation_reasons_impl)
get_cancellation_penalty_safe = _safe(get_cancellation_penalty_impl)
cancel_booking_safe = _safe(cancel_booking_impl)
get_eligible_transitions_safe = _safe(get_eligible_transitions_impl)
change_booking_status_safe = _safe(change_booking_status_impl)
reject_booking_safe = _safe(reject_booking_impl)
list_chats_safe = _safe(list_chats_impl)
get_chat_thread_safe = _safe(get_chat_thread_impl)
send_chat_message_safe = _safe(send_chat_message_impl)
mark_chat_seen_safe = _safe(mark_chat_seen_impl)
get_review_for_reservation_safe = _safe(get_review_for_reservation_impl)
submit_review_safe = _safe(submit_review_impl)
comment_on_review_safe = _safe(comment_on_review_impl)
list_my_reviews_safe = _safe(list_my_reviews_impl)
