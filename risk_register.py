def build_mitigation_plan(risk_scores, route, trip_profile):
    plan = []

    if risk_scores.get("Fitness risk", 0) >= 12:
        plan.append("Increase training focus on long-distance hiking, hill repeats, and endurance before departure.")
    else:
        plan.append("Maintain current conditioning and allow recovery between multi-day segments.")

    if risk_scores.get("Altitude risk", 0) >= 12:
        plan.append("Include acclimatization time, monitor symptoms, and carry altitude medication or oxygen if needed.")
    else:
        plan.append("Plan gradual elevation gains and stay hydrated for altitude comfort.")

    if risk_scores.get("Weather risk", 0) >= 12:
        plan.append("Prepare for variable weather with layered clothing, waterproof gear, and a flexible itinerary.")
    else:
        plan.append("Check forecast updates daily and pack weather-appropriate layers.")

    if risk_scores.get("Logistics risk", 0) >= 12:
        plan.append("Confirm permits, transport connections, and lodging reservations well in advance.")
    else:
        plan.append("Verify key logistics early and keep alternate travel options available.")

    if risk_scores.get("Gear risk", 0) >= 12:
        plan.append("Review gear weight and adequacy, prioritize critical cold-weather and shelter items.")
    else:
        plan.append("Finalize your kit with essential equipment and a lightweight backup plan.")

    return plan


def risk_register_summary(risk_scores):
    summary = []
    for dimension, score in risk_scores.items():
        severity = "Low"
        if score >= 15:
            severity = "High"
        elif score >= 10:
            severity = "Moderate"

        summary.append({
            "dimension": dimension,
            "score": score,
            "severity": severity,
        })
    return summary


def top_risk_drivers(risk_scores, limit=3):
    return sorted(risk_scores.items(), key=lambda item: item[1], reverse=True)[:limit]
