#!/usr/bin/env python3
"""Regression A3.5 lotto 6: storici source-backed e companion MEF."""
from __future__ import annotations

import copy
import json
import math
from pathlib import Path

import enrichment_audit_matrix_core as matrix_core
import enrichment_audit_matrix_structural_base as structural_base
import materialize_a3_5_historical_mef_companions as enrichment

ROOT = Path(__file__).resolve().parents[1]
SITE_PATH = ROOT / "data" / "site-data.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def expected_pairs() -> dict[str, set[str]]:
    return {
        "industryValueAddedShare": {"serie_storica", "categorie_specifiche"},
        "industryWorkerShare": {"serie_storica", "categorie_specifiche"},
        "localEmployeesChange": {"serie_storica"},
        "localUnitsChange": {"serie_storica"},
        "populationChange": {"serie_storica"},
        "rigidExpenditureShare": {"serie_storica"},
        "incomeSourceProfile": {"numeratore_denominatore", "assoluto_normalizzato"},
        "pensionIncomeShare": {"numeratore_denominatore", "assoluto_normalizzato"},
        "municipalIrpef": {"assoluto_normalizzato"},
    }


def public_surface(metric: dict) -> dict:
    return {
        "meta": copy.deepcopy(metric.get("meta")),
        "method": copy.deepcopy(metric.get("method")),
        "aggregate": copy.deepcopy(metric.get("aggregate")),
        "normalizedAggregate": copy.deepcopy(metric.get("normalizedAggregate")),
        "rows": [
            {
                key: copy.deepcopy(row.get(key))
                for key in (
                    "town", "code", "slug", "value", "formatted", "year", "series",
                    "normalized", "benchmarkValue", "parts", "componentSeries",
                    "economicScopes", "sexDimension", "foreignOrigins", "ageSexPyramid",
                )
                if key in row
            }
            for row in metric.get("rows") or []
        ],
    }


def test_historical_mef_companions() -> None:
    site = load(SITE_PATH)
    pairs = expected_pairs()
    assert sum(len(dimensions) for dimensions in pairs.values()) == 13

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
        load(enrichment.FRAME_MANIFEST_PATH),
        load(enrichment.ASIA_PATH),
        load(enrichment.DEMOGRAPHY_PATH),
        load(enrichment.BILANCI_PATH),
        load(enrichment.MEF_INCOME_PATH),
        load(enrichment.MUNICIPAL_IRPEF_PATH),
    )
    assert summary == {
        "metricsEnriched": 9,
        "historyPairs": 6,
        "businessCategoryPairs": 2,
        "mefPairs": 4,
        "municipalIrpefPairs": 1,
        "pairsAcquired": 13,
    }

    token_by_dimension = {
        "serie_storica": "a3History",
        "categorie_specifiche": "businessCategoryBreakdown",
    }
    for metric_id, intended in pairs.items():
        metric = site["metrics"][metric_id]
        for dimension in intended:
            evidence = structural_base.acquired_evidence(metric, dimension)
            assert evidence is not None, (metric_id, dimension)
            if dimension in token_by_dimension:
                assert token_by_dimension[dimension] in evidence, (metric_id, dimension, evidence)
            elif metric_id in {"incomeSourceProfile", "pensionIncomeShare"}:
                assert "mefScaleComponents" in evidence, (metric_id, dimension, evidence)
            else:
                assert "municipalIrpefScaleCompanion" in evidence, (metric_id, dimension, evidence)

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

    for metric_id in enrichment.HISTORY_TARGETS:
        for row in site["metrics"][metric_id]["rows"]:
            series = row["a3History"]["series"]
            assert len(series) >= 2
            assert [item["year"] for item in series] == sorted(item["year"] for item in series)
            assert math.isclose(
                float(series[-1]["value"]),
                float(row["value"]),
                rel_tol=0.0,
                abs_tol=1e-8,
            ), (metric_id, row["town"])

    for metric_id in enrichment.BUSINESS_CATEGORY_TARGETS:
        for row in site["metrics"][metric_id]["rows"]:
            categories = row["businessCategoryBreakdown"]["categories"]
            assert [item["key"] for item in categories] == ["industry", "services"]
            assert math.isclose(
                float(categories[0]["value"]),
                float(row["value"]),
                rel_tol=0.0,
                abs_tol=1e-10,
            )

    for metric_id in enrichment.MEF_RATIO_TARGETS:
        for row in site["metrics"][metric_id]["rows"]:
            component = row["mefScaleComponents"]
            expected = component["numerator"] / component["denominator"] * component["scale"]
            assert math.isclose(expected, component["normalized"], rel_tol=0.0, abs_tol=1e-10)
            assert math.isclose(component["normalized"], row["value"], rel_tol=0.0, abs_tol=1e-10)

    for row in site["metrics"][enrichment.MUNICIPAL_IRPEF_TARGET]["rows"]:
        component = row["municipalIrpefScaleCompanion"]
        assert component["scenarioIncome"] == 20000.0
        assert math.isclose(component["absolute"], row["value"], rel_tol=0.0, abs_tol=1e-10)
        assert math.isclose(
            component["normalized"],
            component["absolute"] / component["scenarioIncome"] * 100.0,
            rel_tol=0.0,
            abs_tol=1e-10,
        )


if __name__ == "__main__":
    test_historical_mef_companions()
    print(
        "A3.5 historical + MEF regression passed: 13 coppie acquisite "
        "(6 serie, 2 categorie business, 4 companion MEF, 1 addizionale IRPEF), "
        "senza modificare il payload pubblico."
    )
