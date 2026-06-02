import streamlit as st


def edit_trip_profile(default_profile):
    lodging_options = [
        "Campsite",
        "Refugio/Campsite",
        "Backcountry hut",
        "Mixed camping/refugio",
        "Hotel",
    ]
    pace_options = ["Leisurely", "Steady", "Brisk"]
    guided_options = ["Self-guided", "Guided"]
    pack_options = ["Minimal", "Light", "Balanced", "Heavy"]

    number_of_days = st.number_input(
        "Number of days",
        min_value=1,
        max_value=60,
        value=default_profile.get("number_of_days", 1),
    )
    lodging_type = st.selectbox(
        "Preferred lodging type",
        lodging_options,
        index=lodging_options.index(default_profile.get("lodging_type", "Campsite"))
        if default_profile.get("lodging_type") in lodging_options
        else 0,
    )
    hiking_pace = st.selectbox(
        "Hiking pace",
        pace_options,
        index=pace_options.index(default_profile.get("hiking_pace", "Steady"))
        if default_profile.get("hiking_pace") in pace_options
        else 1,
    )
    rest_days = st.number_input(
        "Planned rest days",
        min_value=0,
        max_value=14,
        value=default_profile.get("rest_days", 0),
    )
    guided_vs_self_guided = st.radio(
        "Trip style",
        guided_options,
        index=guided_options.index(default_profile.get("guided_vs_self_guided", "Self-guided"))
        if default_profile.get("guided_vs_self_guided") in guided_options
        else 0,
        horizontal=True,
    )
    pack_weight_preference = st.selectbox(
        "Pack weight preference",
        pack_options,
        index=pack_options.index(default_profile.get("pack_weight_preference", "Balanced"))
        if default_profile.get("pack_weight_preference") in pack_options
        else 2,
    )

    return {
        "number_of_days": number_of_days,
        "lodging_type": lodging_type,
        "hiking_pace": hiking_pace,
        "rest_days": rest_days,
        "guided_vs_self_guided": guided_vs_self_guided,
        "pack_weight_preference": pack_weight_preference,
    }
