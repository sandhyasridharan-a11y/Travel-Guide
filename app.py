from __future__ import annotations

import streamlit as st
from datetime import date, timedelta
from route_library import ROUTES, get_route_by_name
from assumption_engine import propose_trip_profile
from trip_profile_editor import edit_trip_profile
from briefing_generator import generate_briefing
from export_utils import build_pdf_filename, pdf_bytes
from risk_engine import readiness_to_risk_label
from packing_engine import build_comprehensive_packing_plan
from scoring_model import (
    score_trip_risks, overall_readiness_score, top_risk_drivers,
    adjust_gear_risk_for_warnings, apply_guided_adjustments,
)
from risk_register import risk_register_summary, build_mitigation_plan
from risk_guidance import render_guidance_page
from itinerary_generator import generate_itinerary
from charts import risk_heatmap_chart, elevation_profile_chart
from ai_layer import generate_risk_summary, generate_briefing_narrative, generate_personalized_recommendations
from weather_client import fetch_forecast, weather_icon, derive_weather_condition
from route_discovery import discover_route, suggest_routes
from map_view import build_route_map, fetch_osm_track

st.set_page_config(page_title="Trek Ready", layout="wide")

# ── Risk color helpers ────────────────────────────────────────────────────────

_RISK_ICONS = {
    "Low": "🟢",
    "Moderate": "🟡",
    "High": "🟠",
    "Very High": "🔴",
    "Extreme": "⛔",
}
_DIFF_ICONS = {"Easy": "🟢", "Moderate": "🟡", "Hard": "🟠", "Rest": "💤"}


def _risk_label(level):
    return f"{_RISK_ICONS.get(level, '⚪')} {level}"


def _score_icon(score, max_score=20):
    pct = score / max_score
    if pct < 0.35:
        return "🟢"
    elif pct < 0.55:
        return "🟡"
    elif pct < 0.75:
        return "🟠"
    return "🔴"


# ── Cached AI helpers (keyed on inputs so sidebar changes don't re-call) ─────
# ttl=3600 prevents a failed None result from being cached permanently across
# the session — if the API key wasn't ready on the first run, a reload retries.

@st.cache_data(show_spinner=False, ttl=3600)
def _ai_risk_summary(risk_scores, user_profile):
    return generate_risk_summary(dict(risk_scores), dict(user_profile))


@st.cache_data(show_spinner=False, ttl=3600)
def _ai_recommendations(risk_scores, user_profile, route_name):
    return generate_personalized_recommendations(
        dict(risk_scores), dict(user_profile), {"route_name": route_name}
    )


@st.cache_data(show_spinner=False, ttl=3600)
def _ai_briefing_narrative(trip_summary):
    return generate_briefing_narrative(dict(trip_summary))


_AI_UNAVAILABLE = "AI narrative unavailable — add ANTHROPIC_API_KEY to .env to enable."

_WEATHER_OPTIONS = ["Stable", "Mixed", "Unstable"]


@st.cache_data(ttl=3600)
def _cached_forecast(lat, lon, start_date_iso, num_days):
    return fetch_forecast(lat, lon, date.fromisoformat(start_date_iso), num_days)


@st.cache_data(ttl=3600, show_spinner=False)
def _cached_discover(trail_name: str):
    return discover_route(trail_name)


@st.cache_data(ttl=86400, show_spinner=False)  # OSM tracks change rarely; cache 24 h
def _cached_osm_track(route_name: str, lat: float | None, lon: float | None):
    return fetch_osm_track(route_name, lat=lat, lon=lon)


@st.cache_data(ttl=300, show_spinner=False)
def _cached_suggest(query: str):
    return suggest_routes(query)


# ── Query params (focus only — tabs own page navigation) ─────────────────────

_raw_focus = st.query_params.get("focus", None)
focus_value = (_raw_focus[0] if isinstance(_raw_focus, list) else _raw_focus) or None

# ── Sidebar ───────────────────────────────────────────────────────────────────

if "discovered_routes" not in st.session_state:
    st.session_state["discovered_routes"] = {}

