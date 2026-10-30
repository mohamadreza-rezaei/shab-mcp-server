"""HTTP client for Shab backoffice v1.4 (Call Center / Host & Guest Office MCP).

Importers: tools/office_*.py, tests. Affected API: backoffice v_1_4.
User: Implement the plan as specified.
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

from shab_mcp import __version__
from shab_mcp.config import Settings, get_settings
from shab_mcp.errors import (
    ShabAuthenticationError,
    ShabNotFoundError,
    ShabRateLimitedError,
    ShabTimeoutError,
    ShabUpstreamError,
    ShabUpstreamUnavailableError,
    ShabValidationError,
)

logger = logging.getLogger(__name__)
RETRYABLE_STATUS = {408, 429, 500, 502, 503, 504}


class OfficeAPIClient:
    """Async client for `api/{lang}/{version}/backoffice`."""

    def __init__(
        self,
        settings: Settings | None = None,
        *,
        client: httpx.AsyncClient | None = None,
        staff_token: str | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self._client = client
        self._owns_client = client is None
        self.staff_token = staff_token

    async def __aenter__(self) -> OfficeAPIClient:
        if self._client is None:
            timeout = httpx.Timeout(
                connect=self.settings.shab_connect_timeout,
                read=self.settings.shab_read_timeout,
                write=self.settings.shab_read_timeout,
                pool=self.settings.shab_connect_timeout,
            )
            self._client = httpx.AsyncClient(
                timeout=timeout,
                headers={
                    "User-Agent": f"shab-mcp/{__version__}",
                    "Accept": "application/json",
                    "Origin": self.settings.shab_api_origin,
                    "Platform": self.settings.shab_api_platform,
                    "Client-Id": self.settings.shab_backoffice_client_id,
                    "currency": "IRT",
                },
                follow_redirects=True,
            )
        return self

    async def __aexit__(self, *args: object) -> None:
        if self._owns_client and self._client is not None:
            await self._client.aclose()
            self._client = None

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None:
            raise RuntimeError("OfficeAPIClient must be used as an async context manager")
        return self._client

    def _url(self, path: str) -> str:
        return f"{self.settings.backoffice_prefix}/{path.lstrip('/')}"

    def _auth_headers(self, staff_token: str | None = None) -> dict[str, str]:
        token = staff_token if staff_token is not None else self.staff_token
        if not token:
            return {}
        return {"Authorization": f"Bearer {token}"}

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | list[tuple[str, Any]] | None = None,
        json: dict[str, Any] | None = None,
        staff_token: str | None = None,
    ) -> Any:
        url = self._url(path)
        headers = self._auth_headers(staff_token)
        attempts = self.settings.shab_max_retries + 1
        last_exc: Exception | None = None

        for attempt in range(attempts):
            try:
                response = await self.client.request(
                    method,
                    url,
                    params=params,
                    json=json,
                    headers=headers or None,
                )
            except httpx.TimeoutException as exc:
                last_exc = ShabTimeoutError("Backoffice API request timed out. Please retry later.")
                if attempt + 1 >= attempts:
                    raise last_exc from exc
                continue
            except httpx.TransportError as exc:
                last_exc = ShabUpstreamUnavailableError(
                    "Backoffice API temporarily unavailable. Please retry later."
                )
                if attempt + 1 >= attempts:
                    raise last_exc from exc
                continue

            if response.status_code in {401, 403}:
                return self._parse_response(response)

            if response.status_code in RETRYABLE_STATUS and attempt + 1 < attempts:
                logger.warning(
                    "office_api retry status=%s attempt=%s path=%s",
                    response.status_code,
                    attempt + 1,
                    path,
                )
                continue

            return self._parse_response(response)

        if last_exc:
            raise last_exc
        raise ShabUpstreamError("Backoffice API request failed after retries.")

    def _parse_response(self, response: httpx.Response) -> Any:
        status = response.status_code
        try:
            payload = response.json()
        except ValueError as exc:
            raise ShabUpstreamError(
                f"Backoffice API returned non-JSON response (HTTP {status})."
            ) from exc

        if status in {401, 403}:
            raise ShabAuthenticationError(
                "Staff authentication failed. Call office_login again.",
                details=(payload.get("meta") if isinstance(payload, dict) else payload),
            )
        if status == 404:
            raise ShabNotFoundError("Requested backoffice resource was not found.")
        if status == 429:
            raise ShabRateLimitedError("Backoffice API rate limit exceeded. Please retry later.")
        if status == 422:
            messages = None
            if isinstance(payload, dict):
                messages = (payload.get("meta") or {}).get("messages") or payload.get("messages")
            raise ShabValidationError(
                "Backoffice API rejected the request parameters.",
                details=messages,
            )
        if status >= 500:
            raise ShabUpstreamUnavailableError(
                "Backoffice API temporarily unavailable. Please retry later."
            )
        if status >= 400:
            raise ShabUpstreamError(
                f"Backoffice API error (HTTP {status}).",
                details=(payload.get("meta") if isinstance(payload, dict) else payload),
            )

        if isinstance(payload, dict) and "data" in payload and "meta" in payload:
            meta = payload.get("meta") or {}
            meta_status = meta.get("status")
            if isinstance(meta_status, int) and meta_status >= 400:
                if meta_status in {401, 403}:
                    raise ShabAuthenticationError(
                        "Staff authentication failed. Call office_login again.",
                        details=meta.get("messages"),
                    )
                if meta_status == 404:
                    raise ShabNotFoundError("Requested backoffice resource was not found.")
                if meta_status == 422:
                    raise ShabValidationError(
                        "Backoffice API rejected the request parameters.",
                        details=meta.get("messages"),
                    )
                raise ShabUpstreamError(
                    f"Backoffice API error (status {meta_status}).",
                    details=meta.get("messages"),
                )
            return payload.get("data")
        return payload

    async def login(self, mobile: str, password: str) -> Any:
        return await self._request(
            "POST",
            "auth/login",
            json={"mobile": mobile, "password": password, "is_remember": 1},
        )

    async def logout(self, staff_token: str) -> Any:
        return await self._request("POST", "auth/logout", staff_token=staff_token)

    async def bootstrap(self, staff_token: str) -> Any:
        return await self._request("GET", "bootstrap", staff_token=staff_token)

    async def search_users(self, staff_token: str, params: dict[str, Any] | None = None) -> Any:
        return await self._request("GET", "user", params=params or {}, staff_token=staff_token)

    async def get_user(self, staff_token: str, user_id: int) -> Any:
        return await self._request("GET", f"user/{user_id}", staff_token=staff_token)

    async def get_user_stats(self, staff_token: str, user_id: int) -> Any:
        return await self._request("GET", f"user/{user_id}/statistic", staff_token=staff_token)

    async def search_reserves(self, staff_token: str, params: dict[str, Any] | None = None) -> Any:
        return await self._request("GET", "reserve", params=params or {}, staff_token=staff_token)

    async def get_reserve(self, staff_token: str, reserve_id: int) -> Any:
        return await self._request("GET", f"reserve/{reserve_id}", staff_token=staff_token)

    async def get_reserve_chat(self, staff_token: str, reserve_id: int) -> Any:
        return await self._request("GET", f"reserve/{reserve_id}/chat", staff_token=staff_token)

    async def get_reserve_transitions(self, staff_token: str, reserve_id: int) -> Any:
        return await self._request(
            "GET", f"reserve/{reserve_id}/eligible-transitions", staff_token=staff_token
        )

    async def search_houses(self, staff_token: str, params: dict[str, Any] | None = None) -> Any:
        return await self._request("GET", "house", params=params or {}, staff_token=staff_token)

    async def get_house(self, staff_token: str, house_id: int) -> Any:
        return await self._request("GET", f"house/{house_id}", staff_token=staff_token)

    async def list_chats(self, staff_token: str, params: dict[str, Any] | None = None) -> Any:
        return await self._request("GET", "chat", params=params or {}, staff_token=staff_token)

    async def list_notes(self, staff_token: str, params: dict[str, Any] | None = None) -> Any:
        return await self._request("GET", "notes", params=params or {}, staff_token=staff_token)

    async def get_notes(self, staff_token: str, note_type: str, model_id: int) -> Any:
        return await self._request(
            "GET", f"notes/{note_type}/{model_id}", staff_token=staff_token
        )

    async def change_reserve_status(self, staff_token: str, body: dict[str, Any]) -> Any:
        return await self._request(
            "POST", "reserve/change-status", json=body, staff_token=staff_token
        )

    async def cancel_reserve(self, staff_token: str, reserve_id: int, body: dict[str, Any]) -> Any:
        return await self._request(
            "POST", f"reserve/{reserve_id}/cancel", json=body, staff_token=staff_token
        )

    async def tag_reserve(self, staff_token: str, reservation_id: int, body: dict[str, Any]) -> Any:
        return await self._request(
            "POST", f"reserve/{reservation_id}/tag", json=body, staff_token=staff_token
        )

    async def search_payments(self, staff_token: str, params: dict[str, Any] | None = None) -> Any:
        return await self._request("GET", "payment", params=params or {}, staff_token=staff_token)

    async def refund_payment(
        self, staff_token: str, payment_id: int, body: dict[str, Any] | None = None
    ) -> Any:
        return await self._request(
            "POST", f"payment/{payment_id}/refund", json=body or {}, staff_token=staff_token
        )

    async def list_message_templates(self, staff_token: str) -> Any:
        return await self._request(
            "GET", "notification/message-templates", staff_token=staff_token
        )

    async def send_notification(self, staff_token: str, body: dict[str, Any]) -> Any:
        return await self._request("POST", "notification", json=body, staff_token=staff_token)

    async def add_note(self, staff_token: str, body: dict[str, Any]) -> Any:
        return await self._request("POST", "notes", json=body, staff_token=staff_token)

    async def list_checkin_followups(
        self, staff_token: str, params: dict[str, Any] | None = None
    ) -> Any:
        return await self._request(
            "GET",
            "followup/reservations/checkin",
            params=params or {},
            staff_token=staff_token,
        )

    async def update_checkin_followup(
        self, staff_token: str, reservation_id: int, body: dict[str, Any]
    ) -> Any:
        return await self._request(
            "POST",
            f"followup/reservations/checkin/{reservation_id}",
            json=body,
            staff_token=staff_token,
        )

    async def list_cancellation_followups(
        self, staff_token: str, params: dict[str, Any] | None = None
    ) -> Any:
        return await self._request(
            "GET",
            "followup/reservations/cancellation",
            params=params or {},
            staff_token=staff_token,
        )

    async def list_review_followups(
        self, staff_token: str, params: dict[str, Any] | None = None
    ) -> Any:
        return await self._request(
            "GET",
            "followup/reservations/review",
            params=params or {},
            staff_token=staff_token,
        )

    async def set_house_support_status(self, staff_token: str, body: dict[str, Any]) -> Any:
        return await self._request(
            "POST",
            "house/support-status/change-status",
            json=body,
            staff_token=staff_token,
        )

    async def easy_login_link(
        self, staff_token: str, user_id: int, agent_mobile: str
    ) -> Any:
        return await self._request(
            "POST",
            f"user/{user_id}/easy/login-link",
            json={"agent_mobile": agent_mobile},
            staff_token=staff_token,
        )

    async def easy_login_token(
        self, staff_token: str, user_id: int, agent_mobile: str | None = None
    ) -> Any:
        body: dict[str, Any] = {}
        if agent_mobile:
            body["agent_mobile"] = agent_mobile
        return await self._request(
            "POST",
            f"user/{user_id}/easy/login-token",
            json=body,
            staff_token=staff_token,
        )

    async def list_reviews(self, staff_token: str, params: dict[str, Any] | None = None) -> Any:
        return await self._request("GET", "review", params=params or {}, staff_token=staff_token)

    async def update_review(
        self, staff_token: str, review_id: int, body: dict[str, Any]
    ) -> Any:
        return await self._request(
            "POST", f"review/{review_id}/update", json=body, staff_token=staff_token
        )

    async def edit_host_guest_financials(self, staff_token: str, body: dict[str, Any]) -> Any:
        return await self._request(
            "POST",
            "financial/edit-host-and-guest-records",
            json=body,
            staff_token=staff_token,
        )

    async def list_withdraw_requests(
        self, staff_token: str, params: dict[str, Any] | None = None
    ) -> Any:
        return await self._request(
            "GET",
            "user/withdraw-requests",
            params=params or {},
            staff_token=staff_token,
        )

    async def review_withdraw(
        self, staff_token: str, request_id: int, status: str, body: dict[str, Any] | None = None
    ) -> Any:
        return await self._request(
            "POST",
            f"user/withdraw-requests/{request_id}/review/{status}",
            json=body or {},
            staff_token=staff_token,
        )
