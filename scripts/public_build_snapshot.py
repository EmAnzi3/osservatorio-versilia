#!/usr/bin/env python3
"""Public snapshot produced by transactional release materialization.

Canonical sources are restored after the static build. Post-build checks must
therefore read the catalog and registry copied into ``dist/`` when they validate
the published release, while source-only checks keep reading ``data/``.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

from content_contract import load_contract as load_content_contract
from content_contract import route_owners, theme_membership
from ephemeral_build_workspace import load_build_materialization_contract

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"


def _snapshot_relatives() -> tuple[Path, ...]:
    contract = load_build_materialization_contract()
    values = tuple(Path(value) for value in contract.get("publicSnapshotFiles", []))
    if values != (Path("data/site-data.json"), Path("data/source-registry.json")):
        raise RuntimeError(f"Snapshot pubblici inattesi nel contratto build: {values}")
    return values


def source_snapshot_path(relative: str | Path) -> Path:
    return ROOT / Path(relative)


def public_snapshot_path(relative: str | Path) -> Path:
    relative = Path(relative)
    if relative not in _snapshot_relatives():
        raise RuntimeError(f"Path non dichiarato come snapshot pubblico: {relative}")
    path = DIST / relative
    if not path.is_file():
        raise RuntimeError(f"Snapshot pubblico mancante: {path}")
    return path


def public_catalog_path() -> Path:
    return public_snapshot_path("data/site-data.json")


def public_registry_path() -> Path:
    return public_snapshot_path("data/source-registry.json")


def resolve_public_snapshot_path(path: Path) -> Path:
    """Redirect an exact canonical snapshot read to the materialized dist copy."""
    try:
        relative = path.resolve().relative_to(ROOT.resolve())
    except ValueError:
        return path
    if relative in _snapshot_relatives():
        return public_snapshot_path(relative)
    return path


def build_aware_load(original_load: Callable[[Path], Any], path: Path) -> Any:
    return original_load(resolve_public_snapshot_path(path))


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"JSON snapshot non-oggetto: {path}")
    return value


def validate_public_snapshot() -> dict[str, int]:
    """Validate the public release snapshot without requiring source == dist."""
    public = _load(public_catalog_path())
    registry = _load(public_registry_path())
    canonical = _load(source_snapshot_path("data/site-data.json"))

    public_metrics = public.get("metrics")
    canonical_metrics = canonical.get("metrics")
    if not isinstance(public_metrics, dict) or not isinstance(canonical_metrics, dict):
        raise RuntimeError("Catalogo metriche non valido")

    missing = sorted(set(canonical_metrics) - set(public_metrics))
    if missing:
        raise RuntimeError(f"La build pubblica ha perso metriche canoniche: {missing}")

    canonical_towns = [town.get("name") for town in canonical.get("towns", [])]
    public_towns = [town.get("name") for town in public.get("towns", [])]
    if canonical_towns != public_towns:
        raise RuntimeError(f"Perimetro comuni alterato dalla materializzazione: {public_towns}")

    theme_membership(public)
    routes = route_owners(public, load_content_contract())

    external = sum(
        metric.get("dataStorage", {}).get("type") == "external-climate"
        for metric in public_metrics.values()
        if isinstance(metric, dict)
    )
    total = len(public_metrics)
    incorporated = total - external
    expected = {
        "total": int(registry["expectedMetricCount"]),
        "incorporated": int(registry["expectedInlineMetricCount"]),
        "external": int(registry["expectedExternalMetricCount"]),
    }
    actual = {"total": total, "incorporated": incorporated, "external": external}
    if actual != expected:
        raise RuntimeError(f"Registry pubblico non allineato al catalogo materializzato: {actual} != {expected}")

    return {
        "canonical_metrics": len(canonical_metrics),
        "public_metrics": total,
        "public_only_metrics": total - len(canonical_metrics),
        "routes": len(routes),
    }
