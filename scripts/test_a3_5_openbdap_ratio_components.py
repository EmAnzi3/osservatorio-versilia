#!/usr/bin/env python3
"""Regression A3.5 lotto 2: numeratore/denominatore OpenBDAP/SIOPE."""
from __future__ import annotations

import copy
import json
from pathlib import Path

import enrichment_audit_matrix_core as matrix_core
import enrichment_audit_matrix_structural_base as structural_base
import materialize_a3_5_openbdap_ratio_components as enrichment

ROOT = Path(__file__).resolve().parents[1]
SITE_PATH = ROOT / "data" / "site-data.json"
BILANCI_PATH = ROOT / "data" / "source-snapshots" / "bilanci-v1.6.0.json"
SIOPE_PATH = ROOT / "data" / "source-snapshots" / "siope-history-v1.6.0.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_openbdap_ratio_components_enrichment() -> None:
    site = copy.deepcopy(load(SITE_PATH))
    bilanci = load(BILANCI_PATH)
    siope = load(SIOPE_PATH)

    baseline_other_dimensions = {}
    for metric_id in enrichment.TARGET_METRICS:
        metric = site["metrics"][metric_id]
        assert structural_base.acquired_evidence(metric, "numeratore_denominatore") is None, metric_id
        baseline_other_dimensions[metric_id] = {
            dimension: structural_base.acquired_evidence(metric, dimension)
            for dimension in matrix_core.DIMENSIONS
            if dimension != "numeratore_denominatore"
        }

    summary = enrichment.apply_enrichment(site, bilanci, siope)
    assert summary == {
        "metricsEnriched": 16,
        "towns": 7,
        "rowsEnriched": 112,
        "pairsAcquired": 16,
    }

    for metric_id in enrichment.TARGET_METRICS:
        metric = site["metrics"][metric_id]
        evidence = structural_base.acquired_evidence(metric, "numeratore_denominatore")
        assert evidence is not None, metric_id
        assert "ratioComponents" in evidence, (metric_id, evidence)

        rows = metric.get("rows") or []
        assert len(rows) == 7, metric_id
        for row in rows:
            payload = row["ratioComponents"]
            assert payload["dimension"] == "numeratore_denominatore", (metric_id, row["town"])
            assert payload["year"] == 2025, (metric_id, row["town"])
            assert payload["source"], (metric_id, row["town"])
            assert payload["sourceUrl"], (metric_id, row["town"])
            assert payload["sourceSnapshot"] in {
                "data/source-snapshots/bilanci-v1.6.0.json",
                "data/source-snapshots/siope-history-v1.6.0.json",
            }
            assert "numerator" in payload and "denominator" in payload
            assert float(payload["denominator"]["value"]) != 0
            enrichment._assert_close(
                float(row["value"]),
                enrichment._ratio_value(payload),
                f"test {metric_id}/{row['town']}",
            )

        for dimension, expected_evidence in baseline_other_dimensions[metric_id].items():
            observed_evidence = structural_base.acquired_evidence(metric, dimension)
            assert observed_evidence == expected_evidence, (
                metric_id,
                dimension,
                expected_evidence,
                observed_evidence,
            )

    assert set(enrichment.BILANCI_TARGETS).isdisjoint(enrichment.SIOPE_TARGETS)
    assert len(set(enrichment.TARGET_METRICS)) == 16


if __name__ == "__main__":
    test_openbdap_ratio_components_enrichment()
    print(
        "A3.5 OpenBDAP ratio-components regression passed: "
        "16 coppie numeratore/denominatore acquisite da snapshot versionati."
    )
