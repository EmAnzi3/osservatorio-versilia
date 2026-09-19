#!/usr/bin/env python3
"""Regression A3.5 lotto 4: componenti censuari Istat."""
from __future__ import annotations

import copy
import json
import math
from pathlib import Path

import enrichment_audit_matrix_core as matrix_core
import enrichment_audit_matrix_structural_base as structural_base
import materialize_a3_5_istat_census_components as enrichment

ROOT = Path(__file__).resolve().parents[1]
SITE_PATH = ROOT / "data" / "site-data.json"
SNAPSHOT_PATH = ROOT / "data" / "source-snapshots" / "istat-sections-history-v1.8.0.json"
INTENDED = {"numeratore_denominatore", "assoluto_normalizzato"}


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_census_components() -> None:
    source_site = load(SITE_PATH)
    site = copy.deepcopy(source_site)
    snapshot = load(SNAPSHOT_PATH)

    baseline_evidence = {}
    public_values = {}
    for metric_id in enrichment.TARGETS:
        metric = site["metrics"][metric_id]
        baseline_evidence[metric_id] = {
            dimension: structural_base.acquired_evidence(metric, dimension)
            for dimension in matrix_core.DIMENSIONS
        }
        for dimension in INTENDED:
            assert baseline_evidence[metric_id][dimension] is None, (
                metric_id,
                dimension,
                baseline_evidence[metric_id][dimension],
            )
        public_values[metric_id] = {
            row["town"]: row["value"]
            for row in metric["rows"]
        }

    summary = enrichment.apply_enrichment(site, snapshot)
    assert summary == {
        "metricsEnriched": 6,
        "towns": 7,
        "rowsEnriched": 42,
        "ratioPairs": 6,
        "absoluteNormalizedPairs": 6,
        "pairsAcquired": 12,
    }

    raw = enrichment._raw_2023(snapshot)
    for metric_id, cfg in enrichment.TARGETS.items():
        metric = site["metrics"][metric_id]
        ratio_evidence = structural_base.acquired_evidence(metric, "numeratore_denominatore")
        normalized_evidence = structural_base.acquired_evidence(metric, "assoluto_normalizzato")
        assert ratio_evidence is not None and "censusRatioComponents" in ratio_evidence, (
            metric_id,
            ratio_evidence,
        )
        assert normalized_evidence is not None and "censusRatioComponents" in normalized_evidence, (
            metric_id,
            normalized_evidence,
        )

        for row in metric["rows"]:
            town = row["town"]
            assert row["value"] == public_values[metric_id][town], (metric_id, town)
            payload = row["censusRatioComponents"]
            assert payload["referenceYear"] == "2023"
            assert payload["sourceSnapshot"] == enrichment.SOURCE_SNAPSHOT
            assert payload["formula"] == cfg["formula"]
            assert payload["numerator"] == raw[town][cfg["numerator"]]
            assert payload["denominator"] == raw[town][cfg["denominator"]]
            expected = float(payload["numerator"]) / float(payload["denominator"]) * float(cfg["scale"])
            assert math.isclose(
                float(row["value"]),
                expected,
                rel_tol=0.0,
                abs_tol=float(cfg["tolerance"]),
            ), (metric_id, town, row["value"], expected)

        for dimension in matrix_core.DIMENSIONS:
            if dimension in INTENDED:
                continue
            observed = structural_base.acquired_evidence(metric, dimension)
            assert observed == baseline_evidence[metric_id][dimension], (
                metric_id,
                dimension,
                baseline_evidence[metric_id][dimension],
                observed,
            )

    for metric_id in enrichment.TARGETS:
        before = source_site["metrics"][metric_id]
        after = site["metrics"][metric_id]
        assert before["meta"] == after["meta"], metric_id
        assert before.get("aggregate") == after.get("aggregate"), metric_id


if __name__ == "__main__":
    test_census_components()
    print(
        "A3.5 Istat Census regression passed: "
        "12 coppie acquisite da componenti grezzi 2023 già versionati "
        "(6 numeratore/denominatore + 6 assoluto/normalizzato)."
    )
