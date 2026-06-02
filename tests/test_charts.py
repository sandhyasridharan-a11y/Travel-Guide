from __future__ import annotations

import altair as alt
import pytest

from charts import build_elevation_data, elevation_profile_chart, readiness_gauge_chart, risk_heatmap_chart

_RISK_SCORES = {
    "Fitness risk": 12,
    "Altitude risk": 8,
    "Weather risk": 15,
    "Logistics risk": 5,
    "Gear risk": 10,
}

_ROUTE = {
    "route_name": "Test Route",
    "max_elevation_m": 1200,
    "elevation_gain_m": 800,
}

# Rest day at index 1 — well away from the peak (index ~2)
_ITINERARY = [
    {"day": 1, "route_segment": "Start", "elevation_gain_m": 200, "difficulty_rating": "Moderate"},
    {"day": 2, "route_segment": "Rest camp", "elevation_gain_m": 0, "difficulty_rating": "Rest"},
    {"day": 3, "route_segment": "Ascent", "elevation_gain_m": 300, "difficulty_rating": "Hard"},
    {"day": 4, "route_segment": "Descent", "elevation_gain_m": 200, "difficulty_rating": "Moderate"},
    {"day": 5, "route_segment": "End", "elevation_gain_m": 100, "difficulty_rating": "Easy"},
]


# ── risk_heatmap_chart ────────────────────────────────────────────────────────

class TestRiskHeatmapChart:
    def test_returns_altair_chart(self):
        assert isinstance(risk_heatmap_chart(_RISK_SCORES), alt.Chart)

    def test_chart_data_has_five_rows(self):
        assert len(risk_heatmap_chart(_RISK_SCORES).data) == 5

    def test_chart_data_contains_all_dimensions(self):
        chart = risk_heatmap_chart(_RISK_SCORES)
        assert set(chart.data["dimension"]) == set(_RISK_SCORES.keys())

    def test_scores_match_input(self):
        chart = risk_heatmap_chart(_RISK_SCORES)
        for _, row in chart.data.iterrows():
            assert row["score"] == _RISK_SCORES[row["dimension"]]


# ── readiness_gauge_chart ─────────────────────────────────────────────────────

class TestReadinessGaugeChart:
    def test_returns_altair_chart(self):
        assert isinstance(readiness_gauge_chart(75), alt.Chart)

    def test_score_stored_in_data(self):
        assert readiness_gauge_chart(63).data["score"].iloc[0] == 63

    def test_score_zero(self):
        assert readiness_gauge_chart(0).data["score"].iloc[0] == 0

    def test_score_100(self):
        assert readiness_gauge_chart(100).data["score"].iloc[0] == 100


# ── build_elevation_data ──────────────────────────────────────────────────────
# Test the DataFrame builder directly — Altair layer internals aren't public API.

class TestBuildElevationData:
    def test_returns_none_when_max_elevation_zero(self):
        assert build_elevation_data(_ITINERARY, {**_ROUTE, "max_elevation_m": 0}) is None

    def test_returns_none_for_empty_itinerary(self):
        assert build_elevation_data([], _ROUTE) is None

    def test_one_row_per_itinerary_day(self):
        df = build_elevation_data(_ITINERARY, _ROUTE)
        assert len(df) == len(_ITINERARY)

    def test_elevation_never_exceeds_max(self):
        df = build_elevation_data(_ITINERARY, _ROUTE)
        assert df["elevation_m"].max() <= _ROUTE["max_elevation_m"]

    def test_rest_day_holds_previous_elevation(self):
        df = build_elevation_data(_ITINERARY, _ROUTE)
        day1_elev = df[df["Day"] == "Day 1"]["elevation_m"].iloc[0]
        day2_elev = df[df["Day"] == "Day 2"]["elevation_m"].iloc[0]
        assert day1_elev == day2_elev  # Day 2 is a rest day

    def test_start_elevation_above_zero(self):
        df = build_elevation_data(_ITINERARY, _ROUTE)
        assert df["elevation_m"].iloc[0] > 0

    def test_exactly_one_peak_point(self):
        df = build_elevation_data(_ITINERARY, _ROUTE)
        assert df["is_peak"].sum() == 1

    def test_peak_does_not_fall_on_rest_day(self):
        df = build_elevation_data(_ITINERARY, _ROUTE)
        peak_row = df[df["is_peak"]]
        day_num = int(peak_row["Day"].iloc[0].split()[-1])
        itinerary_dict = {d["day"]: d for d in _ITINERARY}
        assert itinerary_dict[day_num]["difficulty_rating"] != "Rest"

    def test_all_days_present(self):
        df = build_elevation_data(_ITINERARY, _ROUTE)
        assert set(df["Day"]) == {f"Day {d['day']}" for d in _ITINERARY}

    def test_all_rest_days_treated_as_rest(self):
        all_rest = [
            {"day": i + 1, "route_segment": "Rest", "elevation_gain_m": 0, "difficulty_rating": "Rest"}
            for i in range(4)
        ]
        df = build_elevation_data(all_rest, _ROUTE)
        assert df is not None  # should still return a DataFrame

    def test_single_day_itinerary(self):
        one_day = [{"day": 1, "route_segment": "A to B", "elevation_gain_m": 500, "difficulty_rating": "Hard"}]
        df = build_elevation_data(one_day, _ROUTE)
        assert len(df) == 1
        assert df["is_peak"].iloc[0] is True or df["is_peak"].sum() == 1


# ── elevation_profile_chart ───────────────────────────────────────────────────

class TestElevationProfileChart:
    def test_returns_layer_chart_when_data_present(self):
        assert isinstance(elevation_profile_chart(_ITINERARY, _ROUTE), alt.LayerChart)

    def test_returns_none_when_no_elevation(self):
        assert elevation_profile_chart(_ITINERARY, {**_ROUTE, "max_elevation_m": 0}) is None

    def test_returns_none_for_empty_itinerary(self):
        assert elevation_profile_chart([], _ROUTE) is None
