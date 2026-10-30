from __future__ import annotations

import httpx
import pytest
import respx

from shab_mcp.config import get_settings
from shab_mcp.tools.accommodations import (
    count_accommodations_impl,
    get_landing_tehran_impl,
    get_similar_accommodations_impl,
    list_neighbourhoods_impl,
    search_accommodations_impl,
)


@pytest.fixture(autouse=True)
def clear_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@respx.mock
@pytest.mark.asyncio
async def test_search_bbox_params(fixture_json):
    settings = get_settings()
    route = respx.get(f"{settings.api_prefix}/house/search").mock(
        return_value=httpx.Response(
            200, json={"data": fixture_json("house_search.json"), "meta": {"status": 200}}
        )
    )
    result = await search_accommodations_impl(
        destination="تهران",
        guests=2,
        min_latitude=35.6,
        max_latitude=35.8,
        min_longitude=51.3,
        max_longitude=51.5,
        per_page=5,
    )
    assert route.called
    url = str(route.calls.last.request.url)
    assert "co_ordinates" in url
    assert result["bbox"]["min_latitude"] == 35.6


@respx.mock
@pytest.mark.asyncio
async def test_neighbourhoods_similar_count_landing():
    settings = get_settings()
    respx.get(f"{settings.api_prefix}/house/neighbourhoods").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": {"records": [{"id": 1, "name": "پونک", "city": "تهران"}]},
                "meta": {"status": 200},
            },
        )
    )
    respx.get(f"{settings.api_prefix}/house/35729/similar").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": {
                    "records": [
                        {
                            "id": 1,
                            "title": "x",
                            "pricing": {"price_after_discount": 1000},
                            "location": {},
                            "cover_photo": {},
                            "rates": {},
                        }
                    ]
                },
                "meta": {"status": 200},
            },
        )
    )
    respx.get(f"{settings.api_prefix}/house/count").mock(
        return_value=httpx.Response(
            200, json={"data": {"count": 42}, "meta": {"status": 200}}
        )
    )
    respx.get(f"{settings.api_prefix}/landing/tehran").mock(
        return_value=httpx.Response(
            200, json={"data": {"title": "تهران", "filters": {}}, "meta": {"status": 200}}
        )
    )
    n = await list_neighbourhoods_impl(city="تهران")
    assert n["neighbourhoods"][0]["name"] == "پونک"
    s = await get_similar_accommodations_impl(35729)
    assert s["results"][0]["id"] == 1
    c = await count_accommodations_impl(destination="تهران", guests=2)
    assert c["count"] == 42
    land = await get_landing_tehran_impl()
    assert land["title"] == "تهران"
