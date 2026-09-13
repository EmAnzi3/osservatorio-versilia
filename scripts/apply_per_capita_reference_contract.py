#!/usr/bin/env python3
"""Uniforma il benchmark UI degli indicatori pro capite al vero aggregato Versilia.

Il contratto si applica a tutti gli indicatori, legacy e nuovi, che:
- sono espressi per residente / per abitante / pro capite;
- espongono un aggregato territoriale numerico riproducibile.

Le metriche che dichiarano esplicitamente una media semplice/aritmetica,
una mediana o una copertura parziale restano escluse: non vengono trasformate
in un aggregato territoriale che la fonte non consente di ricostruire.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "site-data.json"

SIMPLE_REFERENCE_MARKERS = (
    "media semplice",
    "media aritmetica",
    "media comunale",
    "mediana",
    "comuni con dato disponibile",
)

EXPECTED_EXCEPTIONS = {
    "roadFinesPerResident",
    "wasteServiceCost",
    "socialSpendingPerResident",
    "libraryLoansPerResident",
}

COMPARISON_NOTE = (
    "Il confronto usa il valore pro capite Versilia calcolato sull’aggregato "
    "territoriale, non la media semplice dei valori comunali."
)


def is_numeric(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def is_per_capita_metric(metric: dict) -> bool:
    meta = metric.get("meta", {})
    if meta.get("compositeType"):
        return False
    label = str(meta.get("label", "")).lower()
    unit = str(meta.get("unit", "")).strip().lower()
    return (
        "per residente" in label
        or "per abitante" in label
        or "pro capite" in label
        or unit in {"eurperresident", "€/ab", "€/ab."}
    )


def has_territorial_per_capita_aggregate(metric: dict) -> bool:
    if not is_per_capita_metric(metric):
        return False
    aggregate = metric.get("aggregate") or {}
    if not is_numeric(aggregate.get("value")):
        return False
    method = f"{aggregate.get('label', '')} {aggregate.get('note', '')}".lower()
    return not any(marker in method for marker in SIMPLE_REFERENCE_MARKERS)


def main() -> None:
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    metrics = data.get("metrics", {})

    eligible: list[str] = []
    exceptions: set[str] = set()
    for key, metric in metrics.items():
        if not is_per_capita_metric(metric):
            continue
        aggregate = metric.get("aggregate") or {}
        if not is_numeric(aggregate.get("value")):
            continue
        if not has_territorial_per_capita_aggregate(metric):
            exceptions.add(key)
            continue

        eligible.append(key)
        aggregate["label"] = "Valore pro capite Versilia"
        meta = metric.setdefault("meta", {})
        meta["comparisonReference"] = "aggregate"
        meta["comparisonLabel"] = "valore pro capite Versilia"
        meta["comparisonOverline"] = "Rispetto al valore pro capite Versilia"
        meta["comparisonNote"] = COMPARISON_NOTE

    if exceptions != EXPECTED_EXCEPTIONS:
        raise RuntimeError(
            "Contratto pro capite: eccezioni inattese: "
            f"attese={sorted(EXPECTED_EXCEPTIONS)}, trovate={sorted(exceptions)}"
        )
    if not eligible:
        raise RuntimeError("Contratto pro capite: nessun indicatore eleggibile")

    DATA_PATH.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        "Contratto pro capite Versilia applicato a "
        f"{len(eligible)} indicatori; eccezioni metodologiche: {', '.join(sorted(exceptions))}"
    )


if __name__ == "__main__":
    main()
