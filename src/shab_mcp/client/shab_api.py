from __future__ import annotations

import logging
from typing import Any

import httpx

from shab_mcp import __version__
from shab_mcp.config import Settings, get_settings
from shab_mcp.errors import (
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
    """Async HTTP client for Shab sandbox v1.4 public read endpoints."""

    def __init__(
        self,
        settings: Settings | None = None,
        *,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self._client = client
        self._owns_client = client is None

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

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | list[tuple[str, Any]] | None = None,
    ) -> Any:
        url = self._url(path)
        attempts = self.settings.shab_max_retries + 1
        last_exc: Exception | None = None

        for attempt in range(attempts):
            try:
                response = await self.client.request(method, url, params=params)
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

    async def search_houses(self, params: list[tuple[str, Any]]) -> Any:
        return await self._request("GET", "house/search", params=params)

    async def get_house(self, house_id: int) -> Any:
        return await self._request("GET", f"house/{house_id}")

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
    ) -> Any:
        return await self._request(
            "GET",
            "reserve/proforma",
            params={
                "house_id": house_id,
                "checkin": checkin,
                "checkout": checkout,
                "guests_count": guests_count,
            },
        )

    async def house_suggestions(self, phrase: str) -> Any:
        return await self._request("GET", "house/suggestions", params={"phrase": phrase})

    async def region_suggestions(self, phrase: str) -> Any:
        return await self._request("GET", "region/suggestions", params={"phrase": phrase})
