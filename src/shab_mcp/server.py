"""FastMCP entrypoint for Shab MCP (stdio or Streamable HTTP)."""

from __future__ import annotations

import logging
from typing import Annotated, Any

from fastmcp import FastMCP
from pydantic import Field
from starlette.requests import Request
from starlette.responses import JSONResponse

from shab_mcp import __version__
from shab_mcp.config import get_settings
from shab_mcp.tools.accommodations import (
    count_accommodations_safe,
    get_accommodation_photos_safe,
    get_accommodation_reviews_safe,
    get_accommodation_safe,
    get_landing_tehran_safe,
    get_similar_accommodations_safe,
    list_neighbourhoods_safe,
    list_search_filters_safe,
    search_accommodations_safe,
)
from shab_mcp.tools.auth import (
    get_auth_status_safe,
    logout_safe,
    request_login_otp_safe,
    verify_login_otp_safe,
)
from shab_mcp.tools.availability import check_availability_safe
from shab_mcp.tools.booking import (
    calculate_invoice_safe,
    create_booking_safe,
    get_payment_link_safe,
)
from shab_mcp.tools.destinations import search_destinations_safe
from shab_mcp.tools.trips import (
    get_booking_host_safe,
    get_booking_safe,
    get_host_profile_safe,
    list_trips_safe,
)
from shab_mcp.tools.lifecycle import (
    cancel_booking_safe,
    change_booking_status_safe,
    comment_on_review_safe,
    get_cancellation_penalty_safe,
    get_chat_thread_safe,
    get_eligible_transitions_safe,
    get_review_for_reservation_safe,
    list_cancellation_reasons_safe,
    list_chats_safe,
    list_my_reviews_safe,
    mark_chat_seen_safe,
    send_chat_message_safe,
    submit_review_safe,
)

INSTRUCTIONS = """\
Official private MCP for Shab (shab.ir), Iran's short-term rental marketplace.

Discovery workflow:
1. search_destinations(query in Persian) to resolve a city/province.
2. list_search_filters() for amenity codes (elevator, parking, …).
3. search_accommodations(destination, dates, guests, amenities, bbox lat/lng, …).
   For map areas use min/max_latitude/longitude; for nearby use user_latitude/longitude + from_map_nearby.
   list_neighbourhoods(city), count_accommodations(...), get_similar_accommodations(id), get_landing_tehran().
4. get_accommodation / get_accommodation_photos / get_accommodation_reviews.
   For visual requirements (e.g. courtyard), fetch photos and judge with vision; also try amenity feature codes.
5. check_availability(accommodation_id, dates, guests, optional discount_code).

Booking workflow (authenticated):
6. request_login_otp(mobile) → ask user for SMS code.
7. verify_login_otp(mobile, code) → receive access_token (treat as secret).
8. create_booking(..., confirm=true, access_token=…).
9. calculate_invoice(invoice_id, discount_code?, access_token).
10. get_payment_link → give user payment_url; they pay in browser (no card in MCP).
11. list_trips / get_booking / get_booking_host for status and host phone.

Rules:
- Dates are Gregorian YYYY-MM-DD. The server converts to Shab Jalali / unix timestamps.
- Prices are Toman.
- Prefer Persian place names (e.g. رامسر, تهران).
Guest lifecycle: cancel_booking, chat REST, submit_review, change_booking_status (confirm=true).
- Never invent an access_token; never complete bank/IPG card payment inside tools.
"""

mcp = FastMCP(
    "shab-mcp",
    instructions=INSTRUCTIONS,
    version=__version__,
)


@mcp.custom_route("/health", methods=["GET"])
async def health_check(_request: Request) -> JSONResponse:
    return JSONResponse({"status": "healthy", "service": "shab-mcp", "version": __version__})


@mcp.tool
async def search_destinations(
    query: Annotated[
        str,
        Field(description="Persian place name: city, province, or area, e.g. 'رامسر'."),
    ],
) -> dict[str, Any]:
    """Resolve a place name into Shab destinations usable by search_accommodations."""
    return await search_destinations_safe(query)


