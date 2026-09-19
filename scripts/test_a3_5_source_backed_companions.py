#!/usr/bin/env python3
"""Regression A3.5 lotto 5: companion strutturali source-backed."""
from __future__ import annotations

import copy
import json
import math
import tempfile
from pathlib import Path

import apply_bilanci_v139 as bilanci_v139
import enrichment_audit_matrix_core as matrix_core
import enrichment_audit_matrix_structural_base as structural_base
import materialize_a3_5_openbdap_ratio_components as openbdap
import materialize_a3_5_source_backed_companions as enrichment

ROOT = Path(__file__).resolve().parents[1]
SITE_PATH = ROOT / "data" / "site-data.json"
REGISTRY_PATH = ROOT / "data" / "source-registry.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def effective_seed_after_openbdap() -> dict:
    with tempfile.TemporaryDirectory(prefix="a3-5-source-backed-") as temp_dir:
        temp = Path(temp_dir)
        data_path = temp / "site-data.json"
        registry_path = temp / "source-registry.json"
        data_path.write_text(SITE_PATH.read_text(encoding="utf-8"), encoding="utf-8")
        registry_path.write_text(REGISTRY_PATH.read_text(encoding="utf-8"), encoding="utf-8")

        original_data_path = bilanci_v139.DATA_PATH
        original_registry_path = bilanci_v139.REGISTRY_PATH
        try:
            bilanci_v139.DATA_PATH = data_path
            bilanci_v139.REGISTRY_PATH = registry_path
            bilanci_v139.main()
            site = load(data_path)
        finally:
            bilanci_v139.DATA_PATH = original_data_path
            bilanci_v139.REGISTRY_PATH = original_registry_path

    openbdap.apply_enrichment(
        site,
        load(openbdap.BILANCI_PATH),
        load(openbdap.SIOPE_PATH),
    )
    return site


def expected_pairs() -> dict[str, set[str]]:
    result = {
        metric_id: {"assoluto_normalizzato"}
        for metric_id in enrichment.OPENBDAP_TARGETS
    }
    result["cohabitingHouseholds"] = {"numeratore_denominatore", "assoluto_normalizzato"}
    result["oldAgeIndex"] = {"numeratore_denominatore", "assoluto_normalizzato"}
    result["agriculturalUsedArea"] = {"numeratore_denominatore"}
    result["averageAgriculturalFarmSize"] = {"numeratore_denominatore", "assoluto_normalizzato"}
    result["irrigatedAgriculturalArea"] = {"numeratore_denominatore"}
    for metric_id in enrichment.BUSINESS_TARGETS:
        result[metric_id] = {"numeratore_denominatore", "assoluto_normalizzato"}
    return result


def public_surface(metric: dict) -> dict:
    return {
        "meta": copy.deepcopy(metric.get("meta")),
        "method": copy.deepcopy(metric.get("method")),
        "aggregate": copy.deepcopy(metric.get("aggregate")),
        "normalizedAggregate": copy.deepcopy(metric.get("normalizedAggregate")),
        "rows": [
            {
                key: copy.deepcopy(row.get(key))
                for key in ("town", "code", "slug", "value", "formatted", "year", "series", "normalized", "benchmarkValue", "parts")
                if key in row
            }
            for row in metric.get("rows") or []
        ],
    }


def test_source_backed_companions() -> None:
    site = effective_seed_after_openbdap()
    pairs = expected_pairs()
    before_surface = {
        metric_id: public_surface(site["metrics"][metric_id])
        for metric_id in pairs
    }
    baseline = {}
    for metric_id, intended in pairs.items():
        metric = site["metrics"][metric_id]
        baseline[metric_id] = {
            dimension: structural_base.acquired_evidence(metric, dimension)
            for dimension in matrix_core.DIMENSIONS
        }
        for dimension in intended:
            assert baseline[metric_id][dimension] is None, (
                metric_id,
                dimension,
                baseline[metric_id][dimension],
            )

    summary = enrichment.apply_enrichment(
        site,
        load(enrichment.LIA_PATH),
        load(enrichment.DEMOGRAPHY_PATH),
        load(enrichment.AGRICULTURE_PATH),
        load(enrichment.ASIA_PATH),
        load(enrichment.FRAME_PATH),
    )
    assert summary == {
        "metricsEnriched": 26,
        "rowsEnriched": 182,
        "openBdapScalePairs": 16,
        "censusPairs": 4,
        "agriculturePairs": 4,
        "businessPairs": 10,
        "pairsAcquired": 34,
    }

    for metric_id, intended in pairs.items():
        metric = site["metrics"][metric_id]
        for dimension in intended:
            evidence = structural_base.acquired_evidence(metric, dimension)
            assert evidence is not None, (metric_id, dimension)
            token = (
                "openBdapScaleCompanion"
                if metric_id in enrichment.OPENBDAP_TARGETS
                else "sourceBackedComponents"
            )
            assert token in evidence, (metric_id, dimension, evidence)

        for dimension in matrix_core.DIMENSIONS:
            if dimension in intended:
                continue
            observed = structural_base.acquired_evidence(metric, dimension)
            assert observed == baseline[metric_id][dimension], (
                metric_id,
                dimension,
                baseline[metric_id][dimension],
                observed,
            )

        assert public_surface(metric) == before_surface[metric_id], metric_id

    for metric_id in enrichment.OPENBDAP_TARGETS:
        rows = site["metrics"][metric_id]["rows"]
        assert len(rows) == 7
        for row in rows:
            ratio = row["ratioComponents"]
            companion = row["openBdapScaleCompanion"]
            assert companion["absolute"] == ratio["numerator"]["value"]
            assert companion["normalized"] == row["value"]
            openbdap._assert_close(
                float(row["value"]),
                openbdap._ratio_value(ratio),
                f"test {metric_id}/{row['town']}",
            )

    for metric_id in ("localEmployeesChange", "localUnitsChange"):
        for row in site["metrics"][metric_id]["rows"]:
            component = row["sourceBackedComponents"]
            assert component["transform"] == "pct_change"
            assert math.isclose(
                float(component["absolute"]),
                float(component["numerator"]) - float(component["denominator"]),
                rel_tol=0.0,
                abs_tol=1e-12,
            ), (metric_id, row["town"], component)

    assert sum(len(dimensions) for dimensions in pairs.values()) == 34


if __name__ == "__main__":
    test_source_backed_companions()
    print(
        "A3.5 source-backed regression passed: 34 coppie acquisite "
        "(16 OpenBDAP + 4 census + 4 agricoltura + 10 business), "
        "senza modificare il payload pubblico."
    )
