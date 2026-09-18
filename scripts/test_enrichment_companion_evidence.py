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