with st.sidebar:
    st.markdown("## 🥾 Trek Ready")

    # ── Route selector ────────────────────────────────────────────────────────
    library_names = [r["route_name"] for r in ROUTES]
    discovered_names = list(st.session_state["discovered_routes"].keys())
    all_route_names = library_names + discovered_names

    selected_route_name = st.selectbox("Route", all_route_names)

    # Resolve route: library first, then discovered cache
    route = get_route_by_name(selected_route_name)
    if route is None:
        route = st.session_state["discovered_routes"].get(selected_route_name)

    # ── Trail search ──────────────────────────────────────────────────────────
    with st.expander("🔍 Search for a trail", expanded=False):
        search_input = st.text_input(
            "Keywords", placeholder="e.g. mont blanc, inca, milford, nepal"
        )

        if search_input.strip():
            with st.spinner("Finding matches…"):
                suggestions = _cached_suggest(search_input.strip())

            existing = set(library_names + discovered_names)
            new_suggestions = [s for s in suggestions if s not in existing]
            already_have = [s for s in suggestions if s in existing]

            for name in already_have:
                st.caption(f"✓ {name} — already in your route list")

            if not new_suggestions and not already_have:
                st.caption("No matches found. Try different keywords.")
            elif new_suggestions:
                chosen = st.selectbox(
                    "Select a trail to add:", new_suggestions, key="trail_suggestion"
                )
                if st.button("➕ Add to routes", use_container_width=True):
                    with st.spinner(f'Loading "{chosen}"…'):
                        result = _cached_discover(chosen)
                    if result is None:
                        st.warning("Could not load trail data. Try again.")
                    elif result["_source"] == "library":
                        st.info("This trail is already in your route list.")
                    else:
                        st.session_state["discovered_routes"][result["route_name"]] = result
                        st.rerun()

    st.markdown("---")

    exp_col, info_col = st.columns([5, 1])
    with exp_col:
        experience = st.selectbox("Experience level", ["Beginner", "Intermediate", "Advanced"])
    with info_col:
        st.write("")
        with st.popover("ℹ️"):
            st.markdown("**Beginner**  \nUnder ~10 mi/day, limited elevation and pack weight training.")
            st.markdown("**Intermediate**  \nSome multi-day treks, moderate elevation, 10–15 lb pack comfort.")
            st.markdown("**Advanced**  \n20+ mi/day, 0–10k ft elevation, comfortable with 15+ lb pack.")

    trip_start_date = st.date_input("Trip start date", value=date.today())

    # Auto-derive weather from forecast; fall back to manual when outside the
    # 16-day window or when the route has no coordinates.
    _prelim_lat = route.get("lat")
    _prelim_lon = route.get("lon")
    if _prelim_lat and _prelim_lon:
        _prelim_forecast = _cached_forecast(
            _prelim_lat, _prelim_lon,
            trip_start_date.isoformat(),
            route.get("duration_days", 5),
        )
        _auto_weather = derive_weather_condition(
            {w["date"]: w for w in _prelim_forecast}
        )
    else:
        _auto_weather = None

    if _auto_weather:
        weather = st.selectbox(
            "Expected weather",
            _WEATHER_OPTIONS,
            index=_WEATHER_OPTIONS.index(_auto_weather),
        )
        st.caption(f"🌤 Auto-detected from forecast — override if needed")
    else:
        weather = st.selectbox("Expected weather", _WEATHER_OPTIONS)
        if _prelim_lat:
            st.caption("No forecast for these dates — set manually")

    st.markdown("---")

    default_profile = propose_trip_profile(route)
    with st.expander("⚙️ Customize trip", expanded=False):
        trip_profile = edit_trip_profile(default_profile)

if not route:
    st.error("Route data could not be loaded.")
    st.stop()

# ── Scoring pipeline ──────────────────────────────────────────────────────────

risk_scores = score_trip_risks(route, trip_profile, experience, weather)
risk_scores = apply_guided_adjustments(risk_scores, trip_profile)
packing_plan = build_comprehensive_packing_plan(
    route, trip_profile, experience, weather,
    trip_profile["pack_weight_preference"], risk_scores,
)
risk_scores = adjust_gear_risk_for_warnings(risk_scores, packing_plan["warnings"])
readiness_score = overall_readiness_score(risk_scores)
risk_score = readiness_to_risk_label(readiness_score)
itinerary = generate_itinerary(route, trip_profile, risk_scores)

