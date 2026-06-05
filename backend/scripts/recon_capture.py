"""T0.1 recon helper — capture the JS-injected stream payload during a live window.

NOT part of the Pi runtime. Run on a dev machine within ~1h of kickoff:

    pip install -r requirements-recon.txt
    playwright install chromium
    python scripts/recon_capture.py 69175

It opens the match page, records every XHR/fetch request+response, and the final
rendered "Трансляция" tab HTML, into tests/fixtures/live_match_<id>.*  so the
extractor (T2.1) can be built against a real payload offline.
"""
from __future__ import annotations

import json
import pathlib
import sys

from playwright.sync_api import sync_playwright

BASE = "https://www.pimpletv.ru"
FIX = pathlib.Path(__file__).resolve().parent.parent / "tests" / "fixtures"


def capture(match_id: str, sport: str = "football") -> None:
    FIX.mkdir(parents=True, exist_ok=True)
    url = f"{BASE}/{sport}/{match_id}-x/"  # slug tail is ignored by WP; id is what matters
    calls: list[dict] = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(user_agent="Mozilla/5.0 (X11; Linux aarch64)")

        def on_response(resp):
            ct = resp.headers.get("content-type", "")
            if "json" in ct or "ajax" in resp.url or "stream" in resp.url.lower():
                try:
                    body = resp.text()
                except Exception:
                    body = "<binary>"
                calls.append({
                    "url": resp.url,
                    "status": resp.status,
                    "request_method": resp.request.method,
                    "content_type": ct,
                    "body": body[:20000],
                })

        page.on("response", on_response)
        page.goto(url, wait_until="networkidle", timeout=60000)
        page.wait_for_timeout(5000)  # let late XHRs land

        tab = page.query_selector(".tabs-content.active")
        tab_html = tab.inner_html() if tab else "<no .tabs-content.active>"
        browser.close()

    (FIX / f"live_match_{match_id}.json").write_text(
        json.dumps(calls, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (FIX / f"live_match_{match_id}_tab.html").write_text(tab_html, encoding="utf-8")
    print(f"Captured {len(calls)} candidate XHR/JSON calls -> tests/fixtures/live_match_{match_id}.json")
    print(f"Rendered stream tab -> tests/fixtures/live_match_{match_id}_tab.html")
    print("Inspect the JSON for the 40-char hex content id / acestream:// URI, then document the field path in docs/recon-findings.md §4.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("usage: python scripts/recon_capture.py <match_id> [sport]")
    capture(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "football")
