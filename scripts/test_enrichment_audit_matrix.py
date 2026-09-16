#!/usr/bin/env python3
"""Regression tests for the A3.2 enrichment matrix contract."""
from __future__ import annotations

import enrichment_audit_matrix as audit


def fixtures():
    data = {
        "version": "v-test",
        "updated": "16 settembre 2026",
        "metrics": {
            "alpha": {
                "sourceUrl": "https://example.test/a.csv",
                "rows": [
                    {
                        "town": "Massarosa",
                        "series": [
                            {"year": 2024, "value": 10},
                            {"year": 2025, "value": 12},
                        ],
                        "numerator": 12,
                        "denominator": 100,
                    }
                ],
            },
            "beta": {
                "sourceUrl": "https://example.test/b.csv",
                "dimensions": {"sesso": ["Maschi", "Femmine"]},
            },
        },
    }
    registry = {
        "defaults": {},
        "sourceProfiles": {
            "profile-a": {
                "enrichmentDimensions": {
                    "sesso": {
                        "state": "AVAILABLE_MISSING",
                        "evidence": "La tabella ufficiale espone il sesso.",
                        "sourceReference": "https://example.test/a-dictionary",
                    },
                    "categorie_specifiche": {
                        "state": "SOURCE_UNAVAILABLE",
                        "evidence": "La fonte ufficiale non espone categorie ulteriori.",
                        "sourceReference": "https://example.test/a-dictionary",
                    },
                }
            },
            "profile-b": {"publisher": "Fixture source B"},
        },
        "sourceProfileByUrl": {
            "https://example.test/a.csv": "profile-a",
            "https://example.test/b.csv": "profile-b",
        },
        "metricOverrides": {
            "alpha": {
                "enrichmentDimensions": {
                    "eta": {
                        "state": "NOT_APPLICABLE",
                        "evidence": "L'indicatore non descrive persone o classi anagrafiche.",
                    }
                }
            }
        },
    }
    return data, registry


def _row(payload, metric_id: str, dimension: str):
    return next(
        row
        for row in payload["rows"]
        if row["metricId"] == metric_id and row["dimension"] == dimension
    )


def test_derived_matrix_and_precedence() -> None:
    data, registry = fixtures()
    payload = audit.build_matrix(data, registry)
    summary = payload["summary"]
    assert summary["publicMetricCount"] == 2
    assert summary["dimensionCount"] == len(audit.DIMENSIONS)
    assert summary["pairCount"] == 2 * len(audit.DIMENSIONS)

    history = _row(payload, "alpha", "serie_storica")
    assert history["state"] == "ACQUIRED"
    assert history["classificationOrigin"] == "catalog_structure"

    numerator = _row(payload, "alpha", "numeratore_denominatore")
    assert numerator["state"] == "ACQUIRED"

    source_available = _row(payload, "alpha", "sesso")
    assert source_available["state"] == "AVAILABLE_MISSING"
    assert source_available["classificationOrigin"] == "source_profile"

    not_applicable = _row(payload, "alpha", "eta")
    assert not_applicable["state"] == "NOT_APPLICABLE"
    assert not_applicable["classificationOrigin"] == "metric_override"

    source_unavailable = _row(payload, "alpha", "categorie_specifiche")
    assert source_unavailable["state"] == "SOURCE_UNAVAILABLE"

    beta_sex = _row(payload, "beta", "sesso")
    assert beta_sex["state"] == "ACQUIRED"


def test_acquired_evidence_wins_over_registry_annotation() -> None:
    data, registry = fixtures()
    registry["sourceProfiles"]["profile-a"]["enrichmentDimensions"]["serie_storica"] = {
        "state": "SOURCE_UNAVAILABLE",
        "evidence": "Fixture intentionally contradictory.",
        "sourceReference": "https://example.test/a-dictionary",
    }
    payload = audit.build_matrix(data, registry)
    history = _row(payload, "alpha", "serie_storica")
    assert history["state"] == "ACQUIRED"
    assert history["classificationOrigin"] == "catalog_structure"


def test_age_token_does_not_match_aggregate() -> None:
    data = {
        "version": "v-test",
        "updated": "16 settembre 2026",
        "metrics": {
            "gamma": {
                "sourceUrl": "https://example.test/gamma.csv",
                "aggregate": {"value": 42, "label": "Media Versilia"},
            }
        },
    }
    registry = {
        "defaults": {},
        "sourceProfiles": {"profile-gamma": {"publisher": "Fixture source gamma"}},
        "sourceProfileByUrl": {"https://example.test/gamma.csv": "profile-gamma"},
        "metricOverrides": {},
    }
    payload = audit.build_matrix(data, registry)
    age = _row(payload, "gamma", "eta")
    assert age["state"] is None
    assert age["classificationOrigin"] == "pending_source_evidence"


def test_strict_validation_rejects_unclassified_pairs() -> None:
    data, registry = fixtures()
    payload = audit.build_matrix(data, registry)
    assert payload["summary"]["unclassifiedPairCount"] > 0
    try:
        audit.validate_matrix(payload, require_complete=True)
    except RuntimeError as exc:
        assert "A3.2 incompleto" in str(exc)
    else:
        raise AssertionError("La validazione strict deve fallire con coppie non classificate")


def test_profile_not_applicable_is_rejected() -> None:
    data, registry = fixtures()
    registry["sourceProfiles"]["profile-a"]["enrichmentDimensions"]["eta"] = {
        "state": "NOT_APPLICABLE",
        "evidence": "Non applicabile solo a livello metrica.",
    }
    registry["metricOverrides"]["alpha"]["enrichmentDimensions"].pop("eta")
    try:
        audit.build_matrix(data, registry)
    except RuntimeError as exc:
        assert "Stato enrichment non ammesso" in str(exc)
    else:
        raise AssertionError("NOT_APPLICABLE non deve essere ammesso sul profilo fonte")


if __name__ == "__main__":
    test_derived_matrix_and_precedence()
    test_acquired_evidence_wins_over_registry_annotation()
    test_age_token_does_not_match_aggregate()
    test_strict_validation_rejects_unclassified_pairs()
    test_profile_not_applicable_is_rejected()
    print("A3.2 enrichment matrix regression passed.")
