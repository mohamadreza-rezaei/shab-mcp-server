"""Auth tools for Shab MCP v0.2.

Importers/callers: server.py registers request_login_otp, verify_login_otp,
get_auth_status, logout; booking.py and trips.py import require_access_token.
Affected API: POST auth/login-otp, auth/verify-otp, auth/logout; GET user.
Schemas: mobile 09xxxxxxxxx; verify returns access_token + user summary.
User instruction: "Implement the plan as specified" (OTP-in-chat auth).
"""

from __future__ import annotations

import re
from typing import Any

from shab_mcp.client import ShabAPIClient
from shab_mcp.errors import ShabAuthenticationError, ShabValidationError, tool_error_payload
from shab_mcp.normalize import normalize_user_summary

_MOBILE_RE = re.compile(r"^09\d{9}$")


def normalize_mobile(mobile: str) -> str:
    digits = re.sub(r"\D", "", mobile or "")
    if digits.startswith("98") and len(digits) == 12:
        digits = "0" + digits[2:]
    if len(digits) == 10 and digits.startswith("9"):
        digits = "0" + digits
    if not _MOBILE_RE.match(digits):
        raise ShabValidationError("mobile must be an Iranian number like 09xxxxxxxxx.")
    return digits


def require_access_token(access_token: str | None) -> str:
    token = (access_token or "").strip()
    if not token:
        raise ShabAuthenticationError(
            "access_token is required. Call request_login_otp then verify_login_otp first."
        )
    return token


async def request_login_otp_impl(*, mobile: str) -> dict[str, Any]:
    normalized = normalize_mobile(mobile)
    async with ShabAPIClient() as api:
        await api.login_otp(normalized)
    return {
        "ok": True,
        "mobile": normalized,
        "message": "OTP sent by SMS. Ask the user for the code, then call verify_login_otp.",
    }


async def verify_login_otp_impl(*, mobile: str, code: str) -> dict[str, Any]:
    normalized = normalize_mobile(mobile)
    otp = re.sub(r"\D", "", code or "")
    if len(otp) < 4:
        raise ShabValidationError("code must be the SMS OTP digits.")

    async with ShabAPIClient() as api:
        data = await api.verify_otp(normalized, otp)

    if isinstance(data, dict) and data.get("status") == "register":
        return {
            "ok": False,
            "status": "register",
            "message": (
                "This mobile is not registered on Shab yet. "
                "Complete registration on www.shab.ir, then retry OTP login."
            ),
        }

    token = None
    if isinstance(data, dict):
        token = data.get("access_token")
    if not token:
        raise ShabAuthenticationError(
            "OTP verified but no access_token returned. "
            "Check SHAB_API_ORIGIN is non-stateful (not a shab.ir SPA domain)."
        )

    user = normalize_user_summary(data)
    return {
        "ok": True,
        "access_token": token,
        "user": user,
        "message": (
            "Authenticated. Pass access_token to booking/trip tools. "
            "Treat the token as a secret."
        ),
    }


async def get_auth_status_impl(*, access_token: str) -> dict[str, Any]:
    token = require_access_token(access_token)
    async with ShabAPIClient() as api:
        data = await api.get_current_user(token)
    return {"authenticated": True, "user": normalize_user_summary(data)}


async def logout_impl(*, access_token: str) -> dict[str, Any]:
    token = require_access_token(access_token)
    async with ShabAPIClient() as api:
        await api.logout(token)
    return {"ok": True, "message": "Logged out; access_token revoked."}


async def request_login_otp_safe(**kwargs: Any) -> dict[str, Any]:
    try:
        return await request_login_otp_impl(**kwargs)
    except Exception as exc:
        return tool_error_payload(exc)


async def verify_login_otp_safe(**kwargs: Any) -> dict[str, Any]:
    try:
        return await verify_login_otp_impl(**kwargs)
    except Exception as exc:
        return tool_error_payload(exc)


async def get_auth_status_safe(**kwargs: Any) -> dict[str, Any]:
    try:
        return await get_auth_status_impl(**kwargs)
    except Exception as exc:
        return tool_error_payload(exc)


async def logout_safe(**kwargs: Any) -> dict[str, Any]:
    try:
        return await logout_impl(**kwargs)
    except Exception as exc:
        return tool_error_payload(exc)
