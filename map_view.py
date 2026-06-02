"""
map_view.py — Folium map builder for trek routes.

Resolution order for the trail polyline:
  1. Overpass API with out geom  →  real GPS-traced OSM way geometries
  2. Curated waypoints            →  approximate key stops (fallback)
  3. Centre marker only           →  when no geometry is available

build_route_map(route, itinerary) is the public entry point.
fetch_osm_track(route_name) is exposed so app.py can cache the result.
"""
from __future__ import annotations

import json
import sys
import urllib.parse
import urllib.request

import folium

_OVERPASS_URL = "https://overpass-api.de/api/interpreter"
_UA = "TrekReadyApp/1.0"
_TIMEOUT = 25
_MAX_TRACK_POINTS = 600   # downsample to keep the map responsive


# ── Curated waypoints (fallback when OSM geometry is unavailable) ─────────────

_WAYPOINTS: dict[str, list[dict]] = {
    "Patagonia W Trek": [
        {"lat": -51.093, "lon": -72.892, "name": "Pudeto — catamaran dock", "type": "start"},
        {"lat": -51.053, "lon": -73.036, "name": "Refugio Paine Grande", "type": "waypoint"},
        {"lat": -51.025, "lon": -73.216, "name": "Refugio Grey / Grey Glacier", "type": "waypoint"},
        {"lat": -51.053, "lon": -73.036, "name": "Refugio Paine Grande", "type": "waypoint"},
        {"lat": -50.950, "lon": -72.993, "name": "French Valley junction", "type": "waypoint"},
        {"lat": -50.916, "lon": -72.956, "name": "Refugio Los Cuernos", "type": "waypoint"},
        {"lat": -50.941, "lon": -72.917, "name": "Refugio Chileno", "type": "waypoint"},
        {"lat": -50.942, "lon": -72.898, "name": "Mirador Las Torres", "type": "waypoint"},
        {"lat": -50.947, "lon": -72.869, "name": "Hotel Las Torres — trailhead", "type": "end"},
    ],
    "Tour du Mont Blanc": [
        {"lat": 45.887, "lon": 6.797, "name": "Les Houches (Start)", "type": "start"},
        {"lat": 45.822, "lon": 6.727, "name": "Les Contamines", "type": "waypoint"},
        {"lat": 45.744, "lon": 6.802, "name": "Col du Bonhomme", "type": "waypoint"},
        {"lat": 45.795, "lon": 6.979, "name": "Courmayeur (Italy)", "type": "waypoint"},
        {"lat": 45.856, "lon": 7.014, "name": "Rifugio Bonatti", "type": "waypoint"},
        {"lat": 45.921, "lon": 7.094, "name": "La Fouly (Switzerland)", "type": "waypoint"},
        {"lat": 46.008, "lon": 7.150, "name": "Champex", "type": "waypoint"},
        {"lat": 46.057, "lon": 6.981, "name": "Trient", "type": "waypoint"},
        {"lat": 45.975, "lon": 6.924, "name": "Col des Montets", "type": "waypoint"},
        {"lat": 45.924, "lon": 6.869, "name": "Chamonix (End)", "type": "end"},
    ],
    "Milford Track": [
        {"lat": -45.237, "lon": 167.843, "name": "Te Anau Downs (Start)", "type": "start"},
        {"lat": -44.997, "lon": 167.867, "name": "Clinton Hut", "type": "waypoint"},
        {"lat": -44.830, "lon": 167.953, "name": "Mintaro Hut", "type": "waypoint"},
        {"lat": -44.779, "lon": 167.978, "name": "Mackinnon Pass", "type": "waypoint"},
        {"lat": -44.695, "lon": 168.012, "name": "Dumpling Hut", "type": "waypoint"},
        {"lat": -44.667, "lon": 167.927, "name": "Milford Sound (End)", "type": "end"},
    ],
    "Inca Trail": [
        {"lat": -13.527, "lon": -71.989, "name": "KM 82 — Piscacucho (Start)", "type": "start"},
        {"lat": -13.397, "lon": -72.107, "name": "Llactapata ruins", "type": "waypoint"},
        {"lat": -13.280, "lon": -72.344, "name": "Dead Woman's Pass (4,215 m)", "type": "waypoint"},
        {"lat": -13.230, "lon": -72.422, "name": "Runkuraqay Pass", "type": "waypoint"},
        {"lat": -13.184, "lon": -72.494, "name": "Wiñay Wayna ruins", "type": "waypoint"},
        {"lat": -13.172, "lon": -72.519, "name": "Sun Gate — Inti Punku", "type": "waypoint"},
        {"lat": -13.163, "lon": -72.545, "name": "Machu Picchu (End)", "type": "end"},
    ],
    "Camino Francés": [
        {"lat": 43.163, "lon": -1.238, "name": "St Jean Pied de Port (Start)", "type": "start"},
        {"lat": 42.812, "lon": -1.644, "name": "Pamplona", "type": "waypoint"},
        {"lat": 42.466, "lon": -2.445, "name": "Logroño", "type": "waypoint"},
        {"lat": 42.344, "lon": -3.700, "name": "Burgos", "type": "waypoint"},
        {"lat": 42.599, "lon": -5.571, "name": "León", "type": "waypoint"},
        {"lat": 42.707, "lon": -7.013, "name": "O Cebreiro", "type": "waypoint"},
        {"lat": 42.881, "lon": -8.546, "name": "Santiago de Compostela (End)", "type": "end"},
    ],
}

