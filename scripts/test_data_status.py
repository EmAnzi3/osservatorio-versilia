#!/usr/bin/env python3
"""Verifica Stato dati e matrice A3 contro lo snapshot realmente pubblicato in dist/."""
from __future__ import annotations

from pathlib import Path

import enrichment_audit_matrix as _enrichment
import test_data_status_impl as _impl
import test_enrichment_audit_matrix as _enrichment_tests
from public_build_snapshot import (
    build_aware_load,
    effective_public_catalog,
    public_registry_path,
    validate_public_snapshot,
)

_ORIGINAL_LOAD = _impl.load


def _public_load(path: Path):
    return build_aware_load(_ORIGINAL_LOAD, path)


def _validate_enrichment_matrix() -> None:
    # Exercise annotation precedence and strict-mode semantics with small fixtures.
    _enrichment_tests.test_derived_matrix_and_precedence()
    _enrichment_tests.test_acquired_evidence_wins_over_registry_annotation()
    _enrichment_tests.test_age_token_does_not_match_aggregate()
    _enrichment_tests.test_strict_validation_rejects_unclassified_pairs()
    _enrichment_tests.test_profile_not_applicable_is_rejected()

    # Then validate the derived matrix against the actual materialized release.
    catalog = effective_public_catalog()
    registry = _ORIGINAL_LOAD(public_registry_path())
    payload = _enrichment.build_matrix(catalog, registry)
    _enrichment.validate_matrix(payload, require_complete=False)
    summary = payload["summary"]
    assert summary["publicMetricCount"] == len(catalog["metrics"])
    assert summary["pairCount"] == summary["publicMetricCount"] * summary["dimensionCount"]
    print(
        "A3.2 enrichment seed verificato: "
        f"{summary['publicMetricCount']} indicatori × {summary['dimensionCount']} dimensioni = "
        f"{summary['pairCount']} coppie; {summary['classifiedPairCount']} classificate, "
        f"{summary['unclassifiedPairCount']} da auditare."
    )


def main() -> None:
    validate_public_snapshot()
    _validate_enrichment_matrix()
    _impl.load = _public_load
    try:
        _impl.main()
    finally:
        _impl.load = _ORIGINAL_LOAD


if __name__ == "__main__":
    main()
