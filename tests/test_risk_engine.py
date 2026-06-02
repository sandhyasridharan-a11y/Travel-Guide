from route_library import ROUTES
from risk_engine import estimate_risk, readiness_to_risk_label

_VALID_LABELS = ["Low", "Moderate", "High", "Very High", "Extreme"]


# --- readiness_to_risk_label ---

def test_readiness_to_risk_label_low():
    assert readiness_to_risk_label(85) == "Low"
    assert readiness_to_risk_label(80) == "Low"


def test_readiness_to_risk_label_moderate():
    assert readiness_to_risk_label(79) == "Moderate"
    assert readiness_to_risk_label(65) == "Moderate"


def test_readiness_to_risk_label_high():
    assert readiness_to_risk_label(64) == "High"
    assert readiness_to_risk_label(50) == "High"


def test_readiness_to_risk_label_very_high():
    assert readiness_to_risk_label(49) == "Very High"
    assert readiness_to_risk_label(35) == "Very High"


def test_readiness_to_risk_label_extreme():
    assert readiness_to_risk_label(34) == "Extreme"
    assert readiness_to_risk_label(0) == "Extreme"


def test_readiness_to_risk_label_covers_full_range():
    for score in range(0, 101, 5):
        assert readiness_to_risk_label(score) in _VALID_LABELS


# --- estimate_risk ---

def test_estimate_risk_outputs_expected_levels():
    route = ROUTES[0]
    assert estimate_risk(route, "Stable", "Advanced") == "Moderate"
    assert estimate_risk(route, "Unstable", "Beginner") == "High"
    assert estimate_risk(route, "Mixed", "Intermediate") == "High"


def test_estimate_risk_returns_valid_string():
    route = ROUTES[0]
    assert estimate_risk(route, "Stable", "Beginner") in _VALID_LABELS


def test_estimate_risk_increases_with_worse_weather_and_lower_experience():
    route = ROUTES[0]
    beginner_unstable = estimate_risk(route, "Unstable", "Beginner")
    advanced_stable = estimate_risk(route, "Stable", "Advanced")

    risk_levels = ["Low", "Moderate", "High", "Very High", "Extreme"]
    assert risk_levels.index(beginner_unstable) > risk_levels.index(advanced_stable)


def test_estimate_risk_consistent_with_scoring_model_when_trip_profile_supplied():
    from scoring_model import score_trip_risks, overall_readiness_score
    route = ROUTES[0]
    trip_profile = {
        "number_of_days": 5,
        "rest_days": 1,
        "lodging_type": "Refugio/Campsite",
        "guided_vs_self_guided": "Self-guided",
        "pack_weight_preference": "Light",
        "season": "October to April",
    }
    risk_scores = score_trip_risks(route, trip_profile, "Intermediate", "Mixed")
    readiness = overall_readiness_score(risk_scores)
    expected_label = readiness_to_risk_label(readiness)

    assert estimate_risk(route, "Mixed", "Intermediate", trip_profile) == expected_label
