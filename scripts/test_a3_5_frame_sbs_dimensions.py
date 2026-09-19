#!/usr/bin/env python3
"""Regression A3.5 lotto 3: dimensioni Frame SBS Territoriale."""
from __future__ import annotations

import copy
import json
from pathlib import Path

import enrichment_audit_matrix_core as matrix_core
import enrichment_audit_matrix_structural_base as structural_base
import materialize_a3_5_frame_sbs_dimensions as enrichment
import materialize_economia_prodotta_release as frame_release

ROOT = Path(__file__).resolve().parents[1]
SITE_PATH = ROOT / "data" / "site-data.json"
SNAPSHOT_PATH = ROOT / "data" / "source-snapshots" / "economia-prodotta-frame-sbs-v134.json"

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


def effective_frame_seed() -> dict:
    """Riproduce le metriche Frame SBS effettive senza patchare asset/runtime."""
    site = copy.deepcopy(load(SITE_PATH))
    snapshot = frame_release.load_snapshot()
    frame_release.validate(snapshot)
    metrics = site["metrics"]
    for metric_id in enrichment.TARGET_METRICS:
        old = metrics.get(metric_id)
        if metric_id in {"businessValueAdded", "labourProductivity"}:
            assert old is not None, metric_id
        metrics[metric_id] = frame_release.metric(snapshot, metric_id, old)
    return site


def test_frame_sbs_enrichment() -> None:
    site = effective_frame_seed()
    snapshot = load(SNAPSHOT_PATH)

    intended = {
        metric_id: {"categorie_specifiche", "assoluto_normalizzato"}
        | ({"numeratore_denominatore"} if metric_id in enrichment.RATIO_TARGETS else set())
        for metric_id in enrichment.TARGET_METRICS
    }
    baseline = {}
    for metric_id in enrichment.TARGET_METRICS:
        metric = site["metrics"][metric_id]
        baseline[metric_id] = {
            dimension: structural_base.acquired_evidence(metric, dimension)
            for dimension in matrix_core.DIMENSIONS
        }
        for dimension in intended[metric_id]:
            assert baseline[metric_id][dimension] is None, (metric_id, dimension, baseline[metric_id][dimension])

    summary = enrichment.apply_enrichment(site, snapshot)
    assert summary == {
        "metricsEnriched": 8,
        "towns": 7,
        "rowsEnriched": 56,
        "categoryPairs": 8,
        "absoluteNormalizedPairs": 8,
        "ratioPairs": 4,
        "pairsAcquired": 20,
    }

    for metric_id in enrichment.TARGET_METRICS:
        metric = site["metrics"][metric_id]
        rows = {row["town"]: row for row in metric["rows"]}
        assert set(rows) == EXPECTED_TOWNS

        category_evidence = structural_base.acquired_evidence(metric, "categorie_specifiche")
        assert category_evidence is not None, metric_id
        assert "frameSbsCategories" in category_evidence, (metric_id, category_evidence)

        normalized_evidence = structural_base.acquired_evidence(metric, "assoluto_normalizzato")
        assert normalized_evidence is not None, metric_id
        assert "frameSbsAbsoluteNormalized" in normalized_evidence, (metric_id, normalized_evidence)

        if metric_id in enrichment.RATIO_TARGETS:
            ratio_evidence = structural_base.acquired_evidence(metric, "numeratore_denominatore")
            assert ratio_evidence is not None, metric_id
            assert "frameSbsRatioComponents" in ratio_evidence, (metric_id, ratio_evidence)

        for town, row in rows.items():
            categories = row["frameSbsCategories"]
            assert categories["dimension"] == "categorie_specifiche"
            assert categories["year"] == 2023
            assert categories["sourceSnapshot"] == enrichment.SOURCE_SNAPSHOT
            assert [item["key"] for item in categories["categories"]] == ["total", "industry", "services"]
            assert all(item["series"] for item in categories["categories"])

            companion = row["frameSbsAbsoluteNormalized"]
            assert companion["dimension"] == "assoluto_normalizzato"
            assert companion["year"] == 2023
            assert companion["absolute"]["value"] is not None
            assert companion["normalized"]["value"] is not None
            assert companion["normalized"]["denominator"]["value"] != 0

            if metric_id in enrichment.RATIO_TARGETS:
                ratio = row["frameSbsRatioComponents"]
                assert ratio["dimension"] == "numeratore_denominatore"
                assert ratio["year"] == 2023
                assert ratio["denominator"]["value"] != 0
                enrichment._assert_ratio(
                    metric_id,
                    float(row["value"]),
                    float(ratio["numerator"]["value"]),
                    float(ratio["denominator"]["value"]),
                    float(ratio["scale"]),
                    f"test {metric_id}/{town}",
                )

        for dimension in matrix_core.DIMENSIONS:
            if dimension in intended[metric_id]:
                continue
            observed = structural_base.acquired_evidence(metric, dimension)
            assert observed == baseline[metric_id][dimension], (
                metric_id,
                dimension,
                baseline[metric_id][dimension],
                observed,
            )

    assert len(set(enrichment.TARGET_METRICS)) == 8
    assert set(enrichment.RATIO_TARGETS).issubset(enrichment.TARGET_METRICS)


if __name__ == "__main__":
    test_frame_sbs_enrichment()
    print(
        "A3.5 Frame SBS regression passed: "
        "20 coppie acquisite da snapshot Istat versionati "
        "(8 categorie, 8 assoluto/normalizzato, 4 numeratore/denominatore)."
    )
