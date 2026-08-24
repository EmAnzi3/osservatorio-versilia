#!/usr/bin/env python3
"""Contratti statici per Sport/LIFE e first-seen del Radar v0.4.4."""
from __future__ import annotations

from datetime import date

import run_opportunity_radar_v044 as radar


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

    print("Radar v0.4.4 static contracts OK: Sport + 4 LIFE pubblicabili · ENERPOV solo discovery · 7/7 Comuni qualificati come conditional.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
