#!/usr/bin/env python3
"""A3.2 matrix with conservative structural-closure detectors.

The matrix engine remains in ``enrichment_audit_matrix_core``. This module adds
only structural detectors: no metric IDs, source-profile IDs, or manual final
states are encoded here. A pair becomes ACQUIRED only when the materialized
metric itself contains machine-verifiable evidence.
"""
from __future__ import annotations

import math
import re
from itertools import permutations
from typing import Any

import enrichment_audit_matrix_core as _core
from enrichment_audit_matrix_core import *  # noqa: F401,F403

_BASE_ACQUIRED_EVIDENCE = _core.acquired_evidence


def _numeric(value: Any) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(float(value))
    )


def _find_aligned_numeric_series(metric: dict[str, Any]) -> str | None:
    """Recognize ``years`` plus any aligned numeric observation vector.

    The previous detector required the vector to be literally named ``values``.
    Composite public metrics also use names such as ``ha`` and ``pct``.
    """
    period_keys = {"years", "anni", "periods", "periodi", "dates"}
    for path, value in _core._walk(metric):
        if not isinstance(value, dict):
            continue
        periods: list[Any] | None = None
        period_key = ""
        for key, candidate in value.items():
            if _core._norm(key) in period_keys and isinstance(candidate, list) and len(candidate) >= 2:
                periods = candidate
                period_key = str(key)
                break
        if periods is None:
            continue
        for key, candidate in value.items():
            if str(key) == period_key or not isinstance(candidate, list):
                continue
            if len(candidate) != len(periods):
                continue
            if sum(1 for item in candidate if _numeric(item)) >= 2:
                return _core._path_text(path)
    return None


def _ratio_scale(metric: dict[str, Any]) -> float | None:
    meta = metric.get("meta")
    meta = meta if isinstance(meta, dict) else {}
    unit = _core._norm(meta.get("unit") or "")
    if unit in {"percent", "percentage", "pct", "per_100", "per100"}:
        return 100.0
    match = re.fullmatch(r"per_?(\d+)", unit)
    if match:
        return float(match.group(1))
    return None


def _find_ratio_components(metric: dict[str, Any]) -> tuple[str, str, float] | None:
    """Find two row fields that reproduce the published normalized value.

    This is deliberately arithmetic rather than name-based. The same pair of
    fields must reproduce at least 90% of the usable municipal rows and at least
    two observations. A single-row numerical coincidence is never sufficient.
    """
    scale = _ratio_scale(metric)
    rows = metric.get("rows")
    if scale is None or not isinstance(rows, list):
        return None
    usable_rows = [
        row for row in rows
        if isinstance(row, dict) and _numeric(row.get("value"))
    ]
    if len(usable_rows) < 2:
        return None

    excluded = {
        "value",
        "benchmark_value",
        "normalized",
        "normalized_value",
        "year",
        "code",
    }
    counts: dict[str, int] = {}
    for row in usable_rows:
        for key, candidate in row.items():
            if _core._norm(key) in excluded or not _numeric(candidate):
                continue
            counts[str(key)] = counts.get(str(key), 0) + 1
    keys = [key for key, count in counts.items() if count >= 2]

    for numerator, denominator in permutations(keys, 2):
        valid = 0
        matches = 0
        for row in usable_rows:
            num = row.get(numerator)
            den = row.get(denominator)
            value = row.get("value")
            if not (_numeric(num) and _numeric(den) and _numeric(value)):
                continue
            den_value = float(den)
            if den_value == 0:
                continue
            valid += 1
            expected = float(num) / den_value * scale
            observed = float(value)
            tolerance = max(1e-3, abs(observed) * 5e-5)
            if abs(expected - observed) <= tolerance:
                matches += 1
        if valid >= 2 and matches / valid >= 0.9:
            return numerator, denominator, scale
    return None


def _find_ratio_evidence(metric: dict[str, Any]) -> str | None:
    pair = _find_ratio_components(metric)
    if pair is None:
        return None
    numerator, denominator, scale = pair
    scale_label = int(scale) if float(scale).is_integer() else scale
    return f"rows.*.{numerator} / rows.*.{denominator} × {scale_label}"


def _find_absolute_from_ratio(metric: dict[str, Any]) -> str | None:
    pair = _find_ratio_components(metric)
    if pair is None:
        return None
    numerator, _denominator, _scale = pair
    return f"rows.*.{numerator} + rows.*.value"


def _find_parts_absolute_normalized(metric: dict[str, Any]) -> str | None:
    normalized_units = {"percent", "percentage", "pct", "per100", "per_100", "per1000", "per_1000"}
    absolute_keys = {"ha", "hectares", "count", "absolute", "assoluto", "km", "sqm", "m2"}
    for path, value in _core._walk(metric):
        if not path or path[-1] != "parts" or not isinstance(value, list):
            continue
        for part in value:
            if not isinstance(part, dict) or not _numeric(part.get("value")):
                continue
            unit = _core._norm(part.get("unit") or "")
            if unit not in normalized_units:
                continue
            if any(_core._norm(key) in absolute_keys and _numeric(candidate) for key, candidate in part.items()):
                return _core._path_text(path)
    return None


def _identifiable_parts(value: Any) -> bool:
    if not isinstance(value, list) or len(value) < 2:
        return False
    keys: set[str] = set()
    for part in value:
        if not isinstance(part, dict):
            continue
        identity = str(part.get("key") or part.get("label") or "").strip()
        if identity:
            keys.add(identity)
    return len(keys) >= 2


def _find_structured_categories(metric: dict[str, Any]) -> str | None:
    definitions = metric.get("categoryDefinitions")
    if _identifiable_parts(definitions):
        return "categoryDefinitions"

    meta = metric.get("meta")
    meta = meta if isinstance(meta, dict) else {}
    if not str(meta.get("compositeType") or "").strip():
        return None
    for path, value in _core._walk(metric):
        if path and path[-1] == "parts" and _identifiable_parts(value):
            return _core._path_text(path)
    return None


def acquired_evidence(metric: dict[str, Any], dimension: str) -> str | None:
    """Return structural evidence, preserving the pre-closure detector first."""
    existing = _BASE_ACQUIRED_EVIDENCE(metric, dimension)
    if existing:
        return existing
    if dimension == "serie_storica":
        return _find_aligned_numeric_series(metric)
    if dimension == "numeratore_denominatore":
        return _find_ratio_evidence(metric)
    if dimension == "assoluto_normalizzato":
        return _find_parts_absolute_normalized(metric) or _find_absolute_from_ratio(metric)
    if dimension == "categorie_specifiche":
        return _find_structured_categories(metric)
    return None


# The core matrix engine resolves ``acquired_evidence`` from its own module
# globals. Patch that single hook so build_matrix/write_matrix/main all use the
# enhanced structural detector without duplicating matrix semantics.
_core.acquired_evidence = acquired_evidence


if __name__ == "__main__":
    raise SystemExit(main())
