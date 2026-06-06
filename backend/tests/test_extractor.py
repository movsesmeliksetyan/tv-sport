"""T2.1 — fixture-based tests for the Ace Stream extractor.

The synthetic fixture is provisional until the real live-window payload (T0.1)
lands; the placeholder/negative cases use the REAL captured match page.
"""
from __future__ import annotations

import pathlib

import pytest

from app.scraper.extractor import AceStreamHtmlExtractor, is_placeholder, active_tab_html

FIX = pathlib.Path(__file__).parent / "fixtures"


def _read(name: str) -> str:
    return (FIX / name).read_text(encoding="utf-8")


@pytest.fixture
def extractor() -> AceStreamHtmlExtractor:
    return AceStreamHtmlExtractor()


# ---- positive: synthetic populated tab ----

def test_extracts_all_acestream_ids(extractor):
    streams = extractor.extract(_read("live_match_synthetic.html"))
    ids = {s.contentId for s in streams}
    assert ids == {
        "a1b2c3d4e5f60718293a4b5c6d7e8f9012345678",
        "00112233445566778899aabbccddeeff00112233",
        "ffeeddccbbaa99887766554433221100ffeeddcc",
    }


def test_all_streams_are_acestream_and_valid(extractor):
    streams = extractor.extract(_read("live_match_synthetic.html"))
    assert streams, "expected >=1 stream"
    for s in streams:
        assert s.type == "acestream"
        assert len(s.contentId) == 40
        int(s.contentId, 16)  # valid hex


def test_per_link_quality(extractor):
    streams = {s.contentId: s for s in extractor.extract(_read("live_match_synthetic.html"))}
    assert streams["a1b2c3d4e5f60718293a4b5c6d7e8f9012345678"].quality.upper() == "HD"
    assert streams["00112233445566778899aabbccddeeff00112233"].quality.upper() == "SD"
    assert streams["ffeeddccbbaa99887766554433221100ffeeddcc"].quality == "720p"


def test_sopcast_is_dropped(extractor):
    # The fixture has 3 acestream links + 1 sop:// link; only the 3 acestream survive.
    streams = extractor.extract(_read("live_match_synthetic.html"))
    assert len(streams) == 3
    assert all(s.type == "acestream" for s in streams)


# ---- positive: REAL live-window captures (T0.1 confirmed) ----

@pytest.mark.parametrize("fid,expected_id", [
    ("69163", "016d48fb89bb9505ab3f883db1bfb3a7c0a3eccc"),
    ("69166", "aca05dc506242324c1727525d0535ceda24f8dea"),
])
def test_real_live_capture(extractor, fid, expected_id):
    streams = extractor.extract(_read(f"live_match_{fid}.html"))
    assert len(streams) == 1
    s = streams[0]
    assert s.type == "acestream"
    assert s.contentId == expected_id
    assert s.quality == "1080p"  # parsed from the broadcast-table Format column


# ---- negative: real pre-window placeholder page ----

def test_real_placeholder_yields_no_streams(extractor):
    html = _read("match_69175.html")
    assert is_placeholder(active_tab_html(html))
    assert extractor.extract(html) == []


# ---- robustness ----

def test_dedup_repeated_ids(extractor):
    cid = "a" * 40
    html = f'<div class="tabs-content active"><a href="acestream://{cid}">x</a>' \
           f'<a href="acestream://{cid.upper()}">y</a></div>'
    streams = extractor.extract(html)
    assert len(streams) == 1
    assert streams[0].contentId == cid


def test_invalid_length_hash_rejected(extractor):
    # 39 hex chars — not a valid content id
    html = '<div class="tabs-content active">acestream stuff aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa</div>'
    assert extractor.extract(html) == []


def test_bare_hex_ignored_without_acestream_context(extractor):
    # a 40-hex string with no acestream mention must NOT be treated as a stream
    sha = "da39a3ee5e6b4b0d3255bfef95601890afd80709"
    html = f'<div class="tabs-content active"><span data-sig="{sha}">commit</span></div>'
    assert extractor.extract(html) == []
