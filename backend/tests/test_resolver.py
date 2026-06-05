"""T2.3 — window gating + cheap-path resolution tests."""
from __future__ import annotations

import pathlib
from datetime import datetime, timedelta, timezone

import httpx
import pytest

from app.models import Match, Team
from app.scraper.resolver import in_resolution_window, resolve_streams, should_resolve

FIX = pathlib.Path(__file__).parent / "fixtures"
MSK = timezone(timedelta(hours=3))


def _match(kickoff: datetime, status: str = "scheduled") -> Match:
    return Match(
        id="1", sport="football", tournament=None,
        home=Team(name="A"), away=Team(name="B"),
        kickoff=kickoff, channel=None, status=status, hasStream=False, lastUpdated=None,
    )


def test_window_opens_75_min_before():
    kickoff = datetime(2026, 6, 5, 20, 0, tzinfo=MSK)
    assert not in_resolution_window(kickoff, kickoff - timedelta(minutes=76), 75)
    assert in_resolution_window(kickoff, kickoff - timedelta(minutes=75), 75)
    assert in_resolution_window(kickoff, kickoff, 75)


def test_should_resolve_skips_finished():
    kickoff = datetime(2026, 6, 5, 20, 0, tzinfo=MSK)
    now = kickoff - timedelta(minutes=30)
    assert should_resolve(_match(kickoff), now, 75)
    assert not should_resolve(_match(kickoff, status="finished"), now, 75)


def test_should_resolve_skips_far_future():
    kickoff = datetime(2026, 6, 5, 20, 0, tzinfo=MSK)
    now = kickoff - timedelta(hours=3)
    assert not should_resolve(_match(kickoff), now, 75)


@pytest.mark.asyncio
async def test_resolve_streams_parses_page():
    html = (FIX / "live_match_synthetic.html").read_text(encoding="utf-8")

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=html)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        streams = await resolve_streams("http://x/match", client)
    assert len(streams) == 3


@pytest.mark.asyncio
async def test_resolve_streams_empty_on_http_error():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        streams = await resolve_streams("http://x/match", client)
    assert streams == []
