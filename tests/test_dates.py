from datetime import date

import pytest

from shab_mcp.dates import to_jalali_api, to_unix_day, validate_stay_range
from shab_mcp.errors import ShabValidationError


def test_to_jalali_api_zero_padded():
    assert to_jalali_api(date(2026, 10, 20)) == "1405-07-28"


def test_to_unix_day_utc_midnight():
    assert to_unix_day("2026-10-20") == 1792454400


def test_validate_stay_range_rejects_inverted():
    with pytest.raises(ShabValidationError):
        validate_stay_range("2026-10-25", "2026-10-20")
