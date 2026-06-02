def plan_day(day_index, route_segment, distance_km, elevation_gain_m, pace, trip_profile, risk_scores, is_rest_day=False):
    if is_rest_day:
        return {
            "day": day_index,
            "route_segment": f"Rest day at {route_segment}",
            "distance_km": 0,
            "elevation_gain_m": 0,
            "estimated_time_hrs": 0,
            "difficulty_rating": "Rest",
            "risk_notes": ["Scheduled recovery day to reduce overall strain."],
            "gear_reminders": ["Stay hydrated", "Use recovery nutrition", "Keep warm and comfortable"],
            "recovery_advice": "Take the day easy, stretch gently, and prioritize sleep and hydration.",
        }

    pace_speeds = {
        "Leisurely": 3.5,
        "Steady": 4.5,
        "Brisk": 5.5,
    }
    speed = pace_speeds.get(pace, 4.0)
    estimated_time_hrs = max(1.0, round(distance_km / speed, 1))

    difficulty_score = (distance_km / 20.0) * 5 + (elevation_gain_m / 800.0) * 5
    if trip_profile.get("lodging_type") in ["Campsite", "Mixed camping/refugio"]:
        difficulty_score += 1
    if pace == "Brisk":
        difficulty_score += 1
    elif pace == "Leisurely":
        difficulty_score -= 1

    if difficulty_score < 4:
        difficulty_rating = "Easy"
    elif difficulty_score < 8:
        difficulty_rating = "Moderate"
    else:
        difficulty_rating = "Hard"

    risk_notes = []
    if risk_scores.get("Fitness risk", 0) >= 15:
        risk_notes.append("This day will require strong endurance and conditioning.")
    if risk_scores.get("Altitude risk", 0) >= 15:
        risk_notes.append("Monitor altitude symptoms closely and pace yourself.")
    if risk_scores.get("Weather risk", 0) >= 15:
        risk_notes.append("Weather may be volatile—expect wind, rain, or cold.")
    if risk_scores.get("Logistics risk", 0) >= 15:
        risk_notes.append("Allow extra time for logistics and confirm all reservations ahead of time.")
    if risk_scores.get("Gear risk", 0) >= 15:
        risk_notes.append("Verify that your gear is adequate for the conditions and day length.")
    if not risk_notes:
        risk_notes.append("Standard day with manageable risk. Stay attentive to conditions.")

    gear_reminders = [
        "Pack layered clothing",
        "Carry enough water and snacks",
        "Bring sun protection and a first-aid kit",
    ]
    if risk_scores.get("Weather risk", 0) >= 15:
        gear_reminders.append("Add waterproof outerwear and insulated layers")
    if risk_scores.get("Gear risk", 0) >= 12:
        gear_reminders.append("Review shelter and sleep system for comfort and safety")
    if trip_profile.get("pack_weight_preference") in ["Minimal", "Light"]:
        gear_reminders.append("Balance lightweight gear with essential safety items")

    recovery_advice = "Stretch, hydrate, and recharge after the hike."
    if estimated_time_hrs >= 7:
        recovery_advice = "Spend extra time recovering after the hike: foam roll, hydrate, and eat a higher-protein meal."
    if difficulty_rating == "Hard":
        recovery_advice += " Take it easy in the evening and rest well."

    return {
        "day": day_index,
        "route_segment": route_segment,
        "distance_km": round(distance_km, 1),
        "elevation_gain_m": int(elevation_gain_m),
        "estimated_time_hrs": estimated_time_hrs,
        "difficulty_rating": difficulty_rating,
        "risk_notes": risk_notes,
        "gear_reminders": gear_reminders,
        "recovery_advice": recovery_advice,
    }
