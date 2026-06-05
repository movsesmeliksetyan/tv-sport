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
    ms = parse_listing(_read("listing_football.html"), DAY, NOON, MSK)
    assert len(ms) == 6
    assert {m.id for m in ms} == {"69163", "69166", "69169", "69172", "69175", "69177"}


def test_match_fields_populated():
    ms = {m.id: m for m in parse_listing(_read("listing_football.html"), DAY, NOON, MSK)}
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
    ms = parse_listing(_read("listing_football.html"), DAY, NOON, MSK)
    for m in ms:
        for team in (m.home, m.away):
            if team.logo:
                assert team.logo.startswith("http")


def test_empty_listing_yields_nothing():
    # hockey fixture has no matches today
    assert parse_listing(_read("listing_hockey.html"), DAY, NOON, MSK) == []


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
        ms = await crawl(client, DAY, NOON)
    assert len(ms) == 6  # 6 football + 0 hockey
    assert all(m.status == Status.scheduled for m in ms)  # NOON is before all kickoffs
