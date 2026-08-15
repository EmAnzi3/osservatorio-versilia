#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = json.loads((ROOT / "data" / "site-data.json").read_text(encoding="utf-8"))
REGISTRY = json.loads((ROOT / "data" / "source-registry.json").read_text(encoding="utf-8"))
SNAPSHOT = json.loads((ROOT / "data" / "source-snapshots" / "costi-fiscalita-redditi-draft-2026-08.json").read_text(encoding="utf-8"))
APP00 = (ROOT / "assets" / "app-parts" / "00.txt").read_text(encoding="utf-8")
APP03 = (ROOT / "assets" / "app-parts" / "03.txt").read_text(encoding="utf-8")


def tax_for(raw: dict, income: float) -> float:
    exemption = raw.get("exemption")
    if exemption is not None and income <= float(exemption):
        return 0.0
    if raw["scheme"] == "flat":
        return income * float(raw["ratePercent"]) / 100.0

    total = 0.0
    lower = 0.0
    for bracket in raw["brackets"]:
        upper = bracket["upTo"]
        rate = float(bracket["ratePercent"]) / 100.0
        taxable = max(0.0, (income if upper is None else min(income, float(upper))) - lower)
        total += taxable * rate
        if upper is None or income <= float(upper):
            break
        lower = float(upper)
    return total


def main() -> None:
    assert DATA["version"] == "v1.12.0", "Il draft non deve decidere il bump di versione"
    metric = DATA["metrics"]["municipalIrpef"]
    assert metric["meta"]["year"] == "2025"
    assert metric["meta"]["compositeType"] == "securityMeasures"
    assert metric["meta"]["selectorLabel"] == "Reddito imponibile"
    assert metric["method"]["coverage"] == "7/7"
    assert len(metric["rows"]) == 7
    assert {row["town"] for row in metric["rows"]} == set(SNAPSHOT["municipalIrpef"]["towns"])

    scenarios = SNAPSHOT["municipalIrpef"]["scenarios"]
    assert scenarios == [20000, 30000, 50000]
    for row in metric["rows"]:
        raw = SNAPSHOT["municipalIrpef"]["towns"][row["town"]]
        assert len(row["parts"]) == 3
        for scenario, part in zip(scenarios, row["parts"]):
            expected = round(tax_for(raw, float(scenario)), 2)
            snap_value = round(float(raw["amounts"][str(scenario)]), 2)
            actual = round(float(part["value"]), 2)
            assert expected == snap_value == actual, (row["town"], scenario, expected, snap_value, actual)

    economy = DATA["themes"]["economia"]
    assert economy["metrics"].count("municipalIrpef") == 1
    fiscal = [section for section in economy["sections"] if section["key"] == "costi-fiscalita"]
    assert len(fiscal) == 1 and fiscal[0]["metrics"] == ["municipalIrpef"]

    assert REGISTRY["expectedMetricCount"] == 122
    assert REGISTRY["expectedInlineMetricCount"] == 118
    assert REGISTRY["expectedExternalMetricCount"] == 4
    assert REGISTRY["metricOverrides"]["municipalIrpef"]["profile"] == "mef-municipal-irpef-annual"

    assert "municipalIrpef:" in APP00
    assert "metric.meta.compositeType === 'securityMeasures'" in APP03
    assert "data-composite-component" in APP03

    draft = DATA["costsFiscalDraft"]
    assert draft["publishedInDraft"] == ["municipalIrpef"]
    assert "fuelPrices" in draft["notPublished"]
    assert SNAPSHOT["audit"]["fuelPrices"]["decision"] == "ESCLUSO"
    assert SNAPSHOT["audit"]["tari"]["decision"] == "DA VALUTARE"
    assert SNAPSHOT["audit"]["imu"]["decision"] == "DA VALUTARE"
    assert SNAPSHOT["audit"]["wasteServiceCost"]["decision"] == "DA VALUTARE"

    print("Draft costi/fiscalità verificato: IRPEF 7/7, 3 scenari, conteggio 122 = 118 inline + 4 esterni")


if __name__ == "__main__":
    main()
