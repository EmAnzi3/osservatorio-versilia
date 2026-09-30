#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SITE_PATH = ROOT / "data" / "site-data.json"
SNAPSHOT_PATH = ROOT / "data" / "source-snapshots" / "fuel-history-mimit-monthly.json"
SNAPSHOT_REF = "data/source-snapshots/fuel-history-mimit-monthly.json"
METRIC_ID = "fuelPrices"


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"JSON non-oggetto: {path}")
    return value


def save(path: Path, value: dict[str, Any]) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def apply_history(site: dict[str, Any], snapshot: dict[str, Any]) -> dict[str, int]:
    metric = (site.get("metrics") or {}).get(METRIC_ID)
    if not isinstance(metric, dict):
        raise RuntimeError(f"{METRIC_ID}: metrica mancante")
    rows = metric.get("rows")
    if not isinstance(rows, list) or len(rows) != 7:
        raise RuntimeError(f"{METRIC_ID}: attese 7 righe comunali")

    points = snapshot.get("points")
    if not isinstance(points, list) or len(points) < 2:
        raise RuntimeError("Snapshot MIMIT: storico mensile insufficiente")
    ordered = sorted(points, key=lambda point: str(point.get("referenceDate") or ""))
    years = [str(point.get("referenceDate") or "") for point in ordered]
    if any(not year for year in years) or len(set(years)) != len(years):
        raise RuntimeError("Snapshot MIMIT: periodi mancanti o duplicati")

    towns = set(snapshot.get("towns") or [])
    row_towns = {str(row.get("town") or "") for row in rows}
    if towns != row_towns:
        raise RuntimeError(f"Snapshot MIMIT: perimetro Comuni non allineato ({towns} != {row_towns})")

    enriched = 0
    available = 0
    for row in rows:
        town = str(row["town"])
        readings = [
            (point.get("towns") or {}).get(town) or {}
            for point in ordered
        ]
        benzina = [reading.get("benzina") for reading in readings]
        gasolio = [reading.get("gasolio") for reading in readings]
        valid_benzina = sum(value is not None for value in benzina)
        valid_gasolio = sum(value is not None for value in gasolio)
        history_available = valid_benzina >= 2 or valid_gasolio >= 2

        row["series"] = {
            "years": list(years),
            "values": list(benzina),
            "unit": "eurliter",
            "source": "MIMIT",
            "sourceSnapshot": SNAPSHOT_REF,
            "note": snapshot.get("statistic"),
        }
        row["componentSeries"] = {
            **(row.get("componentSeries") or {}),
            "Benzina self": {
                "years": list(years),
                "values": list(benzina),
                "unit": "eurliter",
                "source": "MIMIT",
                "sourceSnapshot": SNAPSHOT_REF,
            },
            "Gasolio self": {
                "years": list(years),
                "values": list(gasolio),
                "unit": "eurliter",
                "source": "MIMIT",
                "sourceSnapshot": SNAPSHOT_REF,
            },
        }
        row["fuelHistoryAvailable"] = history_available
        enriched += 1
        available += int(history_available)

    meta = metric.setdefault("meta", {})
    meta["historySourceSnapshot"] = SNAPSHOT_REF
    meta["historyFrequency"] = snapshot.get("frequency") or "monthly"
    meta["historyPeriodStart"] = years[0]
    meta["historyPeriodEnd"] = years[-1]

    if available < 6:
        raise RuntimeError(f"{METRIC_ID}: storico disponibile solo per {available}/7 Comuni")

    return {
        "metricsEnriched": 1,
        "rowsEnriched": enriched,
        "rowsWithHistory": available,
        "periods": len(years),
        "pairsAcquired": 1,
    }


def main() -> None:
    site = load(SITE_PATH)
    summary = apply_history(site, load(SNAPSHOT_PATH))
    save(SITE_PATH, site)
    print(
        "A3 history fuel: "
        f"{summary['pairsAcquired']} coppia acquisita · "
        f"{summary['rowsWithHistory']}/7 Comuni · "
        f"{summary['periods']} mesi materializzati."
    )


if __name__ == "__main__":
    main()
