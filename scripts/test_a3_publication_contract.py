#!/usr/bin/env python3
"""Derived regression gate: ACQUIRED A3 history/benchmark must reach the public UI contract."""
from __future__ import annotations

import copy
import json
from pathlib import Path

import a3_publication_gap_audit as publication
import enrichment_audit_matrix as enrichment

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
DATA = DIST / "data" / "site-data.json"
REGISTRY = DIST / "data" / "source-registry.json"


def check_demographic_component_guards(data: dict, runtime: str) -> None:
    # Derive a component-only family from the real public catalog; no metric inventory.
    metric = next(metric for metric in data["metrics"].values()
                  if metric.get("meta", {}).get("compositeType") == "demographicBreakdown"
                  and not publication._generic_history(metric)
                  and publication._demographic_component_history(metric, runtime))
    component = publication._demographic_component_history(metric, runtime)
    assert component is not None
    original = copy.deepcopy(metric)
    assert publication._history_status("syntheticMetricWithoutRuntimeLiteral", metric, "", DIST, runtime)[0] == "SPECIAL_ROUTE_RENDERED"
    assert metric == original, "publication audit must preserve null default histories"

    def rejects(label: str, candidate: dict, candidate_runtime: str = runtime) -> None:
        assert publication._demographic_component_history(candidate, candidate_runtime) is None, label
        assert publication._history_status("syntheticMetricWithoutRuntimeLiteral", candidate, "", DIST, candidate_runtime)[0] not in publication.PUBLIC_STATUSES, label

    missing = copy.deepcopy(metric)
    next(part for part in missing["rows"][0]["parts"] if part["key"] == component)["series"] = None
    rejects("one town lacks acquired component history", missing)
    missing = copy.deepcopy(metric)
    missing["rows"].pop()
    rejects("missing town", missing)
    duplicate = copy.deepcopy(metric)
    duplicate["rows"][0]["code"] = duplicate["rows"][1]["code"]
    rejects("duplicate town code", duplicate)
    missing = copy.deepcopy(metric)
    missing["meta"]["ageOptions"] = []
    rejects("missing age selector options", missing)
    mismatch = copy.deepcopy(metric)
    next(part for part in mismatch["rows"][0]["parts"] if part["key"] == component)["ageKey"] = "unsupported"
    rejects("unsupported native component age", mismatch)
    disjoint = copy.deepcopy(metric)
    next(part for part in disjoint["rows"][0]["parts"] if part["key"] == component)["series"]["years"] = list(range(1900, 1900 + len(next(part for part in disjoint["rows"][0]["parts"] if part["key"] == component)["series"]["years"])))
    rejects("no common native years", disjoint)
    for token in ("compositeChoiceMetric", "currentCompositeChoice", "hasComponentHistory", "data-demographic-age", "data-demographic-gender", "part.series"):
        rejects("unsupported runtime: " + token, copy.deepcopy(metric), runtime.replace(token, "removedContractToken"))
    incompatible = copy.deepcopy(metric)
    incompatible["meta"]["compositeType"] = "distribution"
    rejects("different composite family", incompatible)
    print("A3 demographic publication guards: component-only route and 13 negative cases PASS.")


def main() -> None:
    data = publication.load(DATA)
    check_demographic_component_guards(data, publication._runtime_corpus(DIST))
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
