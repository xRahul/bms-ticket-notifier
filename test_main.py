import pytest
from main import (
    resolve_region, REGION_MAP, parse_bms_url,
    _cat_status_color, _cat_status_emoji, _cat_status_label,
    filter_shows, ShowInfo, CatInfo
)

def test_resolve_region_known_slug():
    assert resolve_region("chennai") == REGION_MAP["chennai"]
    assert resolve_region("mumbai") == REGION_MAP["mumbai"]

def test_resolve_region_case_and_whitespace():
    assert resolve_region("  CHEnnai  ") == REGION_MAP["chennai"]
    assert resolve_region("MUMBAI") == REGION_MAP["mumbai"]

def test_resolve_region_unknown_slug():
    # Fallback: (key.upper()[:6], key, "0", "0", "")
    assert resolve_region("new-york") == ("NEW-YO", "new-york", "0", "0", "")
    assert resolve_region("p") == ("P", "p", "0", "0", "")

def test_resolve_region_empty_and_none():
    assert resolve_region("") == ("", "", "0", "0", "")
    assert resolve_region(None) == ("", "", "0", "0", "")

def test_resolve_region_long_unknown_slug():
    assert resolve_region("this-is-a-very-long-slug") == ("THIS-I", "this-is-a-very-long-slug", "0", "0", "")

def test_parse_bms_url_valid():
    url = "https://in.bookmyshow.com/movies/chennai/dhurandhar-the-revenge/buytickets/ET00478890"
    res = parse_bms_url(url)
    assert res["event_code"] == "ET00478890"
    assert res["region_slug"] == "chennai"
    assert res["date_code"] is None

def test_parse_bms_url_with_date():
    url = "https://in.bookmyshow.com/movies/chennai/dhurandhar-the-revenge/buytickets/ET00478890/20260318"
    res = parse_bms_url(url)
    assert res["event_code"] == "ET00478890"
    assert res["region_slug"] == "chennai"
    assert res["date_code"] == "20260318"

def test_parse_bms_url_missing_region():
    url = "https://in.bookmyshow.com/event/buytickets/ET00478890"
    res = parse_bms_url(url)
    assert res["event_code"] == "ET00478890"
    assert res["region_slug"] is None

def test_parse_bms_url_invalid():
    url = "https://example.com/some/path"
    res = parse_bms_url(url)
    assert res["event_code"] is None
    assert res["region_slug"] is None
    assert res["date_code"] is None

def test_cat_status_label():
    assert _cat_status_label("0") == "SOLD OUT"
    assert _cat_status_label("1") == "ALMOST FULL"
    assert _cat_status_label("2") == "FILLING FAST"
    assert _cat_status_label("3") == "AVAILABLE"
    assert _cat_status_label("unknown") == "UNKNOWN"

def test_cat_status_emoji():
    assert _cat_status_emoji("0") == "🔴"
    assert _cat_status_emoji("1") == "🟡"
    assert _cat_status_emoji("2") == "🟠"
    assert _cat_status_emoji("3") == "🟢"
    assert _cat_status_emoji("unknown") == ""

def test_cat_status_color():
    assert _cat_status_color("0") == ("#fbebeb", "#d32f2f")
    assert _cat_status_color("1") == ("#fff4e5", "#ed6c02")
    assert _cat_status_color("2") == ("#fff4e5", "#ed6c02")
    assert _cat_status_color("3") == ("#edf7ed", "#2e7d32")
    assert _cat_status_color("unknown") == ("#f5f5f5", "#333333")

@pytest.fixture
def sample_shows():
    return [
        ShowInfo(venue_code="V1", venue_name="PVR Cinemas", session_id="S1", date_code="20260318", time="10:00 AM", time_code="1000", screen_attr="2D"),
        ShowInfo(venue_code="V2", venue_name="INOX Movies", session_id="S2", date_code="20260318", time="01:00 PM", time_code="1300", screen_attr="3D"),
        ShowInfo(venue_code="V1", venue_name="PVR Cinemas", session_id="S3", date_code="20260319", time="06:30 PM", time_code="1830", screen_attr="IMAX"),
        ShowInfo(venue_code="V3", venue_name="Cinepolis", session_id="S4", date_code="20260319", time="09:00 PM", time_code="2100", screen_attr="2D"),
    ]

def test_filter_shows_by_theatre(sample_shows):
    filtered = filter_shows(sample_shows, "PVR", "", "")
    assert len(filtered) == 2
    assert all("PVR" in s.venue_name for s in filtered)

    filtered = filter_shows(sample_shows, "inox,cinepolis", "", "")
    assert len(filtered) == 2
    assert any("INOX" in s.venue_name for s in filtered)
    assert any("Cinepolis" in s.venue_name for s in filtered)

def test_filter_shows_by_date(sample_shows):
    filtered = filter_shows(sample_shows, "", "", "20260318")
    assert len(filtered) == 2
    assert all(s.date_code == "20260318" for s in filtered)

def test_filter_shows_by_time_period(sample_shows):
    filtered = filter_shows(sample_shows, "", "morning", "")
    assert len(filtered) == 1
    assert filtered[0].time_code == "1000"

    filtered = filter_shows(sample_shows, "", "evening,night", "")
    assert len(filtered) == 2
    assert any(s.time_code == "1830" for s in filtered)
    assert any(s.time_code == "2100" for s in filtered)

def test_filter_shows_combined(sample_shows):
    filtered = filter_shows(sample_shows, "PVR", "morning", "20260318")
    assert len(filtered) == 1
    assert filtered[0].venue_name == "PVR Cinemas"
    assert filtered[0].time_code == "1000"

    filtered = filter_shows(sample_shows, "PVR", "night", "20260318")
    assert len(filtered) == 0

def test_filter_shows_no_filters(sample_shows):
    filtered = filter_shows(sample_shows, "", "", "")
    assert len(filtered) == 4
