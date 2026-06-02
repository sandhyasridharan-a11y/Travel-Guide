# Travel Guide App — Project Memory

## 1) What this app does

This is a Streamlit-based hiking readiness and trip planning app. It helps a user:
- select a predefined route
- confirm or edit trip assumptions
- estimate hiking risk and readiness
- generate packing recommendations
- view a risk heatmap and top risk drivers
- build a mitigation plan
- generate a day-by-day itinerary with recovery and risk notes
- review risk reduction guidance for the highest-risk dimensions

The app is structured as a guided trekking planner, not a generative AI assistant. It uses deterministic rules-based scoring to evaluate risk.

## 2) 8-phase build plan

### Phase 1: Project scaffold and route selection
- Build the initial Streamlit app shell
- Add route selection using `route_library.py`
- Create route data and a basic route detail page
- Confirm the app structure and primary dependencies

### Phase 2: Smart assumptions and profile editing
- Add `assumption_engine.py` to propose default trip profile values by route
- Add `trip_profile_editor.py` for editable trip assumptions
- Show confirmed assumptions and let users review them before planning

### Phase 3: Risk scoring and guidance integration
- Add `scoring_model.py` with 5 risk dimensions
- Add `risk_engine.py` for route/weather/experience risk estimation
- Add `risk_register.py` and `risk_guidance.py`
- Display a readiness gauge, risk heatmap, risk drivers, and mitigation plan

### Phase 4: Itinerary generation and recovery advice
- Add `itinerary_generator.py` and `day_planner.py`
- Generate daily route segments with distance, elevation, difficulty, recovery advice, and risk notes
- Integrate itinerary into the main app flow

### Phase 5: UI refactor and stronger navigation
- Refactor `app.py` into a cleaner, tab-based user interface
- Move controls to a sidebar and separate Overview/Itinerary/Guidance sections
- Fix query-param and navigation synchronization issues
- Add stronger test coverage for query state and navigation

### Phase 6: Consistency, testing, and regression protection
- Add unit tests for route lookup, scoring, query utilities, and guidance rendering
- Standardize query param handling on `st.query_params`
- Add a test runner and CI workflow
- Harden the app against regressions when editing navigation or state logic

### Phase 7: Feature polish and UX improvements
- Improve layout, labeling, and the guidance page experience
- Add better link behavior from high-risk drivers to guidance
- Strengthen the `Overview` page and cleaning of the sidebar flow

### Phase 8: Deployment and future expansion
- Prepare for deployment and cleanup
- Add extensibility for new routes, custom trip profiles, or more advanced risk factors
- Define next-phase product features such as route comparison, packing checklist export, or itinerary sharing

## 3) Phase status
- Phase 1: complete
- Phase 2: complete
- Phase 3: complete
- Phase 4: complete
- Phase 5a: UI refactor to sidebar navigation — complete
- Phase 5b: Query parameter standardization and fixes — complete
- Phase 5c: Packing Optimizer with gear rules — complete
- Phase 6a: Unit test coverage for all modules — complete (208 tests, 0 failures)
- Phase 6b: Risk scoring model redesign — complete (see section 8)
- Phase 6c: Integration test for full trip planning pipeline — planned
- Phase 7: UI redesign — complete (see section 9)
- Phase 7d: AI narrative layer (`ai_layer.py`) — complete; optional upgrade, gracefully degrades when key absent
- Phase 8a: Weather integration (Open-Meteo API) — complete (see section 10)
- Phase 8b: Route discovery (OSM + Wikipedia) — complete; 5 curated routes + keyword search for any trail
- Phase 8c: Streamlit Community Cloud deployment — complete; secrets via `st.secrets`
- Phase 9: Further expansion — planned

## 4) Full component structure and responsibilities

