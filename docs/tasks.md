# Implementation Tasks — PimpleTV TV Launcher

**Companion to:** [project-prd.md](project-prd.md), [integration-plan.md](integration-plan.md)
**Date:** 5 June 2026

Ordered, step-by-step tasks. Each has an ID, dependencies, and a clear "Done when". Tasks within a phase marked **∥** can run in parallel. Check off as you go.

Legend: `[ ]` todo · `[~]` in progress · `[x]` done · **(blocker)** must clear before dependents.

---

## Phase 0 — Recon & Contract Freeze

> **Deployment target:** backend runs **dockerized on a local Raspberry Pi (arm64)**. Runtime image is browserless (`httpx` + `selectolax`); Playwright is recon/fallback only, kept out of the Pi image.

- [x] **T0.1 Live-page recon (S1)** — **DONE (confirmed live 2026-06-05 19:09 MSK).** Links are **server-side rendered** into a `table.broadcast-table` in `div.tabs-content.active` — no AJAX, no browser. Each row = one source with bitrate/format/fps + an `acestream://<40-hex>` link; SopCast only in the prose tab. Real fixtures saved (`live_match_69163.html`, `live_match_69166.html`); extractor verified end-to-end (`resolve_streams` → `acestream://016d…ccc (1080p)`). See [recon-findings.md §4](recon-findings.md).

- [x] **T0.2 Listing-page recon** — Save static HTML of `/`, `/category/football/`, `/category/hockey/` and a few match pages (pre-window). Identify selectors for teams, kickoff, tournament, channel, stadium, logos.
  - Done: fixtures saved under `backend/tests/fixtures/` (`listing_*.html`, `match_69175.html`, `wp_post_69175.json`); selector map in [recon-findings.md](recon-findings.md). Site is WordPress; metadata is in static HTML (no browser needed).

- [x] **T0.3 Freeze API contract** — `docs/api/openapi.yaml` authored (endpoints from integration-plan §3, `Match`/`MatchSummary` from PRD §6 + `lastUpdated`, `{error:{code,message}}` envelope). Mirrored in `backend/app/models.py`.

