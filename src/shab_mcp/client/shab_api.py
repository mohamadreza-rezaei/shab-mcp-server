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


class ShabAPIClient:
    """Async HTTP client for Shab sandbox v1.4 (public + authenticated guest flows)."""

    def __init__(
        self,
        settings: Settings | None = None,
        *,
        client: httpx.AsyncClient | None = None,
        access_token: str | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self._client = client
        self._owns_client = client is None
        self.access_token = access_token

    async def __aenter__(self) -> ShabAPIClient:
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
            raise RuntimeError("ShabAPIClient must be used as an async context manager")
        return self._client

    def _url(self, path: str) -> str:
        return f"{self.settings.api_prefix}/{path.lstrip('/')}"

    def _auth_headers(self, access_token: str | None = None) -> dict[str, str]:
        token = access_token if access_token is not None else self.access_token
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
        access_token: str | None = None,
    ) -> Any:
        url = self._url(path)
        headers = self._auth_headers(access_token)
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
                last_exc = ShabTimeoutError("Shab API request timed out. Please retry later.")
                if attempt + 1 >= attempts:
                    raise last_exc from exc
                continue
            except httpx.TransportError as exc:
                last_exc = ShabUpstreamUnavailableError(
                    "Shab API temporarily unavailable. Please retry later."
                )
                if attempt + 1 >= attempts:
                    raise last_exc from exc
                continue

            # Never retry auth failures.
            if response.status_code in {401, 403}:
                return self._parse_response(response)

            if response.status_code in RETRYABLE_STATUS and attempt + 1 < attempts:
                logger.warning(
                    "shab_api retry status=%s attempt=%s path=%s",
                    response.status_code,
                    attempt + 1,
                    path,
                )
                continue

            return self._parse_response(response)

        if last_exc:
            raise last_exc
        raise ShabUpstreamError("Shab API request failed after retries.")

    def _parse_response(self, response: httpx.Response) -> Any:
        status = response.status_code
        try:
            payload = response.json()
        except ValueError as exc:
            raise ShabUpstreamError(
                f"Shab API returned non-JSON response (HTTP {status})."
            ) from exc

        if status in {401, 403}:
            raise ShabAuthenticationError(
                "Shab authentication failed. Request a new OTP or pass a valid access_token.",
                details=(payload.get("meta") if isinstance(payload, dict) else payload),
            )
        if status == 404:
            raise ShabNotFoundError("Requested Shab resource was not found.")
        if status == 429:
            raise ShabRateLimitedError("Shab API rate limit exceeded. Please retry later.")
        if status == 422:
            messages = None
            if isinstance(payload, dict):
                messages = (payload.get("meta") or {}).get("messages") or payload.get("messages")
            raise ShabValidationError(
                "Shab API rejected the request parameters.",
                details=messages,
            )
        if status >= 500:
            raise ShabUpstreamUnavailableError(
                "Shab API temporarily unavailable. Please retry later."
            )
        if status >= 400:
            raise ShabUpstreamError(
                f"Shab API error (HTTP {status}).",
                details=(payload.get("meta") if isinstance(payload, dict) else payload),
            )

        if isinstance(payload, dict) and "data" in payload and "meta" in payload:
            meta = payload.get("meta") or {}
            meta_status = meta.get("status")
            if isinstance(meta_status, int) and meta_status >= 400:
                if meta_status in {401, 403}:
                    raise ShabAuthenticationError(
                        "Shab authentication failed. Request a new OTP or pass a valid access_token.",
                        details=meta.get("messages"),
                    )
                if meta_status == 404:
                    raise ShabNotFoundError("Requested Shab resource was not found.")
                if meta_status == 422:
                    raise ShabValidationError(
                        "Shab API rejected the request parameters.",
                        details=meta.get("messages"),
                    )
                raise ShabUpstreamError(
                    f"Shab API error (status {meta_status}).",
                    details=meta.get("messages"),
                )
            return payload.get("data")
        return payload

    # --- public read ---

    async def search_houses(self, params: list[tuple[str, Any]]) -> Any:
        return await self._request("GET", "house/search", params=params)

    async def get_search_filters(self) -> Any:
        return await self._request("GET", "search/filters")

    async def get_house(self, house_id: int) -> Any:
        return await self._request("GET", f"house/{house_id}")

    async def get_house_photos(self, house_id: int) -> Any:
        return await self._request("GET", f"house/{house_id}/photos")

    async def get_house_reviews(self, house_id: int, *, page: int = 1) -> Any:
        return await self._request("GET", f"house/{house_id}/reviews", params={"page": page})

    async def get_house_calendar(
        self,
        house_id: int,
        *,
        from_date: str,
        to_date: str,
    ) -> Any:
        return await self._request(
            "GET",
            f"house/{house_id}/calendar",
            params={"from_date": from_date, "to_date": to_date},
        )

    async def get_proforma(
        self,
        *,
        house_id: int,
        checkin: str,
        checkout: str,
        guests_count: int,
        discount_code: str | None = None,
    ) -> Any:
        params: dict[str, Any] = {
            "house_id": house_id,
            "checkin": checkin,
            "checkout": checkout,
            "guests_count": guests_count,
        }
        if discount_code:
            params["discount_code"] = discount_code
        return await self._request("GET", "reserve/proforma", params=params)

    async def house_suggestions(self, phrase: str) -> Any:
        return await self._request("GET", "house/suggestions", params={"phrase": phrase})

    async def region_suggestions(self, phrase: str) -> Any:
        return await self._request("GET", "region/suggestions", params={"phrase": phrase})

    async def get_public_profile(self, user_uid: str) -> Any:
        return await self._request("GET", f"profile/{user_uid}")

    async def get_neighbourhoods(self, *, city: str | None = None) -> Any:
        params: dict[str, Any] = {}
        if city:
            params["city"] = city
        return await self._request("GET", "house/neighbourhoods", params=params or None)

    async def get_similar_houses(self, house_id: int) -> Any:
        return await self._request("GET", f"house/{house_id}/similar")

    async def count_houses(self, params: list[tuple[str, Any]]) -> Any:
        return await self._request("GET", "house/count", params=params)

    async def get_landing_tehran(self) -> Any:
        return await self._request("GET", "landing/tehran")

    # --- auth ---

    async def login_otp(self, mobile: str) -> Any:
        return await self._request("POST", "auth/login-otp", json={"mobile": mobile})

    async def verify_otp(self, mobile: str, code: str) -> Any:
        return await self._request(
            "POST",
            "auth/verify-otp",
            json={"mobile": mobile, "code": code},
        )

    async def logout(self, access_token: str) -> Any:
        return await self._request("POST", "auth/logout", access_token=access_token)

    async def get_current_user(self, access_token: str) -> Any:
        return await self._request("GET", "user", access_token=access_token)

    # --- booking / trips ---

    async def create_reserve(
        self,
        access_token: str,
        *,
        house_id: int,
        checkin: str,
        checkout: str,
        guests_count: int,
    ) -> Any:
        return await self._request(
            "POST",
            "reserve",
            json={
                "house_id": house_id,
                "checkin": checkin,
                "checkout": checkout,
                "guests_count": guests_count,
            },
            access_token=access_token,
        )

    async def calculate_invoice(
        self,
        access_token: str,
        *,
        invoice_id: str,
        discount_code: str | None = None,
        use_credit: bool = False,
        prepay_total_fee: bool = False,
    ) -> Any:
        body: dict[str, Any] = {
            "invoice_id": invoice_id,
            "use_credit": use_credit,
            "prepay_total_fee": prepay_total_fee,
        }
        if discount_code:
            body["discount_code"] = discount_code
        return await self._request(
            "POST",
            "invoice/calculate",
            json=body,
            access_token=access_token,
        )

    async def get_invoice(self, access_token: str, invoice_id: str) -> Any:
        return await self._request("GET", f"invoice/{invoice_id}/show", access_token=access_token)

    async def get_payment_gateways(self, access_token: str, reservation_id: str) -> Any:
        return await self._request(
            "GET",
            "payment/gateways",
            params={"reservation": reservation_id},
            access_token=access_token,
        )

    async def list_trips(self, access_token: str, *, page: int = 1) -> Any:
        return await self._request(
            "GET",
            "reserve/trips",
            params={"page": page},
            access_token=access_token,
        )

    async def get_reserve(self, access_token: str, reserve_id: str) -> Any:
        return await self._request("GET", f"reserve/{reserve_id}", access_token=access_token)

    async def get_reserve_host(self, access_token: str, reserve_id: str) -> Any:
        return await self._request("GET", f"reserve/{reserve_id}/host", access_token=access_token)

    async def list_reserves(
        self,
        access_token: str,
        *,
        page: int = 1,
        reserve_type: str | None = "guest",
        new: bool = True,
    ) -> Any:
        params: dict[str, Any] = {"page": page}
        if new:
            params["new"] = "1"
        if reserve_type:
            params["type"] = reserve_type
        return await self._request(
            "GET",
            "reserve",
            params=params,
            access_token=access_token,
        )

    async def get_cancellation_reasons(self, access_token: str, tiny_id: str) -> Any:
        return await self._request(
            "GET", f"reserve/{tiny_id}/cancellation-reasons", access_token=access_token
        )

    async def get_cancellation_penalty(
        self, access_token: str, tiny_id: str, *, reason_id: int
    ) -> Any:
        return await self._request(
            "GET",
            f"reserve/{tiny_id}/cancellation-penalty",
            params={"reason_id": reason_id},
            access_token=access_token,
        )

    async def cancel_reserve(
        self,
        access_token: str,
        tiny_id: str,
        *,
        reason_id: int,
        description: str | None = None,
        accepted_penalty: int | None = None,
    ) -> Any:
        body: dict[str, Any] = {"reason_id": reason_id}
        if description:
            body["description"] = description
        if accepted_penalty is not None:
            body["accepted_penalty"] = accepted_penalty
        return await self._request(
            "POST", f"reserve/{tiny_id}/cancel", json=body, access_token=access_token
        )

    async def get_eligible_transitions(self, access_token: str, reserve_id: str) -> Any:
        return await self._request(
            "GET",
            f"reserve/{reserve_id}/eligible-transitions",
            access_token=access_token,
        )

    async def change_reserve_status(
        self,
        access_token: str,
        reserve_id: str,
        *,
        transition: str,
        reason: str | None = None,
        dates: list[str] | None = None,
        extra: dict[str, Any] | None = None,
    ) -> Any:
        body: dict[str, Any] = {"transition": transition}
        if reason:
            body["reason"] = reason
        if dates:
            body["dates"] = dates
        if extra:
            body.update(extra)
        return await self._request(
            "POST",
            f"reserve/{reserve_id}/change-status",
            json=body,
            access_token=access_token,
        )

    async def reject_reserve_guest(
        self, access_token: str, *, body: dict[str, Any]
    ) -> Any:
        return await self._request(
            "POST", "reserve/reject", json=body, access_token=access_token
        )

    async def list_chats(self, access_token: str, *, page: int = 1) -> Any:
        return await self._request(
            "GET", "chat", params={"page": page}, access_token=access_token
        )

    async def get_reserve_chat(
        self, access_token: str, reserve_id: str, *, page: int = 1
    ) -> Any:
        return await self._request(
            "GET",
            f"reserve/{reserve_id}/chat",
            params={"page": page},
            access_token=access_token,
        )

    async def send_chat_message(
        self,
        access_token: str,
        *,
        reserve_id: str,
        text: str,
        msg_type: str = "TEXT",
    ) -> Any:
        return await self._request(
            "POST",
            "chat",
            json={
                "reserve_id": reserve_id,
                "text": text,
                "type": msg_type,
                "reference_id": None,
                "client_ref": None,
            },
            access_token=access_token,
        )

    async def mark_chat_seen(
        self, access_token: str, reserve_id: str, message_id: str
    ) -> Any:
        return await self._request(
            "POST",
            f"chat/reserve/{reserve_id}/message/{message_id}/seen",
            access_token=access_token,
        )

    async def get_review_reservation(self, access_token: str, reserve_id: str) -> Any:
        return await self._request(
            "GET",
            f"user/review/reservation/{reserve_id}",
            access_token=access_token,
        )

    async def store_review(
        self, access_token: str, *, payload: dict[str, Any]
    ) -> Any:
        return await self._request(
            "POST", "user/review/store", json=payload, access_token=access_token
        )

    async def store_review_comment(
        self, access_token: str, *, payload: dict[str, Any]
    ) -> Any:
        return await self._request(
            "POST", "user/review/comment", json=payload, access_token=access_token
        )

    async def list_my_reviews(self, access_token: str, *, page: int = 1) -> Any:
        return await self._request(
            "GET",
            "user/review/my",
            params={"page": page},
            access_token=access_token,
        )

    # --- guest profile (v0.5) ---

    async def update_user(self, access_token: str, *, payload: dict[str, Any]) -> Any:
        return await self._request("POST", "user", json=payload, access_token=access_token)

    async def list_bookmarks(self, access_token: str, *, page: int = 1, per_page: int = 20) -> Any:
        return await self._request(
            "GET",
            "profile/bookmarks",
            params={"page": page, "perpage": per_page, "with[]": "photos"},
            access_token=access_token,
        )

    async def toggle_bookmark(self, access_token: str, *, house_id: int) -> Any:
        return await self._request(
            "POST",
            "house/bookmark",
            json={"house_id": house_id},
            access_token=access_token,
        )

    async def list_discounts(self, access_token: str) -> Any:
        return await self._request("GET", "user/discount", access_token=access_token)

    # --- host listing (v0.6) ---

    async def store_house(self, access_token: str, *, payload: dict[str, Any]) -> Any:
        return await self._request("POST", "house/store", json=payload, access_token=access_token)

    async def update_house(
        self,
        access_token: str,
        house_id: int,
        *,
        step: str,
        payload: dict[str, Any],
    ) -> Any:
        return await self._request(
            "POST",
            f"house/{house_id}/update",
            params={"step": step},
            json=payload,
            access_token=access_token,
        )

    async def list_my_houses(self, access_token: str, *, page: int = 1) -> Any:
        return await self._request(
            "GET",
            "house/my-houses",
            params={"page": page},
            access_token=access_token,
        )

    async def get_user_house(self, access_token: str, house_id: int) -> Any:
        return await self._request(
            "GET", f"user/house/{house_id}", access_token=access_token
        )

    async def enable_house(self, access_token: str, house_id: int) -> Any:
        return await self._request(
            "POST", f"house/{house_id}/enable", access_token=access_token
        )

    async def delete_or_disable_house(self, access_token: str, house_id: int) -> Any:
        return await self._request(
            "POST", f"house/{house_id}/delete", access_token=access_token
        )
