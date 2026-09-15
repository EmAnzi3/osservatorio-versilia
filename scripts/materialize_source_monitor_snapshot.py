#!/usr/bin/env python3
"""Materializza il catalogo pubblico effettivo per il Source Monitor, senza prerender."""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path

import build_static_brand as public_build
from source_policy import validate_registry

ROOT = Path(__file__).resolve().parents[1]
BUILD_BOUNDARY = (ROOT / "scripts" / "build_static_safe.py").resolve()
SNAPSHOT_FILES = (
    Path("data/site-data.json"),
    Path("data/source-registry.json"),
)


class _PublicCatalogReady(RuntimeError):
    """Sentinella interna: la catena dati è completa, il prerender non deve partire."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args()


def _snapshot_run_path(path_name, *args, **kwargs):
    """Riusa l'orchestrazione di produzione e si ferma al confine del prerender."""
    if Path(path_name).resolve() == BUILD_BOUNDARY:
        raise _PublicCatalogReady
    return public_build._run_path_with_fragilita_r3_fix(path_name, *args, **kwargs)


def _validate_materialized_snapshot() -> tuple[dict, dict]:
    data_path = ROOT / "data" / "site-data.json"
    registry_path = ROOT / "data" / "source-registry.json"
    data = json.loads(data_path.read_text(encoding="utf-8"))
    registry = json.loads(registry_path.read_text(encoding="utf-8"))

    metrics = data.get("metrics")
    if not isinstance(metrics, dict) or not metrics:
        raise RuntimeError("Catalogo pubblico materializzato privo di metriche")

    errors = validate_registry(data, registry)
    if errors:
        details = "; ".join(
            str(item.get("message") or item.get("code") or "policy fonte non valida")
            for item in errors[:12]
        )
        raise RuntimeError(f"Registry pubblico non valido per il monitor: {details}")

    external = sum(
        isinstance(metric, dict)
        and metric.get("dataStorage", {}).get("type") == "external-climate"
        for metric in metrics.values()
    )
    derived_counts = {
        "expectedMetricCount": len(metrics),
        "expectedInlineMetricCount": len(metrics) - external,
        "expectedExternalMetricCount": external,
    }
    for key, expected in derived_counts.items():
        declared = registry.get(key)
        if declared != expected:
            raise RuntimeError(
                f"Registry pubblico incoerente: {key}={declared!r}, derivato={expected}"
            )
    return data, registry


def materialize(output_dir: Path) -> dict[str, int | str]:
    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    previous_release_build = os.environ.get("OV_RELEASE_BUILD")
    previous_argv = list(sys.argv)
    original_run_path = public_build.runpy.run_path
    reached_boundary = False

    try:
        os.environ["OV_RELEASE_BUILD"] = "1"
        sys.argv = [str(public_build.IMPLEMENTATION)]
        with public_build.public_build_workspace():
            public_build._ORIGINAL_RUN_PATH(
                str(public_build.OPPORTUNITY_MATERIALIZER),
                run_name="__main__",
            )
            public_build.runpy.run_path = _snapshot_run_path
            try:
                public_build._ORIGINAL_RUN_PATH(
                    str(public_build.IMPLEMENTATION),
                    run_name="__main__",
                )
            except _PublicCatalogReady:
                reached_boundary = True
            finally:
                public_build.runpy.run_path = original_run_path

            if not reached_boundary:
                raise RuntimeError(
                    "La build pubblica non ha raggiunto il confine dati prima del prerender"
                )

            data, registry = _validate_materialized_snapshot()
            for relative in SNAPSHOT_FILES:
                source = ROOT / relative
                target = output_dir / relative.name
                shutil.copy2(source, target)

            metrics = data["metrics"]
            external = sum(
                isinstance(metric, dict)
                and metric.get("dataStorage", {}).get("type") == "external-climate"
                for metric in metrics.values()
            )
            result = {
                "version": str(data.get("version") or ""),
                "metrics": len(metrics),
                "inline": len(metrics) - external,
                "external": external,
                "sourceProfiles": len(registry.get("sourceProfiles") or {}),
            }
    finally:
        public_build.runpy.run_path = original_run_path
        sys.argv = previous_argv
        if previous_release_build is None:
            os.environ.pop("OV_RELEASE_BUILD", None)
        else:
            os.environ["OV_RELEASE_BUILD"] = previous_release_build

    print(json.dumps(result, ensure_ascii=False))
    return result


def main() -> int:
    args = parse_args()
    materialize(args.output_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
