def propose_trip_profile(route):
    difficulty = route.get("difficulty", "").lower()
    duration = route.get("duration_days", 1)
    recommended_fitness = route.get("recommended_fitness_level", "").lower()

    lodging_type = "Refugio/Campsite" if difficulty == "hard" else "Campsite"
    if "Patagonia" in route.get("region", ""):
        lodging_type = "Refugio/Campsite"

    hiking_pace = "Steady" if difficulty == "hard" else "Leisurely"
    rest_days = 1 if duration >= 5 else 0
    guided_vs_self_guided = "Self-guided" if recommended_fitness == "advanced" else "Guided"
    pack_weight_preference = "Light" if difficulty == "hard" else "Balanced"

    return {
        "number_of_days": duration,
        "lodging_type": lodging_type,
        "hiking_pace": hiking_pace,
        "rest_days": rest_days,
        "guided_vs_self_guided": guided_vs_self_guided,
        "pack_weight_preference": pack_weight_preference,
        "season": route.get("best_season", "Summer"),
    }
