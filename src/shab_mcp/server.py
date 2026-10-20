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
from shab_mcp.tools.accommodations import get_accommodation_safe, search_accommodations_safe
from shab_mcp.tools.availability import check_availability_safe
from shab_mcp.tools.destinations import search_destinations_safe

INSTRUCTIONS = """\
Official private read-only MCP for Shab (shab.ir), Iran's short-term rental marketplace.

Workflow:
1. search_destinations(query in Persian) to resolve a city/province.
2. search_accommodations(destination, check_in, check_out, guests).
3. get_accommodation(accommodation_id) for details.
4. check_availability(accommodation_id, check_in, check_out, guests) for calendar + price quote.

Rules:
- Dates are Gregorian YYYY-MM-DD. The server converts to Shab Jalali / unix timestamps.
- Prices are Toman.
- Read-only: no login, booking, payment, or cancellation.
- Prefer Persian place names (e.g. رامسر, کیش).
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
async def search_accommodations(
    destination: Annotated[
        str | None,
        Field(description="City name in Persian, e.g. 'رامسر'. Optional if browsing broadly."),
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
) -> dict[str, Any]:
    """Search Shab accommodations. Prices are in Toman."""
    return await search_accommodations_safe(
        destination=destination,
        check_in=check_in,
        check_out=check_out,
        guests=guests,
        page=page,
        per_page=per_page,
        min_price=min_price,
        max_price=max_price,
        accommodation_type=accommodation_type,
        is_instant=is_instant,
    )


@mcp.tool
async def get_accommodation(
    accommodation_id: Annotated[int, Field(description="Numeric Shab house id, e.g. 35729.", ge=1)],
) -> dict[str, Any]:
    """Get normalized details for one Shab accommodation."""
    return await get_accommodation_safe(accommodation_id)


@mcp.tool
async def check_availability(
    accommodation_id: Annotated[int, Field(description="Numeric Shab house id.", ge=1)],
    check_in: Annotated[str, Field(description="Check-in Gregorian YYYY-MM-DD.")],
    check_out: Annotated[str, Field(description="Check-out Gregorian YYYY-MM-DD.")],
    guests: Annotated[int, Field(description="Number of guests.", ge=1, le=100)] = 2,
) -> dict[str, Any]:
    """Check nightly availability and return a read-only price quote (no booking)."""
    return await check_availability_safe(
        accommodation_id=accommodation_id,
        check_in=check_in,
        check_out=check_out,
        guests=guests,
    )


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)
    settings = get_settings()
    transport = (settings.shab_mcp_transport or "http").lower()
    if transport == "stdio":
        mcp.run(transport="stdio")
    else:
        mcp.run(transport="http", host=settings.shab_mcp_host, port=settings.shab_mcp_port)


if __name__ == "__main__":
    main()
