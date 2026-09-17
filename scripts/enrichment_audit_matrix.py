#!/usr/bin/env python3
"""A3.2 matrix with local and route/storage-aware structural evidence.

The complete same-payload detector from the previous closure tranche is kept in
``enrichment_audit_matrix_structural_base``.  This entry point adds only a
second, conservative resolver for structured data explicitly declared by the
metric storage contract.  No metric IDs, source-profile IDs, or manual final
states are encoded here.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import enrichment_audit_matrix_core as _core
import enrichment_audit_matrix_structural_base as _structural
from enrichment_audit_matrix_structural_base import *  # noqa: F401,F403
from enrichment_route_evidence import structured_route_evidence

_BASE_STRUCTURAL_EVIDENCE = _structural.acquired_evidence
_REPO_ROOT = Path(__file__).resolve().parents[1]


def acquired_evidence(metric: dict[str, Any], dimension: str) -> str | None:
    """Prefer existing same-payload evidence, then inspect declared storage."""
    existing = _BASE_STRUCTURAL_EVIDENCE(metric, dimension)
    if existing:
        return existing
    return structured_route_evidence(metric, dimension, _REPO_ROOT)


_core.acquired_evidence = acquired_evidence


if __name__ == "__main__":
    raise SystemExit(main())
