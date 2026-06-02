from __future__ import annotations

import altair as alt
import pandas as pd

_RISK_COLOR_SCALE = alt.Scale(
    domain=[0, 7, 11, 15, 20],
    range=["#27ae60", "#f1c40f", "#e67e22", "#e74c3c", "#c0392b"],
)


def risk_heatmap_chart(risk_scores):
    data = pd.DataFrame([
        {"dimension": dimension, "score": score}
        for dimension, score in risk_scores.items()
    ])
    return (
        alt.Chart(data)
        .encode(
            y=alt.Y("dimension:N", sort="-x", title=None),
            x=alt.X("score:Q", title="Risk score (0–20)", scale=alt.Scale(domain=[0, 20])),
            color=alt.Color("score:Q", scale=_RISK_COLOR_SCALE, legend=None),
            tooltip=[
                alt.Tooltip("dimension:N", title="Dimension"),
                alt.Tooltip("score:Q", title="Score"),
            ],
        )
        .mark_bar(cornerRadiusTopRight=4, cornerRadiusBottomRight=4)
        .properties(height=180)
    )


def build_elevation_data(itinerary: list, route: dict) -> pd.DataFrame | None:
    """
    Build the per-day elevation DataFrame used by elevation_profile_chart.
    Extracted as a separate function so it can be tested independently.

    Returns None when the route has no elevation metadata or itinerary is empty.
    """
    max_elev = route.get("max_elevation_m", 0)
    total_gain = route.get("elevation_gain_m", 0)
    if not max_elev or not itinerary:
        return None

    # Prefer the curated trailhead altitude; fall back to deriving it from
    # max elevation minus total gain (works when gain ≤ max, otherwise clamps to 0).
    base_elev = route.get("base_elevation_m") or max(0, max_elev - total_gain)
    n = len(itinerary)
    peak_idx = max(0, int(n * 0.6) - 1)
    # Advance past rest days so the peak label always lands on a hiking day
    while peak_idx < n and itinerary[peak_idx].get("difficulty_rating") == "Rest":
        peak_idx += 1
    if peak_idx >= n:
        peak_idx = n - 1

    rows = []
    for i, day in enumerate(itinerary):
        if day.get("difficulty_rating") == "Rest":
            elev = rows[-1]["elevation_m"] if rows else base_elev
        elif i <= peak_idx:
            progress = (i + 1) / (peak_idx + 1) if peak_idx > 0 else 1.0
            elev = base_elev + (max_elev - base_elev) * progress
        else:
            remaining = n - peak_idx - 1
            descent = (i - peak_idx) / remaining if remaining > 0 else 1.0
            elev = max_elev - (max_elev - base_elev) * descent

        rows.append({
            "Day": f"Day {day['day']}",
            "elevation_m": round(elev),
            "segment": day["route_segment"],
            "is_peak": i == peak_idx and day.get("difficulty_rating") != "Rest",
        })

    return pd.DataFrame(rows)


def elevation_profile_chart(itinerary: list, route: dict) -> alt.LayerChart | None:
    """
    Simulated elevation profile across trek days.

    Builds a bell-curve approximation: ascend to max_elevation_m at ~60% of
    the trip, then descend. Rest days hold the previous day's elevation.
    Labelled as simulated since per-day terrain data isn't available.
    Returns None when the route lacks elevation metadata.
    """
    df = build_elevation_data(itinerary, route)
    if df is None:
        return None

    max_elev = route.get("max_elevation_m", 0)
    total_gain = route.get("elevation_gain_m", 0)
    peak_df = df[df["is_peak"]]

    x_enc = alt.X("Day:O", sort=None, axis=alt.Axis(labelAngle=-30, title=None))
    y_enc = alt.Y(
        "elevation_m:Q",
        title="Elevation (m)",
        scale=alt.Scale(zero=False),
        axis=alt.Axis(format=","),
    )

    area = (
        alt.Chart(df)
        .mark_area(color="#4A90D9", opacity=0.25)
        .encode(x=x_enc, y=y_enc)
    )
    line = (
        alt.Chart(df)
        .mark_line(color="#2171B5", strokeWidth=2.5)
        .encode(
            x=x_enc,
            y=y_enc,
            tooltip=[
                alt.Tooltip("Day:O"),
                alt.Tooltip("segment:N", title="Segment"),
                alt.Tooltip("elevation_m:Q", title="Elevation (m)", format=","),
            ],
        )
    )
    points = (
        alt.Chart(df)
        .mark_point(color="#2171B5", size=50, filled=True)
        .encode(x=x_enc, y=y_enc)
    )
    peak_point = (
        alt.Chart(peak_df)
        .mark_point(color="#E8474C", size=130, filled=True)
        .encode(x=x_enc, y=y_enc)
    )
    peak_label = (
        alt.Chart(peak_df)
        .mark_text(dy=-14, color="#E8474C", fontWeight="bold", fontSize=12)
        .encode(
            x=x_enc,
            y=y_enc,
            text=alt.Text("elevation_m:Q", format=","),
        )
    )

    return (area + line + points + peak_point + peak_label).properties(
        height=240,
        title=alt.TitleParams(
            text=f"Elevation profile  ·  highest point {max_elev:,} m",
            subtitle=f"Simulated from route data  ·  total gain {total_gain:,} m",
            fontSize=13,
            subtitleFontSize=11,
            subtitleColor="#888",
        ),
    )


def readiness_gauge_chart(readiness_score):
    data = pd.DataFrame([{"label": "Readiness", "score": readiness_score}])
    return (
        alt.Chart(data)
        .mark_bar()
        .encode(
            x=alt.X("score:Q", scale=alt.Scale(domain=[0, 100]), title="Readiness"),
            y=alt.Y("label:N", title=""),
            color=alt.condition(alt.datum.score < 60, alt.value("#e74c3c"), alt.value("#27ae60")),
            tooltip=["score"],
        )
        .properties(height=80)
    )
