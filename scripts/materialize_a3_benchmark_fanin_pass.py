#!/usr/bin/env python3
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "data" / "site-data.json"
AGRICULTURE_PUBLIC_SOURCE = ROOT / "data" / "source-snapshots" / "istat-agricoltura-territorio-2020.json"
SNAPSHOTS = (
    ROOT / "data" / "source-snapshots" / "a3-istat-agriculture-benchmark-2020.json",
    ROOT / "data" / "source-snapshots" / "a3-regione-toscana-tourism-benchmark-2025.json",
    ROOT / "data" / "source-snapshots" / "a3-ispra-environment-benchmark-2024.json",
    ROOT / "data" / "source-snapshots" / "a3-istat-agriculture-benchmark-2020-v2.json",
    ROOT / "data" / "source-snapshots" / "a3-agcom-benchmark-2025.json",
    ROOT / "data" / "source-snapshots" / "a3-ispra-environment-benchmark-2024-v2.json",
    ROOT / "data" / "source-snapshots" / "a3-istat-demography-mobility-benchmark-2024.json",
    ROOT / "data" / "source-snapshots" / "a3-ispra-soil-benchmark-2024.json",
)    ROOT / "data" / "source-snapshots" / "a3-regione-toscana-libraries-benchmark-2024.json",
)

def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"{path}: JSON non-oggetto")
    return value

def finite(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise RuntimeError(f"{label}: numerico atteso")
    result = float(value)
    if not math.isfinite(result):
        raise RuntimeError(f"{label}: valore non finito")
    return result

ALLOW_MISSING_PUBLIC = {
    "libraryActiveBorrowersPer100",
    "libraryLoansPerResident",
    "libraryWeeklyOpeningHours",
}

def public_rows(metric: dict[str, Any], metric_id: str) -> list[dict[str, Any]]:
    rows = metric.get("rows") or []
    if len(rows) != 7:
        raise RuntimeError(f"{metric_id}: righe pubbliche {len(rows)} != 7")
    for row in rows:
        value=row.get("value")
        if metric_id in ALLOW_MISSING_PUBLIC and value is None:
            continue
        finite(value, f"{metric_id}/{row.get('code') or row.get('town')}")
    return rows

def validate_agriculture_public(site: dict[str, Any]) -> None:
    source = load(AGRICULTURE_PUBLIC_SOURCE)
    towns = source.get("towns") or {}
    checks = {
        "agriculturalFarms": lambda row: finite(row.get("farms"), "farms"),
        "agriculturalUsedArea": lambda row: finite(row.get("sauLocalizedHa"), "sauLocalizedHa"),
        "averageAgriculturalFarmSize": lambda row: (
            finite(row.get("sauCenterHa"), "sauCenterHa")
            / finite(row.get("farmsWithSau"), "farmsWithSau")
        ),
        "irrigatedAgriculturalArea": lambda row: finite(row.get("irrigatedAreaHa"), "irrigatedAreaHa"),
    }
    for metric_id, expected_value in checks.items():
        metric = (site.get("metrics") or {}).get(metric_id) or {}
        rows = public_rows(metric, metric_id)
        for row in rows:
            code = str(row.get("code") or "")
            src = towns.get(code)
            if not isinstance(src, dict):
                raise RuntimeError(f"{metric_id}/{code}: snapshot agricolo assente")
            expected = expected_value(src)
            observed = finite(row.get("value"), f"{metric_id}/{code}")
            if not math.isclose(observed, expected, rel_tol=0.0, abs_tol=.02):
                raise RuntimeError(f"{metric_id}/{code}: {observed} != {expected}")

def main() -> None:
    site = load(SITE)
    validate_agriculture_public(site)
    metrics = site.get("metrics") or {}
    published: list[str] = []

    for snapshot_path in SNAPSHOTS:
        snapshot = load(snapshot_path)
        gate = snapshot.get("qualityGate") or {}
        if gate.get("status") != "PASS" or gate.get("errors") not in (None, []):
            raise RuntimeError(f"{snapshot_path.name}: quality gate non PASS")
        benchmarks = snapshot.get("benchmarks") or {}
        if not benchmarks:
            raise RuntimeError(f"{snapshot_path.name}: benchmark vuoti")
        source_url = str(snapshot.get("sourceUrl") or "").strip()
        if not source_url:
            raise RuntimeError(f"{snapshot_path.name}: sourceUrl assente")

        for metric_id, benchmark in benchmarks.items():
            metric = metrics.get(metric_id)
            if not isinstance(metric, dict):
                raise RuntimeError(f"{metric_id}: metrica pubblica assente")
            public_rows(metric, metric_id)
            meta = metric.setdefault("meta", {})
            existing = meta.get("benchmark")
            if isinstance(existing, dict) and any(
                isinstance(existing.get(scope), (int, float)) and not isinstance(existing.get(scope), bool)
                for scope in ("tuscany", "italy")
            ):
                raise RuntimeError(f"{metric_id}: benchmark già materializzato")

            year = str(benchmark.get("year") or "").strip()
            unit = str(benchmark.get("unit") or "").strip()
            if not year or not unit:
                raise RuntimeError(f"{metric_id}: year/unit benchmark assenti")
            tuscany = benchmark.get("tuscany")
            italy = benchmark.get("italy")
            if tuscany is None and italy is None:
                raise RuntimeError(f"{metric_id}: entrambi gli scope benchmark sono null")
            if tuscany is not None:
                finite(tuscany, f"{metric_id}/tuscany")
            if italy is not None:
                finite(italy, f"{metric_id}/italy")

            meta["benchmark"] = {
                "year": year,
                "tuscany": tuscany,
                "italy": italy,
                "source": snapshot.get("publisher"),
                "url": source_url,
                "sourceSnapshot": str(snapshot_path.relative_to(ROOT)).replace("\\", "/"),
                "note": "Benchmark A3 materializzato da artifact di acquisizione con quality gate metric-level PASS.",
            }
            published.append(metric_id)

    SITE.write_text(json.dumps(site, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    print(f"A3 benchmark fan-in materialized: {len(published)} metrics :: {', '.join(sorted(published))}")

if __name__ == "__main__":
    main()
