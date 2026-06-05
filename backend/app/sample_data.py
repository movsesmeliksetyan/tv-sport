"""Canned sample matches used when PTV_MOCK_MODE=true. Lets the Android TV app
integrate against the real contract before the crawler (Phase 1) is built."""
from __future__ import annotations

from datetime import datetime

from .models import Match, Stream, Team

BASE = "https://www.pimpletv.ru/wp-content/uploads/logo/football/int"


def sample_matches() -> list[Match]:
    return [
        Match(
            id="69175",
            sport="football",
            tournament="Friendly. National teams",
            home=Team(name="Russia", logo=f"{BASE}/russia.png"),
            away=Team(name="Burkina Faso", logo=f"{BASE}/burkina_faso.png"),
            kickoff=datetime.fromisoformat("2026-06-05T20:00:00+03:00"),
            channel="MATCH! HD",
            stadium="Volgograd Arena",
            status="live",
            hasStream=True,
            streams=[Stream(contentId="a1b2c3d4e5f60718293a4b5c6d7e8f9012345678", quality="HD", language="ru")],
        ),
        Match(
            id="69172",
            sport="football",
            tournament="Friendly. National teams",
            home=Team(name="Moldova", logo=f"{BASE}/moldova.png"),
            away=Team(name="Bulgaria", logo=f"{BASE}/bulgaria.png"),
            kickoff=datetime.fromisoformat("2026-06-05T20:00:00+03:00"),
            channel="Okko Sport",
            status="scheduled",
            hasStream=False,
        ),
        Match(
            id="69169",
            sport="football",
            tournament="Friendly. National teams",
            home=Team(name="Slovakia", logo=f"{BASE}/slovakia.png"),
            away=Team(name="Montenegro", logo=f"{BASE}/montenegro.png"),
            kickoff=datetime.fromisoformat("2026-06-05T19:30:00+03:00"),
            channel="Okko Sport",
            status="scheduled",
            hasStream=False,
        ),
    ]
