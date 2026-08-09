#!/usr/bin/env python3
"""Test di regressione del controllo mensile."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "scripts" / "monthly_data_check.py"
TOWNS = [
    {"name": "Camaiore", "code": "046005"},
    {"name": "Forte dei Marmi", "code": "046013"},
    {"name": "Massarosa", "code": "046018"},
    {"name": "Pietrasanta", "code": "046024"},
    {"name": "Seravezza", "code": "046028"},
    {"name": "Stazzema", "code": "046030"},
    {"name": "Viareggio", "code": "046033"},
]


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def run_checker(work: Path, state: dict) -> dict:
    data = {
        "towns": TOWNS,
        "metrics": {
            "population": {
                "meta": {
                    "key": "population",
                    "theme": "demografia",
                    "label": "Popolazione residente",
                    "unit": "number",
                    "year": "2026",
                    "source": "Istat",
                },
                "sourceUrl": "https://example.invalid/population.csv",
                "rows": [
                    {
                        "town": town["name"],
                        "code": town["code"],
                        "value": 100,
                        "series": {"years": [2025, 2026], "values": [99, 100]},
                    }
                    for town in TOWNS
                ],
                "method": {
                    "type": "Dato ufficiale",
                    "formula": "Valore pubblicato dalla fonte.",
                    "coverage": "7/7",
                },
            }
        },
    }
    registry = {
        "schemaVersion": 2,
        "expectedMetricCount": 1,
        "expectedTowns": TOWNS,
        "defaults": {
            "monitorMode": "availability",
            "unreachableIsBlocker": False,
        },
        "sourceProfiles": {
            "test-annual": {
                "publisher": "Fonte di test",
                "frequency": "annual",
                "frequencyLabel": "Annuale",
                "expectedRelease": "Ogni anno",
                "acquisitionMethod": "Dataset di test",
                "licenseName": "Licenza di test",
                "licenseUrl": "https://example.invalid/license",
            }
        },
        "sourceProfileByUrl": {
            "https://example.invalid/population.csv": "test-annual",
        },
        "metricOverrides": {},
        "contentExtensions": [".csv"],
        "requestTimeoutSeconds": 2,
        "maxDownloadBytes": 1024,
    }
    data_path = work / "data.json"
    registry_path = work / "registry.json"
    state_path = work / "state.json"
    report_md = work / "report.md"
    report_json = work / "report.json"
    next_state = work / "next-state.json"
    write_json(data_path, data)
    write_json(registry_path, registry)
    write_json(state_path, state)

    subprocess.run(
        [
            sys.executable,
            str(CHECKER),
            "--mode",
            "offline",
            "--data",
            str(data_path),
            "--registry",
            str(registry_path),
            "--state",
            str(state_path),
            "--report-md",
            str(report_md),
            "--report-json",
            str(report_json),
            "--next-state",
            str(next_state),
        ],
        cwd=ROOT,
        check=True,
    )
    return json.loads(report_json.read_text(encoding="utf-8"))


def main() -> None:
    with tempfile.TemporaryDirectory() as directory:
        work = Path(directory)
        first = run_checker(
            work / "first",
            {"schemaVersion": 1, "checkedAt": None, "sources": {}},
        )
        assert first["status"] == "baseline_required"
        assert first["summary"]["metricCount"] == 1
        assert first["summary"]["townCount"] == 7
        assert not first["findings"]

        baseline = {
            "schemaVersion": 1,
            "checkedAt": "2026-08-01T00:00:00+00:00",
            "mode": "offline",
            "sources": first["sources"],
        }
        second = run_checker(work / "second", baseline)
        assert second["status"] == "no_changes"
        assert not second["changes"]["content"]
        assert not second["changes"]["removed"]

        changed = dict(baseline)
        sources = dict(baseline["sources"])
        sources["https://example.invalid/removed.csv"] = {
            "url": "https://example.invalid/removed.csv",
            "ok": True,
            "status": 200,
            "finalUrl": "https://example.invalid/removed.csv",
        }
        changed["sources"] = sources
        third = run_checker(work / "third", changed)
        assert third["status"] == "changes_detected"
        assert third["changes"]["removed"]

    print("Monthly data monitor tests passed.")


if __name__ == "__main__":
    main()