### `app.py`
- Main Streamlit app entrypoint; requires `from __future__ import annotations` for Python 3.9 compatibility with `X | None` type hints
- **Sidebar** — route selector (library + discovered routes) → 🔍 Search expander (keyword suggestions + add) → experience level with `st.popover` ℹ️ definitions → trip start date → expected weather (auto-derived from forecast when available, manual otherwise) → "Customize trip" expander
- **Weather auto-derivation** — `_derive_weather_condition()` classifies avg trip-day precip as Stable (<25%) / Mixed (25–55%) / Unstable (≥55%); resets automatically when route or date changes; user can still override manually
- **Navigation** — `st.tabs` with three tabs: Overview, Itinerary, Guidance
- **Overview tab** — hero image → title/caption → 4 hero metrics → risk breakdown + heatmap + high-risk callouts → **⬇️ Download PDF** (primary button, full-width, above packing) → packing section → "About this route" expander → "🤖 AI insights" collapsed expander (risk summary, recommendations, briefing narrative)
- **Itinerary tab** — download PDF button (top-right) → day strip (difficulty + weather icon per day) → expandable day cards with weather row (temp range, precip, wind) + notes/gear layout
- **Guidance tab** — 5-column risk summary → guidance content → mitigation plan
- `.md` download removed; PDF is the only export format
- Uses `st.query_params` only for `focus` (guidance deep-linking); page routing is handled by tabs

### `route_library.py`
- Contains 5 curated routes: Patagonia W Trek, Tour du Mont Blanc, Milford Track, Inca Trail, Camino Francés
- Every route includes `lat`/`lon` coordinates for weather integration
- Provides `get_route_by_name(...)` helper
- New routes added here should follow the same schema (all keys including `lat`, `lon`, `image_url`)

### `assumption_engine.py`
- Creates default trip profile assumptions for a selected route
- Drives initial values for number of days, lodging, pace, rest days, and pack preference

### `trip_profile_editor.py`
- Builds the Streamlit form for editing trip assumptions
- Returns the confirmed profile back to `app.py`

### `briefing_generator.py`
- Generates final briefing text based on route, risk, packing list, readiness score, and top risk drivers

### `risk_engine.py`
- Exposes `readiness_to_risk_label(readiness_score)` — maps a 0–100 readiness score to a consistent label (Low / Moderate / High / Very High / Extreme)
- Exposes `estimate_risk(route, weather_condition, experience_level, trip_profile=None)` — convenience wrapper that calls the scoring model internally and returns a label; accepts an optional trip_profile, uses a sensible fallback if omitted
- Previously contained independent scoring logic that could diverge from `scoring_model.py`; redesigned in Phase 6b to derive all labels from the shared scoring pipeline

### `packing_engine.py`
- **Purpose**: Generate comprehensive packing lists based on route conditions, trip profile, risk scores, and user preferences
- **Current State**: Enhanced with detailed gear rules and structured output
- **Key Functions**:
  - `build_packing_list(route, experience_level, weather_condition, pack_weight_preference)` - legacy function for backward compatibility, returns flat list of items
  - `build_comprehensive_packing_plan(route, trip_profile, experience_level, weather_condition, pack_weight_preference, risk_scores)` - new function that returns structured output with must-haves, optional, risk-based additions, warnings, and weight estimate
- **Output Structure**: 
  - `must_haves`: List of 30+ essential items for the trip
  - `optional`: Items recommended based on pack preference (5-10 items)
  - `risk_based_additions`: Items added based on identified risk dimensions (2-6 items per risk factor)
  - `all_items`: Combined list of all items
  - `estimated_weight_kg`: Estimated pack weight in kg
  - `warnings`: List of validation warnings (overweight, missing critical items, etc.)
- **Dependencies**: gear_rules

### `gear_rules.py`
- **Purpose**: Define comprehensive gear database and rules for intelligent packing recommendations
- **Current State**: New file with detailed gear rules and decision logic
- **Key Data/Functions**:
  - `GEAR_DATABASE`: Dict of 40+ items with weight (grams) and category metadata
  - `get_must_have_items(route, trip_profile, experience_level, weather_condition)` - returns must-have items including route-specific items based on difficulty and lodging type
  - `get_optional_items(route, trip_profile, pack_weight_preference)` - returns optional items based on comfort preference
  - `get_risk_based_additions(risk_scores, route, trip_profile, weather_condition)` - returns risk-sensitive items (e.g., altitude medication for high altitude risk)
  - `estimate_pack_weight(packing_items)` - calculates total weight from item list
  - `validate_packing_list(packing_items, pack_weight_preference, trip_profile)` - generates warnings
- **Dependencies**: None

