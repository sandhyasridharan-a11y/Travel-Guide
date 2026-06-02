from risk_register import risk_register_summary, top_risk_drivers


def _format_profile_section(trip_profile):
    lines = [
        f"- Number of days: {trip_profile.get('number_of_days')}",
        f"- Lodging type: {trip_profile.get('lodging_type')}",
        f"- Hiking pace: {trip_profile.get('hiking_pace')}",
        f"- Rest days: {trip_profile.get('rest_days')}",
        f"- Trip style: {trip_profile.get('guided_vs_self_guided')}",
        f"- Pack weight preference: {trip_profile.get('pack_weight_preference')}",
        f"- Season: {trip_profile.get('season')}",
    ]
    return "\n".join(lines)


def _format_route_profile(route):
    return "\n".join([
        f"- Region: {route.get('region')}",
        f"- Difficulty: {route.get('difficulty')}",
        f"- Distance: {route.get('distance_km')} km",
        f"- Elevation gain: {route.get('elevation_gain_m')} m",
        f"- Maximum elevation: {route.get('max_elevation_m', 'n/a')} m",
        f"- Climate: {route.get('climate')}",
        f"- Remoteness: {route.get('remoteness')}",
        f"- Best season: {route.get('best_season')}",
        f"- Permit required: {'Yes' if route.get('permit_required') else 'No'}",
        f"- Transport complexity: {route.get('transport_complexity')}",
    ])


def _format_risk_register(risk_register):
    lines = []
    for item in risk_register:
        lines.append(f"- {item['dimension']}: {item['severity']} ({item['score']}/20)")
    return "\n".join(lines)


def _format_itinerary(itinerary):
    lines = []
    for day in itinerary:
        lines.append(f"### Day {day['day']}: {day['route_segment']}")
        lines.append(f"- Distance: {day['distance_km']:.1f} km")
        lines.append(f"- Elevation gain: {day['elevation_gain_m']:.0f} m")
        lines.append(f"- Estimated time: {day['estimated_time_hrs']:.1f} hrs")
        lines.append(f"- Difficulty rating: {day['difficulty_rating']}")
        if day.get('risk_notes'):
            lines.append("- Risk notes:")
            for note in day['risk_notes']:
                lines.append(f"  - {note}")
        if day.get('gear_reminders'):
            lines.append("- Gear reminders:")
            for reminder in day['gear_reminders']:
                lines.append(f"  - {reminder}")
        if day.get('recovery_advice'):
            lines.append(f"- Recovery advice: {day['recovery_advice']}")
        lines.append("")
    return "\n".join(lines)


def _format_packing_list(packing_plan):
    lines = []
    lines.append("### Must-have items")
    for item in packing_plan.get('must_haves', []):
        lines.append(f"- {item}")
    if packing_plan.get('optional'):
        lines.append("\n### Optional items")
        for item in packing_plan['optional']:
            lines.append(f"- {item}")
    if packing_plan.get('risk_based_additions'):
        lines.append("\n### Risk-based additions")
        for item in packing_plan['risk_based_additions']:
            lines.append(f"- {item}")
    if packing_plan.get('warnings'):
        lines.append("\n### Packing warnings")
        for warning in packing_plan['warnings']:
            lines.append(f"- {warning}")
    lines.append(f"\nEstimated pack weight: {packing_plan.get('estimated_weight_kg', 0):.1f} kg")
    return "\n".join(lines)


def _format_logistics_checklist(route, trip_profile):
    lines = [
        "- Confirm permits and lodging reservations.",
        "- Review transport connections and contingency options.",
        "- Verify gear weight and pack distribution.",
        "- Pack navigation, communication, and first-aid gear.",
        "- Share itinerary with a trusted contact.",
        "- Check weather forecasts daily before departure.",
    ]
    if route.get('permit_required'):
        lines.append("- Carry copies of permits and official documents.")
    if trip_profile.get('guided_vs_self_guided', '').lower() == 'guided':
        lines.append("- Confirm guide meet-up details and local support plans.")
    if route.get('remoteness', '').lower() in ['high', 'remote']:
        lines.append("- Plan extra water, food, and emergency communication for remote terrain.")
    return "\n".join(lines)


def _format_emergency_notes(route, risk_scores):
    lines = [
        "- Prioritize first-aid readiness and blister care.",
        "- Carry emergency communication and know the nearest rescue contacts.",
        "- If altitude risk is elevated, ascend slowly and monitor symptoms.",
        "- In unstable weather, seek shelter early and keep waterproof layers accessible.",
        "- Keep a lightweight repair kit handy for equipment issues.",
    ]
    if risk_scores.get('Altitude risk', 0) >= 12:
        lines.append("- Review altitude sickness protocols and carry medication if needed.")
    if risk_scores.get('Weather risk', 0) >= 12:
        lines.append("- Bring extra insulation and rain protection for rapidly changing conditions.")
    if route.get('remoteness', '').lower() in ['high', 'remote']:
        lines.append("- Confirm emergency evacuation plans for remote sections.")
    return "\n".join(lines)


def generate_briefing(route, trip_profile, risk_scores, readiness_score, itinerary, packing_plan, *, top_drivers=None, risk_register=None):
    route_name = route.get('route_name', 'this route')
    if top_drivers is None:
        top_drivers = top_risk_drivers(risk_scores)
    if risk_register is None:
        risk_register = risk_register_summary(risk_scores)

    driver_text = ", ".join([f"{dimension} ({score}/20)" for dimension, score in top_drivers])
    briefing_sections = [
        f"# Expedition Briefing: {route_name}",
        "## Trip summary",
        f"- Route: {route_name}",
        f"- Total planned days: {trip_profile.get('number_of_days')}",
        f"- Rest days: {trip_profile.get('rest_days')}",
        f"- Risk assessment: {readiness_score}/100 readiness", 
        f"- Highest risk drivers: {driver_text}",
        "",
        "## Confirmed assumptions",
        _format_profile_section(trip_profile),
        "",
        "## Route profile",
        _format_route_profile(route),
        "",
        "## Readiness and risk",
        f"- Overall readiness score: {readiness_score}/100",
        f"- Risk rating: {risk_scores.get('Weather risk', 0)} weather, {risk_scores.get('Altitude risk', 0)} altitude, {risk_scores.get('Fitness risk', 0)} fitness, {risk_scores.get('Logistics risk', 0)} logistics, {risk_scores.get('Gear risk', 0)} gear.",
        f"- Top risk drivers: {driver_text}",
        "",
        "## Risk register",
        _format_risk_register(risk_register),
        "",
        "## Day-by-day itinerary",
        _format_itinerary(itinerary),
        "",
        "## Packing list",
        _format_packing_list(packing_plan),
        "",
        "## Logistics checklist",
        _format_logistics_checklist(route, trip_profile),
        "",
        "## Emergency notes",
        _format_emergency_notes(route, risk_scores),
    ]

    return "\n".join(briefing_sections)
