#!/usr/bin/env python3
"""Regression tests for A3.2 structural residual closure detectors."""
from __future__ import annotations

import enrichment_audit_matrix as audit


def test_structural_closure_patterns() -> None:
    nested_series = {
        "rows": [{"coverSeries": {"artificialized": {"years": [2007, 2010, 2013], "ha": [10.0, 11.0, 12.0], "pct": [20.0, 21.0, 22.0]}}}]
    }
    assert audit.acquired_evidence(nested_series, "serie_storica") == "rows.0.coverSeries.artificialized"

    one_point_nested = {"rows": [{"coverSeries": {"x": {"years": [2025], "ha": [10.0]}}}]}
    assert audit.acquired_evidence(one_point_nested, "serie_storica") is None

    composite_parts = {"meta": {"compositeType": "hydroNetworkProfile"}, "rows": [{"parts": [{"key": "full", "label": "Totale", "value": 12.0}, {"key": "managed", "label": "Gestito", "value": 8.0}]}]}
    assert audit.acquired_evidence(composite_parts, "categorie_specifiche") == "rows.0.parts"

    unlabeled_parts = {"rows": [{"parts": [{"key": "a"}, {"key": "b"}]}]}
    assert audit.acquired_evidence(unlabeled_parts, "categorie_specifiche") is None

    explicit_definitions = {"categoryDefinitions": [{"key": "a", "label": "Categoria A"}, {"key": "b", "label": "Categoria B"}]}
    assert audit.acquired_evidence(explicit_definitions, "categorie_specifiche") == "categoryDefinitions"

    ratio = {"meta": {"unit": "percent"}, "rows": [{"value": 25.0, "count": 25, "population": 100}, {"value": 20.0, "count": 40, "population": 200}, {"value": 10.0, "count": 30, "population": 300}]}
    assert audit.acquired_evidence(ratio, "numeratore_denominatore") == "rows.*.count / rows.*.population × 100"
    assert audit.acquired_evidence(ratio, "assoluto_normalizzato") == "rows.*.count + rows.*.value"

    per_thousand = {"meta": {"unit": "per1000"}, "rows": [{"value": 5.0, "staffAt31Dec": 50, "residentPopulation": 10000}, {"value": 8.0, "staffAt31Dec": 80, "residentPopulation": 10000}]}
    assert audit.acquired_evidence(per_thousand, "numeratore_denominatore") == "rows.*.staffAt31Dec / rows.*.residentPopulation × 1000"

    single_row_coincidence = {"meta": {"unit": "percent"}, "rows": [{"value": 50.0, "a": 1, "b": 2}]}
    assert audit.acquired_evidence(single_row_coincidence, "numeratore_denominatore") is None

    missing_denominator = {"meta": {"unit": "percent"}, "rows": [{"value": 5.0, "netHeadcount": 1}, {"value": 10.0, "netHeadcount": 2}]}
    assert audit.acquired_evidence(missing_denominator, "numeratore_denominatore") is None

    absolute_and_share_parts = {"meta": {"compositeType": "landCoverProfile"}, "rows": [{"parts": [{"key": "forest", "value": 55.0, "unit": "percent", "ha": 550.0}, {"key": "water", "value": 5.0, "unit": "percent", "ha": 50.0}]}]}
    assert audit.acquired_evidence(absolute_and_share_parts, "assoluto_normalizzato") == "rows.0.parts"

    inherited_unit_parts = {
        "meta": {"unit": "per100k"},
        "rows": [
            {"parts": [{"key": "total", "value": 800.0, "numerator": 80, "denominator": 10000}]},
            {"parts": [{"key": "total", "value": 900.0, "numerator": 90, "denominator": 10000}]},
        ],
    }
    assert audit.acquired_evidence(inherited_unit_parts, "assoluto_normalizzato") == "rows.0.parts"

    exhaustive_distribution = {
        "meta": {"unit": "percent", "compositeType": "distribution"},
        "rows": [
            {"parts": [{"label": "A", "value": 25.0, "count": 25}, {"label": "B", "value": 75.0, "count": 75}]},
            {"parts": [{"label": "A", "value": 20.0, "count": 40}, {"label": "B", "value": 80.0, "count": 160}]},
        ],
    }
    assert audit.acquired_evidence(exhaustive_distribution, "numeratore_denominatore") == "rows.*.parts.*.count / sum(rows.*.parts.*.count)"

    parent_denominator = {
        "meta": {"unit": "percent", "compositeType": "staffAge"},
        "rows": [
            {"staffTotal": 100, "parts": [{"label": "55+", "value": 40.0, "count": 40, "unit": "percent"}]},
            {"staffTotal": 80, "parts": [{"label": "55+", "value": 50.0, "count": 40, "unit": "percent"}]},
        ],
    }
    assert "staffTotal" in (audit.acquired_evidence(parent_denominator, "numeratore_denominatore") or "")

    nested_accounting = {
        "meta": {"unit": "%"},
        "rows": [
            {"value": 7.37, "accounting": {"arrears": 348067.19, "issued": 4721245.44}},
            {"value": 8.56, "accounting": {"arrears": 4304930.64, "issued": 50285906.83}},
        ],
    }
    evidence = audit.acquired_evidence(nested_accounting, "numeratore_denominatore") or ""
    assert "accounting.arrears" in evidence and "accounting.issued" in evidence
    assert audit.acquired_evidence(nested_accounting, "assoluto_normalizzato") is not None

    density_parts = {
        "meta": {"unit": "km", "compositeType": "network"},
        "rows": [
            {"areaKm2": 10.0, "parts": [{"key": "length", "value": 50.0, "unit": "km"}, {"key": "density", "value": 5.0, "unit": "km_per_km2"}]},
            {"areaKm2": 20.0, "parts": [{"key": "length", "value": 60.0, "unit": "km"}, {"key": "density", "value": 3.0, "unit": "km_per_km2"}]},
        ],
    }
    assert audit.acquired_evidence(density_parts, "numeratore_denominatore") is not None
    assert audit.acquired_evidence(density_parts, "assoluto_normalizzato") is not None

    mapped_denominator = {
        "meta": {"unit": "percent", "compositeType": "landCover"},
        "rows": [
            {
                "totals": {"municipalAreaHa": 1000.0},
                "parts": [{"key": "forest", "value": 55.0, "ha": 550.0}],
            },
            {
                "totals": {"municipalAreaHa": 2000.0},
                "parts": [{"key": "forest", "value": 60.0, "ha": 1200.0}],
            },
        ],
    }
    map_evidence = audit.acquired_evidence(mapped_denominator, "numeratore_denominatore") or ""
    assert "municipalAreaHa" in map_evidence and ".ha" in map_evidence

    non_exhaustive_distribution = {
        "meta": {"unit": "percent", "compositeType": "distribution"},
        "rows": [
            {"parts": [{"label": "A", "value": 25.0, "count": 25}, {"label": "B", "value": 50.0, "count": 75}]},
            {"parts": [{"label": "A", "value": 20.0, "count": 40}, {"label": "B", "value": 70.0, "count": 160}]},
        ],
    }
    assert audit.acquired_evidence(non_exhaustive_distribution, "numeratore_denominatore") is None


if __name__ == "__main__":
    test_structural_closure_patterns()
    print("A3.2 structural closure regressions passed.")
