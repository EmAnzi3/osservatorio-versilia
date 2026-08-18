#!/usr/bin/env python3
from __future__ import annotations

import json
import math
from pathlib import Path

DATASET_URL = "https://dati.toscana.it/dataset/regione-toscana-pnrr"
EXPECTED = {
    "046005": {"projects": 16, "concluded": 10, "funding": 3270511.41},
    "046013": {"projects": 15, "concluded": 10, "funding": 1337644.46},
    "046018": {"projects": 11, "concluded": 10, "funding": 5965208.14},
    "046024": {"projects": 12, "concluded": 9, "funding": 9478237.98},
    "046028": {"projects": 12, "concluded": 8, "funding": 2485485.63},
    "046030": {"projects": 11, "concluded": 9, "funding": 2055502.34},
    "046033": {"projects": 24, "concluded": 18, "funding": 12090517.68},
}


def rows(metric):
    return {str(row["code"]): row for row in metric["rows"]}


def count_summary_matches(node, expected):
    count = 0
    if isinstance(node, dict):
        required = {"pnrrProjects", "pnrrConcluded", "pnrrInProgress", "pnrrFunding"}
        if required.issubset(node):
            if (
                node["pnrrProjects"] == expected["projects"]
                and node["pnrrConcluded"] == expected["concluded"]
                and node["pnrrInProgress"] == expected["projects"] - expected["concluded"]
                and math.isclose(float(node["pnrrFunding"]), expected["funding"], abs_tol=0.01)
            ):
                count += 1
        for child in node.values():
            count += count_summary_matches(child, expected)
    elif isinstance(node, list):
        for child in node:
            count += count_summary_matches(child, expected)
    return count


def main():
    data = json.loads(Path("data/site-data.json").read_text(encoding="utf-8"))
    registry = json.loads(Path("data/source-registry.json").read_text(encoding="utf-8"))
    metrics = data["metrics"]
    pop = rows(metrics["population"])
    funding = rows(metrics["pnrrFunding"])
    concluded = rows(metrics["pnrrConcluded"])

    assert metrics["pnrrFunding"]["meta"]["source"] == "Regione Toscana — Open Data PNRR"
    assert metrics["pnrrConcluded"]["meta"]["source"] == "Regione Toscana — Open Data PNRR"
    assert metrics["pnrrFunding"]["sourceUrl"] == DATASET_URL
    assert metrics["pnrrConcluded"]["sourceUrl"] == DATASET_URL

    for code, expected in EXPECTED.items():
        population = float(pop[code]["value"])
        expected_per_resident = expected["funding"] / population
        expected_concluded = expected["concluded"] / expected["projects"] * 100
        assert math.isclose(float(funding[code]["value"]), expected_per_resident, rel_tol=0, abs_tol=1e-9)
        assert math.isclose(float(concluded[code]["value"]), expected_concluded, rel_tol=0, abs_tol=1e-9)
        # Il riepilogo comunale deve essere coerente con i due indicatori.
        assert count_summary_matches(data, expected) >= 1

    assert sum(v["projects"] for v in EXPECTED.values()) == 101
    assert sum(v["concluded"] for v in EXPECTED.values()) == 74
    assert math.isclose(sum(v["funding"] for v in EXPECTED.values()), 36683107.64, abs_tol=0.01)

    profile = registry["sourceProfiles"]["regione-toscana-pnrr-monthly"]
    assert profile["publisher"] == "Regione Toscana"
    assert profile["frequency"] == "monthly"
    assert registry["sourceProfileByUrl"][DATASET_URL] == "regione-toscana-pnrr-monthly"
    assert registry["expectedMetricCount"] == 127
    assert registry["expectedInlineMetricCount"] == 123
    assert registry["expectedExternalMetricCount"] == 4
    print("OK: bozza PNRR Regione Toscana coerente 7/7")


if __name__ == "__main__":
    main()
