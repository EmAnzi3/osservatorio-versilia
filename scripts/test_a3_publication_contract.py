#!/usr/bin/env python3
"""Derived regression gate: ACQUIRED A3 history/benchmark must reach the public UI contract."""
from __future__ import annotations

import json
from pathlib import Path

import a3_publication_gap_audit as publication
import enrichment_audit_matrix as enrichment

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
DATA = DIST / "data" / "site-data.json"
REGISTRY = DIST / "data" / "source-registry.json"


def main() -> None:
    data = publication.load(DATA)
    registry = publication.load(REGISTRY)
    matrix = enrichment.build_matrix(data, registry)
    enrichment.validate_matrix(matrix, require_complete=True)
    if matrix["summary"]["publicMetricCount"] != len(data.get("metrics", {})):
        raise RuntimeError("A3 publication contract: matrice e catalogo effettivo non allineati")
    report = publication.build_report(data, matrix, DIST)
    publication.validate_report(report)
    histories = report["summary"]["serie_storica"]
    benchmarks = report["summary"]["benchmark_toscana_italia"]
    print(
        "A3 publication contract: "
        f"storici {histories['public']}/{histories['acquired']} pubblici · "
        f"benchmark {benchmarks['public']}/{benchmarks['acquired']} pubblici."
    )


if __name__ == "__main__":
    main()
