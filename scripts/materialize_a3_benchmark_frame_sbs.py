#!/usr/bin/env python3
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SITE_PATH = ROOT / "data" / "site-data.json"
SNAPSHOT_PATH = ROOT / "data" / "source-snapshots" / "a3-frame-sbs-benchmark-2023.json"
SNAPSHOT_REF = "data/source-snapshots/a3-frame-sbs-benchmark-2023.json"
EXPECTED_YEAR = "2023"
EXPECTED_SOURCE = "https://www.istat.it/tavole-di-dati/risultati-economici-delle-imprese-e-delle-multinazionali-a-livello-territoriale-anno-2023/"


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"JSON non-oggetto: {path}")
    return value


def save(path: Path, value: dict[str, Any]) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def finite(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def apply_benchmarks(site: dict[str, Any], snapshot: dict[str, Any]) -> dict[str, int]:
    metrics = site.get("metrics")
    benchmarks = snapshot.get("benchmarks")
    if not isinstance(metrics, dict) or not isinstance(benchmarks, dict):
        raise RuntimeError("Catalogo o snapshot benchmark Frame-SBS non valido")

    updated = 0
    for metric_id, values in sorted(benchmarks.items()):
        metric = metrics.get(metric_id)
        if not isinstance(metric, dict):
            raise RuntimeError(f"{metric_id}: metrica mancante")
        meta = metric.get("meta")
        if not isinstance(meta, dict):
            raise RuntimeError(f"{metric_id}: meta mancante")
        if str(meta.get("year") or "") != EXPECTED_YEAR:
            raise RuntimeError(f"{metric_id}: anno {meta.get('year')} != {EXPECTED_YEAR}")
        if str(metric.get("sourceUrl") or "") != EXPECTED_SOURCE:
            raise RuntimeError(f"{metric_id}: fonte pubblica non allineata al Frame-SBS governato")
        if str(meta.get("unit") or "") != str(values.get("unit") or ""):
            raise RuntimeError(
                f"{metric_id}: unità catalogo {meta.get('unit')} != snapshot {values.get('unit')}"
            )
        tuscany = values.get("tuscany")
        italy = values.get("italy")
        if not finite(tuscany) or not finite(italy):
            raise RuntimeError(f"{metric_id}: benchmark Toscana/Italia non numerico")

        meta["benchmark"] = {
            "year": 2023,
            "tuscany": tuscany,
            "italy": italy,
            "source": "Istat — Frame SBS Territoriale 2023 · Tavola 1 regioni",
            "url": snapshot["sourceUrl"],
            "sourceSnapshot": SNAPSHOT_REF,
            "note": (
                "Toscana e Italia provengono dalla stessa tavola regionale/nazionale "
                "e dallo stesso perimetro Frame-SBS della metrica comunale. "
                + str(values.get("derivation") or "")
            ),
        }
        updated += 1

    return {"metricsBenchmarked": updated, "pairsAcquired": updated}


def main() -> None:
    site = load(SITE_PATH)
    summary = apply_benchmarks(site, load(SNAPSHOT_PATH))
    save(SITE_PATH, site)
    print(
        "A3 benchmark Frame-SBS: "
        f"{summary['metricsBenchmarked']} metriche · "
        f"{summary['pairsAcquired']} coppie AVAILABLE_MISSING integrate."
    )


if __name__ == "__main__":
    main()
