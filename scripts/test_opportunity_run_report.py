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


if __name__ == "__main__":
    raise SystemExit(main())
