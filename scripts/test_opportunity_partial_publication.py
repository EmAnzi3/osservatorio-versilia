#!/usr/bin/env python3
"""Pubblicazione parziale del Radar: un gate di completezza non trattiene le schede nuove già verificate."""
from __future__ import annotations

import copy
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import opportunity_daily_refresh as daily
import opportunity_runtime_snapshot as runtime
from opportunity_run_report import build_report

TODAY = date(2026, 11, 22)


def _card(cid: str, **extra) -> dict:
    return {"coverage_id": cid, "id": cid, "title": f"Scheda {cid}", "url": f"https://example.org/{cid}", **extra}


def _result(**extra) -> dict:
    base = {
        "opportunities": [_card("shared", summary="nuova verifica"), _card("fresh")],
        "archive": [_card("expired-today")],
        "backtest": {"passed": True},
        "coverageAudit": {"status": "fail"},
        "regionalCompleteness": {"status": "pass"},
        "continuityHold": [],
        "coverageHold": [],
    }
    base.update(extra)
    return base


PREVIOUS = {"opportunities": [_card("shared", summary="vecchia"), _card("kept"), _card("expired-today")]}


def test_coverage_block_publishes_previous_plus_new() -> None:
    result = _result()
    assert daily._apply_partial_publication(result, copy.deepcopy(PREVIOUS), TODAY)
    ids = [x["coverage_id"] for x in result["opportunities"]]
    assert ids == ["shared", "fresh", "kept"], ids
    # La versione del run vince su quella precedente; ciò che il run ha archiviato non torna.
    assert result["opportunities"][0]["summary"] == "nuova verifica"
    assert result["opportunities"][2]["partial_carryover"] is True
    partial = result["partialPublication"]
    assert partial["status"] == "partial" and partial["date"] == "2026-11-22"
    assert partial["blockedBy"] == ["coverageAudit=fail"] and partial["carriedOver"] == 1


def test_every_completeness_gate_allows_partial() -> None:
    for extra in ({"continuityHold": [{"title": "x"}]}, {"coverageHold": [{"title": "x"}]},
                  {"regionalCompleteness": {"status": "fail"}}):
        result = _result(coverageAudit={"status": "pass"}, **extra)
        assert daily._apply_partial_publication(result, copy.deepcopy(PREVIOUS), TODAY), extra


def test_backtest_or_empty_previous_blocks_everything() -> None:
    assert not daily._apply_partial_publication(_result(backtest={"passed": False}), copy.deepcopy(PREVIOUS), TODAY)
    assert not daily._apply_partial_publication(_result(), {"opportunities": []}, TODAY)
    clean = _result(coverageAudit={"status": "pass"})
    assert not daily._apply_partial_publication(clean, copy.deepcopy(PREVIOUS), TODAY)
    assert "partialPublication" not in clean


def _snapshot(**extra) -> dict:
    payload = {
        "releaseVersion": "0.4.4", "dailyHardeningVersion": "0.4.4-h5", "referenceDate": "2026-11-22",
        "opportunities": [_card("a")], "backtest": {"passed": True}, "coverageAudit": {"status": "fail"},
        "regionalCompleteness": {"status": "pass"},
    }
    payload.update(extra)
    return payload


def test_runtime_seed_accepts_only_declared_partial() -> None:
    assert runtime.validation_errors(_snapshot(), TODAY) == ["coverageAudit"]
    declared = {"status": "partial", "date": "2026-11-22", "blockedBy": ["coverageAudit=fail"]}
    assert runtime.validation_errors(_snapshot(partialPublication=declared), TODAY) == []
    assert runtime.validation_errors(_snapshot(partialPublication=declared, backtest={"passed": False}), TODAY) == ["backtest"]
    wrong = dict(declared, blockedBy=["backtest=fail"])
    assert "partialPublication" in runtime.validation_errors(_snapshot(partialPublication=wrong), TODAY)


def test_run_report_marks_partial_not_pass() -> None:
    phases = {"scan": "success", "validation": "success", "build": "success", "comparison": "success"}
    previous = _snapshot(coverageAudit={"status": "pass"})
    current = _snapshot(partialPublication={"status": "partial", "blockedBy": ["coverageAudit=fail"], "carriedOver": 1})
    report = build_report(previous, current, phase_statuses=phases)
    assert report["overallStatus"] == "partial", report["overallStatus"]
    assert report["partialPublication"]["carriedOver"] == 1
    failed = build_report(previous, current, phase_statuses=dict(phases, build="failure"))
    assert failed["overallStatus"] == "fail"


def main() -> int:
    test_coverage_block_publishes_previous_plus_new()
    test_every_completeness_gate_allows_partial()
    test_backtest_or_empty_previous_blocks_everything()
    test_runtime_seed_accepts_only_declared_partial()
    test_run_report_marks_partial_not_pass()
    print("Pubblicazione parziale Radar: 5 test PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
