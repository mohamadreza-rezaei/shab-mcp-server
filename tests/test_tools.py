from __future__ import annotations

from datetime import date, timedelta

import httpx
import pytest
import respx

from shab_mcp.config import get_settings
from shab_mcp.tools.accommodations import get_accommodation_impl, search_accommodations_impl
from shab_mcp.tools.availability import check_availability_impl
from shab_mcp.tools.destinations import search_destinations_impl


@pytest.fixture(autouse=True)
def clear_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def _future_range(nights: int = 3) -> tuple[str, str]:
    start = date.today() + timedelta(days=14)
    end = start + timedelta(days=nights)
    return start.isoformat(), end.isoformat()


@respx.mock
@pytest.mark.asyncio
async def test_search_accommodations_mocked(fixture_json):
    settings = get_settings()
    route = respx.get(f"{settings.api_prefix}/house/search").mock(
        return_value=httpx.Response(200, json={"data": fixture_json("house_search.json"), "meta": {"status": 200}})
    )
    result = await search_accommodations_impl(destination="رامسر", guests=2, per_page=5)
    assert route.called
    assert result["results"][0]["id"] == 35729


@respx.mock
@pytest.mark.asyncio
async def test_get_accommodation_mocked(fixture_json):
    settings = get_settings()
    respx.get(f"{settings.api_prefix}/house/35729").mock(
        return_value=httpx.Response(200, json={"data": fixture_json("house_detail.json"), "meta": {"status": 200}})
    )
    result = await get_accommodation_impl(35729)
    assert result["title"] == "ویلا تستی رامسر"


@respx.mock
@pytest.mark.asyncio
async def test_check_availability_mocked(fixture_json):
    check_in, check_out = _future_range()
    respx.get(url__regex=r".*/house/35729/calendar.*").mock(
        return_value=httpx.Response(200, json={"data": fixture_json("calendar.json"), "meta": {"status": 200}})
    )
    respx.get(url__regex=r".*/reserve/proforma.*").mock(
        return_value=httpx.Response(200, json={"data": fixture_json("proforma.json"), "meta": {"status": 200}})
    )
    result = await check_availability_impl(
        accommodation_id=35729,
        check_in=check_in,
        check_out=check_out,
        guests=2,
    )
    assert "quote" in result
    assert result["quote"]["total_price"] == 7500000


@respx.mock
@pytest.mark.asyncio
async def test_search_destinations_mocked(fixture_json):
    settings = get_settings()
    respx.get(f"{settings.api_prefix}/house/suggestions").mock(
        return_value=httpx.Response(200, json=fixture_json("suggestions.json"))
    )
    respx.get(f"{settings.api_prefix}/region/suggestions").mock(
        return_value=httpx.Response(200, json=[{"name": "رامسر", "type": "city", "province_name": "مازندران"}])
    )
    result = await search_destinations_impl("رامسر")
    assert result["destinations"][0]["name"] == "رامسر"


@pytest.mark.live
@pytest.mark.asyncio
async def test_live_search_ramsar():
    result = await search_accommodations_impl(destination="رامسر", guests=2, per_page=2)
    assert result["total"] is None or result["total"] >= 0
    assert isinstance(result["results"], list)
