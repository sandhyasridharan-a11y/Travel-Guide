"""
route_discovery.py — find trail profiles from OSM and Wikipedia.

discover_route(trail_name) is the single public entry point.
It checks the curated route_library first; only hits external APIs
when the trail is not already there.

Sources
-------
- Overpass API  (OSM)       coordinates + name confirmation  (no key required)
- Wikipedia API             description, distance, elevation, duration, difficulty
"""
from __future__ import annotations

import json
import re
import sys
import urllib.parse
import urllib.request

from route_library import ROUTES

_OVERPASS_URL = "https://overpass-api.de/api/interpreter"
_WIKI_API = "https://en.wikipedia.org/w/api.php"
_UA = "TrekReadyApp/1.0"
_TIMEOUT = 20


# ── Public entry points ───────────────────────────────────────────────────────

def suggest_routes(query: str) -> list[str]:
    """
    Return up to 5 candidate trail names for *query* (partial / keyword match).

    Sources, in order:
      1. route_library — any word in the query matches any word in a route name
      2. Wikipedia opensearch — autocomplete API handles partial words and typos

    Results are deduplicated; library hits come first.
    """
    suggestions: list[str] = []
    seen: set[str] = set()

    query_words = {w for w in query.lower().split() if len(w) > 2}
    for route in ROUTES:
        name_words = set(route["route_name"].lower().split())
        if query_words & name_words:
            suggestions.append(route["route_name"])
            seen.add(route["route_name"].lower())

    for title in _wiki_opensearch(query, limit=5):
        if title.lower() not in seen:
            suggestions.append(title)
            seen.add(title.lower())

    return suggestions[:5]


def discover_route(trail_name: str) -> dict | None:
    """
    Return a unified trail profile dict for *trail_name*.

    Resolution order:
      1. Exact / substring match in route_library.py  (no network calls)
      2. Wikipedia  →  description + numeric stats
      3. Overpass   →  route coordinates + name confirmation
      4. Merge both into a profile whose keys match route_library schema

    Returns None only when all three sources return nothing.
    The returned dict always contains every key in the route_library schema
    plus ``_source`` ("library" | "discovered") and ``_wiki_url`` (str | None).
    """
    library_hit = _library_lookup(trail_name)
    if library_hit:
        return library_hit

    wiki = _fetch_wikipedia(trail_name)
    osm = _fetch_osm(trail_name)

    if not wiki and not osm:
        return None

    return _build_profile(trail_name, osm, wiki)


# ── Library lookup ────────────────────────────────────────────────────────────

def _library_lookup(trail_name: str) -> dict | None:
    query = trail_name.lower().strip()
    # 1. Exact case-insensitive match
    for route in ROUTES:
        if route["route_name"].lower() == query:
            return {**route, "_source": "library", "_wiki_url": None}
    # 2. Substring: query inside route name or route name inside query
    for route in ROUTES:
        name_lower = route["route_name"].lower()
        if query in name_lower or name_lower in query:
            return {**route, "_source": "library", "_wiki_url": None}
    return None


# ── Overpass (OSM) ────────────────────────────────────────────────────────────

def _fetch_osm(trail_name: str) -> dict | None:
    """
    Returns a dict with keys: lat, lon, osm_name, osm_distance_km.
    Tries ``name:en`` first (faster, avoids false positives), then ``name``.
    """
    escaped = trail_name.replace('"', '\\"')
    for tag in ("name:en", "name"):
        query = (
            f'[out:json][timeout:{_TIMEOUT}];'
            f'relation["route"~"hiking|foot"]["{tag}"~"{escaped}",i];'
            f'out center 3;'
        )
        result = _overpass_post(query)
        if result is None:
            continue
        elements = result.get("elements", [])
        if not elements:
            continue
        el = elements[0]
        center = el.get("center", {})
        tags = el.get("tags", {})
        return {
            "lat": center.get("lat"),
            "lon": center.get("lon"),
            "osm_name": tags.get("name:en") or tags.get("name"),
            "osm_distance_km": _parse_number(tags.get("distance") or tags.get("length")),
        }
    return None


