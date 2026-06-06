"""T1.2 — listing crawler parsing tests (against real captured fixtures)."""
from __future__ import annotations

import pathlib
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import httpx
import pytest

from app.models import Status
from app.scraper.crawler import build_kickoff, crawl, derive_status, parse_listing

FIX = pathlib.Path(__file__).parent / "fixtures"
MSK = ZoneInfo("Europe/Moscow")
DAY = date(2026, 6, 5)
NOON = datetime(2026, 6, 5, 12, 0, tzinfo=MSK)


def _read(name: str) -> str:
    return (FIX / name).read_text(encoding="utf-8")


def test_parses_six_football_matches():
    ms = parse_listing(_read("listing_football.html"), NOON, MSK)
    assert len(ms) == 6
    assert {m.id for m in ms} == {"69163", "69166", "69169", "69172", "69175", "69177"}


def test_match_fields_populated():
    ms = {m.id: m for m in parse_listing(_read("listing_football.html"), NOON, MSK)}
    rus = ms["69175"]
    assert rus.home.name and rus.away.name
    assert rus.kickoff.hour == 20 and rus.kickoff.minute == 0
    assert rus.kickoff.tzinfo is not None
    assert rus.channel == "МАТЧ! HD"
    assert rus.tournament == "Товарищеский матч"
    assert rus.home.logo.startswith("https://www.pimpletv.ru/")
    assert rus.home.logo.endswith("russia.png")
    assert rus.sport == "football"


def test_all_logos_absolute():
    ms = parse_listing(_read("listing_football.html"), NOON, MSK)
    for m in ms:
        for team in (m.home, m.away):
            if team.logo:
                assert team.logo.startswith("http")


def test_empty_listing_yields_nothing():
    # hockey fixture has no matches today
    assert parse_listing(_read("listing_hockey.html"), NOON, MSK) == []


def test_parse_ru_date():
    from app.scraper.crawler import parse_ru_date
    assert parse_ru_date("6 июня", NOON, MSK) == date(2026, 6, 6)
    assert parse_ru_date("8 июня", NOON, MSK) == date(2026, 6, 8)
    assert parse_ru_date("not a date", NOON, MSK) is None


def test_multi_day_listing_assigns_correct_dates():
    # Synthetic listing spanning two days with streams-day headers.
    html = """
    <div class="streams-day">6 июня</div>
    <div class="sport-tournament__block">
      <a href="/football/100-a-b/" class="match-item _rates">
        <div class="match-item__title"><div class="match-item__title-date"><div>16:00</div></div>
        <div class="match-item__title-name">
          <span class="table-item home"><span class="table-item__home-name">A</span></span>
          <span class="table-item away"><span class="table-item__away-name">B</span></span></div></div></a>
    </div>
    <div class="streams-day">8 июня</div>
    <div class="sport-tournament__block">
      <a href="/football/200-c-d/" class="match-item _rates">
        <div class="match-item__title"><div class="match-item__title-date"><div>21:00</div></div>
        <div class="match-item__title-name">
          <span class="table-item home"><span class="table-item__home-name">C</span></span>
          <span class="table-item away"><span class="table-item__away-name">D</span></span></div></div></a>
    </div>
    """
    ms = {m.id: m for m in parse_listing(html, NOON, MSK)}
    assert ms["100"].kickoff.date() == date(2026, 6, 6)
    assert ms["200"].kickoff.date() == date(2026, 6, 8)  # NOT stamped as today


def test_build_kickoff():
    assert build_kickoff("20:00", DAY, MSK).hour == 20
    assert build_kickoff("no time here", DAY, MSK) is None
    assert build_kickoff("25:00", DAY, MSK) is None


def test_derive_status():
    kickoff = datetime(2026, 6, 5, 20, 0, tzinfo=MSK)
    assert derive_status(kickoff, kickoff - timedelta(minutes=10), "football") == Status.scheduled
    assert derive_status(kickoff, kickoff + timedelta(minutes=30), "football") == Status.live
    assert derive_status(kickoff, kickoff + timedelta(hours=5), "football") == Status.finished


@pytest.mark.asyncio
async def test_crawl_combines_both_sports():
    def handler(request: httpx.Request) -> httpx.Response:
        name = "listing_football.html" if "football" in request.url.path else "listing_hockey.html"
        return httpx.Response(200, text=_read(name))

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        ms = await crawl(client, NOON)
    assert len(ms) == 6  # 6 football + 0 hockey
    assert all(m.status == Status.scheduled for m in ms)  # NOON is before all kickoffs
