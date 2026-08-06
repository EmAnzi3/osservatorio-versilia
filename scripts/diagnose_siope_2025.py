#!/usr/bin/env python3
"""Compare every reconstructed SIOPE 2025 metric with the current published values."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import build_siope_history as builder

METRIC_COMPONENTS = {
    "siopePayments": "cash_payments",
    "currentPayments": "current_payments",
    "capitalPayments": "capital_payments",
    "cashReceiptsPerResident": "cash_receipts",
    "cashBalancePerResident": "cash_balance",
}


def main() -> None:
    data = json.loads(builder.DATA_PATH.read_text(encoding="utf-8"))
    discovery = json.loads(builder.DISCOVERY_PATH.read_text(encoding="utf-8"))
    session = builder.requests.Session()
    session.headers.update({
        "User-Agent": "OsservatorioVersilia/1.0 (+https://emanzi3.github.io/osservatorio-versilia/)",
        "Accept": "text/csv,*/*;q=0.8",
    })

    yearly: dict[str, dict[str, dict]] = {}
    sources: dict[str, dict] = {}
    for movement in ("entrata", "spesa"):
        label = f"{movement}-2025-toscana"
        package = discovery["datasets"][label]
        resource = builder.csv_resource(package)
        content, url = builder.download_csv(session, resource)
        parsed, audit = builder.parse_dataset(content, 2025, movement)
        yearly[movement] = parsed
        sources[label] = {
            "url": url,
            "bytes": len(content),
            "sha256": hashlib.sha256(content).hexdigest(),
            "selected_rows": audit.get("selected_rows"),
            "mapped_fields": audit.get("mapped_fields"),
        }

    raw: dict[str, dict] = {}
    for town in builder.TOWN_CODES:
        receipts = yearly["entrata"][town]
        payments = yearly["spesa"][town]
        raw[town] = {
            "population_receipts": receipts["population"],
            "population_payments": payments["population"],
            "cash_receipts": receipts["total"],
            "cash_payments": payments["total"],
            "current_payments": payments["current"],
            "capital_payments": payments["capital"],
            "other_payments": payments["total"] - payments["current"] - payments["capital"],
            "cash_balance": receipts["total"] - payments["total"],
            "selected_rows_receipts": receipts["selected_rows"],
            "selected_rows_payments": payments["selected_rows"],
        }

    comparisons: dict[str, dict[str, dict]] = {}
    mismatch_count = 0
    for metric, component in METRIC_COMPONENTS.items():
        expected = builder.current_values(data, metric)
        comparisons[metric] = {}
        for town in builder.TOWN_CODES:
            population = raw[town]["population_payments"]
            if metric == "cashReceiptsPerResident":
                population = raw[town]["population_receipts"]
            numerator = raw[town][component]
            calculated = numerator / population
            published = expected[town]
            delta = calculated - published
            ratio = calculated / published if published else None
            inferred_published_numerator = published * population
            numerator_gap = numerator - inferred_published_numerator
            mismatch = abs(delta) > 0.02
            mismatch_count += int(mismatch)
            comparisons[metric][town] = {
                "population": population,
                "numerator_reconstructed": numerator,
                "published_per_resident": published,
                "calculated_per_resident": calculated,
                "delta_per_resident": delta,
                "relative_delta_percent": ((ratio - 1) * 100) if ratio is not None else None,
                "inferred_published_numerator": inferred_published_numerator,
                "numerator_gap": numerator_gap,
                "mismatch_over_0_02": mismatch,
            }

    print(json.dumps({
        "sources": sources,
        "raw": raw,
        "comparisons": comparisons,
        "mismatch_count": mismatch_count,
    }, ensure_ascii=False, indent=2))

    if mismatch_count:
        raise SystemExit(f"Confronto diagnostico concluso: {mismatch_count} valori oltre 0,02 €/abitante")


if __name__ == "__main__":
    main()
