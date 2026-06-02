from route_library import ROUTES
from scoring_model import (
    adjust_gear_risk_for_warnings,
    apply_guided_adjustments,
    overall_readiness_score,
    score_fitness_risk,
    score_altitude_risk,
    score_weather_risk,
    score_logistics_risk,
    score_gear_risk,
    score_trip_risks,
    top_risk_drivers,
    _GEAR_RISK_NO_WARNING_REDUCTION,
    _GUIDED_FITNESS_REDUCTION,
    _GUIDED_GEAR_REDUCTION,
)


def test_score_trip_risks_happy_path():
    route = ROUTES[0]
    trip_profile = {
        "season": "October",
        "lodging_type": "Refugio/Campsite",
        "guided_vs_self_guided": "Self-guided",
        "pack_weight_preference": "Balanced",
        "number_of_days": 5,
        "hiking_pace": "Moderate",
        "rest_days": 1,
    }

    risk_scores = score_trip_risks(route, trip_profile, "Intermediate", "Mixed")

    assert set(risk_scores.keys()) == {
        "Fitness risk",
        "Altitude risk",
        "Weather risk",
        "Logistics risk",
        "Gear risk",
    }
    assert all(0 <= score <= 20 for score in risk_scores.values())

    readiness = overall_readiness_score(risk_scores)
    assert 0 <= readiness <= 100

    drivers = top_risk_drivers(risk_scores, count=3)
    assert len(drivers) == 3
    assert drivers[0][1] >= drivers[1][1]
    assert drivers[1][1] >= drivers[2][1]


# --- Individual scoring functions ---

def test_score_fitness_risk_advanced_lower_than_beginner():
    route = ROUTES[0]
    assert score_fitness_risk(route, "Advanced") < score_fitness_risk(route, "Beginner")


def test_score_fitness_risk_uses_daily_distance_not_total():
    route = {"distance_km": 80, "elevation_gain_m": 400}
    short_trip = {"number_of_days": 2, "rest_days": 0}   # 40 km/day
    long_trip = {"number_of_days": 10, "rest_days": 0}   # 8 km/day
    assert score_fitness_risk(route, "Intermediate", short_trip) > score_fitness_risk(route, "Intermediate", long_trip)


def test_score_fitness_risk_rest_days_increase_daily_load():
    route = {"distance_km": 40, "elevation_gain_m": 400}
    no_rest = {"number_of_days": 4, "rest_days": 0}    # 10 km/day
    with_rest = {"number_of_days": 4, "rest_days": 2}  # 20 km/day (2 moving days)
    assert score_fitness_risk(route, "Intermediate", with_rest) > score_fitness_risk(route, "Intermediate", no_rest)


def test_score_fitness_risk_result_clamped_to_zero_minimum():
    short_flat_route = {"distance_km": 10, "elevation_gain_m": 100}
    score = score_fitness_risk(short_flat_route, "Advanced")
    assert score >= 0


def test_score_fitness_risk_result_clamped_to_20_maximum():
    huge_route = {"distance_km": 500, "elevation_gain_m": 5000}
    score = score_fitness_risk(huge_route, "Beginner")
    assert score <= 20


def test_score_altitude_risk_increases_with_elevation():
    low_route = {"max_elevation_m": 500}
    high_route = {"max_elevation_m": 3000}
    assert score_altitude_risk(high_route, "Intermediate") > score_altitude_risk(low_route, "Intermediate")


def test_score_altitude_risk_advanced_lower_than_beginner():
    route = {"max_elevation_m": 2000}
    assert score_altitude_risk(route, "Advanced") < score_altitude_risk(route, "Beginner")


def test_score_altitude_risk_zero_for_routes_below_800m():
    low_route = {"max_elevation_m": 600}
    assert score_altitude_risk(low_route, "Advanced") == 0  # 0 base, experience modifier clamped


def test_score_altitude_risk_nonzero_for_moderate_elevation():
    mid_route = {"max_elevation_m": 1200}
    assert score_altitude_risk(mid_route, "Intermediate") > 0


def test_score_weather_risk_unstable_higher_than_stable():
    route = ROUTES[0]
    assert score_weather_risk(route, "Unstable") > score_weather_risk(route, "Stable")


def test_score_weather_risk_cold_climate_higher_than_temperate():
    cold_route = {"climate": "Cold/Mountain", "region": "Test Range"}
    temperate_route = {"climate": "Temperate", "region": "Test Range"}
    assert score_weather_risk(cold_route, "Stable") > score_weather_risk(temperate_route, "Stable")


def test_score_weather_risk_alpine_region_adds_bonus():
    alpine_route = {"climate": "Temperate", "region": "Alpine Zone, Switzerland"}
    plain_route = {"climate": "Temperate", "region": "Coastal Trail, Oregon"}
    assert score_weather_risk(alpine_route, "Stable") > score_weather_risk(plain_route, "Stable")


def test_score_weather_risk_tropical_higher_than_temperate():
    tropical_route = {"climate": "Tropical", "region": "Amazon Basin"}
    temperate_route = {"climate": "Temperate", "region": "Rolling Hills"}
    assert score_weather_risk(tropical_route, "Stable") > score_weather_risk(temperate_route, "Stable")