@mcp.tool
async def list_search_filters() -> dict[str, Any]:
    """List amenity/feature filter codes for search_accommodations(amenities=[...])."""
    return await list_search_filters_safe()


@mcp.tool
async def search_accommodations(
    destination: Annotated[
        str | None,
        Field(description="City name in Persian, e.g. 'تهران'. Optional if browsing broadly."),
    ] = None,
    province: Annotated[
        str | None,
        Field(description="Province name in Persian, e.g. 'تهران'."),
    ] = None,
    check_in: Annotated[
        str | None,
        Field(description="Check-in Gregorian YYYY-MM-DD, e.g. '2026-10-25'."),
    ] = None,
    check_out: Annotated[
        str | None,
        Field(description="Check-out Gregorian YYYY-MM-DD, e.g. '2026-10-27'."),
    ] = None,
    guests: Annotated[int, Field(description="Number of guests (count children).", ge=1, le=100)] = 2,
    page: Annotated[int, Field(description="Result page (1-based).", ge=1)] = 1,
    per_page: Annotated[int, Field(description="Results per page (max 24).", ge=1, le=24)] = 10,
    min_price: Annotated[
        int | None,
        Field(description="Minimum nightly price in Toman (optional)."),
    ] = None,
    max_price: Annotated[
        int | None,
        Field(description="Maximum nightly price in Toman (optional)."),
    ] = None,
    accommodation_type: Annotated[
        str | None,
        Field(description="Optional type filter, e.g. villa, apartment, boomgardi."),
    ] = None,
    is_instant: Annotated[
        bool | None,
        Field(description="If true, only instant-book listings."),
    ] = None,
    bedroom_count: Annotated[
        int | None,
        Field(description="Minimum bedroom count filter.", ge=0),
    ] = None,
    bed_count: Annotated[
        int | None,
        Field(description="Minimum bed count filter.", ge=0),
    ] = None,
    amenities: Annotated[
        list[str] | None,
        Field(description="Amenity feature codes from list_search_filters, e.g. ['elevator','parking']."),
    ] = None,
    sort_by: Annotated[
        str | None,
        Field(description="Optional sort: price_asc, price_desc, or rating."),
    ] = None,
    min_latitude: Annotated[
        float | None,
        Field(description="Map bbox south (with max_latitude and longitudes)."),
    ] = None,
    max_latitude: Annotated[
        float | None,
        Field(description="Map bbox north."),
    ] = None,
    min_longitude: Annotated[
        float | None,
        Field(description="Map bbox west."),
    ] = None,
    max_longitude: Annotated[
        float | None,
        Field(description="Map bbox east."),
    ] = None,
    user_latitude: Annotated[
        float | None,
        Field(description="User location latitude for nearby search."),
    ] = None,
    user_longitude: Annotated[
        float | None,
        Field(description="User location longitude for nearby search."),
    ] = None,
    from_map_nearby: Annotated[
        bool | None,
        Field(description="If true, search near user_latitude/longitude (map nearby mode)."),
    ] = None,
    place_id: Annotated[
        str | None,
        Field(description="Optional place_id from destination suggestions."),
    ] = None,
) -> dict[str, Any]:
    """Search Shab accommodations. Prices are in Toman. Supports map bbox and nearby."""
    return await search_accommodations_safe(
        destination=destination,
        province=province,
        check_in=check_in,
        check_out=check_out,
        guests=guests,
        page=page,
        per_page=per_page,
        min_price=min_price,
        max_price=max_price,
        accommodation_type=accommodation_type,
        is_instant=is_instant,
        bedroom_count=bedroom_count,
        bed_count=bed_count,
        amenities=amenities,
        sort_by=sort_by,
        min_latitude=min_latitude,
        max_latitude=max_latitude,
        min_longitude=min_longitude,
        max_longitude=max_longitude,
        user_latitude=user_latitude,
        user_longitude=user_longitude,
        from_map_nearby=from_map_nearby,
        place_id=place_id,
    )


