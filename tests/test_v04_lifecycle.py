from __future__ import annotations

import httpx
import pytest
import respx

from shab_mcp.config import get_settings
from shab_mcp.errors import ShabValidationError
from shab_mcp.tools.lifecycle import (
    cancel_booking_impl,
    change_booking_status_impl,
    get_cancellation_penalty_impl,
    get_chat_thread_impl,
    get_eligible_transitions_impl,
    list_cancellation_reasons_impl,
    send_chat_message_impl,
    submit_review_impl,
)
from shab_mcp.tools.trips import list_trips_impl


@pytest.fixture(autouse=True)
def clear_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


TOKEN = "tok_test"


@respx.mock
@pytest.mark.asyncio
async def test_cancel_flow():
    settings = get_settings()
    respx.get(f"{settings.api_prefix}/reserve/ABC/cancellation-reasons").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": {"records": [{"id": 1, "title": "plans changed"}]},
                "meta": {"status": 200},
            },
        )
    )
    respx.get(f"{settings.api_prefix}/reserve/ABC/cancellation-penalty").mock(
        return_value=httpx.Response(
            200,
            json={"data": {"penalty": 100000, "refund": 500000}, "meta": {"status": 200}},
        )
    )
    cancel_route = respx.post(f"{settings.api_prefix}/reserve/ABC/cancel").mock(
        return_value=httpx.Response(
            200, json={"data": {"ok": True}, "meta": {"status": 200}}
        )
    )
    reasons = await list_cancellation_reasons_impl(access_token=TOKEN, reserve_id="ABC")
    assert reasons["reasons"][0]["id"] == 1
    pen = await get_cancellation_penalty_impl(
        access_token=TOKEN, reserve_id="ABC", reason_id=1
    )
    assert pen["penalty"]["penalty"] == 100000
    with pytest.raises(ShabValidationError):
        await cancel_booking_impl(
            access_token=TOKEN, reserve_id="ABC", reason_id=1, confirm=False
        )
    out = await cancel_booking_impl(
        access_token=TOKEN, reserve_id="ABC", reason_id=1, confirm=True
    )
    assert out["ok"] is True
    assert cancel_route.called


@respx.mock
@pytest.mark.asyncio
async def test_chat_status_review_and_trips_parity():
    settings = get_settings()
    trip_route = respx.get(f"{settings.api_prefix}/reserve").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": {
                    "records": [
                        {
                            "id": "1",
                            "tiny_id": "T1",
                            "house": {"id": 1, "title": "x"},
                            "pricing": {},
                            "status": "paid",
                        }
                    ],
                    "pagination": {"current_page": 1, "total": 1},
                },
                "meta": {"status": 200},
            },
        )
    )
    respx.get(f"{settings.api_prefix}/reserve/T1/chat").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": {"records": [{"id": 9, "text": "hi", "type": "TEXT"}]},
                "meta": {"status": 200},
            },
        )
    )
    send_route = respx.post(f"{settings.api_prefix}/chat").mock(
        return_value=httpx.Response(
            200, json={"data": {"id": 10}, "meta": {"status": 200}}
        )
    )
    respx.get(f"{settings.api_prefix}/reserve/T1/eligible-transitions").mock(
        return_value=httpx.Response(
            200, json={"data": ["ABH", "RBH"], "meta": {"status": 200}}
        )
    )
    status_route = respx.post(f"{settings.api_prefix}/reserve/T1/change-status").mock(
        return_value=httpx.Response(
            200, json={"data": {"ok": True}, "meta": {"status": 200}}
        )
    )
    review_route = respx.post(f"{settings.api_prefix}/user/review/store").mock(
        return_value=httpx.Response(
            200, json={"data": {"ok": True}, "meta": {"status": 200}}
        )
    )

    trips = await list_trips_impl(access_token=TOKEN, page=1)
    assert trip_route.called
    assert "type=guest" in str(trip_route.calls.last.request.url)
    assert trips["trips"]

    thread = await get_chat_thread_impl(access_token=TOKEN, reserve_id="T1")
    assert thread["messages"][0]["text"] == "hi"
    await send_chat_message_impl(
        access_token=TOKEN, reserve_id="T1", text="hello", confirm=True
    )
    assert send_route.called

    elig = await get_eligible_transitions_impl(access_token=TOKEN, reserve_id="T1")
    assert "ABH" in elig["transitions"] or elig["transitions"]
    await change_booking_status_impl(
        access_token=TOKEN, reserve_id="T1", transition="ABH", confirm=True
    )
    assert status_route.called
    assert "transition=ABH" in str(status_route.calls.last.request.url)

    await submit_review_impl(
        access_token=TOKEN, reserve_id="T1", rating=5, comment="great", confirm=True
    )
    assert review_route.called
