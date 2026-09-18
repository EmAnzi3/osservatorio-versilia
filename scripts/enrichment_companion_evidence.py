#!/usr/bin/env python3
"""Resolve A3.2 evidence supplied by a separately materialized companion metric.

The relationship contract records semantic links between public indicators,
never final A3 states. A relationship can become ACQUIRED only when the
referenced companion exists in the canonical catalog and the requested
dimension is independently detected in that companion's own structured payload
or declared storage route.
"""
from __future__ import annotations

import json
import math
import re
from pathlib import Path
from typing import Any

import enrichment_audit_matrix_structural_base as _structural
from enrichment_route_evidence import structured_route_evidence

_CONTRACT_PATH = Path("data/enrichment-companion-contract.json")


def _load_contract(repo_root: Path) -> dict[str, Any]:
    path = repo_root / _CONTRACT_PATH
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or value.get("schemaVersion") != 1:
        raise RuntimeError(f"Contratto companion A3 non valido: {path}")
    relationships = value.get("relationships")
    if not isinstance(relationships, list):
        raise RuntimeError(f"Relazioni companion A3 non valide: {path}")
    return value


def _relationship_dimensions(item: dict[str, Any]) -> set[str]:
    singular = item.get("dimension")
    plural = item.get("dimensions")
    if singular is not None and plural is not None:
        raise RuntimeError("Relazione companion A3 con dimension/dimensions simultanei")
    if singular is not None:
        if not isinstance(singular, str) or not singular:
            raise RuntimeError("Dimensione companion A3 non valida")
        return {singular}
    if plural is None:
        return set()
    if not isinstance(plural, list) or not plural or not all(isinstance(value, str) and value for value in plural):
        raise RuntimeError("Dimensioni companion A3 non valide")
    values = set(plural)
    if len(values) != len(plural):
        raise RuntimeError("Dimensioni companion A3 duplicate")
    return values


def _relationship_for(
    contract: dict[str, Any], metric_id: str, dimension: str
) -> dict[str, Any] | None:
    matches: list[dict[str, Any]] = []
    for item in contract.get("relationships", []):
        if not isinstance(item, dict):
            raise RuntimeError("Relazione companion A3 non-oggetto")
        if item.get("metricId") == metric_id and dimension in _relationship_dimensions(item):
            matches.append(item)
    if len(matches) > 1:
        raise RuntimeError(f"Relazione companion A3 duplicata: {metric_id}/{dimension}")
    return matches[0] if matches else None


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def _row_identity(row: dict[str, Any]) -> str | None:
    for key in ("code", "slug", "town"):
        value = row.get(key)
        if value not in (None, ""):
            return f"{key}:{value}"
    return None


def _metric_year(metric: dict[str, Any]) -> str | None:
    meta = metric.get("meta")
    if not isinstance(meta, dict):
        return None
    value = str(meta.get("year") or "").strip()
    return value if re.fullmatch(r"\d{4}", value) else None


def _row_value_for_year(metric: dict[str, Any], row: dict[str, Any], year: str | None) -> float | None:
    if year:
        series = row.get("series")
        if isinstance(series, dict):
            years = series.get("years")
            values = series.get("values")
            if isinstance(years, list) and isinstance(values, list) and len(years) == len(values):
                for index, candidate_year in enumerate(years):
                    if str(candidate_year) == year and _is_number(values[index]):
                        return float(values[index])

        meta = metric.get("meta")
        metric_year = str(meta.get("year") or "").strip() if isinstance(meta, dict) else ""
        if metric_year != year:
            return None

    value = row.get("value")
    return float(value) if _is_number(value) else None