@mcp.tool
async def get_accommodation(
    accommodation_id: Annotated[int, Field(description="Numeric Shab house id, e.g. 35729.", ge=1)],
) -> dict[str, Any]:
    """Get normalized details for one Shab accommodation."""
    return await get_accommodation_safe(accommodation_id)


@mcp.tool
async def get_accommodation_photos(
    accommodation_id: Annotated[int, Field(description="Numeric Shab house id.", ge=1)],
) -> dict[str, Any]:
    """List photo URLs for an accommodation (for agent/user review)."""
    return await get_accommodation_photos_safe(accommodation_id)


@mcp.tool
async def get_accommodation_reviews(
    accommodation_id: Annotated[int, Field(description="Numeric Shab house id.", ge=1)],
    page: Annotated[int, Field(description="Reviews page (1-based).", ge=1)] = 1,
) -> dict[str, Any]:
    """Fetch guest reviews for an accommodation."""
    return await get_accommodation_reviews_safe(accommodation_id, page=page)


@mcp.tool
async def list_neighbourhoods(
    city: Annotated[
        str | None,
        Field(description="City name in Persian to list neighbourhoods, e.g. 'تهران'."),
    ] = None,
) -> dict[str, Any]:
    """List neighbourhoods for map/area search."""
    return await list_neighbourhoods_safe(city=city)


@mcp.tool
async def get_similar_accommodations(
    accommodation_id: Annotated[int, Field(description="Numeric Shab house id.", ge=1)],
) -> dict[str, Any]:
    """List similar accommodations for a house."""
    return await get_similar_accommodations_safe(accommodation_id)


@mcp.tool
async def count_accommodations(
    destination: Annotated[str | None, Field(description="City name in Persian.")] = None,
    province: Annotated[str | None, Field(description="Province name in Persian.")] = None,
    guests: Annotated[int, Field(description="Number of guests.", ge=1, le=100)] = 2,
    amenities: Annotated[list[str] | None, Field(description="Amenity feature codes.")] = None,
    bedroom_count: Annotated[int | None, Field(description="Minimum bedrooms.", ge=0)] = None,
    is_instant: Annotated[bool | None, Field(description="Instant-only filter.")] = None,
    min_latitude: Annotated[float | None, Field(description="Bbox south.")] = None,
    max_latitude: Annotated[float | None, Field(description="Bbox north.")] = None,
    min_longitude: Annotated[float | None, Field(description="Bbox west.")] = None,
    max_longitude: Annotated[float | None, Field(description="Bbox east.")] = None,
) -> dict[str, Any]:
    """Count accommodations matching filters (no full result list)."""
    return await count_accommodations_safe(
        destination=destination,
        province=province,
        guests=guests,
        amenities=amenities,
        bedroom_count=bedroom_count,
        is_instant=is_instant,
        min_latitude=min_latitude,
        max_latitude=max_latitude,
        min_longitude=min_longitude,
        max_longitude=max_longitude,
    )


@mcp.tool
async def get_landing_tehran() -> dict[str, Any]:
    """Tehran landing preset (categories/filters used on the home/Tehran page)."""
    return await get_landing_tehran_safe()


@mcp.tool
async def check_availability(
    accommodation_id: Annotated[int, Field(description="Numeric Shab house id.", ge=1)],
    check_in: Annotated[str, Field(description="Check-in Gregorian YYYY-MM-DD.")],
    check_out: Annotated[str, Field(description="Check-out Gregorian YYYY-MM-DD.")],
    guests: Annotated[int, Field(description="Number of guests.", ge=1, le=100)] = 2,
    discount_code: Annotated[
        str | None,
        Field(description="Optional discount code for the price quote."),
    ] = None,
) -> dict[str, Any]:
    """Check nightly availability and return a price quote (no booking)."""
    return await check_availability_safe(
        accommodation_id=accommodation_id,
        check_in=check_in,
        check_out=check_out,
        guests=guests,
        discount_code=discount_code,
    )


