#!/usr/bin/env python3
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "data" / "site-data.json"
SNAP = ROOT / "data" / "source-snapshots" / "a3-istat-census-benchmark-2024.json"
SNAP_REF = "data/source-snapshots/a3-istat-census-benchmark-2024.json"
YEAR = "2024"

TARGETS: dict[str, dict[str, Any]] = {
    "employmentRate": {
        "unit": "percent", "section": "labour", "num": "employed", "den": "population",
        "formula": "employed / population × 100",
        "note": "Occupati 25–64 anni / residenti 25–64 anni × 100.",
    },
    "unemploymentRate": {
        "unit": "percent", "section": "labour", "num": "unemployed", "den": "active",
        "formula": "unemployed / active × 100",
        "note": "Disoccupati 25–64 anni / popolazione attiva 25–64 anni × 100.",
    },
    "activityRate": {
        "unit": "percent", "section": "labour", "num": "active", "den": "population",
        "formula": "active / population × 100",
        "note": "Popolazione attiva 25–64 anni / residenti 25–64 anni × 100.",
    },
    "tertiary": {
        "unit": "percent", "section": "education", "num": "tertiary", "den": "population",
        "formula": "tertiary / population × 100",
        "note": "Residenti 25–64 anni con titolo terziario / residenti 25–64 anni × 100.",
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
    if snap.get("profileId") != "istat-census-annual" or int(snap.get("referenceYear") or 0) != 2024:
        raise RuntimeError("Snapshot Census 2024 con profilo/anno inatteso")

    gate = snap.get("qualityGate") or {}
    expected_gate = {
        "status": "PASS",
        "publicMetricReconciliation": "4/4 metrics × 7/7 towns PASS",
        "commonMunicipalities": 7896,
        "tuscanyMunicipalities": 273,
        "labourInvalidMunicipalities": 0,
        "educationInvalidMunicipalities": 0,
        "labourZeroCellsFilled": 7,
        "educationZeroCellsFilled": 2994,
    }
    for key, expected in expected_gate.items():
        if gate.get(key) != expected:
            raise RuntimeError(f"Snapshot Census 2024 gate {key}: {gate.get(key)!r} != {expected!r}")

    source = snap.get("source") or {}
    if source.get("labourDataflow") != "DF_DCSS_ISTR_LAV_PEN_2_TV_3":
        raise RuntimeError("Snapshot Census 2024: labour dataflow inatteso")
    if source.get("educationDataflow") != "DF_DCSS_ISTR_LAV_PEN_2_TV_1":
        raise RuntimeError("Snapshot Census 2024: education dataflow inatteso")
    if source.get("referenceSnapshot") != "data/source-snapshots/istat-lavoro-istruzione-eta-genere-2024.json":
        raise RuntimeError("Snapshot Census 2024: snapshot comunale di riferimento inatteso")

    components = snap.get("components") or {}
    benchmarks = snap.get("benchmarks") or {}
    if set(benchmarks) != set(TARGETS):
        raise RuntimeError("Snapshot Census 2024 non 4/4")

    for scope in ("tuscany", "italy"):
        scope_components = components.get(scope) or {}
        labour = scope_components.get("labour") or {}
        education = scope_components.get("education") or {}
        close(labour.get("population"), education.get("population"), f"{scope}/population parity", 1e-9)
        close(
            finite(labour.get("employed"), f"{scope}/employed") + finite(labour.get("unemployed"), f"{scope}/unemployed"),
            finite(labour.get("active"), f"{scope}/active"),
            f"{scope}/labour identity",
            1e-6,
        )
        for metric_id, cfg in TARGETS.items():
            spec = benchmarks.get(metric_id) or {}
            if str(spec.get("year")) != YEAR or spec.get("unit") != cfg["unit"]:
                raise RuntimeError(f"{metric_id}/{scope}: anno/unità snapshot inattesi")
            if spec.get("formula") != cfg["formula"]:
                raise RuntimeError(f"{metric_id}/{scope}: formula snapshot inattesa")
            section = scope_components.get(cfg["section"]) or {}
            numerator = finite(section.get(cfg["num"]), f"{metric_id}/{scope}/numeratore")
            denominator = finite(section.get(cfg["den"]), f"{metric_id}/{scope}/denominatore")
            if denominator <= 0:
                raise RuntimeError(f"{metric_id}/{scope}: denominatore non positivo")
            expected = numerator / denominator * 100.0
            close(spec.get(scope), expected, f"{metric_id}/{scope}", 1e-12)


def validate_public(site: dict[str, Any], snap: dict[str, Any]) -> None:
    metrics = site.get("metrics")
    if not isinstance(metrics, dict):
        raise RuntimeError("Catalogo senza metrics")
    expected_rows = snap.get("publicRows") or {}
    if set(expected_rows) != set(TARGETS):
        raise RuntimeError("Snapshot Census 2024 senza publicRows 4/4")

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
            close(rows[town].get("value"), float(expected_value), f"{metric_id}/{town}", 0.11)


def main() -> None:
    site = load(SITE)
    snap = load(SNAP)
    validate_snapshot(snap)
    validate_public(site, snap)

    metrics = site["metrics"]
    benchmarks = snap["benchmarks"]
    source_url = snap["source"]["api"]
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
            "source": "Istat — Censimento permanente della popolazione",
            "url": metric.get("sourceUrl") or source_url,
            "sourceSnapshot": SNAP_REF,
            "note": cfg["note"] + " Toscana e Italia sono ricalcolate aggregando i conteggi comunali SDMX 2024 prima del calcolo del tasso; non sono medie di percentuali comunali.",
        }
        updated += 1

    SITE.write_text(json.dumps(site, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"A3 benchmark Census 2024: {updated} metriche Toscana/Italia materializzate; gate 4/4 × 7/7 PASS.")


if __name__ == "__main__":
    main()
