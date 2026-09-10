#!/usr/bin/env python3
"""Contratto dati v1.34.0 · Economia prodotta."""
from __future__ import annotations

import json
import math
from pathlib import Path

from economia_prodotta_config import ADDITIVE_KEYS

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "data" / "site-data.json"
REGISTRY = ROOT / "data" / "source-registry.json"
SNAPSHOT = ROOT / "data" / "source-snapshots" / "economia-prodotta-frame-sbs-v134.json"

KEYS = (
    "businessTurnover",
    "businessValueAdded",
    "labourProductivity",
    "turnoverPerPersonEmployed",
    "valueAddedTurnoverShare",
    "averageGrossRemunerationPerEmployee",
    "labourCost",
    "grossOperatingMargin",
)
TOWNS = {
    "Camaiore", "Forte dei Marmi", "Massarosa", "Pietrasanta",
    "Seravezza", "Stazzema", "Viareggio"
}


def close(a: float, b: float, tol: float = 1e-6) -> bool:
    return math.isclose(float(a), float(b), rel_tol=tol, abs_tol=tol)


def snapshot_rows(snapshot: dict) -> list[dict]:
    rows = []
    for name in snapshot.get("parts", []):
        part = json.loads((SNAPSHOT.parent / name).read_text(encoding="utf-8"))
        columns = part["columns"]
        rows.extend(dict(zip(columns, values, strict=True)) for values in part["rows"])
    return rows


def main() -> int:
    snapshot = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    source_rows = snapshot_rows(snapshot)
    assert snapshot["qualityGate"]["coverage"] == "7/7"
    assert snapshot["qualityGate"]["suppressedTargetCells"] == 0
    assert len(source_rows) == 189
    assert set(snapshot["referenceYears"]) == set(range(2015, 2024))

    triplets = {(r["year"], r["scope"], r["town"]) for r in source_rows}
    assert len(triplets) == 189
    for year in range(2015, 2024):
        for scope in ("total", "industry", "services"):
            assert {town for y, s, town in triplets if y == year and s == scope} == TOWNS

    # Verifica aritmetica delle due elaborazioni, separata dai dati diretti.
    for row in source_rows:
        expected = row["turnoverThousandEuro"] / row["personsEmployed"] * 1000
        assert math.isfinite(expected)
        if row["year"] >= 2021:
            mol = row["valueAddedThousandEuro"] - row["labourCostThousandEuro"]
            assert math.isfinite(mol)
        else:
            assert row["labourCostThousandEuro"] is None

    data = json.loads(SITE.read_text(encoding="utf-8"))
    assert data["release_version"] == "1.34.0"
    assert data["version"] == "v1.34.0"
    metrics = data["metrics"]
    for key in KEYS:
        assert key in metrics, key
        metric = metrics[key]
        assert metric["meta"]["theme"] == "economia"
        assert metric["meta"]["economicScopeSelector"] is True
        assert len(metric["rows"]) == 7
        assert {row["town"] for row in metric["rows"]} == TOWNS
        assert all(set(row["economicScopes"]) == {"total", "industry", "services"} for row in metric["rows"])
        assert set(metric["aggregate"]["economicScopes"]) == {"total", "industry", "services"}
        assert metric["method"]["coverage"] == "7/7"

    for key in ADDITIVE_KEYS:
        metric = metrics[key]
        assert metric["meta"]["comparisonDifference"] == "shareOfAggregate"
        assert metric["meta"]["comparisonOverline"] == "Peso sulla Versilia"
        for scope in ("total", "industry", "services"):
            total = metric["aggregate"]["economicScopes"][scope]["value"]
            shares = [row["economicScopes"][scope]["value"] / total * 100 for row in metric["rows"]]
            assert all(0 <= share <= 100 for share in shares)
            assert close(sum(shares), 100)

    assert len(metrics["businessTurnover"]["rows"][0]["economicScopes"]["total"]["series"]["years"]) == 9
    assert len(metrics["labourCost"]["rows"][0]["economicScopes"]["total"]["series"]["years"]) == 3
    assert len(metrics["grossOperatingMargin"]["rows"][0]["economicScopes"]["services"]["series"]["years"]) == 3
    assert metrics["labourProductivity"]["method"]["type"] == "Dato ufficiale"
    assert metrics["turnoverPerPersonEmployed"]["method"]["type"].startswith("Elaborazione")
    assert metrics["grossOperatingMargin"]["method"]["formula"] == "valore aggiunto − costo del lavoro"

    # Valori sentinella 2023 estratti dalle tavole ufficiali.
    by_town = {r["town"]: r for r in metrics["businessTurnover"]["rows"]}
    assert close(by_town["Massarosa"]["value"], 1323.339)
    assert close(by_town["Viareggio"]["value"], 3199.059)
    assert close(by_town["Stazzema"]["value"], 42.019)
    productivity = {r["town"]: r for r in metrics["labourProductivity"]["rows"]}
    assert close(productivity["Camaiore"]["value"], 41505)
    assert close(productivity["Massarosa"]["value"], 53005)

    economy = data["themes"]["economia"]
    sections = [section for section in economy["sections"] if section["key"] == "economia-prodotta"]
    assert len(sections) == 1
    assert tuple(sections[0]["metrics"]) == KEYS
    flattened = [key for section in economy["sections"] for key in section.get("metrics", [])]
    assert len(flattened) == len(set(flattened)), "Indicatore duplicato tra sezioni Economia"
    assert economy["metrics"] == [key for key in flattened if key in metrics]

    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    assert registry["expectedMetricCount"] == len(metrics)
    assert registry["expectedInlineMetricCount"] + registry["expectedExternalMetricCount"] == len(metrics)
    for key in KEYS:
        assert registry["metricOverrides"][key]["profile"] == "istat-business-annual"

    report = {
        "release": data["version"],
        "rows": len(source_rows),
        "coverage": snapshot["qualityGate"]["coverage"],
        "suppressedTargetCells": snapshot["qualityGate"]["suppressedTargetCells"],
        "referenceYears": snapshot["referenceYears"],
        "scopes": [item["key"] for item in snapshot["scopes"]],
        "metrics": list(KEYS),
        "metricCount": len(metrics),
        "status": "pass",
    }
    report_path = ROOT / "reports" / "economia-prodotta-data-gate.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        "PASS Economia prodotta: 189 righe ufficiali, 7/7, 3 perimetri, "
        "8 metriche canoniche, storici 2015–2023 / 2021–2023 e nessun duplicato."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
