#!/usr/bin/env python3
from __future__ import annotations

from opportunity_run_report import (
    build_report,
    incomplete_run_stages,
    render_html,
    render_markdown,
)


def _item(
    title: str,
    coverage_id: str,
    *,
    deadline: str = "2026-10-01",
    url: str | None = None,
    source: str = "Regione Toscana",
) -> dict:
    return {
        "id": "opp-" + coverage_id,
        "coverage_id": coverage_id,
        "title": title,
        "deadline_at": deadline,
        "url": url or f"https://example.test/{coverage_id}",
        "source_id": "regione-toscana",
        "source_name": source,
        "eligibility": "eligible",
        "access_mode": "direct",
        "municipality_eligibility": {"Massarosa": {"status": "eligible"}},
        "verified_at": "2026-09-13",
        "is_new": False,
    }


def _snapshot(items: list[dict]) -> dict:
    return {
        "referenceDate": "2026-09-14",
        "opportunities": items,
        "archive": [],
        "continuityHold": [],
        "coverageHold": [],
        "continuityReconciliation": {"reconciled": 1, "remaining": 0},
        "coverageAudit": {"status": "pass", "runtimeUncoveredFamilies": []},
        "regionalCompleteness": {"status": "pass", "overdue": []},
        "backtest": {"passed": True, "recall": 0.95},
        "transportAudit": {
            "summary": {
                "configuredSources": 3,
                "configuredEndpoints": 4,
                "fallbackSuccesses": 1,
                "endpointFailures": 1,
                "sourcesInGrace": 0,
                "unhealthySources": 0,
            },
            "sources": [],
        },
    }


def _test_coverage_failure_names_expired_evidence() -> None:
    from opportunity_run_report import _gate_summary
    coverage = {"status": "fail", "residualCoverage": {"staleEvidence": ["eu-cef", "masaf-bandi"]}, "runtimeUnhealthyFamilies": ["education-school-infrastructure"]}
    for current, diagnostic in (
        ({"coverageAudit": coverage}, None),
        ({}, {"coverageAudit": coverage, "gateSummary": {"coverageAuditStatus": "fail"}}),
    ):
        gate = next(x for x in _gate_summary(current, diagnostic) if x["name"] == "Copertura")
        assert gate["status"] == "fail"
        assert all(x in gate["detail"] for x in ("eu-cef", "masaf-bandi", "education-school-infrastructure"))


