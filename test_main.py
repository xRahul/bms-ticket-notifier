import pytest
from main import resolve_region, REGION_MAP, filter_shows, ShowInfo

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

# ──────────────────────────────────────────────────────────────────────
# filter_shows TESTS
# ──────────────────────────────────────────────────────────────────────
@pytest.fixture
def sample_shows():
    return [
        ShowInfo(
            venue_code="V1", venue_name="PVR: Phoenix Marketcity", session_id="1",
            date_code="20240101", time="10:00 AM", time_code="1000", screen_attr="IMAX"
        ),
        ShowInfo(
            venue_code="V2", venue_name="INOX: Lido Mall", session_id="2",
            date_code="20240101", time="01:00 PM", time_code="1300", screen_attr="3D"
        ),
        ShowInfo(
            venue_code="V3", venue_name="Cinepolis: Nexus Shantiniketan", session_id="3",
            date_code="20240102", time="06:00 PM", time_code="1800", screen_attr="2D"
        ),
        ShowInfo(
            venue_code="V4", venue_name="PVR: VR Mall", session_id="4",
            date_code="20240102", time="10:00 PM", time_code="2200", screen_attr="4DX"
        ),
        ShowInfo(
            venue_code="V5", venue_name="Single Screen Theatre", session_id="5",
            date_code="20240103", time="Invalid Time", time_code="invalid", screen_attr="2D"
        )
    ]

def test_filter_shows_no_filters(sample_shows):
    filtered = filter_shows(sample_shows, "", "", "")
    assert len(filtered) == 5

def test_filter_shows_theatre_filter(sample_shows):
    filtered = filter_shows(sample_shows, "PVR", "", "")
    assert len(filtered) == 2
    assert all("pvr" in s.venue_name.lower() for s in filtered)

    filtered_multiple = filter_shows(sample_shows, "PVR, INOX", "", "")
    assert len(filtered_multiple) == 3

def test_filter_shows_date_filter(sample_shows):
    filtered = filter_shows(sample_shows, "", "", "20240101")
    assert len(filtered) == 2
    assert all(s.date_code == "20240101" for s in filtered)

    filtered_multiple = filter_shows(sample_shows, "", "", "20240101, 20240103")
    assert len(filtered_multiple) == 3

def test_filter_shows_time_period_filter(sample_shows):
    filtered_morning = filter_shows(sample_shows, "", "morning", "")
    assert len(filtered_morning) == 1
    assert filtered_morning[0].venue_name == "PVR: Phoenix Marketcity"

    filtered_afternoon = filter_shows(sample_shows, "", "afternoon", "")
    assert len(filtered_afternoon) == 1
    assert filtered_afternoon[0].venue_name == "INOX: Lido Mall"

    filtered_evening = filter_shows(sample_shows, "", "evening", "")
    assert len(filtered_evening) == 1
    assert filtered_evening[0].venue_name == "Cinepolis: Nexus Shantiniketan"

    filtered_night = filter_shows(sample_shows, "", "night", "")
    assert len(filtered_night) == 1
    assert filtered_night[0].venue_name == "PVR: VR Mall"

    filtered_multiple = filter_shows(sample_shows, "", "morning, night", "")
    assert len(filtered_multiple) == 2

def test_filter_shows_invalid_time_code_handling(sample_shows):
    # The last show has invalid time_code. It should default to 0 and not match morning/afternoon/evening/night.
    filtered = filter_shows(sample_shows, "", "morning, afternoon, evening, night", "")
    # Should match all valid times, but skip 'invalid'
    assert len(filtered) == 4
    assert not any(s.time_code == "invalid" for s in filtered)

def test_filter_shows_combined_filters(sample_shows):
    # Theatre "PVR", morning time
    filtered = filter_shows(sample_shows, "pvr", "morning", "")
    assert len(filtered) == 1
    assert filtered[0].venue_name == "PVR: Phoenix Marketcity"

    # Theatre "PVR", specific date
    filtered = filter_shows(sample_shows, "pvr", "", "20240102")
    assert len(filtered) == 1
    assert filtered[0].venue_name == "PVR: VR Mall"
