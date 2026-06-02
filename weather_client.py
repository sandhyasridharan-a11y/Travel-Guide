from __future__ import annotations

import json
import sys
import urllib.request
from datetime import date, timedelta

_FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
_FORECAST_WINDOW_DAYS = 16


def fetch_forecast(lat: float, lon: float, start_date: date, num_days: int) -> list[dict]:
    """
    Returns a list of daily weather dicts for the given location and date range.
    Returns an empty list when dates fall outside the 16-day forecast window or on API failure.

    Each dict contains:
      date                     – str (YYYY-MM-DD)
      temp_min_c               – float | None
      temp_max_c               – float | None
      precipitation_probability – int | None  (0–100)
      windspeed_kmh            – float | None
    """
    today = date.today()
    end_date = start_date + timedelta(days=num_days - 1)

    if start_date > today + timedelta(days=_FORECAST_WINDOW_DAYS) or end_date < today:
        return []

    params = "&".join([
        f"latitude={lat}",
        f"longitude={lon}",
        "daily=temperature_2m_max,temperature_2m_min,"
        "precipitation_probability_max,windspeed_10m_max",
        f"start_date={start_date.isoformat()}",
        f"end_date={end_date.isoformat()}",
        "timezone=auto",
    ])
    url = f"{_FORECAST_URL}?{params}"

    try:
        with urllib.request.urlopen(url, timeout=5) as resp:
            data = json.loads(resp.read())
        daily = data.get("daily", {})
        dates = daily.get("time", [])
        temps_max = daily.get("temperature_2m_max", [])
        temps_min = daily.get("temperature_2m_min", [])
        precip = daily.get("precipitation_probability_max", [])
        wind = daily.get("windspeed_10m_max", [])

        return [
            {
                "date": dates[i],
                "temp_min_c": temps_min[i] if i < len(temps_min) else None,
                "temp_max_c": temps_max[i] if i < len(temps_max) else None,
                "precipitation_probability": precip[i] if i < len(precip) else None,
                "windspeed_kmh": wind[i] if i < len(wind) else None,
            }
            for i in range(len(dates))
        ]
    except Exception as e:
        print(f"[weather_client] fetch failed: {e}", file=sys.stderr)
        return []


def weather_icon(precip_prob: int | None, windspeed_kmh: float | None) -> str:
    """Returns a weather emoji summarising the day's conditions."""
    if precip_prob is not None and precip_prob >= 70:
        return "🌧"
    if precip_prob is not None and precip_prob >= 40:
        return "🌦"
    if windspeed_kmh is not None and windspeed_kmh >= 50:
        return "🌬"
    return "🌤"


def derive_weather_condition(weather_by_date: dict) -> str | None:
    """
    Classify average trip-day precipitation into Stable / Mixed / Unstable.

    Thresholds: avg precip < 25% → Stable, 25–55% → Mixed, ≥ 55% → Unstable.
    Returns None when no precipitation data is available.
    """
    precip_values = [
        w["precipitation_probability"]
        for w in weather_by_date.values()
        if w.get("precipitation_probability") is not None
    ]
    if not precip_values:
        return None
    avg = sum(precip_values) / len(precip_values)
    if avg >= 55:
        return "Unstable"
    if avg >= 25:
        return "Mixed"
    return "Stable"
