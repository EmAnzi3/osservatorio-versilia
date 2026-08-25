#!/usr/bin/env python3
from __future__ import annotations

import copy
from datetime import date

import opportunity_regione_toscana_guard as guard

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


def main() -> int:
    test_audience_detection()
    test_accounted_public_is_not_duplicated()
    test_missing_recent_candidate_enters_discovery()
    test_overdue_unresolved_candidate_blocks_publish()
    test_existing_review_becomes_overdue_without_duplicate_discovery()
    print("Regione Toscana guard: 5 test PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