def main() -> int:
    _test_coverage_failure_names_expired_evidence()
    _test_actionable_document_review()
    prior = _snapshot([])
    candidate = _snapshot([])
    candidate["discoveryQueue"] = [{"title": "Nuovo avviso da verificare", "url": "https://example.test/lead", "source_label": "Fonte istituzionale"}]
    candidate["transportAudit"]["sources"] = [{"sourceId": "mim-enti-locali", "runtimeStatus": "deferred", "effectiveStatus": "error",
        "checkDeferred": True, "lastAttemptedFetch": "2026-10-10", "lastCheckStatus": "error", "nextScheduledCheck": "2026-10-17", "consecutiveFailures": 8}]
    discovery_report = build_report(prior, candidate, phase_statuses={"scan": "success", "validation": "success", "build": "success"})
    assert discovery_report["counts"]["added"] == 0
    assert len(discovery_report["discoveryReview"]["added"]) == 1
    for rendered in (render_markdown(discovery_report), render_html(discovery_report)):
        assert "Nuovo avviso da verificare" in rendered and "2026-10-17" in rendered and "2026-10-10" in rendered
    incomplete = build_report(prior, candidate, phase_statuses={"scan": "failure", "validation": "skipped", "build": "skipped"})
    assert incomplete["discoveryReview"]["added"] == []
    assert incomplete_run_stages({"scan": "success", "validation": "success"}) == {}
    assert incomplete_run_stages({"scan": "failure", "validation": "skipped"}) == {
        "scan": "failure",
        "validation": "skipped",
    }
    unchanged_old = _item("Bando invariato", "same")
    unchanged_new = {**unchanged_old, "verified_at": "2026-09-14", "is_new": True}
    modified_old = _item("Bando modificato", "changed", deadline="2026-10-01")
    modified_new = _item("Bando modificato", "changed", deadline="2026-10-15", url="https://example.test/changed-new")
    archived_old = _item("Bando scaduto", "expired", deadline="2026-09-13")
    removed_old = _item("Bando scomparso", "removed")
    added_new = _item("Bando nuovo", "added")

    previous = _snapshot([unchanged_old, modified_old, archived_old, removed_old])
    current = _snapshot([unchanged_new, modified_new, added_new])
    current["archive"] = [{
        "identity_key": "coverage:expired",
        "id": archived_old["id"],
        "title": archived_old["title"],
        "url": archived_old["url"],
    }]

    report = build_report(
        previous,
        current,
        phase_statuses={"scan": "success", "validation": "success", "build": "success"},
    )
    assert report["overallStatus"] == "pass_with_warnings"
    assert report["counts"] == {
        "previous": 4,
        "current": 3,
        "added": 1,
        "modified": 1,
        "archived": 1,
        "removed": 1,
        "unchanged": 1,
    }, report["counts"]
    assert [row["field"] for row in report["modified"][0]["changes"]] == ["deadline_at", "url"]
    assert report["added"][0]["title"] == "Bando nuovo"
    assert report["archived"][0]["title"] == "Bando scaduto"
    assert report["removed"][0]["title"] == "Bando scomparso"
    assert report["sourceHealth"]["contentSanitized"] == 0

    markdown = render_markdown(report)
    page = render_html(report)
    for token in ("Bando nuovo", "Bando modificato", "Bando scaduto", "Bando scomparso", "Modificate"):
        assert token in markdown, token
        assert token in page, token

    failed = build_report(
        previous,
        previous,
        phase_statuses={"scan": "failure", "validation": "skipped", "build": "skipped"},
        diagnostic={
            "error": "Snapshot non pubblicabile: coverageHold=1",
            "gateSummary": {
                "continuityHoldCount": 0,
                "coverageHoldCount": 1,
                "backtestPassed": True,
                "coverageAuditStatus": "fail",
                "regionalCompletenessStatus": "pass",
                "runtimeUncoveredFamilyCount": 1,
            },
        },
    )
    assert failed["overallStatus"] == "fail"
    assert failed["comparisonAvailable"] is False
    assert failed["counts"]["added"] == 0
    failed_markdown = render_markdown(failed)
    assert "FAIL" in failed_markdown
    assert "coverageHold=1" in failed_markdown
    assert "non è conclusivo" in failed_markdown

    duplicate_titles_old = _snapshot([
        _item("Titolo duplicato", "", url="https://example.test/a"),
        _item("Titolo duplicato", "", url="https://example.test/b"),
    ])
    duplicate_titles_new = _snapshot([
        _item("Titolo duplicato", "", url="https://example.test/c"),
        _item("Titolo duplicato", "", url="https://example.test/d"),
    ])
    ambiguous = build_report(
        duplicate_titles_old,
        duplicate_titles_new,
        phase_statuses={"scan": "success", "validation": "success", "build": "success"},
    )
    assert ambiguous["counts"]["added"] == 2
    assert ambiguous["counts"]["removed"] == 2
    assert ambiguous["counts"]["modified"] == 0

    healthy = _snapshot([])
    healthy["transportAudit"]["summary"]["endpointFailures"] = 0
    phases = {"scan": "success", "validation": "success", "build": "success"}
    assert build_report(healthy, healthy, phase_statuses=phases)["overallStatus"] == "pass"
    healthy["transportAudit"]["sources"] = [{
        "sourceId": "anci-nazionale", "runtimeStatus": "error", "effectiveStatus": "grace",
        "graceUsed": True, "consecutiveFailures": 1, "failureClasses": ["timeout_client"],
        "endpoints": [{"url": "https://example.test/national", "role": "listing",
            "status": "error", "transport": "failed", "httpAttempts": 2,
            "fallbackUsed": True, "proxyUsed": True, "browserFailureClass": "timeout_client",
            "readerFailureClass": "http_403_waf", "errors": ["HTTP timeout", "Chromium timeout", "Reader 403"],
            "resolvedUrl": "https://example.test/redirect", "redirected": True}],
    }]
    diagnostic_report = build_report(healthy, healthy, phase_statuses=phases)
    assert diagnostic_report["overallStatus"] == "pass_with_warnings"
    endpoint = diagnostic_report["sourceHealth"]["attention"][0]["endpoints"][0]
    assert endpoint["role"] == "listing" and endpoint["httpAttempts"] == 2
    for rendered in (render_markdown(diagnostic_report), render_html(diagnostic_report)):
        for token in ("Dettaglio endpoint", "Chromium timeout", "Reader 403", "https://example.test/redirect", "listing"):
            assert token in rendered, token

    print("Rapporto run Radar: PASS")
    return 0


