#!/usr/bin/env python3
from __future__ import annotations

import copy
import json
import tempfile
from pathlib import Path

from visualization_content_contract import (
    validate_visual_runtime_contract,
    validate_visualization_content_contract,
)


def expect_failure(payload: dict, path: Path, contract_path: Path, needle: str) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")
    try:
        validate_visualization_content_contract(path, contract_path)
    except AssertionError as exc:
        assert needle in str(exc), (needle, str(exc))
    else:
        raise AssertionError(f"Regressione non intercettata: {needle}")


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    contract_path = root / "ci" / "visualization-content-contract.json"

    with tempfile.TemporaryDirectory(prefix="a4-contract-") as tmp:
        path = Path(tmp) / "catalog.json"
        payload = {
            "metrics": {
                "sample": {
                    "meta": {
                        "unit": "percent",
                        "polarity": "neutral",
                        "comparisonReference": "aggregate",
                        "comparisonDifference": "percentagePoints",
                        "normalized": {
                            "unit": "per1000",
                            "label": "Tasso",
                            "description": "Valore normalizzato.",
                        },
                        "benchmark": {
                            "year": 2025,
                            "source": "Fonte",
                            "url": "https://example.test/",
                            "note": "Benchmark omogeneo.",
                            "tuscany": 50.0,
                            "italy": None,
                        },
                    },
                    "aggregate": {
                        "value": 86.36363636363636,
                        "label": "Valore ponderato Versilia",
                        "parts": [{"label": "Quota", "value": 86.36, "unit": "percent"}],
                    },
                    "rows": [
                        {
                            "town": "A",
                            "value": 50.0,
                            "normalized": {"value": 500.0, "unit": "per1000"},
                            "parts": [{"label": "Quota", "value": 50.0, "unit": "percent"}],
                            "ratioComponents": {
                                "scale": 100.0,
                                "numerator": {"value": 50.0, "unit": "number"},
                                "denominator": {"value": 100.0, "unit": "number"},
                            },
                        },
                        {
                            "town": "B",
                            "value": 90.0,
                            "normalized": {"value": 900.0, "unit": "per1000"},
                            "parts": [{"label": "Quota", "value": 90.0, "unit": "percent"}],
                            "ratioComponents": {
                                "scale": 100.0,
                                "numerator": {"value": 900.0, "unit": "number"},
                                "denominator": {"value": 1000.0, "unit": "number"},
                            },
                        },
                        {"town": "C", "value": None},
                        {"town": "D", "value": None, "notApplicable": True},
                    ],
                }
            }
        }
        path.write_text(json.dumps(payload), encoding="utf-8")
        report = validate_visualization_content_contract(path, contract_path)
        assert report["metrics"] == 1
        assert report["rows"] == 4
        assert report["explicitComparisonReference"] == 1
        assert report["fallbackComparisonReference"] == 0
        assert report["benchmarkMetrics"] == 1
        assert report["missingRows"] == 1
        assert report["notApplicableRows"] == 1
        assert report["ratioComponentMetrics"] == 1
        assert report["ratioComponentRows"] == 2
        assert report["aggregateShapes"]["other"] == 1

        bad = copy.deepcopy(payload)
        bad["metrics"]["sample"]["meta"].pop("comparisonReference")
        expect_failure(
            bad,
            path,
            contract_path,
            "Rapporto ponderato senza comparisonReference=aggregate",
        )

        bad = copy.deepcopy(payload)
        bad["metrics"]["sample"]["aggregate"]["value"] = 70.0
        expect_failure(bad, path, contract_path, "Aggregato ponderato sample")

        bad = copy.deepcopy(payload)
        bad["metrics"]["sample"]["rows"][0]["ratioComponents"]["denominator"]["value"] = 0.0
        expect_failure(bad, path, contract_path, "Denominatore nullo sample/A")

        bad = copy.deepcopy(payload)
        bad["metrics"]["sample"]["meta"]["unit"] = "mystery-unit"
        expect_failure(bad, path, contract_path, "Unità non governata")

        bad = copy.deepcopy(payload)
        bad["metrics"]["sample"]["rows"][0]["normalized"]["unit"] = "per100"
        expect_failure(bad, path, contract_path, "Unità normalizzata incoerente")

    runtime = validate_visual_runtime_contract(root / "assets" / "visual-grammar.js")
    assert len(runtime) >= 8
    print(
        "A4 visualization/content contract regression passed: "
        "unità, runtime, fallback e rapporti ponderati governati."
    )


if __name__ == "__main__":
    main()
