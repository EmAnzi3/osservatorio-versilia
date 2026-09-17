#!/usr/bin/env python3
"""Regression tests for A3.2 structural residual closure detectors."""
from __future__ import annotations

import enrichment_audit_matrix as audit


def test_structural_closure_patterns() -> None:
    nested_series = {
        "rows": [
            {
                "coverSeries": {
                    "artificialized": {
                        "years": [2007, 2010, 2013],
                        "ha": [10.0, 11.0, 12.0],
                        "pct": [20.0, 21.0, 22.0],
                    }
                }
            }
        ]
    }
    assert audit.acquired_evidence(nested_series, "serie_storica") == "rows.0.coverSeries.artificialized"

    one_point_nested = {
        "rows": [{"coverSeries": {"x": {"years": [2025], "ha": [10.0]}}}]
    }
    assert audit.acquired_evidence(one_point_nested, "serie_storica") is None

    composite_parts = {
        "meta": {"compositeType": "hydroNetworkProfile"},
        "rows": [
            {
                "parts": [
                    {"key": "full", "label": "Totale", "value": 12.0},
                    {"key": "managed", "label": "Gestito", "value": 8.0},
                ]
            }
        ],
    }
    assert audit.acquired_evidence(composite_parts, "categorie_specifiche") == "rows.0.parts"

    unlabeled_parts = {
        "rows": [{"parts": [{"key": "a"}, {"key": "b"}]}],
    }
    assert audit.acquired_evidence(unlabeled_parts, "categorie_specifiche") is None

    explicit_definitions = {
        "categoryDefinitions": [
            {"key": "a", "label": "Categoria A"},
            {"key": "b", "label": "Categoria B"},
        ]
    }
    assert audit.acquired_evidence(explicit_definitions, "categorie_specifiche") == "categoryDefinitions"

    ratio = {
        "meta": {"unit": "percent"},
        "rows": [
            {"value": 25.0, "count": 25, "population": 100},
            {"value": 20.0, "count": 40, "population": 200},
            {"value": 10.0, "count": 30, "population": 300},
        ],
    }
    assert (
        audit.acquired_evidence(ratio, "numeratore_denominatore")
        == "rows.*.count / rows.*.population × 100"
    )
    assert audit.acquired_evidence(ratio, "assoluto_normalizzato") == "rows.*.count + rows.*.value"

    per_thousand = {
        "meta": {"unit": "per1000"},
        "rows": [
            {"value": 5.0, "staffAt31Dec": 50, "residentPopulation": 10000},
            {"value": 8.0, "staffAt31Dec": 80, "residentPopulation": 10000},
        ],
    }
    assert (
        audit.acquired_evidence(per_thousand, "numeratore_denominatore")
        == "rows.*.staffAt31Dec / rows.*.residentPopulation × 1000"
    )

    single_row_coincidence = {
        "meta": {"unit": "percent"},
        "rows": [{"value": 50.0, "a": 1, "b": 2}],
    }
    assert audit.acquired_evidence(single_row_coincidence, "numeratore_denominatore") is None

    missing_denominator = {
        "meta": {"unit": "percent"},
        "rows": [
            {"value": 5.0, "netHeadcount": 1},
            {"value": 10.0, "netHeadcount": 2},
        ],
    }
    assert audit.acquired_evidence(missing_denominator, "numeratore_denominatore") is None

    absolute_and_share_parts = {
        "meta": {"compositeType": "landCoverProfile"},
        "rows": [
            {
                "parts": [
                    {"key": "forest", "value": 55.0, "unit": "percent", "ha": 550.0},
                    {"key": "water", "value": 5.0, "unit": "percent", "ha": 50.0},
                ]
            }
        ],
    }
    assert audit.acquired_evidence(absolute_and_share_parts, "assoluto_normalizzato") == "rows.0.parts"


if __name__ == "__main__":
    test_structural_closure_patterns()
    print("A3.2 structural closure regressions passed.")
