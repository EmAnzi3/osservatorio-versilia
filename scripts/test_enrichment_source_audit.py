#!/usr/bin/env python3
"""Regression tests for the A3.3 source-by-source audit."""
from __future__ import annotations

import enrichment_audit_matrix_core as matrix_core
import enrichment_source_audit as audit


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
    rows = []
    special = {
        ("alpha", "eta"): "AVAILABLE_MISSING",
        ("alpha", "categorie_specifiche"): "SOURCE_UNAVAILABLE",
        ("beta", "sesso"): "NOT_APPLICABLE",
    }
    profile_by_metric = {"alpha": "profile-a", "beta": "profile-b"}
    counts = {state: 0 for state in matrix_core.FINAL_STATES}
    for metric_id in ("alpha", "beta"):
        for dimension in matrix_core.DIMENSIONS:
            state = special.get((metric_id, dimension), "ACQUIRED")
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
                        f"https://example.test/{metric_id}/dictionary"
                        if state in {"AVAILABLE_MISSING", "SOURCE_UNAVAILABLE"}
                        else ""
                    ),
                    "classificationOrigin": (
                        "catalog_structure" if state == "ACQUIRED" else "metric_override"
                    ),
                }
            )

    matrix = {
        "schemaVersion": 1,
        "generatedFrom": {"catalogVersion": "v-test", "catalogUpdated": "today"},
        "dimensions": list(matrix_core.DIMENSIONS),
        "summary": {
            "publicMetricCount": 2,
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
            "unused-profile": _profile("Unused fixture"),
        }
    }
    return matrix, registry


def test_source_audit_covers_matrix_by_profile() -> None:
    matrix, registry = fixtures()
    payload = audit.build_source_audit(matrix, registry)
    summary = payload["summary"]
    assert summary["publicMetricCount"] == 2
    assert summary["sourceProfileCount"] == 2
    assert summary["registryProfileCount"] == 3
    assert summary["unusedRegistryProfileCount"] == 1
    assert summary["pairCount"] == 2 * len(matrix_core.DIMENSIONS)
    assert summary["availableMissingPairCount"] == 1
    assert summary["sourceUnavailablePairCount"] == 1
    assert summary["notApplicablePairCount"] == 1
    assert summary["acquiredPairCount"] == 15
    assert payload["unusedRegistryProfiles"] == ["unused-profile"]

    by_id = {item["profileId"]: item for item in payload["profiles"]}
    alpha = by_id["profile-a"]
    assert alpha["metricIds"] == ["alpha"]
    assert alpha["pairCount"] == len(matrix_core.DIMENSIONS)
    assert alpha["availableMissing"][0]["dimension"] == "eta"
    assert alpha["sourceUnavailable"][0]["dimension"] == "categorie_specifiche"

    markdown = audit.render_markdown(payload)
    assert "profile-a" in markdown
    assert "AVAILABLE_MISSING" in markdown
    assert "alpha x eta" in markdown
    assert "Fixture license" in markdown
    assert "https://example.test/license" in markdown
    assert "metric_override=" in markdown


def test_source_audit_rejects_missing_profile_metadata() -> None:
    matrix, registry = fixtures()
    registry["sourceProfiles"]["profile-a"].pop("expectedRelease")
    try:
        audit.build_source_audit(matrix, registry)
    except RuntimeError as exc:
        assert "Metadati fonte incompleti" in str(exc)
        assert "expectedRelease" in str(exc)
    else:
        raise AssertionError("A3.3 deve rifiutare profili fonte con metadati incompleti")


def test_source_audit_rejects_metric_on_multiple_profiles() -> None:
    matrix, registry = fixtures()
    for row in matrix["rows"]:
        if row["metricId"] == "alpha" and row["dimension"] == "eta":
            row["sourceProfileId"] = "profile-b"
            break
    try:
        audit.build_source_audit(matrix, registry)
    except RuntimeError as exc:
        assert "più profili fonte" in str(exc)
    else:
        raise AssertionError("A3.3 deve rifiutare una metrica risolta su più profili")


if __name__ == "__main__":
    test_source_audit_covers_matrix_by_profile()
    test_source_audit_rejects_missing_profile_metadata()
    test_source_audit_rejects_metric_on_multiple_profiles()
    print("A3.3 source audit regression passed.")
