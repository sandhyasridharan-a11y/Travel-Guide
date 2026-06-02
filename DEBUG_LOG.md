# Debug Log — Trek Ready App

A chronological record of bugs caught, their root causes, and how they were fixed.
For the engineering decisions behind each fix, see CLAUDE.md section 6.

---

## Navigation & State Bugs

### Inconsistent query param API (Phase 5)
- **Symptom:** Page nav and refresh broke when switching between Overview and Guidance.
- **Root cause:** Mixed `st.experimental_get_query_params` and `st.query_params` across the codebase.
- **Fix:** Standardised everything on `st.query_params`; added a normalisation helper.

### Risk driver guidance link mismatch (Phase 5)
- **Symptom:** Clicking a high-risk driver link didn't reliably navigate to the focused section.
- **Root cause:** `+` encoding in URLs; focus values decoded inconsistently.
- **Fix:** Switched to percent-encoding with `quote(..., safe='')`; added `normalize_focus()`.

### Sidebar section selector stuck (Phase 5)
- **Symptom:** Left nav could get stuck in Guidance; couldn't toggle back to Overview.
- **Root cause:** Streamlit widget state conflicts and improper session-state overrides.
- **Fix:** Simplified sidebar selection logic; removed conflicting state sync.

### Page URL out of sync on refresh (Phase 5)
- **Symptom:** Refreshing sometimes returned to a previous page state.
- **Root cause:** Query params not updated consistently on section change.
- **Fix:** Added explicit query param sync; helper keeps browser URL aligned.

### Tests passed but navigation bug remained (Phase 5)
- **Symptom:** All tests green; nav bug survived.
- **Root cause:** Tests only covered helper output, not section resolution logic.
- **Fix:** Expanded tests to cover query utilities, page resolution, link encoding, and guidance rendering.

---

## Scoring Model Bugs

### Fitness risk scored against total distance, not daily (Phase 6b)
- **Symptom:** Beginner doing 80 km over 10 days scored same fitness risk as 80 km in 3 days.
- **Root cause:** `score_fitness_risk` used raw route totals; `trip_profile` was never passed in.
- **Fix:** Added `trip_profile` param; compute `moving_days = total_days - rest_days`; score daily load.

### Hotel treated as higher logistics risk than backcountry hut (Phase 6b)
- **Symptom:** Hotel got +3 more logistics risk than a backcountry hut.
- **Root cause:** `else` branch caught both `"Hotel"` and `"Campsite"` and added 4 to both.
- **Fix:** Added explicit `"Hotel"` branch (+0) at the top; full ordered tier now explicit.

### Risk label diverged from readiness score (Phase 6b)
- **Symptom:** UI showed "72/100 readiness" alongside "High" risk simultaneously.
- **Root cause:** `risk_engine.py` had its own independent scoring logic separate from `scoring_model.py`.
- **Fix:** Rewrote `estimate_risk` to call the shared pipeline; risk label derived from readiness score.

### Guided trips got no meaningful risk reduction (Phase 6b)
- **Symptom:** Beginner guided vs. self-guided differed only by 2 logistics points.
- **Root cause:** Guided/self-guided only touched `score_logistics_risk`.
- **Fix:** Added `apply_guided_adjustments()` — reduces Fitness and Gear risk for guided trips.

### Gear risk lodging tier inversion (same bug as logistics, found later) (Phase 6b)
- **Symptom:** Hotel had higher gear risk than backcountry hut.
- **Root cause:** Same `else → +4` catch-all that was fixed in logistics existed in gear risk.
- **Fix:** Applied same explicit tier ordering to `score_gear_risk`.

### Altitude risk zero-band too high (Phase 6b)
- **Symptom:** W Trek (1200m max) scored 0 altitude risk despite mountain conditions.
- **Root cause:** Zero-risk threshold was `< 1200m`.
- **Fix:** Lowered to `< 800m`; added 800–1500m band (+3); rescaled upper bands.

### Weather scoring hemisphere-blind (Phase 6b)
- **Symptom:** October Patagonia trip (southern summer) penalised as "Fall."
- **Root cause:** Season inferred from month name substrings — northern-hemisphere assumption baked in.
- **Fix:** Dropped season parsing entirely; score from `route["climate"]` field instead.

### Gear risk had no feedback from the packing plan (Phase 6b)
- **Symptom:** Well-prepared hiker scored same gear risk as poorly-prepared one.
- **Root cause:** `score_gear_risk` computed before the packing plan existed.
- **Fix:** Two-pass flow: initial scores → build packing plan → `adjust_gear_risk_for_warnings()` → adjusted scores.

---

## API & Environment Bugs

### AI layer silently swallowed all errors (Phase 7d)
- **Symptom:** AI narratives showed "unavailable" with no explanation; no way to debug.
- **Root cause:** All three generation functions had bare `except Exception: return None`.
- **Fix:** Extracted shared `_call()` helper that logs errors to stderr before returning None.

### `ANTHROPIC_API_KEY` conflicting with Claude Code auth (Phase 7d)
- **Symptom:** App used Claude Code's session key instead of the project key.
- **Root cause:** `load_dotenv()` default `override=False` deferred to whatever was already in the environment.
- **Fix:** Changed to `load_dotenv(override=True)` so `.env` file always wins.

### Stale `None` cached in Streamlit on first AI failure (Phase 7d)
- **Symptom:** After fixing the API key, AI sections still showed "unavailable."
- **Root cause:** `@st.cache_data` cached the `None` result permanently for the session.
- **Fix:** Added `ttl=3600` so failed results expire after one hour.

---

## Discovery & Map Bugs

### OSM name search returns wrong route (Phase 8b)
- **Symptom:** Searching "Appalachian Trail" added "International Appalachian Trail, Québec."
- **Root cause:** Global Overpass name search returns first regex match; OSM name took priority over Wikipedia title.
- **Fix:** Swapped priority to prefer Wikipedia title (curated, English); OSM name only when no Wikipedia title.

### Overpass global name search timing out (Phase 8b/map)
- **Symptom:** `HTTP Error 504: Gateway Timeout` when fetching trail geometry by name.
- **Root cause:** Global regex search over all OSM data is expensive; busy servers time out.
- **Fix:** Switched to bbox search (±1.5° around route centre); name-match scoring picks best result from local results.

### Elevation chart base altitude wrong for high-gain routes (Phase 8a/map)
- **Symptom:** Tour du Mont Blanc chart showed 0m start and 0m end; Chamonix is at 1035m.
- **Root cause:** `base_elev = max(0, max_elev - total_gain)` → 0 when total_gain > max_elev.
- **Fix:** Added `base_elevation_m` field to route library; chart uses that when present.

---

## Python Compatibility Bugs

### `str | None` type hints fail on Python 3.9 (Phase 8a)
- **Symptom:** `TypeError: unsupported operand type(s) for |: 'type' and 'NoneType'` at startup.
- **Root cause:** Union type syntax `X | None` requires Python 3.10+ at runtime unless `from __future__ import annotations` is present.
- **Fix:** Added `from __future__ import annotations` to `app.py` and `charts.py`.

---

## Data / Logic Bugs

### `max_value=21` on trip days broke Camino Francés (30-day route)
- **Symptom:** `StreamlitValueAboveMaxError` on selecting Camino Francés.
- **Root cause:** Hard-coded `max_value=21` predated multi-week routes.
- **Fix:** Raised `max_value` to 60 days; `rest_days` max raised from 7 to 14.
