from shab_mcp.normalize import (
    normalize_calendar,
    normalize_destinations,
    normalize_house_detail,
    normalize_proforma,
    normalize_search_record,
)


def test_normalize_search_record(fixture_json):
    record = fixture_json("house_search.json")["records"][0]
    out = normalize_search_record(record)
    assert out["id"] == 35729
    assert out["price_per_night"] == 2000000
    assert out["currency"] == "Toman"
    assert out["location"]["city"] == "رامسر"


def test_normalize_house_detail(fixture_json):
    out = normalize_house_detail(fixture_json("house_detail.json"))
    assert out["capacity"]["max"] == 4
    assert "روتختی" in out["amenities"]


def test_normalize_calendar(fixture_json):
    nights = normalize_calendar(fixture_json("calendar.json"))
    assert nights[0]["jalali_date"] == "1405-07-28"
    assert nights[1]["is_bookable"] is False


def test_normalize_proforma(fixture_json):
    out = normalize_proforma(fixture_json("proforma.json"))
    assert out["total_price"] == 7500000


def test_normalize_destinations(fixture_json):
    out = normalize_destinations(fixture_json("suggestions.json"))
    assert out[0]["name"] == "رامسر"
    assert out[0]["search"]["city"] == ["رامسر"]
