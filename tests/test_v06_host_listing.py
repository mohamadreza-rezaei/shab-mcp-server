from __future__ import annotations

import httpx
import pytest
import respx

from shab_mcp.config import get_settings
from shab_mcp.tools.host_listing import (
    create_host_listing_impl,
    list_my_houses_impl,
    update_host_listing_impl,
)


@pytest.fixture(autouse=True)
def clear_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


TOKEN = "tok"


@respx.mock
@pytest.mark.asyncio
async def test_host_listing_wizard():
    settings = get_settings()
    store = respx.post(f"{settings.api_prefix}/house/store").mock(
        return_value=httpx.Response(
            200, json={"data": {"id": 42}, "meta": {"status": 200}}
        )
    )
    upd = respx.post(f"{settings.api_prefix}/house/42/update").mock(
        return_value=httpx.Response(
            200, json={"data": {"ok": True}, "meta": {"status": 200}}
        )
    )
    respx.get(f"{settings.api_prefix}/house/my-houses").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": {"records": [{"id": 42, "title": "My villa"}]},
                "meta": {"status": 200},
            },
        )
    )
    created = await create_host_listing_impl(
        access_token=TOKEN, payload={"type": "villa"}, confirm=True
    )
    assert created["house_id"] == 42
    assert store.called
    await update_host_listing_impl(
        access_token=TOKEN,
        house_id=42,
        step="pricing",
        payload={"base_price": 1000000},
        confirm=True,
    )
    assert upd.called
    assert "step=pricing" in str(upd.calls.last.request.url)
    houses = await list_my_houses_impl(access_token=TOKEN)
    assert houses["houses"][0]["id"] == 42
