"""API routes implementing docs/api/openapi.yaml."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException, Query

from .config import settings
from .models import (
    HealthResponse,
    Match,
    MatchListResponse,
    MatchSummary,
    Sport,
    Status,
)
from .store import store

router = APIRouter(prefix="/api")


@router.get("/matches", response_model=MatchListResponse)
def list_matches(
    sport: Sport | None = Query(default=None),
    window: str = Query(default="today", pattern="^(today|live)$"),
) -> MatchListResponse:
    matches = store.all()
    if sport is not None:
        matches = [m for m in matches if m.sport == sport]
    if window == "live":
        matches = [m for m in matches if m.status == Status.live or m.hasStream]
    summaries = [MatchSummary(**m.model_dump(exclude={"stadium", "streams"})) for m in matches]
    summaries.sort(key=lambda m: m.kickoff)
    return MatchListResponse(matches=summaries, lastUpdated=store.last_successful_crawl)


@router.get("/matches/{match_id}", response_model=Match)
def get_match(match_id: str) -> Match:
    match = store.get(match_id)
    if match is None:
        raise HTTPException(status_code=404, detail={"code": "not_found", "message": "Match not found"})
    return match


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    now = datetime.now(timezone.utc)
    window = timedelta(minutes=settings.stream_window_minutes)
    live_window = sum(
        1 for m in store.all() if abs(m.kickoff - now) <= window and m.status != Status.finished
    )
    last = store.last_successful_crawl
    if store.count() == 0:
        status = "unhealthy"
    elif last is not None and (now - last) > timedelta(seconds=settings.listing_refresh_seconds * 3):
        status = "degraded"
    else:
        status = "healthy"
    return HealthResponse(
        status=status,
        lastSuccessfulCrawl=last,
        matchCount=store.count(),
        liveWindowMatches=live_window,
    )
