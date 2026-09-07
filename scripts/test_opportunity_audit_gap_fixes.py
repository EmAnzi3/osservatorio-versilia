#!/usr/bin/env python3
"""Contratti dei fix emersi dall'audit indipendente del 7 settembre 2026."""
from __future__ import annotations

from datetime import date
from pathlib import Path

import opportunity_daily_refresh_audit_fixed as fixed
import opportunity_regione_toscana_guard as guard


ROOT = Path(__file__).resolve().parents[1]
C4T_ID = "eu-c4t-groundwork-2026"
CERV_ID = "eu-cerv-town-twinning-2026"


def test_c4t_source_and_verified_seed() -> None:
    fixes = fixed._load_fixes()
    entries = fixes.get("verifiedEntries") or []
    assert len(entries) == 1
    entry = entries[0]
    assert entry.get("coverage_id") == C4T_ID
    assert entry.get("deadline_at") == "2026-09-11"
    assert entry.get("municipality_role") == "direct_applicant"
    assert "PO2" in str(entry.get("project_requirements") or "")

    matrix = entry.get("municipality_status_overrides") or {}
    assert set(matrix) == set(fixed.core.TOWNS)
    assert all((row or {}).get("status") == "conditional" for row in matrix.values())

    config, coverage = fixed._compose_with_audit_fixes()
    discovery = {
        str(source.get("id") or ""): source
        for source in config.get("discoverySources") or []
    }
    assert "eu-c4t-groundwork" in discovery
    assert any("managenergy.ec.europa.eu" in url for url in discovery["eu-c4t-groundwork"].get("urls") or [])
    registry = coverage.get("sources") or {}
    assert registry["eu-c4t-groundwork"]["monitoringStatus"] == "active"
    assert registry["eu-c4t-groundwork"]["family"] == "energy-climate-environment"


def test_c4t_injection_is_conditional_and_deterministic() -> None:
    entry = fixed._load_fixes()["verifiedEntries"][0]
    url = entry["url"]
    fixture = """
    <html><body>
      <h1>C4T GROUNDWORK call open for technical assistance</h1>
      <p>Local and regional authorities involved in Cohesion Policy investments under PO2 can apply.</p>
      <p>Applications must be submitted by 11 September 2026.</p>
    </body></html>
    """
    result = {"opportunities": [], "archive": [], "coverageHold": []}
    resolved = fixed._inject_fix_entries(
        result,
        date(2026, 9, 7),
        detail_payloads={url: fixture},
        live=False,
    )
    assert C4T_ID in resolved
    assert result["coverageHold"] == []
    assert len(result["opportunities"]) == 1
    item = result["opportunities"][0]
    assert item.get("coverage_id") == C4T_ID
    assert item.get("eligibility") == "conditional"
    assert item.get("applicant_eligibility") == "conditional"
    assert item.get("municipality_role") == "direct_applicant"
    assert item.get("deadline_at") == "2026-09-11"
    assert item.get("first_seen_at") == "2026-09-07"
    assert all(
        (row or {}).get("status") == "conditional"
        for row in (item.get("municipality_eligibility") or {}).values()
    )


def _all_verified_detail_fixtures() -> dict[str, str]:
    paths = (
        "opportunity-verified-v04.json",
        "opportunity-verified-v04-extra.json",
        "opportunity-verified-v042.json",
        "opportunity-verified-v043.json",
        "opportunity-verified-v044.json",
    )
    detail_payloads: dict[str, str] = {}
    for name in paths:
        payload = fixed.core._load(ROOT / "data" / name)
        for entry in payload.get("entries") or []:
            url = str(entry.get("url") or "")
            terms = [str(term) for term in entry.get("required_terms") or []]
            if url:
                detail_payloads[url] = "<html><body>" + " | ".join(terms) + "</body></html>"
    for entry in fixed._load_fixes().get("verifiedEntries") or []:
        url = str(entry.get("url") or "")
        terms = [str(term) for term in entry.get("required_terms") or []]
        if url:
            detail_payloads[url] = "<html><body>" + " | ".join(terms) + "</body></html>"
    return detail_payloads


