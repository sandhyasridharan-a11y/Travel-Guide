from route_library import ROUTES
from packing_engine import build_comprehensive_packing_plan, build_packing_list
from gear_rules import (
    get_must_have_items,
    get_optional_items,
    get_risk_based_additions,
    estimate_pack_weight,
    validate_packing_list,
    GEAR_DATABASE,
)


def test_must_have_items_includes_essentials():
    route = ROUTES[0]  # Patagonia W Trek
    trip_profile = {"lodging_type": "Refugio/Campsite", "number_of_days": 5}
    must_haves = get_must_have_items(route, trip_profile, "Intermediate", "Mixed")

    assert "Waterproof shell jacket" in must_haves
    assert "Hiking boots (broken in)" in must_haves
    assert "First-aid kit" in must_haves
    assert "Sleeping bag (season-appropriate)" in must_haves
    assert "Tent" in must_haves


def test_optional_items_based_on_pack_preference():
    route = ROUTES[0]
    trip_profile = {"lodging_type": "Refugio/Campsite", "number_of_days": 5}

    optional_minimal = get_optional_items(route, trip_profile, "Minimal")
    optional_light = get_optional_items(route, trip_profile, "Light")
    optional_balanced = get_optional_items(route, trip_profile, "Balanced")
    optional_heavy = get_optional_items(route, trip_profile, "Heavy")

    # Verify progressive increase
    assert len(optional_minimal) == 0, "Minimal should have no optional items"
    assert len(optional_light) > len(optional_minimal), "Light should have more than Minimal"
    assert len(optional_balanced) > len(optional_light), "Balanced should have more than Light"
    assert len(optional_heavy) > len(optional_balanced), "Heavy should have more than Balanced"


def test_risk_based_additions_for_high_altitude_risk():
    route = ROUTES[0]
    trip_profile = {"lodging_type": "Refugio/Campsite", "number_of_days": 5}
    high_altitude_risk = {
        "Fitness risk": 5,
        "Altitude risk": 15,
        "Weather risk": 5,
        "Logistics risk": 5,
        "Gear risk": 5,
    }

    additions = get_risk_based_additions(high_altitude_risk, route, trip_profile, "Mixed")

    assert "Altitude sickness medication" in additions
    assert "Oxygen supplementary" in additions


def test_risk_based_additions_for_high_weather_risk():
    route = ROUTES[0]
    trip_profile = {"lodging_type": "Refugio/Campsite", "number_of_days": 5}
    high_weather_risk = {
        "Fitness risk": 5,
        "Altitude risk": 5,
        "Weather risk": 16,
        "Logistics risk": 5,
        "Gear risk": 5,
    }

    additions = get_risk_based_additions(high_weather_risk, route, trip_profile, "Unstable")

    assert "Heavy insulation layer" in additions
    assert "Sun shade/umbrella" in additions


def test_estimate_pack_weight_positive():
    items = ["Backpack (70L)", "Sleeping bag (season-appropriate)", "Tent"]
    weight = estimate_pack_weight(items)

    assert weight > 4
    assert weight < 10


def test_validate_packing_list_warns_on_overweight():
    items = ["Backpack (70L)"] + list(GEAR_DATABASE.keys())[:30]
    warnings = validate_packing_list(items, "Light", {})

    assert any("weight" in w.lower() for w in warnings)


def test_validate_packing_list_warns_on_missing_tent_for_campsite():
    trip_profile = {"lodging_type": "Campsite", "number_of_days": 5}
    items = ["Backpack (70L)", "Sleeping bag (season-appropriate)", "Sleeping pad (insulated)"]
    warnings = validate_packing_list(items, "Balanced", trip_profile)

    assert any("tent" in w.lower() for w in warnings)


def test_comprehensive_packing_plan_patagonia_w_trek():
    route = ROUTES[0]  # Patagonia W Trek
    trip_profile = {
        "lodging_type": "Refugio/Campsite",
        "number_of_days": 5,
        "pack_weight_preference": "Light",
    }
    risk_scores = {
        "Fitness risk": 12,
        "Altitude risk": 10,
        "Weather risk": 14,
        "Logistics risk": 8,
        "Gear risk": 9,
    }

    plan = build_comprehensive_packing_plan(
        route, trip_profile, "Intermediate", "Mixed", "Light", risk_scores
    )

    assert len(plan["must_haves"]) > 20
    assert len(plan["optional"]) >= 0
    assert len(plan["risk_based_additions"]) > 0
    assert plan["estimated_weight_kg"] > 10
    assert plan["estimated_weight_kg"] < 25
    assert isinstance(plan["warnings"], list)


def test_comprehensive_packing_plan_structure():
    route = ROUTES[0]
    trip_profile = {"lodging_type": "Refugio/Campsite", "number_of_days": 5}
    risk_scores = {
        "Fitness risk": 5,
        "Altitude risk": 5,
        "Weather risk": 5,
        "Logistics risk": 5,
        "Gear risk": 5,
    }

    plan = build_comprehensive_packing_plan(
        route, trip_profile, "Advanced", "Stable", "Balanced", risk_scores
    )

    assert "must_haves" in plan
    assert "optional" in plan
    assert "risk_based_additions" in plan
    assert "all_items" in plan
    assert "estimated_weight_kg" in plan
    assert "warnings" in plan
    assert all(
        item in plan["all_items"]
        for item in plan["must_haves"] + plan["optional"] + plan["risk_based_additions"]
    )


def test_legacy_build_packing_list_backward_compatibility():
    route = ROUTES[0]
    items = build_packing_list(route, "Intermediate", "Mixed", "Balanced")

    assert isinstance(items, list)
    assert len(items) > 0
    assert all(isinstance(item, str) for item in items)