- [x] **T0.4 Stand up mock API server** — FastAPI app runs in `PTV_MOCK_MODE` serving sample matches that satisfy the contract. Smoke-tested: list/detail/health/404/422 all verified. (Chose a FastAPI mock over Prism so it's the same stack as production and runs on the Pi.)

- [x] **T0.5 Repo scaffold (backend)** — `backend/` created: FastAPI app, models, store, config, routes, sample data, **Dockerfile (arm64) + docker-compose**, recon script, README. Runs end-to-end locally.
  - [x] **T0.5b androidtv scaffold** — Kotlin + Leanback project in `androidtv/` (Gradle Kotlin DSL + version catalog, wrapper included; AGP 8.7.3 / Gradle 8.11.1; minSdk 21 / target 35). Browse skeleton (`BrowseSupportFragment` + `MatchCardPresenter`) wired to the contract via Retrofit/Gson; LEANBACK_LAUNCHER manifest, TV banner, `Theme.Leanback`. **Validated:** Gradle wrapper bootstraps on Studio's bundled JDK 21 and `:app:help` configures cleanly (AGP + catalog resolve). Full APK build pending SDK 35 install on first Studio sync.

---

## Phase 1 — Backend: Crawler + API  *(∥ with Phase 3)*

- [x] **T1.1 Match model + normalizer** — Pydantic models (`app/models.py`) match the contract; `crawler.build_kickoff` parses HH:MM → tz-aware datetime (Europe/Moscow), `derive_status` from kickoff vs now, 40-hex validation lives in the `Stream` model. Tested.

- [x] **T1.2 Listing crawler** — `app/scraper/crawler.py`: httpx + selectolax, selectors per recon §2. Two live-data fixes after testing against the real site: (a) **multi-day** — the listing spans ~4 days grouped by `<div class="streams-day">6 июня</div>` headers; the crawler now parses Russian dates per day-block instead of stamping all as today; (b) **live matches** show the game clock (`13'`) + `liveTime` class instead of HH:MM → detected as `live`, kickoff derived from elapsed minutes. 10 crawler tests + verified live (14 matches across 2026-06-06…09).

- [x] **T1.3 Cache + scheduler** — `app/scheduler.py`: `AsyncIOScheduler`, listing refresh + resolution jobs on env-configurable cadences; `store.merge_listing` carries resolved streams across re-crawls. Initial crawl on boot so the API is never empty.

- [x] **T1.4 API endpoints** — Endpoints now serve **real crawled data** in live mode (`PTV_MOCK_MODE=false`). Verified: app boots → scheduler → 6 real matches via `/api/matches`, health green. Requests served from cache, never blocking on a scrape.

- [x] **T1.5 Health & observability** — `/api/health` reports `lastSuccessfulCrawl` + counts; crawler logs an **R2 error on 0-parse** and health returns `unhealthy` when `matchCount==0`.

> **Phase 1 complete + T2.3 fully wired:** the scheduler's `resolve_due` calls the Phase 2 resolver for in-window matches and flips `hasStream`/`streams` (clearing on finish). Match-page URL uses an id-only slug, which the site 301-redirects to canonical (`follow_redirects=True`). Live stream resolution itself stays **provisional** on the real markup (T0.1) — tonight's 17:45 window is the first real test.

---

## Phase 2 — Backend: Stream Extractor

- [x] **T2.1 Extractor interface + fixture tests** — `Extractor` protocol + `AceStreamHtmlExtractor` (`app/scraper/extractor.py`). **Validated against REAL live captures (T0.1 done):** Strategy 0 parses `table.broadcast-table` rows → content ID + quality (1080p); anchor + regex sweep remain as fallbacks; dedup, 40-hex validation, SopCast dropped. 10 fixture tests pass incl. the two real live matches. No longer provisional.

- [ ] **T2.2 Playwright renderer** — *Likely unnecessary.* JS analysis (recon §4a) found no AJAX loader → links appear server-rendered, so the cheap httpx path (T2.3) should suffice. Keep `recon_capture.py` as fallback; only build this if the live capture proves links are JS-injected late.
  - Deps: T2.1

- [~] **T2.3 Window-gated resolution job** — Core built (`app/scraper/resolver.py`): `in_resolution_window` / `should_resolve` (≤75 min before kickoff, skip finished) + `resolve_streams` cheap-path (httpx GET → extractor, empty on error). 5 tests pass (incl. httpx MockTransport). **Remaining:** wire into the APScheduler loop + flip `hasStream`/`streams` on the store — lands with Phase 1 (T1.3 store/scheduler).
  - Deps: T2.1, ~~T2.2~~, T1.3

- [x] **T2.4 Recon harness (fallback)** — Covered by `backend/scripts/recon_poll.py` (stdlib poller that auto-captures any match entering its live window). Running now against today's matches.

---

## Phase 3 — TV App  *(migrated to Jetpack Compose for TV)*

> **UI stack change:** replaced classic Leanback with **Jetpack Compose for TV** (`androidx.tv:tv-material` 1.0.0 + Compose BOM, Coil for images) to match the modern Android TV design system (Featured hero, focus-scaled cards). Data layer (Retrofit/Gson) unchanged.

- [x] **T3.1 API client + DTOs** — Retrofit/Gson client + DTOs from the contract + `MatchRepository` (`data/`). Drives the live UI on the emulator.

- [x] **T3.2 Browse screen** — Compose `BrowseScreen`: a `LazyColumn` with a **Featured hero** + `LazyRow` rows "Live now / Football / Hockey" of focus-scaled `MatchCard`s; overscan-safe margins, enlarged TV type, dark high-contrast theme. **Verified on the Television_4K emulator**: real mock data, real team logos (Coil), D-pad navigation. See `docs/screenshot-browse.png`, `screenshot-rows.png`.

- [x] **T3.3 LIVE/link badge** — `LiveBadge` on cards + hero, driven by `hasStream`/status (FR-2, FR-4). Visible in screenshots.

- [x] **T3.4 ~~Detail screen~~ → removed by design** — Per product decision, there is **no detail page**. Selecting a match with a link launches Ace Stream directly (fewer remote clicks). Live cards show an inline "▶ Watch" affordance; non-live shows a "links appear ~1h before" message (FR-8). The hero carries this too.

- [x] **T3.5 Polling refresh** — Lifecycle-aware polling (`PimpleApp` `repeatOnLifecycle(RESUMED)` loop, 60s) calls `MatchViewModel.poll()` — a silent refresh that keeps the last good data (no blanking, no error flash on transient failures). **Verified on the emulator**: 2 fetches in 65s foreground, **0 while backgrounded**, immediate refresh on return.

---

## Phase 4 — Ace Stream Hand-off

- [x] **T4.1 Launcher** — `acestream/AceStream.kt`: `launch()` builds an `acestream://<id>` ACTION_VIEW intent with NEW_TASK, handles content-id vs full-URI (§5.3). **Verified end-to-end on the emulator**: Watch → Ace Stream (`org.acestream.node/ContentStartActivity`) received the content id and began loading. See `docs/screenshot-acestream-launch.png`.

- [x] **T4.2 Install detection + prompt** — Detection resolves the `acestream://` VIEW intent (robust to package differences), falls back to a package list; if absent, a `MessageDialog` with sideload guidance (FR-7, R3). **Required an Android 11+ `<queries>` manifest entry** (scheme `acestream` + packages) — without it, detection AND launch silently fail (this was the "says I don't have it" bug).

- [x] **T4.3 Package-name verification** — Real package on the test device is **`org.acestream.node`** (not the PRD's `org.acestream.media*`); added to the list + `<queries>`. Confirmed via `pm query-activities` (R5).

- [x] **T4.4 Stream chooser** — `StreamChooser` overlay (`ui/Overlays.kt`): single stream launches directly, multiple shows a compact quality/source picker before launch (FR-6). Modal, not a page.

---

## Phase 5 — Polish & States

- [ ] **T5.1 No-link-yet state** — Countdown / "links appear ~1h before kickoff" when `!hasStream` and kickoff is future (FR-8).
  - Deps: T3.4
  - Done when: future-kickoff match shows countdown, not an empty Watch.

- [ ] **T5.2 Loading & empty states** — Splash → first API call; empty-list and API-unreachable (cached + staleness banner) states.
  - Deps: T3.5
  - Done when: each state renders correctly with forced conditions.

- [ ] **T5.3 Launch-error state** — Handle `ActivityNotFoundException` and bad/expired content IDs gracefully.
  - Deps: T4.1
  - Done when: an invalid content ID shows a friendly error, not a crash.

- [x] **T5.4 Backend deploy (Raspberry Pi)** — Deployed dockerized on the Pi (`pi@192.168.0.56`, aarch64/Debian 12) in **live mode on port 8090** (8000 = Portainer), `restart: unless-stopped`. `docker-compose.pi.yml` + one-command `deploy-pi.sh` (rsync → rebuild → health). Reachable on the LAN at **http://pimpletv.pi:8090/** via a Pi-hole local DNS record (`pimpletv.pi → 192.168.0.57`). App base URL points at the domain (release) / Pi IP (debug). **Verified end-to-end**: emulator app loads the Pi's 14 real matches (`docs/screenshot-pi-backend.png`). *(VPS/HTTPS from the original PRD not needed — it's a private LAN box per the Pi decision.)*

- [ ] **T5.5 End-to-end integration pass** — App on real TV → deployed backend → real match → Ace Stream launch.
  - Deps: T4.3, T5.4
  - Done when: full happy path verified on hardware during a live match window.

---

## Phase 6 — Legal Gate  *(blocks distribution)*

- [ ] **T6.1 Legal review (R1)** — Obtain a rights/copyright assessment before any public distribution. Document a go/no-go decision.
  - Deps: (none technically, but gates release)
  - Done when: written go/no-go recorded; until "go", build stays private/personal-use.

---

## Critical Path

```
T0.1 ─┐
T0.2 ─┴─> T0.3 ─> T0.4 ─┐
                        ├─> T3.1 ─> T3.2 ─> T3.4 ─> T4.1 ─> T4.2 ─> T4.3 ─┐
T0.1 ─> T2.1 ─> T2.2 ─> T2.3 ─────────────────────────────────────────┐  │
T0.3 ─> T1.1 ─> T1.2 ─> T1.4 ─> (T3.5) ───────────────────────> T5.4 ─┴──┴─> T5.5 ─> T6.1
```

**Start now (no deps):** T0.1, T0.2, T0.5. Freeze the contract (T0.3) as fast as possible — it unblocks both tracks.