@mcp.tool
async def request_login_otp(
    mobile: Annotated[
        str,
        Field(description="Iranian mobile, e.g. 09121234567."),
    ],
) -> dict[str, Any]:
    """Send a Shab login OTP SMS to the user."""
    return await request_login_otp_safe(mobile=mobile)


@mcp.tool
async def verify_login_otp(
    mobile: Annotated[str, Field(description="Same mobile used in request_login_otp.")],
    code: Annotated[str, Field(description="SMS OTP code from the user.")],
) -> dict[str, Any]:
    """Verify OTP and return access_token for booking/trip tools."""
    return await verify_login_otp_safe(mobile=mobile, code=code)


@mcp.tool
async def get_auth_status(
    access_token: Annotated[str, Field(description="Bearer token from verify_login_otp.")],
) -> dict[str, Any]:
    """Check whether access_token is still valid and return user summary."""
    return await get_auth_status_safe(access_token=access_token)


@mcp.tool
async def logout(
    access_token: Annotated[str, Field(description="Bearer token to revoke.")],
) -> dict[str, Any]:
    """Revoke the Shab access_token."""
    return await logout_safe(access_token=access_token)


@mcp.tool
async def create_booking(
    access_token: Annotated[str, Field(description="Bearer token from verify_login_otp.")],
    accommodation_id: Annotated[int, Field(description="House id to book.", ge=1)],
    check_in: Annotated[str, Field(description="Check-in Gregorian YYYY-MM-DD.")],
    check_out: Annotated[str, Field(description="Check-out Gregorian YYYY-MM-DD.")],
    guests: Annotated[int, Field(description="Number of guests.", ge=1, le=100)] = 2,
    confirm: Annotated[
        bool,
        Field(description="Must be true after the user explicitly confirms the booking."),
    ] = False,
) -> dict[str, Any]:
    """Create a reservation request or instant booking. Requires confirm=true."""
    return await create_booking_safe(
        access_token=access_token,
        accommodation_id=accommodation_id,
        check_in=check_in,
        check_out=check_out,
        guests=guests,
        confirm=confirm,
    )


@mcp.tool
async def calculate_invoice(
    access_token: Annotated[str, Field(description="Bearer token from verify_login_otp.")],
    invoice_id: Annotated[str, Field(description="Invoice id from create_booking.")],
    discount_code: Annotated[
        str | None,
        Field(description="Optional discount/promo code."),
    ] = None,
    use_credit: Annotated[bool, Field(description="Apply wallet credit if available.")] = False,
    prepay_total_fee: Annotated[
        bool,
        Field(description="If true, attempt full prepay when allowed."),
    ] = False,
) -> dict[str, Any]:
    """Apply discount/credit to an invoice before payment."""
    return await calculate_invoice_safe(
        access_token=access_token,
        invoice_id=invoice_id,
        discount_code=discount_code,
        use_credit=use_credit,
        prepay_total_fee=prepay_total_fee,
    )


@mcp.tool
async def get_payment_link(
    access_token: Annotated[str, Field(description="Bearer token from verify_login_otp.")],
    reserve_id: Annotated[str, Field(description="Reservation id from create_booking.")],
    invoice_id: Annotated[str, Field(description="Invoice id from create_booking.")],
) -> dict[str, Any]:
    """Return a Shab payment URL for the user to complete card payment in a browser."""
    return await get_payment_link_safe(
        access_token=access_token,
        reserve_id=reserve_id,
        invoice_id=invoice_id,
    )


@mcp.tool
async def list_trips(
    access_token: Annotated[str, Field(description="Bearer token from verify_login_otp.")],
    page: Annotated[int, Field(description="Page number.", ge=1)] = 1,
) -> dict[str, Any]:
    """List the authenticated user's trips/bookings."""
    return await list_trips_safe(access_token=access_token, page=page)


