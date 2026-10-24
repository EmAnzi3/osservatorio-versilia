#!/usr/bin/env python3
"""Contratti dei fix emersi dall'audit indipendente del 7 settembre 2026."""
from __future__ import annotations

from datetime import date
from pathlib import Path
import hashlib
import json

import opportunity_daily_refresh_audit_fixed as fixed
import opportunity_regione_toscana_guard as guard


ROOT = Path(__file__).resolve().parents[1]
C4T_ID = "eu-c4t-groundwork-2026"
CERV_ID = "eu-cerv-town-twinning-2026"
PROLOCO_ID = "rt-proloco-identita-locali-partner-2026"
SMARTOSCANA_DATI_ID = "rt-smartoscana-dati-enti-locali-2026"


def test_proloco_documented_partnership() -> None:
    """Real frozen source, not required_terms synthesized from the entry."""
    from pypdf import PdfReader
    from opportunity_municipal_relevance import apply_to_payload
    fixture = ROOT / "tests/fixtures/proloco-notices"
    provenance = json.loads((fixture / "provenance.json").read_text())
    entry = next(e for e in fixed._load_fixes()["verifiedEntries"] if e["coverage_id"] == PROLOCO_ID)
    document = fixture / "avviso.pdf"
    assert hashlib.sha256(document.read_bytes()).hexdigest() == "d350edaa454a9e24fa3db658721869f2d60f60a91a9842c8b55af5b13d2aed9f"
    assert entry["document_evidence"] == provenance["document"]
    assert provenance["decree"]["annexAExpectedSha256"] == entry["document_evidence"]["sha256"]
    assert entry["supporting_documents"] == provenance["supporting_documents"]
    for label, expected_pages, expected_hash in (
        ("B", 8, "d87ab7615eeaec9db868456fc04bb84f1757c9a789350f9537cd92884524a2d2"),
        ("C", 3, "6722746568df649ce2756703e629718883ead7e533a7a9277bbaf8e4d6b6c2b7"),
    ):
        supporting = fixture / ("allegato-" + label + ".pdf")
        assert hashlib.sha256(supporting.read_bytes()).hexdigest() == expected_hash
        assert len(PdfReader(supporting).pages) == expected_pages
    reader = PdfReader(document)
    assert len(reader.pages) == 13
    page2 = " ".join(reader.pages[1].extract_text().split())
    page5 = " ".join(reader.pages[4].extract_text().split())
    assert "realizzazione condivisa delle attività progettuali" in page2
    assert "associazioni pro-loco iscritte" in page2
    assert "attività e dei rispettivi ruoli" in page5
    source = (fixture / "source.html").read_text()
    assert hashlib.sha256((fixture / "source.html").read_bytes()).hexdigest() == provenance["pageSha256"]
    assert entry["allow_recent_evidence_fallback"] is False
    assert not fixed.core.verify_entry(entry, date(2026, 10, 18), live=False)[0]
    details = {entry["url"]: source}
    assert fixed.core.verify_entry(entry, date(2026, 10, 18), detail_payloads=details, live=False)[0]
    # A changed application term must fail the current-source reconfirmation.
    changed = source.replace("03.11.2026 13:00", "04.11.2026 13:00")
    assert not fixed.core.verify_entry(entry, date(2026, 10, 18), detail_payloads={entry["url"]: changed}, live=False)[0]
    result = {"opportunities": [], "coverageHold": [], "reviewQueue": [{"url": entry["url"], "title": "Pro Loco"}]}
    fixed._inject_fix_entries(result, date(2026, 10, 18), detail_payloads=details, live=False)
    items = [x for x in result["opportunities"] if x["coverage_id"] == PROLOCO_ID]
    assert len(items) == 1
    item = items[0]
    assert item["municipality_role"] == "partner" and item["partnership_required"]
    assert item["applicant_eligibility"] == "not_direct_applicant"
    assert item["deadline_at"] == "2026-11-03" and item["deadline_time"] == "13:00"
    assert set(item["municipality_eligibility"]) == set(fixed.core.TOWNS)
    assert all(x["status"] == "conditional" for x in item["municipality_eligibility"].values())
    apply_to_payload(result)
    assert result["municipalRelevance"]["partnershipTotal"] == 1
    assert result["municipalRelevance"]["headlineTotal"] == 0
    assert not item["municipal_headline"]
    candidate = {"url": entry["url"], "title": "Sostegno pro-loco", "published_at": "2026-10-14", "age_days": 4}
    guard.apply(result, date(2026, 10, 18), candidates=[candidate])
    assert result["regionalCompleteness"]["status"] == "pass"
    assert not any(x.get("gate_origin") == "regional_completeness" for x in result["coverageHold"])
    # Repeated injection cannot duplicate the card; other holds stay effective.
    result["coverageHold"].append({"coverage_id": "unrelated", "reason": "unresolved"})
    fixed._inject_fix_entries(result, date(2026, 10, 18), detail_payloads=details, live=False)
    assert len([x for x in result["opportunities"] if x.get("coverage_id") == PROLOCO_ID]) == 1
    assert {"coverage_id": "unrelated", "reason": "unresolved"} in result["coverageHold"]
    missing = {"opportunities": []}
    fixed._inject_fix_entries(missing, date(2026, 10, 18), live=False)
    assert not any(x.get("coverage_id") == PROLOCO_ID for x in missing["opportunities"])
    assert any(x.get("coverage_id") == PROLOCO_ID for x in missing["coverageHold"])
    expired = {"opportunities": []}
    fixed._inject_fix_entries(expired, date(2026, 11, 4), live=False)
    assert not any(x.get("coverage_id") == PROLOCO_ID for x in expired["opportunities"])
    assert any(x.get("coverage_id") == PROLOCO_ID for x in expired["archive"])


