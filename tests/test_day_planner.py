from day_planner import plan_day

_REQUIRED_KEYS = {
    "day",
    "route_segment",
    "distance_km",
    "elevation_gain_m",
    "estimated_time_hrs",
    "difficulty_rating",
    "risk_notes",
    "gear_reminders",
    "recovery_advice",
}

_BASE_TRIP_PROFILE = {
    "lodging_type": "Refugio/Campsite",
    "pack_weight_preference": "Balanced",
}

_LOW_RISK_SCORES = {
    "Fitness risk": 5,
    "Altitude risk": 5,
    "Weather risk": 5,
    "Logistics risk": 5,
    "Gear risk": 5,
}

_HIGH_RISK_SCORES = {
    "Fitness risk": 16,
    "Altitude risk": 16,
    "Weather risk": 16,
    "Logistics risk": 16,
    "Gear risk": 16,
}


def test_plan_day_returns_all_required_keys():
    result = plan_day(1, "Segment A", 16, 400, "Steady", _BASE_TRIP_PROFILE, _LOW_RISK_SCORES)
    assert _REQUIRED_KEYS.issubset(result.keys())


def test_plan_day_rest_day_returns_zero_distance_and_elevation():
    result = plan_day(3, "Camp", 0, 0, "Steady", _BASE_TRIP_PROFILE, _LOW_RISK_SCORES, is_rest_day=True)
    assert result["distance_km"] == 0
    assert result["elevation_gain_m"] == 0
    assert result["estimated_time_hrs"] == 0


def test_plan_day_rest_day_difficulty_is_rest():
    result = plan_day(2, "Camp", 0, 0, "Steady", _BASE_TRIP_PROFILE, _LOW_RISK_SCORES, is_rest_day=True)
    assert result["difficulty_rating"] == "Rest"


def test_plan_day_rest_day_returns_all_required_keys():
    result = plan_day(2, "Camp", 0, 0, "Steady", _BASE_TRIP_PROFILE, _LOW_RISK_SCORES, is_rest_day=True)
    assert _REQUIRED_KEYS.issubset(result.keys())


def test_plan_day_brisk_pace_takes_less_time_than_leisurely():
    brisk = plan_day(1, "Seg", 20, 400, "Brisk", _BASE_TRIP_PROFILE, _LOW_RISK_SCORES)
    leisurely = plan_day(1, "Seg", 20, 400, "Leisurely", _BASE_TRIP_PROFILE, _LOW_RISK_SCORES)
    assert brisk["estimated_time_hrs"] < leisurely["estimated_time_hrs"]


def test_plan_day_estimated_time_minimum_is_one_hour():
    # Very short segment should not produce sub-1-hour time
    result = plan_day(1, "Seg", 1, 0, "Brisk", _BASE_TRIP_PROFILE, _LOW_RISK_SCORES)
    assert result["estimated_time_hrs"] >= 1.0


def test_plan_day_easy_for_short_flat_segment():
    result = plan_day(1, "Seg", 5, 100, "Steady", _BASE_TRIP_PROFILE, _LOW_RISK_SCORES)
    assert result["difficulty_rating"] == "Easy"


def test_plan_day_hard_for_long_steep_segment():
    result = plan_day(1, "Seg", 30, 1200, "Brisk", _BASE_TRIP_PROFILE, _LOW_RISK_SCORES)
    assert result["difficulty_rating"] == "Hard"


def test_plan_day_risk_notes_contain_fitness_warning_for_high_fitness_risk():
    scores = {**_LOW_RISK_SCORES, "Fitness risk": 15}
    result = plan_day(1, "Seg", 16, 400, "Steady", _BASE_TRIP_PROFILE, scores)
    assert any("endurance" in note.lower() for note in result["risk_notes"])


def test_plan_day_risk_notes_contain_weather_warning_for_high_weather_risk():
    scores = {**_LOW_RISK_SCORES, "Weather risk": 15}
    result = plan_day(1, "Seg", 16, 400, "Steady", _BASE_TRIP_PROFILE, scores)
    assert any("weather" in note.lower() or "wind" in note.lower() for note in result["risk_notes"])


def test_plan_day_default_risk_note_when_all_risks_low():
    result = plan_day(1, "Seg", 16, 400, "Steady", _BASE_TRIP_PROFILE, _LOW_RISK_SCORES)
    assert len(result["risk_notes"]) == 1
    assert "manageable" in result["risk_notes"][0].lower()


def test_plan_day_all_high_risks_produce_multiple_notes():
    result = plan_day(1, "Seg", 16, 400, "Steady", _BASE_TRIP_PROFILE, _HIGH_RISK_SCORES)
    assert len(result["risk_notes"]) > 1


def test_plan_day_recovery_advice_enhanced_for_long_hard_day():
    # Long segment at brisk pace > 7 hrs estimated time
    result = plan_day(1, "Seg", 40, 800, "Brisk", _BASE_TRIP_PROFILE, _LOW_RISK_SCORES)
    assert "foam roll" in result["recovery_advice"].lower() or "protein" in result["recovery_advice"].lower()


def test_plan_day_gear_reminders_include_waterproof_for_high_weather_risk():
    scores = {**_LOW_RISK_SCORES, "Weather risk": 15}
    result = plan_day(1, "Seg", 16, 400, "Steady", _BASE_TRIP_PROFILE, scores)
    assert any("waterproof" in r.lower() for r in result["gear_reminders"])


def test_plan_day_day_index_stored_correctly():
    result = plan_day(4, "Seg", 16, 400, "Steady", _BASE_TRIP_PROFILE, _LOW_RISK_SCORES)
    assert result["day"] == 4


def test_plan_day_segment_name_stored_correctly():
    result = plan_day(1, "Torres Base to Trailhead", 16, 400, "Steady", _BASE_TRIP_PROFILE, _LOW_RISK_SCORES)
    assert result["route_segment"] == "Torres Base to Trailhead"
