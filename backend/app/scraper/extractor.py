"""Stream extractor (T2.1).

Turns a match page's HTML into a list of `Stream` (Ace Stream content IDs).
Isolated behind the `Extractor` protocol so the fragile parsing can be swapped
without touching the crawler/API (integration-plan §4, R2 mitigation).

Strategy (cheap-path-first, per recon §4): the links are expected to be
server-rendered into `div.tabs-content.active`. We scan that block for Ace
Stream identifiers in several shapes, strongest signal first:

  1. `acestream://<40-hex>` URIs
  2. content IDs in engine/get_stream URLs or data-* attrs / query params
     (e.g. `?content_id=`, `?infohash=`, `data-acestream=`)
  3. bare 40-hex hashes, but ONLY inside a block that mentions "acestream"
     (avoids matching unrelated sha1-looking strings)

SopCast (`sop://`) is intentionally dropped — Ace Stream only for v1 (PRD §5.3).

NOTE: until the real live-window payload (T0.1) is captured, the exact markup is
inferred. If reality differs, adjust ONLY the selectors/patterns here — the
protocol and the dedup/validation logic stay put.
"""
from __future__ import annotations

import re
from typing import Protocol

from selectolax.parser import HTMLParser

from ..models import Stream

HEX40 = re.compile(r"[0-9a-fA-F]{40}")
ACESTREAM_URI = re.compile(r"acestream://([0-9a-fA-F]{40})", re.IGNORECASE)
# content id carried as a query/data param or engine URL
PARAM_ID = re.compile(
    r"(?:content_id|infohash|content-id|data-acestream|[?&]id)=[\"']?([0-9a-fA-F]{40})",
    re.IGNORECASE,
)
PLACEHOLDER_MARKER = "появятся"  # pre-window placeholder text
QUALITY_RE = re.compile(r"\b(4K|UHD|FHD|HD|SD|1080p?|720p?|480p?)\b", re.IGNORECASE)
LANG_RE = re.compile(r"\b(ru|en|es|fr|de|it|рус|англ)\b", re.IGNORECASE)


class Extractor(Protocol):
    """Input: match-page HTML. Output: de-duplicated Ace Stream list (may be empty)."""

    def extract(self, html: str) -> list[Stream]: ...


def active_tab_html(html: str) -> str:
    """Return the broadcast tab block (`div.tabs-content.active`), or '' if absent."""
    tree = HTMLParser(html)
    node = tree.css_first("div.tabs-content.active")
    return node.html or "" if node else ""


def is_placeholder(block: str) -> bool:
    """True when the block only shows the 'links appear ~1h before' placeholder."""
    return PLACEHOLDER_MARKER in block and not ACESTREAM_URI.search(block)


class AceStreamHtmlExtractor:
    """Server-rendered-HTML extractor (no browser). Implements `Extractor`."""

    def extract(self, html: str) -> list[Stream]:
        block = active_tab_html(html)
        block_is_tab = bool(block)
        if not block:
            # Tab structure missing (e.g. removed by adblock JS) — fall back to whole doc.
            block = html
        if is_placeholder(block):
            return []

        seen: set[str] = set()
        streams: list[Stream] = []

        # Strategy A: per-anchor — captures each link's own quality/language (FR-6 chooser).
        node = HTMLParser(html).css_first("div.tabs-content.active") if block_is_tab else HTMLParser(html).body
        if node is not None:
            for a in node.css("a"):
                href = a.attributes.get("href") or ""
                cid = _id_from(href) or _id_from(_attrs_blob(a))
                if not cid:
                    continue
                label = (a.text() or "") + " " + href
                self._add(streams, seen, cid, _first(QUALITY_RE, label), _first(LANG_RE, label))

        # Strategy B: block-level regex sweep for any ids not in anchors.
        block_q = _first(QUALITY_RE, block)
        block_l = _first(LANG_RE, block)
        leftover = ACESTREAM_URI.findall(block) + PARAM_ID.findall(block)
        if "acestream" in block.lower() or "ace stream" in block.lower():
            leftover += HEX40.findall(block)
        for cid in leftover:
            self._add(streams, seen, cid, block_q, block_l)

        return streams

    @staticmethod
    def _add(streams: list[Stream], seen: set[str], cid: str, quality: str | None, lang: str | None) -> None:
        cid = cid.lower()
        if cid in seen:
            return
        seen.add(cid)
        try:
            streams.append(
                Stream(type="acestream", contentId=cid, quality=quality, language=_normalize_lang(lang))
            )
        except Exception:  # noqa: BLE001 — invalid id (not 40-hex) is dropped
            return


def _id_from(text: str) -> str | None:
    for pat in (ACESTREAM_URI, PARAM_ID):
        m = pat.search(text)
        if m:
            return m.group(1)
    return None


def _attrs_blob(node) -> str:
    return " ".join(f'{k}="{v}"' for k, v in (node.attributes or {}).items())


def _first(pattern: re.Pattern[str], text: str) -> str | None:
    m = pattern.search(text)
    return m.group(1) if m else None


def _normalize_lang(raw: str | None) -> str | None:
    if raw is None:
        return None
    low = raw.lower()
    if low in ("рус",):
        return "ru"
    if low in ("англ",):
        return "en"
    return low


# Default extractor used by the resolution job (T2.3).
default_extractor: Extractor = AceStreamHtmlExtractor()
