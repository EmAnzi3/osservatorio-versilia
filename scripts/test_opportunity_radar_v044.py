#!/usr/bin/env python3
"""Contratti statici per Sport/LIFE, first-seen e copertura Toscana del Radar v0.4.4."""
from __future__ import annotations

from datetime import date

import run_opportunity_radar_v044 as radar


CELEBRAZIONI_URL = (
    "https://www.regione.toscana.it/it/-/"
    "celebrazioni-storiche-2026-sostegno-a-progetti-dedicati-a-san-francesco-collodi-e-alluvione-firenze"
)


def _test_regione_toscana_bandi_tutti(config: dict, coverage: dict) -> None:
    primary = {
        str(item.get("id") or ""): item
        for item in config.get("sources") or []
    }
    source = primary.get("regione-toscana-tutti")
    assert source is not None, "bandi-tutti deve essere un collector primario"
    assert source.get("ruleSourceId") == "regione-toscana"
    assert "/bandi-tutti?" in str(source.get("url") or "")
    assert (coverage.get("sources") or {}).get("regione-toscana-tutti", {}).get("role") == "primary"

    payloads: dict[str, str] = {}
    for item in config.get("sources") or []:
        source_id = str(item.get("id") or "")
        payloads[source_id] = "[]" if item.get("type") == "padigitale_json" else "<html><body></body></html>"

    listing = """
    <html><body>
      <h2><a href="/it/-/celebrazioni-storiche-2026-sostegno-a-progetti-dedicati-a-san-francesco-collodi-e-alluvione-firenze">
        Sostegno a progetti dedicati a San Francesco, Collodi e Alluvione di Firenze
      </a></h2>
      <p>Pubblicato il 19.08.2026 Stato: Aperto Scadenza presentazione domande 18.09.2026 13:00</p>
    </body></html>
    """
    detail = """
    <html><body>
      <h1>Celebrazioni storiche 2026</h1>
      <h2>Destinatari / beneficiari</h2>
      <p>Enti locali della Toscana e soggetti iscritti al Registro unico nazionale del Terzo settore.</p>
      <h2>Come partecipare</h2>
      <p>Il progetto deve essere realizzato in Toscana nel 2026 e dedicato a una delle ricorrenze previste.</p>
    </body></html>
    """
    payloads["regione-toscana-tutti"] = listing
    detail_payloads = {CELEBRAZIONI_URL: detail}
    discovery_payloads = {
        str(url): "<html><body></body></html>"
        for item in config.get("discoverySources") or []
        for url in item.get("urls") or []
    }

    # Prima isola il collector HTML: il caso deve emergere dalla listing e dal dettaglio
    # ufficiale senza dipendere dalle regole documentali successive.
    source_runtime = {**source, "_towns": list(config.get("municipalities") or [])}
    quality = radar.radar.v025.v022.v02.quality
    collected = quality.collect_html(
        source_runtime,
        date(2026, 8, 25),
        listing,
        loader=lambda url: detail_payloads.get(url, ""),
    )
    assert len(collected) == 1, [(x.get("title"), x.get("url"), x.get("eligibility")) for x in collected]
    assert collected[0].get("url") == CELEBRAZIONI_URL
    assert collected[0].get("eligibility") == "eligible"

    result = radar.run_v04(
        date(2026, 8, 25),
        payloads=payloads,
        detail_payloads=detail_payloads,
        discovery_payloads=discovery_payloads,
    )
    matches = [
        item for item in result.get("opportunities") or []
        if item.get("rule_id") == "rt-celebrazioni-storiche-2026"
    ]
    diagnostics = {
        "source": next((x for x in result.get("sources") or [] if x.get("sourceId") == "regione-toscana-tutti"), None),
        "review": [x for x in result.get("reviewQueue") or [] if x.get("source_id") == "regione-toscana-tutti"],
        "qualityHold": [
            {
                "title": x.get("title"),
                "rule_id": x.get("rule_id"),
                "eligibility": x.get("eligibility"),
                "quality_gate": x.get("quality_gate"),
            }
            for x in result.get("qualityHold") or []
            if x.get("source_id") == "regione-toscana-tutti"
        ],
    }
    assert len(matches) == 1, "Il fixture bandi-tutti non raggiunge l'output: " + repr(diagnostics)
    item = matches[0]
    assert item.get("source_id") == "regione-toscana-tutti"
    assert item.get("url") == CELEBRAZIONI_URL
    assert item.get("eligibility") == "conditional"
    assert item.get("applicant_eligibility") == "conditional"
    assert item.get("municipality_role") == "direct_applicant"
    assert item.get("actionable_for_municipality") is True
    assert item.get("deadline_at") == "2026-09-18"
    assert len(item.get("municipalities") or []) == 7
    assert item.get("discovery_only") is not True
    presentation = item.get("presentation") or {}
    assert presentation.get("source_label") == "Regione Toscana"
    assert presentation.get("source_mark") == "RT"


def main() -> int:
    config, coverage = radar.compose_runtime_payloads()
    discovery = {
        str(item.get("id") or ""): item
        for item in config.get("discoverySources") or []
    }
    assert "pcm-sport" in discovery
    assert "cinea-life" in discovery
    sport_urls = set(discovery["pcm-sport"].get("urls") or [])
    life_urls = set(discovery["cinea-life"].get("urls") or [])
    assert any("avvisibandi.sport.governo.it" in url for url in sport_urls)
    assert any("heating-and-cooling-plans" in url for url in life_urls)
    assert any("energy-communities" in url for url in life_urls)
    assert any("energy-poverty" in url for url in life_urls), "ENERPOV deve essere monitorato"

    registry = coverage.get("sources") or {}
    assert registry["pcm-sport"]["family"] == "sport-social-infrastructure"
    assert registry["cinea-life"]["family"] == "energy-climate-environment"

    verified = radar._load(radar.VERIFIED_V044).get("entries") or []
    ids = {str(item.get("coverage_id") or "") for item in verified}
    expected = {
        "pcm-sport-eventi-2026",
        "life-2026-cet-heatcoolplan",
        "life-2026-cet-pda",
        "life-2026-cet-enercom",
        "life-2026-cet-empower",
    }
    assert ids == expected, ids
    assert not any("enerpov" in coverage_id.lower() for coverage_id in ids), "ENERPOV non è ancora qualificato per la pubblicazione"
    assert all(item.get("first_seen_at") == "2026-08-24" for item in verified)

    today = date(2026, 8, 24)
    cards = [radar.build_seed_item(item, today, "test") for item in verified]
    assert all(card.get("actionable_for_municipality") for card in cards)
    assert any(card.get("municipality_role") == "direct_applicant" for card in cards)
    assert sum(card.get("municipality_role") == "direct_or_partner" for card in cards) == 4
    for item in verified:
        matrix = item.get("municipality_status_overrides") or {}
        assert len(matrix) == 7
        assert set(matrix) == set(radar.core.TOWNS)
        assert all((row or {}).get("status") == "conditional" for row in matrix.values())

    mock = {
        "sourceCoverage": {
            "rows": [
                {"source_id": "pcm-sport"},
                {"source_id": "cinea-life"},
            ]
        }
    }
    evidence = radar._v044_evidence_audit(mock, today)
    assert evidence["status"] == "pass", evidence
    assert evidence["sourcesVerified"] == evidence["sourcesExpected"] == 2

    _test_regione_toscana_bandi_tutti(config, coverage)

    print(
        "Radar v0.4.4 contracts OK: Sport + 4 LIFE pubblicabili · ENERPOV solo discovery · "
        "Regione bandi-tutti primaria · Celebrazioni raggiunge l'output operativo."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
