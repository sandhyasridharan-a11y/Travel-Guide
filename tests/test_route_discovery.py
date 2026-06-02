"""
Tests for route_discovery.py.
All network calls are mocked — no live API calls.
"""
import json
from unittest.mock import MagicMock, call, patch

import pytest

from route_discovery import (
    _build_profile,
    _library_lookup,
    _parse_difficulty,
    _parse_distance_km,
    _parse_duration_days,
    _parse_elevation_m,
    _parse_season,
    _wiki_search_variants,
    discover_route,
    suggest_routes,
)

# ── Helpers ───────────────────────────────────────────────────────────────────

def _urlopen_mock(responses: list[dict]):
    """
    Returns a context-manager mock that yields successive JSON responses
    for each urlopen call.
    """
    call_count = [0]

    def _side_effect(req, timeout=None):
        idx = call_count[0]
        call_count[0] += 1
        payload = responses[idx % len(responses)]
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps(payload).encode()
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        return mock_resp

    return MagicMock(side_effect=_side_effect)


_OSM_HIT = {
    "elements": [
        {
            "type": "relation",
            "center": {"lat": -51.006, "lon": -73.029},
            "tags": {"name:en": "W Trek", "name": "La Ruta del W", "route": "hiking"},
        }
    ]
}
_OSM_EMPTY = {"elements": []}

_WIKI_SEARCH_HIT = ["Appalachian Trail", ["Appalachian Trail", "Appalachian Trail by state"], [], []]
_WIKI_SEARCH_MISS = ["No trail", [], [], []]

_WIKI_EXTRACT = {
    "query": {
        "pages": {
            "1": {
                "pageid": 1,
                "title": "Appalachian Trail",
                "extract": (
                    "The Appalachian Trail is a hiking trail extending almost 2,200 miles (3,540 km). "
                    "It typically takes 5 to 7 months to thru-hike. "
                    "The trail involves 464,500 feet (141,582 m) of elevation gain. "
                    "It is considered strenuous and challenging for thru-hikers. "
                    "Best season is spring to fall."
                ),
                "coordinates": [{"lat": 41.98, "lon": -73.41}],
            }
        }
    }
}

_WIKI_EXTRACT_NO_COORDS = {
    "query": {
        "pages": {
            "1": {
                "pageid": 1,
                "title": "Some Trail",
                "extract": "A moderate trail covering 50 km in 3 days.",
            }
        }
    }
}


# ── _library_lookup ───────────────────────────────────────────────────────────

class TestLibraryLookup:
    def test_exact_match_case_insensitive(self):
        result = _library_lookup("patagonia w trek")
        assert result is not None
        assert result["route_name"] == "Patagonia W Trek"
        assert result["_source"] == "library"

    def test_substring_query_in_route_name(self):
        result = _library_lookup("W Trek")
        assert result is not None
        assert result["_source"] == "library"

    def test_substring_route_name_in_query(self):
        result = _library_lookup("Complete Patagonia W Trek Experience")
        assert result is not None
        assert result["_source"] == "library"

    def test_no_match_returns_none(self):
        assert _library_lookup("Kilimanjaro Summit Route") is None

    def test_library_hit_has_no_wiki_url(self):
        result = _library_lookup("Patagonia W Trek")
        assert result["_wiki_url"] is None


# ── Text parsers ──────────────────────────────────────────────────────────────

class TestParseDistanceKm:
    def test_km_unit(self):
        assert _parse_distance_km("80 km trail") == 80.0

    def test_kilometres_spelled_out(self):
        assert _parse_distance_km("covers 120 kilometres") == 120.0

    def test_comma_thousands(self):
        assert _parse_distance_km("3,540 km") == 3540.0

    def test_miles_converted(self):
        assert _parse_distance_km("2,200 miles") == pytest.approx(3540.5, abs=1)

    def test_km_preferred_over_miles(self):
        # "2,200 miles (3,540 km)" — km should win
        result = _parse_distance_km("almost 2,200 miles (3,540 km)")
        assert result == 3540.0

    def test_no_distance_returns_none(self):
        assert _parse_distance_km("a beautiful trail in the mountains") is None


