"""Office auth tests.

Callers: pytest. Affected API: backoffice auth/login bootstrap logout.
User: Implement the plan as specified.
"""

from __future__ import annotations

import httpx
import pytest
import respx

from shab_mcp.config import get_settings
from shab_mcp.errors import ShabValidationError
from shab_mcp.tools.office_auth import (
    office_auth_status_impl,
    office_bootstrap_impl,
    office_login_impl,
    office_logout_impl,
)


@pytest.fixture(autouse=True)
def clear_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@respx.mock
@pytest.mark.asyncio
async def test_office_login_bootstrap_logout():
    settings = get_settings()
    base = settings.backoffice_prefix
    respx.post(f"{base}/auth/login").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": {"access_token": "staff-tok", "id": 1, "mobile": "09120000000"},
                "meta": {"status": 200},
            },
        )
    )
    respx.get(f"{base}/bootstrap").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": {
                    "user_info": {"id": 1, "mobile": "09120000000", "name": "Agent"},
                    "permissions": ["see backoffice panel"],
                },
                "meta": {"status": 200},
            },
        )
    )
    respx.post(f"{base}/auth/logout").mock(
        return_value=httpx.Response(200, json={"data": {}, "meta": {"status": 200}})
    )

    login = await office_login_impl(mobile="9120000000", password="secret")
    assert login["staff_token"] == "staff-tok"

    boot = await office_bootstrap_impl(staff_token="staff-tok")
    assert boot["ok"] is True
    assert boot["user"]["id"] == 1

    status = await office_auth_status_impl(staff_token="staff-tok")
    assert status["authenticated"] is True

    out = await office_logout_impl(staff_token="staff-tok")
    assert out["ok"] is True


@pytest.mark.asyncio
async def test_office_login_requires_password():
    with pytest.raises(ShabValidationError):
        await office_login_impl(mobile="09120000000", password="")
