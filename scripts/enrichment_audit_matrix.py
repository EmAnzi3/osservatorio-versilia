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
    """Recognize ``years`` plus any aligned numeric observation vector."""
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


def _unit_scale(unit: Any) -> float | None:
    raw = str(unit or "").strip()
    normalized = _core._norm(raw)
    if raw == "%" or normalized in {"percent", "percentage", "pct", "per_100", "per100"}:
        return 100.0
    aliases = {"per1000": 1000.0, "per_1000": 1000.0, "per100k": 100000.0, "per_100k": 100000.0}
    if normalized in aliases:
        return aliases[normalized]
    match = re.fullmatch(r"per_?(\d+)", normalized)
    if match:
        return float(match.group(1))
    if "_per_" in normalized:
        return 1.0
    return None


def _ratio_scale(metric: dict[str, Any]) -> float | None:
    meta = metric.get("meta")
    meta = meta if isinstance(meta, dict) else {}
    return _unit_scale(meta.get("unit"))


def _find_ratio_components(metric: dict[str, Any]) -> tuple[str, str, float] | None:
    """Find two row fields that reproduce the published normalized value."""
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
        "value", "benchmark_value", "normalized", "normalized_value", "year", "code",
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


def _absolute_field(part: dict[str, Any]) -> tuple[str, float] | None:
    absolute_keys = {
        "ha", "hectares", "count", "absolute", "assoluto", "km", "sqm", "m2",
        "numerator", "numeratore", "people", "persons", "number",
    }
    for key, candidate in part.items():
        if _core._norm(key) in absolute_keys and _numeric(candidate):
            return str(key), float(candidate)
    return None


def _part_scale(part: dict[str, Any], metric_unit: Any) -> float | None:
    return _unit_scale(part.get("unit") or metric_unit)


def _find_parts_absolute_normalized(metric: dict[str, Any]) -> str | None:
    meta = metric.get("meta")
    meta = meta if isinstance(meta, dict) else {}
    metric_unit = meta.get("unit")
    for path, value in _core._walk(metric):
        if not path or path[-1] != "parts" or not isinstance(value, list):
            continue
        for part in value:
            if not isinstance(part, dict) or not _numeric(part.get("value")):
                continue
            if _part_scale(part, metric_unit) is None:
                continue
            if _absolute_field(part) is not None:
                return _core._path_text(path)
    return None


def _ratio_matches(numerator: Any, denominator: Any, observed: Any, scale: float) -> bool:
    if not (_numeric(numerator) and _numeric(denominator) and _numeric(observed)):
        return False
    denominator_value = float(denominator)
    if denominator_value == 0:
        return False
    expected = float(numerator) / denominator_value * scale
    observed_value = float(observed)
    # Some official payloads publish percentages rounded to two decimals.
    tolerance = max(0.02 if scale == 100.0 else 1e-3, abs(observed_value) * 5e-5)
    return abs(expected - observed_value) <= tolerance


def _enough(matches: list[bool]) -> bool:
    return len(matches) >= 2 and sum(matches) / len(matches) >= 0.9


def _find_parts_row_denominator(metric: dict[str, Any]) -> str | None:
    """Recognize nested normalized parts divided by a top-level row denominator."""
    rows = [row for row in metric.get("rows", []) if isinstance(row, dict)]
    if len(rows) < 2:
        return None
    meta = metric.get("meta") if isinstance(metric.get("meta"), dict) else {}
    metric_unit = meta.get("unit")
    first_parts = rows[0].get("parts")
    if not isinstance(first_parts, list):
        return None
    denominator_keys = [
        str(key) for key, value in rows[0].items()
        if key not in {"value", "year", "code", "benchmarkValue", "normalized"} and _numeric(value)
    ]
    for index, part in enumerate(first_parts):
        if not isinstance(part, dict) or not _numeric(part.get("value")):
            continue
        absolute = _absolute_field(part)
        scale = _part_scale(part, metric_unit)
        if absolute is None or scale is None:
            continue
        absolute_key, _ = absolute
        for denominator_key in denominator_keys:
            checks: list[bool] = []
            for row in rows:
                parts = row.get("parts")
                if not isinstance(parts, list) or index >= len(parts) or not isinstance(parts[index], dict):
                    continue
                checks.append(_ratio_matches(
                    parts[index].get(absolute_key), row.get(denominator_key), parts[index].get("value"), scale
                ))
            if _enough(checks):
                return f"rows.*.parts[{index}].{absolute_key} / rows.*.{denominator_key}"
    return None


def _find_parts_map_denominator(metric: dict[str, Any]) -> str | None:
    """Recognize normalized parts against a structured top-level denominator map."""
    rows = [row for row in metric.get("rows", []) if isinstance(row, dict)]
    if len(rows) < 2:
        return None
    meta = metric.get("meta") if isinstance(metric.get("meta"), dict) else {}
    metric_unit = meta.get("unit")
    first_parts = rows[0].get("parts")
    if not isinstance(first_parts, list):
        return None
    map_keys = [
        str(key) for key, value in rows[0].items()
        if isinstance(value, dict) and value and all(_numeric(item) for item in value.values())
    ]
    for index, part in enumerate(first_parts):
        if not isinstance(part, dict) or not _numeric(part.get("value")):
            continue
        absolute = _absolute_field(part)
        scale = _part_scale(part, metric_unit)
        if absolute is None or scale is None:
            continue
        absolute_key, _ = absolute
        for map_key in map_keys:
            common = set(rows[0][map_key])
            for row in rows[1:]:
                candidate = row.get(map_key)
                if not isinstance(candidate, dict):
                    common.clear()
                    break
                common &= set(candidate)
            for subkey in sorted(common):
                checks: list[bool] = []
                for row in rows:
                    parts = row.get("parts")
                    denominator_map = row.get(map_key)
                    if (
                        not isinstance(parts, list) or index >= len(parts) or not isinstance(parts[index], dict)
                        or not isinstance(denominator_map, dict)
                    ):
                        continue
                    checks.append(_ratio_matches(
                        parts[index].get(absolute_key), denominator_map.get(subkey), parts[index].get("value"), scale
                    ))
                if _enough(checks):
                    return f"rows.*.parts[{index}].{absolute_key} / rows.*.{map_key}.{subkey}"
    return None