def _rows_by_identity(metric: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows = metric.get("rows")
    if not isinstance(rows, list):
        return {}
    result: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        identity = _row_identity(row)
        if identity:
            result[identity] = row
    return result


def _ratio_scale(metric: dict[str, Any]) -> float:
    meta = metric.get("meta")
    unit = str(meta.get("unit") or "").strip().lower() if isinstance(meta, dict) else ""
    if unit in {"percent", "%", "percentage"}:
        return 100.0
    if unit == "per100":
        return 100.0
    if unit == "per1000":
        return 1000.0
    if unit == "per10k":
        return 10000.0
    if unit == "per100k":
        return 100000.0
    return 1.0


def _ratio_formula_evidence(
    *,
    metric_id: str,
    dimension: str,
    relationship: dict[str, Any],
    catalog: dict[str, Any],
) -> str | None:
    if dimension not in {"assoluto_normalizzato", "numeratore_denominatore"}:
        return None

    numerator_id = str(relationship.get("numeratorMetricId") or "").strip()
    denominator_id = str(relationship.get("denominatorMetricId") or "").strip()
    if not numerator_id or not denominator_id:
        raise RuntimeError(f"Relazione ratio A3 incompleta: {metric_id}/{dimension}")
    if metric_id in {numerator_id, denominator_id}:
        raise RuntimeError(f"Relazione ratio A3 autoreferenziale: {metric_id}/{dimension}")

    target = catalog.get(metric_id)
    numerator = catalog.get(numerator_id)
    denominator = catalog.get(denominator_id)
    if not isinstance(target, dict):
        raise RuntimeError(f"Metrica target A3 assente dal catalogo: {metric_id}")
    if not isinstance(numerator, dict):
        raise RuntimeError(f"Numeratore companion A3 assente: {metric_id} -> {numerator_id}")
    if not isinstance(denominator, dict):
        raise RuntimeError(f"Denominatore companion A3 assente: {metric_id} -> {denominator_id}")

    year = _metric_year(target)
    if year is None:
        return None

    target_rows = _rows_by_identity(target)
    numerator_rows = _rows_by_identity(numerator)
    denominator_rows = _rows_by_identity(denominator)
    if not target_rows:
        return None

    scale = _ratio_scale(target)
    verified = 0
    for identity, target_row in target_rows.items():
        numerator_row = numerator_rows.get(identity)
        denominator_row = denominator_rows.get(identity)
        if numerator_row is None or denominator_row is None:
            return None

        denominator_year_mode = str(relationship.get("denominatorYearMode") or "target_year")
        if denominator_year_mode not in {"target_year", "metric_current"}:
            raise RuntimeError(
                f"Modalità anno denominatore A3 non valida: {metric_id}/{dimension} -> {denominator_year_mode}"
            )
        denominator_year = year if denominator_year_mode == "target_year" else None

        observed = _row_value_for_year(target, target_row, year)
        numerator_value = _row_value_for_year(numerator, numerator_row, year)
        denominator_value = _row_value_for_year(denominator, denominator_row, denominator_year)
        if observed is None or numerator_value is None or denominator_value in (None, 0):
            return None

        expected = numerator_value / denominator_value * scale
        if not math.isclose(observed, expected, rel_tol=1e-6, abs_tol=1e-6):
            return None
        verified += 1

    if verified < 2:
        return None
    denominator_year_mode = str(relationship.get("denominatorYearMode") or "target_year")
    return (
        f"ratio_formula:{numerator_id}/{denominator_id}:"
        f"{year}:denominator={denominator_year_mode}:"
        f"scale={scale:g}:{verified}/{len(target_rows)}"
    )



def _series_change_formula_evidence(
    *,
    metric_id: str,
    dimension: str,
    relationship: dict[str, Any],
    catalog: dict[str, Any],
) -> str | None:
    if dimension not in {"assoluto_normalizzato", "numeratore_denominatore"}:
        return None

    companion_id = str(relationship.get("companionMetricId") or "").strip()
    start_year = str(relationship.get("startYear") or "").strip()
    end_year = str(relationship.get("endYear") or "").strip()
    if not companion_id or not re.fullmatch(r"\d{4}", start_year) or not re.fullmatch(r"\d{4}", end_year):
        raise RuntimeError(f"Relazione series-change A3 incompleta: {metric_id}/{dimension}")
    if companion_id == metric_id or start_year == end_year:
        raise RuntimeError(f"Relazione series-change A3 non valida: {metric_id}/{dimension}")

    target = catalog.get(metric_id)
    companion = catalog.get(companion_id)
    if not isinstance(target, dict):
        raise RuntimeError(f"Metrica target A3 assente dal catalogo: {metric_id}")
    if not isinstance(companion, dict):
        raise RuntimeError(f"Companion A3 assente dal catalogo: {metric_id}/{dimension} -> {companion_id}")

    target_rows = _rows_by_identity(target)
    companion_rows = _rows_by_identity(companion)
    if not target_rows:
        return None

    scale = _ratio_scale(target)
    verified = 0
    for identity, target_row in target_rows.items():
        companion_row = companion_rows.get(identity)
        if companion_row is None:
            return None
        observed = target_row.get("value")
        start_value = _row_value_for_year(companion, companion_row, start_year)
        end_value = _row_value_for_year(companion, companion_row, end_year)
        if not _is_number(observed) or start_value in (None, 0) or end_value is None:
            return None
        expected = (end_value - start_value) / start_value * scale
        if not math.isclose(float(observed), expected, rel_tol=1e-6, abs_tol=1e-6):
            return None
        verified += 1

    if verified < 2:
        return None
    return (
        f"series_change_formula:{companion_id}:{start_year}->{end_year}:"
        f"scale={scale:g}:{verified}/{len(target_rows)}"
    )


def _parts_ratio_formula_evidence(
    *,
    metric_id: str,
    dimension: str,
    relationship: dict[str, Any],
    catalog: dict[str, Any],
) -> str | None:
    if dimension not in {"eta", "assoluto_normalizzato", "numeratore_denominatore"}:
        return None

    companion_id = str(relationship.get("companionMetricId") or "").strip()
    numerator_parts = relationship.get("numeratorParts")
    denominator_parts = relationship.get("denominatorParts")
    selector_field = str(relationship.get("partSelectorField") or "selectorLabel").strip()
    value_field = str(relationship.get("partValueField") or "count").strip()
    if (
        not companion_id
        or not isinstance(numerator_parts, list)
        or not numerator_parts
        or not all(isinstance(value, str) and value for value in numerator_parts)
        or not isinstance(denominator_parts, list)
        or not denominator_parts
        or not all(isinstance(value, str) and value for value in denominator_parts)
        or not selector_field
        or not value_field
    ):
        raise RuntimeError(f"Relazione parts-ratio A3 incompleta: {metric_id}/{dimension}")
    if companion_id == metric_id:
        raise RuntimeError(f"Relazione parts-ratio A3 autoreferenziale: {metric_id}/{dimension}")

    target = catalog.get(metric_id)
    companion = catalog.get(companion_id)
    if not isinstance(target, dict):
        raise RuntimeError(f"Metrica target A3 assente dal catalogo: {metric_id}")
    if not isinstance(companion, dict):
        raise RuntimeError(f"Companion A3 assente dal catalogo: {metric_id}/{dimension} -> {companion_id}")

    target_rows = _rows_by_identity(target)
    companion_rows = _rows_by_identity(companion)
    if not target_rows:
        return None

    wanted_num = set(numerator_parts)
    wanted_den = set(denominator_parts)
    if wanted_num & wanted_den or len(wanted_num) != len(numerator_parts) or len(wanted_den) != len(denominator_parts):
        raise RuntimeError(f"Parti ratio A3 duplicate/sovrapposte: {metric_id}/{dimension}")

    scale = _ratio_scale(target)
    verified = 0
    for identity, target_row in target_rows.items():
        companion_row = companion_rows.get(identity)
        if companion_row is None:
            return None
        parts = companion_row.get("parts")
        if not isinstance(parts, list):
            return None

        values: dict[str, float] = {}
        for part in parts:
            if not isinstance(part, dict):
                continue
            selector = part.get(selector_field)
            raw = part.get(value_field)
            if isinstance(selector, str) and selector and _is_number(raw):
                if selector in values:
                    return None
                values[selector] = float(raw)

        if not wanted_num.issubset(values) or not wanted_den.issubset(values):
            return None
        numerator = sum(values[label] for label in numerator_parts)
        denominator = sum(values[label] for label in denominator_parts)
        observed = target_row.get("value")
        if not _is_number(observed) or denominator == 0:
            return None
        expected = numerator / denominator * scale
        if not math.isclose(float(observed), expected, rel_tol=1e-6, abs_tol=1e-6):
            return None
        verified += 1

    if verified < 2:
        return None
    return (
        f"parts_ratio_formula:{companion_id}:"
        f"scale={scale:g}:{verified}/{len(target_rows)}"
    )



def _row_field_ratio_formula_evidence(
    *,
    metric_id: str,
    dimension: str,
    relationship: dict[str, Any],
    catalog: dict[str, Any],
) -> str | None:
    """Verify a target-row numerator against a field from a companion row."""
    if dimension != "numeratore_denominatore":
        return None

    numerator_field = str(relationship.get("targetNumeratorField") or "").strip()
    denominator_id = str(relationship.get("denominatorMetricId") or "").strip()
    denominator_field = str(relationship.get("denominatorField") or "").strip()
    if not numerator_field or not denominator_id or not denominator_field:
        raise RuntimeError(f"Relazione row-field ratio A3 incompleta: {metric_id}/{dimension}")
    if denominator_id == metric_id:
        raise RuntimeError(f"Relazione row-field ratio A3 autoreferenziale: {metric_id}/{dimension}")

    target = catalog.get(metric_id)
    denominator_metric = catalog.get(denominator_id)
    if not isinstance(target, dict):
        raise RuntimeError(f"Metrica target A3 assente dal catalogo: {metric_id}")
    if not isinstance(denominator_metric, dict):
        raise RuntimeError(
            f"Denominatore companion A3 assente: {metric_id}/{dimension} -> {denominator_id}"
        )

    target_rows = _rows_by_identity(target)
    denominator_rows = _rows_by_identity(denominator_metric)
    if not target_rows:
        return None

    scale = _ratio_scale(target)
    verified = 0
    for identity, target_row in target_rows.items():
        denominator_row = denominator_rows.get(identity)
        if denominator_row is None:
            return None

        observed = target_row.get("value")
        numerator = target_row.get(numerator_field)
        denominator = denominator_row.get(denominator_field)
        if not _is_number(observed) or not _is_number(numerator) or not _is_number(denominator):
            return None
        if float(denominator) == 0:
            return None

        expected = float(numerator) / float(denominator) * scale
        if not math.isclose(float(observed), expected, rel_tol=1e-6, abs_tol=1e-6):
            return None
        verified += 1

    if verified < 2:
        return None
    return (
        f"row_field_ratio_formula:{metric_id}.{numerator_field}/"
        f"{denominator_id}.{denominator_field}:"
        f"scale={scale:g}:{verified}/{len(target_rows)}"
    )



def companion_acquired_evidence(
    *,
    metric_id: str,
    dimension: str,
    catalog: dict[str, Any],
    repo_root: Path,
) -> str | None:
    """Return evidence only after independently proving the companion payload."""
    relationship = _relationship_for(_load_contract(repo_root), metric_id, dimension)
    if relationship is None:
        return None

    relationship_type = str(relationship.get("relationship") or "").strip()
    if not relationship_type:
        raise RuntimeError(f"Relazione companion A3 incompleta: {metric_id}/{dimension}")

    if relationship_type == "ratio_formula":
        evidence = _ratio_formula_evidence(
            metric_id=metric_id,
            dimension=dimension,
            relationship=relationship,
            catalog=catalog,
        )
        return f"companion:{evidence}" if evidence else None

    if relationship_type == "series_change_formula":
        evidence = _series_change_formula_evidence(
            metric_id=metric_id,
            dimension=dimension,
            relationship=relationship,
            catalog=catalog,
        )
        return f"companion:{evidence}" if evidence else None

    if relationship_type == "parts_ratio_formula":
        evidence = _parts_ratio_formula_evidence(
            metric_id=metric_id,
            dimension=dimension,
            relationship=relationship,
            catalog=catalog,
        )
        return f"companion:{evidence}" if evidence else None

    if relationship_type == "row_field_ratio_formula":
        evidence = _row_field_ratio_formula_evidence(
            metric_id=metric_id,
            dimension=dimension,
            relationship=relationship,
            catalog=catalog,
        )
        return f"companion:{evidence}" if evidence else None

    companion_id = str(relationship.get("companionMetricId") or "").strip()
    if not companion_id:
        raise RuntimeError(f"Relazione companion A3 incompleta: {metric_id}/{dimension}")
    if companion_id == metric_id:
        raise RuntimeError(f"Relazione companion A3 autoreferenziale: {metric_id}/{dimension}")

    companion = catalog.get(companion_id)
    if not isinstance(companion, dict):
        raise RuntimeError(
            f"Companion A3 assente dal catalogo: {metric_id}/{dimension} -> {companion_id}"
        )

    # Deliberately verify only local/route evidence on the companion. Do not
    # recurse through companion relationships, which would turn a declared
    # semantic edge into transitive ACQUIRED evidence.
    evidence = _structural.acquired_evidence(companion, dimension)
    if not evidence:
        evidence = structured_route_evidence(companion, dimension, repo_root)
    if not evidence:
        return None

    return f"companion:{relationship_type}:{companion_id}:{evidence}"