def test_smartoscana_data_call_resolves_regional_review() -> None:
    """Bando a sportello per Comuni: la qualificazione chiude il candidato regionale.

    Evidenza: estratto congelato della pagina ufficiale e impronte di Allegato A
    e Allegato O coincidenti con quelle dichiarate nel decreto 22706/2026.
    """
    from opportunity_municipal_relevance import apply_to_payload
    fixture = ROOT / "tests/fixtures/rt-dati-enti-locali-notices"
    provenance = json.loads((fixture / "provenance.json").read_text(encoding="utf-8"))
    entry = next(e for e in fixed._load_fixes()["verifiedEntries"] if e["coverage_id"] == SMARTOSCANA_DATI_ID)
    source_path = fixture / "source-extract.html"
    assert hashlib.sha256(source_path.read_bytes()).hexdigest() == provenance["pageExtractSha256"]
    assert entry["url"] == provenance["pageUrl"]
    assert entry["document_evidence"]["sha256"] == provenance["decree"]["annexAExpectedSha256"]
    assert {d["sha256"] for d in entry["supporting_documents"]} >= {provenance["decree"]["annexOExpectedSha256"]}
    assert entry["document_evidence"] == {k: provenance["document"][k] for k in ("url", "sha256", "pages")}
    assert entry["supporting_documents"] == provenance["supporting_documents"]
    source = source_path.read_text(encoding="utf-8")
    folded = fixed.core.radar.v025.fold(fixed.core.radar.base.visible(source))
    for phrase in ("i Comuni toscani", "in forma singola in qualità di beneficiario unico",
                   "ore 9.00 del 22 ottobre", "duecentosettantesimo giorno solare", "€ 367.643,80"):
        assert fixed.core.radar.v025.fold(phrase) in folded, phrase
    assert entry["allow_recent_evidence_fallback"] is False
    today = date(2026, 10, 25)
    assert not fixed.core.verify_entry(entry, today, live=False)[0]
    details = {entry["url"]: source}
    assert fixed.core.verify_entry(entry, today, detail_payloads=details, live=False)[0]
    # Un cambio della dotazione pubblicata deve far fallire la riconferma.
    changed = source.replace("367.643,80", "400.000,00")
    assert not fixed.core.verify_entry(entry, today, detail_payloads={entry["url"]: changed}, live=False)[0]

    result = {"opportunities": [], "coverageHold": [], "reviewQueue": [{"url": entry["url"], "title": "SmarToscana dati"}]}
    fixed._inject_fix_entries(result, today, detail_payloads=details, live=False)
    items = [x for x in result["opportunities"] if x["coverage_id"] == SMARTOSCANA_DATI_ID]
    assert len(items) == 1
    item = items[0]
    assert item["municipality_role"] == "direct_applicant"
    assert item["lifecycle_stage"] == "rolling_open"
    assert set(item["municipality_eligibility"]) == set(fixed.core.TOWNS)
    assert all(x["status"] == "conditional" for x in item["municipality_eligibility"].values())
    apply_to_payload(result)
    assert item["municipal_headline"]

    # Lo stesso candidato che oggi produrrebbe un hold (eta 4 > grazia 3) risulta pubblico.
    candidate = {"url": entry["url"], "title": "Contributi agli enti locali per lo sviluppo di progettualità sui dati: il bando 2026",
                 "published_at": "2026-10-21", "age_days": 4}
    guard.apply(result, today, candidates=[candidate])
    assert result["regionalCompleteness"]["status"] == "pass"
    assert result["regionalCompleteness"]["overdue"] == []
    assert not any(x.get("gate_origin") == "regional_completeness" for x in result["coverageHold"])
    unresolved = {"opportunities": [], "coverageHold": []}
    guard.apply(unresolved, today, candidates=[candidate])
    assert unresolved["regionalCompleteness"]["status"] == "fail", "senza qualificazione il gate deve restare bloccante"

    # Lo sportello resta aperto fino al termine ordinario documentato, poi la scheda esce.
    still_open = {"opportunities": []}
    fixed._inject_fix_entries(still_open, date(2027, 7, 1), detail_payloads=details, live=False)
    assert any(x.get("coverage_id") == SMARTOSCANA_DATI_ID for x in still_open["opportunities"])


