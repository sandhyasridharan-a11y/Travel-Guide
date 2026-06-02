from assumption_engine import propose_trip_profile


def _hard_route():
    return {
        "difficulty": "Hard",
        "duration_days": 5,
        "recommended_fitness_level": "Advanced",
        "region": "Patagonia, Chile",
        "best_season": "October to April",
    }


def _easy_route():
    return {
        "difficulty": "Easy",
        "duration_days": 3,
        "recommended_fitness_level": "Beginner",
        "region": "Coastal Trail, Oregon",
        "best_season": "June to September",
    }


def test_propose_trip_profile_returns_all_required_keys():
    profile = propose_trip_profile(_hard_route())
    expected_keys = {
        "number_of_days",
        "lodging_type",
        "hiking_pace",
        "rest_days",
        "guided_vs_self_guided",
        "pack_weight_preference",
        "season",
    }
    assert set(profile.keys()) == expected_keys


def test_propose_trip_profile_hard_route_sets_steady_pace():
    profile = propose_trip_profile(_hard_route())
    assert profile["hiking_pace"] == "Steady"


def test_propose_trip_profile_easy_route_sets_leisurely_pace():
    profile = propose_trip_profile(_easy_route())
    assert profile["hiking_pace"] == "Leisurely"


def test_propose_trip_profile_hard_route_sets_light_pack():
    profile = propose_trip_profile(_hard_route())
    assert profile["pack_weight_preference"] == "Light"


def test_propose_trip_profile_easy_route_sets_balanced_pack():
    profile = propose_trip_profile(_easy_route())
    assert profile["pack_weight_preference"] == "Balanced"


def test_propose_trip_profile_long_trip_gets_rest_day():
    route = _hard_route()
    route["duration_days"] = 5
    profile = propose_trip_profile(route)
    assert profile["rest_days"] == 1


def test_propose_trip_profile_short_trip_no_rest_day():
    route = _easy_route()
    route["duration_days"] = 4
    profile = propose_trip_profile(route)
    assert profile["rest_days"] == 0


def test_propose_trip_profile_advanced_fitness_is_self_guided():
    profile = propose_trip_profile(_hard_route())
    assert profile["guided_vs_self_guided"] == "Self-guided"


def test_propose_trip_profile_beginner_fitness_is_guided():
    profile = propose_trip_profile(_easy_route())
    assert profile["guided_vs_self_guided"] == "Guided"


def test_propose_trip_profile_patagonia_region_sets_refugio_lodging():
    route = _hard_route()
    route["difficulty"] = "Easy"  # Override difficulty to isolate region logic
    profile = propose_trip_profile(route)
    assert profile["lodging_type"] == "Refugio/Campsite"


def test_propose_trip_profile_non_patagonia_easy_route_sets_campsite():
    profile = propose_trip_profile(_easy_route())
    assert profile["lodging_type"] == "Campsite"


def test_propose_trip_profile_number_of_days_matches_route_duration():
    route = _hard_route()
    route["duration_days"] = 7
    profile = propose_trip_profile(route)
    assert profile["number_of_days"] == 7


def test_propose_trip_profile_season_taken_from_best_season():
    profile = propose_trip_profile(_hard_route())
    assert profile["season"] == "October to April"


def test_propose_trip_profile_season_defaults_to_summer_when_missing():
    route = _easy_route()
    del route["best_season"]
    profile = propose_trip_profile(route)
    assert profile["season"] == "Summer"
