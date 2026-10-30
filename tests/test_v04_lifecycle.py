from __future__ import annotations

import httpx
import pytest
import respx

from shab_mcp.config import get_settings
from shab_mcp.errors import ShabValidationError
from shab_mcp.tools.lifecycle import (
    cancel_booking_impl,
    change_booking_status_impl,
    comment_on_review_impl,
    get_cancellation_penalty_impl,
    get_chat_thread_impl,
    get_eligible_transitions_impl,
    list_cancellation_reasons_impl,
    list_chats_impl,
    reject_booking_impl,
    send_chat_message_impl,
    submit_review_impl,
)
from shab_mcp.tools.trips import list_trips_impl


@pytest.fixture(autouse=True)
def clear_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@respx.mock
@pytest.mark.asyncio
async def test_list_trips_uses_guest_reserve_parity():
    settings = get_settings()
    route = respx.get(f"{settings.api_prefix}/reserve").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": {
                    "records": [
                        {
                            "id": "abc",
                            "house": {"id": 1, "title": "x"},
                            "checkin": "1403-01-01",
                            "checkout": "1403-01-03",
                            "last_state": "paid",
                        }
                    ],
                    "pagination": {"current_page": 1, "total": 1},
                },
                "meta": {"status": 200},
            },
        )
    )
    result = await list_trips_impl(access_token="tok", page=1)
    assert route.called
    url = str(route.calls.last.request.url)
    assert "type=guest" in url
    assert "new=1" in url
    assert result["trips"]


@respx.mock
@pytest.mark.asyncio
async def test_cancel_flow_requires_confirm():
    settings = get_settings()
    respx.get(f"{settings.api_prefix}/reserve/rid1/cancellation-reasons").mock(
        return_value=httpx.Response(
            200,
            json={"data": {"records": [{"id": 7, "title": "change of plans"}]}, "meta": {"status": 200}},
        )
    )
    respx.get(url__regex=r".*/cancellation-penalty.*").mock(
        return_value=httpx.Response(
            200, json={"data": {"penalty": 100000}, "meta": {"status": 200}}
        )
    )
    cancel_route = respx.post(f"{settings.api_prefix}/reserve/rid1/cancel").mock(
        return_value=httpx.Response(200, json={"data": {"ok": True}, "meta": {"status": 200}})
    )
    reasons = await list_cancellation_reasons_impl(access_token="tok", reserve_id="rid1")
    assert reasons["reasons"]
    penalty = await get_cancellation_penalty_impl(
        access_token="tok", reserve_id="rid1", reason_id=7
    )
    assert penalty["penalty"]["penalty"] == 100000
    with pytest.raises(ShabValidationError):
        await cancel_booking_impl(access_token="tok", reserve_id="rid1", reason_id=7)
    out = await cancel_booking_impl(
        access_token="tok", reserve_id="rid1", reason_id=7, confirm=True
    )
    assert out["ok"] is True
    assert cancel_route.called


@respx.mock
@pytest.mark.asyncio
async def test_chat_and_transitions_and_review():
    settings = get_settings()
    respx.get(f"{settings.api_prefix}/chat").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": {"records": [{"reservation_id": "r1", "title": "t"}]},
                "meta": {"status": 200},
            },
        )
    )
    respx.get(f"{settings.api_prefix}/reserve/r1/chat").mock(
        return_value=httpx.Response(
            200,
            json={"data": {"records": [{"id": "m1", "text": "hi"}]}, "meta": {"status": 200}},
        )
    )
    send = respx.post(f"{settings.api_prefix}/chat").mock(
        return_value=httpx.Response(
            201, json={"data": {"message_id": "m2"}, "meta": {"status": 201}}
        )
    )
    respx.get(f"{settings.api_prefix}/reserve/r1/eligible-transitions").mock(
        return_value=httpx.Response(
            200, json={"data": [{"transition": "ABH"}], "meta": {"status": 200}}
        )
    )
    change = respx.post(f"{settings.api_prefix}/reserve/r1/change-status").mock(
        return_value=httpx.Response(200, json={"data": {}, "meta": {"status": 200}})
    )
    reject = respx.post(f"{settings.api_prefix}/reserve/reject").mock(
        return_value=httpx.Response(200, json={"data": {}, "meta": {"status": 200}})
    )
    review = respx.post(f"{settings.api_prefix}/user/review/store").mock(
        return_value=httpx.Response(200, json={"data": {"step": 1}, "meta": {"status": 200}})
    )
    comment = respx.post(f"{settings.api_prefix}/user/review/comment").mock(
        return_value=httpx.Response(200, json={"data": {}, "meta": {"status": 200}})
    )

    chats = await list_chats_impl(access_token="tok")
    assert chats["chats"]
    thread = await get_chat_thread_impl(access_token="tok", reserve_id="r1")
    assert thread["messages"]
    await send_chat_message_impl(access_token="tok", reserve_id="r1", text="سلام", confirm=True)
    assert send.called
    body = send.calls.last.request.content.decode()
    assert "TEXT" in body

    tr = await get_eligible_transitions_impl(access_token="tok", reserve_id="r1")
    assert tr["transitions"]
    await change_booking_status_impl(
        access_token="tok", reserve_id="r1", transition="ABH", confirm=True
    )
    assert change.called
    change_body = change.calls.last.request.content.decode()
    assert "ABH" in change_body or "transition" in change_body

    await reject_booking_impl(access_token="tok", reserve_id="r1", confirm=True)
    assert reject.called

    await submit_review_impl(
        access_token="tok",
        reserve_id="r1",
        step=1,
        host=5,
        value=5,
        accuracy=5,
        cleanliness=5,
        accessibility=5,
        confirm=True,
    )
    assert review.called
    await comment_on_review_impl(
        access_token="tok", review_id="rev1", comment="thanks", confirm=True
    )
    assert comment.called
