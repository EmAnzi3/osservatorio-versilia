#!/usr/bin/env python3
"""Test di regressione del controllo mensile."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import monthly_data_check_coverage as coverage
import monthly_data_check_status as status_model

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
        "expectedInlineMetricCount": 1,
        "expectedExternalMetricCount": 0,
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
    mef_old = (
        "https://www1.finanze.gov.it/finanze/analisi_stat/public/index.php"
        "?tree=2013&t=111"
    )
    mef_new = (
        "https://www1.finanze.gov.it/finanze/analisi_stat/public/index.php"
        "?tree=2013&t=222"
    )
    mef_stable = (
        "https://www1.finanze.gov.it/finanze/analisi_stat/public/index.php"
        "?tree=2013"
    )
    assert coverage.canonical_url(mef_old) == mef_stable
    assert coverage.canonical_url(mef_new) == mef_stable
    assert coverage.canonical_url("https://example.org/data?t=222").endswith("?t=222")

    redirect_changes = coverage.compare_states(
        {
            "sources": {
                "https://www1.finanze.gov.it/finanze/analisi_stat/public/index.php": {
                    "ok": True,
                    "finalUrl": mef_old,
                }
            }
        },
        {
            "https://www1.finanze.gov.it/finanze/analisi_stat/public/index.php": {
                "ok": True,
                "finalUrl": mef_new,
            }
        },
    )
    assert not redirect_changes["redirect"]

    # L'ingresso di una URL nella nuova baseline del monitor non è un'anomalia
    # del dato. Solo contenuto o redirect cambiati di una fonte già monitorata
    # richiedono una verifica umana.
    new_source = "https://example.org/new-source"
    changed_source = "https://example.org/changed-source"
    status_changes = status_model.changed_urls(
        {
            "changes": {
                "added": [{"url": new_source}],
                "removed": [{"url": "https://example.org/old-source"}],
                "content": [{"url": changed_source}],
                "redirect": [],
            }
        }
    )
    assert coverage.canonical_url(new_source) not in status_changes
    assert coverage.canonical_url(changed_source) in status_changes

    with tempfile.TemporaryDirectory() as directory:
        work = Path(directory)
        first = run_checker(
            work / "first",
            {"schemaVersion": 1, "checkedAt": None, "sources": {}},
        )
        assert first["status"] == "baseline_required"
        assert first["summary"]["metricCount"] == 1
        assert first["summary"]["inlineMetricCount"] == 1
        assert first["summary"]["externalMetricCount"] == 0
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
