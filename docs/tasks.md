# Implementation Tasks — PimpleTV TV Launcher

**Companion to:** [project-prd.md](project-prd.md), [integration-plan.md](integration-plan.md)
**Date:** 5 June 2026

Ordered, step-by-step tasks. Each has an ID, dependencies, and a clear "Done when". Tasks within a phase marked **∥** can run in parallel. Check off as you go.

Legend: `[ ]` todo · `[~]` in progress · `[x]` done · **(blocker)** must clear before dependents.

---

## Phase 0 — Recon & Contract Freeze

> **Deployment target:** backend runs **dockerized on a local Raspberry Pi (arm64)**. Runtime image is browserless (`httpx` + `selectolax`); Playwright is recon/fallback only, kept out of the Pi image.

- [~] **T0.1 Live-page recon (S1)** — Open a match page within ~1h of kickoff with browser dev-tools. Capture the exact AJAX endpoint + request headers + JSON/HTML response carrying the Ace Stream content IDs.
  - Deps: none · **(blocker for T2.x)**
  - Done when: raw request/response saved to `backend/tests/fixtures/live_match_<id>.{html,json}` and the field path to the 40-char content ID is documented.
  - **Status:** JS analysis done — **no script fetches stream links** (`ajax-tabs.js` is tab-switching only; `detect.js` is adblock/ads). Hypothesis: links are **server-rendered** within the window, not JS-injected → likely **no browser needed on the Pi**. Cheap-path poller `backend/scripts/recon_poll.py` (stdlib, no browser) is **running** to capture the first live window (~18:00 MSK today); Playwright `recon_capture.py` is the fallback. See [recon-findings.md §4](recon-findings.md).

- [x] **T0.2 Listing-page recon** — Save static HTML of `/`, `/category/football/`, `/category/hockey/` and a few match pages (pre-window). Identify selectors for teams, kickoff, tournament, channel, stadium, logos.
  - Done: fixtures saved under `backend/tests/fixtures/` (`listing_*.html`, `match_69175.html`, `wp_post_69175.json`); selector map in [recon-findings.md](recon-findings.md). Site is WordPress; metadata is in static HTML (no browser needed).

- [x] **T0.3 Freeze API contract** — `docs/api/openapi.yaml` authored (endpoints from integration-plan §3, `Match`/`MatchSummary` from PRD §6 + `lastUpdated`, `{error:{code,message}}` envelope). Mirrored in `backend/app/models.py`.

