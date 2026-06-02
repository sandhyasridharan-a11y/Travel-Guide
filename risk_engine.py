from scoring_model import score_trip_risks, overall_readiness_score


def readiness_to_risk_label(readiness_score):
    if readiness_score >= 80:
        return "Low"
    elif readiness_score >= 65:
        return "Moderate"
    elif readiness_score >= 50:
        return "High"
    elif readiness_score >= 35:
        return "Very High"
    else:
        return "Extreme"


def estimate_risk(route, weather_condition, experience_level, trip_profile=None):
    """Estimate overall route risk label from the scoring model.

    When trip_profile is omitted a minimal fallback is used so the function
    remains callable without a full profile (e.g. in tests or previews).
    """
    if trip_profile is None:
        trip_profile = {
            "number_of_days": route.get("duration_days", 5),
            "rest_days": 0,
            "lodging_type": "Refugio/Campsite",
            "guided_vs_self_guided": "Self-guided",
            "pack_weight_preference": "Balanced",
            "season": route.get("best_season", "Summer"),
        }
    risk_scores = score_trip_risks(route, trip_profile, experience_level, weather_condition)
    readiness = overall_readiness_score(risk_scores)
    return readiness_to_risk_label(readiness)
