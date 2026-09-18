#!/usr/bin/env python3
"""Regression tests for A3.2 cross-metric companion evidence."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

from enrichment_companion_evidence import companion_acquired_evidence


def _root_with_contract(relationships: list[dict[str, str]]) -> Path:
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
