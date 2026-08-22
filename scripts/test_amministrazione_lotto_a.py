#!/usr/bin/env python3
from __future__ import annotations

import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "data" / "site-data.json"
REGISTRY = ROOT / "data" / "source-registry.json"
SNAPSHOT = ROOT / "data" / "source-snapshots" / "rgs-amministrazione-2024.json"
TRAINING_SNAPSHOT = ROOT / "data" / "source-snapshots" / "rgs-formazione-2024.json"
ONLINE_SNAPSHOT = ROOT / "data" / "source-snapshots" / "regione-toscana-servizi-online-2018-2022.json"
KEYS = (
    "municipalEmployeesPer1000",
    "municipalStaffTurnover",
    "municipalStaffAgeStructure",
    "municipalStaffTraining",
    "municipalOnlineServicesAdvanced",
)


def close(a: float, b: float, label: str) -> None:
    assert math.isclose(float(a), float(b), rel_tol=1e-9, abs_tol=1e-9), f"{label}: {a} != {b}"


def main() -> None:
    site = json.loads(SITE.read_text(encoding="utf-8"))
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    snapshot = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    training_snapshot = json.loads(TRAINING_SNAPSHOT.read_text(encoding="utf-8"))
    online_snapshot = json.loads(ONLINE_SNAPSHOT.read_text(encoding="utf-8"))

    assert len(site["metrics"]) == 138, f"Attesi 138 indicatori, trovati {len(site['metrics'])}"
    assert registry["expectedMetricCount"] == 138
    assert registry["expectedInlineMetricCount"] == 134
    assert registry["expectedExternalMetricCount"] == 4

    theme = site["themes"]["bilanci"]
    assert theme["label"] == "Bilanci e amministrazione"
    assert all(key in theme["metrics"] for key in KEYS)
    section = next(section for section in theme["sections"] if section["key"] == "personale-amministrazione")
    assert section["metrics"] == list(KEYS)

    expected_towns = set(snapshot["towns"])
    assert set(training_snapshot["towns"]) == expected_towns
    assert set(online_snapshot["towns"]) == expected_towns
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
        assert row["staffAt31Dec"] == staff
        assert sum(part["count"] for part in parts) == staff
        close(sum(part["value"] for part in parts), 100.0, f"età/{row['town']}/somma")
        close(row["value"], parts[0]["value"], f"età/{row['town']}/55+")
        for index, part in enumerate(parts):
            aggregate_counts[index] += part["count"]
    total = sum(aggregate_counts)
    assert age["aggregate"]["staffAt31Dec"] == total
    for index, part in enumerate(age["aggregate"]["parts"]):
        close(part["value"], aggregate_counts[index] / total * 100, f"età/Versilia/{index}")

    training = site["metrics"]["municipalStaffTraining"]
    assert training["meta"]["compositeType"] == "securityMeasures"
    for row in training["rows"]:
        raw = training_snapshot["towns"][row["town"]]
        parts = row["parts"]
        assert len(parts) == 4
        close(row["value"], raw["meanTotalRgs"], f"formazione/{row['town']}/media totale")
        close(parts[0]["value"], raw["meanTotalRgs"], f"formazione/{row['town']}/part0")
        assert parts[1]["value"] == raw["totalDays"]
        close(parts[2]["value"], raw["meanMen"], f"formazione/{row['town']}/uomini")
        close(parts[3]["value"], raw["meanWomen"], f"formazione/{row['town']}/donne")
        assert raw["menDays"] + raw["womenDays"] == raw["totalDays"]
        close(raw["meanTotalRgs"], (raw["meanMen"] + raw["meanWomen"]) / 2, f"formazione/{row['town']}/formula RGS")

    versilia = training_snapshot["versilia"]
    close(training["aggregate"]["value"], versilia["meanTotalRgs"], "formazione/Versilia/media totale")
    assert training["aggregate"]["parts"][1]["value"] == versilia["totalDays"] == 1278
    close(training["aggregate"]["parts"][2]["value"], versilia["meanMen"], "formazione/Versilia/uomini")
    close(training["aggregate"]["parts"][3]["value"], versilia["meanWomen"], "formazione/Versilia/donne")

    online = site["metrics"]["municipalOnlineServicesAdvanced"]
    assert online["meta"]["year"] == "2022"
    assert online["meta"]["unit"] == "percent"
    assert "livelli 3 e 4" in online["method"]["formula"]
    assert "24 servizi" in online["method"]["caveat"] and "27" in online["method"]["caveat"]
    current_values = []
    for row in online["rows"]:
        raw = online_snapshot["towns"][row["town"]]
        close(row["value"], raw["2022"], f"online/{row['town']}/2022")
        assert row["series"]["years"] == [2018, 2022]
        assert len(row["series"]["values"]) == 2
        close(row["series"]["values"][0], raw["2018"], f"online/{row['town']}/2018")
        close(row["series"]["values"][1], raw["2022"], f"online/{row['town']}/serie2022")
        current_values.append(float(raw["2022"]))
    close(online["aggregate"]["value"], sum(current_values) / 7, "online/Versilia")
    assert "media aritmetica" in online["aggregate"]["note"].lower()
    assert registry["metricOverrides"]["municipalOnlineServicesAdvanced"]["profile"] == "regione-toscana-indicatori-comunali"

    print("Amministrazione verificata: 138 indicatori, 5 letture amministrative 7/7, servizi online ind18 2022 con storico reale 2018→2022.")


if __name__ == "__main__":
    main()
