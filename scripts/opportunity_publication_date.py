#!/usr/bin/env python3
"""Data ufficiale di pubblicazione di un avviso, letta dalla pagina della fonte.

Ordine: metadati della pagina (JSON-LD `datePublished`, `article:published_time`, Dublin Core), poi
le diciture esplicite nel testo («Data di pubblicazione», «Pubblicato il»). Una data futura o più
vecchia di due anni non vale. Nessuna data è meglio di una data sbagliata: in dubbio restituisce None.
"""
from __future__ import annotations

import html as htmllib
import json
import re
from datetime import date
from typing import Any

MONTHS = {"gennaio": 1, "febbraio": 2, "marzo": 3, "aprile": 4, "maggio": 5, "giugno": 6, "luglio": 7, "agosto": 8,
          "settembre": 9, "ottobre": 10, "novembre": 11, "dicembre": 12}
ISO = r"(20\d{2})-(\d{2})-(\d{2})"
NUMERIC = r"(\d{1,2})[./-](\d{1,2})[./-](20\d{2})"
WORDS = r"(\d{1,2})(?:°|º)?\s+(" + "|".join(MONTHS) + r")\s+(20\d{2})"

META = [
    ("meta article:published_time", re.compile(
        r"<meta[^>]+(?:property|name)\s*=\s*[\"'](?:article:published_time|og:published_time|datePublished)[\"'][^>]*>", re.I)),
    ("meta Dublin Core", re.compile(
        r"<meta[^>]+name\s*=\s*[\"'](?:DC\.date\.issued|dcterms\.issued|DC\.date\.created|dcterms\.created)[\"'][^>]*>", re.I)),
]
CONTENT = re.compile(r"content\s*=\s*[\"']([^\"']+)[\"']", re.I)
JSONLD = re.compile(r"<script[^>]+application/ld\+json[^>]*>(.*?)</script>", re.I | re.S)
LABEL = re.compile(
    r"\b(?:data\s+(?:di\s+)?pubblicazione|pubblicat[oa]\s+(?:il|in\s+data)|data\s+di\s+inserimento|"
    r"pubblicazione\s*:|published\s*(?:on|:))\s*:?\s*(?:il\s+)?(?:\w+,?\s+)?"
    r"(" + NUMERIC + r"|" + WORDS + r"|" + ISO + r")", re.I)


def _parse(text: str) -> date | None:
    text = str(text or "").strip().lower()
    for pattern, order in ((ISO, "ymd"), (NUMERIC, "dmy"), (WORDS, "dwy")):
        m = re.search(pattern, text)
        if not m:
            continue
        try:
            if order == "ymd":
                return date(int(m[1]), int(m[2]), int(m[3]))
            if order == "dmy":
                return date(int(m[3]), int(m[2]), int(m[1]))
            return date(int(m[3]), MONTHS[m[2]], int(m[1]))
        except (ValueError, KeyError):
            return None
    return None


def _jsonld_dates(raw: str) -> list[str]:
    found: list[str] = []

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            if isinstance(node.get("datePublished"), str):
                found.append(node["datePublished"])
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)

    for block in JSONLD.findall(raw or ""):
        try:
            walk(json.loads(htmllib.unescape(block)))
        except (ValueError, TypeError):
            continue
    return found


def _plausible(value: date | None, today: date) -> bool:
    return value is not None and value <= today and (today - value).days <= 730


def publication_date(raw_html: str, visible_text: str, today: date) -> tuple[str | None, str]:
    """(data ISO, evidenza) dalla pagina; (None, "") se la pagina non la dichiara senza ambiguità."""
    raw = raw_html or ""
    for value in _jsonld_dates(raw):
        parsed = _parse(value)
        if _plausible(parsed, today):
            return parsed.isoformat(), "metadati della pagina (datePublished)"
    for label, pattern in META:
        for tag in pattern.findall(raw):
            m = CONTENT.search(tag)
            parsed = _parse(m[1]) if m else None
            if _plausible(parsed, today):
                return parsed.isoformat(), f"metadati della pagina ({label.split(' ', 1)[1]})"
    text = re.sub(r"\s+", " ", visible_text or "")
    dates = []
    for m in LABEL.finditer(text):
        parsed = _parse(m[1])
        if _plausible(parsed, today):
            dates.append((parsed, m.group(0).strip()))
    # Più diciture con date diverse (avviso, allegati, aggiornamenti): ambiguo, nessuna data.
    if dates and len({d for d, _ in dates}) == 1:
        parsed, quote = dates[0]
        return parsed.isoformat(), f"testo della pagina: «{quote[:80]}»"
    return None, ""


OVERLAY = "data/opportunity-publication-dates.json"


def apply_overlay(result: dict[str, Any], root: Any) -> int:
    """Date verificate a mano per le schede curate (`data/opportunity-publication-dates.json`): solo dove manca la data."""
    from pathlib import Path
    path = Path(root) / OVERLAY
    if not path.exists():
        return 0
    entries = {str(e["coverage_id"]): e for e in json.loads(path.read_text(encoding="utf-8")).get("entries") or []}
    applied = 0
    for item in result.get("opportunities") or []:
        entry = entries.get(str(item.get("coverage_id") or item.get("id") or ""))
        if entry and not item.get("published_at"):
            item["published_at"] = entry["published_at"]
            item["published_at_evidence"] = f"{entry['evidence']} ({entry['evidence_url']})"
            applied += 1
    return applied
