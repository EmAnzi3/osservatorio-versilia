#!/usr/bin/env python3
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import apply_agcom_absolute_policy as absolute_policy  # noqa: E402
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


def test_absolute_source_policy_alignment():
    data = {
        "metrics": {
            key: {"sourceUrl": "https://geo.agcom.it/reportistica/ai/index.html"}
            for key in absolute_policy.restore.PARTIAL_KEYS
        }
    }
    absolute_policy._align_absolute_sources(data)
    for key in absolute_policy.restore.PARTIAL_KEYS:
        assert data["metrics"][key]["sourceUrl"] == absolute_policy.primary.AI_READY_PAGE

    registry_path = SCRIPT_DIR.parent / "data" / "source-registry.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    assert (
        registry["sourceProfileByUrl"][absolute_policy.primary.AI_READY_PAGE]
        == "agcom-quarterly"
    )


def primary_csv_fixture(*, leading_blank_lines: bool = False) -> bytes:
    header = [f"col_{index}" for index in range(19)]
    header[3] = "pro_com"
    row = [""] * 19
    row[2] = "Comune test"
    row[3] = "046001"
    row[13] = "1000"
    row[14] = "700"
    row[15] = "650"
    row[16] = "70,0"
    row[18] = "65,0"
    prefix = "\n\n" if leading_blank_lines else ""
    return (prefix + ";".join(header) + "\n" + ";".join(row) + "\n").encode("utf-8-sig")


def assert_primary_data_error(payload: bytes):
    primary = absolute_policy.primary
    try:
        primary.parse_csv(payload)
    except primary.base.DataError:
        return
    raise AssertionError("Il payload AGCOM non valido doveva essere rifiutato")


def test_primary_csv_tolerates_leading_blank_lines():
    primary = absolute_policy.primary
    rows = primary.parse_csv(primary_csv_fixture(leading_blank_lines=True))
    assert rows["046001"]["famiglie_residenti"] == 1000
    assert rows["046001"]["famiglie_ftth"] == 700
    assert rows["046001"]["copertura_ftth_desi_pct"] == 70.0


def test_primary_csv_rejects_invalid_payloads():
    assert_primary_data_error(b"\n\n")
    assert_primary_data_error(b"<html><body>errore</body></html>")


def test_primary_csv_retries_malformed_payload():
    primary = absolute_policy.primary
    original_fetch = primary.fetch_bytes
    original_sleep = primary.time.sleep
    payloads = [b"\n", primary_csv_fixture()]
    calls = []

    def fake_fetch(url: str, accept: str = "*/*") -> bytes:
        calls.append((url, accept))
        return payloads.pop(0)

    primary.fetch_bytes = fake_fetch
    primary.time.sleep = lambda _seconds: None
    try:
        rows = primary.fetch_primary_rows("https://example.invalid/agcom.csv", attempts=2)
    finally:
        primary.fetch_bytes = original_fetch
        primary.time.sleep = original_sleep

    assert len(calls) == 2
    assert "046001" in rows


if __name__ == "__main__":
    test_apply_primary_percentages()
    test_absolute_source_policy_alignment()
    test_primary_csv_tolerates_leading_blank_lines()
    test_primary_csv_rejects_invalid_payloads()
    test_primary_csv_retries_malformed_payload()
    print("OK: test percentuali FTTH primarie AGCOM, policy fonte e resilienza CSV")
