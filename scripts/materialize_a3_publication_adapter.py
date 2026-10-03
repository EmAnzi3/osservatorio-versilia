#!/usr/bin/env python3
"""Normalize A3-acquired public history companions into the canonical UI series contract."""
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SITE_PATH = ROOT / "data" / "site-data.json"
_METADATA_KEYS = ("source", "sourceUrl", "sourceSnapshot", "note")


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"JSON non-oggetto: {path}")
    return value


def save(path: Path, value: dict[str, Any]) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _number(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise RuntimeError(f"{label}: valore storico non numerico")
    result = float(value)
    if not math.isfinite(result):
        raise RuntimeError(f"{label}: valore storico non finito")
    return result


def _canonical_history(history: dict[str, Any], label: str) -> tuple[list[Any], list[float]]:
    points = history.get("series")
    if isinstance(points, list):
        if len(points) < 2 or not all(isinstance(item, dict) for item in points):
            raise RuntimeError(f"{label}: a3History.series non valida")
        periods: list[Any] = []
        values: list[float] = []
        for index, point in enumerate(points):
            period = point.get("year", point.get("period"))
            if period in (None, ""):
                raise RuntimeError(f"{label}: periodo storico mancante al punto {index}")
            periods.append(period)
            values.append(_number(point.get("value"), f"{label}/{period}"))
    else:
        periods = history.get("periods")
        values_raw = history.get("values")
        if not isinstance(periods, list) or not isinstance(values_raw, list):
            raise RuntimeError(f"{label}: a3History senza series o periods/values")
        if len(periods) < 2 or len(periods) != len(values_raw):
            raise RuntimeError(f"{label}: periods/values non allineati")
        values = [_number(value, f"{label}/{period}") for period, value in zip(periods, values_raw, strict=True)]

    normalized_periods = [str(period).strip() for period in periods]
    if any(not period for period in normalized_periods):
        raise RuntimeError(f"{label}: periodo storico vuoto")
    if len(set(normalized_periods)) != len(normalized_periods):
        raise RuntimeError(f"{label}: periodi storici duplicati")
    return list(periods), values


def _same_series(existing: dict[str, Any], periods: list[Any], values: list[float]) -> bool:
    years = existing.get("years")
    existing_values = existing.get("values")
    if not isinstance(years, list) or not isinstance(existing_values, list):
        return False
    if [str(item) for item in years] != [str(item) for item in periods] or len(existing_values) != len(values):
        return False
    for left, right in zip(existing_values, values, strict=True):
        if isinstance(left, bool) or not isinstance(left, (int, float)):
            return False
        if not math.isclose(float(left), float(right), rel_tol=0.0, abs_tol=1e-10):
            return False
    return True


def _adapt_holder(holder: dict[str, Any], label: str) -> bool:
    history = holder.get("a3History")
    if not isinstance(history, dict):
        return False
    periods, values = _canonical_history(history, label)
    existing = holder.get("series")
    if isinstance(existing, dict) and existing:
        if not _same_series(existing, periods, values):
            raise RuntimeError(f"{label}: series pubblica già presente ma diversa da a3History")
        canonical = dict(existing)
    elif existing in (None, {}, []):
        canonical = {"years": periods, "values": values}
    else:
        raise RuntimeError(f"{label}: series pubblica di tipo inatteso")

    for key in _METADATA_KEYS:
        value = history.get(key)
        if value not in (None, "") and key not in canonical:
            canonical[key] = value
    holder["series"] = canonical
    del holder["a3History"]
    return True


def apply_publication_adapter(site: dict[str, Any]) -> dict[str, int]:
    metrics = site.get("metrics")
    if not isinstance(metrics, dict):
        raise RuntimeError("Catalogo senza metrics")

    adapted_rows = 0
    adapted_aggregates = 0
    adapted_metrics: set[str] = set()
    for metric_id, metric in metrics.items():
        if not isinstance(metric, dict):
            continue
        rows = metric.get("rows")
        if isinstance(rows, list):
            for index, row in enumerate(rows):
                if isinstance(row, dict) and _adapt_holder(row, f"{metric_id}/rows[{index}]"):
                    adapted_rows += 1
                    adapted_metrics.add(metric_id)
        aggregate = metric.get("aggregate")
        if isinstance(aggregate, dict) and _adapt_holder(aggregate, f"{metric_id}/aggregate"):
            adapted_aggregates += 1
            adapted_metrics.add(metric_id)

    return {
        "metricsAdapted": len(adapted_metrics),
        "rowsAdapted": adapted_rows,
        "aggregatesAdapted": adapted_aggregates,
    }


def main() -> None:
    site = load(SITE_PATH)
    summary = apply_publication_adapter(site)
    save(SITE_PATH, site)
    print(
        "A3 publication adapter: "
        f"{summary['metricsAdapted']} metriche · {summary['rowsAdapted']} righe · "
        f"{summary['aggregatesAdapted']} aggregati normalizzati nel contratto series.years/values."
    )


if __name__ == "__main__":
    main()
