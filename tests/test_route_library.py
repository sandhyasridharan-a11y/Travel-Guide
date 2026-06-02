import pytest
from route_library import ROUTES, get_route_by_name

_REQUIRED_KEYS = [
    "route_name", "region", "difficulty", "duration_days", "distance_km",
    "elevation_gain_m", "max_elevation_m", "base_elevation_m", "highlights",
    "best_season", "climate", "remoteness", "permit_required",
    "transport_complexity", "description", "recommended_nights",
    "recommended_activities", "route_type", "recommended_fitness_level",
    "lat", "lon", "image_url",
]

_EXPECTED_ROUTES = [
    "Patagonia W Trek",
    "Tour du Mont Blanc",
    "Milford Track",
    "Inca Trail",
    "Camino Francés",
]


def test_library_contains_all_expected_routes():
    names = [r["route_name"] for r in ROUTES]
    for name in _EXPECTED_ROUTES:
        assert name in names, f"Missing route: {name}"


def test_get_route_by_name_returns_matching_route():
    route = get_route_by_name("Patagonia W Trek")
    assert route is not None
    assert route["route_name"] == "Patagonia W Trek"


def test_get_route_by_name_returns_none_for_missing_route():
    assert get_route_by_name("Nonexistent Trail") is None


@pytest.mark.parametrize("route", ROUTES, ids=lambda r: r["route_name"])
def test_every_route_has_required_schema_keys(route):
    for key in _REQUIRED_KEYS:
        assert key in route, f"{route['route_name']} missing key: {key}"


@pytest.mark.parametrize("route", ROUTES, ids=lambda r: r["route_name"])
def test_every_route_has_coordinates(route):
    assert route["lat"] is not None, f"{route['route_name']} missing lat"
    assert route["lon"] is not None, f"{route['route_name']} missing lon"
    assert -90 <= route["lat"] <= 90
    assert -180 <= route["lon"] <= 180


@pytest.mark.parametrize("route", ROUTES, ids=lambda r: r["route_name"])
def test_every_route_has_positive_stats(route):
    assert route["duration_days"] >= 1
    assert route["distance_km"] > 0
    assert route["elevation_gain_m"] >= 0
    assert route["max_elevation_m"] >= 0


@pytest.mark.parametrize("route", ROUTES, ids=lambda r: r["route_name"])
def test_every_route_difficulty_is_valid(route):
    assert route["difficulty"] in ("Easy", "Moderate", "Hard")