### `scoring_model.py`
- Implements five risk scoring dimensions (each 0–20):
  - **Fitness risk** — scored against *daily* distance and elevation (`distance_km / moving_days`, `elevation_gain_m / moving_days`), adjusted for experience level; requires `trip_profile` to compute moving days correctly
  - **Altitude risk** — scored against max elevation, adjusted for experience level
  - **Weather risk** — scored against season and weather condition; Patagonia/alpine regions add a base penalty
  - **Logistics risk** — scored against remoteness, permit requirement, transport complexity, lodging tier, and trip style; self-guided adds +2; lodging tiers ordered Hotel (0) → Backcountry hut (1) → Refugio/Campsite (2) → Mixed (3) → Campsite (4)
  - **Gear risk** — scored against climate, lodging type, pack weight preference, and weather condition; lodging tiers use the same Hotel → Campsite ordering as logistics risk
- `apply_guided_adjustments(risk_scores, trip_profile)` — reduces Fitness risk by 2 and Gear risk by 2 for guided trips (guide manages pace/turnaround decisions; carries group safety gear); no effect on self-guided; does not mutate the input dict
- `adjust_gear_risk_for_warnings(risk_scores, packing_warnings)` — post-hoc adjustment: reduces Gear risk by 3 points when the packing plan has no warnings (complete kit, appropriate weight, shelter covered); does not mutate the input dict
- `overall_readiness_score(risk_scores)` — weighted average across the five dimensions, inverted to a 0–100 readiness percentage
- `top_risk_drivers(risk_scores, count)` — returns the N highest-scoring dimensions

### `risk_register.py`
- Creates a risk register summary and mitigation plan based on risk scores

### `risk_guidance.py`
- Provides guidance points for each risk dimension
- `build_guidance_link(dimension)` — builds a `?focus=...` URL for deep-linking to a focused guidance view (page-switching links removed in Phase 7)
- `render_guidance_page(focus)` — renders all guidance content with optional focus highlighting; no longer contains navigation links

### `itinerary_generator.py`
- Generates daily itinerary segments from route and trip profile
- Uses risk scores to adjust difficulty and recovery notes

### `day_planner.py`
- Supports per-day planning logic and detailed day segment structure

### `charts.py`
- `risk_heatmap_chart(risk_scores)` — horizontal bar chart with semantic color scale: green (0–7) → yellow (7–11) → orange (11–15) → red (15–20); rounded bar ends
- `readiness_gauge_chart(readiness_score)` — simple gauge bar (green above 60, red below)

### `query_utils.py`
- Centralizes query parameter helpers
- Builds page query strings and syncs page/focus state
- Resolves the intended navigation section from query and session state

### `ai_layer.py`
- Optional AI narrative layer using the Anthropic API (claude-haiku-4-5-20251001)
- Reads `ANTHROPIC_API_KEY` from `.env` via `load_dotenv(override=True)` — `override=True` ensures the project key wins over any conflicting env var set by Claude Code's own auth
- All three generation functions (`generate_risk_summary`, `generate_personalized_recommendations`, `generate_briefing_narrative`) degrade gracefully: return `None` when the key is absent, log actual errors to stderr via a shared `_call()` helper instead of swallowing them silently
- App caches results with `@st.cache_data(ttl=3600)` so a transient failure expires rather than being locked in for the session
- **Setup**: copy `.env.example` → `.env` and add a valid key with API credits; the rest of the app works without it

### `weather_client.py`
- Fetches daily weather forecasts from the Open-Meteo API (free, no API key required)
- `fetch_forecast(lat, lon, start_date, num_days)` — returns a list of per-day dicts: `date`, `temp_min_c`, `temp_max_c`, `precipitation_probability` (0–100), `windspeed_kmh`; returns `[]` if outside 16-day window or on failure
- `weather_icon(precip_prob, windspeed_kmh)` — maps conditions to emoji (🌧 / 🌦 / 🌬 / 🌤)
- Uses `urllib.request` (stdlib) — no extra dependency

### `route_discovery.py`
- Finds trail profiles from external sources for routes not in `route_library.py`
- `suggest_routes(query)` — keyword search returning up to 5 candidate names; checks library first (word-level match, ignores words ≤2 chars), then Wikipedia opensearch for autocomplete
- `discover_route(trail_name)` — full profile fetch: library lookup → Wikipedia (description, distance, elevation, duration, difficulty) → Overpass/OSM (coordinates via `name:en` tag then `name`); merges into route_library-compatible schema with `_source` and `_wiki_url` extras
- Wikipedia title preferred over OSM name (cleaner, English; OSM names can be local-language or include geographic qualifiers)
- All network calls use `User-Agent: TrekReadyApp/1.0`; failures log to stderr and return gracefully
- Discovered routes are stored in `st.session_state["discovered_routes"]` and appear in the route dropdown alongside library routes