def test_overlay_reaches_real_v044_run_and_recomputes_counts() -> None:
    """Blind test sul percorso del motore, non solo sulla funzione di injection."""
    config, _ = fixed._compose_with_audit_fixes()
    payloads = {
        str(source.get("id") or ""): (
            "[]" if source.get("type") == "padigitale_json" else "<html><body></body></html>"
        )
        for source in config.get("sources") or []
    }
    discovery_payloads = {
        str(url): "<html><body></body></html>"
        for source in config.get("discoverySources") or []
        for url in source.get("urls") or []
    }
    detail_payloads = _all_verified_detail_fixtures()

    original_compose = fixed.core.compose_runtime_payloads
    original_core_inject = fixed.core.inject_verified_v04
    original_radar_inject = getattr(fixed.radar_module, "inject_verified_v04", None)
    fixed.core.compose_runtime_payloads = fixed._compose_with_audit_fixes
    fixed.core.inject_verified_v04 = fixed._inject_with_audit_fixes
    if original_radar_inject is not None:
        fixed.radar_module.inject_verified_v04 = fixed._inject_with_audit_fixes
    try:
        result = fixed.radar_module.run_v04(
            date(2026, 9, 7),
            payloads=payloads,
            detail_payloads=detail_payloads,
            discovery_payloads=discovery_payloads,
        )
    finally:
        fixed.core.compose_runtime_payloads = original_compose
        fixed.core.inject_verified_v04 = original_core_inject
        if original_radar_inject is not None:
            fixed.radar_module.inject_verified_v04 = original_radar_inject

    by_id = {
        str(item.get("coverage_id") or ""): item
        for item in result.get("opportunities") or []
        if item.get("coverage_id")
    }
    assert C4T_ID in by_id, sorted(by_id)
    assert CERV_ID in by_id, sorted(by_id)
    assert by_id[C4T_ID].get("eligibility") == "conditional"
    assert (result.get("counts") or {}).get("public") == len(result.get("opportunities") or [])
    assert (result.get("coverageAudit") or {}).get("status") == "pass", result.get("coverageAudit")


def test_cerv_regression_contract_is_already_active() -> None:
    sentinels = fixed.core._load(ROOT / "data" / "opportunity-coverage-sentinels-v042.json")
    current = {
        str(case.get("coverage_id") or "")
        for case in sentinels.get("cases") or []
        if case.get("expected") == "current"
    }
    assert CERV_ID in current

    verified = fixed.core._load(ROOT / "data" / "opportunity-verified-v042.json")
    entries = {
        str(entry.get("coverage_id") or ""): entry
        for entry in verified.get("entries") or []
    }
    cerv = entries.get(CERV_ID)
    assert cerv is not None
    assert cerv.get("deadline_at") == "2026-09-23"
    assert cerv.get("municipality_role") == "direct_applicant"


def test_mercati_rionali_cross_source_contract() -> None:
    candidate = {
        "title": "Mercati rionali: contributi ai Comuni per ammodernamento, ampliamento e riqualificazione",
        "url": "https://www.regione.toscana.it/it/-/mercati-rionali-contributi-ai-comuni-per-ammodernamento-ampliamento-e-riqualificazione",
        "deadline_at": "2026-09-15",
    }
    public = {
        "title": "Avviso Mercati Rionali",
        "url": "https://www.sviluppo.toscana.it/bando/avviso-mercati-rionali/",
        "deadline_at": "2026-09-15",
        "rule_id": "st-mercati-rionali-2026",
    }
    result = {"opportunities": [public]}
    assert guard._cross_source_identity(candidate) == "rt-mercati-rionali-2026"
    assert guard._cross_source_identity(public) == "rt-mercati-rionali-2026"
    assert guard._account_state(result, candidate) == "public"


def main() -> int:
    test_c4t_source_and_verified_seed()
    test_c4t_injection_is_conditional_and_deterministic()
    test_overlay_reaches_real_v044_run_and_recomputes_counts()
    test_cerv_regression_contract_is_already_active()
    test_mercati_rionali_cross_source_contract()
    print("Audit gap fixes: C4T + CERV + Mercati rionali PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
