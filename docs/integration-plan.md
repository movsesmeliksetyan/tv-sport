# Integration Plan — PimpleTV TV Launcher

**Companion to:** [project-prd.md](project-prd.md)
**Version:** 0.1
**Date:** 5 June 2026
**Status:** Implementation planning

> ⚠️ **Gate before distribution:** This plan assumes a private / educational / personal-use build. The legal review (PRD R1) must be cleared before any public distribution. All milestones below are buildable in parallel with that review, but **M5 (legal go/no-go) blocks release**.

---

## 1. System Shape

Two deployable units plus a third-party hand-off:

```
[Android TV App] ──HTTPS/JSON──> [Backend Scraper/API] ──render/scrape──> [pimpletv.ru]
       │
       └─ acestream:// intent ──> [Ace Stream Media Center (TV)]
```

| Unit | Tech | Repo / dir |
|---|---|---|
| Backend Scraper/API | Python 3.11, Playwright, FastAPI, APScheduler | `backend/` |
| Android TV App | Kotlin, AndroidX Leanback, Retrofit, Glide, Coroutines | `androidtv/` |
| Contract | OpenAPI 3.1 + JSON Schema (shared) | `docs/api/` |

The **API contract is the integration seam**. Lock it early (Phase 1) so backend and app can be built in parallel against a mock.

---

## 2. The Critical Unknown (S1) — resolve first

Everything downstream depends on the **shape of the stream-link payload**, which only exists ~1h before kickoff and is JS-injected. Until S1 is captured, the scraper's extraction layer is a guess.

**De-risking strategy:**
1. Do a live recon session (PRD §2, S1) and record the exact request/response.
2. Encode the finding as a **fixture** (`backend/tests/fixtures/live_match_*.html|.json`).
3. Build the extractor against the fixture (TDD), so the live-only window isn't needed to iterate.
4. Keep the rest of the pipeline (listing scrape, API, app) independent of S1 so they can proceed in parallel.

If S1 cannot be captured in time, fall back to a **scheduled recon harness** (a job that auto-captures any match entering its live window and dumps the payload for inspection).

---

## 3. API Contract (the integration seam)

Freeze these two endpoints first; build everything against them.

```
GET /api/matches?sport=football|hockey&window=today
    -> { matches: Match[] }            // metadata + hasStream flag, streams omitted

GET /api/matches/{id}
    -> Match                           // full detail incl. resolved streams[]

GET /api/health                        // scraper freshness + last successful crawl
```

`Match` shape per PRD §6. Additions for robustness:
- `hasStream: boolean` is the **only** field the browse grid needs for the badge — keep it cheap.
- `streams[]` resolved lazily / only in detail endpoint.
- `lastUpdated` (ISO) per match so the app can show staleness.
- Standard error envelope: `{ error: { code, message } }`.

Deliverable: `docs/api/openapi.yaml` + a runnable **mock server** (Prism or FastAPI stub) so the app team isn't blocked on the scraper.

---

## 4. Backend Plan

**Layers (keep extraction isolated — it's the fragile part):**
1. **Crawler** — fetch listing pages (`/`, `/category/football/`, `/category/hockey/`), parse match anchors → match metadata. Plain HTTP is enough here (static HTML).
2. **Extractor** — for matches in the link window (`kickoff - now <= 75 min`), render the match page (Playwright) and pull Ace Stream content IDs. This is the only part that needs a headless browser.
3. **Normalizer** — map raw scrape → `Match` model; validate content IDs (40-char hex); drop SopCast for v1.
4. **Store + scheduler** — in-memory/Redis cache; APScheduler refreshes listings every 2–5 min and stream resolution only inside live windows.
5. **API** — FastAPI serving the frozen contract from cache (never block a request on a live scrape).

**Operational concerns:**
- Respect source: single shared crawl, sane cadence, conditional requests / backoff.
- Geo: source may be geo-blocked (R4) — provision egress accordingly (proxy/VPS region).
- Resilience: site changes break parsing (R2) — extraction behind an interface with fixture-based tests and a health endpoint that flags "0 matches parsed".

---

## 5. Android TV App Plan

**Module/screen structure (Leanback, D-pad-first):**
- `data/` — Retrofit API client, DTOs (generated from OpenAPI), repository with polling refresh.
- `ui/browse/` — `BrowseSupportFragment`: rows "Live now", "Football today", "Hockey today"; focusable cards with a LIVE/link badge.
- `ui/detail/` — match info + "Watch" button enabled only when `hasStream`.
- `ui/chooser/` — stream/quality picker (FR-6) when `streams.length > 1`.
- `acestream/` — launcher + install detection (PRD §5).
- `ui/states/` — loading, empty, no-link-yet (countdown), Ace-Stream-not-installed, launch-error.

**Integration touchpoints:**
- Poll the list endpoint every 2–5 min (lifecycle-aware; pause when backgrounded).
- Ace Stream hand-off via implicit `acestream://` intent; detect `org.acestream.media.atv` / `org.acestream.media`; verify package names on a real device (R5).
- Graceful degradation when API unreachable (cached last list + staleness banner).

---

## 6. Integration & Test Strategy

| Level | What | Where |
|---|---|---|
| Contract | App ↔ mock server (Prism) validates DTOs against OpenAPI | CI |
| Extractor | Fixture-based unit tests for stream-ID parsing (S1 payload) | `backend/tests` |
| Crawler | Recorded-HTML fixtures for listing parse | `backend/tests` |
| E2E (backend) | Live recon harness against a real match window | manual/scheduled |
| Hand-off | `acestream://` launch on a real TV with Ace Stream installed | device |
| App states | Each designed state rendered with mock data | device/emulator |

**Definition of integrated (per milestone):** the app, pointed at the real backend, lists matches, shows correct badges, and launches a real Ace Stream link on a TV device.

---

## 7. Phasing (maps to PRD milestones)

| Phase | PRD | Goal | Exit criteria |
|---|---|---|---|
| P0 | M0/S1 | Recon + contract freeze | Live payload captured as fixture; `openapi.yaml` + mock server live |
| P1 | M1 | Backend crawler + API | List endpoint serves real metadata; health endpoint green |
| P2 | M1 | Backend extractor | Stream IDs resolved from fixture + verified live once |
| P3 | M2 | TV app skeleton | Browse + detail consuming mock, then real API |
| P4 | M3 | Ace Stream hand-off | Real `acestream://` launch + install handling on device |
| P5 | M4 | Polish + states | Refresh, badges, countdown, all error states |
| P6 | M5 | Legal review gate | Documented go/no-go — **blocks distribution** |

P1–P2 (backend) and P3 (app skeleton) run in **parallel** once the contract is frozen in P0.

---

## 8. Risks → Mitigations (from PRD §11)

| Risk | Mitigation in this plan |
|---|---|
| S1 unknown payload | Capture-as-fixture + recon harness; isolate extractor behind interface |
| R1 legal | P6 gate blocks release; build stays private until cleared |
| R2 scraping breakage | Extractor interface + fixtures + health alarm on 0-parse |
| R3 Ace Stream sideload UX | Dedicated install-prompt screen with documented APK source |
| R4 geo-block | Backend egress in a permitted region / proxy |
| R5 package names | Multi-package detection + on-device verification task |

---

*See [tasks.md](tasks.md) for the ordered, actionable task breakdown.*
