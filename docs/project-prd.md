# Product Requirements Document — Android TV Sports + Ace Stream Launcher

**Project codename:** PimpleTV TV Launcher
**Source site:** https://www.pimpletv.ru/
**Document version:** 0.1 (Draft)
**Date:** 5 June 2026
**Status:** Pre-development / technical architecture draft

---

## 0. Legal & Risk Notice (read first)

This is the single most important section. The source site aggregates **Ace Stream** and **SopCast** links to live football and hockey broadcasts. Live sports broadcasts are protected by copyright/broadcasting rights in essentially every jurisdiction.

- An app that scrapes and re-surfaces these streams is very likely facilitating access to **unlicensed/pirated** content.
- It **will not be accepted on Google Play** and could expose the developer/distributor to copyright-infringement liability (DMCA takedowns, rights-holder claims, regional anti-piracy law).
- The source site itself is positioned behind VPN/proxy messaging, indicating it is blocked in some regions.

**Recommendation:** Treat this PRD as a *technical* specification. Before any public distribution, obtain a clear legal assessment of the rights situation. The technical work below is straightforward; the legal exposure is the real project risk.

The remainder of this document assumes a private/educational/personal-use build unless the legal situation is cleared.

---

## 1. Overview

### 1.1 Problem statement
A user with an Android TV device wants to browse the sports matches listed on pimpletv.ru, see which matches have live Ace Stream links available, and launch a selected match directly in the Ace Stream Media Center app — all using a TV remote (D-pad), without a browser or keyboard.

### 1.2 Goal
Build a native Android TV app that:
1. Aggregates the match list (football + hockey) from the source.
2. Indicates which matches currently have Ace Stream links (links only appear ~1h before kickoff).
3. On match selection, resolves and launches the `acestream://<content_id>` link in the installed Ace Stream app.

### 1.3 Non-goals
- Playing the stream inside our own app (we hand off to Ace Stream).
- Hosting, caching, or re-broadcasting any video content.
- User accounts, betting integration, or social features.

---

## 2. Source Site Analysis (findings)

| Aspect | Finding |
|---|---|
| Listing pages | Homepage `/`, `/category/football/`, `/category/hockey/` list matches as anchor links. |
| Match URL pattern | `/{sport}/{id}-{home}-{away}/` e.g. `/football/69175-russia-burkina-faso/`. |
| Match metadata available | Teams, kickoff time, tournament, stadium, TV channel, team logos, odds. |
| Stream link availability | **Links appear only ~1 hour before kickoff.** Before that the page shows a placeholder ("Ссылки на трансляцию появятся приблизительно за час до эфира"). |
| Link delivery | Ace Stream/SopCast links are **not in the static server HTML** at view time — they are injected dynamically (JS/AJAX). The scraper must render JS or call the underlying data endpoint. |
| Link format expected | Ace Stream content ID (40-char hex hash) and/or `acestream://` URI, plus possibly SopCast (`sop://`) links. |

> **Open item (S1):** Inspect a *live* match page (within 1h of kickoff) with browser dev-tools to capture the exact AJAX endpoint and JSON/HTML shape that carries the Ace Stream content IDs. This is the critical unknown and must be done before scraper implementation.

---

## 3. Architecture

### 3.1 Recommended high-level design

```
┌──────────────────────┐        HTTPS/JSON        ┌─────────────────────────┐
│  Android TV App      │  ───────────────────────▶ │  Backend Scraper/API    │
│  (Kotlin, Leanback)  │ ◀───────────────────────  │  (server you control)   │
│                      │   match list + stream IDs │                         │
└─────────┬────────────┘                           └───────────┬─────────────┘
          │ acestream:// intent                                 │ scrape/render
          ▼                                                     ▼
┌──────────────────────┐                           ┌─────────────────────────┐
│  Ace Stream Media    │                           │   pimpletv.ru           │
│  Center (TV build)   │                           │                         │
└──────────────────────┘                           └─────────────────────────┘
```

**Why a backend, not on-device scraping:**
- Scraping logic breaks when the site changes; a backend lets you fix it without shipping app updates.
- JS rendering (headless browser) is heavy/impractical on a TV device.
- One scrape serves all clients; lighter on the source site and the TV.
- Keeps fragile parsing out of the shipped binary.

### 3.2 Components

**A. Backend Scraper/API**
- Tech: Python (Playwright/Selenium for JS rendering) or Node (Puppeteer). Plain `requests` is insufficient because links are JS-injected.
- Responsibilities:
  - Crawl listing pages → match list with metadata.
  - For matches within the link window, fetch the match page (rendered) and extract Ace Stream content IDs / `acestream://` URIs.
  - Normalize into a clean JSON API.
  - Cache results; respect a sane refresh cadence.
- Endpoints (proposed):
  - `GET /api/matches?sport=football|hockey` → list with metadata + `hasStream` flag.
  - `GET /api/matches/{id}` → full detail incl. resolved `streams[]`.

**B. Android TV App**
- Tech: Kotlin, AndroidX **Leanback** (BrowseSupportFragment / VerticalGridSupportFragment), Glide for images, Retrofit/OkHttp for API.
- Min SDK: API 21+ (Android TV baseline); target latest.
- D-pad-first navigation, focusable cards, no touch assumptions.

**C. Ace Stream hand-off**
- Launch via intent (see §5).

---

## 4. Functional Requirements