### Tests — 208 total, all passing
- `tests/test_route_library.py` — route lookup and not-found behavior
- `tests/test_query_utils.py` — query param construction, section resolution, focus normalization
- `tests/test_risk_engine.py` — `readiness_to_risk_label` boundary mapping, `estimate_risk` ordering invariants, consistency with scoring model when trip_profile is supplied
- `tests/test_risk_guidance.py` — link encoding and focus decoding
- `tests/test_risk_guidance_render.py` — guidance page rendering with and without a focus dimension
- `tests/test_scoring_model.py` — all five individual scoring functions, daily-vs-total fitness distance behavior, lodging tier ordering, gear risk warning adjustment, season normalization, top drivers sorting
- `tests/test_packing_engine.py` — must-haves, optional tiers, risk-based additions, weight estimation, validation warnings, backward-compatible flat list
- `tests/test_assumption_engine.py` — default profile logic for hard/easy routes, Patagonia region override, rest day thresholds, guided/self-guided selection
- `tests/test_day_planner.py` — rest day structure, pace speed ordering, difficulty thresholds (Easy/Moderate/Hard), risk note triggers per dimension, recovery advice escalation
- `tests/test_itinerary_generator.py` — daily profile distribution, rest day index placement, Patagonia vs generic segment naming, itinerary length and day index invariants, summarize field exclusions
- `tests/test_risk_register.py` — severity thresholds (Low/Moderate/High), mitigation plan content for high vs low risk, structural invariants
- `tests/test_briefing_generator.py` — all required sections present, itinerary days included, keyword-only argument enforcement
- `tests/test_export_utils.py` — filename construction, file write, bytes encoding
- `tests/test_weather_client.py` — happy path mapping, partial/missing data, out-of-range dates, API failure, `weather_icon` thresholds and priority
- `tests/test_route_discovery.py` — library lookup (exact/substring), all 5 text parsers, `suggest_routes` keyword matching and deduplication, `_build_profile` merge priority, full `discover_route` flow with mocked network

### Tooling
- `pytest.ini` configures test discovery
- `requirements.txt` declares runtime dependencies
- `scripts/run_tests.sh` is a local test runner script
- `.github/workflows/python-app.yml` runs CI on push/pull request

## 5) Coding conventions
- Always write unit tests for new logic and regression-prone behavior
- Standardize on `st.query_params` for query parameter access and updates
- Avoid mixed experimental Streamlit query APIs across the app
- Use rules-based scoring logic for risk assessment, not AI/LLM inference
- Keep UI state and URL state consistent and centralized with helpers
- Prefer readable, deterministic functions over implicit app behavior
- Keep the app design modular with one responsibility per file

## 6) Known bugs we fixed and how

### Bug: inconsistent query param API usage
- **Symptom:** page navigation and refresh behavior broke when switching between Overview and Guidance
- **Cause:** app used both `st.experimental_get_query_params` and `st.query_params`/`st.experimental_set_query_params`
- **Fix:** standardized all query state handling to `st.query_params`, added normalization helper, and removed experimental API usage

### Bug: risk driver guidance link mismatch
- **Symptom:** clicking a high-risk driver link did not reliably navigate to the focused guidance section
- **Cause:** link encoding used `+` and focus values were decoded inconsistently
- **Fix:** switched to percent-encoding with `quote(..., safe='')`, added `normalize_focus(...)`, and updated guidance rendering to honor focus

### Bug: sidebar section selector stuck
- **Symptom:** left nav could get stuck in Guidance, preventing toggling back to Overview or Itinerary
- **Cause:** Streamlit widget state conflicts and improper session-state overrides in the sidebar
- **Fix:** simplified the sidebar page selection logic and removed conflicting state sync behavior

### Bug: page URL did not stay in sync on refresh
- **Symptom:** refreshing sometimes returned to a previous page state
- **Cause:** query params were not consistently updated when the selected section changed
- **Fix:** added explicit query param sync logic and a helper to keep browser URL aligned with app state

### Bug: test coverage gap for actual navigation flow
- **Symptom:** tests passed but the navigation bug remained
- **Cause:** initial tests only covered helper outputs, not the section resolution rule or Streamlit navigation logic
- **Fix:** expanded tests to cover query utilities, page resolution, guidance link encoding, and guidance page rendering

