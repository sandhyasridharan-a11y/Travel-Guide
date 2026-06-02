def clamp(value, minimum=0, maximum=20):
    return max(minimum, min(value, maximum))


def score_fitness_risk(route, experience_level, trip_profile=None):
    distance = route.get("distance_km", 0)
    elevation = route.get("elevation_gain_m", 0)

    if trip_profile is not None:
        total_days = trip_profile.get("number_of_days", route.get("duration_days", 1))
        rest_days = trip_profile.get("rest_days", 0)
        moving_days = max(1, total_days - rest_days)
    else:
        moving_days = 1

    daily_distance = distance / moving_days
    daily_elevation = elevation / moving_days
    risk = 0

    if daily_distance <= 10:
        risk += 0
    elif daily_distance <= 15:
        risk += 2
    elif daily_distance <= 20:
        risk += 5
    elif daily_distance <= 25:
        risk += 8
    else:
        risk += 10

    if daily_elevation <= 300:
        risk += 0
    elif daily_elevation <= 600:
        risk += 2
    elif daily_elevation <= 1000:
        risk += 4
    elif daily_elevation <= 1500:
        risk += 6
    else:
        risk += 8

    if experience_level == "Beginner":
        risk += 4
    elif experience_level == "Intermediate":
        risk += 1
    elif experience_level == "Advanced":
        risk -= 5

    return clamp(risk)


def score_altitude_risk(route, experience_level):
    max_elevation = route.get("max_elevation_m", 0)
    risk = 0

    if max_elevation < 800:
        risk += 0
    elif max_elevation < 1500:
        risk += 3
    elif max_elevation < 2500:
        risk += 7
    elif max_elevation < 3500:
        risk += 12
    else:
        risk += 16

    if experience_level == "Beginner":
        risk += 3
    elif experience_level == "Intermediate":
        risk += 1
    elif experience_level == "Advanced":
        risk -= 4

    return clamp(risk)


def score_weather_risk(route, weather_condition):
    climate = route.get("climate", "Temperate").lower()
    region = route.get("region", "").lower()
    risk = 0

    if "cold" in climate or "mountain" in climate or "alpine" in climate:
        risk += 4
    elif "tropical" in climate or "desert" in climate:
        risk += 3
    else:
        risk += 1

    if weather_condition == "Mixed":
        risk += 3
    elif weather_condition == "Unstable":
        risk += 6

    if "patagonia" in region or "alpine" in region:
        risk += 2

    return clamp(risk)


def score_logistics_risk(route, trip_profile):
    risk = 0
    remoteness = route.get("remoteness", "Moderate")
    permit_required = route.get("permit_required", False)
    transport = route.get("transport_complexity", "Moderate")
    lodging = trip_profile.get("lodging_type", "Campsite")
    trip_style = trip_profile.get("guided_vs_self_guided", "Self-guided")

    if remoteness == "High":
        risk += 6
    elif remoteness == "Moderate":
        risk += 3
    else:
        risk += 1

    if permit_required:
        risk += 3

    if transport == "High":
        risk += 4
    elif transport == "Moderate":
        risk += 2
    else:
        risk += 0

    if lodging == "Hotel":
        risk += 0
    elif lodging == "Backcountry hut":
        risk += 1
    elif lodging == "Refugio/Campsite":
        risk += 2
    elif lodging == "Mixed camping/refugio":
        risk += 3
    elif lodging == "Campsite":
        risk += 4
    else:
        risk += 2

    if trip_style == "Self-guided":
        risk += 2

    return clamp(risk)


def score_gear_risk(route, trip_profile, weather_condition):
    risk = 0
    climate = route.get("climate", "Temperate")
    lodging = trip_profile.get("lodging_type", "Campsite")
    pack_style = trip_profile.get("pack_weight_preference", "Balanced")

    if "cold" in climate.lower() or "mountain" in climate.lower():
        risk += 4
    elif "hot" in climate.lower():
        risk += 3
    else:
        risk += 2

    if lodging == "Hotel":
        risk += 0
    elif lodging == "Backcountry hut":
        risk += 1
    elif lodging == "Refugio/Campsite":
        risk += 2
    elif lodging == "Mixed camping/refugio":
        risk += 3
    elif lodging == "Campsite":
        risk += 4
    else:
        risk += 2

    if pack_style == "Minimal":
        risk += 5
    elif pack_style == "Light":
        risk += 3
    elif pack_style == "Balanced":
        risk += 1
    else:
        risk += 2

    if weather_condition == "Mixed":
        risk += 2
    elif weather_condition == "Unstable":
        risk += 4

    return clamp(risk)


def score_trip_risks(route, trip_profile, experience_level, weather_condition):
    fitness = score_fitness_risk(route, experience_level, trip_profile)
    altitude = score_altitude_risk(route, experience_level)
    weather = score_weather_risk(route, weather_condition)
    logistics = score_logistics_risk(route, trip_profile)
    gear = score_gear_risk(route, trip_profile, weather_condition)

    return {
        "Fitness risk": fitness,
        "Altitude risk": altitude,
        "Weather risk": weather,
        "Logistics risk": logistics,
        "Gear risk": gear,
    }


_GUIDED_FITNESS_REDUCTION = 2
_GUIDED_GEAR_REDUCTION = 2
_GEAR_RISK_NO_WARNING_REDUCTION = 3


def apply_guided_adjustments(risk_scores, trip_profile):
    """Reduce Fitness and Gear risk for guided trips.

    A professional guide manages pace, rest, and turnaround decisions (fitness)
    and carries group safety and emergency gear (gear). Self-guided trips carry
    both responsibilities without professional support, so no reduction applies.
    """
    adjusted = dict(risk_scores)
    if trip_profile.get("guided_vs_self_guided") == "Guided":
        adjusted["Fitness risk"] = clamp(adjusted.get("Fitness risk", 0) - _GUIDED_FITNESS_REDUCTION)
        adjusted["Gear risk"] = clamp(adjusted.get("Gear risk", 0) - _GUIDED_GEAR_REDUCTION)
    return adjusted


def adjust_gear_risk_for_warnings(risk_scores, packing_warnings):
    """Reduce Gear risk when the packing plan is complete and correctly weighted.

    A plan with no warnings means critical items are present, pack weight is
    within the chosen preference, and shelter is covered. That directly offsets
    the route/climate-driven gear risk that was scored before the plan was built.
    """
    adjusted = dict(risk_scores)
    if not packing_warnings:
        adjusted["Gear risk"] = clamp(adjusted.get("Gear risk", 0) - _GEAR_RISK_NO_WARNING_REDUCTION)
    return adjusted


def overall_readiness_score(risk_scores):
    """Compute an overall readiness percentage from normalized risk dimensions."""
    weights = {
        "Fitness risk": 1.1,
        "Altitude risk": 1.0,
        "Weather risk": 1.0,
        "Logistics risk": 0.9,
        "Gear risk": 0.8,
    }
    total_weight = sum(weights.values())

    weighted_risk_sum = 0
    for dimension, score in risk_scores.items():
        weight = weights.get(dimension, 1.0)
        weighted_risk_sum += (score / 20) * 100 * weight

    average_weighted_risk = weighted_risk_sum / total_weight
    readiness = max(0, min(100, 100 - average_weighted_risk))
    return int(round(readiness))


def top_risk_drivers(risk_scores, count=3):
    return sorted(risk_scores.items(), key=lambda item: item[1], reverse=True)[:count]
