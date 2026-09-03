#!/usr/bin/env python3
from __future__ import annotations

import json
import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
METRIC_KEY = "financialDebtProfile"
YEARS = list(range(2019, 2026))
TOWNS = ["Massarosa", "Viareggio", "Camaiore", "Pietrasanta", "Seravezza", "Forte dei Marmi", "Stazzema"]


def load(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def close(a: float, b: float, tol: float = 1e-9) -> bool:
    return math.isclose(float(a), float(b), rel_tol=tol, abs_tol=tol)


def main() -> None:
    data = load("data/site-data.json")
    snapshot = load("data/source-snapshots/salute-finanziaria-v129.json")
    bilanci = load("data/source-snapshots/bilanci-v1.6.0.json")
    registry = load("data/source-registry.json")
    app = (ROOT / "assets/app-parts/03.txt").read_text(encoding="utf-8")
    css = (ROOT / "assets/fidelity.css").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    assert data["version"] == "v1.29.0"
    assert data["updated"] == "3 settembre 2026"
    assert len(data["metrics"]) == 181, len(data["metrics"])
    assert METRIC_KEY in data["themes"]["bilanci"]["metrics"]
    section = next(s for s in data["themes"]["bilanci"]["sections"] if s["key"] == "equilibri")
    assert METRIC_KEY in section["metrics"]

    metric = data["metrics"][METRIC_KEY]
    assert metric["meta"]["compositeType"] == "financialProfile"
    assert metric["meta"]["polarity"] == "neutral"
    assert metric["method"]["coverage"] == "7/7 · 2019–2025"
    assert [row["town"] for row in metric["rows"]] == TOWNS

    by_town = {row["town"]: row for row in metric["rows"]}
    for town in TOWNS:
        raw = snapshot["towns"][town]
        row = by_town[town]
        assert len(row["parts"]) == 3
        pop = [float(bilanci["raw"][town]["years"][str(y)]["population_at_1_january"]) for y in YEARS]
        expected_debt = [d / p for d, p in zip(raw["debt_financing_d1"], pop, strict=True)]
        expected_interest = [i / r * 100 for i, r in zip(raw["interest_commitments"], raw["current_revenue"], strict=True)]
        expected_sustainability = raw["debt_sustainability_10_3"]
        for part, expected in zip(row["parts"], [expected_debt, expected_interest, expected_sustainability], strict=True):
            assert part["series"]["years"] == YEARS
            assert len(part["series"]["values"]) == 7
            assert all(close(actual, target) for actual, target in zip(part["series"]["values"], expected, strict=True)), (town, part["key"])

    camaiore = by_town["Camaiore"]["parts"][2]
    assert close(camaiore["series"]["values"][4], 9.64)
    assert close(camaiore["series"]["values"][5], 10.82)
    assert snapshot["towns"]["Camaiore"]["debt_sustainability_pdi_raw"][4:6] == [964.0, 1082.0]
    assert snapshot["towns"]["Camaiore"]["debt_sustainability_source"][4:6] == ["pdi_scale_normalized", "pdi_scale_normalized"]

    forte = by_town["Forte dei Marmi"]["parts"][2]
    assert close(forte["series"]["values"][0], 0.273416)
    assert forte["series"]["values"][4:] == [0.0, 0.0, 0.0]
    assert snapshot["towns"]["Forte dei Marmi"]["debt_sustainability_source"][4:] == ["reconstructed_components"] * 3
    assert snapshot["towns"]["Forte dei Marmi"]["interest_commitments"][4:] == [0.0, 0.0, 0.0]
    assert snapshot["towns"]["Forte dei Marmi"]["title4_repayment"][4:] == [0.0, 0.0, 0.0]
    assert snapshot["towns"]["Forte dei Marmi"]["excluded_capital_transfers_10_3"][4:] == [0.0, 0.0, 0.0]

    aggregate = metric["aggregate"]["parts"]
    for idx, year in enumerate(YEARS):
        total_debt = sum(snapshot["towns"][t]["debt_financing_d1"][idx] for t in TOWNS)
        total_pop = sum(float(bilanci["raw"][t]["years"][str(year)]["population_at_1_january"]) for t in TOWNS)
        total_interest = sum(snapshot["towns"][t]["interest_commitments"][idx] for t in TOWNS)
        total_revenue = sum(snapshot["towns"][t]["current_revenue"][idx] for t in TOWNS)
        weighted_10_3 = sum(snapshot["towns"][t]["debt_sustainability_10_3"][idx] * snapshot["towns"][t]["current_revenue"][idx] for t in TOWNS) / total_revenue
        assert close(aggregate[0]["series"]["values"][idx], total_debt / total_pop)
        assert close(aggregate[1]["series"]["values"][idx], total_interest / total_revenue * 100)
        assert close(aggregate[2]["series"]["values"][idx], weighted_10_3)

    for part_index in range(3):
        simple = sum(float(by_town[t]["parts"][part_index]["value"]) for t in TOWNS) / len(TOWNS)
        weighted = float(aggregate[part_index]["value"])
        assert not close(simple, weighted, tol=1e-6), (part_index, simple, weighted)

    massarosa = by_town["Massarosa"]
    assert "OSL" in massarosa["contextNote"]
    massarosa_raw = snapshot["towns"]["Massarosa"]
    expected_massarosa_2025 = massarosa_raw["interest_commitments"][-1] / massarosa_raw["current_revenue"][-1] * 100
    assert close(massarosa["parts"][1]["series"]["values"][-1], expected_massarosa_2025)
    assert expected_massarosa_2025 > 4.38

    assert registry["expectedMetricCount"] == 181
    assert registry["expectedInlineMetricCount"] == 177
    assert registry["expectedExternalMetricCount"] == 4
    assert registry["metricOverrides"][METRIC_KEY]["profile"] == "openbdap-annual"
    assert "181 indicatori nel catalogo canonico: 177 con valori incorporati" in readme

    assert "'financialProfile'" in app
    assert "data-financial-profile-history" in app
    assert "financialProfileHistoryMarkup" in app
    compact_css = re.sub(r"\s+", "", css)
    assert re.search(r"\.composite-town-mobilityarticle\{[^}]*padding:17px", compact_css), "Padding composito non verificato"

    print("OK salute finanziaria v1.29.0: formule, aggregati, provenienza e padding verificati.")


if __name__ == "__main__":
    main()
