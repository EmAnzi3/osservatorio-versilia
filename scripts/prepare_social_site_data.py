#!/usr/bin/env python3
"""Prepara in CI una vista temporanea delle serie storiche per il Social Kit.

Il dataset canonico non viene modificato nel repository: il workflow opera su un
checkout effimero. Per le sole metriche pianificate, quando i sette Comuni hanno
anni storici non perfettamente coincidenti, conserva l'ultimo intervallo annuale
continuo comune che termina nell'anno corrente della metrica.

Non vengono inventati, interpolati o sostituiti valori mancanti.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SITE_DATA = ROOT / "data" / "site-data.json"


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def planned_metrics(plan: dict[str, Any]) -> list[str]:
    keys: list[str] = []
    for item in plan.get("scheduled", []):
        key = item.get("metric")
        if key and key not in keys:
            keys.append(key)
    return keys


def normalize_metric(metric_key: str, metric: dict[str, Any]) -> tuple[bool, str]:
    rows = metric.get("rows") or []
    if not rows or not all(row.get("series") for row in rows):
        return False, "nessuna serie completa 7/7 da armonizzare"

    year_maps: list[dict[int, Any]] = []
    year_lists: list[list[int]] = []
    for row in rows:
        series = row["series"]
        years = [int(value) for value in series.get("years", [])]
        values = list(series.get("values", []))
        if not years or len(years) != len(values):
            raise ValueError(f"{metric_key}: serie non valida per {row.get('town', 'comune sconosciuto')}")
        if len(set(years)) != len(years):
            raise ValueError(f"{metric_key}: anni duplicati per {row.get('town', 'comune sconosciuto')}")
        year_lists.append(years)
        year_maps.append(dict(zip(years, values)))

    if all(years == year_lists[0] for years in year_lists[1:]):
        return False, f"serie già omogenea {year_lists[0][0]}–{year_lists[0][-1]}"

    current = int(metric.get("meta", {}).get("year", max(year_lists[0])))
    common = set(year_lists[0])
    for years in year_lists[1:]:
        common.intersection_update(years)

    if current not in common:
        raise ValueError(f"{metric_key}: anno corrente {current} non presente per tutti i Comuni")

    start = current
    while start - 1 in common:
        start -= 1
    common_suffix = list(range(start, current + 1))
    if len(common_suffix) < 2:
        raise ValueError(f"{metric_key}: intervallo storico comune insufficiente")

    for row, mapping in zip(rows, year_maps):
        row["series"] = {
            "years": common_suffix,
            "values": [mapping[year] for year in common_suffix],
        }

    return True, f"armonizzata sul periodo comune continuo {start}–{current}"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", required=True, help="week.json prodotto da plan_social_week.py")
    args = parser.parse_args()

    plan = load(Path(args.plan))
    site = load(SITE_DATA)
    changed = False

    for key in planned_metrics(plan):
        metric = site.get("metrics", {}).get(key)
        if not metric:
            print(f"{key}: metrica assente, nessuna normalizzazione")
            continue
        normalized, message = normalize_metric(key, metric)
        changed = changed or normalized
        print(f"{key}: {message}")

    if changed:
        SITE_DATA.write_text(json.dumps(site, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print("Vista temporanea data/site-data.json aggiornata per il rendering social")
    else:
        print("Nessuna normalizzazione temporanea necessaria")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
