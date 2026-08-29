#!/usr/bin/env python3
"""Contratto dati/UI per i confronti della sezione Investimenti e opere."""
from __future__ import annotations

import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def close(actual: float, expected: float) -> None:
    assert math.isclose(actual, expected, rel_tol=0, abs_tol=1e-9), (actual, expected)


def main() -> None:
    data = json.loads((ROOT / "data" / "site-data.json").read_text(encoding="utf-8"))
    metrics = data["metrics"]
    towns = {town["code"]: town for town in data["towns"]}
    details = data["details"]

    total_population = sum(town["population"][-1] for town in towns.values())
    public_works_total = sum(details[code]["government"]["publicWorksValue"] for code in towns)
    pnrr_funding_total = sum(details[code]["government"]["pnrrFunding"] for code in towns)
    pnrr_concluded = sum(details[code]["government"]["pnrrConcluded"] for code in towns)
    pnrr_projects = sum(details[code]["government"]["pnrrProjects"] for code in towns)

    close(metrics["publicWorks"]["aggregate"]["value"], public_works_total / total_population)
    close(metrics["pnrrFunding"]["aggregate"]["value"], pnrr_funding_total / total_population)
    close(metrics["pnrrConcluded"]["aggregate"]["value"], pnrr_concluded / pnrr_projects * 100)
    assert (public_works_total, total_population) == (223_384_943, 158_520)
    assert math.isclose(pnrr_funding_total, 36_683_107.64, abs_tol=0.001)
    assert (pnrr_concluded, pnrr_projects) == (74, 101)

    for key in ("publicWorks", "pnrrFunding", "pnrrConcluded"):
        meta = metrics[key]["meta"]
        assert meta["comparisonReference"] == "aggregate"
        assert "media semplice" in meta["comparisonNote"]
    assert metrics["publicWorks"]["meta"]["comparisonDifference"] == "absolute"
    assert metrics["pnrrFunding"]["meta"]["comparisonDifference"] == "absolute"
    assert metrics["pnrrConcluded"]["meta"]["comparisonDifference"] == "percentagePoints"

    visual = (ROOT / "assets" / "visual-grammar.js").read_text(encoding="utf-8")
    assert "comparisonReference === 'aggregate'" in visual
    assert "comparisonDifference === 'absolute'" in visual
    assert "metric?.meta?.comparisonNote" in visual
    print("Investimenti e opere: aggregati e grammatica del confronto verificati su 7/7 Comuni.")


if __name__ == "__main__":
    main()