@mcp.tool
async def get_booking(
    access_token: Annotated[str, Field(description="Bearer token from verify_login_otp.")],
    reserve_id: Annotated[str, Field(description="Reservation tiny id.")],
) -> dict[str, Any]:
    """Get details/status for one booking."""
    return await get_booking_safe(access_token=access_token, reserve_id=reserve_id)


@mcp.tool
async def get_booking_host(
    access_token: Annotated[str, Field(description="Bearer token from verify_login_otp.")],
    reserve_id: Annotated[str, Field(description="Reservation tiny id.")],
) -> dict[str, Any]:
    """Get host contact info for a booking (when the reservation allows it)."""
    return await get_booking_host_safe(access_token=access_token, reserve_id=reserve_id)


@mcp.tool
async def get_host_profile(
    user_id: Annotated[str, Field(description="Public host uid from listing/host data.")],
) -> dict[str, Any]:
    """Get a public host profile (no auth required)."""
    return await get_host_profile_safe(user_id=user_id)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)
    settings = get_settings()
    transport = (settings.shab_mcp_transport or "http").lower()
    if transport == "stdio":
        mcp.run(transport="stdio")
    else:
        mcp.run(transport="http", host=settings.shab_mcp_host, port=settings.shab_mcp_port)




@mcp.tool
async def list_cancellation_reasons(
    access_token: Annotated[str, Field(description="Bearer token from verify_login_otp.")],
    reserve_id: Annotated[str, Field(description="Reservation tiny id.")],
) -> dict[str, Any]:
    """List cancellation reasons for a booking."""
    return await list_cancellation_reasons_safe(access_token=access_token, reserve_id=reserve_id)


@mcp.tool
async def get_cancellation_penalty(
    access_token: Annotated[str, Field(description="Bearer token from verify_login_otp.")],
    reserve_id: Annotated[str, Field(description="Reservation tiny id.")],
    reason_id: Annotated[int, Field(description="Cancellation reason id.", ge=1)],
) -> dict[str, Any]:
    """Preview cancellation penalty before cancel_booking."""
    return await get_cancellation_penalty_safe(
        access_token=access_token, reserve_id=reserve_id, reason_id=reason_id
    )


@mcp.tool
async def cancel_booking(
    access_token: Annotated[str, Field(description="Bearer token from verify_login_otp.")],
    reserve_id: Annotated[str, Field(description="Reservation tiny id.")],
    reason_id: Annotated[int, Field(description="Cancellation reason id.", ge=1)],
    description: Annotated[str | None, Field(description="Optional guest note.")] = None,
    confirm: Annotated[bool, Field(description="Must be true after penalty preview.")] = False,
) -> dict[str, Any]:
    """Cancel a booking. Requires confirm=true."""
    return await cancel_booking_safe(
        access_token=access_token,
        reserve_id=reserve_id,
        reason_id=reason_id,
        description=description,
        confirm=confirm,
    )


@mcp.tool
async def get_eligible_transitions(
    access_token: Annotated[str, Field(description="Bearer token from verify_login_otp.")],
    reserve_id: Annotated[str, Field(description="Reservation id.")],
) -> dict[str, Any]:
    """List eligible status transitions for a reservation."""
    return await get_eligible_transitions_safe(access_token=access_token, reserve_id=reserve_id)


@mcp.tool
async def change_booking_status(
    access_token: Annotated[str, Field(description="Bearer token from verify_login_otp.")],
    reserve_id: Annotated[str, Field(description="Reservation id.")],
    transition: Annotated[
        str,
        Field(description="Transition code, e.g. ABH (accept), RBH (reject by host), RBG."),
    ],
    confirm: Annotated[bool, Field(description="Must be true.")] = False,
) -> dict[str, Any]:
    """Apply a reservation status transition. Requires confirm=true."""
    return await change_booking_status_safe(
        access_token=access_token,
        reserve_id=reserve_id,
        transition=transition,
        confirm=confirm,
    )


