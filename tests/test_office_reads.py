"""Office read tools tests.

Callers: pytest. Affected API: GET user. User: Implement the plan as specified.
"""

from __future__ import annotations

import httpx
import pytest
import respx

from shab_mcp.config import get_settings
from shab_mcp.tools.office_reads import office_get_user_impl, office_search_users_impl


@pytest.fixture(autouse=True)
def clear_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@respx.mock
@pytest.mark.asyncio
async def test_office_search_and_get_user():
    base = get_settings().backoffice_prefix
    respx.get(f"{base}/user").mock(
        return_value=httpx.Response(
            200, json={"data": [{"id": 9}], "meta": {"status": 200}}
        )
    )
    respx.get(f"{base}/user/9").mock(
        return_value=httpx.Response(
            200, json={"data": {"id": 9, "mobile": "09121111111"}, "meta": {"status": 200}}
        )
    )
    search = await office_search_users_impl(staff_token="t", q="0912")
    assert search["ok"] is True
    got = await office_get_user_impl(staff_token="t", user_id=9)
    assert got["user"]["id"] == 9
