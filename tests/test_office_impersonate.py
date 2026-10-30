"""Office impersonation tests. Callers: pytest. User: Implement the plan as specified."""
from __future__ import annotations

import httpx
import pytest
import respx

from shab_mcp.config import get_settings
from shab_mcp.errors import ShabValidationError
from shab_mcp.tools.office_impersonate import (
    office_end_impersonation_impl,
    office_impersonate_user_impl,
)


@pytest.fixture(autouse=True)
def clear_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.mark.asyncio
async def test_impersonate_requires_confirm():
    with pytest.raises(ShabValidationError):
        await office_impersonate_user_impl(staff_token="t", user_id=1, confirm=False)


@respx.mock
@pytest.mark.asyncio
async def test_impersonate_and_end():
    settings = get_settings()
    respx.post(f"{settings.backoffice_prefix}/user/7/easy/login-token").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": {
                    "access_token": "user-tok",
                    "agent_id": 99,
                    "expires_at": "2099-01-01T00:00:00+00:00",
                    "user": {"id": 7, "mobile": "09120000007"},
                },
                "meta": {"status": 200},
            },
        )
    )
    respx.post(f"{settings.api_prefix}/auth/logout").mock(
        return_value=httpx.Response(200, json={"data": {}, "meta": {"status": 200}})
    )
    out = await office_impersonate_user_impl(staff_token="staff", user_id=7, confirm=True)
    assert out["access_token"] == "user-tok"
    end = await office_end_impersonation_impl(access_token="user-tok")
    assert end["ok"] is True
