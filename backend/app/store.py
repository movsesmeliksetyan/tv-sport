"""In-memory match store. Phase 1 (T1.3) swaps the seed for live crawl output;
optionally back with Redis later. Single-process safe for the Pi's load."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from .models import Match


class MatchStore:
    def __init__(self) -> None:
        self._matches: dict[str, Match] = {}
        self.last_successful_crawl: Optional[datetime] = None

    def replace_all(self, matches: list[Match]) -> None:
        self._matches = {m.id: m for m in matches}
        self.last_successful_crawl = datetime.now(timezone.utc)

    def upsert(self, match: Match) -> None:
        self._matches[match.id] = match

    def get(self, match_id: str) -> Optional[Match]:
        return self._matches.get(match_id)

    def all(self) -> list[Match]:
        return list(self._matches.values())

    def count(self) -> int:
        return len(self._matches)


store = MatchStore()
