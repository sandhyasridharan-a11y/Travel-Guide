import json
from datetime import date, timedelta
from unittest.mock import MagicMock, patch

import pytest

from weather_client import fetch_forecast, weather_icon

_SAMPLE_RESPONSE = {
    "daily": {
        "time": ["2026-06-02", "2026-06-03", "2026-06-04"],
        "temperature_2m_max": [8.1, 6.5, 5.0],
        "temperature_2m_min": [1.2, 0.5, -1.0],
        "precipitation_probability_max": [20, 65, 85],
        "windspeed_10m_max": [30.0, 45.0, 60.0],
    }
}


def _mock_urlopen(payload):
    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps(payload).encode()
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    return MagicMock(return_value=mock_resp)


# ── fetch_forecast ────────────────────────────────────────────────────────────

class TestFetchForecast:
    def test_returns_one_dict_per_day(self):
        with patch("urllib.request.urlopen", _mock_urlopen(_SAMPLE_RESPONSE)):
            result = fetch_forecast(-51.03, -73.05, date(2026, 6, 2), 3)
        assert len(result) == 3

    def test_dict_has_expected_keys(self):
        with patch("urllib.request.urlopen", _mock_urlopen(_SAMPLE_RESPONSE)):
            result = fetch_forecast(-51.03, -73.05, date(2026, 6, 2), 3)
        day = result[0]
        assert "date" in day
        assert "temp_min_c" in day
        assert "temp_max_c" in day
        assert "precipitation_probability" in day
        assert "windspeed_kmh" in day

    def test_values_are_mapped_correctly(self):
        with patch("urllib.request.urlopen", _mock_urlopen(_SAMPLE_RESPONSE)):
            result = fetch_forecast(-51.03, -73.05, date(2026, 6, 2), 3)
        assert result[0]["date"] == "2026-06-02"
        assert result[0]["temp_max_c"] == 8.1
        assert result[0]["temp_min_c"] == 1.2
        assert result[0]["precipitation_probability"] == 20
        assert result[0]["windspeed_kmh"] == 30.0

    def test_returns_empty_list_on_api_failure(self):
        with patch("urllib.request.urlopen", side_effect=Exception("timeout")):
            result = fetch_forecast(-51.03, -73.05, date(2026, 6, 2), 3)
        assert result == []

    def test_returns_empty_list_for_past_dates(self):
        past = date.today() - timedelta(days=5)
        result = fetch_forecast(-51.03, -73.05, past, 3)
        assert result == []

    def test_returns_empty_list_for_far_future_dates(self):
        far_future = date.today() + timedelta(days=30)
        result = fetch_forecast(-51.03, -73.05, far_future, 5)
        assert result == []

    def test_returns_empty_list_when_daily_missing(self):
        with patch("urllib.request.urlopen", _mock_urlopen({})):
            result = fetch_forecast(-51.03, -73.05, date(2026, 6, 2), 3)
        assert result == []

    def test_handles_partial_data_gracefully(self):
        partial = {
            "daily": {
                "time": ["2026-06-02"],
                "temperature_2m_max": [7.0],
                # mins, precip, wind intentionally absent
            }
        }
        with patch("urllib.request.urlopen", _mock_urlopen(partial)):
            result = fetch_forecast(-51.03, -73.05, date(2026, 6, 2), 1)
        assert len(result) == 1
        assert result[0]["temp_min_c"] is None
        assert result[0]["precipitation_probability"] is None
        assert result[0]["windspeed_kmh"] is None


# ── weather_icon ──────────────────────────────────────────────────────────────

class TestWeatherIcon:
    def test_heavy_rain_threshold(self):
        assert weather_icon(70, 20) == "🌧"
        assert weather_icon(100, 0) == "🌧"

    def test_light_rain_threshold(self):
        assert weather_icon(40, 20) == "🌦"
        assert weather_icon(69, 20) == "🌦"

    def test_high_wind_no_rain(self):
        assert weather_icon(10, 50) == "🌬"
        assert weather_icon(0, 80) == "🌬"

    def test_clear_conditions(self):
        assert weather_icon(10, 20) == "🌤"
        assert weather_icon(0, 0) == "🌤"

    def test_none_inputs_return_clear(self):
        assert weather_icon(None, None) == "🌤"

    def test_precip_takes_priority_over_wind(self):
        # High precip + high wind → rain icon, not wind icon
        assert weather_icon(80, 60) == "🌧"


# ── derive_weather_condition ──────────────────────────────────────────────────

from weather_client import derive_weather_condition


class TestDeriveWeatherCondition:
    def test_stable_when_low_precip(self):
        data = {
            "2026-06-01": {"precipitation_probability": 10},
            "2026-06-02": {"precipitation_probability": 15},
            "2026-06-03": {"precipitation_probability": 20},
        }
        assert derive_weather_condition(data) == "Stable"

    def test_mixed_when_moderate_precip(self):
        data = {
            "2026-06-01": {"precipitation_probability": 30},
            "2026-06-02": {"precipitation_probability": 40},
        }
        assert derive_weather_condition(data) == "Mixed"

    def test_unstable_when_high_precip(self):
        data = {
            "2026-06-01": {"precipitation_probability": 60},
            "2026-06-02": {"precipitation_probability": 75},
        }
        assert derive_weather_condition(data) == "Unstable"

    def test_boundary_25_is_mixed(self):
        data = {"2026-06-01": {"precipitation_probability": 25}}
        assert derive_weather_condition(data) == "Mixed"

    def test_boundary_55_is_unstable(self):
        data = {"2026-06-01": {"precipitation_probability": 55}}
        assert derive_weather_condition(data) == "Unstable"

    def test_returns_none_for_empty_dict(self):
        assert derive_weather_condition({}) is None

    def test_ignores_days_with_no_precip_data(self):
        data = {
            "2026-06-01": {"precipitation_probability": None},
            "2026-06-02": {"precipitation_probability": 10},
        }
        assert derive_weather_condition(data) == "Stable"

    def test_returns_none_when_all_precip_none(self):
        data = {
            "2026-06-01": {"precipitation_probability": None},
            "2026-06-02": {},
        }
        assert derive_weather_condition(data) is None
