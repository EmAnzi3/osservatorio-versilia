#!/usr/bin/env python3
from __future__ import annotations

import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "data" / "site-data.json"
REGISTRY = ROOT / "data" / "source-registry.json"
SNAPSHOT = ROOT / "data" / "source-snapshots" / "rgs-amministrazione-2024.json"
KEYS = ("municipalEmployeesPer1000", "municipalStaffTurnover", "municipalStaffAgeStructure")


def close(a: float, b: float, label: str) -> None:
    assert math.isclose(float(a), float(b), rel_tol=1e-9, abs_tol=1e-9), f"{label}: {a} != {b}"


def main() -> None:
    site = json.loads(SITE.read_text(encoding="utf-8"))
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    snapshot = json.loads(SNAPSHOT.read_text(encoding="utf-8"))

    assert len(site["metrics"]) == 136, f"Attesi 136 indicatori, trovati {len(site['metrics'])}"
    assert registry["expectedMetricCount"] == 136
    assert registry["expectedInlineMetricCount"] == 132
    assert registry["expectedExternalMetricCount"] == 4

    theme = site["themes"]["bilanci"]
    assert theme["label"] == "Bilanci e amministrazione"
    assert all(key in theme["metrics"] for key in KEYS)
    section = next(section for section in theme["sections"] if section["key"] == "personale-amministrazione")
    assert section["metrics"] == list(KEYS)

    expected_towns = set(snapshot["towns"])
    for key in KEYS:
        metric = site["metrics"][key]
        assert metric["method"]["coverage"] == "7/7"
        assert {row["town"] for row in metric["rows"]} == expected_towns
        assert len(metric["rows"]) == 7
        assert metric["meta"]["polarity"] == "neutral"

    employees = site["metrics"]["municipalEmployeesPer1000"]
    staff_total = population_total = 0.0
    for row in employees["rows"]:
        staff = row["staffAt31Dec"]
        population = row["residentPopulation"]
        close(row["value"], staff / population * 1000, f"dipendenti/{row['town']}")
        staff_total += staff
        population_total += population
    close(employees["aggregate"]["value"], staff_total / population_total * 1000, "dipendenti/Versilia")

    turnover = site["metrics"]["municipalStaffTurnover"]
    net_hires = net_cessations = staff_total = 0.0
    for row in turnover["rows"]:
        staff = snapshot["towns"][row["town"]]["staffAt31Dec"]
        expected = (row["netHires"] - row["netCessations"]) / staff * 100
        close(row["value"], expected, f"turnover/{row['town']}")
        net_hires += row["netHires"]
        net_cessations += row["netCessations"]
        staff_total += staff
    close(turnover["aggregate"]["value"], (net_hires - net_cessations) / staff_total * 100, "turnover/Versilia")

    age = site["metrics"]["municipalStaffAgeStructure"]
    assert age["meta"]["compositeType"] == "securityMeasures"
    aggregate_counts = [0, 0, 0]
    for row in age["rows"]:
        parts = row["parts"]
        assert len(parts) == 3
        staff = snapshot["towns"][row["town"]]["staffAt31Dec"]
        assert sum(part["count"] for part in parts) == staff
        close(sum(part["value"] for part in parts), 100.0, f"età/{row['town']}/somma")
        close(row["value"], parts[0]["value"], f"età/{row['town']}/55+")
        for index, part in enumerate(parts):
            aggregate_counts[index] += part["count"]
    total = sum(aggregate_counts)
    for index, part in enumerate(age["aggregate"]["parts"]):
        close(part["value"], aggregate_counts[index] / total * 100, f"età/Versilia/{index}")

    print("Amministrazione Lotto A verificata: 136 indicatori, 7/7 Comuni, aggregati pesati e semantica neutrale.")


if __name__ == "__main__":
    main()
