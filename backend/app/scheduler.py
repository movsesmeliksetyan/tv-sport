"""Scheduler (T1.3 + T2.3 wiring).

Two cadences sharing one httpx client:
  - listing refresh  (every PTV_LISTING_REFRESH_SECONDS): crawl → store.merge_listing
  - stream resolution (every PTV_STREAM_REFRESH_SECONDS):  resolve in-window matches

Resolution flips hasStream/streams on the stored Match and clears streams once a
match is finished.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import httpx
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from .config import settings
from .models import Status
from .scraper.crawler import crawl
from .scraper.resolver import resolve_streams, should_resolve
from .store import store

log = logging.getLogger("pimpletv.scheduler")


def _now_tz() -> datetime:
    return datetime.now(ZoneInfo(settings.timezone))


class CrawlScheduler:
    def __init__(self) -> None:
        self._sched = AsyncIOScheduler(timezone=settings.timezone)
        self._client: httpx.AsyncClient | None = None

    async def start(self) -> None:
        self._client = httpx.AsyncClient(timeout=settings.request_timeout_s, follow_redirects=True)
        await self.refresh_listing()  # populate immediately so the API isn't empty on boot
        self._sched.add_job(
            self.refresh_listing, "interval",
            seconds=settings.listing_refresh_seconds, id="listing", max_instances=1,
        )
        self._sched.add_job(
            self.resolve_due, "interval",
            seconds=settings.stream_refresh_seconds, id="resolve", max_instances=1,
        )
        self._sched.start()
        log.info(
            "scheduler started (listing=%ss, resolve=%ss)",
            settings.listing_refresh_seconds, settings.stream_refresh_seconds,
        )

    async def stop(self) -> None:
        if self._sched.running:
            self._sched.shutdown(wait=False)
        if self._client:
            await self._client.aclose()

    async def refresh_listing(self) -> None:
        now = _now_tz()
        matches = await crawl(self._client, now.date(), now)
        if matches:
            store.merge_listing(matches)
            log.info("listing refreshed: %d matches", len(matches))

    async def resolve_due(self) -> None:
        now = _now_tz()
        for match in store.all():
            if match.status == Status.finished and match.streams:
                match.streams = []
                match.hasStream = False
                continue
            if not should_resolve(match, now):
                continue
            url = f"{settings.base_url}/{match.sport}/{match.id}-x/"
            streams = await resolve_streams(url, self._client)
            if streams:
                match.streams = streams
                match.hasStream = True
                match.lastUpdated = datetime.now(timezone.utc)
                log.info("resolved %d stream(s) for match %s", len(streams), match.id)


scheduler = CrawlScheduler()
