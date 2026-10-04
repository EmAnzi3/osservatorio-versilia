#!/usr/bin/env python3
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "data" / "site-data.json"
SNAP = ROOT / "data" / "source-snapshots" / "a3-istat-census-benchmark-2023.json"
SNAP_REF = "data/source-snapshots/a3-istat-census-benchmark-2023.json"
YEAR = "2023"

TARGETS: dict[str, dict[str, Any]] = {
    "femaleEmploymentRate": {
        "unit": "percent", "num": "P103", "den": "female1564", "scale": 100.0,
        "formula": "P103 / female1564 × 100",
        "note": "Donne occupate 15–64 anni / donne residenti 15–64 anni × 100.",
    },
    "maleEmploymentRate": {
        "unit": "percent", "num": "P102", "den": "male1564", "scale": 100.0,
        "formula": "P102 / male1564 × 100",
        "note": "Uomini occupati 15–64 anni / uomini residenti 15–64 anni × 100.",
    },
    "housingStockPer1000": {
        "unit": "per1000", "num": "A8", "den": "P1", "scale": 1000.0,
        "formula": "A8 / P1 × 1000",
        "note": "Abitazioni censite ogni 1.000 residenti.",
    },
    "nonOccupiedHomesPer1000": {
        "unit": "per1000", "num": "A3", "den": "P1", "scale": 1000.0,
        "formula": "A3 / P1 × 1000",
        "note": "Abitazioni non occupate da residenti ogni 1.000 residenti.",
    },
    "vacantHomes": {
        "unit": "percent", "num": "A3", "den": "A8", "scale": 100.0,
        "formula": "A3 / A8 × 100",
        "note": "Abitazioni non occupate da residenti / abitazioni totali × 100.",
    },
    "singleHouseholds": {
        "unit": "percent", "num": "PF3", "den": "PF1", "scale": 100.0,
        "formula": "PF3 / PF1 × 100",
        "note": "Famiglie unipersonali / famiglie residenti × 100.",
    },
    "cohabitingHouseholds": {
        "unit": "percent", "num": "PF9", "den": "PF1", "scale": 100.0,
        "formula": "PF9 / PF1 × 100",
        "note": "Famiglie coabitanti / famiglie residenti × 100.",
    },
    "employmentGenderGap": {
        "unit": "percentagePoints", "formula": "maleEmploymentRate − femaleEmploymentRate",
        "note": "Differenza in punti percentuali tra il tasso di occupazione maschile e femminile 15–64 anni.",
    },
}


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"JSON non-oggetto: {path}")
    return value