_ICON_CONFIG = {
    "start":    {"color": "green",  "icon": "play",   "prefix": "fa"},
    "end":      {"color": "red",    "icon": "flag",   "prefix": "fa"},
    "waypoint": {"color": "blue",   "icon": "circle", "prefix": "fa"},
}


# ── OSM geometry fetch ────────────────────────────────────────────────────────

def fetch_osm_track(route_name: str, lat: float | None = None, lon: float | None = None) -> list[tuple[float, float]]:
    """
    Fetch the real GPS-traced polyline for a hiking route from OSM via Overpass.

    Uses a bounding-box search (±1.5° around the route centre) so the query
    scope is small and fast. Matches any relation whose name or name:en contains
    a significant word from route_name.
    Falls back to a global name search if no lat/lon is provided.
    Returns [] on failure or when the route is not in OSM.
    """
    if lat is not None and lon is not None:
        # Bbox search — much faster than global, avoids global timeout
        pad = 1.5
        south, north = lat - pad, lat + pad
        west, east = lon - pad, lon + pad
        bbox = f"({south},{west},{north},{east})"
        coords = _overpass_geom(
            f'[out:json][timeout:{_TIMEOUT}];'
            f'relation["route"~"hiking|foot"]{bbox};'
            f'out geom;',
            name_filter=route_name,
        )
        if coords:
            return coords

    # Global name search as fallback
    escaped = route_name.replace('"', '\\"')
    for tag in ("name:en", "name"):
        coords = _overpass_geom(
            f'[out:json][timeout:{_TIMEOUT}];'
            f'relation["route"~"hiking|foot"]["{tag}"~"{escaped}",i];'
            f'out geom;',
        )
        if coords:
            return coords
    return []


