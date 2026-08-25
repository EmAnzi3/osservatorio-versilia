#!/usr/bin/env python3
"""Filtro di qualità live per il prototipo Radar Opportunità Versilia.

La pagina HTML ufficiale resta la prima fonte. Se i destinatari rimangono
ambigui, il filtro tenta l'estrazione mirata dagli allegati PDF ufficiali
(bando/avviso/decreto) prima di lasciare il caso in review.
"""
from __future__ import annotations

import re
import sys
from datetime import date
from pathlib import Path
from typing import Callable

sys.path.insert(0, str(Path(__file__).resolve().parent))
import opportunity_radar as base
import opportunity_pdf_evidence as pdf_evidence

ORIG_GRANTS = base.collect_grants

AUDIENCE_KEYS = (
    "destinatari / beneficiari",
    "destinatari/beneficiari",
    "destinatari",
    "beneficiari",
    "chi può partecipare",
    "chi puo partecipare",
    "soggetti beneficiari",
    "soggetti ammissibili",
    "chi può presentare domanda",
    "chi puo presentare domanda",
)
CLEAR_NON_MUNICIPAL = (
    r"\bpmi\b",
    r"\bstart[ -]?up\b",
    r"\bimprese\b",
    r"\bagenzie formative\b",
    r"\blavorator",
    r"\blavoratric",
    r"\bdatori di lavoro\b",
    r"\bpersone fisiche\b",
    r"\boperatori economici\b",
    r"\bprofessionist",
    r"\bstudent",
    r"\buniversit",
    r"\bscuole\b",
    r"\bagricoltor",
    r"\bpescator",
    r"\bapicoltor",
)


def audience_section(payload: str) -> str:
    heads = list(re.finditer(r"<h[1-6][^>]*>(.*?)</h[1-6]\s*>", payload, re.I | re.S))
    for idx, match in enumerate(heads):
        heading = base.norm(base.visible(match.group(1)))
        if not any(key in heading for key in AUDIENCE_KEYS) or "destinatari dei progetti" in heading:
            continue
        candidates = [x.start() for x in heads[idx + 1 :]]
        for marker in re.finditer(r"<(?:footer|nav|/main)\b", payload[match.end() :], re.I):
            candidates.append(match.end() + marker.start())
        stop = min(candidates) if candidates else len(payload)
        return base.visible(payload[match.end() : stop])
    return ""


def clearly_non_municipal(text: str) -> bool:
    normalized = base.norm(text)
    if any(re.search(pattern, normalized, re.I) for pattern in base.DIRECT):
        return False
    return any(re.search(pattern, normalized, re.I) for pattern in CLEAR_NON_MUNICIPAL)


def collect_html(
    source: dict,
    today: date,
    payload: str,
    loader: Callable[[str], str] | None = None,
    pdf_text_loader: Callable[[str], str] | None = None,
):
    loader = loader or base.fetch
    parser = base.Cards()
    parser.feed(payload)
    parser.close()
    out = []

    for title, href, body in parser.out:
        if len(title) < 8 or base.norm(title) in base.IGNORE or not href:
            continue
        listing = f"{title}. {body}"
        prelim, _, _ = base.eligibility(listing, source["_towns"])
        if prelim == "not_relevant" or (prelim == "review" and clearly_non_municipal(title)):
            continue

        url = base.urljoin(source["url"], href)
        detail = ""
        audience = ""
        document_url = None
        if source.get("detailEnrichment"):
            try:
                detail = loader(url)
                audience = audience_section(detail)
            except Exception:
                detail = audience = ""

        classify = f"{title}. {audience}" if audience else listing
        status, towns, reason = base.eligibility(classify, source["_towns"])

        # Solo i casi ancora ambigui attivano la lettura dei PDF allegati.
        if status == "review" and detail:
            pdf_audience, document_url = pdf_evidence.attached_pdf_audience(
                detail, url, text_loader=pdf_text_loader
            )
            if pdf_audience:
                audience = pdf_audience
                classify = f"{title}. {pdf_audience}"
                status, towns, reason = base.eligibility(classify, source["_towns"])

        if status == "review" and clearly_non_municipal(audience or title):
            status = "not_relevant"
            towns = []
            reason = "I destinatari rilevati non sono amministrazioni comunali."
        if status == "not_relevant":
            continue

        opens, deadline, published = base.dates(listing)
        if detail and (not deadline or not published):
            detail_opens, detail_deadline, detail_published = base.dates(base.visible(detail))
            opens = opens or detail_opens
            deadline = deadline or detail_deadline
            published = published or detail_published
        if deadline and date.fromisoformat(deadline) < today:
            continue

        total, maximum = base.money(base.clean(f"{body}. {audience}"))
        item = base.opportunity(
            source, title, url, body, today, classify, opens, deadline, published, total, maximum
        )
        item["eligibility"] = status
        item["municipalities"] = towns
        item["eligibility_reason"] = reason
        item["priority"] = base.priority(status, deadline, item["themes"], today)
        if document_url:
            item["eligibility_document_url"] = document_url
            item["eligibility_document_type"] = "pdf"
            item["eligibility_document_used"] = True
        out.append(item)

    return out


def collect_grants(
    source: dict,
    today: date,
    payload: str,
    loader: Callable[[str], str] | None = None,
    pdf_text_loader: Callable[[str], str] | None = None,
):
    loader = loader or base.fetch

    def focused(url: str) -> str:
        raw = loader(url)
        section = audience_section(raw)
        if not section:
            section, _ = pdf_evidence.attached_pdf_audience(
                raw, url, text_loader=pdf_text_loader
            )
        return f"<h2>Destinatari</h2><p>{section}</p>" if section else "<p></p>"

    return ORIG_GRANTS(source, today, payload, focused)


base.collect_html = lambda source, today, payload: collect_html(source, today, payload, base.fetch)
base.collect_grants = lambda source, today, payload, detail_loader=None: collect_grants(
    source, today, payload, base.fetch
)

if __name__ == "__main__":
    raise SystemExit(base.main())