@mcp.tool
async def list_chats(
    access_token: Annotated[str, Field(description="Bearer token from verify_login_otp.")],
    page: Annotated[int, Field(description="Page (1-based).", ge=1)] = 1,
) -> dict[str, Any]:
    """List chat conversations (REST)."""
    return await list_chats_safe(access_token=access_token, page=page)


@mcp.tool
async def get_chat_thread(
    access_token: Annotated[str, Field(description="Bearer token from verify_login_otp.")],
    reserve_id: Annotated[str, Field(description="Reservation id for the chat thread.")],
    page: Annotated[int, Field(description="Messages page.", ge=1)] = 1,
) -> dict[str, Any]:
    """Fetch chat messages for a reservation (poll; no Pusher)."""
    return await get_chat_thread_safe(
        access_token=access_token, reserve_id=reserve_id, page=page
    )


@mcp.tool
async def send_chat_message(
    access_token: Annotated[str, Field(description="Bearer token from verify_login_otp.")],
    reserve_id: Annotated[str, Field(description="Reservation id.")],
    text: Annotated[str, Field(description="Message text.")],
    confirm: Annotated[bool, Field(description="Must be true.")] = False,
) -> dict[str, Any]:
    """Send a TEXT chat message. Requires confirm=true."""
    return await send_chat_message_safe(
        access_token=access_token, reserve_id=reserve_id, text=text, confirm=confirm
    )


@mcp.tool
async def mark_chat_seen(
    access_token: Annotated[str, Field(description="Bearer token from verify_login_otp.")],
    reserve_id: Annotated[str, Field(description="Reservation id.")],
    message_id: Annotated[str, Field(description="Message id to mark seen.")],
) -> dict[str, Any]:
    """Mark a chat message as seen."""
    return await mark_chat_seen_safe(
        access_token=access_token, reserve_id=reserve_id, message_id=message_id
    )


@mcp.tool
async def get_review_for_reservation(
    access_token: Annotated[str, Field(description="Bearer token from verify_login_otp.")],
    reserve_id: Annotated[str, Field(description="Reservation id.")],
) -> dict[str, Any]:
    """Get review form/detail for a reservation."""
    return await get_review_for_reservation_safe(
        access_token=access_token, reserve_id=reserve_id
    )


@mcp.tool
async def submit_review(
    access_token: Annotated[str, Field(description="Bearer token from verify_login_otp.")],
    reserve_id: Annotated[str, Field(description="Reservation id.")],
    rating: Annotated[int | None, Field(description="Optional overall rating 1-5.", ge=1, le=5)] = None,
    comment: Annotated[str | None, Field(description="Optional review text.")] = None,
    confirm: Annotated[bool, Field(description="Must be true.")] = False,
) -> dict[str, Any]:
    """Submit a guest review for a stay. Requires confirm=true."""
    return await submit_review_safe(
        access_token=access_token,
        reserve_id=reserve_id,
        rating=rating,
        comment=comment,
        confirm=confirm,
    )


@mcp.tool
async def comment_on_review(
    access_token: Annotated[str, Field(description="Bearer token from verify_login_otp.")],
    review_id: Annotated[int, Field(description="Review id to comment on.", ge=1)],
    comment: Annotated[str, Field(description="Comment text.")],
    confirm: Annotated[bool, Field(description="Must be true.")] = False,
) -> dict[str, Any]:
    """Reply/comment on a review. Requires confirm=true."""
    return await comment_on_review_safe(
        access_token=access_token,
        payload={"review_id": review_id, "comment": comment},
        confirm=confirm,
    )


@mcp.tool
async def list_my_reviews(
    access_token: Annotated[str, Field(description="Bearer token from verify_login_otp.")],
    page: Annotated[int, Field(description="Page (1-based).", ge=1)] = 1,
) -> dict[str, Any]:
    """List reviews written by the current user."""
    return await list_my_reviews_safe(access_token=access_token, page=page)


if __name__ == "__main__":
    main()
