#!/usr/bin/env python3
"""A3.5 lotto 4: componenti censuari Istat per rapporti già pubblicati."""
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SITE_PATH = ROOT / "data" / "site-data.json"
SNAPSHOT_PATH = ROOT / "data" / "source-snapshots" / "istat-sections-history-v1.8.0.json"

SOURCE = "Istat — Censimento permanente della popolazione, dati per sezione"
SOURCE_SNAPSHOT = "istat-sections-history-v1.8.0.json"
REFERENCE_YEAR = "2023"

TARGETS: dict[str, dict[str, Any]] = {
    "femaleEmploymentRate": {
        "unit": "percent",
        "numerator": "P103",
        "denominator": "female1564",
        "numeratorLabel": "Donne occupate 15–64 anni",
        "denominatorLabel": "Donne residenti 15–64 anni",
        "scale": 100.0,
        "formula": "P103 / female1564 × 100",
        "tolerance": 1e-6,
    },
    "maleEmploymentRate": {
        "unit": "percent",
        "numerator": "P102",
        "denominator": "male1564",
        "numeratorLabel": "Uomini occupati 15–64 anni",
        "denominatorLabel": "Uomini residenti 15–64 anni",
        "scale": 100.0,
        "formula": "P102 / male1564 × 100",
        "tolerance": 1e-6,
    },
    "housingStockPer1000": {
        "unit": "per1000",
        "numerator": "A8",
        "denominator": "P1",
        "numeratorLabel": "Abitazioni totali",
        "denominatorLabel": "Popolazione residente",
        "scale": 1000.0,
        "formula": "A8 / P1 × 1.000",
        "tolerance": 1e-6,
    },
    "nonOccupiedHomesPer1000": {
        "unit": "per1000",
        "numerator": "A3",
        "denominator": "P1",
        "numeratorLabel": "Abitazioni non occupate da residenti",
        "denominatorLabel": "Popolazione residente",
        "scale": 1000.0,
        "formula": "A3 / P1 × 1.000",
        "tolerance": 1e-6,
    },
    "vacantHomes": {
        "unit": "percent",
        "numerator": "A3",
        "denominator": "A8",
        "numeratorLabel": "Abitazioni non occupate da residenti",
        "denominatorLabel": "Abitazioni totali",
        "scale": 100.0,
        "formula": "A3 / A8 × 100",
        "tolerance": 0.051,
    },
    "singleHouseholds": {
        "unit": "percent",
        "numerator": "PF3",
        "denominator": "PF1",
        "numeratorLabel": "Famiglie unipersonali",
        "denominatorLabel": "Famiglie residenti",
        "scale": 100.0,
        "formula": "PF3 / PF1 × 100",
        "tolerance": 0.051,
    },
}


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def save(path: Path, value: dict[str, Any]) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _num(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise RuntimeError(f"{label}: valore numerico atteso")
    result = float(value)
    if not math.isfinite(result):
        raise RuntimeError(f"{label}: valore non finito")
    return result


def _raw_2023(snapshot: dict[str, Any]) -> dict[str, dict[str, Any]]:
    scope = snapshot.get("scope") or {}
    if scope.get("coverage") != "7/7":
        raise RuntimeError("Snapshot censuario senza copertura 7/7")
    years = {int(year) for year in scope.get("years") or []}
    if 2023 not in years:
        raise RuntimeError("Snapshot censuario senza anno 2023")

    accepted = {
        item.get("key")
        for item in snapshot.get("acceptedIndicators") or []
        if isinstance(item, dict)
    }
    missing = sorted(set(TARGETS) - accepted)
    if missing:
        raise RuntimeError(f"Indicatori non governati dallo snapshot: {missing}")

    rows = (snapshot.get("raw") or {}).get(REFERENCE_YEAR)
    if not isinstance(rows, list) or len(rows) != 7:
        raise RuntimeError("Snapshot censuario 2023 senza 7 righe comunali")
    result = {
        str(row["town"]): row
        for row in rows
        if isinstance(row, dict) and row.get("town")
    }
    if len(result) != 7:
        raise RuntimeError("Snapshot censuario 2023 con perimetro comunale non univoco")
    return result


def _rows_by_town(metric: dict[str, Any], metric_id: str) -> dict[str, dict[str, Any]]:
    rows = metric.get("rows")
    if not isinstance(rows, list):
        raise RuntimeError(f"{metric_id}: rows mancanti")
    result = {
        str(row["town"]): row
        for row in rows
        if isinstance(row, dict) and row.get("town")
    }
    if len(result) != 7:
        raise RuntimeError(f"{metric_id}: perimetro comunale atteso 7/7")
    return result


def apply_enrichment(site: dict[str, Any], snapshot: dict[str, Any]) -> dict[str, int]:
    metrics = site.get("metrics")
    if not isinstance(metrics, dict):
        raise RuntimeError("Catalogo senza metrics")

    raw = _raw_2023(snapshot)
    enriched_rows = 0

    for metric_id, cfg in TARGETS.items():
        metric = metrics.get(metric_id)
        if not isinstance(metric, dict):
            raise RuntimeError(f"Indicatore censuario mancante: {metric_id}")
        meta = metric.get("meta") if isinstance(metric.get("meta"), dict) else {}
        if meta.get("unit") != cfg["unit"]:
            raise RuntimeError(
                f"{metric_id}: unità inattesa {meta.get('unit')!r}, attesa {cfg['unit']!r}"
            )

        rows = _rows_by_town(metric, metric_id)
        if set(rows) != set(raw):
            raise RuntimeError(f"{metric_id}: Comuni non allineati allo snapshot censuario")

        for town, row in rows.items():
            raw_row = raw[town]
            numerator = _num(raw_row.get(cfg["numerator"]), f"{metric_id}/{town}: numeratore")
            denominator = _num(raw_row.get(cfg["denominator"]), f"{metric_id}/{town}: denominatore")
            if denominator == 0:
                raise RuntimeError(f"{metric_id}/{town}: denominatore nullo")
            observed = _num(row.get("value"), f"{metric_id}/{town}: valore pubblico")
            expected = numerator / denominator * float(cfg["scale"])
            if not math.isclose(
                observed,
                expected,
                rel_tol=0.0,
                abs_tol=float(cfg["tolerance"]),
            ):
                raise RuntimeError(
                    f"{metric_id}/{town}: valore pubblico {observed} non riconciliato "
                    f"con {expected}"
                )

            row["censusRatioComponents"] = {
                "referenceYear": REFERENCE_YEAR,
                "source": SOURCE,
                "sourceSnapshot": SOURCE_SNAPSHOT,
                "formula": cfg["formula"],
                "numeratorLabel": cfg["numeratorLabel"],
                "denominatorLabel": cfg["denominatorLabel"],
                "numerator": numerator,
                "denominator": denominator,
                "absolute": numerator,
                "normalized": observed,
            }
            enriched_rows += 1

    return {
        "metricsEnriched": len(TARGETS),
        "towns": len(raw),
        "rowsEnriched": enriched_rows,
        "ratioPairs": len(TARGETS),
        "absoluteNormalizedPairs": len(TARGETS),
        "pairsAcquired": len(TARGETS) * 2,
    }


def main() -> None:
    site = load(SITE_PATH)
    snapshot = load(SNAPSHOT_PATH)
    summary = apply_enrichment(site, snapshot)
    save(SITE_PATH, site)
    print(
        "A3.5 Istat Census components: "
        f"{summary['metricsEnriched']} metriche × {summary['towns']} comuni; "
        f"{summary['pairsAcquired']} coppie AVAILABLE_MISSING integrate "
        f"({summary['ratioPairs']} numeratore/denominatore, "
        f"{summary['absoluteNormalizedPairs']} assoluto/normalizzato)."
    )


if __name__ == "__main__":
    main()
