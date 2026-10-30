from __future__ import annotations

import httpx
import pytest
import respx

from shab_mcp.config import get_settings
from shab_mcp.tools.host_ops import (
    get_host_calendar_impl,
    list_host_reserves_impl,
    update_host_calendar_impl,
)


@pytest.fixture(autouse=True)
def clear_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


TOKEN = "tok"


@respx.mock
@pytest.mark.asyncio
async def test_host_calendar_and_reserves():
    settings = get_settings()
    respx.get(f"{settings.api_prefix}/house/42/host-calendar").mock(
        return_value=httpx.Response(
            200, json={"data": {"days": [{"date": "1403-07-01"}]}, "meta": {"status": 200}}
        )
    )
    cal = respx.post(f"{settings.api_prefix}/house/42/calendar").mock(
        return_value=httpx.Response(
            200, json={"data": {"ok": True}, "meta": {"status": 200}}
        )
    )
    route = respx.get(f"{settings.api_prefix}/reserve").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": {
                    "records": [
                        {
                            "id": "9",
                            "tiny_id": "H1",
                            "house": {"id": 42, "title": "v"},
                            "pricing": {},
                            "status": "pending",
                        }
                    ]
                },
                "meta": {"status": 200},
            },
        )
    )
    c = await get_host_calendar_impl(
        access_token=TOKEN,
        house_id=42,
        from_date="1403-07-01",
        to_date="1403-08-01",
    )
    assert c["calendar"]["days"][0]["date"] == "1403-07-01"
    await update_host_calendar_impl(
        access_token=TOKEN,
        house_id=42,
        payload={"action": "close", "dates": ["1403-07-02"]},
        confirm=True,
    )
    assert cal.called
    reserves = await list_host_reserves_impl(access_token=TOKEN)
    assert route.called
    assert "type=host" in str(route.calls.last.request.url)
    assert reserves["reserves"]
