#!/usr/bin/env python3
"""POC meteo/clima per Osservatorio Versilia.

Fase 1: verifica che una serie storica lunga e riproducibile possa essere
costruita senza API key usando un archivio bulk statico. Il benchmark è la
stazione WMO Pisa/S. Giusto (16158), vicina alla Versilia e con inventario
storico dal 1944. Non è un dato comunale e non è destinato alla pubblicazione.

Il passo successivo, se il segnale è utile, è la spazializzazione comunale con
LaMMA 1 km e/o ERA5-Land su poligoni comunali, validata contro SIR Toscana.
"""

from __future__ import annotations

import argparse
import calendar
import csv
import gzip
import io
import json
import math
import urllib.request
from collections import defaultdict
from pathlib import Path

STATION_ID = "16158"
STATION_NAME = "Pisa / S. Giusto"
STATION_LAT = 43.6833
STATION_LON = 10.3833
STATION_ELEVATION_M = 2
SOURCE_URL = f"https://data.meteostat.net/monthly/{STATION_ID}.csv.gz"
START_YEAR = 1950
END_YEAR = 2024


def fnum(value: str | None) -> float | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def fetch_rows() -> list[dict]:
    request = urllib.request.Request(
        SOURCE_URL,
        headers={"User-Agent": "OsservatorioVersilia-MeteoPOC/1.1"},
    )
    with urllib.request.urlopen(request, timeout=120) as response:
        raw = response.read()
    text = gzip.decompress(raw).decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    rows = list(reader)
    if not rows:
        raise RuntimeError("Meteostat monthly dump is empty")
    required = {"date", "temp", "prcp"}
    missing = required - set(rows[0])
    if missing:
        raise RuntimeError(f"Unexpected Meteostat schema; missing: {sorted(missing)}")
    return rows


def annualize(monthly_rows: list[dict]) -> list[dict]:
    grouped: dict[int, list[dict]] = defaultdict(list)
    for row in monthly_rows:
        year = int(row["date"][:4])
        if START_YEAR <= year <= END_YEAR:
            grouped[year].append(row)

    annual: list[dict] = []
    for year in range(START_YEAR, END_YEAR + 1):
        rows = sorted(grouped.get(year, []), key=lambda r: r["date"])
        if len(rows) != 12:
            continue

        temp_weighted = 0.0
        temp_days = 0
        precip = 0.0
        complete = True
        source_fields: set[str] = set()

        for row in rows:
            month = int(row["date"][5:7])
            temp = fnum(row.get("temp"))
            prcp = fnum(row.get("prcp"))
            if temp is None or prcp is None:
                complete = False
                break
            days = calendar.monthrange(year, month)[1]
            temp_weighted += temp * days
            temp_days += days
            precip += prcp
            for key, value in row.items():
                if key.endswith("_source") and value:
                    source_fields.update(str(value).split())

        if not complete:
            continue
        annual.append(
            {
                "year": year,
                "tmean_c": temp_weighted / temp_days,
                "precip_mm": precip,
                "source_ids": " ".join(sorted(source_fields)),
            }
        )
    return annual


def mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else math.nan


def period(rows: list[dict], start: int, end: int) -> dict:
    chosen = [r for r in rows if start <= r["year"] <= end]
    expected = end - start + 1
    return {
        "start": start,
        "end": end,
        "years_expected": expected,
        "years_available": len(chosen),
        "tmean_c": mean([float(r["tmean_c"]) for r in chosen]),
        "precip_mm": mean([float(r["precip_mm"]) for r in chosen]),
    }


def slope_per_decade(rows: list[dict], field: str) -> float:
    xs = [float(r["year"]) for r in rows]
    ys = [float(r[field]) for r in rows]
    xb, yb = mean(xs), mean(ys)
    den = sum((x - xb) ** 2 for x in xs)
    return 10.0 * sum((x - xb) * (y - yb) for x, y in zip(xs, ys)) / den


def fmt(value: float, digits: int = 1) -> str:
    return "n.d." if math.isnan(value) else f"{value:.{digits}f}"


