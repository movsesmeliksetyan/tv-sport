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

# Listing groups matches by day: <div class="streams-day">6 июня</div> then that day's matches.
DAY_RE = re.compile(r'<div class="streams-day">\s*([^<]+?)\s*</div>')
RU_MONTHS = {
    "января": 1, "февраля": 2, "марта": 3, "апреля": 4, "мая": 5, "июня": 6,
    "июля": 7, "августа": 8, "сентября": 9, "октября": 10, "ноября": 11, "декабря": 12,
}

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


def parse_ru_date(text: str, now: datetime, tz: ZoneInfo) -> date | None:
    """'6 июня' -> date(2026, 6, 6). Year inferred from `now`, with rollover handling."""
    m = re.search(r"(\d{1,2})\s+([а-яё]+)", text.lower())
    if not m:
        return None
    day = int(m.group(1))
    month = RU_MONTHS.get(m.group(2))
    if not month:
        return None
    today = now.astimezone(tz).date()
    year = now.year
    # Listing shows upcoming days; if the parsed month is well behind now, it's next year.
    if month < today.month - 1:
        year += 1
    try:
        return date(year, month, day)
    except ValueError:
        return None


def _day_segments(html: str, now: datetime, tz: ZoneInfo) -> list[tuple[date, str]]:
    """Split listing HTML into (day, segment_html) by `streams-day` headers.
    Falls back to a single 'today' segment when no day headers are present."""
    parts = DAY_RE.split(html)
    if len(parts) < 3:  # no day markers
        return [(now.astimezone(tz).date(), html)]
    segments: list[tuple[date, str]] = []
    pairs = iter(parts[1:])  # drop preamble before the first header
    for date_text, content in zip(pairs, pairs):
        on_day = parse_ru_date(date_text, now, tz) or now.astimezone(tz).date()
        segments.append((on_day, content))
    return segments


def _parse_anchor(item: Node, on_day: date, now: datetime, tz: ZoneInfo) -> Match | None:
    href = item.attributes.get("href") or ""
    hm = HREF_RE.search(href)
    if not hm:
        return None
    sport, mid = hm.group(1), hm.group(2)

    # Live matches show the game clock ("13'") with a `liveTime` class instead of HH:MM.
    date_node = item.css_first(".match-item__title-date")
    date_class = (date_node.attributes.get("class") or "") if date_node else ""
    date_text = _text(date_node) or ""

    if "liveTime" in date_class:
        elapsed = re.search(r"(\d{1,3})\s*'", date_text)
        mins = int(elapsed.group(1)) if elapsed else 0
        kickoff = now - timedelta(minutes=mins)  # listing has no kickoff for live games
        status = Status.live
    else:
        kickoff = build_kickoff(date_text, on_day, tz)
        if kickoff is None:
            log.warning("skip match %s: unparseable kickoff %r", mid, date_text)
            return None
        status = derive_status(kickoff, now, sport)

    home = _text(item.css_first(".table-item.home .table-item__home-name"))
    away = _text(item.css_first(".table-item.away .table-item__away-name"))
    if not home or not away:
        log.warning("skip match %s: missing team name(s)", mid)
        return None

    return Match(
        id=mid,
        sport=sport,
        tournament=_text(item.css_first(".match-item__title-tournament")),
        home=Team(name=home, logo=_logo(item, "home")),
        away=Team(name=away, logo=_logo(item, "away")),
        kickoff=kickoff,
        channel=_text(item.css_first(".match-item__logo-channel")),
        status=status,
        hasStream=False,
        lastUpdated=now,
    )


def parse_listing(html: str, now: datetime, tz: ZoneInfo | None = None) -> list[Match]:
    """Parse one listing page into Matches, assigning each its correct day from the
    `streams-day` headers (the listing spans several days). Metadata only; no streams."""
    tz = tz or ZoneInfo(settings.timezone)
    matches: list[Match] = []
    for on_day, segment in _day_segments(html, now, tz):
        for item in HTMLParser(segment).css("a.match-item"):
            m = _parse_anchor(item, on_day, now, tz)
            if m is not None:
                matches.append(m)
    return matches


async def fetch(url: str, client: httpx.AsyncClient) -> str | None:
    try:
        resp = await client.get(url, headers={"User-Agent": settings.user_agent})
        resp.raise_for_status()
        return resp.text
    except httpx.HTTPError as e:
        log.warning("fetch failed %s: %s", url, e)
        return None


async def crawl(client: httpx.AsyncClient, now: datetime) -> list[Match]:
    """Crawl football + hockey listings → de-duplicated Match list (all days present)."""
    tz = ZoneInfo(settings.timezone)
    by_id: dict[str, Match] = {}
    for sport in ("football", "hockey"):
        html = await fetch(f"{settings.base_url}/category/{sport}/", client)
        if not html:
            continue
        for m in parse_listing(html, now, tz):
            by_id[m.id] = m
    if not by_id:
        log.error("crawl parsed 0 matches — site structure may have changed (R2)")
    return list(by_id.values())
