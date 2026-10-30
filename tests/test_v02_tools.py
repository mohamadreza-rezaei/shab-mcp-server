from __future__ import annotations

from datetime import date, timedelta

import httpx
import pytest
import respx

from shab_mcp.config import get_settings
from shab_mcp.tools.accommodations import (
    get_accommodation_photos_impl,
    get_accommodation_reviews_impl,
    list_search_filters_impl,
    search_accommodations_impl,
)
from shab_mcp.tools.auth import (
    normalize_mobile,
    request_login_otp_impl,
    verify_login_otp_impl,
)
from shab_mcp.tools.booking import (
    calculate_invoice_impl,
    create_booking_impl,
    get_payment_link_impl,
)
from shab_mcp.tools.trips import get_booking_host_impl, get_host_profile_impl, list_trips_impl
from shab_mcp.errors import ShabValidationError


@pytest.fixture(autouse=True)
def clear_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def _future_range(nights: int = 3) -> tuple[str, str]:
    start = date.today() + timedelta(days=14)
    end = start + timedelta(days=nights)
    return start.isoformat(), end.isoformat()


def test_normalize_mobile():
    assert normalize_mobile("9121234567") == "09121234567"
    assert normalize_mobile("+989121234567") == "09121234567"


@respx.mock
@pytest.mark.asyncio
async def test_search_with_amenities(fixture_json):
    settings = get_settings()
    route = respx.get(f"{settings.api_prefix}/house/search").mock(
        return_value=httpx.Response(
            200, json={"data": fixture_json("house_search.json"), "meta": {"status": 200}}
        )
    )
    result = await search_accommodations_impl(
        destination="تهران",
        guests=2,
        bedroom_count=2,
        amenities=["elevator", "parking"],
        per_page=5,
    )
    assert route.called
    assert result["bedroom_count"] == 2
    assert result["amenities"] == ["elevator", "parking"]
    req = route.calls.last.request
    assert "features" in str(req.url) or "elevator" in str(req.url)


@respx.mock
@pytest.mark.asyncio
async def test_list_filters_photos_reviews(fixture_json):
    settings = get_settings()
    respx.get(f"{settings.api_prefix}/search/filters").mock(
        return_value=httpx.Response(
            200, json={"data": fixture_json("filters.json"), "meta": {"status": 200}}
        )
    )
    respx.get(f"{settings.api_prefix}/house/35729/photos").mock(
        return_value=httpx.Response(
            200, json={"data": fixture_json("photos.json"), "meta": {"status": 200}}
        )
    )
    respx.get(url__regex=r".*/house/35729/reviews.*").mock(
        return_value=httpx.Response(
            200, json={"data": fixture_json("reviews.json"), "meta": {"status": 200}}
        )
    )
    filters = await list_search_filters_impl()
    assert filters["amenities"][0]["code"] == "elevator"
    photos = await get_accommodation_photos_impl(35729)
    assert photos["count"] == 2
    reviews = await get_accommodation_reviews_impl(35729)
    assert len(reviews["reviews"]) == 2


@respx.mock
@pytest.mark.asyncio
async def test_otp_flow(fixture_json):
    settings = get_settings()
    respx.post(f"{settings.api_prefix}/auth/login-otp").mock(
        return_value=httpx.Response(200, json={"data": {}, "meta": {"status": 200}})
    )
    respx.post(f"{settings.api_prefix}/auth/verify-otp").mock(
        return_value=httpx.Response(
            200, json={"data": fixture_json("otp_verify.json"), "meta": {"status": 200}}
        )
    )
    sent = await request_login_otp_impl(mobile="09121234567")
    assert sent["ok"] is True
    verified = await verify_login_otp_impl(mobile="09121234567", code="12345")
    assert verified["access_token"] == "test-token-abc"


@respx.mock
@pytest.mark.asyncio
async def test_create_booking_requires_confirm():
    with pytest.raises(ShabValidationError):
        await create_booking_impl(
            access_token="tok",
            accommodation_id=1,
            check_in=_future_range()[0],
            check_out=_future_range()[1],
            confirm=False,
        )


@respx.mock
@pytest.mark.asyncio
async def test_booking_and_payment(fixture_json):
    settings = get_settings()
    check_in, check_out = _future_range()
    respx.post(f"{settings.api_prefix}/reserve").mock(
        return_value=httpx.Response(
            201, json={"data": fixture_json("create_reserve.json"), "meta": {"status": 201}}
        )
    )
    respx.post(f"{settings.api_prefix}/invoice/calculate").mock(
        return_value=httpx.Response(
            200, json={"data": fixture_json("invoice_calculate.json"), "meta": {"status": 200}}
        )
    )
    respx.get(url__regex=r".*/payment/gateways.*").mock(
        return_value=httpx.Response(
            200, json={"data": fixture_json("gateways.json"), "meta": {"status": 200}}
        )
    )
    respx.get(url__regex=r".*/invoice/.*/show.*").mock(
        return_value=httpx.Response(
            200, json={"data": fixture_json("invoice_calculate.json"), "meta": {"status": 200}}
        )
    )
    booked = await create_booking_impl(
        access_token="tok",
        accommodation_id=35729,
        check_in=check_in,
        check_out=check_out,
        guests=2,
        confirm=True,
    )
    assert booked["reserve_id"] == "nsPG"
    inv = await calculate_invoice_impl(
        access_token="tok", invoice_id="nfXS", discount_code="SAVE10"
    )
    assert inv["invoice_id"] == "nfXS"
    pay = await get_payment_link_impl(access_token="tok", reserve_id="nsPG", invoice_id="nfXS")
    assert pay["payment_url"].endswith("/order-tracking/nfXS/show")
    assert pay["gateways"][0]["name"] == "ملت"


@respx.mock
@pytest.mark.asyncio
async def test_trips_and_host(fixture_json):
    settings = get_settings()
    respx.get(url__regex=r".*/reserve/trips.*").mock(
        return_value=httpx.Response(
            200, json={"data": fixture_json("trips.json"), "meta": {"status": 200}}
        )
    )
    respx.get(f"{settings.api_prefix}/reserve/nsPG/host").mock(
        return_value=httpx.Response(
            200, json={"data": fixture_json("host_contact.json"), "meta": {"status": 200}}
        )
    )
    respx.get(f"{settings.api_prefix}/profile/host123").mock(
        return_value=httpx.Response(
            200, json={"data": fixture_json("host_profile.json"), "meta": {"status": 200}}
        )
    )
    trips = await list_trips_impl(access_token="tok")
    assert trips["trips"][0]["reserve_id"] == "nsPG"
    host = await get_booking_host_impl(access_token="tok", reserve_id="nsPG")
    assert host["host"]["mobile"] == "09120000000"
    profile = await get_host_profile_impl(user_id="host123")
    assert profile["name"] == "میزبان تست"
