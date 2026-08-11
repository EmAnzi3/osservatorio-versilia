#!/usr/bin/env python3
"""Extract annual observed Tmin/Tmax from the official SIR Toscana archive.

This is a focused companion to sir_validate_climate.py. It preserves annual
validation state and completeness and exposes annual means of daily Tmin and
Tmax separately, so the LaMMA/ERA5-Land extreme-temperature trends can be
checked against an independent observational source.
"""
from __future__ import annotations

import argparse
import calendar
import csv
import json
import re
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from bs4 import BeautifulSoup

from sir_validate_climate import BASE, STATIONS, fetch_text, parse_station_panel

VALIDATION_FROM = 1995
VALIDATION_TO = 2015


def parse_temperature_extremes(text: str, year: int) -> dict:
    soup = BeautifulSoup(text, "html.parser")
    plain = soup.get_text(" ", strip=True)
    status = (
        "VALIDATED"
        if "Anno VALIDATO" in plain and "PRE-VALIDATO" not in plain
        else "PREVALIDATED"
        if "PRE-VALIDATO" in plain
        else "UNKNOWN"
    )
    daily_min: list[float] = []
    daily_max: list[float] = []
    for tr in soup.find_all("tr"):
        cells = tr.find_all("td", recursive=False)
        if len(cells) < 13:
            continue
        day_text = cells[0].get_text(" ", strip=True)
        if not day_text.isdigit():
            continue
        day = int(day_text)
        if not 1 <= day <= 31:
            continue
        for month in range(1, 13):
            if day > calendar.monthrange(year, month)[1]:
                continue
            cell = cells[month]
            max_span = cell.find(
                "span",
                class_=lambda c: c and "text-danger" in (c if isinstance(c, list) else str(c)),
            )
            min_span = cell.find(
                "span",
                class_=lambda c: c and "text-primary" in (c if isinstance(c, list) else str(c)),
            )
            if max_span is None or min_span is None:
                continue
            max_nums = re.findall(r"-?\d+(?:[.,]\d+)?", max_span.get_text(" ", strip=True))
            min_nums = re.findall(r"-?\d+(?:[.,]\d+)?", min_span.get_text(" ", strip=True))
            if not max_nums or not min_nums:
                continue
            tmax = float(max_nums[0].replace(",", "."))
            tmin = float(min_nums[0].replace(",", "."))
            if not (-40 <= tmin <= 50 and -40 <= tmax <= 55 and tmax >= tmin):
                continue
            daily_min.append(tmin)
            daily_max.append(tmax)

    expected = 366 if calendar.isleap(year) else 365
    if not daily_min or len(daily_min) != len(daily_max):
        raise ValueError("Could not parse any complete SIR daily Tmin/Tmax pairs")
    return {
        "validation_status_table": status,
        "tmin_mean_c_observed": sum(daily_min) / len(daily_min),
        "tmax_mean_c_observed": sum(daily_max) / len(daily_max),
        "temperature_days": len(daily_min),
        "temperature_completeness": len(daily_min) / expected,
    }


def extract_one(task: dict) -> dict:
    sid = task["station_id"]
    year = task["year"]
    path = f"/archivio/dati.php?A={year}&IDS={sid}&IDST=termo"
    parsed = parse_temperature_extremes(fetch_text(path), year)
    return {**task, **parsed, "source_url": urllib.parse.urljoin(BASE, path)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output-dir", default="reports/runtime/minmax/sir")
    ap.add_argument("--workers", type=int, default=2)
    args = ap.parse_args()
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    stations = [cfg for cfg in STATIONS if cfg["sensor"] == "termo"]
    tasks: list[dict] = []
    metadata: list[dict] = []
    for cfg in stations:
        sid = cfg["station_id"]
        panel_path = f"/archivio/stazione.php?IDST=termo&IDS={sid}"
        print(f"[sir-minmax] panel {cfg['station_label']}", flush=True)
        try:
            panel = parse_station_panel(fetch_text(panel_path))
        except Exception as exc:
            metadata.append({**cfg, "panel_error": repr(exc)})
            print(f"[sir-minmax] panel failed {sid}: {exc!r}", flush=True)
            continue
        metadata.append(
            {
                **cfg,
                **{k: v for k, v in panel.items() if k != "years"},
                "available_years": panel["years"],
            }
        )
        available = [
            y
            for y in panel["years"]
            if VALIDATION_FROM <= y["year"] <= VALIDATION_TO
            and y["sensor"] == "termo"
            and y["validation_status"] == "VALIDATED"
        ]
        for y in available:
            tasks.append(
                {
                    **cfg,
                    "year": y["year"],
                    "validation_status_panel": y["validation_status"],
                }
            )
        print(
            f"[sir-minmax] {cfg['station_label']}: {len(available)} validated overlap years",
            flush=True,
        )

    rows: list[dict] = []
    errors: list[dict] = []
    with ThreadPoolExecutor(max_workers=max(1, min(args.workers, 3))) as pool:
        futures = {pool.submit(extract_one, task): task for task in tasks}
        for future in as_completed(futures):
            task = futures[future]
            try:
                rows.append(future.result())
                print(f"[sir-minmax] OK {task['station_label']} {task['year']}", flush=True)
            except Exception as exc:
                errors.append({**task, "error": repr(exc)})
                print(
                    f"[sir-minmax] FAIL {task['station_label']} {task['year']}: {exc!r}",
                    flush=True,
                )

    rows.sort(key=lambda r: (r["station_label"], r["year"]))
    fields = [
        "municipality",
        "station_label",
        "station_id",
        "year",
        "validation_status_panel",
        "validation_status_table",
        "tmin_mean_c_observed",
        "tmax_mean_c_observed",
        "temperature_days",
        "temperature_completeness",
        "source_url",
    ]
    csv_path = out_dir / "sir-minmax-observed.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

    meta = {
        "source": "Regione Toscana - Servizio Idrologico Regionale (SIR)",
        "period_requested": [VALIDATION_FROM, VALIDATION_TO],
        "selection_note": (
            "Only panel years marked VALIDATED in the LaMMA/ERA5 overlap are requested; "
            "strict comparison also requires the annual page to be VALIDATED and >=95% complete."
        ),
        "station_metadata": metadata,
        "rows": len(rows),
        "errors": errors,
    }
    (out_dir / "sir-minmax-meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"[sir-minmax] wrote {len(rows)} station-years; errors={len(errors)} -> {csv_path}")
    return 0 if rows else 2


if __name__ == "__main__":
    raise SystemExit(main())