def build_report(annual: list[dict]) -> tuple[str, dict]:
    baseline = period(annual, 1961, 1990)
    recent = period(annual, 1991, 2020)
    trend_rows = [r for r in annual if 1950 <= r["year"] <= 2020]
    trend_t = slope_per_decade(trend_rows, "tmean_c")
    trend_p = slope_per_decade(trend_rows, "precip_mm")
    delta_t = recent["tmean_c"] - baseline["tmean_c"]
    delta_p = recent["precip_mm"] - baseline["precip_mm"]
    delta_p_pct = delta_p / baseline["precip_mm"] * 100.0

    summary = {
        "station": {
            "id": STATION_ID,
            "name": STATION_NAME,
            "latitude": STATION_LAT,
            "longitude": STATION_LON,
            "elevation_m": STATION_ELEVATION_M,
        },
        "coverage": {
            "first_complete_year": annual[0]["year"] if annual else None,
            "last_complete_year": annual[-1]["year"] if annual else None,
            "complete_years": len(annual),
        },
        "baseline_1961_1990": baseline,
        "recent_1991_2020": recent,
        "delta_temperature_c": delta_t,
        "delta_precipitation_mm": delta_p,
        "delta_precipitation_pct": delta_p_pct,
        "trend_1950_2020_temperature_c_decade": trend_t,
        "trend_1950_2020_precipitation_mm_decade": trend_p,
    }

    lines = [
        "# Meteo e clima — prova numerica su serie storica lunga",
        "",
        f"Benchmark: **{STATION_NAME} (WMO {STATION_ID})**, {STATION_LAT:.4f}, {STATION_LON:.4f}, {STATION_ELEVATION_M} m.",
        "",
        "> Questo benchmark non rappresenta un Comune della Versilia. Serve a provare, con dati realmente scaricati e calcolati dalla CI, che la pipeline storica funziona e a quantificare l'ordine di grandezza del segnale climatico costiero locale.",
        "",
        "## Numeri ottenuti",
        "",
        "| Indicatore | 1961–1990 | 1991–2020 | Differenza |",
        "|---|---:|---:|---:|",
        f"| Temperatura media annua | {fmt(baseline['tmean_c'], 2)} °C | {fmt(recent['tmean_c'], 2)} °C | **{fmt(delta_t, 2)} °C** |",
        f"| Precipitazione media annua | {fmt(baseline['precip_mm'], 0)} mm | {fmt(recent['precip_mm'], 0)} mm | **{fmt(delta_p, 0)} mm ({fmt(delta_p_pct, 1)}%)** |",
        "",
        f"**Trend lineare temperatura 1950–2020:** {fmt(trend_t, 3)} °C/decennio.",
        "",
        f"**Trend lineare precipitazione 1950–2020:** {fmt(trend_p, 1)} mm/decennio.",
        "",
        f"Copertura annuale completa utilizzata: **{summary['coverage']['first_complete_year']}–{summary['coverage']['last_complete_year']}**, {summary['coverage']['complete_years']} anni completi disponibili nell'intervallo richiesto.",
        "",
        "## Cosa dimostra e cosa non dimostra",
        "",
        "- Dimostra che possiamo costruire automaticamente serie annuali, confronti tra normali climatiche e trend senza inserire numeri a mano.",
        "- Non autorizza a chiamare questi valori `Viareggio`, `Massarosa` o `Versilia`: la stazione è Pisa/S. Giusto.",
        "- Meteostat aggrega più archivi e i dump possono includere dati modellati a riempimento: è un benchmark tecnico, non la fonte finale dell'Osservatorio.",
        "- Per la pubblicazione comunale la priorità resta: LaMMA 1 km per la spazializzazione, SIR Toscana per la verifica osservativa, ERA5-Land per estendere la ricostruzione lunga.",
        "",
    ]
    return "\n".join(lines), summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="reports/runtime/meteo-poc")
    args = parser.parse_args()
    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)

    print(f"[meteo-poc] downloading monthly dump for {STATION_NAME}...")
    monthly = fetch_rows()
    annual = annualize(monthly)
    if len([r for r in annual if 1961 <= r["year"] <= 2020]) < 55:
        raise RuntimeError("Insufficient complete coverage for climate-period comparison")

    report, summary = build_report(annual)

    with (out / "pisa-annual.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["year", "tmean_c", "precip_mm", "source_ids"])
        writer.writeheader()
        writer.writerows(annual)

    metadata = {
        "status": "POC only — benchmark station, not municipal statistics",
        "source": {
            "provider": "Meteostat monthly station dump",
            "url": SOURCE_URL,
            "station_id": STATION_ID,
            "note": "Meteostat may include model data as substitute for missing observations.",
        },
        "processing": {
            "annual_temperature": "day-weighted mean of monthly mean temperature",
            "annual_precipitation": "sum of monthly precipitation totals",
            "comparison_periods": ["1961-1990", "1991-2020"],
            "trend": "OLS on complete annual values, 1950-2020",
        },
        "summary": summary,
    }
    (out / "metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    (out / "report.md").write_text(report, encoding="utf-8")
    print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