def test_reviewed_regional_seeds() -> None:
    entries = {e["coverage_id"]: e for e in fixed._load_fixes()["verifiedEntries"]}
    for key in ("rt-artea-immobile-sede-2026", "rt-risorse-genetiche-agrarie-aca16b-2026"):
        entry = entries[key]
        assert entry["allow_recent_evidence_fallback"] is False
        assert len(entry["document_evidence"]["sha256"]) == 64
        assert not fixed.core.verify_entry(entry, date(2026, 10, 11), live=False)[0]
    for day, stage in [(date(2026, 10, 11), "announced_upcoming"), (date(2026, 11, 2), "application_open")]:
        result = {"opportunities": []}
        details = {e["url"]: "<p>" + " | ".join(e["required_terms"]) + "</p>" for e in entries.values()}
        fixed._inject_fix_entries(result, day, detail_payloads=details, live=False)
        item = next(x for x in result["opportunities"] if x["coverage_id"] == "rt-risorse-genetiche-agrarie-aca16b-2026")
        assert item["lifecycle_stage"] == stage
        assert item["deadline_at"] == "2026-11-30" and item["deadline_time"] == "13:00"
    kiev = entries["rt-generatori-kiev-cooperazione-2026"]
    assert kiev["deadline_at"] == "2026-10-12" and kiev["allow_recent_evidence_fallback"] is False
    assert "15.a" in kiev["project_requirements"] and "nessun intervento locale" in kiev["project_requirements"]
    assert kiev["supporting_documents"][0]["sha256"] == "de0025cd57a8488bcbfd1645d9445ad97822d89956aa3df7d0ac5f6235a2a215"
    social = entries["mlps-assistenti-sociali-manifestazione-2026"]
    result = {"opportunities": []}
    fixed._inject_fix_entries(result, date(2026, 10, 11), detail_payloads={social["url"]: " | ".join(social["required_terms"])}, live=False)
    item = next(x for x in result["opportunities"] if x["coverage_id"] == social["coverage_id"])
    assert item["deadline_at"] == "2026-11-11" and item["municipality_role"] == "direct_applicant"
    assert "SIOSS" in item["project_requirements"] and "senza nuovi contributi" in item["project_requirements"]
    assert not fixed.core.verify_entry(social, date(2026, 10, 11), live=False)[0]
    assert "Firenze" in entries["rt-artea-immobile-sede-2026"]["project_requirements"]
    entry = entries["rt-spreco-alimentare-ets-partner-2026"]
    result = {"opportunities": []}
    details = {entry["url"]: " | ".join(entry["required_terms"])}
    fixed._inject_fix_entries(result, date(2026, 10, 11), detail_payloads=details, live=False)
    item = next(x for x in result["opportunities"] if x["coverage_id"] == entry["coverage_id"])
    assert item["municipality_role"] == "partner" and item["partnership_required"]
    assert item["applicant_eligibility"] == "not_direct_applicant"
    assert item["deadline_time"] == "14:00"
    from opportunity_municipal_relevance import annotate_item
    assert annotate_item(item) == "partner" and not item["municipal_headline"]


