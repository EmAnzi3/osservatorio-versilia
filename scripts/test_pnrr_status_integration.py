#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from data_status_model import derive_status  # noqa: E402
from monthly_data_check_status import apply_pnrr_verification_result  # noqa: E402

LIMITED_PROBE = {
    "ok": True,
    "directReachable": False,
    "automationLimited": True,
    "status": 403,
    "probeMethod": "automation-limited",
}


def metric_state() -> dict[str, dict[str, object]]:
    return {
        "pnrrFunding": {
            "publishedPeriod": "2026",
            "checkedAt": "2026-08-18T00:00:00+00:00",
            "observedLatestPeriod": "",
            "status": "source_access_limited",
        },
        "pnrrConcluded": {
            "publishedPeriod": "2026",
            "checkedAt": "2026-08-18T00:00:00+00:00",
            "observedLatestPeriod": "",
            "status": "source_access_limited",
        },
    }


def audit_result(funding: str, concluded: str) -> dict[str, object]:
    overall = (
        "match"
        if funding == concluded == "match"
        else "not_comparable"
        if "not_comparable" in {funding, concluded}
        else "different_current_snapshot"
    )
    return {
        "verdict": overall,
        "metricVerdicts": {
            "pnrrFunding": funding,
            "pnrrConcluded": concluded,
        },
        "resource": "https://www301.regione.toscana.it/example.csv",
        "dataset": "https://dati.toscana.it/dataset/regione-toscana-pnrr",
        "dataElaborationDates": ["2026-08-11"],
        "recordsScanned": 45204,
        "selectedProjects": 107,
    }


def test_release_detection_beats_limited_landing() -> None:
    state = metric_state()
    apply_pnrr_verification_result(
        state,
        audit_result("different_current_snapshot", "different_current_snapshot"),
        "2026-08-18T15:00:00+00:00",
    )
    for item in state.values():
        assert item["status"] == "release_detected"
        assert item["observedLatestPeriod"] == ""
        assert isinstance(item.get("verificationEvidence"), dict)
        assert isinstance(item.get("releaseEvidence"), dict)
        assert derive_status("2026", LIMITED_PROBE, item) == "release_detected"


def test_verified_match_can_override_limited_landing() -> None:
    state = metric_state()
    apply_pnrr_verification_result(
        state,
        audit_result("match", "match"),
        "2026-08-18T15:00:00+00:00",
    )
    for item in state.values():
        assert item["status"] == "current"
        assert item["observedLatestPeriod"] == "2026"
        assert isinstance(item.get("verificationEvidence"), dict)
        assert "releaseEvidence" not in item
        assert derive_status("2026", LIMITED_PROBE, item) == "current"


def test_indicators_are_independent() -> None:
    state = metric_state()
    apply_pnrr_verification_result(
        state,
        audit_result("different_current_snapshot", "match"),
        "2026-08-18T15:00:00+00:00",
    )
    assert state["pnrrFunding"]["status"] == "release_detected"
    assert state["pnrrConcluded"]["status"] == "current"
    assert derive_status("2026", LIMITED_PROBE, state["pnrrFunding"]) == "release_detected"
    assert derive_status("2026", LIMITED_PROBE, state["pnrrConcluded"]) == "current"


def test_arbitrary_current_flag_does_not_override_limited_landing() -> None:
    operational = {
        "status": "current",
        "observedLatestPeriod": "2026",
    }
    assert derive_status("2026", LIMITED_PROBE, operational) == "source_access_limited"


def test_not_comparable_is_per_metric() -> None:
    state = metric_state()
    apply_pnrr_verification_result(
        state,
        audit_result("not_comparable", "match"),
        "2026-08-18T15:00:00+00:00",
    )
    assert state["pnrrFunding"]["status"] == "verification_required"
    assert state["pnrrConcluded"]["status"] == "current"
    assert derive_status("2026", LIMITED_PROBE, state["pnrrFunding"]) == "verification_required"
    assert derive_status("2026", LIMITED_PROBE, state["pnrrConcluded"]) == "current"


if __name__ == "__main__":
    test_release_detection_beats_limited_landing()
    test_verified_match_can_override_limited_landing()
    test_indicators_are_independent()
    test_arbitrary_current_flag_does_not_override_limited_landing()
    test_not_comparable_is_per_metric()
    print("OK: integrazione stato PNRR Toscana")
