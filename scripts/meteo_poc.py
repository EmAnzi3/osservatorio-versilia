#!/usr/bin/env python3
"""Proof of concept: reconstruct long climate series for Versilia from ERA5-Land.

This script is intentionally publication-safe:
- it labels outputs as point-based reanalysis, not municipal observations;
- it uses fixed representative coordinates for three contrasting locations;
- it records the exact API request parameters and processing rules;
- it writes only derived annual metrics and a machine-readable metadata file.

Data source for the POC: Open-Meteo Historical Weather API, forced to ERA5-Land.
Production should prefer the Copernicus Climate Data Store directly when practical.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Iterable

API_URL = "https://archive-api.open-meteo.com/v1/archive"
START_YEAR = 1950
END_YEAR = 2025

LOCATIONS = {
    "Viareggio": {"latitude": 43.8745, "longitude": 10.2568, "profile": "costa"},
    "Massarosa": {"latitude": 43.8686, "longitude": 10.3407, "profile": "pianura/collina"},
    "Stazzema": {"latitude": 43.9974, "longitude": 10.2954, "profile": "montagna"},
}

DAILY_VARS = [
    "temperature_2m_mean",
    "temperature_2m_max",
    "temperature_2m_min",
    "precipitation_sum",
]


@dataclass(frozen=True)
class DailyRecord:
    day: date
    tmean: float
    tmax: float
    tmin: float
    precip: float


def request_json(params: dict[str, str | float], retries: int = 4) -> dict:
    query = urllib.parse.urlencode(params)
    url = f"{API_URL}?{query}"
    headers = {"User-Agent": "OsservatorioVersilia-MeteoPOC/1.0"}
    last_exc: Exception | None = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=120) as response:
                return json.load(response)
        except Exception as exc:
            last_exc = exc
            if attempt + 1 < retries:
                time.sleep(2 ** attempt)
    raise RuntimeError(f"Open-Meteo request failed after {retries} attempts: {last_exc}")


def year_chunks(start: int, end: int, width: int = 10) -> Iterable[tuple[int, int]]:
    y = start
    while y <= end:
        chunk_end = min(end, y + width - 1)
        yield y, chunk_end
        y = chunk_end + 1


def fetch_location(name: str, cfg: dict[str, float | str]) -> tuple[list[DailyRecord], dict]:
    records: list[DailyRecord] = []
    api_meta: dict = {}

    for start_year, end_year in year_chunks(START_YEAR, END_YEAR):
        params = {
            "latitude": cfg["latitude"],
            "longitude": cfg["longitude"],
            "start_date": f"{start_year}-01-01",
            "end_date": f"{end_year}-12-31",
            "daily": ",".join(DAILY_VARS),
            "timezone": "Europe/Rome",
            "models": "era5_land",
            "cell_selection": "nearest",
        }
        payload = request_json(params)
        daily = payload.get("daily") or {}
        times = daily.get("time") or []
        arrays = {var: daily.get(var) or [] for var in DAILY_VARS}

        expected = len(times)
        if expected == 0 or any(len(values) != expected for values in arrays.values()):
            raise ValueError(f"{name}: incomplete daily arrays for {start_year}-{end_year}")

        for idx, day_text in enumerate(times):
            values = [arrays[var][idx] for var in DAILY_VARS]
            if any(v is None for v in values):
                continue
            records.append(
                DailyRecord(
                    day=date.fromisoformat(day_text),
                    tmean=float(values[0]),
                    tmax=float(values[1]),
                    tmin=float(values[2]),
                    precip=float(values[3]),
                )
            )

        if not api_meta:
            api_meta = {
                "requested_latitude": cfg["latitude"],
                "requested_longitude": cfg["longitude"],
                "returned_latitude": payload.get("latitude"),
                "returned_longitude": payload.get("longitude"),
                "elevation_m": payload.get("elevation"),
                "timezone": payload.get("timezone"),
                "utc_offset_seconds": payload.get("utc_offset_seconds"),
            }

    records.sort(key=lambda r: r.day)
    return records, api_meta


def mean(values: list[float]) -> float:
    if not values:
        return math.nan
    return sum(values) / len(values)


def annual_metrics(records: list[DailyRecord]) -> list[dict]:
    by_year: dict[int, list[DailyRecord]] = {}
    for record in records:
        by_year.setdefault(record.day.year, []).append(record)

    rows: list[dict] = []
    for year in range(START_YEAR, END_YEAR + 1):
        days = by_year.get(year, [])
        expected_days = 366 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 365
        completeness = len(days) / expected_days if expected_days else 0.0
        if completeness < 0.98:
            raise ValueError(f"Year {year}: only {len(days)}/{expected_days} daily values")

        rows.append(
            {
                "year": year,
                "days": len(days),
                "tmean_c": mean([r.tmean for r in days]),
                "tmax_mean_c": mean([r.tmax for r in days]),
                "tmin_mean_c": mean([r.tmin for r in days]),
                "precip_mm": sum(r.precip for r in days),
                "days_tmax_ge_30": sum(r.tmax >= 30.0 for r in days),
                "nights_tmin_gt_20": sum(r.tmin > 20.0 for r in days),
                "wet_days_ge_1mm": sum(r.precip >= 1.0 for r in days),
                "heavy_rain_days_ge_50mm": sum(r.precip >= 50.0 for r in days),
            }
        )
    return rows


def subset(rows: list[dict], start: int, end: int) -> list[dict]:
    return [row for row in rows if start <= int(row["year"]) <= end]


def period_summary(rows: list[dict], start: int, end: int) -> dict[str, float]:
    chosen = subset(rows, start, end)
    if len(chosen) != (end - start + 1):
        raise ValueError(f"Period {start}-{end}: incomplete annual coverage")
    return {
        "tmean_c": mean([float(r["tmean_c"]) for r in chosen]),
        "precip_mm": mean([float(r["precip_mm"]) for r in chosen]),
        "days_tmax_ge_30": mean([float(r["days_tmax_ge_30"]) for r in chosen]),
        "nights_tmin_gt_20": mean([float(r["nights_tmin_gt_20"]) for r in chosen]),
        "wet_days_ge_1mm": mean([float(r["wet_days_ge_1mm"]) for r in chosen]),
        "heavy_rain_days_ge_50mm": mean([float(r["heavy_rain_days_ge_50mm"]) for r in chosen]),
    }


def linear_slope_per_year(rows: list[dict], field: str) -> float:
    xs = [float(row["year"]) for row in rows]
    ys = [float(row[field]) for row in rows]
    xbar = mean(xs)
    ybar = mean(ys)
    denom = sum((x - xbar) ** 2 for x in xs)
    if denom == 0:
        return math.nan
    return sum((x - xbar) * (y - ybar) for x, y in zip(xs, ys)) / denom


def pct_change(new: float, old: float) -> float:
    if old == 0:
        return math.nan
    return (new - old) / old * 100.0


def validate_location(name: str, rows: list[dict]) -> None:
    if len(rows) != END_YEAR - START_YEAR + 1:
        raise ValueError(f"{name}: expected {END_YEAR - START_YEAR + 1} annual rows, got {len(rows)}")
    for row in rows:
        if not (-10.0 <= float(row["tmean_c"]) <= 30.0):
            raise ValueError(f"{name} {row['year']}: implausible mean temperature")
        if not (100.0 <= float(row["precip_mm"]) <= 6000.0):
            raise ValueError(f"{name} {row['year']}: implausible annual precipitation")


def fmt(value: float, digits: int = 1) -> str:
    if math.isnan(value):
        return "n.d."
    return f"{value:.{digits}f}"


def build_report(results: dict[str, dict]) -> str:
    lines = [
        "# Meteo e clima — proof of concept ERA5-Land",
        "",
        f"Serie analizzata: **{START_YEAR}–{END_YEAR}**. Fonte POC: **ERA5-Land** tramite Open-Meteo Historical Weather API.",
        "",
        "> Questi valori sono **stime di rianalisi su punti rappresentativi**, non osservazioni di stazione e non medie dei confini comunali. Servono a verificare se esiste un segnale climatico abbastanza solido da giustificare una pipeline comunale.",
        "",
        "## Risultato sintetico",
        "",
        "| Località | Profilo | Cella/elevazione | T media 1961–1990 | T media 1991–2020 | Δ T | Trend 1950–2025 | Pioggia 1961–1990 | Pioggia 1991–2020 | Δ pioggia |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for name, data in results.items():
        b = data["baseline"]
        r = data["recent"]
        meta = data["api_meta"]
        trend = data["trend_tmean_c_decade"]
        cell = f"{fmt(float(meta.get('returned_latitude') or math.nan), 3)}, {fmt(float(meta.get('returned_longitude') or math.nan), 3)} / {fmt(float(meta.get('elevation_m') or math.nan), 0)} m"
        lines.append(
            f"| {name} | {LOCATIONS[name]['profile']} | {cell} | "
            f"{fmt(b['tmean_c'])} °C | {fmt(r['tmean_c'])} °C | "
            f"**{fmt(r['tmean_c'] - b['tmean_c'], 2)} °C** | "
            f"**{fmt(trend, 2)} °C/decennio** | "
            f"{fmt(b['precip_mm'], 0)} mm | {fmt(r['precip_mm'], 0)} mm | "
            f"{fmt(pct_change(r['precip_mm'], b['precip_mm']), 1)}% |"
        )

    lines += [
        "",
        "## Indicatori di caldo",
        "",
        "| Località | Giorni Tmax ≥30 °C/anno 1961–1990 | 1991–2020 | Δ | Notti Tmin >20 °C/anno 1961–1990 | 1991–2020 | Δ |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for name, data in results.items():
        b = data["baseline"]
        r = data["recent"]
        lines.append(
            f"| {name} | {fmt(b['days_tmax_ge_30'])} | {fmt(r['days_tmax_ge_30'])} | "
            f"**{fmt(r['days_tmax_ge_30'] - b['days_tmax_ge_30'])}** | "
            f"{fmt(b['nights_tmin_gt_20'])} | {fmt(r['nights_tmin_gt_20'])} | "
            f"**{fmt(r['nights_tmin_gt_20'] - b['nights_tmin_gt_20'])}** |"
        )

    lines += [
        "",
        "## Indicazioni per l'Osservatorio",
        "",
        "- **Temperatura:** se il segnale è coerente tra i tre profili territoriali e supera ampiamente la variabilità interannuale, la serie ERA5-Land è utilizzabile per la ricostruzione lunga, dichiarandola come rianalisi.",
        "- **Precipitazioni:** la rianalisi è utile per tendenze e confronti di larga scala, ma in Versilia/Apuane va validata contro SIR/LaMMA prima di pubblicare estremi locali.",
        "- **Scala comunale:** il passo successivo non è usare il municipio come valore del Comune, ma mediare celle/raster sul poligono comunale. Per il 1995–2015 LaMMA a 1 km è la base preferibile; ERA5-Land serve per estendere la serie al 1950.",
        "- **Pubblicazione:** mantenere etichette separate `OSSERVATO`, `INTERPOLATO`, `RIANALISI` e conservare snapshot/metadati riproducibili.",
        "",
        "## Metodo",
        "",
        "- Coordinate fisse dei centri comunali: Viareggio, Massarosa, Stazzema.",
        "- Modello forzato: `era5_land`; selezione cella: `nearest`; timezone: `Europe/Rome`.",
        "- Variabili giornaliere: temperatura media, massima, minima, precipitazione totale.",
        "- Periodi di confronto: **1961–1990** e **1991–2020**.",
        "- Trend: regressione lineare sui valori medi annuali 1950–2025, espresso in °C/decennio.",
        "- Soglie: Tmax ≥30 °C; Tmin >20 °C; giorno piovoso ≥1 mm; pioggia intensa ≥50 mm.",
        "",
        "Il CSV allegato contiene tutti gli anni e consente di verificare i calcoli.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="reports/runtime/meteo-poc")
    args = parser.parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    all_rows: list[dict] = []
    results: dict[str, dict] = {}

    for name, cfg in LOCATIONS.items():
        print(f"[meteo-poc] fetching {name}...")
        daily, api_meta = fetch_location(name, cfg)
        rows = annual_metrics(daily)
        validate_location(name, rows)

        baseline = period_summary(rows, 1961, 1990)
        recent = period_summary(rows, 1991, 2020)
        result = {
            "api_meta": api_meta,
            "baseline": baseline,
            "recent": recent,
            "trend_tmean_c_decade": linear_slope_per_year(rows, "tmean_c") * 10.0,
            "trend_precip_mm_decade": linear_slope_per_year(rows, "precip_mm") * 10.0,
        }
        results[name] = result

        for row in rows:
            all_rows.append({"location": name, "profile": cfg["profile"], **row})

    csv_path = output_dir / "era5-land-annual.csv"
    fields = [
        "location",
        "profile",
        "year",
        "days",
        "tmean_c",
        "tmax_mean_c",
        "tmin_mean_c",
        "precip_mm",
        "days_tmax_ge_30",
        "nights_tmin_gt_20",
        "wet_days_ge_1mm",
        "heavy_rain_days_ge_50mm",
    ]
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(all_rows)

    metadata = {
        "source": {
            "name": "ERA5-Land via Open-Meteo Historical Weather API",
            "api_url": API_URL,
            "model": "era5_land",
            "upstream": "Copernicus Climate Change Service / ECMWF ERA5-Land",
        },
        "period": {"start": START_YEAR, "end": END_YEAR},
        "locations": {name: {**LOCATIONS[name], **results[name]["api_meta"]} for name in LOCATIONS},
        "processing": {
            "baseline": "1961-1990",
            "recent": "1991-2020",
            "temperature_trend": "OLS slope of annual mean temperature, x10 for °C/decade",
            "thresholds": {
                "hot_day": "Tmax >= 30 °C",
                "warm_night": "Tmin > 20 °C",
                "wet_day": "precipitation >= 1 mm",
                "heavy_rain_day": "precipitation >= 50 mm",
            },
        },
        "publication_status": "POC only — point-based reanalysis, not municipal statistics",
        "results": results,
    }
    (output_dir / "metadata.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    report = build_report(results)
    (output_dir / "report.md").write_text(report, encoding="utf-8")
    print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