def _test_actionable_document_review():
    import opportunity_pdf_evidence as pdf_evidence
    # SRA31's index contains "Beneficiari" followed by "Imprese in
    # difficoltà". It must not replace the actual applicant section.
    document_text = """Indice
2. Richiedenti/Beneficiari .................................. 7
2.3 Imprese in difficoltà .................................. 10
Disposizioni generali sulle imprese.
2. Richiedenti/Beneficiari
Sono ammessi proprietari, possessori, pubblici o privati e loro associazioni.
Sono ammessi anche enti pubblici titolari della superficie forestale.
"""
    audience = pdf_evidence.document_audience(document_text)
    assert audience.startswith("2. Richiedenti/Beneficiari Sono ammessi")
    assert "Imprese in difficoltà" not in audience
    import opportunity_radar as base_radar
    assert base_radar.eligibility(audience, ["Massarosa"])[0] == "conditional"
    assert not pdf_evidence.document_audience("Beneficiari ........ 7\nImprese ........ 10")
    assert pdf_evidence.document_audience("Beneficiari: imprese private").startswith("Beneficiari:")
    attachment = "https://www301.regione.toscana.it/bancadati/atti/Contenuto.xml?id=5530617&nomeFile=Decreto+n.20302+del+14-09-2026-+Allegato+A+"
    page_html = f'<a href="{attachment.replace("&", "&amp;")}">Avviso pubblico</a>'
    assert pdf_evidence.pdf_links(page_html, "https://www.regione.toscana.it/") == [attachment]
    assert not pdf_evidence.pdf_links(page_html.replace("www301.regione.toscana.it", "example.test"), "https://www.regione.toscana.it/")
    assert not pdf_evidence.pdf_links('<a href="https://www301.regione.toscana.it/bancadati/atti/Contenuto.xml?id=1">Avviso pubblico</a>', "https://www.regione.toscana.it/")
    assert pdf_evidence.pdf_links('<a href="/documents/1/allegato.pdf/uuid?t=1">Allegato A</a>', "https://www.regione.toscana.it/") == ["https://www.regione.toscana.it/documents/1/allegato.pdf/uuid?t=1"]
    from opportunity_review_actions import build_actions, collect_document_links, is_administrative_update
    page = "https://www.anciabruzzo.it/avviso/"
    document = "https://www.anciabruzzo.it/avviso-integrale.pdf"
    current = _snapshot([])
    current["discoveryQueue"] = [
        {"title": "Avviso da verificare", "url": page},
        {"title": "Copia della segnalazione", "url": page+"?utm_source=feed"},
        {"title": "Navigazione principale", "url": "https://www.anciabruzzo.it/"},
        {"title": "Già pubblicata", "url": "https://example.test/public"},
    ]
    current["opportunities"] = [_item("Scheda pubblicata", "public")]
    current["documentPromotion"] = {"checks": [{"url": page, "status": "review", "errors": ["PDF scansionato"],
        "documents": [{"url": document, "status": "review", "error": "PDF scansionato"}]}]}
    actions = build_actions(current)
    assert actions["signalCount"] == 4 and actions["uniqueCount"] == 3 and actions["duplicatesGrouped"] == 1
    assert actions["counts"] == {"human": 1, "covered": 1, "monitor": 1}
    row = actions["items"][0]
    assert row["reasonCode"] == "scanned_pdf" and row["documents"][0]["url"] == document
    report = build_report(current, current, phase_statuses={"scan": "success", "validation": "success", "build": "success"})
    for rendered in (render_markdown(report), render_html(report)):
        assert "Verifiche richieste" in rendered and "Cosa fare" in rendered and document in rendered
        assert "avviso-integrale.pdf" in rendered and "trascrizione controllata" in rendered
    assert report["counts"]["added"] == 0
    import opportunity_daily_refresh_audit_fixed as audit_refresh
    import json
    from pathlib import Path
    from unittest.mock import patch
    from tempfile import TemporaryDirectory
    with TemporaryDirectory() as folder:
        diagnostic_path = Path(folder) / "diagnostic.json"
        with patch.object(audit_refresh.stable, "PUBLISHABILITY_DIAGNOSTIC_PATH", diagnostic_path):
            audit_refresh._write_full_publishability_diagnostic(current, [], error="scan blocked")
        diagnostic = json.loads(diagnostic_path.read_text())
        blocked = build_report(current, current, diagnostic=diagnostic,
                               phase_statuses={"scan": "failure", "validation": "skipped", "build": "skipped"})
        assert blocked["reviewActions"]["counts"] == actions["counts"]
        assert document in render_markdown(blocked), "Il blocco della scansione non deve nascondere i documenti"
        diagnostic["documentPromotion"]["checks"].append({"url": page+"nuovo/", "title": "Avviso verificato non pubblicato", "status": "published_candidate", "coverage_id": "new-verified",
                                                          "documents": [{"url": document+"?new=1", "status": "verified", "deadline": "2026-10-23"}]})
        pending = build_report(current, current, diagnostic=diagnostic,
                               phase_statuses={"scan": "failure", "validation": "skipped", "build": "skipped"})
        pending_rows = [x for x in pending["reviewActions"]["items"] if x["reasonCode"] == "publication_blocked"]
        assert len(pending_rows) == 1 and pending_rows[0]["documents"][0]["url"] == document+"?new=1"
        assert pending_rows[0]["deadline"] == "2026-10-23" and "non va ricercato nuovamente" in render_markdown(pending)
    changed = {**current, "documentPromotion": {"checks": [{"url": page, "status": "deferred", "errors": ["budget exhausted"]}]}}
    changed_report = build_report(current, changed, phase_statuses={"scan": "success", "validation": "success", "build": "success"})
    assert changed_report["fingerprint"] != report["fingerprint"]
    assert changed_report["reviewActions"]["counts"]["retry"] == 1
    failed_lookup = {**current, "documentPromotion": {}, "reviewDocumentLookup": [{"url": page, "status": "error", "errors": ["timeout"]}]}
    failed_actions = build_actions(failed_lookup)
    assert failed_actions["items"][0]["documentLookup"] == "failed"
    from opportunity_review_actions import render_actions_markdown
    assert "Ricerca non riuscita" in render_actions_markdown(failed_actions)
    assert is_administrative_update("<p>È stata approvata la graduatoria definitiva.</p>")
    assert is_administrative_update("<p>Sono state approvate le graduatorie definitive.</p>")
    assert not is_administrative_update("<p>Sono state approvate le graduatorie definitive. Nuova finestra.</p>")
    assert not is_administrative_update("<p>È stata approvata la graduatoria definitiva. Riapertura delle domande.</p>")
    from opportunity_radar_v03 import discovery_candidates
    detail = "https://www.lavoro.gov.it/notizie/pagine/assunzione-assistenti-sociali-riaperti-i-termini-la-manifestazione-di-interesse"
    mlps = {"id": "mlps-social-services", "includeTerms": ["manifestazione"], "municipalTerms": ["Comuni"]}
    fixture = '<nav><a href="/notizie/Pagine/Notizie">Notizie</a></nav><article><a href="' + detail + '"><h3>Comuni: riaperti i termini per la manifestazione di interesse</h3></a></article>'
    leads = discovery_candidates(mlps, fixture, "https://www.lavoro.gov.it/notizie")
    assert len(leads) == 1 and leads[0]["url"] == detail
    fixture = '<div class="item alternative"><a class="search-item-link" href="' + detail + '"></a><div><h2>Assunzione Assistenti sociali: riaperti i termini per la manifestazione di interesse</h2><p>Ambiti territoriali sociali e Comuni</p></div></div>'
    leads = discovery_candidates(mlps, fixture, "https://www.lavoro.gov.it/notizie")
    assert len(leads) == 1 and leads[0]["url"] == detail and leads[0]["title"].startswith("Assunzione")
    news_titles = [
        "17 Comuni fermani candidano progetti per la videosorveglianza",
        "Approvati i progetti di videosorveglianza presentati da 11 Comuni",
        "Approvati in Prefettura 31 progetti di videosorveglianza urbana",
        "Approvati in Prefettura i progetti di videosorveglianza urbana",
        "Approvazione graduatoria per cofinanziamento impianti videosorveglianza",
        "Approvazione progetti di videosorveglianza",
        "Approvazione progetti per potenziamento della videosorveglianza urbana",
        "Assegnazione fondi per videosorveglianza a n.7 Comuni dell'Ascolano",
    ]
    allocations = _snapshot([])
    allocations["referenceDate"] = "2026-10-11"
    allocations["discoveryQueue"] = [{"title": title, "url": f"https://prefettura.interno.gov.it/it/notizie/{i}"} for i, title in enumerate(news_titles)]
    assert build_actions(allocations)["discardedCount"] == 8
    collect_document_links(allocations, loader=lambda u: (_ for _ in ()).throw(AssertionError("notizie, nessun documento da cercare")))
    assert allocations["reviewDocumentLookup"] == []
    for title in news_titles:
        assert is_administrative_update(title, "https://prefettura.interno.gov.it/it/notizie/caso")
        assert not is_administrative_update(title + ". Riapertura delle domande", "https://prefettura.interno.gov.it/it/notizie/caso")
    assert not is_administrative_update("Avviso pubblico per nuovi progetti di videosorveglianza", "https://prefettura.interno.gov.it/it/notizie/caso")
    fresh = _snapshot([]);fresh["referenceDate"] = "2026-10-10"
    fresh["discoveryQueue"] = [{"title": "Avviso A", "url": page}, {"title": "Avviso B", "url": page+"secondo/"}]
    queued = build_actions(fresh)
    assert queued["counts"] == {"retry": 2}
    assert all(x["reasonCode"] == "document_lookup_pending" for x in queued["items"])
    assert "Attendere il tentativo automatico" in render_actions_markdown(queued)
    searched = {**fresh, "reviewDocumentLookup": [{"url": page, "status": "ok", "documents": []}]}
    searched_row = next(x for x in build_actions(searched)["items"] if x["url"] == page)
    assert searched_row["status"] == "technical" and searched_row["documentLookup"] == "not_found"
    located = {**fresh, "reviewDocumentLookup": [{"url": page, "status": "ok", "documents": [{"url": document, "status": "located"}]}]}
    located_row = next(x for x in build_actions(located)["items"] if x["url"] == page)
    assert located_row["status"] == "technical" and located_row["documentLookup"] == "found"
    calls = []
    def loader(url):
        calls.append(url)
        return {"text": '<a href="avviso-integrale.pdf">Avviso</a>', "resolvedUrl": "https://www.anciabruzzo.it/redirect/"}
    collect_document_links(fresh, loader=loader, max_pages=1)
    assert len(calls) == 1
    assert fresh["reviewDocumentLookup"][0]["documents"][0]["url"] == "https://www.anciabruzzo.it/redirect/avviso-integrale.pdf"
    previous = fresh.copy()
    next_run = {**fresh, "reviewDocumentLookup": []}
    collect_document_links(next_run, previous=previous, loader=loader, max_pages=1)
    assert len(calls) == 2 and calls[0] != calls[1], "Il limite non deve affamare sempre le stesse pagine"
    assert len(next_run["reviewDocumentLookup"]) == 2
    assert sum(build_actions(next_run)["counts"].values()) == 2
    carried = {**next_run}
    collect_document_links(carried, previous=next_run, loader=loader, max_pages=1)
    assert len(calls) == 2 and len(carried["reviewDocumentLookup"]) == 2, "Gli allegati persistono senza nuove richieste per sette giorni"
    legacy = {**previous, "reviewDocumentLookup": [{**x, "extractorVersion": 1, "documents": []} for x in previous["reviewDocumentLookup"]]}
    legacy_payload = {**fresh, "discoveryQueue": [fresh["discoveryQueue"][0]]}
    collect_document_links(legacy_payload, previous=legacy, loader=lambda url: page_html, max_pages=1)
    assert legacy_payload["reviewDocumentLookup"][0]["documents"][0]["url"] == attachment, "Un vecchio esito senza PDF non deve restare in cache dopo la correzione del lettore"

    from opportunity_review_actions import reviewed_source, source_text_hash
    entry = audit_refresh._load_fixes()["reviewAssessments"][0]
    probe = "<main>Selezione individuale controllata</main>"
    evidence = {**entry, "sourceTextSha256": source_text_hash(probe)}
    with patch("opportunity_review_actions.json.loads", return_value={"reviewAssessments": [evidence]}):
        assert reviewed_source(probe, entry["url"])["reasonCode"] == "outside_municipal_call"
        assert reviewed_source(probe+"<p>Nuova candidatura comunale</p>", entry["url"]) is None

    # An old reader failure must not prevent reassessment of a located PDF.
    closure = next(x for x in audit_refresh._load_fixes()["reviewAssessments"] if x["status"] == "expired")
    reassessed = _snapshot([])
    reassessed["discoveryQueue"] = [{"url": closure["url"], "title": "Edilizia scolastica"}]
    reassessed["documentPromotion"] = {"checks": [{"url": closure["url"], "status": "review", "errors": ["Articoli ripetuti"], "documents": [{"url": document}]}]}
    with patch("opportunity_review_actions.reviewed_source", return_value=closure):
        collect_document_links(reassessed, loader=lambda u: "<p>Avviso verificato e scaduto</p>")
    assert build_actions(reassessed)["counts"] == {}
    assert build_actions(reassessed)["discardedCount"] == 1
    assert closure["url"] not in render_actions_markdown(build_actions(reassessed))
    from opportunity_review_actions import render_actions_html
    assert closure["url"] not in render_actions_html(build_actions(reassessed))
    # Removed cases still have their evidence refreshed and can reopen.
    previous = {"reviewDocumentLookup": reassessed["reviewDocumentLookup"]}
    previous["reviewDocumentLookup"][0]["checkedAt"] = "2026-09-01"
    with patch("opportunity_review_actions.reviewed_source", return_value=None):
        collect_document_links(reassessed, previous=previous, loader=lambda u: f'<a href="{document}">Nuovo avviso</a>')
    assert build_actions(reassessed)["counts"] == {"technical": 1}
    technical = {**current, "documentPromotion": {"checks": [{"url": page, "errors": ["Struttura non supportata"], "documents": [{"url": document}]}]}}
    assert build_actions(technical)["counts"].get("technical") == 1
    assert "Interventi sul Radar: 1" in render_actions_markdown(build_actions(technical))


if __name__ == "__main__":
    raise SystemExit(main())