class TestParseElevationM:
    def test_metres_with_gain(self):
        assert _parse_elevation_m("1,500 m elevation gain") == 1500

    def test_feet_with_gain_converted(self):
        result = _parse_elevation_m("4,921 ft of elevation gain")
        assert result == pytest.approx(1500, abs=5)

    def test_no_elevation_returns_none(self):
        assert _parse_elevation_m("a flat coastal walk") is None

    def test_requires_gain_keyword(self):
        # "rises 2500 m above sea level" should NOT match (not gain)
        assert _parse_elevation_m("the peak rises 2500 m above sea level") is None


class TestParseDurationDays:
    def test_range_takes_upper(self):
        assert _parse_duration_days("takes 4 to 5 days") == 5

    def test_range_with_dash(self):
        assert _parse_duration_days("a 4-5 day hike") == 5

    def test_hyphenated_single(self):
        assert _parse_duration_days("a 5-day route") == 5

    def test_plain_days(self):
        assert _parse_duration_days("approximately 7 days") == 7

    def test_no_duration_returns_none(self):
        assert _parse_duration_days("a beautiful mountain hike") is None


class TestParseDifficulty:
    def test_strenuous_is_hard(self):
        assert _parse_difficulty("This is a strenuous hike") == "Hard"

    def test_challenging_is_hard(self):
        assert _parse_difficulty("The route is challenging and demanding") == "Hard"

    def test_moderate(self):
        assert _parse_difficulty("A moderate trail suitable for families") == "Moderate"

    def test_easy(self):
        assert _parse_difficulty("An easy gentle walk for beginners") == "Easy"

    def test_no_difficulty_returns_none(self):
        assert _parse_difficulty("A trail through the mountains") is None


class TestParseSeason:
    def test_best_season_phrase(self):
        result = _parse_season("The best season is October to April for this trek.")
        assert result is not None
        assert "October" in result

    def test_no_season_returns_none(self):
        assert _parse_season("A trail through scenic landscapes") is None


class TestWikiSearchVariants:
    def test_exact_name_is_first(self):
        variants = _wiki_search_variants("Appalachian Trail")
        assert variants[0] == "Appalachian Trail"

    def test_strips_generic_words(self):
        variants = _wiki_search_variants("Torres del Paine Trek")
        assert any("trek" not in v.lower() for v in variants)

    def test_no_duplicate_when_stripping_changes_nothing(self):
        variants = _wiki_search_variants("Appalachian")
        assert len(set(v.lower() for v in variants)) == len(variants)


# ── _build_profile ────────────────────────────────────────────────────────────

class TestBuildProfile:
    def test_osm_coords_take_priority(self):
        osm = {"lat": -51.0, "lon": -73.0, "osm_name": "W Trek", "osm_distance_km": 80.0}
        wiki = {"lat": 99.0, "lon": 99.0, "wiki_title": "W Trek", "wiki_url": "http://x"}
        profile = _build_profile("W Trek", osm, wiki)
        assert profile["lat"] == -51.0
        assert profile["lon"] == -73.0

    def test_falls_back_to_wiki_coords_when_osm_missing(self):
        wiki = {"lat": -51.0, "lon": -73.0, "wiki_title": "W Trek", "wiki_url": "http://x"}
        profile = _build_profile("W Trek", None, wiki)
        assert profile["lat"] == -51.0

    def test_wiki_title_preferred_over_osm_name(self):
        # Wikipedia titles are cleaner and in English; OSM names can be local-language
        # or include geographic qualifiers ("International Appalachian Trail, Québec").
        osm = {"lat": 0, "lon": 0, "osm_name": "La Ruta del W", "osm_distance_km": None}
        wiki = {"wiki_title": "Torres del Paine", "wiki_url": "http://x"}
        profile = _build_profile("W Trek", osm, wiki)
        assert profile["route_name"] == "Torres del Paine"

    def test_all_schema_keys_present(self):
        from route_library import ROUTES
        schema_keys = set(ROUTES[0].keys())
        profile = _build_profile("Test Trail", {}, {})
        for key in schema_keys:
            assert key in profile, f"missing key: {key}"

    def test_source_is_discovered(self):
        profile = _build_profile("Test Trail", {}, {})
        assert profile["_source"] == "discovered"

    def test_recommended_nights_derived_from_duration(self):
        wiki = {"duration_days": 5, "wiki_title": "X", "wiki_url": "http://x"}
        profile = _build_profile("X", None, wiki)
        assert profile["recommended_nights"] == 4

    def test_none_inputs_give_safe_defaults(self):
        profile = _build_profile("Mystery Trail", None, None)
        assert profile["distance_km"] == 0.0
        assert profile["duration_days"] == 1
        assert profile["difficulty"] == "Moderate"