- [x] **T0.4 Stand up mock API server** — FastAPI app runs in `PTV_MOCK_MODE` serving sample matches that satisfy the contract. Smoke-tested: list/detail/health/404/422 all verified. (Chose a FastAPI mock over Prism so it's the same stack as production and runs on the Pi.)

- [x] **T0.5 Repo scaffold (backend)** — `backend/` created: FastAPI app, models, store, config, routes, sample data, **Dockerfile (arm64) + docker-compose**, recon script, README. Runs end-to-end locally.
  - [x] **T0.5b androidtv scaffold** — Kotlin + Leanback project in `androidtv/` (Gradle Kotlin DSL + version catalog, wrapper included; AGP 8.7.3 / Gradle 8.11.1; minSdk 21 / target 35). Browse skeleton (`BrowseSupportFragment` + `MatchCardPresenter`) wired to the contract via Retrofit/Gson; LEANBACK_LAUNCHER manifest, TV banner, `Theme.Leanback`. **Validated:** Gradle wrapper bootstraps on Studio's bundled JDK 21 and `:app:help` configures cleanly (AGP + catalog resolve). Full APK build pending SDK 35 install on first Studio sync.

---

## Phase 1 — Backend: Crawler + API  *(∥ with Phase 3)*

- [ ] **T1.1 Match model + normalizer** — Pydantic `Match`/`Team`/`Stream` models matching the contract; helpers to validate 40-char hex content IDs and parse kickoff to ISO+tz.
  - Deps: T0.3
  - Done when: model round-trips the OpenAPI examples; unit tests pass.

- [ ] **T1.2 Listing crawler** — Fetch + parse the three listing pages → `Match[]` metadata (no streams). Plain HTTP (httpx), fixture-tested.
  - Deps: T0.2, T1.1 · **(blocker for T1.4)**
  - Done when: crawler parses `listing_*.html` fixtures into correct `Match` objects; live smoke run returns today's matches.

- [ ] **T1.3 Cache + scheduler** — In-memory (or Redis) store; APScheduler job refreshing listings every 2–5 min (configurable).
  - Deps: T1.1
  - Done when: store holds latest crawl; refresh interval configurable via env.

- [ ] **T1.4 API endpoints** — FastAPI serving `/api/matches`, `/api/matches/{id}`, `/api/health` from cache (never block on a live scrape).
  - Deps: T1.2, T1.3 · **(blocker for T3.5)**
  - Done when: endpoints return real crawled data and pass contract validation against `openapi.yaml`.

- [ ] **T1.5 Health & observability** — `/api/health` reports last successful crawl time + match count; alarm/log when 0 matches parsed (R2 early-warning).
  - Deps: T1.4
  - Done when: health flips to unhealthy on a forced parse failure.

---

## Phase 2 — Backend: Stream Extractor

- [x] **T2.1 Extractor interface + fixture tests** — `Extractor` protocol + `AceStreamHtmlExtractor` (`app/scraper/extractor.py`): anchor-aware + regex sweep, per-link quality/language, dedup, 40-hex validation, SopCast dropped, bare-hex ignored without Ace Stream context. 8 fixture tests pass (positive = synthetic populated tab; negative = real `match_69175.html` placeholder).
  - **Provisional:** synthetic fixture stands in until the real live payload (T0.1) lands; if real markup differs, adjust only the selectors/patterns — the protocol stays. See [recon-findings.md §4](recon-findings.md).

- [ ] **T2.2 Playwright renderer** — *Likely unnecessary.* JS analysis (recon §4a) found no AJAX loader → links appear server-rendered, so the cheap httpx path (T2.3) should suffice. Keep `recon_capture.py` as fallback; only build this if the live capture proves links are JS-injected late.
  - Deps: T2.1

- [~] **T2.3 Window-gated resolution job** — Core built (`app/scraper/resolver.py`): `in_resolution_window` / `should_resolve` (≤75 min before kickoff, skip finished) + `resolve_streams` cheap-path (httpx GET → extractor, empty on error). 5 tests pass (incl. httpx MockTransport). **Remaining:** wire into the APScheduler loop + flip `hasStream`/`streams` on the store — lands with Phase 1 (T1.3 store/scheduler).
  - Deps: T2.1, ~~T2.2~~, T1.3

- [x] **T2.4 Recon harness (fallback)** — Covered by `backend/scripts/recon_poll.py` (stdlib poller that auto-captures any match entering its live window). Running now against today's matches.

---

## Phase 3 — TV App: Skeleton  *(∥ with Phase 1, against mock)*

- [ ] **T3.1 API client + DTOs** — Generate DTOs from `openapi.yaml`; Retrofit/OkHttp client; coroutine repository.
  - Deps: T0.3, T0.4 · **(blocker for T3.2)**
  - Done when: client fetches from the mock server and maps to DTOs in a unit test.

- [ ] **T3.2 Browse screen (Leanback)** — `BrowseSupportFragment` with rows "Live now", "Football today", "Hockey today"; focusable cards (teams, kickoff, tournament) with Glide-loaded logos.
  - Deps: T3.1 · **(blocker for T3.3)**
  - Done when: rows render mock data; full D-pad navigation works on emulator.

- [ ] **T3.3 LIVE/link badge** — Card overlay driven by `hasStream` (FR-2, FR-4).
  - Deps: T3.2
  - Done when: cards visibly differ for `hasStream` true vs false.

- [ ] **T3.4 Detail screen** — Match info (channel, stadium, time); "Watch" button enabled only when `hasStream` (FR-10).
  - Deps: T3.2
  - Done when: selecting a card opens detail; Watch enabled/disabled correctly.

- [ ] **T3.5 Polling refresh** — Lifecycle-aware repository polling every 2–5 min; pause when backgrounded; swap mock → real API base URL.
  - Deps: T3.1, T1.4
  - Done when: list auto-updates against the real backend; no polling while backgrounded.

---

## Phase 4 — Ace Stream Hand-off

- [ ] **T4.1 Launcher** — `launchAceStream(contentId)` building `acestream://<id>` ACTION_VIEW intent with NEW_TASK (PRD §5.1); content-ID vs full-URI handling (§5.3).
  - Deps: T3.4 · **(blocker for T4.2)**
  - Done when: Watch launches Ace Stream with a real content ID on a TV device.

- [ ] **T4.2 Install detection + prompt** — `isAceStreamInstalled()` across `org.acestream.media.atv` / `org.acestream.media`; if missing, show install-prompt screen with documented APK source (FR-7, R3).
  - Deps: T4.1
  - Done when: with Ace Stream uninstalled, the prompt shows instead of a crash.

- [ ] **T4.3 Package-name verification on device** — Confirm actual Ace Stream TV package name(s) on the target hardware; update the detection list (R5).
  - Deps: T4.2
  - Done when: detection list matches the real installed package on the test TV.

- [ ] **T4.4 Stream chooser** — When `streams.length > 1`, show a quality/source picker before launch (FR-6).
  - Deps: T4.1
  - Done when: multi-stream match shows chooser; single-stream launches directly.

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

- [ ] **T5.4 Backend deploy** — Containerize; deploy to a VPS in a permitted egress region (R4); HTTPS; configure refresh cadence.
  - Deps: T1.5, T2.3
  - Done when: app points at the deployed URL and works end-to-end.

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
