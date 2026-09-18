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
        "numeratorYearMode": "metric_current",
        "denominatorYearMode": "metric_current",
    }
    current_root = _root_with_contract([current_relationship])
    current_catalog = {
        **ratio_catalog,
        "absoluteMetric": {
            "meta": {"unit": "number", "year": "2024"},
            "rows": [
                {"code": "001", "value": 100.0},
                {"code": "002", "value": 50.0},
            ],
        },
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
    assert "numerator=metric_current" in current_evidence
    assert "denominator=metric_current" in current_evidence

    average_population_relationship = {
        "metricId": "mobilityRate",
        "dimension": "numeratore_denominatore",
        "relationship": "part_count_average_population_formula",
        "companionMetricId": "population",
        "numeratorPartLabel": "Saldo",
        "partSelectorField": "label",
        "partCountField": "count",
        "populationYearMode": "target_and_next_average",
    }
    average_population_root = _root_with_contract([average_population_relationship])
    average_population_catalog = {
        "mobilityRate": {
            "meta": {"unit": "per1000", "year": "2024"},
            "rows": [
                {"code": "001", "value": 10.0 / 1050.0 * 1000.0, "parts": [{"label": "Saldo", "count": 10}]},
                {"code": "002", "value": -5.0 / 2050.0 * 1000.0, "parts": [{"label": "Saldo", "count": -5}]},
            ],
        },
        "population": {
            "meta": {"unit": "number", "year": "2025"},
            "rows": [
                {"code": "001", "value": 1100, "series": {"years": [2024, 2025], "values": [1000, 1100]}},
                {"code": "002", "value": 2100, "series": {"years": [2024, 2025], "values": [2000, 2100]}},
            ],
        },
    }
    average_population_evidence = companion_acquired_evidence(
        metric_id="mobilityRate",
        dimension="numeratore_denominatore",
        catalog=average_population_catalog,
        repo_root=average_population_root,
    ) or ""
    assert average_population_evidence.startswith(
        "companion:part_count_average_population_formula:Saldo/"
        "population:2024->2025:scale=1000:2/2"
    )

    broken_average_population_catalog = {
        **average_population_catalog,
        "mobilityRate": {
            **average_population_catalog["mobilityRate"],
            "rows": [
                {"code": "001", "value": 9.0, "parts": [{"label": "Saldo", "count": 10}]},
                average_population_catalog["mobilityRate"]["rows"][1],
            ],
        },
    }
    assert companion_acquired_evidence(
        metric_id="mobilityRate",
        dimension="numeratore_denominatore",
        catalog=broken_average_population_catalog,
        repo_root=average_population_root,
    ) is None

    normalized_companion_relationship = {
        "metricId": "absoluteSource",
        "dimension": "assoluto_normalizzato",
        "relationship": "normalized_companion_formula",
        "normalizedMetricId": "normalizedRate",
        "denominatorMetricId": "population",
        "denominatorYearMode": "target_year",
    }
    normalized_companion_root = _root_with_contract([normalized_companion_relationship])
    normalized_companion_catalog = {
        "absoluteSource": {
            "meta": {"unit": "number", "year": "2025"},
            "rows": [
                {"code": "001", "value": 100.0},
                {"code": "002", "value": 50.0},
            ],
        },
        "normalizedRate": {
            "meta": {"unit": "per1000", "year": "2025"},
            "rows": [
                {"code": "001", "value": 50.0},
                {"code": "002", "value": 25.0},
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
    normalized_companion_evidence = companion_acquired_evidence(
        metric_id="absoluteSource",
        dimension="assoluto_normalizzato",
        catalog=normalized_companion_catalog,
        repo_root=normalized_companion_root,
    ) or ""
    assert normalized_companion_evidence.startswith(
        "companion:normalized_companion_formula:normalizedRate/population:"
        "2025:denominator=target_year:scale=1000:2/2"
    )

    current_normalized_relationship = {
        **normalized_companion_relationship,
        "metricId": "absoluteCurrent",
        "normalizedMetricId": "normalizedCurrent",
        "denominatorYearMode": "metric_current",
    }
    current_normalized_root = _root_with_contract([current_normalized_relationship])
    current_normalized_catalog = {
        **normalized_companion_catalog,
        "absoluteCurrent": {
            "meta": {"unit": "number", "year": "2025"},
            "rows": [
                {"code": "001", "value": 100.0},
                {"code": "002", "value": 50.0},
            ],
        },
        "normalizedCurrent": {
            "meta": {"unit": "per1000", "year": "2025"},
            "rows": [
                {"code": "001", "value": 100.0 / 2100.0 * 1000.0},
                {"code": "002", "value": 50.0 / 2200.0 * 1000.0},
            ],
        },
    }
    current_normalized_evidence = companion_acquired_evidence(
        metric_id="absoluteCurrent",
        dimension="assoluto_normalizzato",
        catalog=current_normalized_catalog,
        repo_root=current_normalized_root,
    ) or ""
    assert "denominator=metric_current" in current_normalized_evidence

    broken_normalized_catalog = {
        **normalized_companion_catalog,
        "normalizedRate": {
            **normalized_companion_catalog["normalizedRate"],
            "rows": [
                {"code": "001", "value": 49.0},
                normalized_companion_catalog["normalizedRate"]["rows"][1],
            ],
        },
    }
    assert companion_acquired_evidence(
        metric_id="absoluteSource",
        dimension="assoluto_normalizzato",
        catalog=broken_normalized_catalog,
        repo_root=normalized_companion_root,
    ) is None

    fields_relationship = {
        "metricId": "staffTurnover",
        "dimension": "numeratore_denominatore",
        "relationship": "target_fields_ratio_formula",
        "targetNumeratorFields": ["netHires", "netCessations"],
        "targetNumeratorOperation": "difference",
        "targetNumeratorCheckField": "netTurnoverHeadcount",
        "companionMetricId": "staffAge",
        "companionDenominatorField": "staffAt31Dec",
    }
    fields_root = _root_with_contract([fields_relationship])
    fields_catalog = {
        "staffTurnover": {
            "meta": {"unit": "percent", "year": "2024"},
            "rows": [
                {
                    "code": "001",
                    "value": -1.0 / 87.0 * 100.0,
                    "netHires": 2,
                    "netCessations": 3,
                    "netTurnoverHeadcount": -1,
                },
                {
                    "code": "002",
                    "value": 19.0 / 412.0 * 100.0,
                    "netHires": 41,
                    "netCessations": 22,
                    "netTurnoverHeadcount": 19,
                },
            ],
        },
        "staffAge": {
            "meta": {"unit": "percent", "year": "2024"},
            "rows": [
                {"code": "001", "staffAt31Dec": 87},
                {"code": "002", "staffAt31Dec": 412},
            ],
        },
    }
    fields_evidence = companion_acquired_evidence(
        metric_id="staffTurnover",
        dimension="numeratore_denominatore",
        catalog=fields_catalog,
        repo_root=fields_root,
    ) or ""
    assert fields_evidence.startswith(
        "companion:target_fields_ratio_formula:netHires-netCessations/"
        "staffAge.staffAt31Dec:scale=100:2/2"
    )

    broken_fields_catalog = {
        **fields_catalog,
        "staffTurnover": {
            **fields_catalog["staffTurnover"],
            "rows": [
                {
                    "code": "001",
                    "value": 0.0,
                    "netHires": 2,
                    "netCessations": 3,
                    "netTurnoverHeadcount": -1,
                },
                fields_catalog["staffTurnover"]["rows"][1],
            ],
        },
    }
    assert companion_acquired_evidence(
        metric_id="staffTurnover",
        dimension="numeratore_denominatore",
        catalog=broken_fields_catalog,
        repo_root=fields_root,
    ) is None

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
