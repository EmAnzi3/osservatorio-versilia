#!/usr/bin/env python3
"""Entry point v0.3 con compatibilità e hardening del discovery.

- espone il fetch resiliente al namespace atteso dal collector v0.3;
- amplia il parser listing a h5/h6 per portali istituzionali diversi da Regione Toscana;
- aggiunge la sezione 'A chi si rivolge' alla lettura dei destinatari;
- propaga alla matrice di copertura le icone affidabili del registro di presentazione.
"""
from __future__ import annotations

import json
import re

import opportunity_radar_v03 as radar

radar.v025.v022.fetch_resilient = radar.v025.v022.v02.fetch_resilient

quality = radar.v025.v022.v02.quality
if "a chi si rivolge" not in quality.AUDIENCE_KEYS:
    quality.AUDIENCE_KEYS = tuple(quality.AUDIENCE_KEYS) + ("a chi si rivolge",)

_ORIGINAL_COLLECT_HTML = quality.collect_html


def _expanded_collect_html(source, today, payload, loader=None, pdf_text_loader=None):
    # Alcuni portali (es. Sviluppo Toscana / portali ministeriali) usano h5/h6
    # per i titoli delle card. Li normalizziamo soltanto nel listing, lasciando
    # invariata la lettura della scheda e dei PDF ufficiali.
    expanded = re.sub(r"<(/?)h[56](\b[^>]*)>", r"<\1h4\2>", payload, flags=re.I)
    rows = _ORIGINAL_COLLECT_HTML(
        source,
        today,
        expanded,
        loader=loader,
        pdf_text_loader=pdf_text_loader,
    )
    terms = [radar.base.norm(term) for term in source.get("listingIncludeTerms") or [] if term]
    if not terms:
        return rows
    filtered = []
    for item in rows:
        context = radar.base.norm(
            f"{item.get('title', '')}. {item.get('summary', '')}. {item.get('beneficiary_text', '')}"
        )
        if any(term in context for term in terms):
            filtered.append(item)
    return filtered


quality.collect_html = _expanded_collect_html

_ORIGINAL_BUILD_COVERAGE = radar.build_coverage


def _build_coverage_with_visuals(result, registry, discovery_states):
    coverage = _ORIGINAL_BUILD_COVERAGE(result, registry, discovery_states)
    presentation = json.loads(radar.DEFAULT_PRESENTATION.read_text(encoding="utf-8"))
    visuals = presentation.get("sources") or {}
    for row in coverage.get("rows") or []:
        meta = visuals.get(str(row.get("source_id") or "")) or {}
        if meta.get("favicon"):
            row["favicon"] = meta["favicon"]
    return coverage


radar.build_coverage = _build_coverage_with_visuals

if __name__ == "__main__":
    raise SystemExit(radar.main())