# ── suggest_routes ────────────────────────────────────────────────────────────

class TestSuggestRoutes:
    def test_partial_word_matches_library_route(self):
        # "blanc" is a word in "Tour du Mont Blanc"
        results = suggest_routes("blanc")
        assert "Tour du Mont Blanc" in results

    def test_keyword_matches_library_route(self):
        results = suggest_routes("milford")
        assert "Milford Track" in results

    def test_library_results_come_first(self):
        wiki_response = ["q", ["Some Wikipedia Trail", "Another Trail"], [], []]
        with patch("urllib.request.urlopen", _urlopen_mock([wiki_response])):
            results = suggest_routes("milford")
        assert results[0] == "Milford Track"

    def test_wikipedia_suggestions_appended(self):
        wiki_response = ["q", ["Appalachian Trail", "Appalachian Mountains"], [], []]
        with patch("urllib.request.urlopen", _urlopen_mock([wiki_response])):
            results = suggest_routes("appalachian")
        assert "Appalachian Trail" in results

    def test_returns_at_most_five(self):
        wiki_response = ["q", ["T1", "T2", "T3", "T4", "T5"], [], []]
        with patch("urllib.request.urlopen", _urlopen_mock([wiki_response])):
            results = suggest_routes("trail")
        assert len(results) <= 5

    def test_no_duplicates(self):
        # Library has "Milford Track"; Wikipedia also returns it
        wiki_response = ["q", ["Milford Track", "Milford Sound"], [], []]
        with patch("urllib.request.urlopen", _urlopen_mock([wiki_response])):
            results = suggest_routes("milford")
        assert results.count("Milford Track") == 1

    def test_empty_query_returns_empty(self):
        wiki_response = ["q", [], [], []]
        with patch("urllib.request.urlopen", _urlopen_mock([wiki_response])):
            results = suggest_routes("")
        assert results == []

    def test_short_words_ignored_in_library_match(self):
        # "of" is 2 chars — should be ignored in keyword matching
        wiki_response = ["q", [], [], []]
        with patch("urllib.request.urlopen", _urlopen_mock([wiki_response])):
            results = suggest_routes("of")
        assert results == []


# ── discover_route ────────────────────────────────────────────────────────────