| ID | Requirement | Priority |
|---|---|---|
| FR-1 | Display a browse screen with rows/grid for Football and Hockey matches. | Must |
| FR-2 | Each match card shows teams, kickoff time, tournament, and a "LIVE/link available" badge. | Must |
| FR-3 | Periodically refresh the list (configurable; e.g. every 2–5 min). | Must |
| FR-4 | Visually distinguish matches that have an available Ace Stream link from those that don't yet. | Must |
| FR-5 | On selecting a match with a link, launch the Ace Stream app via `acestream://` intent. | Must |
| FR-6 | If a match has multiple links/qualities, present a chooser before launch. | Should |
| FR-7 | If Ace Stream app is not installed, show a message + deep link to install it. | Must |
| FR-8 | Handle "no link yet" gracefully (show kickoff countdown / "links appear ~1h before"). | Must |
| FR-9 | Full D-pad navigation; no reliance on touch or pointer. | Must |
| FR-10 | Detail screen showing match info, channel, stadium, and available stream(s). | Should |

---

## 5. Ace Stream Integration (technical detail)

### 5.1 Launching the stream
Ace Stream Media Center registers handlers for `acestream://` URIs and content IDs.

```kotlin
fun launchAceStream(context: Context, contentId: String) {
    val uri = Uri.parse("acestream://$contentId") // 40-char hex content id
    val intent = Intent(Intent.ACTION_VIEW, uri).apply {
        // Prefer the Android TV build if present, else fall back.
        // Common packages: org.acestream.media (mobile),
        //                  org.acestream.media.atv (TV)
        addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
    }
    try {
        context.startActivity(intent)
    } catch (e: ActivityNotFoundException) {
        promptInstallAceStream(context)
    }
}
```

### 5.2 Detecting installation / prompting install
```kotlin
fun isAceStreamInstalled(context: Context): Boolean {
    val pm = context.packageManager
    return listOf("org.acestream.media.atv", "org.acestream.media").any { pkg ->
        try { pm.getPackageInfo(pkg, 0); true } catch (e: Exception) { false }
    }
}
```
If not installed, direct the user to the Ace Stream APK/store listing (Ace Stream is generally **not** on Google Play; sideloading the TV build is typical — document this for the user).

### 5.3 Content ID vs full URI
- If the source provides a full `acestream://...` URI, pass it through as `ACTION_VIEW`.
- If it provides only a 40-char hex hash, wrap it as `acestream://<hash>`.
- If it provides an HTTP "engine" URL or a `.acelive`/transport file, resolve to the content ID on the backend before sending to the TV.
- SopCast (`sop://`) links, if present, require the SopCast app and are out of scope for v1 (Ace Stream only).

---

## 6. Data Model (API contract)

```json
{
  "id": "69175",
  "sport": "football",
  "tournament": "Friendly. National teams",
  "home": { "name": "Russia", "logo": "https://.../russia.png" },
  "away": { "name": "Burkina Faso", "logo": "https://.../burkina_faso.png" },
  "kickoff": "2026-06-05T20:00:00+03:00",
  "channel": "MATCH! HD",
  "stadium": "Volgograd Arena",
  "status": "scheduled | live | finished",
  "hasStream": false,
  "streams": [
    { "type": "acestream", "contentId": "<40-char-hex>", "quality": "HD", "language": "ru" }
  ]
}
```

---

## 7. Refresh & Lifecycle Logic

- Match list: refresh every 2–5 min (configurable).
- Stream resolution: only attempt for matches with `kickoff - now <= ~75 min`.
- Mark `hasStream=true` only when at least one valid stream is resolved.
- Backend caches stream IDs for the match's live window; invalidate after `finished`.

---

## 8. UX / Screen Flow

1. **Splash** → load config + first API call.
2. **Browse (Leanback)** → rows: "Live now", "Football today", "Hockey today". Cards focusable via D-pad.
3. **Detail** → teams, time, channel, stadium; "Watch" button enabled only if `hasStream`.
4. **Stream chooser** (if multiple) → list of qualities/sources.
5. **Hand-off** → launch Ace Stream; if missing, install-prompt screen.

States to design: loading, empty (no matches), no-link-yet (countdown), Ace-Stream-not-installed, launch-error.

---

## 9. Tech Stack Summary

| Layer | Choice |
|---|---|
| TV app | Kotlin, AndroidX Leanback, Glide, Retrofit/OkHttp, Coroutines |
| Min/Target SDK | 21 / latest stable |
| Backend | Python + Playwright (or Node + Puppeteer) for JS-rendered scraping |
| API | REST/JSON over HTTPS |
| Hosting | Any small VPS / container host you control |
| Hand-off | Android implicit intent → `acestream://` |

---

## 10. Milestones

| # | Milestone | Output |
|---|---|---|
| M0 | Source recon (S1) | Confirmed AJAX endpoint + stream-link format from a live match |
| M1 | Backend scraper + API | JSON API serving match list + resolved streams |
| M2 | TV app skeleton (Leanback) | Browse + detail UI consuming the API |
| M3 | Ace Stream hand-off | Working `acestream://` launch + install handling |
| M4 | Polish + states | Refresh, badges, countdown, error states |
| M5 | Legal review gate | Go/no-go decision before any distribution |

---

## 11. Open Questions / Risks

| ID | Item |
|---|---|
| S1 | Exact AJAX endpoint and payload format carrying Ace Stream IDs (must capture live, ~1h before kickoff). |
| R1 | **Legal/rights exposure** — primary project risk. |
| R2 | Site structure/anti-bot changes can break scraping; plan for maintenance. |
| R3 | Ace Stream TV build availability/sideloading UX for end users. |
| R4 | Source site may be geo-blocked; backend may need appropriate egress. |
| R5 | Ace Stream package names may differ across builds/versions — verify on target device. |

---

*End of draft. Section S1 (live-page recon) and the legal review (R1) are the two gates that should be cleared before serious development.*
