from __future__ import annotations

import httpx
import pytest
import respx

from shab_mcp.config import get_settings
from shab_mcp.tools.profile import (
    get_user_profile_impl,
    list_bookmarks_impl,
    list_discounts_impl,
    toggle_bookmark_impl,
    update_user_profile_impl,
)


@pytest.fixture(autouse=True)
def clear_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


TOKEN = "tok"


@respx.mock
@pytest.mark.asyncio
async def test_profile_bookmarks_discounts():
    settings = get_settings()
    respx.get(f"{settings.api_prefix}/user").mock(
        return_value=httpx.Response(
            200, json={"data": {"id": 1, "name": "Ali"}, "meta": {"status": 200}}
        )
    )
    respx.post(f"{settings.api_prefix}/user").mock(
        return_value=httpx.Response(
            200, json={"data": {"id": 1, "email": "a@b.c"}, "meta": {"status": 200}}
        )
    )
    respx.get(f"{settings.api_prefix}/profile/bookmarks").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": {
                    "records": [
                        {"id": 9, "title": "villa", "pricing": {"price_after_discount": 1}}
                    ]
                },
                "meta": {"status": 200},
            },
        )
    )
    bm = respx.post(f"{settings.api_prefix}/house/bookmark").mock(
        return_value=httpx.Response(
            200, json={"data": {"bookmarked": True}, "meta": {"status": 200}}
        )
    )
    respx.get(f"{settings.api_prefix}/user/discount").mock(
        return_value=httpx.Response(
            200,
            json={"data": {"records": [{"code": "SAVE10"}]}, "meta": {"status": 200}},
        )
    )
    u = await get_user_profile_impl(access_token=TOKEN)
    assert u["user"]["name"] == "Ali"
    upd = await update_user_profile_impl(
        access_token=TOKEN, email="a@b.c", confirm=True
    )
    assert upd["ok"]
    b = await list_bookmarks_impl(access_token=TOKEN)
    assert b["bookmarks"][0]["id"] == 9
    await toggle_bookmark_impl(access_token=TOKEN, accommodation_id=9, confirm=True)
    assert bm.called
    d = await list_discounts_impl(access_token=TOKEN)
    assert d["discounts"][0]["code"] == "SAVE10"