# Weather forecast — keyed by date string so each day card can look up its day
_route_lat = route.get("lat")
_route_lon = route.get("lon")
_weather_by_date: dict[str, dict] = {}
if _route_lat is not None and _route_lon is not None:
    _forecast = _cached_forecast(
        _route_lat, _route_lon,
        trip_start_date.isoformat(),
        trip_profile["number_of_days"],
    )
    _weather_by_date = {w["date"]: w for w in _forecast}

briefing_markdown = generate_briefing(
    route, trip_profile, risk_scores, readiness_score, itinerary, packing_plan,
    top_drivers=top_risk_drivers(risk_scores),
)

# Shared context dicts for AI calls — built once, passed to cached helpers
_user_profile = {
    "experience_level": experience,
    "weather_condition": weather,
    "number_of_days": trip_profile["number_of_days"],
    "rest_days": trip_profile.get("rest_days", 0),
    "guided": trip_profile.get("guided_vs_self_guided", "Self-guided"),
    "pack_preference": trip_profile.get("pack_weight_preference", "Moderate"),
}
_trip_summary = {
    "route_name": route["route_name"],
    "region": route["region"],
    "distance_km": route["distance_km"],
    "elevation_gain_m": route["elevation_gain_m"],
    "number_of_days": trip_profile["number_of_days"],
    "experience_level": experience,
    "readiness_score": readiness_score,
    "risk_level": risk_score,
}

# ── Tabs ──────────────────────────────────────────────────────────────────────

tab_overview, tab_itinerary, tab_guidance = st.tabs(
    ["📋  Overview", "🗓  Itinerary", "🧭  Guidance"]
)