### Bug: fitness risk scored against total trip distance, not daily distance
- **Symptom:** a Beginner doing 80 km over 10 relaxed days scored the same fitness risk as one doing 80 km in 3 hard days
- **Cause:** `score_fitness_risk` used raw `distance_km` and `elevation_gain_m` from the route; `trip_profile` (which holds number of days and rest days) was never passed in
- **Fix:** added `trip_profile` parameter to `score_fitness_risk`; computes `moving_days = total_days - rest_days` and scores `daily_distance` and `daily_elevation` against rescaled thresholds; `score_trip_risks` now passes `trip_profile` through

### Bug: Hotel treated as higher logistics risk than a backcountry hut
- **Symptom:** a hiker staying in a Hotel got a logistics risk score 3 points higher than one in a backcountry hut
- **Cause:** the lodging `else` branch caught both `"Hotel"` and `"Campsite"` and added 4 to both; `"Backcountry hut"` was the explicit lowest tier at +1
- **Fix:** added explicit `"Hotel"` branch (`+0`) at the top of the chain; `"Campsite"` made explicit at `+4`; full ordered tier is now Hotel → Backcountry hut → Refugio/Campsite → Mixed → Campsite

### Bug: risk label from `estimate_risk` could diverge from the readiness score shown in the UI
- **Symptom:** the "Risk level" metric and the "Overall readiness" metric could tell contradictory stories — e.g. readiness 72/100 alongside "High" risk
- **Cause:** `risk_engine.py` had its own independent scoring logic (difficulty + weather + experience) that was completely separate from the weighted `scoring_model.py` pipeline
- **Fix:** rewrote `estimate_risk` to call `score_trip_risks` + `overall_readiness_score` internally and map through a new `readiness_to_risk_label()` helper; `app.py` now derives the risk label from the already-computed readiness score, so both always agree

### Bug: guided trips received no meaningful risk reduction beyond 2 logistics points
- **Symptom:** a Beginner on a guided W Trek had the same fitness and gear risk as a Beginner going self-guided; the only difference was 2 logistics points (13% of max), understating the real safety value of professional support
- **Cause:** guided/self-guided only appeared in `score_logistics_risk` (+2 for self-guided), nowhere else
- **Fix:** added `apply_guided_adjustments(risk_scores, trip_profile)` — reduces Fitness risk by 2 (guide manages pace and turnaround decisions) and Gear risk by 2 (guide carries group safety gear) for guided trips; called in `app.py` between `score_trip_risks` and `build_comprehensive_packing_plan` so the packing plan also benefits from the adjusted scores

### Bug: `score_gear_risk` lodging tiers had the same Hotel/Campsite inversion fixed in logistics
- **Symptom:** a hiker staying in a Hotel had gear risk 3 points higher than one in a Backcountry hut; Hotel and Campsite were equally penalized despite very different gear requirements
- **Cause:** the same `else → +4` catch-all bug that we previously fixed in `score_logistics_risk` existed in `score_gear_risk` as well
- **Fix:** applied the same explicit lodging tier ordering: Hotel (0) → Backcountry hut (1) → Refugio/Campsite (2) → Mixed (3) → Campsite (4)

### Bug: altitude risk zero-band too high, erasing meaningful risk for mountain routes
- **Symptom:** routes with `max_elevation_m` up to 1199m scored 0 altitude base risk; an Advanced hiker on the 1200m Patagonia W Trek netted 0 altitude risk, which understated the cold/mountain environment
- **Cause:** zero-risk threshold was `< 1200m`, matching northern European easy hikes and challenging mountain routes alike
- **Fix:** lowered zero-risk band to `< 800m`; added a new low-risk band (800–1500m → +3); rescaled upper bands to 1500–2500m (+7), 2500–3500m (+12), ≥3500m (+16); deliberate choice NOT to add daily ascent rate to avoid double-counting with `score_fitness_risk`