class TestDiscoverRoute:
    def test_returns_library_route_without_api_calls(self):
        with patch("urllib.request.urlopen") as mock_open:
            result = discover_route("Patagonia W Trek")
        mock_open.assert_not_called()
        assert result["_source"] == "library"
        assert result["route_name"] == "Patagonia W Trek"

    def test_library_case_insensitive(self):
        result = discover_route("patagonia w trek")
        assert result is not None
        assert result["_source"] == "library"

    def test_returns_none_when_all_sources_empty(self):
        # discover_route calls _fetch_wikipedia first, then _fetch_osm.
        # "Completely Unknown Trail XYZ123" → variants ["Completely Unknown Trail XYZ123",
        # "Completely Unknown  XYZ123"] → 2 wiki searches, then 2 OSM tag searches.
        wiki_miss = ["q", [], [], []]
        osm_empty = {"elements": []}
        responses = [wiki_miss, wiki_miss, osm_empty, osm_empty]
        with patch("urllib.request.urlopen", _urlopen_mock(responses)):
            result = discover_route("Completely Unknown Trail XYZ123")
        assert result is None

    def test_discovered_profile_merges_osm_and_wiki(self):
        # "Appalachian Trail" → variant "Appalachian Trail" hits wiki immediately.
        # Call order: wiki search → wiki extract → OSM name:en (hit)
        responses = [_WIKI_SEARCH_HIT, _WIKI_EXTRACT, _OSM_HIT]
        with patch("urllib.request.urlopen", _urlopen_mock(responses)):
            result = discover_route("Appalachian Trail")
        assert result is not None
        assert result["_source"] == "discovered"
        assert result["lat"] == pytest.approx(-51.006, abs=0.01)  # OSM takes priority
        assert result["distance_km"] == 3540.0                    # from Wikipedia text
        assert result["difficulty"] == "Hard"                     # "strenuous" in text

    def test_discovered_with_only_wiki(self):
        # Wikipedia hits; both OSM tag searches return nothing.
        # Call order: wiki search → wiki extract → OSM name:en → OSM name
        responses = [_WIKI_SEARCH_HIT, _WIKI_EXTRACT, _OSM_EMPTY, _OSM_EMPTY]
        with patch("urllib.request.urlopen", _urlopen_mock(responses)):
            result = discover_route("Appalachian Trail")
        assert result is not None
        assert result["lat"] == pytest.approx(41.98, abs=0.01)   # from Wikipedia

    def test_discovered_with_only_osm(self):
        # Wikipedia misses on both search variants; OSM name:en hits.
        # "Appalachian Trail" doesn't match the library (only W Trek is curated).
        # Variants: ["Appalachian Trail", "Appalachian"] → 2 wiki misses → OSM name:en hit
        responses = [_WIKI_SEARCH_MISS, _WIKI_SEARCH_MISS, _OSM_HIT]
        with patch("urllib.request.urlopen", _urlopen_mock(responses)):
            result = discover_route("Appalachian Trail")
        assert result is not None
        assert result["lat"] == pytest.approx(-51.006, abs=0.01)  # from OSM mock
        assert result["route_name"] == "W Trek"                   # osm_name from mock tags

    def test_wiki_url_stored_in_profile(self):
        # Call order: wiki search → wiki extract → OSM name:en → OSM name
        responses = [_WIKI_SEARCH_HIT, _WIKI_EXTRACT, _OSM_EMPTY, _OSM_EMPTY]
        with patch("urllib.request.urlopen", _urlopen_mock(responses)):
            result = discover_route("Appalachian Trail")
        assert result is not None
        assert result["_wiki_url"] is not None
        assert "wikipedia.org" in result["_wiki_url"]

    def test_no_wiki_coords_falls_back_to_osm(self):
        # "W Trek Patagonia" doesn't substring-match the library (word order differs).
        # Strips "Trek" → variant "W  Patagonia" also tried.
        # Call order: wiki search (hit) → wiki extract (no coords) → OSM name:en (hit)
        wiki_no_coords = {
            "query": {
                "pages": {
                    "1": {
                        "pageid": 1,
                        "title": "Some Trail",
                        "extract": "A moderate 50 km trail.",
                    }
                }
            }
        }
        responses = [_WIKI_SEARCH_HIT, wiki_no_coords, _OSM_HIT]
        with patch("urllib.request.urlopen", _urlopen_mock(responses)):
            result = discover_route("W Trek Patagonia")
        assert result["lat"] == pytest.approx(-51.006, abs=0.01)  # from OSM