def _overpass_post(query: str) -> dict | None:
    try:
        data = urllib.parse.urlencode({"data": query}).encode()
        req = urllib.request.Request(_OVERPASS_URL, data=data)
        req.add_header("Content-Type", "application/x-www-form-urlencoded")
        req.add_header("User-Agent", _UA)
        with urllib.request.urlopen(req, timeout=_TIMEOUT + 5) as resp:
            return json.loads(resp.read())
    except Exception as exc:
        print(f"[route_discovery] Overpass error: {exc}", file=sys.stderr)
        return None


# ── Wikipedia ─────────────────────────────────────────────────────────────────

def _fetch_wikipedia(trail_name: str) -> dict | None:
    """
    Returns a dict with keys: wiki_title, wiki_url, description, lat, lon,
    distance_km, elevation_gain_m, duration_days, difficulty, best_season.
    """
    title = _wiki_search(trail_name)
    if not title:
        return None

    params = urllib.parse.urlencode({
        "action": "query",
        "prop": "extracts|coordinates",
        "exintro": 1,
        "explaintext": 1,
        "titles": title,
        "format": "json",
    })
    try:
        req = urllib.request.Request(f"{_WIKI_API}?{params}")
        req.add_header("User-Agent", _UA)
        with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
            data = json.loads(resp.read())
        page = next(iter(data.get("query", {}).get("pages", {}).values()))
        extract = page.get("extract", "") or ""
        coords = (page.get("coordinates") or [{}])[0]
        return {
            "wiki_title": title,
            "wiki_url": f"https://en.wikipedia.org/wiki/{urllib.parse.quote(title.replace(' ', '_'))}",
            "description": extract[:600].strip(),
            "lat": coords.get("lat"),
            "lon": coords.get("lon"),
            "distance_km": _parse_distance_km(extract),
            "elevation_gain_m": _parse_elevation_m(extract),
            "duration_days": _parse_duration_days(extract),
            "difficulty": _parse_difficulty(extract),
            "best_season": _parse_season(extract),
        }
    except Exception as exc:
        print(f"[route_discovery] Wikipedia fetch error: {exc}", file=sys.stderr)
        return None


def _wiki_opensearch(query: str, limit: int = 3) -> list[str]:
    """Return Wikipedia page title suggestions for *query* (opensearch API)."""
    params = urllib.parse.urlencode({
        "action": "opensearch",
        "search": query,
        "limit": limit,
        "namespace": 0,
        "format": "json",
    })
    try:
        req = urllib.request.Request(f"{_WIKI_API}?{params}")
        req.add_header("User-Agent", _UA)
        with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
            results = json.loads(resp.read())
        return results[1]
    except Exception as exc:
        print(f"[route_discovery] Wikipedia opensearch error: {exc}", file=sys.stderr)
        return []


def _wiki_search(trail_name: str) -> str | None:
    """
    Returns the best-matching Wikipedia page title, or None.
    Tries the exact name first, then a simplified variant (drop generic words).
    """
    for query in _wiki_search_variants(trail_name):
        titles = _wiki_opensearch(query, limit=3)
        if titles:
            return titles[0]
    return None


def _wiki_search_variants(trail_name: str) -> list[str]:
    """Generate search query variants from most to least specific."""
    variants = [trail_name]
    # Drop common generic suffixes/prefixes that confuse Wikipedia search
    stripped = re.sub(r'\b(trek|trail|route|path|way|circuit|loop)\b', '', trail_name, flags=re.I).strip()
    if stripped and stripped.lower() != trail_name.lower():
        variants.append(stripped)
    return variants


# ── Text parsers ──────────────────────────────────────────────────────────────

def _parse_distance_km(text: str) -> float | None:
    # Prefer km mentions; fall back to miles
    m = re.search(r'(\d[\d,]*(?:\.\d+)?)\s*(?:km|kilometres?|kilometers?)', text, re.I)
    if m:
        return float(m.group(1).replace(",", ""))
    m = re.search(r'(\d[\d,]*(?:\.\d+)?)\s*(?:mi|miles?)\b', text, re.I)
    if m:
        return round(float(m.group(1).replace(",", "")) * 1.60934, 1)
    return None


