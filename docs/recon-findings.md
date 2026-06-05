# Recon Findings — pimpletv.ru

**Tasks:** T0.1 (live recon — *partial, see §4*), T0.2 (listing recon — **done**)
**Date:** 5 June 2026
**Fixtures:** `backend/tests/fixtures/`

---

## 1. Site platform

- **WordPress.** Match pages are WP posts; `post_id == match_id` (e.g. `/wp-json/wp/v2/posts/69175`).
- Listing & match **metadata is in static server HTML** — `httpx` is sufficient, **no headless browser needed for metadata.** (Confirmed: `curl` returns full match cards.)
- The WP REST API (`/wp-json/wp/v2/posts/{id}`) returns `content.rendered` but `meta` is empty (no structured kickoff/stadium fields). Parse the HTML instead.
- **Implication for the Raspberry Pi:** the production scraper can run on pure `httpx` + `selectolax`/`lxml`. Playwright is **only** a recon/fallback tool and should NOT be in the Pi runtime image.

## 2. Listing pages (T0.2 — done)

Pages: `/`, `/category/football/`, `/category/hockey/`. Each match is an `<a class="match-item _rates">` with:

| Field | Selector (relative to `a.match-item`) |
|---|---|
| Match URL / id | `@href` → `/{sport}/{id}-{home}-{away}/` |
| Sport | from URL path or `.match-item__logo-sport img@src` |
| Kickoff time (HH:MM, local MSK) | `.match-item__title-date > div` |
| Tournament | `.match-item__title-tournament` |
| Home name | `.table-item.home .table-item__home-name` |
| Home logo | `.table-item.home .table-item__logo img@src` |
| Away name | `.table-item.away .table-item__away-name` |
| Away logo | `.table-item.away .table-item__logo img@src` |
| Channel | `.match-item__status .match-item__logo-channel` |

Logo URLs are root-relative (`/wp-content/uploads/logo/...`) → prefix with `https://www.pimpletv.ru`.
Kickoff is **time-only** on listings; the date is "today" (site lists today's matches). Full date + stadium come from the match page (§3). Timezone is **Europe/Moscow (UTC+3)**.

## 3. Match page (T0.2 — done)

- Stadium + date are in the "Превью" tab prose and a `.match-text` block, e.g. *"стадионе Волгоград Арена (Волгоград). 20:00 … дата – 5 июня 2026"*.
- The stream area is a tabbed widget:
  ```
  div.tabs
    ul.tabs-caption > li.active "Трансляция"   (broadcast/stream tab)
    div.tabs-content.active                     ← STREAM LINKS GO HERE
    div.tabs-content > div.match-text           (SEO prose, "Превью")
  ```
- **Pre-window state:** `div.tabs-content.active` contains only the placeholder:
  `<p>Ссылки на трансляцию появятся приблизительно за час до эфира.</p>`
  → presence of this string ⇒ `hasStream = false`.

## 4. Stream links — the critical unknown (T0.1 — IN PROGRESS)

### 4a. JS analysis (done) — *the PRD's "JS-injected" assumption looks wrong*

Inspected every script the match page loads:

| Script | What it does | Loads streams? |
|---|---|---|
| `themes/rufootballtv/js/ajax-tabs.js` | Tab **switching UI only** (misnamed — no AJAX) | No |
| `themes/rufootballtv/js/detect.js` | Adblock detection + Melbet ad injection; removes `.tabs` if adblock | No |
| `twentythirteen/js/functions.js`, `jquery.min.js` | Theme/jQuery boilerplate | No |

**No script fetches stream data.** There is no `admin-ajax`/XHR loader. → Strong hypothesis: the links are **server-side rendered** into `div.tabs-content.active` within the ~1h window, *not* JS-injected. If confirmed, **the Pi scraper needs no browser at all** — plain `httpx` of the match page suffices, and there is no AJAX endpoint to reverse-engineer.

Fixtures saved: `ajax-tabs.js`, `detect.js`.

### 4b. Live capture (running) — cheap-path-first

`backend/scripts/recon_poll.py` (stdlib `urllib`, **no browser**) polls today's match pages every 5 min and captures the first matches whose tab stops showing the placeholder. Confirmed pre-window: it correctly reports the placeholder state as not-populated.

- **If it captures links** → hypothesis confirmed, server-rendered, no browser on the Pi. Document the exact link markup below.
- **If it times out at kickoff with the placeholder still showing** → links really are JS-injected late; fall back to `scripts/recon_capture.py` (Playwright).

Window math: earliest kickoff today 19:00 MSK → first window ~18:00 MSK / 15:00 UTC.

> ⏳ **Pending:** live-window capture output. The Ace Stream content-ID field path / link markup will be filled in here once `recon_poll.py` captures a populated tab.

**Still required (time-sensitive, manual):** open a match page **within ~1h of kickoff** with browser dev-tools Network panel and capture:
1. The XHR/fetch **request** the JS makes (URL, method, headers, query/body — likely `admin-ajax.php?action=...` or a custom endpoint).
2. The **response** payload and the exact field path to the 40-char hex content ID / `acestream://` URI.
3. Save both to `backend/tests/fixtures/live_match_<id>.{json,html}`.

→ Use `backend/scripts/recon_capture.py` (Playwright) to automate this capture during a live window.

**Decision gate:** if the JS hits a plain JSON/AJAX endpoint, the Pi scraper replicates it with `httpx` (no browser). If links are computed client-side from obfuscated JS, Playwright stays as a fallback — but ideally as a *separate* container the Pi runs only during live windows, not the always-on API.

## 5. Captured fixtures

| File | What |
|---|---|
| `listing_home.html` / `listing_football.html` / `listing_hockey.html` | Listing pages (HTTP 200) |
| `match_69175.html` | Pre-window match page (placeholder state) |
| `wp_post_69175.json` | WP REST API sample (shows empty `meta`) |
| `live_match_*.{json,html}` | **TODO** — capture during a live window (T0.1) |