### Bug: weather risk scoring was hemisphere-blind
- **Symptom:** a Patagonia trip in October (southern hemisphere summer, best season) was penalized as "Fall" (+4 base risk) because `normalize_season_text` used northern hemisphere month-to-season mapping; "October to April" also matched "april" → "Spring" through substring matching
- **Cause:** `score_weather_risk` inferred seasonal risk from month names in the `best_season` string — a fragile heuristic that breaks for any southern hemisphere or equatorial route
- **Decision:** evaluated two options: (A) add a `hemisphere` field to each route and flip the season logic; (B) replace season-based scoring with climate-based scoring using the route's existing `climate` field. Chose Option B — it removes the root cause entirely, reuses data already in the route model, and doesn't require every new route to carry hemisphere metadata
- **Fix:** removed `normalize_season_text`; rewrote `score_weather_risk(route, weather_condition)` to score from `route["climate"]` (Cold/Mountain → +4, Tropical/Desert → +3, Temperate → +1) plus the user-selected weather condition and regional bonus; removed the unused `season` parameter from the function signature and from `score_trip_risks`

### Bug: gear risk had no feedback from the packing plan
- **Symptom:** a hiker with a comprehensive, well-weighted packing plan received the same gear risk score as one with a poorly matched kit
- **Cause:** `score_gear_risk` was computed entirely from route/profile/weather metadata; the packing plan (built afterward) was never consulted
- **Architectural decision:** avoided a circular dependency (packing plan uses risk scores to select gear) by introducing a two-pass flow — initial `risk_scores` → build packing plan → `adjust_gear_risk_for_warnings()` → adjusted `risk_scores` used for readiness, itinerary, and briefing
- **Fix:** added `adjust_gear_risk_for_warnings(risk_scores, packing_warnings)` to `scoring_model.py`; reduces Gear risk by 3 points when the packing plan has no warnings (weight OK, critical items present, tent included if camping)

### Bug: Python 3.9 incompatibility with `X | None` type hints
- **Symptom:** `TypeError: unsupported operand type(s) for |: 'type' and 'NoneType'` at runtime when `_derive_weather_condition` was defined in `app.py`
- **Cause:** `str | None` union syntax is only valid at runtime in Python 3.10+; without `from __future__ import annotations`, Python 3.9 evaluates annotations eagerly and raises TypeError
- **Fix:** added `from __future__ import annotations` to `app.py`; all other modules already had it

### Bug: OSM name resolution returns wrong route (e.g. "International Appalachian Trail, Québec")
- **Symptom:** searching "Appalachian Trail" added a route named "International Appalachian Trail, Québec" with coordinates in Quebec
- **Cause:** Overpass global name search finds the nearest/first relation matching the regex, which can be a regional extension rather than the main trail; OSM name took priority over Wikipedia title
- **Fix:** swapped priority in `_build_profile` — Wikipedia title is now preferred over OSM name (Wikipedia titles are curated, in English, and match user intent); OSM is used only when Wikipedia has no title

## 7) What to build next

### Remaining Phase 6 work
- Integration test for the full trip planning pipeline: route → assumptions → scoring → packing → adjusted scores → itinerary → briefing
- Verify that `adjust_gear_risk_for_warnings` produces a measurable readiness score improvement end-to-end

### Risk scoring — deferred improvements (#2 and #4) — COMPLETED

### Phase 7 — UI polish
- Improve packing checklist export (checkbox UI, downloadable checklist)
- Guidance page UX: better visual hierarchy for focus vs other sections
- Overview page: surface the gear risk adjustment status (show if packing plan reduced risk)

### Phase 9 — Further expansion
- Route comparison view
- Dashboard view for readiness across multiple trip configurations
- Weather: extend beyond 16-day window using Open-Meteo's historical climate API for trip planning further ahead
- Elevation profile chart in the itinerary tab
- Packing checklist export (checkbox UI)
- Integration test for the full trip planning pipeline

---

## 8) Risk scoring redesign — engineering decisions log

This section captures the thinking behind the Phase 6b scoring model changes, intended as a reference for design discussions.

### What was wrong with the original model

The original `scoring_model.py` had five independent scoring functions wired together by `score_trip_risks`. Three systemic issues were identified:

1. **Fitness risk ignored trip shape.** Scoring against total `distance_km` and `elevation_gain_m` meant a 10-day leisurely trek and a 3-day hard push got identical scores. The fix was to divide by `moving_days` (total days minus rest days) and score daily load instead. This required threading `trip_profile` through to `score_fitness_risk`, which previously had no access to it.

2. **Lodging tiers were inverted in logistics risk.** The `else` branch caught both `"Hotel"` and `"Campsite"` and penalized both equally. This was a logic error — a hotel has near-zero logistics overhead. The fix explicitly listed all five lodging types in descending risk order.

