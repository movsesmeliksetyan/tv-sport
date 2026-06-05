"""Stream resolution (T2.3 core).

Decides WHICH matches to resolve (window gating) and resolves one match's
streams via the cheap path: httpx GET of the match page → extractor. No browser
(per the server-render hypothesis, recon §4). The scheduler that calls this on a
cadence is wired in Phase 1 (T1.3) once the crawler populates the store.
"""
from __future__ import annotations

from datetime import datetime, timedelta

import httpx

from ..config import settings
from ..models import Match, Status, Stream
from .extractor import Extractor, default_extractor


def in_resolution_window(kickoff: datetime, now: datetime, window_minutes: int) -> bool:
    """True from `window_minutes` before kickoff onward (links appear ~1h before)."""
    return now >= kickoff - timedelta(minutes=window_minutes)


def should_resolve(match: Match, now: datetime, window_minutes: int = None) -> bool:
    """Resolve only live-window matches that aren't already finished."""
    if match.status == Status.finished:
        return False
    wm = settings.stream_window_minutes if window_minutes is None else window_minutes
    return in_resolution_window(match.kickoff, now, wm)


async def resolve_streams(
    match_url: str,
    client: httpx.AsyncClient,
    extractor: Extractor = default_extractor,
) -> list[Stream]:
    """Fetch a match page and extract its Ace Stream list (empty on error/placeholder)."""
    try:
        resp = await client.get(match_url, headers={"User-Agent": settings.user_agent})
        resp.raise_for_status()
    except httpx.HTTPError:
        return []
    return extractor.extract(resp.text)
