#!/usr/bin/env python3
"""Regression tests for A3.2 cross-metric companion evidence."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

from enrichment_companion_evidence import companion_acquired_evidence


def _root_with_contract(relationships: list[dict[str, object]]) -> Path:
    root = Path(tempfile.mkdtemp())
    data = root / "data"
    data.mkdir(parents=True)
    data.joinpath("enrichment-companion-contract.json").write_text(
        json.dumps({"schemaVersion": 1, "relationships": relationships}),
        encoding="utf-8",
    )
    return root


def test_companion_evidence() -> None:
    relationship = {
        "metricId": "population",
        "dimension": "eta",
        "companionMetricId": "ageDistribution",
        "relationship": "age_breakdown",
    }
    root = _root_with_contract([relationship])
    catalog = {
        "population": {"rows": [{"value": 100}]},
        "ageDistribution": {
            "rows": [
                {"age": "0-14", "value": 12},
                {"age": "15-64", "value": 63},
                {"age": "65+", "value": 25},
            ]
        },
    }

    evidence = companion_acquired_evidence(
        metric_id="population",
        dimension="eta",
        catalog=catalog,
        repo_root=root,
    ) or ""
    assert evidence.startswith("companion:age_breakdown:ageDistribution:")

    assert companion_acquired_evidence(
        metric_id="population",
        dimension="sesso",
        catalog=catalog,
        repo_root=root,
    ) is None

    no_age = dict(catalog)
    no_age["ageDistribution"] = {"rows": [{"value": 12}, {"value": 63}]}
    assert companion_acquired_evidence(
        metric_id="population",
        dimension="eta",
        catalog=no_age,
        repo_root=root,
    ) is None

    ratio_relationship = {
        "metricId": "rateMetric",
        "dimensions": ["assoluto_normalizzato", "numeratore_denominatore"],
        "relationship": "ratio_formula",
        "numeratorMetricId": "absoluteMetric",
        "denominatorMetricId": "population",
    }
    ratio_root = _root_with_contract([ratio_relationship])
    ratio_catalog = {
        "rateMetric": {
            "meta": {"unit": "per1000", "year": "2025"},
            "rows": [
                {"code": "001", "value": 50.0},
                {"code": "002", "value": 25.0},
            ],
        },
        "absoluteMetric": {
            "meta": {"unit": "number", "year": "2025"},
            "rows": [
                {"code": "001", "value": 100.0},
                {"code": "002", "value": 50.0},
            ],
        },
        "population": {
            "meta": {"unit": "number", "year": "2026"},
            "rows": [
                {"code": "001", "value": 2100, "series": {"years": [2025, 2026], "values": [2000, 2100]}},
                {"code": "002", "value": 2200, "series": {"years": [2025, 2026], "values": [2000, 2200]}},
            ],
        },
    }
    for dimension in ("assoluto_normalizzato", "numeratore_denominatore"):
        ratio_evidence = companion_acquired_evidence(
            metric_id="rateMetric",
            dimension=dimension,
            catalog=ratio_catalog,
            repo_root=ratio_root,
        ) or ""
        assert ratio_evidence.startswith(
            "companion:ratio_formula:absoluteMetric/population:2025:"
            "denominator=target_year:scale=1000:2/2"
        )

    current_relationship = {
        **ratio_relationship,
        "metricId": "currentRateMetric",
        "denominatorYearMode": "metric_current",
    }
    current_root = _root_with_contract([current_relationship])
    current_catalog = {
        **ratio_catalog,
        "currentRateMetric": {
            "meta": {"unit": "per1000", "year": "2025"},
            "rows": [
                {"code": "001", "value": 100.0 / 2100.0 * 1000.0},
                {"code": "002", "value": 50.0 / 2200.0 * 1000.0},
            ],
        },
    }
    current_evidence = companion_acquired_evidence(
        metric_id="currentRateMetric",
        dimension="numeratore_denominatore",
        catalog=current_catalog,
        repo_root=current_root,
    ) or ""
    assert "denominator=metric_current" in current_evidence

    series_change_relationship = {
        "metricId": "populationChange",
        "dimensions": ["assoluto_normalizzato", "numeratore_denominatore"],
        "relationship": "series_change_formula",
        "companionMetricId": "population",
        "startYear": "2019",
        "endYear": "2026",
    }
    series_change_root = _root_with_contract([series_change_relationship])
    series_change_catalog = {
        "populationChange": {
            "meta": {"unit": "percent", "year": "2019–2026"},
            "rows": [
                {"code": "001", "value": 10.0},
                {"code": "002", "value": -10.0},
            ],
        },
        "population": {
            "meta": {"unit": "number", "year": "2026"},
            "rows": [
                {"code": "001", "value": 110, "series": {"years": [2019, 2026], "values": [100, 110]}},
                {"code": "002", "value": 180, "series": {"years": [2019, 2026], "values": [200, 180]}},
            ],
        },
    }
    for dimension in ("assoluto_normalizzato", "numeratore_denominatore"):
        evidence = companion_acquired_evidence(
            metric_id="populationChange",
            dimension=dimension,
            catalog=series_change_catalog,
            repo_root=series_change_root,
        ) or ""
        assert evidence.startswith(
            "companion:series_change_formula:population:2019->2026:scale=100:2/2"
        )

    broken_change_catalog = dict(series_change_catalog)
    broken_change_catalog["populationChange"] = {
        **series_change_catalog["populationChange"],
        "rows": [{"code": "001", "value": 9.0}, {"code": "002", "value": -10.0}],
    }
    assert companion_acquired_evidence(
        metric_id="populationChange",
        dimension="numeratore_denominatore",
        catalog=broken_change_catalog,
        repo_root=series_change_root,
    ) is None

    parts_ratio_relationship = {
        "metricId": "dependencyIndices",
        "dimensions": ["eta", "assoluto_normalizzato", "numeratore_denominatore"],
        "relationship": "parts_ratio_formula",
        "companionMetricId": "ageDistribution",
        "numeratorParts": ["0–14", "65–79", "80–84", "85+"],
        "denominatorParts": ["15–19", "20–34", "35–49", "50–64"],
        "partSelectorField": "selectorLabel",
        "partValueField": "count",
    }
    parts_ratio_root = _root_with_contract([parts_ratio_relationship])
    parts_ratio_catalog = {
        "dependencyIndices": {
            "meta": {"unit": "per100", "year": "2026"},
            "rows": [
                {"code": "001", "value": 30.0 / 70.0 * 100.0},
                {"code": "002", "value": 75.0},
            ],
        },
        "ageDistribution": {
            "meta": {"unit": "percent", "year": "2026"},
            "rows": [
                {
                    "code": "001",
                    "parts": [
                        {"selectorLabel": "0–14", "count": 10},
                        {"selectorLabel": "15–19", "count": 10},
                        {"selectorLabel": "20–34", "count": 20},
                        {"selectorLabel": "35–49", "count": 20},
                        {"selectorLabel": "50–64", "count": 20},
                        {"selectorLabel": "65–79", "count": 10},
                        {"selectorLabel": "80–84", "count": 4},
                        {"selectorLabel": "85+", "count": 6},
                    ],
                },
                {
                    "code": "002",
                    "parts": [
                        {"selectorLabel": "0–14", "count": 20},
                        {"selectorLabel": "15–19", "count": 10},
                        {"selectorLabel": "20–34", "count": 20},
                        {"selectorLabel": "35–49", "count": 20},
                        {"selectorLabel": "50–64", "count": 10},
                        {"selectorLabel": "65–79", "count": 15},
                        {"selectorLabel": "80–84", "count": 5},
                        {"selectorLabel": "85+", "count": 5},
                    ],
                },
            ],
        },
    }
    for dimension in ("eta", "assoluto_normalizzato", "numeratore_denominatore"):
        evidence = companion_acquired_evidence(
            metric_id="dependencyIndices",
            dimension=dimension,
            catalog=parts_ratio_catalog,
            repo_root=parts_ratio_root,
        ) or ""
        assert evidence.startswith(
            "companion:parts_ratio_formula:ageDistribution:scale=100:2/2"
        )

    broken_parts_catalog = dict(parts_ratio_catalog)
    broken_parts_catalog["dependencyIndices"] = {
        **parts_ratio_catalog["dependencyIndices"],
        "rows": [{"code": "001", "value": 49.0}, {"code": "002", "value": 75.0}],
    }
    assert companion_acquired_evidence(
        metric_id="dependencyIndices",
        dimension="eta",
        catalog=broken_parts_catalog,
        repo_root=parts_ratio_root,
    ) is None

    broken_ratio_catalog = dict(ratio_catalog)
    broken_ratio_catalog["rateMetric"] = {
        **ratio_catalog["rateMetric"],
        "rows": [
            {"code": "001", "value": 49.0},
            {"code": "002", "value": 25.0},
        ],
    }
    assert companion_acquired_evidence(
        metric_id="rateMetric",
        dimension="numeratore_denominatore",
        catalog=broken_ratio_catalog,
        repo_root=ratio_root,
    ) is None

    assert companion_acquired_evidence(
        metric_id="rateMetric",
        dimension="sesso",
        catalog=ratio_catalog,
        repo_root=ratio_root,
    ) is None

    row_field_relationship = {
        "metricId": "staffTurnover",
        "dimension": "numeratore_denominatore",
        "relationship": "row_field_ratio_formula",
        "targetNumeratorField": "netTurnoverHeadcount",
        "denominatorMetricId": "staffAge",
        "denominatorField": "staffAt31Dec",
    }
    row_field_root = _root_with_contract([row_field_relationship])
    row_field_catalog = {
        "staffTurnover": {
            "meta": {"unit": "percent", "year": "2024"},
            "rows": [
                {"code": "001", "value": -1.0, "netTurnoverHeadcount": -1},
                {"code": "002", "value": 5.0, "netTurnoverHeadcount": 2},
            ],
        },
        "staffAge": {
            "meta": {"unit": "percent", "year": "2024"},
            "rows": [
                {"code": "001", "value": 40.0, "staffAt31Dec": 100},
                {"code": "002", "value": 35.0, "staffAt31Dec": 40},
            ],
        },
    }
    row_field_evidence = companion_acquired_evidence(
        metric_id="staffTurnover",
        dimension="numeratore_denominatore",
        catalog=row_field_catalog,
        repo_root=row_field_root,
    ) or ""
    assert row_field_evidence.startswith(
        "companion:row_field_ratio_formula:"
        "staffTurnover.netTurnoverHeadcount/staffAge.staffAt31Dec:"
        "scale=100:2/2"
    )

    broken_row_field_catalog = dict(row_field_catalog)
    broken_row_field_catalog["staffTurnover"] = {
        **row_field_catalog["staffTurnover"],
        "rows": [
            {"code": "001", "value": -1.0, "netTurnoverHeadcount": -1},
            {"code": "002", "value": 4.9, "netTurnoverHeadcount": 2},
        ],
    }
    assert companion_acquired_evidence(
        metric_id="staffTurnover",
        dimension="numeratore_denominatore",
        catalog=broken_row_field_catalog,
        repo_root=row_field_root,
    ) is None

    missing = {"population": catalog["population"]}
    try:
        companion_acquired_evidence(
            metric_id="population",
            dimension="eta",
            catalog=missing,
            repo_root=root,
        )
    except RuntimeError as exc:
        assert "Companion A3 assente" in str(exc)
    else:
        raise AssertionError("Missing companion must fail closed")


if __name__ == "__main__":
    test_companion_evidence()
    print("A3.2 companion evidence regressions passed.")
