"""T0.1 cheap-path recon poller — NO browser, stdlib only.

Hypothesis (from JS analysis): pimpletv.ru renders Ace Stream / SopCast links
SERVER-SIDE into div.tabs-content.active within ~1h of kickoff — they are NOT
JS-injected (no loader script exists; ajax-tabs.js only switches tabs).

This poller fetches today's match pages every few minutes and detects when the
placeholder ("появятся ... за час до эфира") is replaced by real link markup.
On the first populated match it saves the full HTML + the extracted tab block to
tests/fixtures/live_match_<id>.* and logs the link shape, then keeps going to
grab a second sample before exiting.

If links appear here (in raw curl/urllib output) the hypothesis holds and the Pi
scraper needs NO browser. If pages stay on the placeholder right up to kickoff,
fall back to scripts/recon_capture.py (Playwright).

Run (background): python scripts/recon_poll.py
Env: PTV_POLL_INTERVAL (s, default 300), PTV_POLL_TIMEOUT_MIN (default 360),
     PTV_POLL_SAMPLES (default 2)
"""
from __future__ import annotations

import os
import pathlib
import re
import time
import urllib.request
from datetime import datetime, timezone

BASE = "https://www.pimpletv.ru"
UA = "Mozilla/5.0 (X11; Linux aarch64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
FIX = pathlib.Path(__file__).resolve().parent.parent / "tests" / "fixtures"
LOG = FIX / "recon_poll.log"

PLACEHOLDER = "появятся"  # part of the pre-window placeholder text
LINK_MARKERS = ("acestream", "sop://", "sopcast", "infohash", "content_id", "/engine/", "acelive")

INTERVAL = int(os.environ.get("PTV_POLL_INTERVAL", "300"))
TIMEOUT_MIN = int(os.environ.get("PTV_POLL_TIMEOUT_MIN", "360"))
SAMPLES = int(os.environ.get("PTV_POLL_SAMPLES", "2"))


def log(msg: str) -> None:
    line = f"{datetime.now(timezone.utc).isoformat(timespec='seconds')}  {msg}"
    print(line, flush=True)
    FIX.mkdir(parents=True, exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def fetch(url: str) -> str | None:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            return r.read().decode("utf-8", "replace")
    except Exception as e:  # noqa: BLE001
        log(f"  fetch error {url}: {e}")
        return None


def list_today_matches() -> list[tuple[str, str]]:
    """Return [(match_id, full_url)] from football + hockey listings."""
    found: dict[str, str] = {}
    for sport in ("football", "hockey"):
        html = fetch(f"{BASE}/category/{sport}/")
        if not html:
            continue
        for href in re.findall(r'href="(/[a-z]+/(\d+)-[^"]+)"', html):
            path, mid = href
            found[mid] = BASE + path
    return sorted(found.items())


def extract_active_tab(html: str) -> str:
    m = re.search(r'<div class="tabs-content active">(.*?)</div>\s*<div class="tabs-content"', html, re.S)
    return m.group(1).strip() if m else ""


def is_populated(html: str) -> bool:
    tab = extract_active_tab(html)
    if not tab:
        # tab structure changed (or removed) — treat full-page marker scan as fallback
        tab = html
    low = tab.lower()
    if any(mk in low for mk in LINK_MARKERS):
        return True
    # populated if the placeholder is gone but the tab now has anchors/iframes
    if PLACEHOLDER not in tab and re.search(r"<a\s|<iframe|data-", tab):
        return True
    return False


def save_capture(mid: str, html: str) -> None:
    (FIX / f"live_match_{mid}.html").write_text(html, encoding="utf-8")
    (FIX / f"live_match_{mid}_tab.html").write_text(extract_active_tab(html), encoding="utf-8")
    tab = extract_active_tab(html)
    # surface any link-ish tokens for quick inspection
    tokens = set(re.findall(r"acestream://[0-9a-fA-F]{40}", tab))
    tokens |= set(re.findall(r"\b[0-9a-fA-F]{40}\b", tab))
    tokens |= set(re.findall(r"sop://[^\s\"'<]+", tab))
    log(f"  CAPTURED match {mid} -> fixtures/live_match_{mid}.html")
    log(f"  link tokens: {sorted(tokens)[:10] or 'none found in tab — inspect _tab.html'}")


def main() -> None:
    deadline = time.time() + TIMEOUT_MIN * 60
    captured: set[str] = set()
    log(f"poller start: interval={INTERVAL}s timeout={TIMEOUT_MIN}min target_samples={SAMPLES}")
    while time.time() < deadline and len(captured) < SAMPLES:
        matches = list_today_matches()
        log(f"checking {len(matches)} matches; captured so far={len(captured)}")
        for mid, url in matches:
            if mid in captured:
                continue
            html = fetch(url)
            if not html:
                continue
            if is_populated(html):
                save_capture(mid, html)
                captured.add(mid)
                if len(captured) >= SAMPLES:
                    break
        if len(captured) < SAMPLES:
            time.sleep(INTERVAL)
    if captured:
        log(f"DONE — captured {len(captured)} live sample(s): {sorted(captured)}. "
            f"Hypothesis CONFIRMED: links are server-rendered (no browser needed). "
            f"Document the field path in docs/recon-findings.md §4.")
    else:
        log("TIMEOUT — no match populated in raw HTML within the window. "
            "Links may be JS-injected after all → run scripts/recon_capture.py (Playwright).")


if __name__ == "__main__":
    main()
