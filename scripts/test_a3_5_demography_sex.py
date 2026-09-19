#!/usr/bin/env python3
"""Regression A3.5 lotto 1: sesso su popolazione, dipendenza e residenti stranieri."""
from __future__ import annotations

import copy
import json
from pathlib import Path

import enrichment_audit_matrix_core as matrix_core
import materialize_a3_5_demography_sex as enrichment

ROOT = Path(__file__).resolve().parents[1]
SITE_PATH = ROOT / "data" / "site-data.json"
DEMOGRAPHY_SNAPSHOT_PATH = ROOT / "data" / "source-snapshots" / "istat-demography-lotto-a-2026-08.json"
RCS_SNAPSHOT_PATH = ROOT / "data" / "source-snapshots" / "istat-rcs-demography-2025.json"

TARGETS = ("population", "dependencyIndices", "foreignResidents")
EXPECTED_TOWNS = {
    "Camaiore",
    "Forte dei Marmi",
    "Massarosa",
    "Pietrasanta",
    "Seravezza",
    "Stazzema",
    "Viareggio",
}


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def groups(item: dict) -> dict[str, dict]:
    return {group["key"]: group for group in item["groups"]}


def test_demography_sex_enrichment() -> None:
    site = copy.deepcopy(load(SITE_PATH))
    demography = load(DEMOGRAPHY_SNAPSHOT_PATH)
    rcs = load(RCS_SNAPSHOT_PATH)

    summary = enrichment.apply_enrichment(site, demography, rcs)
    assert summary == {"metricsEnriched": 3, "towns": 7, "pairsAcquired": 3}

    for metric_id in TARGETS:
        metric = site["metrics"][metric_id]
        evidence = matrix_core.acquired_evidence(metric, "sesso")
        assert evidence is not None, (metric_id, evidence)
        assert "sexBreakdown" in evidence, (metric_id, evidence)
        rows = {row["town"]: row for row in metric["rows"]}
        assert set(rows) == EXPECTED_TOWNS
        for town, row in rows.items():
            breakdown = row["sexBreakdown"]
            assert breakdown["dimension"] == "sesso", (metric_id, town)
            assert breakdown["sourceUrl"], (metric_id, town)
            assert set(groups(breakdown)) == {"men", "women"}
        aggregate = metric["aggregate"]["sexBreakdown"]
        assert aggregate["dimension"] == "sesso", metric_id
        assert aggregate["sourceUrl"], metric_id
        assert set(groups(aggregate)) == {"men", "women"}

    population = site["metrics"]["population"]
    for row in population["rows"]:
        breakdown = row["sexBreakdown"]
        by_sex = groups(breakdown)
        assert by_sex["men"]["count"] + by_sex["women"]["count"] == int(row["value"])
        assert abs(
            by_sex["men"]["sharePercent"] + by_sex["women"]["sharePercent"] - 100.0
        ) < 1e-9
    population_aggregate = population["aggregate"]["sexBreakdown"]
    assert population_aggregate["total"] == int(population["aggregate"]["value"])

    dependency = site["metrics"]["dependencyIndices"]
    for row in dependency["rows"]:
        for group in row["sexBreakdown"]["groups"]:
            structural, elderly = group["parts"]
            assert structural["key"] == "structural"
            assert elderly["key"] == "elderly"
            assert structural["denominator"] > 0
            assert elderly["denominator"] == structural["denominator"]
            assert abs(
                structural["value"]
                - structural["numerator"] / structural["denominator"] * 100
            ) < 1e-9
            assert abs(
                elderly["value"]
                - elderly["numerator"] / elderly["denominator"] * 100
            ) < 1e-9

    foreign = site["metrics"]["foreignResidents"]
    rcs_towns = rcs["towns"]
    for row in foreign["rows"]:
        town = row["town"]
        breakdown = row["sexBreakdown"]
        by_sex = groups(breakdown)
        expected = int(rcs_towns[town]["citizenshipTotal"])
        assert breakdown["total"] == expected
        assert by_sex["men"]["count"] + by_sex["women"]["count"] == expected
        assert abs(
            by_sex["men"]["shareWithinForeignResidentsPercent"]
            + by_sex["women"]["shareWithinForeignResidentsPercent"]
            - 100.0
        ) < 1e-9
        if row.get("count") is not None:
            assert int(row["count"]) == expected
    foreign_aggregate = foreign["aggregate"]["sexBreakdown"]
    assert foreign_aggregate["total"] == int(
        rcs["aggregate"]["Versilia"]["citizenshipTotal"]
    )


if __name__ == "__main__":
    test_demography_sex_enrichment()
    print(
        "A3.5 demografia sesso regression passed: "
        "population, dependencyIndices, foreignResidents strutturalmente acquisiti."
    )
