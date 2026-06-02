import streamlit as st
from urllib.parse import quote, unquote_plus

GUIDANCE_POINTS = {
    "Fitness risk": [
        "Build endurance with progressively longer day hikes.",
        "Train on terrain similar to the route, including hills and trails.",
        "Practice carrying at least 15 lbs on hikes to simulate pack load.",
    ],
    "Altitude risk": [
        "Schedule acclimatization time before high-altitude segments.",
        "Plan shorter days and gradual elevation gain when possible.",
        "Stay well hydrated and monitor altitude symptoms closely.",
    ],
    "Weather risk": [
        "Check the forecast frequently and plan flexible days.",
        "Pack layered insulation and waterproof outerwear.",
        "Build contingency plans for poor weather and slow travel.",
    ],
    "Logistics risk": [
        "Confirm permits, transportation, and lodging early.",
        "Use established entry points and avoid unnecessarily remote access.",
        "Consider supported or guided logistics if the route is complex.",
    ],
    "Gear risk": [
        "Verify your kit before departure and replace worn items.",
        "Balance weight and protection; avoid overly minimal packing.",
        "Carry backup essentials for shelter, warmth, and repairs.",
    ],
}


def build_guidance_link(dimension):
    return f"?page=guidance&focus={quote(dimension, safe='')}"


def normalize_focus(focus):
    if focus is None:
        return None
    return unquote_plus(focus)


def render_guidance_page(focus=None):
    focus = normalize_focus(focus)
    st.header("Risk reduction guidance")
    st.write(
        "Review practical ways to lower the highest-scoring risk dimensions. "
        "Use this page to improve route planning, logistics, gear, and overall readiness."
    )

    if focus and focus in GUIDANCE_POINTS:
        st.markdown(f"### Focus: {focus}")
        st.write("This section is highlighted because it was identified as a high-risk dimension.")
        st.markdown("---")
        for point in GUIDANCE_POINTS[focus]:
            st.write(f"- {point}")

        st.markdown("---")
        st.subheader("Other guidance")
        for dimension, bullets in GUIDANCE_POINTS.items():
            if dimension == focus:
                continue
            with st.expander(dimension):
                for point in bullets:
                    st.write(f"- {point}")
    else:
        for dimension, bullets in GUIDANCE_POINTS.items():
            st.subheader(dimension)
            for point in bullets:
                st.write(f"- {point}")
