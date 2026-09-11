#!/usr/bin/env python3
from __future__ import annotations

import copy
from datetime import date

import opportunity_regione_toscana_guard as guard
import test_opportunity_audit_gap_fixes as audit_fixes

TODAY = date(2026, 8, 25)


def _candidate(age_days: int = 2) -> dict:
    published = date.fromordinal(TODAY.toordinal() - age_days)
    return {
        "title": "Avviso comunale di prova",
        "url": "https://www.regione.toscana.it/it/-/avviso-comunale-di-prova",
        "summary": "Stato: Aperto",
        "published_at": published.isoformat(),
        "age_days": age_days,
        "deadline_at": "2026-09-30",
    }


def test_audience_detection() -> None:
    assert guard._has_explicit_municipal_audience(
        "Beneficiari. Possono presentare domanda gli Enti locali della Toscana e gli Enti del Terzo settore."
    )
    assert not guard._has_explicit_municipal_audience(
        "Beneficiari. Possono presentare domanda le micro e piccole imprese della Toscana."
    )


def test_accounted_public_is_not_duplicated() -> None:
    candidate = _candidate()
    result = {
        "opportunities": [{"title": candidate["title"], "url": candidate["url"]}],
        "discoveryQueue": [],
        "coverageHold": [],
        "counts": {},
    }
    guard.apply(result, TODAY, candidates=[candidate])
    assert result["regionalCompleteness"]["status"] == "pass"
    assert result["regionalCompleteness"]["safetyNetAdded"] == 0
    assert result["discoveryQueue"] == []


def test_cross_source_market_identity_is_reconciled() -> None:
    candidate = {
        "title": "Mercati rionali: contributi ai Comuni per ammodernamento, ampliamento e riqualificazione",
        "url": "https://www.regione.toscana.it/it/-/mercati-rionali-contributi-ai-comuni-per-ammodernamento-ampliamento-e-riqualificazione",
        "summary": "Comuni della Regione Toscana",
        "published_at": "2026-08-23",
        "age_days": 2,
        "deadline_at": "2026-09-15",
    }
    result = {
        "opportunities": [
            {
                "title": "Avviso Mercati Rionali",
                "url": "https://www.sviluppo.toscana.it/bando/avviso-mercati-rionali/",
                "deadline_at": "2026-09-15",
                "rule_id": "st-mercati-rionali-2026",
            }
        ],
        "reviewQueue": [
            {
                "title": candidate["title"],
                "url": candidate["url"],
                "deadline_at": candidate["deadline_at"],
            }
        ],
        "discoveryQueue": [],
        "coverageHold": [],
        "counts": {},
    }
    guard.apply(result, TODAY, candidates=[copy.deepcopy(candidate)])
    assert result["regionalCompleteness"]["status"] == "pass"
    assert result["regionalCompleteness"]["safetyNetAdded"] == 0
    assert result["regionalCompleteness"]["unresolved"] == []
    assert result["counts"]["regionalUnresolved"] == 0


def test_missing_recent_candidate_enters_discovery() -> None:
    result = {"opportunities": [], "discoveryQueue": [], "coverageHold": [], "counts": {}}
    guard.apply(result, TODAY, candidates=[_candidate(age_days=2)])
    assert result["regionalCompleteness"]["status"] == "pass"
    assert result["regionalCompleteness"]["safetyNetAdded"] == 1
    assert len(result["discoveryQueue"]) == 1
    assert result["coverageHold"] == []


def test_overdue_unresolved_candidate_blocks_publish() -> None:
    result = {"opportunities": [], "discoveryQueue": [], "coverageHold": [], "counts": {}}
    guard.apply(result, TODAY, candidates=[_candidate(age_days=guard.REVIEW_GRACE_DAYS + 1)])
    assert result["regionalCompleteness"]["status"] == "fail"
    assert len(result["coverageHold"]) == 1
    assert result["coverageHold"][0]["source_id"] == "regione-toscana"


def test_existing_review_becomes_overdue_without_duplicate_discovery() -> None:
    candidate = _candidate(age_days=guard.REVIEW_GRACE_DAYS + 2)
    result = {
        "opportunities": [],
        "reviewQueue": [{"title": candidate["title"], "url": candidate["url"]}],
        "discoveryQueue": [],
        "coverageHold": [],
        "counts": {},
    }
    guard.apply(result, TODAY, candidates=[copy.deepcopy(candidate)])
    assert result["regionalCompleteness"]["status"] == "fail"
    assert result["regionalCompleteness"]["safetyNetAdded"] == 0
    assert result["regionalCompleteness"]["unresolved"][0]["account_state"] == "review"
    assert len(result["coverageHold"]) == 1


def test_final_reconciliation_removes_stale_regional_hold() -> None:
    """Replay of runs 42-44: detail recovery must invalidate the old hold."""
    candidate = {
        "title": "Mercati rionali: contributi ai Comuni",
        "url": "https://www.regione.toscana.it/it/-/mercati-rionali-contributi-ai-comuni-per-ammodernamento-ampliamento-e-riqualificazione",
        "summary": "Comuni della Regione Toscana",
        "published_at": "2026-09-02",
        "age_days": guard.REVIEW_GRACE_DAYS + 2,
        "deadline_at": "2026-09-15",
    }
    external_hold = {"coverage_id": "other-quality-gate", "reason": "must survive"}
    result = {
        "opportunities": [],
        "reviewQueue": [copy.deepcopy(candidate)],
        "discoveryQueue": [],
        "coverageHold": [external_hold],
        "counts": {},
    }
    guard.apply(result, date(2026, 9, 11), candidates=[copy.deepcopy(candidate)])
    assert result["regionalCompleteness"]["status"] == "fail"
    assert len(result["coverageHold"]) == 2

    result["opportunities"].append({
        "title": "Avviso Mercati Rionali",
        "url": "https://www.sviluppo.toscana.it/bando/avviso-mercati-rionali/",
        "deadline_at": "2026-09-15",
        "rule_id": "st-mercati-rionali-2026",
        "verification_status": "live_detail_revalidated",
    })
    guard.apply(result, date(2026, 9, 11), candidates=[copy.deepcopy(candidate)])

    assert result["regionalCompleteness"]["status"] == "pass", result
    assert result["regionalCompleteness"]["unresolved"] == []
    assert result["regionalCompleteness"]["overdue"] == []
    assert result["coverageHold"] == [external_hold]


def main() -> int:
    test_audience_detection()
    test_accounted_public_is_not_duplicated()
    test_cross_source_market_identity_is_reconciled()
    test_missing_recent_candidate_enters_discovery()
    test_overdue_unresolved_candidate_blocks_publish()
    test_existing_review_becomes_overdue_without_duplicate_discovery()
    test_final_reconciliation_removes_stale_regional_hold()
    assert audit_fixes.main() == 0
    print("Regione Toscana guard: 7 test PASS + audit gap contracts PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
