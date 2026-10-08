#!/usr/bin/env python3
"""Regression matrix for the single final publishability decision."""
from __future__ import annotations

import copy
from datetime import date

import opportunity_daily_refresh as daily
import opportunity_regione_toscana_guard as regional


def _base() -> dict:
    return {
        "opportunities": [{"id": "verified"}],
        "continuityHold": [],
        "coverageHold": [],
        "backtest": {"passed": True},
        "coverageAudit": {
            "status": "pass",
            "runtimeUncoveredFamilies": [],
        },
        "regionalCompleteness": {"status": "pass"},
    }


def test_clean_run() -> None:
    assert daily._publishability_problems(_base()) == []


def test_simultaneous_continuity_coverage_and_regional_failure() -> None:
    result = _base()
    result["continuityHold"] = [{"identity_key": "rule:missing"}]
    result["coverageHold"] = [{"coverage_id": "missing-coverage"}]
    result["regionalCompleteness"] = {"status": "fail"}
    assert daily._publishability_problems(result) == [
        "continuityHold=1",
        "coverageHold=1",
        "regionalCompleteness=fail",
    ]


def test_backtest_and_runtime_coverage_are_not_hidden() -> None:
    result = _base()
    result["backtest"] = {"passed": False}
    result["coverageAudit"] = {
        "status": "fail",
        "runtimeUncoveredFamilies": ["maritime-coastal"],
    }
    assert daily._publishability_problems(result) == [
        "backtest=fail",
        "coverageAudit=fail",
    ]


def test_empty_output_is_an_independent_blocker() -> None:
    result = _base()
    result["opportunities"] = []
    assert daily._publishability_problems(result) == ["opportunities=0"]


def test_recent_date_replay_reconciles_before_final_decision() -> None:
    """Replay 09/09, 10/09 and 11/09 instead of one hard-coded green day."""
    canonical = {
        "title": "Avviso Mercati Rionali",
        "url": "https://www.sviluppo.toscana.it/bando/avviso-mercati-rionali/",
        "deadline_at": "2026-09-15",
        "rule_id": "st-mercati-rionali-2026",
        "verified_direct": True,
    }
    for run_day in (date(2026, 9, 9), date(2026, 9, 10), date(2026, 9, 11)):
        published = date(2026, 9, 2)
        candidate = {
            "title": "Mercati rionali: contributi ai Comuni",
            "url": "https://www.regione.toscana.it/it/-/mercati-rionali-contributi-ai-comuni-per-ammodernamento-ampliamento-e-riqualificazione",
            "summary": "Comuni della Regione Toscana",
            "published_at": published.isoformat(),
            "age_days": (run_day - published).days,
            "deadline_at": "2026-09-15",
        }
        result = _base()
        result["opportunities"] = [copy.deepcopy(canonical)]
        result["reviewQueue"] = [copy.deepcopy(candidate)]
        result["discoveryQueue"] = []
        result["counts"] = {}
        regional.apply(result, run_day, candidates=[copy.deepcopy(candidate)])
        assert result["regionalCompleteness"]["status"] == "pass", (run_day, result)
        assert result["coverageHold"] == [], (run_day, result)
        assert daily._publishability_problems(result) == [], (run_day, result)



def test_scan_budget_exhaustion_blocks_publication() -> None:
    from types import SimpleNamespace
    import opportunity_daily_refresh_resilient as resilient

    previous_budget = resilient.discovery.LIVE_BUDGET
    previous_runtime = resilient._runtime_uncovered_families
    previous_assert = resilient._ORIGINAL_ASSERT
    try:
        resilient.discovery.LIVE_BUDGET = SimpleNamespace(scan_exhausted=True)
        resilient._runtime_uncovered_families = lambda result: []
        resilient._ORIGINAL_ASSERT = daily._assert_publishable
        result = _base()
        try:
            resilient._assert_publishable_hardened(result)
        except RuntimeError as exc:
            assert "coverageAudit=fail" in str(exc)
        else:
            raise AssertionError("Incomplete scan must not publish even with recent source health")
        assert result["coverageAudit"]["transportBudget"]["status"] == "fail"
    finally:
        resilient.discovery.LIVE_BUDGET = previous_budget
        resilient._runtime_uncovered_families = previous_runtime
        resilient._ORIGINAL_ASSERT = previous_assert


def main() -> int:
    test_scan_budget_exhaustion_blocks_publication()
    test_clean_run()
    test_simultaneous_continuity_coverage_and_regional_failure()
    test_backtest_and_runtime_coverage_are_not_hidden()
    test_empty_output_is_an_independent_blocker()
    test_recent_date_replay_reconciles_before_final_decision()
    print("Publishability finale Radar: 6 scenari + replay 09/09-11/09 PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
