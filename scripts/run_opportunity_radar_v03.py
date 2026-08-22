#!/usr/bin/env python3
"""Entry point v0.3 con compatibilità e hardening del discovery.

- espone il fetch resiliente al namespace atteso dal collector v0.3;
- amplia il parser listing a h5/h6 per portali istituzionali diversi da Regione Toscana;
- aggiunge la sezione 'A chi si rivolge' alla lettura dei destinatari;
- usa asset SVG locali per le icone fonte che non espongono favicon affidabili;
- risolve dettagli ufficiali verificati che i listing non espongono correttamente;
- collassa duplicati semantici dello stesso bando tramite rule_id;
- riconcilia la continuità sull'output finale, dopo i recuperi documentali verificati.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import opportunity_radar_v03 as radar
import opportunity_radar_v03_post as post

radar.v025.v022.fetch_resilient = radar.v025.v022.v02.fetch_resilient

quality = radar.v025.v022.v02.quality
if "a chi si rivolge" not in quality.AUDIENCE_KEYS:
    quality.AUDIENCE_KEYS = tuple(quality.AUDIENCE_KEYS) + ("a chi si rivolge",)

_ORIGINAL_COLLECT_HTML = quality.collect_html
_ICON_REGISTRY = radar.ROOT / "data" / "opportunity-source-icons-v03.json"


def _local_icons():
    payload = json.loads(_ICON_REGISTRY.read_text(encoding="utf-8"))
    return {str(k): str(v) for k, v in (payload.get("icons") or {}).items()}


def _expanded_collect_html(source, today, payload, loader=None, pdf_text_loader=None):
    # Alcuni portali istituzionali usano h5/h6 per i titoli delle card.
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

_ORIGINAL_ATTACH_SOURCE_VISUALS = radar.attach_source_visuals


def _attach_source_visuals_with_local_icons(result, presentation_path):
    _ORIGINAL_ATTACH_SOURCE_VISUALS(result, presentation_path)
    icons = _local_icons()
    for item in result.get("opportunities") or []:
        sid = str(item.get("source_id") or "")
        if sid in icons:
            item.setdefault("presentation", {})["source_favicon"] = icons[sid]
    for item in result.get("archive") or []:
        sid = str(item.get("source_id") or "")
        if sid in icons:
            item["source_favicon"] = icons[sid]


radar.attach_source_visuals = _attach_source_visuals_with_local_icons

_ORIGINAL_BUILD_COVERAGE = radar.build_coverage


def _build_coverage_with_visuals(result, registry, discovery_states):
    coverage = _ORIGINAL_BUILD_COVERAGE(result, registry, discovery_states)
    presentation = json.loads(radar.DEFAULT_PRESENTATION.read_text(encoding="utf-8"))
    visuals = presentation.get("sources") or {}
    icons = _local_icons()
    for row in coverage.get("rows") or []:
        sid = str(row.get("source_id") or "")
        meta = visuals.get(sid) or {}
        favicon = icons.get(sid) or meta.get("favicon")
        if favicon:
            row["favicon"] = favicon
    return coverage


radar.build_coverage = _build_coverage_with_visuals

_ORIGINAL_RUN = radar.run
_VERIFIED = radar.ROOT / "data" / "opportunity-verified-details-v03.json"


def _reconcile_final_continuity(result):
    """Rimuove solo gli HOLD che risultano presenti nell'output finale.

    Il collector base calcola la continuità prima del recupero documentale v0.3.
    Se un bando viene recuperato dopo (es. Jazz 2027), non deve risultare nello
    stesso run sia tra le opportunità correnti sia tra i continuity hold.
    """
    active = {radar.v025.identity_key(item) for item in result.get("opportunities") or []}
    holds = [
        hold for hold in result.get("continuityHold") or []
        if str(hold.get("identity_key") or "") not in active
    ]
    result["continuityHold"] = holds
    result.setdefault("counts", {})["continuityHold"] = len(holds)
    return result


def _hardened_run(config_path: Path, today, **kwargs):
    result = _ORIGINAL_RUN(config_path, today, **kwargs)
    result = post.harden(
        radar,
        result,
        config_path,
        today,
        kwargs.get("presentation_path", radar.DEFAULT_PRESENTATION),
        _VERIFIED,
        detail_payloads=kwargs.get("detail_payloads"),
        live=kwargs.get("payloads") is None,
    )
    return _reconcile_final_continuity(result)


radar.run = _hardened_run

if __name__ == "__main__":
    raise SystemExit(radar.main())
