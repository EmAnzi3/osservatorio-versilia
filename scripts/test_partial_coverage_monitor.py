#!/usr/bin/env python3
"""Regressione: una copertura 6/7 può conservare null reali senza stime."""
from __future__ import annotations

import copy

import monthly_data_check_coverage as coverage

TOWNS = [
    {"name": "Camaiore", "code": "046005"},
    {"name": "Forte dei Marmi", "code": "046013"},
    {"name": "Massarosa", "code": "046018"},
    {"name": "Pietrasanta", "code": "046024"},
    {"name": "Seravezza", "code": "046028"},
    {"name": "Stazzema", "code": "046030"},
    {"name": "Viareggio", "code": "046033"},
]


def fixture():
    rows = []
    for town in TOWNS:
        missing = town["name"] == "Stazzema"
        rows.append({
            "town": town["name"],
            "code": town["code"],
            "value": None if missing else 1.8,
            "series": {"years": [2025, 2026], "values": [None, None] if missing else [1.7, 1.8]},
        })
    data = {
        "towns": TOWNS,
        "metrics": {
            "fuel": {
                "meta": {"key": "fuel", "theme": "mobilita", "label": "Carburante", "unit": "currency", "year": "2026", "source": "Fonte"},
                "sourceUrl": "https://example.invalid/fuel.csv",
                "rows": rows,
                "method": {"type": "Dato ufficiale", "formula": "Mediana", "coverage": "6/7"},
            }
        },
    }
    registry = {
        "schemaVersion": 2,
        "expectedMetricCount": 1,
        "expectedInlineMetricCount": 1,
        "expectedExternalMetricCount": 0,
        "expectedTowns": TOWNS,
        "defaults": {"monitorMode": "availability", "unreachableIsBlocker": False},
        "sourceProfiles": {
            "fuel": {
                "publisher": "Fonte",
                "frequency": "daily",
                "frequencyLabel": "Giornaliera",
                "expectedRelease": "Aggiornamento quotidiano",
                "acquisitionMethod": "Open data",
                "licenseName": "Open data",
            }
        },
        "sourceProfileByUrl": {"https://example.invalid/fuel.csv": "fuel"},
        "metricOverrides": {},
        "contentExtensions": [".csv"],
    }
    return data, registry


def main():
    data, registry = fixture()
    findings, _, _ = coverage.validate_dataset(data, registry)
    assert not findings, findings
    # Il validatore deve lavorare su una copia: i null canonici restano null.
    missing = next(row for row in data["metrics"]["fuel"]["rows"] if row["town"] == "Stazzema")
    assert missing["value"] is None
    assert missing["series"]["values"] == [None, None]

    wrong = copy.deepcopy(data)
    missing_wrong = next(row for row in wrong["metrics"]["fuel"]["rows"] if row["town"] == "Stazzema")
    missing_wrong["formatted"] = "0,00"
    findings, _, _ = coverage.validate_dataset(wrong, registry)
    assert any(item["code"] == "missing_value_label" for item in findings)
    print("Partial coverage monitor tests passed.")


if __name__ == "__main__":
    main()
