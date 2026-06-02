"""
Gear rules and packing logic for hiking trips.
Defines item categories, seasonal adjustments, weather considerations, and weight estimates.
"""

# Gear categories with weights (grams) and descriptions
GEAR_DATABASE = {
    # Clothing - base layer system
    "Base layer set": {"weight": 300, "category": "clothing", "essential": True},
    "Insulating mid-layer (fleece/down)": {"weight": 400, "category": "clothing", "essential": True},
    "Waterproof shell jacket": {"weight": 350, "category": "clothing", "essential": True},
    "Waterproof shell pants": {"weight": 250, "category": "clothing", "essential": False},
    "Hiking boots (broken in)": {"weight": 1200, "category": "clothing", "essential": True},
    "Camp/casual shoes": {"weight": 400, "category": "clothing", "essential": False},
    "Wool socks (3 pairs)": {"weight": 150, "category": "clothing", "essential": True},
    "Hat/beanie": {"weight": 80, "category": "clothing", "essential": True},
    "Sun hat": {"weight": 120, "category": "clothing", "essential": False},
    "Gloves": {"weight": 100, "category": "clothing", "essential": False},
    "Underwear (4 pairs)": {"weight": 150, "category": "clothing", "essential": True},

    # Sleep system
    "Sleeping bag (season-appropriate)": {"weight": 1200, "category": "sleep", "essential": True},
    "Sleeping pad (insulated)": {"weight": 600, "category": "sleep", "essential": True},
    "Sleeping pad (lightweight)": {"weight": 400, "category": "sleep", "essential": False},
    "Pillow/stuff sack": {"weight": 100, "category": "sleep", "essential": False},

    # Shelter & camp
    "Tent": {"weight": 1500, "category": "shelter", "essential": True},
    "Lightweight tarp": {"weight": 300, "category": "shelter", "essential": False},
    "Ground sheet": {"weight": 150, "category": "shelter", "essential": False},

    # Navigation & safety
    "Map and compass": {"weight": 150, "category": "navigation", "essential": True},
    "GPS device": {"weight": 200, "category": "navigation", "essential": False},
    "Emergency whistle": {"weight": 20, "category": "navigation", "essential": True},
    "First-aid kit": {"weight": 300, "category": "safety", "essential": True},
    "Multi-tool": {"weight": 150, "category": "safety", "essential": True},
    "Emergency repair kit": {"weight": 200, "category": "safety", "essential": True},
    "Communication device (satellite)": {"weight": 250, "category": "safety", "essential": False},

    # Lighting
    "Headlamp with batteries": {"weight": 200, "category": "lighting", "essential": True},
    "Backup headlamp": {"weight": 150, "category": "lighting", "essential": False},
    "Lantern (camp)": {"weight": 250, "category": "lighting", "essential": False},

    # Water & food
    "Water bottles (2L capacity)": {"weight": 600, "category": "water", "essential": True},
    "Water filter or purification": {"weight": 200, "category": "water", "essential": True},
    "Cooking stove": {"weight": 300, "category": "food", "essential": True},
    "Lightweight cookware": {"weight": 400, "category": "food", "essential": True},
    "Utensils": {"weight": 100, "category": "food", "essential": True},
    "Food (high-calorie, multi-day)": {"weight": 1500, "category": "food", "essential": True},
    "Emergency rations": {"weight": 200, "category": "food", "essential": True},

    # Hygiene & personal
    "Toothbrush and toothpaste": {"weight": 50, "category": "hygiene", "essential": True},
    "Toilet paper and trowel": {"weight": 100, "category": "hygiene", "essential": True},
    "Biodegradable soap": {"weight": 30, "category": "hygiene", "essential": True},
    "Sunscreen (high SPF)": {"weight": 100, "category": "hygiene", "essential": True},
    "Lip balm with SPF": {"weight": 20, "category": "hygiene", "essential": True},
    "Insect repellent": {"weight": 50, "category": "hygiene", "essential": False},
    "Blister treatment kit": {"weight": 50, "category": "hygiene", "essential": True},

    # Documents & miscellaneous
    "Permits and ID": {"weight": 50, "category": "documents", "essential": True},
    "Cash and cards": {"weight": 50, "category": "documents", "essential": True},
    "Travel insurance documents": {"weight": 20, "category": "documents", "essential": True},
    "Notebook and pencil": {"weight": 50, "category": "miscellaneous", "essential": False},

    # Altitude-specific
    "Altitude sickness medication": {"weight": 50, "category": "altitude", "essential": False},
    "Oxygen supplementary": {"weight": 200, "category": "altitude", "essential": False},

    # Weather-specific
    "Rain cover for pack": {"weight": 150, "category": "weather", "essential": False},
    "Windproof shell": {"weight": 200, "category": "weather", "essential": False},
    "Heavy insulation layer": {"weight": 600, "category": "weather", "essential": False},
    "Sun shade/umbrella": {"weight": 200, "category": "weather", "essential": False},

    # Bag
    "Backpack (70L)": {"weight": 2000, "category": "bag", "essential": True},
    "Daypack": {"weight": 600, "category": "bag", "essential": False},
}


