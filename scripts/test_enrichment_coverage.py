#!/usr/bin/env python3
from __future__ import annotations

import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import enrichment_coverage as coverage


def row(metric: str, dimension: str, profile: str, state: str) -> dict:
    return {
        "metricId": metric,
        "dimension": dimension,
        "sourceProfileId": profile,
        "state": state,
    }


def main() -> None:
    rows = [
        row("a", "serie_storica", "p1", "ACQUIRED"),
        row("b", "serie_storica", "p1", "AVAILABLE_MISSING"),
        row("c", "serie_storica", "p2", "SOURCE_UNAVAILABLE"),
        row("d", "sesso", "p2", "NOT_APPLICABLE"),
        row("e", "sesso", "p2", "ACQUIRED"),
        row("f", "sesso", "p2", "ACQUIRED"),
    ]
    matrix = {
        "summary": {
            "publicMetricCount": 6,
            "sourceProfileCount": 2,
            "dimensionCount": 2,
            "pairCount": 6,
            "classifiedPairCount": 6,
            "unclassifiedPairCount": 0,
        },
        "rows": rows,
    }
    report = coverage.build_coverage(matrix)
    summary = report["summary"]
    assert summary["acquiredPairCount"] == 3
    assert summary["availableMissingPairCount"] == 1
    assert summary["eligiblePairCount"] == 4
    assert math.isclose(summary["coveragePercent"], 75.0)
    assert summary["sourceUnavailablePairCount"] == 1
    assert summary["notApplicablePairCount"] == 1
    assert summary["totalPairCount"] == 6

    dimensions = {item["dimension"]: item for item in report["dimensions"]}
    assert dimensions["serie_storica"]["acquiredPairCount"] == 1
    assert dimensions["serie_storica"]["availableMissingPairCount"] == 1
    assert math.isclose(dimensions["serie_storica"]["coveragePercent"], 50.0)
    assert dimensions["sesso"]["acquiredPairCount"] == 2
    assert dimensions["sesso"]["availableMissingPairCount"] == 0
    assert math.isclose(dimensions["sesso"]["coveragePercent"], 100.0)

    profiles = {item["sourceProfileId"]: item for item in report["sourceProfiles"]}
    assert profiles["p1"]["eligiblePairCount"] == 2
    assert profiles["p2"]["eligiblePairCount"] == 2

    markdown = coverage.render_markdown(report)
    assert "Non è un voto di qualità" in markdown
    assert "75.0%" in markdown
    print("A3.6 enrichment coverage regression passed.")


if __name__ == "__main__":
    main()