def _parse_elevation_m(text: str) -> int | None:
    # "1,500 m elevation gain", "4,921 ft of elevation gain/ascent"
    m = re.search(
        r'(\d[\d,]*)\s*(?:m|metres?|meters?)\s+(?:of\s+)?(?:elevation\s+)?(?:gain|ascent)',
        text, re.I,
    )
    if m:
        return int(m.group(1).replace(",", ""))
    m = re.search(
        r'(\d[\d,]*)\s*(?:ft|feet)\s+(?:of\s+)?(?:elevation\s+)?(?:gain|ascent)',
        text, re.I,
    )
    if m:
        return int(round(int(m.group(1).replace(",", "")) * 0.3048))
    return None


def _parse_duration_days(text: str) -> int | None:
    # "4 to 5 days" → 5, "5-day" → 5, "approximately 5 days" → 5
    m = re.search(r'(\d+)\s*(?:to|[-–])\s*(\d+)\s*days?', text, re.I)
    if m:
        return int(m.group(2))
    m = re.search(r'(\d+)[-\s]day', text, re.I)
    if m:
        return int(m.group(1))
    m = re.search(r'(\d+)\s*days?', text, re.I)
    if m:
        return int(m.group(1))
    return None


def _parse_difficulty(text: str) -> str | None:
    t = text.lower()
    if any(w in t for w in ("strenuous", "demanding", "very difficult", "challenging")):
        return "Hard"
    if any(w in t for w in ("moderate", "moderately difficult")):
        return "Moderate"
    if any(w in t for w in ("easy", "gentle", "beginner-friendly")):
        return "Easy"
    return None


def _parse_season(text: str) -> str | None:
    # No re.I — month names are naturally capitalised; re.I would cause [A-Z] to
    # match lowercase words like "is" that appear before the month name.
    m = re.search(
        r'best\s+(?:time|season|months?)\b[^.\n]{0,40}?'
        r'([A-Z][a-z]+(?:\s+(?:to|through|–|-)\s+[A-Z][a-z]+)?)',
        text,
    )
    return m.group(1).strip() if m else None


def _parse_number(value: str | None) -> float | None:
    if not value:
        return None
    try:
        return float(re.sub(r"[^\d.]", "", str(value)))
    except ValueError:
        return None


# ── Profile builder ───────────────────────────────────────────────────────────

def _build_profile(trail_name: str, osm: dict | None, wiki: dict | None) -> dict:
    """
    Merge OSM and Wikipedia data into a dict whose keys match route_library schema.
    OSM center coords take priority; Wikipedia coords used as fallback.
    """
    osm = osm or {}
    wiki = wiki or {}

    lat = osm.get("lat") or wiki.get("lat")
    lon = osm.get("lon") or wiki.get("lon")
    distance_km = osm.get("osm_distance_km") or wiki.get("distance_km") or 0
    duration_days = wiki.get("duration_days") or 1
    difficulty = wiki.get("difficulty") or "Moderate"

    # Wikipedia title is cleaner and in English; OSM names can be in local
    # language or include geographic qualifiers (e.g. "International
    # Appalachian Trail, Québec" instead of "Appalachian Trail").
    route_name = (
        wiki.get("wiki_title")
        or osm.get("osm_name")
        or trail_name
    )

    return {
        "route_name": route_name,
        "region": "",
        "difficulty": difficulty,
        "duration_days": duration_days,
        "distance_km": float(distance_km),
        "elevation_gain_m": wiki.get("elevation_gain_m") or 0,
        "max_elevation_m": 0,
        "highlights": "",
        "best_season": wiki.get("best_season") or "",
        "climate": "",
        "remoteness": "Unknown",
        "permit_required": False,
        "transport_complexity": "Unknown",
        "description": wiki.get("description") or "",
        "recommended_nights": max(0, duration_days - 1),
        "recommended_activities": [],
        "route_type": "",
        "recommended_fitness_level": difficulty,
        "lat": lat,
        "lon": lon,
        "base_elevation_m": None,   # unknown for discovered routes
        "image_url": None,
        "_source": "discovered",
        "_wiki_url": wiki.get("wiki_url"),
    }
