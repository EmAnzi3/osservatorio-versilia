#!/usr/bin/env python3
"""Contratti KPI indipendenti: niente percentuali premature o lag inventati."""
from __future__ import annotations

from unittest.mock import patch

import run_opportunity_radar_v042 as radar


def _case(n: int) -> dict:
    return {
        "id": f"prospective-{n}",
        "coverage_id": f"independent-{n}",
        "expected": "prospective_current",
        "official_published_at": "2026-10-01",
        "radar_detected_at": "2026-10-03",
        "radar_qualified_at": "2026-10-05",
        "radar_published_at": "2026-10-06",
    }


def _audit(cases: list[dict], captured: int) -> dict:
    config = {
        "baselineDate": "2026-10-28",
        "baselineIsRepresentative": False,
        "minimumProspectiveSample": 20,
        "cases": cases,
    }
    payload = {
        "opportunities": [
            {"coverage_id": case["coverage_id"]}
            for case in cases[:captured]
        ],
        "archive": [],
    }
    with patch.object(radar.core, "_load", return_value=config), patch.object(
        radar, "_probe_holdouts", return_value=[]
    ):
        return radar.build_independent_audit(payload, live=False)


def test_threshold_and_distinct_phases() -> None:
    small = _audit([_case(i) for i in range(19)], captured=19)["prospective"]
    assert small["sampleSize"] == 19
    assert small["status"] == "pending_minimum_sample"
    assert small["captureRate"] is None
    assert all(p["median"] is None for p in small["timingLagDays"].values())

    complete = _audit([_case(i) for i in range(20)], captured=19)["prospective"]
    assert complete["status"] == "measurable"
    assert complete["sampleSize"] == 20
    assert complete["captured"] == 19
    assert abs(complete["captureRate"] - .95) < 1e-9
    stages = complete["timingLagDays"]
    assert stages["detection"]["median"] == 2
    assert stages["qualification"]["median"] == 2
    assert stages["publication"]["median"] == 1
    assert stages["detection"]["from"] == "official_published_at"
    assert stages["qualification"]["from"] == "radar_detected_at"
    assert stages["publication"]["from"] == "radar_qualified_at"

    missing = [_case(i) for i in range(20)]
    for case in missing[1:]:
        case.pop("radar_qualified_at")
    incomplete = _audit(missing, captured=20)["prospective"]
    assert incomplete["captureRate"] == 1.0
    assert incomplete["timingLagDays"]["detection"]["median"] == 2
    assert incomplete["timingLagDays"]["qualification"]["median"] is None
    assert incomplete["timingLagDays"]["publication"]["median"] is None



def test_iso_timestamps_and_offset_normalization() -> None:
    cases = [_case(i) for i in range(20)]
    for case in cases:
        case.update({
            "official_published_at": "2026-10-01T10:00:00+02:00",
            "radar_detected_at": "2026-10-01T09:30:00Z",
            "radar_qualified_at": "2026-10-01T12:00:00+02:00",
            "radar_published_at": "2026-10-01T10:45:00+00:00",
        })
    report = _audit(cases, captured=20)["prospective"]
    lag = report["timingLagDays"]
    assert all(row["sampleSize"] == 20 for row in lag.values())
    assert abs(lag["detection"]["median"] - 90 / 1440) < 1e-10
    assert abs(lag["qualification"]["median"] - 30 / 1440) < 1e-10
    assert abs(lag["publication"]["median"] - 45 / 1440) < 1e-10

    # Un evento temporalmente impossibile non conta nel relativo campione.
    cases[0]["radar_qualified_at"] = "2026-10-01T08:00:00Z"
    report = _audit(cases, captured=20)["prospective"]
    assert report["timingLagDays"]["qualification"]["sampleSize"] == 19
    assert report["timingLagDays"]["qualification"]["median"] is None
    assert report["timingLagDays"]["detection"]["sampleSize"] == 20


def test_retro_audit_date_is_not_detection() -> None:
    case = {
        "id": "old",
        "coverage_id": "legacy-2026",
        "expected": "current",
        "published_at": "2026-01-01",
        "audit_found_at": "2026-02-01",
        "baselineRadarStatus": "missed",
    }
    result = _audit([case], captured=1)
    assert result["targetedDetectionLagDays"]["median"] is None
    assert result["targetedDetectionLagDays"]["sampleSize"] == 0
    assert result["targetedAuditIdentificationDelayDays"]["median"] == 31


def main() -> int:
    test_threshold_and_distinct_phases()
    test_retro_audit_date_is_not_detection()
    test_iso_timestamps_and_offset_normalization()
    print("KPI indipendenti: soglia >=20 e tre lag separati PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