3. **Two scoring systems that could contradict each other.** `risk_engine.py` had its own parallel scoring function (`estimate_risk`) that produced a risk label using different logic than `scoring_model.py`. The UI displayed both simultaneously (the "Risk level" metric and the "Overall readiness" number), which could tell contradictory stories. The fix unified them: `readiness_to_risk_label()` maps any readiness score to a label, and `estimate_risk` now calls the shared pipeline. In `app.py`, the label is derived directly from the already-computed readiness score.

### The gear risk two-pass design

Gear risk presented a circular dependency problem: `score_gear_risk` is called before the packing plan is built, but the packing plan uses `risk_scores` to select gear. Feeding packing warnings back into the initial scoring call would mean the packing plan influences its own inputs.

The solution was a two-pass flow:
1. Score initial `risk_scores` (including gear risk from route/climate/pack preference)
2. Build packing plan using those scores
3. Call `adjust_gear_risk_for_warnings(risk_scores, packing_warnings)` — if the plan is complete (no warnings), reduce Gear risk by 3 points
4. Recompute readiness score and all downstream outputs using the adjusted scores

This keeps `build_comprehensive_packing_plan` unchanged (it doesn't need to know about the adjustment), and the adjustment is a clear, testable, single-responsibility function. The packing plan is not rebuilt — it was built correctly from the initial scores, and the adjustment is a reflection of its quality, not an input to it.

### Altitude risk: threshold-only fix, not daily rate

Two sub-problems were identified: the zero-risk threshold was too high (1200m → 800m), and the function doesn't account for how quickly a hiker ascends. We chose to fix only the threshold. Adding daily ascent rate to altitude risk would mean `score_altitude_risk` and `score_fitness_risk` would both score the same daily elevation gain number, from two different angles. Keeping the separation clean (altitude risk = where you are; fitness risk = how hard it is to get there) avoids that overlap and keeps each function easier to reason about and test independently.

### Weather risk: climate field beats season text

The root problem with season-based weather scoring was not just the hemisphere issue — it was that the app always passes `route["best_season"]` as the trip season, meaning the scoring logic could never distinguish "going in peak season" from "going off-season." That question isn't answered today. Given that, the season parameter was doing no useful work at all: it was just re-encoding the route's inherent environment risk through a fragile text-parsing path.

Replacing it with `route["climate"]` is more direct. `"Cold/Mountain"` already says what we need to know about base weather difficulty. The user-selected `weather_condition` (Stable/Mixed/Unstable) covers the variable part. The hemisphere problem disappears because there's no month parsing anywhere. The tradeoff is that we've permanently given up on encoding "is this the right season for this route?" — that would require a separate `is_in_season` boolean on the trip profile if we ever want it back.

### Test philosophy for the scoring model

Rather than only testing `score_trip_risks` as a black box, we added tests for each individual scoring function. This catches regressions in a single dimension without requiring a full end-to-end scenario. The key tests check:
- Directional invariants (Advanced < Beginner, Unstable > Stable) rather than exact values
- Boundary behavior (clamp to 0 minimum, clamp to 20 maximum)
- The daily-vs-total distinction explicitly (`test_score_fitness_risk_uses_daily_distance_not_total`)
- Immutability of the input dict in `adjust_gear_risk_for_warnings`

---

## 9) UI redesign — engineering decisions log (Phase 7)

### Navigation: sidebar radio → `st.tabs`

The original navigation used radio buttons in the sidebar to switch between Overview, Itinerary, and Guidance. This created a physical disconnect — the control is on the left, the content is on the right — and led to several state bugs (section selector stuck, URL not syncing on refresh). It also violated the UI principle that navigation should be proximate to the content it controls.

`st.tabs` places navigation directly above the content it reveals, which is the standard modern pattern for multi-view apps that share a common context (same route and trip profile). As a side effect, it eliminated all the query-param page-switching logic and the associated bugs. `st.query_params` is now used only for the `focus` parameter (guidance deep-linking), not for page routing.

### Sidebar: four jobs → one job

The original sidebar contained: route selection, experience/weather controls, page navigation, 6 trip assumption widgets, and quick tips. Cognitive overload, and users had to scroll to reach the trip assumptions.

New structure: route, experience/weather (persistent — affects all views), and a single collapsed "Customize trip" expander for trip assumption editing. Progressive disclosure — smart defaults are applied immediately, customisation is one click away. Streamlit renders collapsed expander widgets normally, so `trip_profile` is always defined regardless of expander state.

### Information hierarchy: risk score as hero

The original Overview page led with route description text, then buried the readiness score in a small right column. Users had to scroll past assumptions and packing to reach the risk dashboard.

New order: hero image → route title → 4 hero metrics (readiness, risk level, duration, trip style) → 5-column risk breakdown → chart → high-risk callouts → everything else. The most important number (readiness score) is the first metric the eye lands on.

### Color system: semantic emoji indicators

`st.success`/`st.warning`/`st.error` are Streamlit status message components, not decoration primitives. Using them as risk badges misrepresents their semantic purpose and creates confusion (a "success" callout for a low-risk dimension looks like an operation succeeded).

Emoji color indicators (🟢🟡🟠🔴⛔) are accessible (color + shape, not color alone), require no custom CSS, work in all Streamlit render contexts, and carry consistent meaning everywhere they appear — metrics, the risk register, itinerary difficulty, and the Altair chart color scale. The chart uses a matching five-stop color gradient (green → yellow → orange → red → dark red) keyed to the same score thresholds.

### Images: `image_url` field in route data, rendered only when set

Rather than hardcoding an image URL or using a placeholder, `image_url: None` is added to the route data schema. The UI renders `st.image` only when the field is non-null. This means the layout works correctly today (no placeholder gap) and is immediately ready for real photos when added. Adding a route photo is a one-line data change.

---

---

## 10) Weather integration — engineering decisions log (Phase 8a)

### API choice: Open-Meteo
Open-Meteo is free, requires no API key, and returns standard JSON over a plain HTTPS GET. No SDK, no auth flow, no rate-limit concerns for a single-user planning app. `urllib.request` (stdlib) is sufficient — no new dependency needed.

### 16-day forecast window
Open-Meteo's forecast endpoint covers today through today + 16 days. Dates outside that range return an empty list from `fetch_forecast`, and the UI shows a caption explaining the limit. The historical/climate API exists for further-future dates but is out of scope for Phase 8a.

### Trip start date in the sidebar
A `trip_start_date` date picker was added to the sidebar (not inside the Customize expander) because it directly governs what appears in the Itinerary tab. It defaults to today so users immediately see real forecast data without any setup. Changing it re-fetches weather (the result is cached for 1 hour via `@st.cache_data(ttl=3600)`).

### Per-day lookup by date string
The weather fetch returns a flat list. In `app.py` this is converted to a dict keyed by date string (`YYYY-MM-DD`) immediately after the fetch. Each itinerary day computes its date as `trip_start_date + timedelta(days=day_index - 1)` and does a single dict lookup — O(1), no index arithmetic in the loop.

### Graceful degradation
If the route has no coordinates (`lat`/`lon` absent), `_weather_by_date` is empty and no weather UI is rendered. If the forecast API fails, `fetch_forecast` logs to stderr and returns `[]` — same result, same UI. The itinerary remains fully functional without weather data.

### `weather_icon` priority: precip before wind
High precipitation probability is a more operationally relevant signal than wind speed alone — a rainy day with high wind is still primarily a rain day. The function checks precip thresholds first, then wind, so the icon reflects the dominant hazard.

---

## 11) Deployment

### Streamlit Community Cloud (current target)
- Free hosting at share.streamlit.io; deploys directly from GitHub
- Push repo to GitHub, connect at share.streamlit.io, set main file to `app.py`
- **API key**: never commit `.env`; add `ANTHROPIC_API_KEY = "sk-ant-..."` under Settings → Secrets in the Streamlit Cloud dashboard
- `ai_layer.py` reads the key from `st.secrets` when `ANTHROPIC_API_KEY` is absent from the environment (cloud path), and from `.env` via `load_dotenv(override=True)` locally
- `.env` and `.streamlit/secrets.toml` are both gitignored

### Local development
- Copy `.env.example` → `.env`, add real key
- `streamlit run app.py` — hot-reloads on file save
- All external APIs (Open-Meteo, Overpass, Wikipedia) are free with no key; only Anthropic requires a key (and the app degrades gracefully without it)

---

This file is the definitive project memory for Claude sessions. It captures the current app purpose, build phases, file responsibilities, coding rules, debug history, engineering decisions, and the next work plan.
