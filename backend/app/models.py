"""Pydantic models — the API contract (docs/api/openapi.yaml). Source of truth for T1.1."""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class Sport(str, Enum):
    football = "football"
    hockey = "hockey"


class Status(str, Enum):
    scheduled = "scheduled"
    live = "live"
    finished = "finished"


class Team(BaseModel):
    name: str
    logo: Optional[str] = None


class Stream(BaseModel):
    type: str = "acestream"  # v1 = acestream only; SopCast out of scope
    contentId: str = Field(pattern=r"^[0-9a-fA-F]{40}$")
    quality: Optional[str] = None
    language: Optional[str] = None


class MatchSummary(BaseModel):
    id: str
    sport: Sport
    tournament: Optional[str] = None
    home: Team
    away: Team
    kickoff: datetime
    channel: Optional[str] = None
    status: Status = Status.scheduled
    hasStream: bool = False
    lastUpdated: Optional[datetime] = None


class Match(MatchSummary):
    stadium: Optional[str] = None
    streams: list[Stream] = Field(default_factory=list)


class MatchListResponse(BaseModel):
    matches: list[MatchSummary]
    lastUpdated: Optional[datetime] = None


class HealthResponse(BaseModel):
    status: str
    lastSuccessfulCrawl: Optional[datetime] = None
    matchCount: int = 0
    liveWindowMatches: int = 0
