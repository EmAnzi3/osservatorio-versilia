#!/usr/bin/env python3
from __future__ import annotations

import json
import tempfile
from pathlib import Path

from visualization_content_contract import validate_visualization_content_contract


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
                        "benchmark": {
                            "year": 2025,
                            "source": "Fonte",
                            "url": "https://example.test/",
                            "note": "Benchmark omogeneo.",
                            "tuscany": 50.0,
                            "italy": None,
                        },
                    },
                    "aggregate": {"value": 50.0, "label": "Versilia"},
                    "rows": [
                        {"town": "A", "value": 40.0},
                        {"town": "B", "value": None},
                        {"town": "C", "value": None, "notApplicable": True},
                    ],
                }
            }
        }
        path.write_text(json.dumps(payload), encoding="utf-8")
        report = validate_visualization_content_contract(path, contract_path)
        assert report["metrics"] == 1
        assert report["rows"] == 3
        assert report["explicitComparisonReference"] == 1
        assert report["fallbackComparisonReference"] == 0
        assert report["benchmarkMetrics"] == 1
        assert report["missingRows"] == 1
        assert report["notApplicableRows"] == 1

        payload["metrics"]["sample"]["meta"]["unit"] = "mystery-unit"
        path.write_text(json.dumps(payload), encoding="utf-8")
        try:
            validate_visualization_content_contract(path, contract_path)
        except AssertionError as exc:
            assert "Unità non governata" in str(exc)
        else:
            raise AssertionError("Unità sconosciuta non rifiutata")

    print("A4 visualization/content contract regression passed.")


if __name__ == "__main__":
    main()
