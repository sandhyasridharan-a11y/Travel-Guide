from __future__ import annotations

import anthropic
import os
import sys

from dotenv import load_dotenv

# override=True ensures the .env file wins over any conflicting env var
# (e.g. Claude Code sets ANTHROPIC_API_KEY for its own auth; we need ours)
load_dotenv(override=True)


def _get_client():
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        # Fall back to Streamlit Cloud secrets when running deployed
        try:
            import streamlit as st
            api_key = st.secrets.get("ANTHROPIC_API_KEY")
        except Exception:
            pass
    if not api_key:
        return None
    return anthropic.Anthropic(api_key=api_key)


def _call(client, **kwargs) -> str | None:
    """Shared API call wrapper that logs errors to stderr instead of swallowing them."""
    try:
        message = client.messages.create(**kwargs)
        return message.content[0].text
    except Exception as e:
        print(f"[ai_layer] API call failed: {e}", file=sys.stderr)
        return None


def generate_risk_summary(risk_scores: dict, user_profile: dict) -> str | None:
    client = _get_client()
    if client is None:
        return None
    prompt = f"""You are a hiking safety expert. Based on the following risk scores and user profile,
write a 2-3 paragraph plain English summary explaining the top risks and what the hiker should do about them.

Risk Scores:
{risk_scores}

User Profile:
{user_profile}

Be specific, practical, and encouraging. Focus on the top 3 risks."""
    return _call(
        client,
        model="claude-haiku-4-5-20251001",
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}],
    )


def generate_personalized_recommendations(risk_scores: dict, user_profile: dict, route: dict) -> str | None:
    client = _get_client()
    if client is None:
        return None
    prompt = f"""You are a hiking coach. Based on this hiker's profile and risk scores for their planned trek,
give 4-5 specific, actionable recommendations to improve their readiness.

Route: {route.get('name', route.get('route_name', 'Unknown'))}
Risk Scores: {risk_scores}
User Profile: {user_profile}

Be direct and practical."""
    return _call(
        client,
        model="claude-haiku-4-5-20251001",
        max_tokens=400,
        messages=[{"role": "user", "content": prompt}],
    )


def generate_briefing_narrative(trip_summary: dict) -> str | None:
    client = _get_client()
    if client is None:
        return None
    prompt = f"""Write a compelling 1-paragraph expedition briefing introduction for this hiking trip.
Make it feel like a professional guide briefing — informative, confident, and motivating.

Trip details: {trip_summary}"""
    return _call(
        client,
        model="claude-haiku-4-5-20251001",
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}],
    )
