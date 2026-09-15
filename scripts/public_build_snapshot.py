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
from source_policy import validate_registry

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
    """Return the materialized catalog that is actually published."""
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


def effective_public_catalog() -> dict[str, Any]:
    """Load the derived Effective Public Catalog from the build output.

    This is a reproducible view of the release after public materializers have
    run. It is not a second canonical inventory: ``data/site-data.json`` remains
    the canonical source catalog.
    """
    return _load(public_catalog_path())


def _format_ids(values: set[str] | list[str], limit: int = 12) -> str:
    ordered = sorted(values)
    shown = ", ".join(ordered[:limit])
    if len(ordered) > limit:
        shown += f", ... (+{len(ordered) - limit})"
    return shown


def validate_public_governance() -> dict[str, int]:
    """Validate ID-level governance invariants on the materialized release.

    Operational freshness and last-check coverage belong to the source monitor
    and are intentionally not part of this structural publication gate.
    """
    public = effective_public_catalog()
    registry = _load(public_registry_path())
    status_path = DIST / "data/data-status.json"
    if not status_path.is_file():
        raise RuntimeError(f"Stato dati pubblico mancante: {status_path}")
    status = _load(status_path)

    public_metrics = public.get("metrics")
    status_metrics = status.get("metrics")
    if not isinstance(public_metrics, dict):
        raise RuntimeError("Catalogo pubblico privo di metriche valide")
    if not isinstance(status_metrics, list):
        raise RuntimeError("Stato dati pubblico privo della lista metriche")

    public_ids = set(public_metrics)
    status_ids_list: list[str] = []
    for row in status_metrics:
        if not isinstance(row, dict):
            raise RuntimeError("Voce non valida nello Stato dati pubblico")
        metric_id = str(row.get("key") or "").strip()
        if not metric_id:
            raise RuntimeError("Voce senza ID nello Stato dati pubblico")
        status_ids_list.append(metric_id)

    duplicate_status_ids = {
        metric_id
        for metric_id in status_ids_list
        if status_ids_list.count(metric_id) > 1
    }
    if duplicate_status_ids:
        raise RuntimeError(
            "ID duplicati nello Stato dati: " + _format_ids(duplicate_status_ids)
        )

    status_ids = set(status_ids_list)
    missing_status = public_ids - status_ids
    extra_status = status_ids - public_ids
    if missing_status or extra_status:
        details = []
        if missing_status:
            details.append(
                "mancanti in Stato dati: " + _format_ids(missing_status)
            )
        if extra_status:
            details.append(
                "extra in Stato dati: " + _format_ids(extra_status)
            )
        raise RuntimeError("ID pubblici non allineati: " + "; ".join(details))

    metric_count = status.get("metricCount")
    if metric_count != len(public_ids):
        raise RuntimeError(
            "Conteggio Stato dati non allineato al catalogo pubblico: "
            f"{metric_count} != {len(public_ids)}"
        )

    policy_errors = validate_registry(public, registry)
    if policy_errors:
        metric_ids = {
            str(error.get("metric") or "").strip()
            for error in policy_errors
            if str(error.get("metric") or "").strip()
        }
        messages = {
            str(error.get("message") or "").strip()
            for error in policy_errors
            if str(error.get("message") or "").strip()
        }
        details = "; ".join(sorted(messages))
        if metric_ids:
            details += "; metriche: " + _format_ids(metric_ids)
        raise RuntimeError("Policy fonte del catalogo pubblico non valide: " + details)

    return {
        "public_metrics": len(public_ids),
        "status_metrics": len(status_ids),
        "source_policies": len(public_ids),
    }


def validate_public_snapshot() -> dict[str, int]:
    """Validate the public release snapshot without requiring source == dist."""
    public = effective_public_catalog()
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
