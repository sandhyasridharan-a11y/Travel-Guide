from route_library import ROUTES
from itinerary_generator import (
    generate_itinerary,
    summarize_itinerary,
    _estimate_daily_profile,
    _determine_rest_day_indices,
    _choose_segments,
)

_ROUTE = ROUTES[0]  # Patagonia W Trek

_TRIP_PROFILE = {
    "number_of_days": 5,
    "rest_days": 1,
    "lodging_type": "Refugio/Campsite",
    "hiking_pace": "Steady",
    "pack_weight_preference": "Light",
    "guided_vs_self_guided": "Self-guided",
}

_RISK_SCORES = {
    "Fitness risk": 8,
    "Altitude risk": 6,
    "Weather risk": 8,
    "Logistics risk": 10,
    "Gear risk": 7,
}


# --- _estimate_daily_profile ---

def test_estimate_daily_profile_number_of_days():
    result = _estimate_daily_profile(_ROUTE, _TRIP_PROFILE)
    assert result["total_days"] == 5


def test_estimate_daily_profile_moving_days_excludes_rest():
    result = _estimate_daily_profile(_ROUTE, _TRIP_PROFILE)
    assert result["moving_days"] == 4  # 5 days - 1 rest day


def test_estimate_daily_profile_daily_distance_distributed():
    result = _estimate_daily_profile(_ROUTE, _TRIP_PROFILE)
    expected = _ROUTE["distance_km"] / result["moving_days"]
    assert abs(result["daily_distance"] - expected) < 0.01


def test_estimate_daily_profile_daily_elevation_distributed():
    result = _estimate_daily_profile(_ROUTE, _TRIP_PROFILE)
    expected = _ROUTE["elevation_gain_m"] / result["moving_days"]
    assert abs(result["daily_elevation"] - expected) < 0.01


def test_estimate_daily_profile_no_rest_days():
    profile = {**_TRIP_PROFILE, "rest_days": 0, "number_of_days": 5}
    result = _estimate_daily_profile(_ROUTE, profile)
    assert result["moving_days"] == 5
    assert result["rest_days"] == 0


def test_estimate_daily_profile_moving_days_at_least_one():
    # All days are rest days — should clamp to 1 moving day
    profile = {**_TRIP_PROFILE, "number_of_days": 1, "rest_days": 5}
    result = _estimate_daily_profile(_ROUTE, profile)
    assert result["moving_days"] >= 1


# --- _determine_rest_day_indices ---

def test_determine_rest_day_indices_returns_empty_for_zero_rest():
    assert _determine_rest_day_indices(5, 0) == []


def test_determine_rest_day_indices_places_one_rest_near_midpoint():
    indices = _determine_rest_day_indices(5, 1)
    assert len(indices) == 1
    # Midpoint of 5-day trip is day 3; index should be at or near middle
    assert 2 <= indices[0] <= 4


def test_determine_rest_day_indices_two_rest_days_are_consecutive_after_midpoint():
    indices = _determine_rest_day_indices(6, 2)
    assert len(indices) == 2
    assert indices[1] == indices[0] + 1


def test_determine_rest_day_indices_does_not_exceed_total_days():
    indices = _determine_rest_day_indices(5, 3)
    assert all(i <= 5 for i in indices)


# --- _choose_segments ---

def test_choose_segments_patagonia_route_returns_named_segments():
    segments = _choose_segments("Patagonia W Trek", 3)
    assert len(segments) == 3
    assert "Pudeto" in segments[0]


def test_choose_segments_unknown_route_returns_generic_segments():
    segments = _choose_segments("Unknown Trail", 4)
    assert len(segments) == 4
    assert all("Segment" in s for s in segments)


def test_choose_segments_caps_at_available_patagonia_segments():
    # Only 5 named Patagonia segments exist; requesting more returns all 5
    segments = _choose_segments("Patagonia W Trek", 10)
    assert len(segments) == 5


# --- generate_itinerary ---

def test_generate_itinerary_length_equals_total_days():
    itinerary = generate_itinerary(_ROUTE, _TRIP_PROFILE, _RISK_SCORES)
    assert len(itinerary) == _TRIP_PROFILE["number_of_days"]


def test_generate_itinerary_rest_days_have_zero_distance():
    itinerary = generate_itinerary(_ROUTE, _TRIP_PROFILE, _RISK_SCORES)
    rest_days = [d for d in itinerary if d["distance_km"] == 0]
    assert len(rest_days) == _TRIP_PROFILE["rest_days"]


def test_generate_itinerary_day_indices_are_sequential():
    itinerary = generate_itinerary(_ROUTE, _TRIP_PROFILE, _RISK_SCORES)
    assert [d["day"] for d in itinerary] == list(range(1, len(itinerary) + 1))


def test_generate_itinerary_no_rest_days():
    profile = {**_TRIP_PROFILE, "rest_days": 0}
    itinerary = generate_itinerary(_ROUTE, profile, _RISK_SCORES)
    assert all(d["distance_km"] > 0 for d in itinerary)


def test_generate_itinerary_patagonia_segment_names_used():
    profile = {**_TRIP_PROFILE, "rest_days": 0, "number_of_days": 5}
    itinerary = generate_itinerary(_ROUTE, profile, _RISK_SCORES)
    moving_segments = [d["route_segment"] for d in itinerary]
    assert any("Pudeto" in s for s in moving_segments)


# --- summarize_itinerary ---

def test_summarize_itinerary_returns_correct_length():
    itinerary = generate_itinerary(_ROUTE, _TRIP_PROFILE, _RISK_SCORES)
    summary = summarize_itinerary(itinerary)
    assert len(summary) == len(itinerary)


def test_summarize_itinerary_contains_required_fields():
    itinerary = generate_itinerary(_ROUTE, _TRIP_PROFILE, _RISK_SCORES)
    summary = summarize_itinerary(itinerary)
    expected_keys = {"day", "route_segment", "distance_km", "elevation_gain_m", "estimated_time_hrs"}
    for entry in summary:
        assert expected_keys.issubset(entry.keys())


def test_summarize_itinerary_excludes_risk_notes_and_gear_reminders():
    itinerary = generate_itinerary(_ROUTE, _TRIP_PROFILE, _RISK_SCORES)
    summary = summarize_itinerary(itinerary)
    for entry in summary:
        assert "risk_notes" not in entry
        assert "gear_reminders" not in entry
