"""Listing crawler (T1.1 normalizer + T1.2 crawler).

Fetches the listing pages and parses each `a.match-item` into a `Match`.
Pure HTTP (httpx) + selectolax — no browser (metadata is static HTML, recon §2).
Selectors are documented in docs/recon-findings.md §2.
"""
from __future__ import annotations

import logging
import re
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import httpx
from selectolax.parser import HTMLParser, Node

from ..config import settings
from ..models import Match, Status, Team

log = logging.getLogger("pimpletv.crawler")

HREF_RE = re.compile(r"/([a-z]+)/(\d+)-")
TIME_RE = re.compile(r"\b(\d{1,2}):(\d{2})\b")

# Assumed play+buffer durations to derive status from kickoff (no reliable live flag on listings).
DURATION_MIN = {"football": 140, "hockey": 165}


def _text(node: Node | None) -> str | None:
    if node is None:
        return None
    t = node.text(strip=True)
    return t or None


def _abs_url(src: str | None) -> str | None:
    if not src:
        return None
    if src.startswith("http"):
        return src
    return settings.base_url.rstrip("/") + "/" + src.lstrip("/")


def _logo(item: Node, side: str) -> str | None:
    img = item.css_first(f".table-item.{side} .table-item__logo img")
    return _abs_url(img.attributes.get("src")) if img else None


def build_kickoff(time_str: str, on_day: date, tz: ZoneInfo) -> datetime | None:
    m = TIME_RE.search(time_str or "")
    if not m:
        return None
    hh, mm = int(m.group(1)), int(m.group(2))
    if hh > 23 or mm > 59:
        return None
    return datetime(on_day.year, on_day.month, on_day.day, hh, mm, tzinfo=tz)


def derive_status(kickoff: datetime, now: datetime, sport: str) -> Status:
    if now < kickoff:
        return Status.scheduled
    end = kickoff + timedelta(minutes=DURATION_MIN.get(sport, 150))
    return Status.live if now < end else Status.finished


def parse_listing(html: str, on_day: date, now: datetime, tz: ZoneInfo | None = None) -> list[Match]:
    """Parse one listing page's HTML into Matches (metadata only; no streams)."""
    tz = tz or ZoneInfo(settings.timezone)
    tree = HTMLParser(html)
    matches: list[Match] = []
    for item in tree.css("a.match-item"):
        href = item.attributes.get("href") or ""
        hm = HREF_RE.search(href)
        if not hm:
            continue
        sport, mid = hm.group(1), hm.group(2)

        kickoff = build_kickoff(_text(item.css_first(".match-item__title-date")) or "", on_day, tz)
        if kickoff is None:
            log.warning("skip match %s: unparseable kickoff", mid)
            continue

        home = _text(item.css_first(".table-item.home .table-item__home-name"))
        away = _text(item.css_first(".table-item.away .table-item__away-name"))
        if not home or not away:
            log.warning("skip match %s: missing team name(s)", mid)
            continue

        matches.append(
            Match(
                id=mid,
                sport=sport,
                tournament=_text(item.css_first(".match-item__title-tournament")),
                home=Team(name=home, logo=_logo(item, "home")),
                away=Team(name=away, logo=_logo(item, "away")),
                kickoff=kickoff,
                channel=_text(item.css_first(".match-item__logo-channel")),
                status=derive_status(kickoff, now, sport),
                hasStream=False,
                lastUpdated=now,
            )
        )
    return matches


async def fetch(url: str, client: httpx.AsyncClient) -> str | None:
    try:
        resp = await client.get(url, headers={"User-Agent": settings.user_agent})
        resp.raise_for_status()
        return resp.text
    except httpx.HTTPError as e:
        log.warning("fetch failed %s: %s", url, e)
        return None


async def crawl(client: httpx.AsyncClient, on_day: date, now: datetime) -> list[Match]:
    """Crawl football + hockey listings → de-duplicated Match list."""
    tz = ZoneInfo(settings.timezone)
    by_id: dict[str, Match] = {}
    for sport in ("football", "hockey"):
        html = await fetch(f"{settings.base_url}/category/{sport}/", client)
        if not html:
            continue
        for m in parse_listing(html, on_day, now, tz):
            by_id[m.id] = m
    if not by_id:
        log.error("crawl parsed 0 matches — site structure may have changed (R2)")
    return list(by_id.values())
