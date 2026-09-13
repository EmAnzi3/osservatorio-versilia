#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "site-data.json"
SNAPSHOT = ROOT / "data" / "source-snapshots" / "bilanci-v139.json"
REGISTRY = ROOT / "data" / "source-registry.json"

EXPECTED = [
    "fcdePerResident",
    "yearEndCashFundPerResident",
    "generalAdministrationMissionExpenditurePerResident",
    "territorialPlanningMissionExpenditurePerResident",
    "civilProtectionMissionExpenditurePerResident",
    "economicDevelopmentMissionExpenditurePerResident",
]
EXCLUDED = [
    "energyMissionExpenditurePerResident",
    "liquidityManagementProfile",
]
MISSION_KEYS = [
    "educationMissionExpenditurePerResident",
    "socialMissionExpenditurePerResident",
    "environmentMissionExpenditurePerResident",
    "mobilityMissionExpenditurePerResident",
    "cultureSportMissionExpenditurePerResident",
    "tourismDevelopmentMissionExpenditurePerResident",
    "generalAdministrationMissionExpenditurePerResident",
    "territorialPlanningMissionExpenditurePerResident",
    "civilProtectionMissionExpenditurePerResident",
    "economicDevelopmentMissionExpenditurePerResident",
]
LEGACY_MISSION_AGGREGATES_2025 = {
    "educationMissionExpenditurePerResident": 184.10909423800476,
    "socialMissionExpenditurePerResident": 220.24242893455312,
    "environmentMissionExpenditurePerResident": 489.1386980457789,
    "mobilityMissionExpenditurePerResident": 148.91404145012518,
    "cultureSportMissionExpenditurePerResident": 89.1105431048585,
    "tourismDevelopmentMissionExpenditurePerResident": 76.34913268066794,
}


def population_2025(data: dict) -> dict[str, int]:
    result = {}
    for row in data["metrics"]["population"]["rows"]:
        years = row["series"]["years"]
        result[row["town"]] = int(row["series"]["values"][years.index(2025)])
    return result


def assert_mission_aggregates(data: dict, population: dict[str, int]) -> None:
    total_population = sum(population.values())
    for key in MISSION_KEYS:
        metric = data["metrics"][key]
        weighted = sum(float(row["value"]) * population[row["town"]] for row in metric["rows"]) / total_population
        assert abs(float(metric["aggregate"]["value"]) - weighted) < 1e-9, (key, metric["aggregate"]["value"], weighted)
        assert metric["aggregate"]["label"] == "Valore pro capite Versilia"
        assert "popolazione complessiva" in metric["aggregate"]["note"].lower(), key

    # I sei indicatori missione già pubblicati in v1.38 non devono cambiare.
    for key, expected in LEGACY_MISSION_AGGREGATES_2025.items():
        actual = float(data["metrics"][key]["aggregate"]["value"])
        assert abs(actual - expected) < 1e-9, (key, actual, expected)


def main() -> None:
    data = json.loads(DATA.read_text(encoding="utf-8"))
    snapshot = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))

    assert data["version"] == "v1.39.0"
    assert data["release_version"] == "1.39.0"
    assert data["updated"] == "13 settembre 2026"
    assert registry["expectedMetricCount"] == len(data["metrics"])
    assert registry["expectedInlineMetricCount"] + registry["expectedExternalMetricCount"] == len(data["metrics"])

    bilanci = data["themes"]["bilanci"]
    theme_metrics = bilanci["metrics"]
    for key in EXPECTED:
        assert key in data["metrics"], key
        assert key in theme_metrics, key
        metric = data["metrics"][key]
        assert metric["meta"]["theme"] == "bilanci"
        assert metric["meta"]["polarity"] == "neutral"
        assert metric["meta"]["year"] == "2025"
        assert len(metric["rows"]) == 7
        assert {row["town"] for row in metric["rows"]} == {
            "Massarosa", "Viareggio", "Camaiore", "Pietrasanta",
            "Seravezza", "Forte dei Marmi", "Stazzema"
        }
        years = metric["rows"][0]["series"]["years"]
        assert 2025 in years
        for row in metric["rows"]:
            assert row["series"]["years"] == years
            assert len(row["series"]["values"]) == len(years)
            assert row["value"] == row["series"]["values"][-1]
            assert row["value"] is not None

    for key in EXCLUDED:
        assert key not in data["metrics"], f"Indicatore escluso materializzato per errore: {key}"

    pop = population_2025(data)
    assert_mission_aggregates(data, pop)

    # Valori 2025 già verificati nel gate sorgenti.
    cash_expected = {
        "Camaiore": 8104846.43,
        "Forte dei Marmi": 47669797.59,
        "Massarosa": 7030169.59,
        "Pietrasanta": 37276807.73,
        "Seravezza": 5188811.87,
        "Stazzema": 449403.31,
        "Viareggio": 46361668.52,
    }
    cash = data["metrics"]["yearEndCashFundPerResident"]
    cash_years = cash["rows"][0]["series"]["years"]
    idx = cash_years.index(2025)
    for row in cash["rows"]:
        reconstructed = row["series"]["values"][idx] * pop[row["town"]]
        assert abs(reconstructed - cash_expected[row["town"]]) < 0.02, (row["town"], reconstructed)

    # La vecchia serie 07+14 deve restare distinta dalla nuova Missione 14.
    legacy = data["metrics"]["tourismDevelopmentMissionExpenditurePerResident"]
    m14 = data["metrics"]["economicDevelopmentMissionExpenditurePerResident"]
    assert legacy["meta"]["label"] == "Spesa impegnata per turismo e sviluppo economico per residente"
    assert legacy["method"]["formula"] == "impegni missioni 07 + 14 / popolazione residente"
    assert legacy != m14

    assert snapshot["policy"]["row_absence"].startswith("mai convertita in zero")
    for key in EXPECTED:
        assert key in snapshot["coverage"]
        assert "2025" not in snapshot["coverage"][key]["excluded_years"]

    sections = {section["key"]: section for section in bilanci["sections"]}
    assert "fcdePerResident" in sections["equilibri"]["metrics"]
    assert "yearEndCashFundPerResident" in sections["cassa"]["metrics"]
    for key in EXPECTED[2:]:
        assert key in sections["priorita"]["metrics"]

    print("Bilanci v1.39: metadata, 10 aggregati missione, copertura, esclusioni e guardie legacy OK")


if __name__ == "__main__":
    main()
