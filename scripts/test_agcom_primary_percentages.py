#!/usr/bin/env python3
from __future__ import annotations

import math
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import apply_agcom_primary_percentages as module  # noqa: E402

TOWNS = [
    ("Massarosa", "046018", 9000, 47.0, 34.0),
    ("Viareggio", "046033", 25000, 94.8, 86.0),
    ("Camaiore", "046005", 13000, 91.3, 80.1),
    ("Pietrasanta", "046024", 9300, 59.3, 44.2),
    ("Seravezza", "046028", 5000, 0.7, 0.1),
    ("Forte dei Marmi", "046013", 2700, 0.0, 0.0),
    ("Stazzema", "046030", 1100, 87.9, 77.4),
]


def data_fixture():
    def metric(key):
        return {
            "meta": {"key": key, "source": "old", "year": "old"},
            "sourceUrl": "old",
            "rows": [
                {"town": name, "code": code, "slug": name.lower().replace(" ", "-"), "value": 1.0, "formatted": "1,0%", "benchmarkValue": 1.0}
                for name, code, *_ in TOWNS
            ],
            "aggregate": {"value": 1.0, "label": "old", "note": "old"},
            "method": {},
        }
    return {"metrics": {"ftthCoverageDesi": metric("ftthCoverageDesi"), "ftthCoverage20m": metric("ftthCoverage20m")}}


def snapshot_fixture():
    return {
        "agcomAudit": {"officialCsvUrl": "https://example.invalid/agcom.csv"},
        "towns": [
            {
                "town": name,
                "code": code,
                "agcom": {
                    "primaryOfficialCsv": {
                        "famiglie_residenti": households,
                        "copertura_ftth_desi_pct": desi,
                        "copertura_ftth_20m_pct": within20,
                    }
                },
            }
            for name, code, households, desi, within20 in TOWNS
        ],
    }


def test_apply_primary_percentages():
    data, snapshot = module.apply(data_fixture(), snapshot_fixture())
    desi = data["metrics"]["ftthCoverageDesi"]
    massarosa = next(row for row in desi["rows"] if row["code"] == "046018")
    assert massarosa["value"] == 47.0
    assert massarosa["formatted"] == "47,0%"
    assert desi["method"]["coverage"] == "7/7"
    expected = sum(h * p for _, _, h, p, _ in TOWNS) / sum(h for _, _, h, _, _ in TOWNS)
    assert math.isclose(desi["aggregate"]["value"], expected)
    within = data["metrics"]["ftthCoverage20m"]
    assert next(row for row in within["rows"] if row["code"] == "046018")["value"] == 34.0
    assert snapshot["agcomPrimarySource"]["role"].startswith("Fonte primaria")


if __name__ == "__main__":
    test_apply_primary_percentages()
    print("OK: test percentuali FTTH primarie AGCOM")