def test_concrete_versilia_scope_excludes_only_reviewed_calls() -> None:
    entries = {e["coverage_id"]: e for e in fixed._load_fixes()["verifiedEntries"]}
    rejected = {"rt-artea-immobile-sede-2026", "rt-generatori-kiev-cooperazione-2026"}
    kept = {"rt-risorse-genetiche-agrarie-aca16b-2026", "rt-spreco-alimentare-ets-partner-2026", "mlps-assistenti-sociali-manifestazione-2026"}
    unrelated = {"url": "https://www.regione.toscana.it/it/-/altro-avviso", "title": "Altro avviso"}
    result = {"referenceDate": "2026-10-11", "opportunities": [dict(entries[x]) for x in rejected],
              "continuityHold": [dict(entries[x]) for x in rejected] + [unrelated],
              "coverageHold": [dict(entries[x]) for x in rejected] + [unrelated],
              "discoveryQueue": [dict(entries[x]) for x in rejected]}
    details = {e["url"]: " | ".join(e["required_terms"]) for e in entries.values()}
    fixed._inject_fix_entries(result, date(2026, 10, 11), detail_payloads=details, live=False)
    ids = {x.get("coverage_id") for x in result["opportunities"]}
    assert kept <= ids and ids.isdisjoint(rejected)
    assert all(guard._documented_exclusion_rule(entries[x]) is not None for x in rejected)
    assert guard._documented_exclusion_rule(entries["rt-risorse-genetiche-agrarie-aca16b-2026"]) is None
    assert result["continuityHold"] == [unrelated] and result["coverageHold"] == [unrelated]
    # A generic rediscovery with a different id must remain excluded by exact URL.
    result["opportunities"].append({"id": "rediscovered", "url": entries[next(iter(rejected))]["url"]})
    fixed._apply_publication_exclusions(result)
    assert not any(x.get("id") == "rediscovered" for x in result["opportunities"])
    actions = fixed.review_actions.build_actions(result)
    assert actions["items"] == [] and len(actions["discarded"]) == 2
    assert all(x["reasonCode"] == "outside_municipal_call" for x in actions["discarded"])


def test_c4t_source_and_verified_seed() -> None:
    fixes = fixed._load_fixes()
    entries = fixes.get("verifiedEntries") or []
    assert {e["coverage_id"] for e in entries} == {C4T_ID, PROLOCO_ID, "rt-artea-immobile-sede-2026", "rt-risorse-genetiche-agrarie-aca16b-2026", "rt-spreco-alimentare-ets-partner-2026", "mlps-assistenti-sociali-manifestazione-2026", "rt-generatori-kiev-cooperazione-2026", SMARTOSCANA_DATI_ID}
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