# ─────────────────────────────────────────────────────────────────────────────
# OVERVIEW TAB
# ─────────────────────────────────────────────────────────────────────────────
with tab_overview:

    # Hero image
    if route.get("image_url"):
        st.image(route["image_url"], use_container_width=True)

    # Route title + caption strip
    st.title(route["route_name"])
    if route.get("_source") == "discovered":
        wiki_url = route.get("_wiki_url")
        wiki_link = f" [Wikipedia]({wiki_url})" if wiki_url else ""
        st.info(
            f"This route was discovered automatically and may have incomplete data.{wiki_link}  \n"
            "Edit it via ⚙️ Customize trip or add it to route_library.py to fill in missing details."
        )
    st.caption(
        f"📍 {route['region']}  ·  "
        f"⛰ {route['difficulty']}  ·  "
        f"📏 {route['distance_km']} km  ·  "
        f"↑ {route['elevation_gain_m']} m  ·  "
        f"🗓 Best season: {route['best_season']}"
    )

    # ── Route map ─────────────────────────────────────────────────────────────
    with st.spinner("Loading trail map…"):
        _osm_track = _cached_osm_track(
            route["route_name"], route.get("lat"), route.get("lon")
        )
    _route_map = build_route_map(route, osm_track=_osm_track)
    if _route_map:
        try:
            from streamlit_folium import st_folium
            st_folium(_route_map, use_container_width=True, height=400, returned_objects=[])
            if _osm_track:
                st.caption("🗺 GPS track from OpenStreetMap contributors.")
            else:
                st.caption("🗺 Approximate waypoints shown — OSM track not available for this route.")
        except ImportError:
            st.caption("Install streamlit-folium to enable the route map.")

    st.markdown("---")

    # ── Hero metrics ──────────────────────────────────────────────────────────
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Readiness score", f"{readiness_score} / 100")
    m2.metric("Risk level", _risk_label(risk_score))
    m3.metric("Duration", f"{trip_profile['number_of_days']} days")
    m4.metric("Trip style", trip_profile["guided_vs_self_guided"])

    st.markdown("---")

    # ── Risk breakdown ────────────────────────────────────────────────────────
    st.subheader("Risk breakdown")
    rcols = st.columns(5)
    for col, (dim, score) in zip(rcols, risk_scores.items()):
        col.metric(dim.replace(" risk", ""), f"{_score_icon(score)} {score} / 20")

    st.altair_chart(risk_heatmap_chart(risk_scores), use_container_width=True)

    high_risks = [(dim, score) for dim, score in risk_scores.items() if score >= 15]
    if high_risks:
        st.subheader("⚠️ High-risk dimensions")
        st.caption("Switch to the Guidance tab for mitigation advice on these dimensions.")
        for dim, score in high_risks:
            st.error(f"{_score_icon(score)} **{dim}** — {score} / 20")

    st.markdown("---")

    # ── Download ──────────────────────────────────────────────────────────────
    st.subheader("📄 Expedition briefing")
    st.caption("Includes trip summary, risk register, itinerary, packing list, and emergency notes.")
    try:
        pdf_data = pdf_bytes(briefing_markdown, title=f"Expedition Briefing: {route['route_name']}")
        st.download_button(
            "⬇️ Download expedition briefing (PDF)",
            data=pdf_data,
            file_name=build_pdf_filename(route["route_name"], trip_profile),
            mime="application/pdf",
            use_container_width=True,
            type="primary",
        )
    except ImportError as exc:
        st.warning(str(exc))
    with st.expander("Preview briefing", expanded=False):
        st.code(briefing_markdown, language="markdown")

    st.markdown("---")

    # ── Packing ───────────────────────────────────────────────────────────────
    st.subheader("🎒 Packing recommendations")
    weight_kg = packing_plan["estimated_weight_kg"]
    st.metric("Estimated pack weight", f"{weight_kg:.1f} kg  ({weight_kg * 2.20462:.1f} lbs)")

    pcol1, pcol2 = st.columns(2)
    with pcol1:
        with st.expander(f"Must-have items ({len(packing_plan['must_haves'])})", expanded=True):
            for item in packing_plan["must_haves"]:
                st.write(f"- {item}")
        if packing_plan["optional"]:
            with st.expander(f"Optional items ({len(packing_plan['optional'])})", expanded=False):
                for item in packing_plan["optional"]:
                    st.write(f"- {item}")
    with pcol2:
        if packing_plan["risk_based_additions"]:
            with st.expander(
                f"Risk-based additions ({len(packing_plan['risk_based_additions'])})", expanded=True
            ):
                st.info("These items address high-risk dimensions in your profile.")
                for item in packing_plan["risk_based_additions"]:
                    st.write(f"- {item}")
        for warning in packing_plan["warnings"]:
            st.warning(warning)

    st.markdown("---")

    # ── Route details ─────────────────────────────────────────────────────────
    with st.expander("📍 About this route"):
        st.write(route["description"])
        st.markdown(
            f"- **Highlights:** {route['highlights']}  \n"
            f"- **Climate:** {route['climate']}  \n"
            f"- **Remoteness:** {route['remoteness']}  \n"
            f"- **Permit required:** {'Yes' if route.get('permit_required') else 'No'}  \n"
            f"- **Transport complexity:** {route['transport_complexity']}"
        )

    # ── AI insights (optional) ────────────────────────────────────────────────
    with st.expander("🤖 AI insights", expanded=False):
        st.markdown("**Risk summary**")
        with st.spinner("Generating…"):
            ai_summary = _ai_risk_summary(tuple(risk_scores.items()), tuple(_user_profile.items()))
        if ai_summary:
            st.info(ai_summary)
        else:
            st.caption(_AI_UNAVAILABLE)

        st.markdown("**Personalized recommendations**")
        with st.spinner("Generating…"):
            ai_recs = _ai_recommendations(
                tuple(risk_scores.items()), tuple(_user_profile.items()), route["route_name"]
            )
        if ai_recs:
            st.markdown(ai_recs)
        else:
            st.caption(_AI_UNAVAILABLE)

        st.markdown("**Briefing narrative**")
        with st.spinner("Generating…"):
            ai_narrative = _ai_briefing_narrative(tuple(sorted(_trip_summary.items())))
        if ai_narrative:
            st.markdown(ai_narrative)
        else:
            st.caption(_AI_UNAVAILABLE)