def test_score_logistics_risk_hotel_lower_than_campsite():
    route = {"remoteness": "Low", "permit_required": False, "transport_complexity": "Low"}
    hotel_profile = {"lodging_type": "Hotel", "guided_vs_self_guided": "Guided"}
    campsite_profile = {"lodging_type": "Campsite", "guided_vs_self_guided": "Guided"}
    assert score_logistics_risk(route, hotel_profile) < score_logistics_risk(route, campsite_profile)


def test_score_logistics_risk_hotel_lowest_among_lodging_tiers():
    route = {"remoteness": "Low", "permit_required": False, "transport_complexity": "Low"}
    guided = "Guided"
    lodging_scores = {
        lodging: score_logistics_risk(route, {"lodging_type": lodging, "guided_vs_self_guided": guided})
        for lodging in ["Hotel", "Backcountry hut", "Refugio/Campsite", "Mixed camping/refugio", "Campsite"]
    }
    assert lodging_scores["Hotel"] == min(lodging_scores.values())
    assert lodging_scores["Campsite"] == max(lodging_scores.values())


def test_score_logistics_risk_remote_with_permit_higher_than_local():
    remote_route = {"remoteness": "High", "permit_required": True, "transport_complexity": "High"}
    local_route = {"remoteness": "Low", "permit_required": False, "transport_complexity": "Low"}
    profile = {"lodging_type": "Backcountry hut", "guided_vs_self_guided": "Guided"}
    assert score_logistics_risk(remote_route, profile) > score_logistics_risk(local_route, profile)


def test_score_gear_risk_minimal_pack_higher_than_balanced():
    route = ROUTES[0]
    minimal_profile = {"lodging_type": "Campsite", "pack_weight_preference": "Minimal"}
    balanced_profile = {"lodging_type": "Campsite", "pack_weight_preference": "Balanced"}
    assert score_gear_risk(route, minimal_profile, "Stable") > score_gear_risk(route, balanced_profile, "Stable")


def test_score_gear_risk_unstable_weather_increases_score():
    route = ROUTES[0]
    profile = {"lodging_type": "Campsite", "pack_weight_preference": "Balanced"}
    assert score_gear_risk(route, profile, "Unstable") > score_gear_risk(route, profile, "Stable")


def test_score_gear_risk_hotel_lower_than_campsite():
    route = ROUTES[0]
    hotel_profile = {"lodging_type": "Hotel", "pack_weight_preference": "Balanced"}
    campsite_profile = {"lodging_type": "Campsite", "pack_weight_preference": "Balanced"}
    assert score_gear_risk(route, hotel_profile, "Stable") < score_gear_risk(route, campsite_profile, "Stable")


def test_score_gear_risk_hotel_lowest_lodging_tier():
    route = ROUTES[0]
    lodging_scores = {
        lodging: score_gear_risk(route, {"lodging_type": lodging, "pack_weight_preference": "Balanced"}, "Stable")
        for lodging in ["Hotel", "Backcountry hut", "Refugio/Campsite", "Mixed camping/refugio", "Campsite"]
    }
    assert lodging_scores["Hotel"] == min(lodging_scores.values())
    assert lodging_scores["Campsite"] == max(lodging_scores.values())


# --- apply_guided_adjustments ---

def test_apply_guided_adjustments_reduces_fitness_and_gear_for_guided():
    scores = {"Fitness risk": 10, "Altitude risk": 4, "Weather risk": 6, "Logistics risk": 12, "Gear risk": 8}
    guided_profile = {"guided_vs_self_guided": "Guided"}
    adjusted = apply_guided_adjustments(scores, guided_profile)
    assert adjusted["Fitness risk"] == 10 - _GUIDED_FITNESS_REDUCTION
    assert adjusted["Gear risk"] == 8 - _GUIDED_GEAR_REDUCTION


def test_apply_guided_adjustments_no_change_for_self_guided():
    scores = {"Fitness risk": 10, "Altitude risk": 4, "Weather risk": 6, "Logistics risk": 12, "Gear risk": 8}
    self_guided_profile = {"guided_vs_self_guided": "Self-guided"}
    adjusted = apply_guided_adjustments(scores, self_guided_profile)
    assert adjusted["Fitness risk"] == 10
    assert adjusted["Gear risk"] == 8


def test_apply_guided_adjustments_does_not_go_below_zero():
    scores = {"Fitness risk": 1, "Altitude risk": 0, "Weather risk": 0, "Logistics risk": 0, "Gear risk": 0}
    guided_profile = {"guided_vs_self_guided": "Guided"}
    adjusted = apply_guided_adjustments(scores, guided_profile)
    assert adjusted["Fitness risk"] == 0
    assert adjusted["Gear risk"] == 0


def test_apply_guided_adjustments_does_not_modify_other_dimensions():
    scores = {"Fitness risk": 10, "Altitude risk": 4, "Weather risk": 6, "Logistics risk": 12, "Gear risk": 8}
    guided_profile = {"guided_vs_self_guided": "Guided"}
    adjusted = apply_guided_adjustments(scores, guided_profile)
    for dim in ["Altitude risk", "Weather risk", "Logistics risk"]:
        assert adjusted[dim] == scores[dim]