def _find_nested_sibling_ratio(metric: dict[str, Any]) -> str | None:
    """Recognize top-level normalized value from two numeric siblings in a child object."""
    scale = _ratio_scale(metric)
    rows = [row for row in metric.get("rows", []) if isinstance(row, dict) and _numeric(row.get("value"))]
    if scale is None or len(rows) < 2:
        return None
    for child_key, child in rows[0].items():
        if not isinstance(child, dict):
            continue
        numeric_keys = [str(key) for key, value in child.items() if _numeric(value)]
        for numerator, denominator in permutations(numeric_keys, 2):
            checks: list[bool] = []
            for row in rows:
                nested = row.get(child_key)
                if not isinstance(nested, dict):
                    continue
                checks.append(_ratio_matches(
                    nested.get(numerator), nested.get(denominator), row.get("value"), scale
                ))
            if _enough(checks):
                return f"rows.*.{child_key}.{numerator} / rows.*.{child_key}.{denominator}"
    return None


def _find_density_parts_ratio(metric: dict[str, Any]) -> str | None:
    """Recognize absolute-length and density parts sharing a row-level area denominator."""
    rows = [row for row in metric.get("rows", []) if isinstance(row, dict)]
    if len(rows) < 2:
        return None
    first_parts = rows[0].get("parts")
    if not isinstance(first_parts, list):
        return None
    denominator_keys = [
        str(key) for key, value in rows[0].items()
        if key not in {"value", "year", "code"} and _numeric(value)
    ]
    for numerator_index, numerator_part in enumerate(first_parts):
        if not isinstance(numerator_part, dict) or not _numeric(numerator_part.get("value")):
            continue
        numerator_unit = _core._norm(numerator_part.get("unit") or "")
        if "_per_" in numerator_unit:
            continue
        for value_index, normalized_part in enumerate(first_parts):
            if not isinstance(normalized_part, dict) or not _numeric(normalized_part.get("value")):
                continue
            normalized_unit = _core._norm(normalized_part.get("unit") or "")
            if "_per_" not in normalized_unit:
                continue
            for denominator_key in denominator_keys:
                checks: list[bool] = []
                for row in rows:
                    parts = row.get("parts")
                    if not isinstance(parts, list) or max(numerator_index, value_index) >= len(parts):
                        continue
                    checks.append(_ratio_matches(
                        parts[numerator_index].get("value"), row.get(denominator_key),
                        parts[value_index].get("value"), 1.0,
                    ))
                if _enough(checks):
                    return (
                        f"rows.*.parts[{numerator_index}].value / rows.*.{denominator_key} "
                        f"= rows.*.parts[{value_index}].value"
                    )
    return None


def _find_exhaustive_parts_ratio(metric: dict[str, Any]) -> str | None:
    """Recognize exhaustive distributions where counts generate every published share."""
    rows = [row for row in metric.get("rows", []) if isinstance(row, dict)]
    if len(rows) < 2:
        return None
    meta = metric.get("meta") if isinstance(metric.get("meta"), dict) else {}
    scale = _unit_scale(meta.get("unit"))
    if scale is None:
        return None
    checks: list[bool] = []
    absolute_key: str | None = None
    for row in rows:
        parts = row.get("parts")
        if not isinstance(parts, list) or len(parts) < 2:
            continue
        observations: list[tuple[float, float]] = []
        row_key: str | None = None
        for part in parts:
            if not isinstance(part, dict):
                observations = []
                break
            absolute = _absolute_field(part)
            if absolute is None or not _numeric(part.get("value")):
                observations = []
                break
            key, absolute_value = absolute
            if row_key is None:
                row_key = key
            elif row_key != key:
                observations = []
                break
            observations.append((absolute_value, float(part["value"])))
        if not observations or row_key is None:
            continue
        if absolute_key is None:
            absolute_key = row_key
        elif absolute_key != row_key:
            return None
        denominator = sum(item[0] for item in observations)
        if denominator == 0:
            continue
        checks.append(all(
            _ratio_matches(absolute, denominator, normalized, scale)
            for absolute, normalized in observations
        ))
    if _enough(checks) and absolute_key:
        return (
            f"rows.*.parts.*.{absolute_key} / "
            f"sum(rows.*.parts.*.{absolute_key})"
        )
    return None


def _find_nested_ratio_evidence(metric: dict[str, Any]) -> str | None:
    return (
        _find_parts_row_denominator(metric)
        or _find_parts_map_denominator(metric)
        or _find_nested_sibling_ratio(metric)
        or _find_density_parts_ratio(metric)
        or _find_exhaustive_parts_ratio(metric)
    )


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
        return _find_ratio_evidence(metric) or _find_nested_ratio_evidence(metric)
    if dimension == "assoluto_normalizzato":
        nested = _find_nested_ratio_evidence(metric)
        if nested:
            return nested
        return _find_parts_absolute_normalized(metric) or _find_absolute_from_ratio(metric)
    if dimension == "categorie_specifiche":
        return _find_structured_categories(metric)
    return None


_core.acquired_evidence = acquired_evidence


if __name__ == "__main__":
    raise SystemExit(main())
