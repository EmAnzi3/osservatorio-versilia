#!/usr/bin/env python3
"""Regression tests for the A3.4 enrichment backlog."""
from __future__ import annotations

import json

import enrichment_audit_matrix_core as matrix_core
import enrichment_backlog as backlog
import enrichment_source_audit as source_audit


def _profile(publisher: str) -> dict:
    return {
        "publisher": publisher,
        "frequency": "annual",
        "frequencyLabel": "Annuale",
        "expectedRelease": "Annuale",
        "acquisitionMethod": "Fixture acquisition",
        "licenseName": "Fixture license",
        "licenseUrl": "https://example.test/license",
    }


def fixtures():
    metrics = ("alpha", "beta", "gamma")
    profile_by_metric = {
        "alpha": "profile-a",
        "beta": "profile-a",
        "gamma": "profile-b",
    }
    special = {
        ("alpha", "serie_storica"): ("AVAILABLE_MISSING", "source_profile"),
        ("beta", "serie_storica"): ("AVAILABLE_MISSING", "source_profile"),
        ("alpha", "eta"): ("AVAILABLE_MISSING", "metric_override"),
        ("gamma", "benchmark_toscana_italia"): ("AVAILABLE_MISSING", "metric_override"),
    }

    rows = []
    counts = {state: 0 for state in matrix_core.FINAL_STATES}
    for metric_id in metrics:
        for dimension in matrix_core.DIMENSIONS:
            state, origin = special.get(
                (metric_id, dimension),
                ("ACQUIRED", "catalog_structure"),
            )
            counts[state] += 1
            rows.append(
                {
                    "metricId": metric_id,
                    "sourceUrl": f"https://example.test/{metric_id}",
                    "sourceProfileId": profile_by_metric[metric_id],
                    "dimension": dimension,
                    "state": state,
                    "evidence": f"fixture:{metric_id}:{dimension}",
                    "sourceReference": (
                        f"https://example.test/{profile_by_metric[metric_id]}/{dimension}"
                        if state == "AVAILABLE_MISSING"
                        else ""
                    ),
                    "classificationOrigin": origin,
                }
            )

    matrix = {
        "schemaVersion": 1,
        "generatedFrom": {"catalogVersion": "v-test", "catalogUpdated": "today"},
        "dimensions": list(matrix_core.DIMENSIONS),
        "summary": {
            "publicMetricCount": len(metrics),
            "dimensionCount": len(matrix_core.DIMENSIONS),
            "pairCount": len(rows),
            "classifiedPairCount": len(rows),
            "unclassifiedPairCount": 0,
            "sourceProfileCount": 2,
            **{f"state_{state}": counts[state] for state in sorted(counts)},
        },
        "rows": rows,
    }
    registry = {
        "sourceProfiles": {
            "profile-a": _profile("Fixture A"),
            "profile-b": _profile("Fixture B"),
        }
    }
    audit = source_audit.build_source_audit(matrix, registry)
    return matrix, audit


def test_backlog_covers_every_available_missing_once() -> None:
    matrix, audit = fixtures()
    payload = backlog.build_backlog(matrix, audit)
    assert payload["summary"]["availableMissingPairCount"] == 4
    assert payload["summary"]["bundleCount"] == 3

    bundles = {
        (item["profileId"], item["dimension"]): item
        for item in payload["bundles"]
    }
    history = bundles[("profile-a", "serie_storica")]
    assert history["pairCount"] == 2
    assert history["metricIds"] == ["alpha", "beta"]
    assert history["informationValuePoints"] == 10
    assert history["costPoints"] == 2
    assert history["rank"] == 1

    age = bundles[("profile-a", "eta")]
    assert age["acquiredSameDimensionCount"] == 1
    assert age["costPoints"] == 3

    benchmark = bundles[("profile-b", "benchmark_toscana_italia")]
    assert benchmark["costPoints"] == 4

    covered = {
        (item["profileId"], pair["metricId"], item["dimension"])
        for item in payload["bundles"]
        for pair in item["pairs"]
    }
    expected = {
        (
            row["sourceProfileId"],
            row["metricId"],
            row["dimension"],
        )
        for row in matrix["rows"]
        if row["state"] == "AVAILABLE_MISSING"
    }
    assert covered == expected


def test_backlog_rejects_a3_source_audit_drift() -> None:
    matrix, audit = fixtures()
    audit["profiles"][0]["availableMissing"].pop()
    try:
        backlog.build_backlog(matrix, audit)
    except RuntimeError as exc:
        assert "divergenza" in str(exc) or "non allineati" in str(exc)
    else:
        raise AssertionError("A3.4 deve rifiutare un audit A3.3 incompleto")


def test_backlog_is_reproducible() -> None:
    matrix, audit = fixtures()
    payload = backlog.build_backlog(matrix, audit)
    backlog.validate_backlog(payload, matrix, audit)
    round_tripped = json.loads(json.dumps(payload))
    backlog.validate_backlog(round_tripped, matrix, audit)
    assert set(round_tripped["rubric"]["costScale"]) == {"1", "2", "3", "4", "5"}
    markdown = backlog.render_markdown(payload)
    assert "Backlog ordinato" in markdown
    assert "profile-a" in markdown
    assert "priorityIndex" in payload["rubric"]["formula"]


if __name__ == "__main__":
    test_backlog_covers_every_available_missing_once()
    test_backlog_rejects_a3_source_audit_drift()
    test_backlog_is_reproducible()
    print("A3.4 enrichment backlog regression passed.")