def _overpass_geom(query: str, name_filter: str | None = None) -> list[tuple[float, float]]:
    """
    POST a query and extract way-geometry coordinates from the best-matching relation.

    When *name_filter* is given, scores each relation by how many words from the
    filter appear in its name/name:en tags and uses the highest-scoring one.
    """
    try:
        data = urllib.parse.urlencode({"data": query}).encode()
        req = urllib.request.Request(_OVERPASS_URL, data=data)
        req.add_header("Content-Type", "application/x-www-form-urlencoded")
        req.add_header("User-Agent", _UA)
        with urllib.request.urlopen(req, timeout=_TIMEOUT + 5) as resp:
            result = json.loads(resp.read())
    except Exception as exc:
        print(f"[map_view] Overpass error: {exc}", file=sys.stderr)
        return []

    relations = [el for el in result.get("elements", []) if el.get("type") == "relation"]
    if not relations:
        return []

    # Pick the best-matching relation
    if name_filter and len(relations) > 1:
        filter_words = {w.lower() for w in name_filter.split() if len(w) > 2}
        def score(rel: dict) -> int:
            tags = rel.get("tags", {})
            combined = " ".join([
                tags.get("name", ""),
                tags.get("name:en", ""),
            ]).lower()
            return sum(1 for w in filter_words if w in combined)
        relations = sorted(relations, key=score, reverse=True)

    best = relations[0]
    coords: list[tuple[float, float]] = []
    for member in best.get("members", []):
        if member.get("type") != "way":
            continue
        for pt in member.get("geometry", []):
            if pt.get("lat") is not None and pt.get("lon") is not None:
                coords.append((pt["lat"], pt["lon"]))

    return _downsample(coords, _MAX_TRACK_POINTS)


def _downsample(coords: list[tuple[float, float]], max_pts: int) -> list[tuple[float, float]]:
    if len(coords) <= max_pts:
        return coords
    step = len(coords) // max_pts
    return coords[::step]


# ── Public map builder ────────────────────────────────────────────────────────

def build_route_map(
    route: dict,
    osm_track: list[tuple[float, float]] | None = None,
) -> folium.Map | None:
    """
    Return a Folium map for *route*, or None if no coordinate data is available.

    Pass *osm_track* (from a cached `fetch_osm_track` call) to draw the real
    GPS polyline. Falls back to curated waypoints, then to a centre marker.
    """
    lat = route.get("lat")
    lon = route.get("lon")
    if lat is None or lon is None:
        return None

    route_name = route.get("route_name", "")
    waypoints = _WAYPOINTS.get(route_name, [])

    # ── Choose coordinate source for the polyline ─────────────────────────────
    if osm_track:
        line_coords = osm_track
        track_source = "osm"
    elif waypoints:
        line_coords = [(wp["lat"], wp["lon"]) for wp in waypoints]
        track_source = "curated"
    else:
        line_coords = []
        track_source = "none"

    # ── Build map ─────────────────────────────────────────────────────────────
    if line_coords:
        lats = [c[0] for c in line_coords]
        lons = [c[1] for c in line_coords]
        center = [sum(lats) / len(lats), sum(lons) / len(lons)]
        m = folium.Map(location=center, zoom_start=10, tiles="OpenStreetMap")
        m.fit_bounds([[min(lats), min(lons)], [max(lats), max(lons)]],
                     padding=(20, 20))
    else:
        m = folium.Map(location=[lat, lon], zoom_start=9, tiles="OpenStreetMap")

    # ── Polyline ──────────────────────────────────────────────────────────────
    if line_coords:
        tooltip_text = (
            f"{route_name} — GPS track (OpenStreetMap)"
            if track_source == "osm"
            else f"{route_name} — key waypoints"
        )
        folium.PolyLine(
            locations=line_coords,
            color="#2171B5",
            weight=4 if track_source == "osm" else 3,
            opacity=0.85,
            tooltip=tooltip_text,
        ).add_to(m)

    # ── Markers ───────────────────────────────────────────────────────────────
    if waypoints:
        # Always show curated named stops regardless of track source
        for wp in waypoints:
            cfg = _ICON_CONFIG.get(wp["type"], _ICON_CONFIG["waypoint"])
            folium.Marker(
                location=[wp["lat"], wp["lon"]],
                popup=folium.Popup(wp["name"], max_width=220),
                tooltip=wp["name"],
                icon=folium.Icon(**cfg),
            ).add_to(m)
    elif not line_coords:
        folium.CircleMarker(
            location=[lat, lon],
            radius=12,
            color="#2171B5",
            fill=True,
            fill_color="#2171B5",
            fill_opacity=0.5,
            tooltip=f"{route_name} — approximate centre",
            popup=folium.Popup(
                f"<b>{route_name}</b><br>{route.get('region', '')}",
                max_width=220,
            ),
        ).add_to(m)

    return m