def finite(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise RuntimeError(f"{label}: valore numerico atteso")
    result = float(value)
    if not math.isfinite(result):
        raise RuntimeError(f"{label}: valore non finito")
    return result


def close(actual: Any, expected: float, label: str, tol: float = 1e-10) -> None:
    value = finite(actual, label)
    if not math.isclose(value, float(expected), rel_tol=0.0, abs_tol=tol):
        raise RuntimeError(f"{label}: {value} != {expected}")


def validate_snapshot(snap: dict[str, Any]) -> None:
    if snap.get("profileId") != "istat-census-annual" or int(snap.get("referenceYear") or 0) != 2023:
        raise RuntimeError("Snapshot Census benchmark con profilo/anno inatteso")
    gate = snap.get("qualityGate") or {}
    if gate.get("status") != "PASS":
        raise RuntimeError("Snapshot Census benchmark senza qualityGate PASS")
    if gate.get("tuscanyVersiliaReconciliation") != "7/7 PASS":
        raise RuntimeError("Snapshot Census benchmark senza riconciliazione Versilia 7/7")
    if gate.get("publicMetricReconciliation") != "8/8 metrics × 7/7 towns PASS":
        raise RuntimeError("Snapshot Census benchmark senza riconciliazione pubblica 8/8 × 7/7")
    source = snap.get("source") or {}
    if int(source.get("regionalWorkbookCount") or 0) != 20:
        raise RuntimeError("Snapshot Census benchmark senza 20 file regionali")
    if source.get("sha256") != "05661a6e248d4241c9fdd1b1fa1e740eae0706dd3fcfdbeb366f608269bfeb45":
        raise RuntimeError("Snapshot Census benchmark con SHA ZIP inatteso")

    raw = snap.get("raw") or {}
    benchmarks = snap.get("benchmarks") or {}
    if set(benchmarks) != set(TARGETS):
        raise RuntimeError("Snapshot Census benchmark non 8/8")

    for scope in ("tuscany", "italy"):
        scope_raw = raw.get(scope) or {}
        for metric_id, cfg in TARGETS.items():
            spec = benchmarks.get(metric_id) or {}
            if str(spec.get("year")) != YEAR or spec.get("unit") != cfg["unit"]:
                raise RuntimeError(f"{metric_id}/{scope}: anno/unità snapshot inattesi")
            if spec.get("formula") != cfg["formula"]:
                raise RuntimeError(f"{metric_id}/{scope}: formula snapshot inattesa")
            if metric_id == "employmentGenderGap":
                male = finite(benchmarks["maleEmploymentRate"][scope], f"{scope}/male")
                female = finite(benchmarks["femaleEmploymentRate"][scope], f"{scope}/female")
                expected = male - female
            else:
                numerator = finite(scope_raw.get(cfg["num"]), f"{metric_id}/{scope}/numeratore")
                denominator = finite(scope_raw.get(cfg["den"]), f"{metric_id}/{scope}/denominatore")
                if denominator <= 0:
                    raise RuntimeError(f"{metric_id}/{scope}: denominatore non positivo")
                expected = numerator / denominator * float(cfg["scale"])
            close(spec.get(scope), expected, f"{metric_id}/{scope}", 1e-12)


def validate_public(site: dict[str, Any], snap: dict[str, Any]) -> None:
    metrics = site.get("metrics")
    if not isinstance(metrics, dict):
        raise RuntimeError("Catalogo senza metrics")
    expected_rows = snap.get("publicRows") or {}
    if set(expected_rows) != set(TARGETS):
        raise RuntimeError("Snapshot Census senza publicRows 8/8")

    for metric_id, cfg in TARGETS.items():
        metric = metrics.get(metric_id)
        if not isinstance(metric, dict):
            raise RuntimeError(f"{metric_id}: metrica pubblica mancante")
        meta = metric.get("meta") or {}
        if str(meta.get("year")) != YEAR or meta.get("unit") != cfg["unit"]:
            raise RuntimeError(f"{metric_id}: anno/unità pubblici inattesi")
        rows = {
            str(row.get("town")): row
            for row in (metric.get("rows") or [])
            if isinstance(row, dict) and row.get("town")
        }
        expected = expected_rows[metric_id]
        if set(rows) != set(expected) or len(rows) != 7:
            raise RuntimeError(f"{metric_id}: perimetro pubblico non 7/7")
        for town, expected_value in expected.items():
            close(rows[town].get("value"), float(expected_value), f"{metric_id}/{town}", 1e-12)


def main() -> None:
    site = load(SITE)
    snap = load(SNAP)
    validate_snapshot(snap)
    validate_public(site, snap)

    metrics = site["metrics"]
    benchmarks = snap["benchmarks"]
    source_url = snap["source"]["url"]
    updated = 0

    for metric_id, cfg in TARGETS.items():
        metric = metrics[metric_id]
        meta = metric.get("meta")
        if not isinstance(meta, dict):
            raise RuntimeError(f"{metric_id}: meta mancante")
        spec = benchmarks[metric_id]
        meta["benchmark"] = {
            "year": YEAR,
            "tuscany": finite(spec["tuscany"], f"{metric_id}/tuscany"),
            "italy": finite(spec["italy"], f"{metric_id}/italy"),
            "source": "Istat — Censimento permanente della popolazione e delle abitazioni",
            "url": metric.get("sourceUrl") or source_url,
            "sourceSnapshot": SNAP_REF,
            "note": cfg["note"] + " Toscana e Italia sono ricalcolate sui conteggi aggregati dei file regionali ufficiali 2023.",
        }
        updated += 1

    SITE.write_text(json.dumps(site, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"A3 benchmark Census 2023: {updated} metriche Toscana/Italia materializzate; gate 8/8 × 7/7 PASS.")


if __name__ == "__main__":
    main()
