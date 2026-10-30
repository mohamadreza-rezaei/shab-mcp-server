from __future__ import annotations

import httpx
import pytest
import respx

from shab_mcp.config import get_settings
from shab_mcp.tools.host_finance import (
    get_host_dashboard_impl,
    get_my_host_profile_impl,
    list_host_payments_impl,
)


@pytest.fixture(autouse=True)
def clear_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


TOKEN = "tok"


@respx.mock
@pytest.mark.asyncio
async def test_host_finance_dashboard():
    settings = get_settings()
    respx.get(f"{settings.api_prefix}/user/host-dashboard/at-a-glance").mock(
        return_value=httpx.Response(
            200, json={"data": {"pending": 2}, "meta": {"status": 200}}
        )
    )
    respx.get(f"{settings.api_prefix}/user/host-dashboard/notices").mock(
        return_value=httpx.Response(
            200, json={"data": [], "meta": {"status": 200}}
        )
    )
    respx.get(f"{settings.api_prefix}/user/host-dashboard/my-performance").mock(
        return_value=httpx.Response(
            200, json={"data": {"score": 90}, "meta": {"status": 200}}
        )
    )
    respx.get(f"{settings.api_prefix}/user/host-profile").mock(
        return_value=httpx.Response(
            200, json={"data": {"bio": "host"}, "meta": {"status": 200}}
        )
    )
    respx.get(f"{settings.api_prefix}/profile/payments").mock(
        return_value=httpx.Response(
            200,
            json={"data": {"records": [{"id": 1, "amount": 1000}]}, "meta": {"status": 200}},
        )
    )
    dash = await get_host_dashboard_impl(access_token=TOKEN)
    assert dash["at_a_glance"]["pending"] == 2
    assert dash["performance"]["score"] == 90
    prof = await get_my_host_profile_impl(access_token=TOKEN)
    assert prof["host_profile"]["bio"] == "host"
    pays = await list_host_payments_impl(access_token=TOKEN)
    assert pays["payments"]["records"][0]["amount"] == 1000
