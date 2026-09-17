#!/usr/bin/env python3
"""A3.2 matrix with local, route/storage and verified companion evidence.

The same-payload detector remains in ``enrichment_audit_matrix_structural_base``.
This entry point layers route/storage evidence and a conservative cross-metric
resolver. Companion relationships never encode final states: ACQUIRED is
returned only when the referenced public metric independently exposes the
requested structured dimension.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import enrichment_audit_matrix_core as _core
import enrichment_audit_matrix_structural_base as _structural
from enrichment_audit_matrix_structural_base import *  # noqa: F401,F403
from enrichment_companion_evidence import companion_acquired_evidence
from enrichment_route_evidence import structured_route_evidence

_BASE_STRUCTURAL_EVIDENCE = _structural.acquired_evidence
_BASE_BUILD_MATRIX = _core.build_matrix
_REPO_ROOT = Path(__file__).resolve().parents[1]
_ACTIVE_CATALOG: dict[str, Any] | None = None
_ACTIVE_METRIC_IDS: dict[int, str] = {}


def acquired_evidence(metric: dict[str, Any], dimension: str) -> str | None:
    """Prefer same-payload, then route, then independently verified companion evidence."""
    existing = _BASE_STRUCTURAL_EVIDENCE(metric, dimension)
    if existing:
        return existing

    routed = structured_route_evidence(metric, dimension, _REPO_ROOT)
    if routed:
        return routed

    if _ACTIVE_CATALOG is None:
        return None
    metric_id = _ACTIVE_METRIC_IDS.get(id(metric))
    if not metric_id:
        return None
    return companion_acquired_evidence(
        metric_id=metric_id,
        dimension=dimension,
        catalog=_ACTIVE_CATALOG,
        repo_root=_REPO_ROOT,
    )


def build_matrix(data: dict[str, Any], registry: dict[str, Any]) -> dict[str, Any]:
    """Expose catalog identity to the evidence hook without changing the core API."""
    global _ACTIVE_CATALOG, _ACTIVE_METRIC_IDS
    metrics = data.get("metrics")
    if not isinstance(metrics, dict):
        return _BASE_BUILD_MATRIX(data, registry)

    previous_catalog = _ACTIVE_CATALOG
    previous_ids = _ACTIVE_METRIC_IDS
    _ACTIVE_CATALOG = metrics
    _ACTIVE_METRIC_IDS = {
        id(metric): metric_id
        for metric_id, metric in metrics.items()
        if isinstance(metric, dict)
    }
    try:
        return _BASE_BUILD_MATRIX(data, registry)
    finally:
        _ACTIVE_CATALOG = previous_catalog
        _ACTIVE_METRIC_IDS = previous_ids


_core.acquired_evidence = acquired_evidence
_core.build_matrix = build_matrix


if __name__ == "__main__":
    raise SystemExit(main())
