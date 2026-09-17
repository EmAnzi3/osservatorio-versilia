#!/usr/bin/env python3
"""Resolve A3.2 evidence supplied by a separately materialized companion metric.

The relationship contract is declarative and intentionally small: it records
semantic links between public indicators, never final A3 states. A relationship
can become ACQUIRED only when the referenced companion exists in the canonical
catalog and the requested dimension is independently detected in that
companion's own structured payload or declared storage route.
"""
from __future__ import annotations

import json
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


def _relationship_for(
    contract: dict[str, Any], metric_id: str, dimension: str
) -> dict[str, Any] | None:
    matches: list[dict[str, Any]] = []
    for item in contract.get("relationships", []):
        if not isinstance(item, dict):
            raise RuntimeError("Relazione companion A3 non-oggetto")
        if item.get("metricId") == metric_id and item.get("dimension") == dimension:
            matches.append(item)
    if len(matches) > 1:
        raise RuntimeError(f"Relazione companion A3 duplicata: {metric_id}/{dimension}")
    return matches[0] if matches else None


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

    companion_id = str(relationship.get("companionMetricId") or "").strip()
    relationship_type = str(relationship.get("relationship") or "").strip()
    if not companion_id or not relationship_type:
        raise RuntimeError(f"Relazione companion A3 incompleta: {metric_id}/{dimension}")
    if companion_id == metric_id:
        raise RuntimeError(f"Relazione companion A3 autoreferenziale: {metric_id}/{dimension}")

    companion = catalog.get(companion_id)
    if not isinstance(companion, dict):
        raise RuntimeError(
            f"Companion A3 assente dal catalogo: {metric_id}/{dimension} -> {companion_id}"
        )

    evidence = _structural.acquired_evidence(
        companion,
        dimension,
        metric_id=companion_id,
        catalog=catalog,
    )
    if not evidence:
        evidence = structured_route_evidence(companion, dimension, repo_root)
    if not evidence:
        return None

    return f"companion:{relationship_type}:{companion_id}:{evidence}"
