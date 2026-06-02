import inspect

from route_library import ROUTES
from assumption_engine import propose_trip_profile
from scoring_model import score_trip_risks, overall_readiness_score
from itinerary_generator import generate_itinerary
from packing_engine import build_comprehensive_packing_plan
from briefing_generator import generate_briefing


def test_generate_briefing_contains_all_sections():
    route = ROUTES[0]
    trip_profile = propose_trip_profile(route)
    risk_scores = score_trip_risks(route, trip_profile, "Intermediate", "Mixed")
    readiness_score = overall_readiness_score(risk_scores)
    itinerary = generate_itinerary(route, trip_profile, risk_scores)
    packing_plan = build_comprehensive_packing_plan(
        route, trip_profile, "Intermediate", "Mixed", trip_profile["pack_weight_preference"], risk_scores
    )

    briefing = generate_briefing(
        route,
        trip_profile,
        risk_scores,
        readiness_score,
        itinerary,
        packing_plan,
    )

    assert "# Expedition Briefing" in briefing
    assert "## Trip summary" in briefing
    assert "## Confirmed assumptions" in briefing
    assert "## Route profile" in briefing
    assert "## Readiness and risk" in briefing
    assert "## Risk register" in briefing
    assert "## Day-by-day itinerary" in briefing
    assert "## Packing list" in briefing
    assert "## Logistics checklist" in briefing
    assert "## Emergency notes" in briefing
    assert route["route_name"] in briefing
    assert str(trip_profile["number_of_days"]) in briefing
    assert "permit" in briefing.lower()
    assert "Altitude risk" in briefing or "Weather risk" in briefing
    assert "Estimated pack weight" in briefing


def test_generate_briefing_includes_itinerary_days():
    route = ROUTES[0]
    trip_profile = propose_trip_profile(route)
    risk_scores = score_trip_risks(route, trip_profile, "Intermediate", "Stable")
    readiness_score = overall_readiness_score(risk_scores)
    itinerary = generate_itinerary(route, trip_profile, risk_scores)
    packing_plan = build_comprehensive_packing_plan(
        route, trip_profile, "Intermediate", "Stable", trip_profile["pack_weight_preference"], risk_scores
    )

    briefing = generate_briefing(
        route,
        trip_profile,
        risk_scores,
        readiness_score,
        itinerary,
        packing_plan,
    )

    assert "Day 1" in briefing
    assert "Day 2" in briefing or trip_profile["number_of_days"] == 1


def test_generate_briefing_top_drivers_argument_is_keyword_only():
    signature = inspect.signature(generate_briefing)
    param = signature.parameters.get("top_drivers")

    assert param is not None
    assert param.kind == inspect.Parameter.KEYWORD_ONLY