def test_expired_audit_entry_is_archived_without_live_probe() -> None:
    original_verify = fixed.core.verify_entry

    def unexpected_verify(*args, **kwargs):
        raise AssertionError("una candidatura scaduta non deve essere verificata live")

    fixed.core.verify_entry = unexpected_verify
    result = {"opportunities": [], "archive": [], "coverageHold": []}
    try:
        resolved = fixed._inject_fix_entries(result, date(2026, 9, 15), live=True)
    finally:
        fixed.core.verify_entry = original_verify

    assert C4T_ID in resolved
    assert result["opportunities"] == []
    assert result["coverageHold"] == []
    archived = {str(item.get("coverage_id") or ""): item for item in result["archive"]}
    assert C4T_ID in archived
    assert archived[C4T_ID].get("deadline_at") == "2026-09-11"


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


def test_overlay_reaches_real_v044_run_and_recomputes_counts(*, current_evidence: bool = False) -> None:
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
    replay_date = date(2026, 9, 7)
    if current_evidence:
        # Historical candidates retain their original lifecycle dates; renewed
        # coverage evidence must be checked at its own reference date.
        replay_date = max(
            replay_date,
            *(date.fromisoformat(fixed.core._load(ROOT / "data" / name)["referenceDate"])
              for name in ("opportunity-coverage-evidence-v043.json", "opportunity-coverage-evidence-v044.json")),
        )

    original_compose = fixed.core.compose_runtime_payloads
    original_core_inject = fixed.core.inject_verified_v04
    original_radar_inject = getattr(fixed.radar_module, "inject_verified_v04", None)
    fixed.core.compose_runtime_payloads = fixed._compose_with_audit_fixes
    fixed.core.inject_verified_v04 = fixed._inject_with_audit_fixes
    if original_radar_inject is not None:
        fixed.radar_module.inject_verified_v04 = fixed._inject_with_audit_fixes
    try:
        result = fixed.radar_module.run_v04(
            replay_date,
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
        for item in (result.get("opportunities") or []) + (result.get("archive") or [])
        if item.get("coverage_id")
    }
    assert C4T_ID in by_id, sorted(by_id)
    assert CERV_ID in by_id, sorted(by_id)
    if not current_evidence:
        assert by_id[C4T_ID].get("eligibility") == "conditional"
        assert {C4T_ID, CERV_ID} <= {
            item.get("coverage_id") for item in result.get("opportunities") or []
        }
    else:
        for coverage_id in (C4T_ID, CERV_ID):
            bucket = "archive" if date.fromisoformat(by_id[coverage_id]["deadline_at"]) < replay_date else "opportunities"
            assert coverage_id in {item.get("coverage_id") for item in result.get(bucket) or []}
    assert (result.get("counts") or {}).get("public") == len(result.get("opportunities") or [])
    audit = result.get("coverageAudit") or {}
    if current_evidence:
        assert audit.get("status") == "pass", audit
    else:
        # Evidence verified after the historical replay cannot attest coverage
        # at that time. Keep the production rejection of future evidence.
        for key in ("residualCoverage", "sportLifeCoverage"):
            rows = (audit.get(key) or {}).get("rows") or []
            max_age = (audit.get(key) or {}).get("maxEvidenceAgeDays", 45)
            assert rows
            assert all(row["fresh"] == (0 <= row["ageDays"] <= max_age) for row in rows), rows
            if any(row["ageDays"] < 0 for row in rows):
                assert audit[key]["status"] == "fail", audit[key]


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
    test_proloco_documented_partnership()
    test_smartoscana_data_call_resolves_regional_review()
    test_concrete_versilia_scope_excludes_only_reviewed_calls()
    test_reviewed_regional_seeds()
    test_c4t_source_and_verified_seed()
    test_c4t_injection_is_conditional_and_deterministic()
    test_expired_audit_entry_is_archived_without_live_probe()
    test_overlay_reaches_real_v044_run_and_recomputes_counts()
    test_overlay_reaches_real_v044_run_and_recomputes_counts(current_evidence=True)
    test_cerv_regression_contract_is_already_active()
    test_mercati_rionali_cross_source_contract()
    print("Audit gap fixes: C4T + CERV + Mercati rionali + Pro Loco documented partnership + SmarToscana dati PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
