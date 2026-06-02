from gear_rules import (
    get_must_have_items,
    get_optional_items,
    get_risk_based_additions,
    estimate_pack_weight,
    validate_packing_list,
)


def build_packing_list(route, experience_level, weather_condition, pack_weight_preference="Balanced"):
    """
    Legacy function for backward compatibility.
    Returns a simple list of items.
    """
    trip_profile = {
        "lodging_type": "Refugio/Campsite" if route.get("difficulty") == "Hard" else "Campsite",
        "number_of_days": route.get("duration_days", 5),
    }
    risk_scores = {
        "Fitness risk": 5,
        "Altitude risk": 5,
        "Weather risk": 5,
        "Logistics risk": 5,
        "Gear risk": 5,
    }
    
    result = build_comprehensive_packing_plan(route, trip_profile, experience_level, weather_condition, pack_weight_preference, risk_scores)
    # Return a flat list for backward compatibility
    all_items = result["must_haves"] + result["optional"] + result["risk_based_additions"]
    return all_items


def build_comprehensive_packing_plan(route, trip_profile, experience_level, weather_condition, pack_weight_preference, risk_scores):
    """
    Build a comprehensive packing plan with must-haves, optional, risk-based, warnings, and weight.
    """
    must_haves = get_must_have_items(route, trip_profile, experience_level, weather_condition)
    optional = get_optional_items(route, trip_profile, pack_weight_preference)
    risk_based = get_risk_based_additions(risk_scores, route, trip_profile, weather_condition)
    
    all_items = must_haves + optional + risk_based
    warnings = validate_packing_list(all_items, pack_weight_preference, trip_profile)
    pack_weight = estimate_pack_weight(all_items)
    
    return {
        "must_haves": must_haves,
        "optional": optional,
        "risk_based_additions": risk_based,
        "all_items": all_items,
        "estimated_weight_kg": pack_weight,
        "warnings": warnings,
    }
