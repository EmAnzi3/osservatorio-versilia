#!/usr/bin/env python3
"""Fail-closed source gate for the accepted Bilanci v1.39 scope.

The broader audit intentionally records rejected candidates (M17 and PDI 3.1/3.2).
This gate fails only when one of the six approved metrics lacks the required
OpenBDAP evidence. It never mutates canonical data.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import requests

import probe_bilanci_v139_sources as audit

ROOT = Path(__file__).resolve().parents[1]
ACCEPTED_MISSIONS = ("01", "08", "11", "14")


def accepted_mission_failures(failures: list[str]) -> list[str]:
    prefixes = tuple(f"M{code} " for code in ACCEPTED_MISSIONS)
    return [failure for failure in failures if failure.startswith(prefixes)]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="reports/bilanci-v139-source-gate.json")
    args = parser.parse_args()

    session = requests.Session()
    session.headers["User-Agent"] = "OsservatorioVersilia/1.39-source-gate"
    schemes_raw, schemes_url = audit.get_zip(session, audit.SCHEMI_PATH)
    pdi_raw, pdi_url = audit.get_zip(session, audit.PDI_PATH)

    with zipfile.ZipFile(io.BytesIO(schemes_raw)) as archive:
        mission_rows, mission_meta = audit.member(archive, audit.MISSION_MEMBER)
        result_rows, result_meta = audit.member(archive, audit.RESULT_MEMBER)
        missions, mission_failures_all = audit.mission_audit(mission_rows)
        fcde, fcde_failures, fcde_members = audit.fcde_audit(result_rows, archive)

    with zipfile.ZipFile(io.BytesIO(pdi_raw)) as archive:
        pdi_rows, pdi_meta = audit.member(archive, audit.PDI_MEMBER)
        pdi, pdi_failures = audit.pdi_audit(pdi_rows)

    mission_failures = accepted_mission_failures(mission_failures_all)
    hard_failures = mission_failures + fcde_failures

    accepted_missions = {
        town: {code: values[code] for code in ACCEPTED_MISSIONS}
        for town, values in missions.items()
    }
    excluded_m17 = {town: values["17"] for town, values in missions.items()}

    report = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "baseline": "2592a4694c89fc80f30fd643e0efc6acb67e30d5",
        "accepted_scope": [
            "fcdePerResident",
            "yearEndCashFundPerResident",
            "generalAdministrationMissionExpenditurePerResident",
            "territorialPlanningMissionExpenditurePerResident",
            "civilProtectionMissionExpenditurePerResident",
            "economicDevelopmentMissionExpenditurePerResident",
        ],
        "sources": {
            "schemi": {
                "url": schemes_url,
                "sha256": hashlib.sha256(schemes_raw).hexdigest(),
                "bytes": len(schemes_raw),
                "missions_member": mission_meta,
                "result_member": result_meta,
            },
            "pdi_audit_only": {
                "url": pdi_url,
                "sha256": hashlib.sha256(pdi_raw).hexdigest(),
                "bytes": len(pdi_raw),
                "member": pdi_meta,
            },
        },
        "accepted_missions_2025": accepted_missions,
        "fcde_2025": {
            "towns": fcde,
            "reconciliation_candidate_members": fcde_members,
        },
        "excluded_candidates_evidence": {
            "mission_17": excluded_m17,
            "mission_17_failures": [f for f in mission_failures_all if f.startswith("M17 ")],
            "pdi_3_1_3_2": pdi,
            "pdi_failures": pdi_failures,
            "art195": "deferred; no proxy and no 1450/1400 substitution",
        },
        "hard_failures": hard_failures,
        "hard_gate": "PASS" if not hard_failures else "FAIL",
    }

    output = ROOT / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(json.dumps({
        "hard_gate": report["hard_gate"],
        "accepted_mission_failures": mission_failures,
        "fcde_failures": fcde_failures,
        "excluded_m17_gaps": report["excluded_candidates_evidence"]["mission_17_failures"],
        "excluded_pdi_gaps": pdi_failures,
        "output": str(output.relative_to(ROOT)),
    }, ensure_ascii=False, indent=2))

    if hard_failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
