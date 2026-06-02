from route_library import ROUTES
from risk_register import build_mitigation_plan, risk_register_summary

_ROUTE = ROUTES[0]  # Patagonia W Trek

_TRIP_PROFILE = {
    "lodging_type": "Refugio/Campsite",
    "number_of_days": 5,
    "rest_days": 1,
    "guided_vs_self_guided": "Self-guided",
}

_LOW_RISK_SCORES = {
    "Fitness risk": 4,
    "Altitude risk": 3,
    "Weather risk": 5,
    "Logistics risk": 6,
    "Gear risk": 4,
}

_HIGH_RISK_SCORES = {
    "Fitness risk": 15,
    "Altitude risk": 16,
    "Weather risk": 14,
    "Logistics risk": 13,
    "Gear risk": 15,
}


# --- risk_register_summary ---

def test_risk_register_summary_returns_five_entries():
    summary = risk_register_summary(_LOW_RISK_SCORES)
    assert len(summary) == 5


def test_risk_register_summary_contains_all_dimensions():
    summary = risk_register_summary(_LOW_RISK_SCORES)
    dimensions = {item["dimension"] for item in summary}
    assert dimensions == {"Fitness risk", "Altitude risk", "Weather risk", "Logistics risk", "Gear risk"}


def test_risk_register_summary_high_severity_for_score_15_or_above():
    scores = {"Fitness risk": 15, "Altitude risk": 0, "Weather risk": 0, "Logistics risk": 0, "Gear risk": 0}
    summary = risk_register_summary(scores)
    fitness_item = next(i for i in summary if i["dimension"] == "Fitness risk")
    assert fitness_item["severity"] == "High"


def test_risk_register_summary_moderate_severity_for_score_10_to_14():
    scores = {"Fitness risk": 10, "Altitude risk": 0, "Weather risk": 0, "Logistics risk": 0, "Gear risk": 0}
    summary = risk_register_summary(scores)
    fitness_item = next(i for i in summary if i["dimension"] == "Fitness risk")
    assert fitness_item["severity"] == "Moderate"


def test_risk_register_summary_low_severity_for_score_below_10():
    summary = risk_register_summary(_LOW_RISK_SCORES)
    for item in summary:
        assert item["severity"] == "Low"


def test_risk_register_summary_score_stored_correctly():
    scores = {"Fitness risk": 12, "Altitude risk": 0, "Weather risk": 0, "Logistics risk": 0, "Gear risk": 0}
    summary = risk_register_summary(scores)
    fitness_item = next(i for i in summary if i["dimension"] == "Fitness risk")
    assert fitness_item["score"] == 12


# --- build_mitigation_plan ---

def test_build_mitigation_plan_returns_five_items():
    plan = build_mitigation_plan(_LOW_RISK_SCORES, _ROUTE, _TRIP_PROFILE)
    assert len(plan) == 5


def test_build_mitigation_plan_all_items_are_strings():
    plan = build_mitigation_plan(_LOW_RISK_SCORES, _ROUTE, _TRIP_PROFILE)
    assert all(isinstance(item, str) for item in plan)


def test_build_mitigation_plan_high_fitness_risk_includes_training_advice():
    scores = {**_LOW_RISK_SCORES, "Fitness risk": 14}
    plan = build_mitigation_plan(scores, _ROUTE, _TRIP_PROFILE)
    assert any("training" in item.lower() or "endurance" in item.lower() for item in plan)


def test_build_mitigation_plan_high_altitude_risk_includes_acclimatization():
    scores = {**_LOW_RISK_SCORES, "Altitude risk": 13}
    plan = build_mitigation_plan(scores, _ROUTE, _TRIP_PROFILE)
    assert any("acclimatization" in item.lower() or "altitude" in item.lower() for item in plan)


def test_build_mitigation_plan_high_weather_risk_includes_layers():
    scores = {**_LOW_RISK_SCORES, "Weather risk": 12}
    plan = build_mitigation_plan(scores, _ROUTE, _TRIP_PROFILE)
    assert any("weather" in item.lower() or "layer" in item.lower() for item in plan)


def test_build_mitigation_plan_high_logistics_risk_mentions_permits():
    scores = {**_LOW_RISK_SCORES, "Logistics risk": 14}
    plan = build_mitigation_plan(scores, _ROUTE, _TRIP_PROFILE)
    assert any("permit" in item.lower() or "reservation" in item.lower() for item in plan)


def test_build_mitigation_plan_high_gear_risk_mentions_kit_review():
    scores = {**_LOW_RISK_SCORES, "Gear risk": 12}
    plan = build_mitigation_plan(scores, _ROUTE, _TRIP_PROFILE)
    assert any("gear" in item.lower() or "kit" in item.lower() or "shelter" in item.lower() for item in plan)


def test_build_mitigation_plan_low_risk_produces_maintenance_advice():
    plan = build_mitigation_plan(_LOW_RISK_SCORES, _ROUTE, _TRIP_PROFILE)
    # Low-risk plan should mention conditioning or maintenance, not "increase training"
    assert not any("increase training" in item.lower() for item in plan)
