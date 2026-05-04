import pytest
from main import resolve_region, REGION_MAP, detect_changes, parse_bms_url

def test_parse_bms_url_full():
    url = "https://in.bookmyshow.com/movies/chennai/dhurandhar-the-revenge/buytickets/ET00478890/20231015"
    result = parse_bms_url(url)
    assert result == {"event_code": "ET00478890", "date_code": "20231015", "region_slug": "chennai"}

def test_parse_bms_url_without_date():
    url = "https://in.bookmyshow.com/movies/mumbai/some-movie/buytickets/ET12345678"
    result = parse_bms_url(url)
    assert result == {"event_code": "ET12345678", "date_code": None, "region_slug": "mumbai"}

def test_parse_bms_url_missing_movies():
    url = "https://in.bookmyshow.com/plays/delhi/some-play/ET87654321"
    result = parse_bms_url(url)
    assert result == {"event_code": "ET87654321", "date_code": None, "region_slug": None}

def test_parse_bms_url_movies_at_end():
    url = "https://in.bookmyshow.com/some/path/movies"
    result = parse_bms_url(url)
    assert result == {"event_code": None, "date_code": None, "region_slug": None}

def test_parse_bms_url_empty():
    url = ""
    result = parse_bms_url(url)
    assert result == {"event_code": None, "date_code": None, "region_slug": None}

def test_parse_bms_url_malformed():
    url = "not-a-valid-url"
    result = parse_bms_url(url)
    assert result == {"event_code": None, "date_code": None, "region_slug": None}

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

def test_detect_changes_no_change():
    state = {
        "dates": {"20240101": "BOOKABLE"},
        "shows": {"show1": {"venue": "V1", "time": "10:00", "date": "20240101", "cat": "VIP", "price": "100", "status": "3"}}
    }
    assert detect_changes(state, state) == []

def test_detect_changes_new_date_opened():
    old_state = {"dates": {"20240101": "NOT_OPEN", "20240102": "NOT_OPEN"}}
    new_state = {"dates": {"20240101": "BOOKABLE", "20240102": "AVAILABLE"}}

    changes = detect_changes(old_state, new_state)
    assert len(changes) == 2
    assert "📅 NEW DATE OPENED: 20240101" in changes
    assert "📅 NEW DATE OPENED: 20240102" in changes

def test_detect_changes_new_showtime():
    old_state = {"shows": {}}
    new_state = {
        "shows": {
            "show1": {"venue": "V1", "time": "10:00 AM", "date": "20240101", "cat": "VIP", "price": "1000", "status": "3"}
        }
    }
    changes = detect_changes(old_state, new_state)
    assert changes == ["🆕 NEW: V1 10:00 AM [20240101] — VIP ₹1000"]

def test_detect_changes_sold_out_to_available():
    old_state = {
        "shows": {
            "show1": {"venue": "V1", "time": "10:00 AM", "date": "20240101", "cat": "VIP", "price": "1000", "status": "0"}
        }
    }
    new_state = {
        "shows": {
            "show1": {"venue": "V1", "time": "10:00 AM", "date": "20240101", "cat": "VIP", "price": "1000", "status": "3"}
        }
    }
    changes = detect_changes(old_state, new_state)
    assert changes == ["🟢 BACK: V1 10:00 AM [20240101] — VIP → AVAILABLE"]

    # Also test unknown status mapping
    new_state_unknown = {
        "shows": {
            "show1": {"venue": "V1", "time": "10:00 AM", "date": "20240101", "cat": "VIP", "price": "1000", "status": "99"}
        }
    }
    changes = detect_changes(old_state, new_state_unknown)
    assert changes == ["⚪ BACK: V1 10:00 AM [20240101] — VIP → UNKNOWN"]

def test_detect_changes_multiple_changes():
    old_state = {
        "dates": {"20240101": "NOT_OPEN"},
        "shows": {
            "show1": {"venue": "V1", "time": "10:00 AM", "date": "20240101", "cat": "VIP", "price": "1000", "status": "0"}
        }
    }
    new_state = {
        "dates": {"20240101": "BOOKABLE"},
        "shows": {
            "show1": {"venue": "V1", "time": "10:00 AM", "date": "20240101", "cat": "VIP", "price": "1000", "status": "3"},
            "show2": {"venue": "V2", "time": "12:00 PM", "date": "20240101", "cat": "Gen", "price": "500", "status": "3"}
        }
    }
    changes = detect_changes(old_state, new_state)

    assert len(changes) == 3
    assert "📅 NEW DATE OPENED: 20240101" in changes
    assert "🆕 NEW: V2 12:00 PM [20240101] — Gen ₹500" in changes
    assert "🟢 BACK: V1 10:00 AM [20240101] — VIP → AVAILABLE" in changes