def test_apply_guided_adjustments_does_not_mutate_input():
    scores = {"Fitness risk": 10, "Altitude risk": 4, "Weather risk": 6, "Logistics risk": 12, "Gear risk": 8}
    original_fitness = scores["Fitness risk"]
    apply_guided_adjustments(scores, {"guided_vs_self_guided": "Guided"})
    assert scores["Fitness risk"] == original_fitness


def test_apply_guided_adjustments_guided_readiness_higher_than_self_guided():
    route = ROUTES[0]
    trip_profile_base = {
        "number_of_days": 5, "rest_days": 1,
        "lodging_type": "Refugio/Campsite", "pack_weight_preference": "Balanced",
        "season": "October to April",
    }
    guided_profile = {**trip_profile_base, "guided_vs_self_guided": "Guided"}
    self_guided_profile = {**trip_profile_base, "guided_vs_self_guided": "Self-guided"}

    guided_scores = apply_guided_adjustments(
        score_trip_risks(route, guided_profile, "Beginner", "Unstable"), guided_profile
    )
    self_guided_scores = apply_guided_adjustments(
        score_trip_risks(route, self_guided_profile, "Beginner", "Unstable"), self_guided_profile
    )
    assert overall_readiness_score(guided_scores) > overall_readiness_score(self_guided_scores)


def test_top_risk_drivers_returns_sorted_descending():
    scores = {"A": 10, "B": 18, "C": 5, "D": 15}
    drivers = top_risk_drivers(scores, count=3)
    values = [v for _, v in drivers]
    assert values == sorted(values, reverse=True)


def test_top_risk_drivers_returns_requested_count():
    scores = {"A": 10, "B": 18, "C": 5, "D": 15, "E": 8}
    assert len(top_risk_drivers(scores, count=2)) == 2


# --- adjust_gear_risk_for_warnings ---

def test_adjust_gear_risk_reduces_by_constant_when_no_warnings():
    scores = {"Fitness risk": 8, "Altitude risk": 4, "Weather risk": 6, "Logistics risk": 10, "Gear risk": 9}
    adjusted = adjust_gear_risk_for_warnings(scores, packing_warnings=[])
    assert adjusted["Gear risk"] == 9 - _GEAR_RISK_NO_WARNING_REDUCTION


def test_adjust_gear_risk_unchanged_when_warnings_present():
    scores = {"Fitness risk": 8, "Altitude risk": 4, "Weather risk": 6, "Logistics risk": 10, "Gear risk": 9}
    warnings = ["Pack weight exceeds Light preference limit (12 kg)."]
    adjusted = adjust_gear_risk_for_warnings(scores, packing_warnings=warnings)
    assert adjusted["Gear risk"] == 9


def test_adjust_gear_risk_does_not_go_below_zero():
    scores = {"Fitness risk": 0, "Altitude risk": 0, "Weather risk": 0, "Logistics risk": 0, "Gear risk": 1}
    adjusted = adjust_gear_risk_for_warnings(scores, packing_warnings=[])
    assert adjusted["Gear risk"] == 0


def test_adjust_gear_risk_does_not_modify_other_dimensions():
    scores = {"Fitness risk": 8, "Altitude risk": 4, "Weather risk": 6, "Logistics risk": 10, "Gear risk": 9}
    adjusted = adjust_gear_risk_for_warnings(scores, packing_warnings=[])
    for dim in ["Fitness risk", "Altitude risk", "Weather risk", "Logistics risk"]:
        assert adjusted[dim] == scores[dim]


def test_adjust_gear_risk_does_not_mutate_input():
    scores = {"Fitness risk": 8, "Altitude risk": 4, "Weather risk": 6, "Logistics risk": 10, "Gear risk": 9}
    original_gear = scores["Gear risk"]
    adjust_gear_risk_for_warnings(scores, packing_warnings=[])
    assert scores["Gear risk"] == original_gear


# --- Integration tests ---

def test_overall_readiness_score_reduces_with_higher_risks():
    route = ROUTES[0]
    low_risk_profile = {
        "season": "October",
        "lodging_type": "Backcountry hut",
        "guided_vs_self_guided": "Guided",
        "pack_weight_preference": "Balanced",
        "number_of_days": 4,
        "hiking_pace": "Moderate",
        "rest_days": 1,
    }
    high_risk_profile = {
        "season": "October",
        "lodging_type": "Campsite",
        "guided_vs_self_guided": "Self-guided",
        "pack_weight_preference": "Minimal",
        "number_of_days": 6,
        "hiking_pace": "Fast",
        "rest_days": 0,
    }

    low_risk_scores = score_trip_risks(route, low_risk_profile, "Advanced", "Stable")
    high_risk_scores = score_trip_risks(route, high_risk_profile, "Beginner", "Unstable")

    assert overall_readiness_score(high_risk_scores) < overall_readiness_score(low_risk_scores)
