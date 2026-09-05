#!/usr/bin/env python3
from __future__ import annotations

from datetime import date

import opportunity_daily_refresh_stable as stable


def _test_recent_success_gives_family_grace() -> None:
    original_load = stable.h4.core._load
    original_previous = stable._PREVIOUS_HEALTH
    original_date = stable._RUN_DATE
    try:
        stable.h4.core._load = lambda _path: {
            "requiredFamilies": [{"id": "maritime-coastal", "sourceIds": ["pcm-mare"]}]
        }
        stable._PREVIOUS_HEALTH = {
            "pcm-mare": {
                "lastSuccessfulFetch": "2026-09-04",
                "consecutiveFailures": 0,
                "effectiveStatus": "ok",
            }
        }
        stable._RUN_DATE = date(2026, 9, 5)
        result = {
            "sourceCoverage": {"rows": [{"source_id": "pcm-mare", "runtimeStatus": "error"}]},
            "coverageAudit": {},
        }
        uncovered = stable._runtime_uncovered_families_stable(result)
    finally:
        stable.h4.core._load = original_load
        stable._PREVIOUS_HEALTH = original_previous
        stable._RUN_DATE = original_date

    assert uncovered == [], uncovered
    grace = result["coverageAudit"]["runtimeGraceFamilies"]
    assert grace and grace[0]["familyId"] == "maritime-coastal", grace
    assert grace[0]["sources"][0]["graceReason"] == "recent_success", grace


def _test_legacy_error_gets_bootstrap_failure_window() -> None:
    original_previous = stable._PREVIOUS_HEALTH
    try:
        snapshot = {
            "referenceDate": "2026-09-04",
            "sourceCoverage": {
                "rows": [{"source_id": "legacy-error", "runtimeStatus": "error"}]
            },
        }
        stable._PREVIOUS_HEALTH = stable._seed_previous_health(snapshot)
        state = stable._health_state("legacy-error", "error", date(2026, 9, 5))
    finally:
        stable._PREVIOUS_HEALTH = original_previous

    assert state["lastSuccessfulFetch"] is None, state
    assert state["consecutiveFailures"] == 2, state
    assert state["effectiveStatus"] == "grace", state
    assert state["graceReason"] == "consecutive_failure_window", state


def _test_expired_grace_blocks_family() -> None:
    original_load = stable.h4.core._load
    original_previous = stable._PREVIOUS_HEALTH
    original_date = stable._RUN_DATE
    try:
        stable.h4.core._load = lambda _path: {
            "requiredFamilies": [{"id": "maritime-coastal", "sourceIds": ["pcm-mare"]}]
        }
        stable._PREVIOUS_HEALTH = {
            "pcm-mare": {
                "lastSuccessfulFetch": "2026-09-02",
                "consecutiveFailures": 2,
                "effectiveStatus": "grace",
            }
        }
        stable._RUN_DATE = date(2026, 9, 5)
        result = {
            "sourceCoverage": {"rows": [{"source_id": "pcm-mare", "runtimeStatus": "error"}]},
            "coverageAudit": {},
        }
        uncovered = stable._runtime_uncovered_families_stable(result)
    finally:
        stable.h4.core._load = original_load
        stable._PREVIOUS_HEALTH = original_previous
        stable._RUN_DATE = original_date

    assert uncovered == ["maritime-coastal"], uncovered
    assert result["coverageAudit"]["runtimeGraceFamilies"] == []


def _test_success_resets_failure_counter() -> None:
    original_previous = stable._PREVIOUS_HEALTH
    try:
        stable._PREVIOUS_HEALTH = {
            "source": {
                "lastSuccessfulFetch": "2026-09-01",
                "consecutiveFailures": 4,
                "effectiveStatus": "error",
            }
        }
        state = stable._health_state("source", "ok", date(2026, 9, 5))
    finally:
        stable._PREVIOUS_HEALTH = original_previous

    assert state["lastSuccessfulFetch"] == "2026-09-05", state
    assert state["consecutiveFailures"] == 0, state
    assert state["effectiveStatus"] == "ok", state
    assert state["graceUsed"] is False


def _test_pre_h5_snapshot_seeds_health() -> None:
    snapshot = {
        "referenceDate": "2026-09-04",
        "sourceCoverage": {
            "rows": [
                {"source_id": "healthy", "runtimeStatus": "ok"},
                {"source_id": "broken", "runtimeStatus": "error"},
            ]
        },
    }
    seeded = stable._seed_previous_health(snapshot)
    assert seeded["healthy"]["lastSuccessfulFetch"] == "2026-09-04", seeded
    assert seeded["healthy"]["consecutiveFailures"] == 0, seeded
    assert seeded["broken"]["lastSuccessfulFetch"] is None, seeded
    assert seeded["broken"]["consecutiveFailures"] == 1, seeded


def main() -> int:
    _test_recent_success_gives_family_grace()
    _test_legacy_error_gets_bootstrap_failure_window()
    _test_expired_grace_blocks_family()
    _test_success_resets_failure_counter()
    _test_pre_h5_snapshot_seeds_health()
    print("Salute persistente fonti Radar: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