def get_must_have_items(route, trip_profile, experience_level, weather_condition):
    """
    Build a list of must-have items based on route and trip conditions.
    """
    must_haves = []

    # Core essentials
    must_haves.extend([
        "Base layer set",
        "Insulating mid-layer (fleece/down)",
        "Waterproof shell jacket",
        "Hiking boots (broken in)",
        "Wool socks (3 pairs)",
        "Hat/beanie",
        "Underwear (4 pairs)",
        "Sleeping bag (season-appropriate)",
        "Sleeping pad (insulated)",
        "Map and compass",
        "Emergency whistle",
        "First-aid kit",
        "Multi-tool",
        "Emergency repair kit",
        "Headlamp with batteries",
        "Water bottles (2L capacity)",
        "Water filter or purification",
        "Cooking stove",
        "Lightweight cookware",
        "Utensils",
        "Food (high-calorie, multi-day)",
        "Emergency rations",
        "Toothbrush and toothpaste",
        "Toilet paper and trowel",
        "Biodegradable soap",
        "Sunscreen (high SPF)",
        "Lip balm with SPF",
        "Blister treatment kit",
        "Permits and ID",
        "Cash and cards",
        "Travel insurance documents",
        "Backpack (70L)",
    ])

    # Route-specific essentials
    if route.get("difficulty") == "Hard":
        must_haves.append("Waterproof shell pants")
        must_haves.append("Trekking poles")
    
    if trip_profile.get("lodging_type") == "Campsite" or trip_profile.get("lodging_type") == "Refugio/Campsite":
        must_haves.append("Tent")
        must_haves.append("Ground sheet")

    # Weather-based
    if weather_condition in ["Mixed", "Unstable"]:
        must_haves.extend(["Rain cover for pack", "Windproof shell"])

    # Experience-based
    if experience_level == "Beginner":
        must_haves.append("Communication device (satellite)")

    return must_haves


def get_optional_items(route, trip_profile, pack_weight_preference):
    """
    Build a list of optional items based on preferences and conditions.
    Scales from minimal (essentials only) to heavy (max comfort).
    """
    optional = []

    if pack_weight_preference == "Minimal":
        # Ultra-light: skip most optional comfort items
        pass

    elif pack_weight_preference == "Light":
        # Light: a few lightweight comfort items
        optional.extend([
            "Pillow/stuff sack",
            "Backup headlamp",
        ])

    elif pack_weight_preference == "Balanced":
        # Balanced: good mix of comfort and weight
        optional.extend([
            "Camp/casual shoes",
            "Pillow/stuff sack",
            "Backup headlamp",
            "Lantern (camp)",
            "Daypack",
        ])

    elif pack_weight_preference == "Heavy":
        # Heavy: maximum comfort items
        optional.extend([
            "Camp/casual shoes",
            "Pillow/stuff sack",
            "Backup headlamp",
            "Lantern (camp)",
            "Daypack",
            "Lightweight tarp",
            "Notebook and pencil",
            "Sun hat",
            "Sleeping pad (lightweight)",
        ])

    return optional


def get_risk_based_additions(risk_scores, route, trip_profile, weather_condition):
    """
    Add gear based on identified risk dimensions.
    Thresholds are scaled for 0-20 scoring system.
    """
    additions = []

    fitness_risk = risk_scores.get("Fitness risk", 0)
    if fitness_risk >= 12:
        additions.extend([
            "Extra emergency rations",
            "Emergency repair kit",
            "Communication device (satellite)",
        ])

    altitude_risk = risk_scores.get("Altitude risk", 0)
    if altitude_risk >= 10:
        additions.extend([
            "Altitude sickness medication",
            "Extra insulation layer",
            "Oxygen supplementary",
        ])

    weather_risk = risk_scores.get("Weather risk", 0)
    if weather_risk >= 12:
        additions.extend([
            "Heavy insulation layer",
            "Extra waterproof layers",
            "Sun shade/umbrella",
        ])

    logistics_risk = risk_scores.get("Logistics risk", 0)
    if logistics_risk >= 12:
        additions.extend([
            "Communication device (satellite)",
            "Extra emergency rations",
        ])

    gear_risk = risk_scores.get("Gear risk", 0)
    if gear_risk >= 12:
        additions.extend([
            "Backup sleeping pad",
            "Emergency repair kit",
            "Multi-tool",
        ])

    return additions


def estimate_pack_weight(packing_items):
    """
    Estimate total pack weight in kg from a list of item names.
    """
    total_weight_grams = 0
    for item_name in packing_items:
        if item_name in GEAR_DATABASE:
            total_weight_grams += GEAR_DATABASE[item_name]["weight"]
    return total_weight_grams / 1000


def validate_packing_list(packing_items, pack_weight_preference, trip_profile):
    """
    Check for potential missing gear and return warnings.
    """
    warnings = []

    pack_weight = estimate_pack_weight(packing_items)
    max_weight = {
        "Minimal": 8,
        "Light": 12,
        "Balanced": 16,
        "Heavy": 20,
    }.get(pack_weight_preference, 16)

    if pack_weight > max_weight:
        warnings.append(f"Pack weight ({pack_weight:.1f} kg) exceeds {pack_weight_preference} preference limit ({max_weight} kg). Consider removing optional items.")

    # Check for critical items
    critical_items = ["Waterproof shell jacket", "Sleeping bag (season-appropriate)", "First-aid kit", "Water filter or purification"]
    for item in critical_items:
        if item not in packing_items:
            warnings.append(f"Missing critical item: {item}")

    # Check for tent if needed
    if trip_profile.get("lodging_type") == "Campsite" and "Tent" not in packing_items:
        warnings.append("Trip includes camping but no tent in packing list.")

    return warnings
