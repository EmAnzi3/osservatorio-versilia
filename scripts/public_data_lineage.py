#!/usr/bin/env python3
"""Derive the minimum source→acquisition→materialization→metric→view lineage."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from content_contract import load_contract as load_content_contract
from content_contract import route_owners, storage_type, theme_membership, visualization_family
from ephemeral_build_workspace import load_build_materialization_contract
from public_build_snapshot import effective_public_catalog, public_registry_path
from source_policy import resolve_metric_policy

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
LINEAGE_PATH = DIST / "data" / "data-lineage.json"


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"JSON non-oggetto: {path}")
    return value


def _direct_build_script_refs() -> set[str]:
    refs: set[str] = set()
    for relative in ("scripts/build_static_brand.py", "scripts/build_static_brand_impl.py"):
        text = (ROOT / relative).read_text(encoding="utf-8")
        for name in re.findall(r'ROOT\s*/\s*"scripts"\s*/\s*"([^\"]+\.py)"', text):
            base = Path(name).name
            if base.startswith(("materialize_", "apply_", "patch_", "refine_", "prepare_")) or base in {
                "run_invalsi_v138_runtime.py",
            }:
                refs.add(f"scripts/{name}")
    return refs


def validate_materialization_chain() -> list[str]:
    contract = load_build_materialization_contract()
    if contract.get("schemaVersion") != 2:
        raise RuntimeError("build-materialization-contract deve usare schemaVersion 2 per la lineage")
    materializers = [str(value) for value in contract.get("publicMaterializers") or []]
    if len(materializers) != len(set(materializers)):
        raise RuntimeError("Materializzatori pubblici duplicati nel contratto build")
    missing_paths = [value for value in materializers if not (ROOT / value).is_file()]
    if missing_paths:
        raise RuntimeError(f"Materializzatori dichiarati assenti: {missing_paths}")
    direct_refs = _direct_build_script_refs()
    undeclared = sorted(direct_refs - set(materializers))
    if undeclared:
        raise RuntimeError(f"Passaggi build pubblici non dichiarati nella lineage: {undeclared}")
    return materializers


def _route_by_metric(data: dict[str, Any]) -> dict[str, str]:
    result: dict[str, str] = {}
    for path, owner in route_owners(data, load_content_contract()).items():
        if owner.startswith("indicator:"):
            result[owner.split(":", 1)[1]] = "/" + path.as_posix().removesuffix("index.html")
        elif owner.startswith("special-route:"):
            result[owner.split(":", 1)[1]] = "/" + path.as_posix().removesuffix("index.html")
    return result


def build_lineage() -> dict[str, Any]:
    public = effective_public_catalog()
    canonical = _load(ROOT / "data" / "site-data.json")
    registry = _load(public_registry_path())
    metrics = public.get("metrics")
    canonical_metrics = canonical.get("metrics")
    if not isinstance(metrics, dict) or not isinstance(canonical_metrics, dict):
        raise RuntimeError("Catalogo metriche non valido per la lineage")
    membership = theme_membership(public)
    routes = _route_by_metric(public)
    chain = validate_materialization_chain()

    rows: list[dict[str, Any]] = []
    for key, metric in metrics.items():
        if not isinstance(metric, dict):
            continue
        meta = metric.get("meta") if isinstance(metric.get("meta"), dict) else {}
        policy = resolve_metric_policy(key, metric, registry)
        kind = storage_type(metric)
        path = routes.get(key)
        if kind == "external-climate":
            path = "/confronta/meteo-clima/"
        if not path:
            raise RuntimeError(f"Visualizzazione pubblica non risolta per {key}")
        rows.append(
            {
                "key": key,
                "label": str(meta.get("label") or key),
                "theme": membership[key],
                "source": {
                    "publisher": str(policy.get("publisher") or ""),
                    "url": str(policy.get("sourceUrl") or metric.get("sourceUrl") or ""),
                    "profileId": str(policy.get("profileId") or ""),
                },
                "acquisition": {
                    "method": str(policy.get("acquisitionMethod") or ""),
                    "evidenceRoot": "data/source-snapshots/",
                },
                "transformation": {
                    "origin": "canonical" if key in canonical_metrics else "materialized",
                    "canonicalCatalog": "data/site-data.json",
                    "materializationChainRef": "$.materializationChain",
                },
                "indicator": key,
                "visualization": {
                    "storageType": kind,
                    "family": visualization_family(metric),
                    "path": path,
                },
            }
        )

    return {
        "schemaVersion": 1,
        "catalogVersion": str(public.get("version") or ""),
        "catalogUpdated": str(public.get("updated") or ""),
        "metricCount": len(rows),
        "canonicalMetricCount": len(canonical_metrics),
        "materializedMetricCount": len(rows) - len(canonical_metrics),
        "materializationChain": chain,
        "metrics": rows,
    }


def write_lineage() -> dict[str, Any]:
    lineage = build_lineage()
    LINEAGE_PATH.parent.mkdir(parents=True, exist_ok=True)
    LINEAGE_PATH.write_text(json.dumps(lineage, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return lineage


def validate_lineage() -> dict[str, Any]:
    expected = build_lineage()
    if not LINEAGE_PATH.is_file():
        raise RuntimeError("Artifact lineage pubblico mancante")
    actual = _load(LINEAGE_PATH)
    if actual != expected:
        raise RuntimeError("Artifact lineage pubblico non riproducibile dalla release corrente")
    public_ids = set(effective_public_catalog().get("metrics") or {})
    lineage_ids = {str(row.get("key") or "") for row in actual.get("metrics") or []}
    if public_ids != lineage_ids:
        raise RuntimeError("ID lineage non allineati al catalogo pubblico")
    return actual


if __name__ == "__main__":
    lineage = write_lineage()
    print(
        f"Lineage pubblica derivata: {lineage['metricCount']} indicatori · "
        f"{len(lineage['materializationChain'])} passaggi dichiarati."
    )
