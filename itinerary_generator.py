import math
from day_planner import plan_day

PATAGONIA_SEGMENTS = [
    "Pudeto to Refugio Grey",
    "Refugio Grey to French Valley",
    "French Valley to Refugio Los Cuernos",
    "Los Cuernos to Torres Base",
    "Torres Base to Trailhead",
]


def _choose_segments(route_name, moving_days):
    if "Patagonia W Trek" in route_name:
        return PATAGONIA_SEGMENTS[:moving_days] or ["Patagonia W Trek segment"]
    return [f"Segment {i + 1}" for i in range(moving_days)]


def _estimate_daily_profile(route, trip_profile):
    total_days = trip_profile.get("number_of_days", route.get("duration_days", 1))
    rest_days = trip_profile.get("rest_days", 0)
    moving_days = max(1, total_days - rest_days)

    distance = route.get("distance_km", 0)
    elevation = route.get("elevation_gain_m", 0)
    daily_distance = distance / moving_days
    daily_elevation = elevation / moving_days

    return {
        "total_days": total_days,
        "rest_days": rest_days,
        "moving_days": moving_days,
        "daily_distance": daily_distance,
        "daily_elevation": daily_elevation,
    }


def _determine_rest_day_indices(total_days, rest_days):
    if rest_days <= 0:
        return []
    indices = []
    midpoint = math.ceil(total_days / 2)
    for i in range(rest_days):
        index = min(total_days, midpoint + i)
        indices.append(index)
    return indices


def generate_itinerary(route, trip_profile, risk_scores):
    profile = _estimate_daily_profile(route, trip_profile)
    total_days = profile["total_days"]
    moving_days = profile["moving_days"]
    daily_distance = profile["daily_distance"]
    daily_elevation = profile["daily_elevation"]
    segments = _choose_segments(route.get("route_name", "Route"), moving_days)
    rest_day_indices = _determine_rest_day_indices(total_days, profile["rest_days"])

    itinerary = []
    moving_index = 0
    last_segment = segments[-1] if segments else route.get("route_name", "Route")

    for day in range(1, total_days + 1):
        if day in rest_day_indices:
            itinerary.append(plan_day(day, last_segment, 0, 0, trip_profile.get("hiking_pace", "Steady"), trip_profile, risk_scores, is_rest_day=True))
            continue

        segment_name = segments[min(moving_index, len(segments) - 1)]
        itinerary.append(plan_day(day, segment_name, daily_distance, daily_elevation, trip_profile.get("hiking_pace", "Steady"), trip_profile, risk_scores))
        moving_index += 1

    return itinerary


def summarize_itinerary(itinerary):
    return [
        {
            "day": day_plan["day"],
            "route_segment": day_plan["route_segment"],
            "distance_km": day_plan["distance_km"],
            "elevation_gain_m": day_plan["elevation_gain_m"],
            "estimated_time_hrs": day_plan["estimated_time_hrs"],
        }
        for day_plan in itinerary
    ]