# ─────────────────────────────────────────────────────────────────────────────
# ITINERARY TAB
# ─────────────────────────────────────────────────────────────────────────────
with tab_itinerary:
    itin_title_col, itin_dl_col = st.columns([3, 1])
    itin_title_col.subheader(f"Daily itinerary — {route['route_name']}")
    try:
        pdf_data = pdf_bytes(briefing_markdown, title=f"Expedition Briefing: {route['route_name']}")
        itin_dl_col.download_button(
            "⬇️ Download PDF",
            data=pdf_data,
            file_name=build_pdf_filename(route["route_name"], trip_profile),
            mime="application/pdf",
            use_container_width=True,
        )
    except ImportError:
        pass

    # ── Elevation profile ─────────────────────────────────────────────────────
    elev_chart = elevation_profile_chart(itinerary, route)
    if elev_chart:
        st.altair_chart(elev_chart, use_container_width=True)
        st.markdown("---")

    # Day strip
    strip_cols = st.columns(len(itinerary))
    for col, day in zip(strip_cols, itinerary):
        diff = day["difficulty_rating"]
        icon = _DIFF_ICONS.get(diff, "⚪")
        day_date = trip_start_date + timedelta(days=day["day"] - 1)
        w = _weather_by_date.get(day_date.isoformat())
        wx = weather_icon(
            w.get("precipitation_probability") if w else None,
            w.get("windspeed_kmh") if w else None,
        )
        col.markdown(f"**Day {day['day']}**  \n{icon} {diff}  \n{wx}")

    st.markdown("---")

    for day in itinerary:
        diff = day["difficulty_rating"]
        icon = _DIFF_ICONS.get(diff, "⚪")
        day_date = trip_start_date + timedelta(days=day["day"] - 1)
        day_weather = _weather_by_date.get(day_date.isoformat())

        with st.expander(
            f"{icon}  Day {day['day']}: {day['route_segment']}", expanded=day["day"] == 1
        ):
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Distance", f"{day['distance_km']} km")
            c2.metric("Elevation", f"{day['elevation_gain_m']} m")
            c3.metric("Time", f"{day['estimated_time_hrs']} hrs")
            c4.metric("Difficulty", f"{icon} {diff}")

            if day_weather:
                wx = weather_icon(
                    day_weather.get("precipitation_probability"),
                    day_weather.get("windspeed_kmh"),
                )
                w1, w2, w3 = st.columns(3)
                t_min = day_weather.get("temp_min_c")
                t_max = day_weather.get("temp_max_c")
                precip = day_weather.get("precipitation_probability")
                wind = day_weather.get("windspeed_kmh")
                temp_str = (
                    f"{t_min:.0f}–{t_max:.0f} °C"
                    if t_min is not None and t_max is not None
                    else "—"
                )
                w1.metric(f"{wx} Temperature", temp_str)
                w2.metric("🌧 Precip. chance", f"{precip}%" if precip is not None else "—")
                w3.metric("💨 Wind", f"{wind:.0f} km/h" if wind is not None else "—")
            elif _route_lat is not None:
                st.caption("Weather forecast unavailable for this date — only the next 16 days are supported.")

            n_col, g_col = st.columns(2)
            with n_col:
                st.markdown("**Risk notes**")
                for note in day["risk_notes"]:
                    st.write(f"- {note}")
                st.markdown(f"**Recovery:** {day['recovery_advice']}")
            with g_col:
                st.markdown("**Gear reminders**")
                for reminder in day["gear_reminders"]:
                    st.write(f"- {reminder}")


# ─────────────────────────────────────────────────────────────────────────────
# GUIDANCE TAB
# ─────────────────────────────────────────────────────────────────────────────
with tab_guidance:

    # Risk summary row
    st.subheader("Risk summary")
    reg_cols = st.columns(5)
    for col, item in zip(reg_cols, risk_register_summary(risk_scores)):
        icon = _score_icon(item["score"])
        col.metric(
            item["dimension"].replace(" risk", ""),
            f"{icon} {item['severity']}",
            f"{item['score']} / 20",
        )

    st.markdown("---")

    render_guidance_page(focus_value)

    st.markdown("---")

    st.subheader("Your mitigation plan")
    for item in build_mitigation_plan(risk_scores, route, trip_profile):
        st.write(f"- {item}")
