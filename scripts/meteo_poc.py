#!/usr/bin/env python3
"""POC meteo/clima per Osservatorio Versilia.

Fase 1: verifica una serie storica lunga e riproducibile da archivio bulk
statico. Benchmark: stazione WMO Pisa/S. Giusto (16158), vicina alla Versilia,
con inventario storico dal 1944. Non è un dato comunale né da pubblicare.

Passo successivo: spazializzazione comunale con LaMMA 1 km e/o ERA5-Land su
poligoni comunali, validata contro SIR Toscana.
"""
from __future__ import annotations

import argparse, calendar, csv, gzip, io, json, math, urllib.request
from collections import defaultdict
from pathlib import Path

STATION_ID = "16158"
STATION_NAME = "Pisa / S. Giusto"
STATION_LAT, STATION_LON, STATION_ELEVATION_M = 43.6833, 10.3833, 2
SOURCE_URL = f"https://data.meteostat.net/monthly/{STATION_ID}.csv.gz"
START_YEAR, END_YEAR = 1950, 2024


def fnum(value):
    text = "" if value is None else str(value).strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def fetch_rows() -> list[dict]:
    req = urllib.request.Request(SOURCE_URL, headers={"User-Agent": "OsservatorioVersilia-MeteoPOC/1.3"})
    with urllib.request.urlopen(req, timeout=120) as response:
        text = gzip.decompress(response.read()).decode("utf-8-sig")
    rows = list(csv.DictReader(io.StringIO(text)))
    if not rows:
        raise RuntimeError("Meteostat monthly dump is empty")
    cols = set(rows[0])
    if {"year", "month"} <= cols:
        for row in rows:
            row["date"] = f"{int(row['year']):04d}-{int(row['month']):02d}-01"
    elif "date" in cols:
        pass
    elif "time" in cols:
        for row in rows:
            row["date"] = row["time"]
    else:
        raise RuntimeError(f"Unexpected Meteostat schema; columns: {sorted(cols)}")
    missing = {"temp", "prcp"} - cols
    if missing:
        raise RuntimeError(f"Unexpected Meteostat schema; missing: {sorted(missing)}")
    return rows


def annualize(monthly_rows: list[dict]) -> list[dict]:
    grouped = defaultdict(list)
    for row in monthly_rows:
        year = int(row["date"][:4])
        if START_YEAR <= year <= END_YEAR:
            grouped[year].append(row)
    annual = []
    for year in range(START_YEAR, END_YEAR + 1):
        rows = sorted(grouped.get(year, []), key=lambda r: r["date"])
        if len(rows) != 12:
            continue
        tw, tdays, precip, complete = 0.0, 0, 0.0, True
        source_ids = set()
        for row in rows:
            month = int(row["date"][5:7])
            temp, prcp = fnum(row.get("temp")), fnum(row.get("prcp"))
            if temp is None or prcp is None:
                complete = False
                break
            days = calendar.monthrange(year, month)[1]
            tw += temp * days
            tdays += days
            precip += prcp
            for key, value in row.items():
                if key.endswith("_source") and value:
                    source_ids.update(str(value).split())
        if complete:
            annual.append({"year": year, "tmean_c": tw / tdays, "precip_mm": precip,
                           "source_ids": " ".join(sorted(source_ids))})
    return annual


def mean(values):
    return sum(values) / len(values) if values else math.nan


def period(rows, start, end):
    chosen = [r for r in rows if start <= r["year"] <= end]
    return {"start": start, "end": end, "years_expected": end-start+1,
            "years_available": len(chosen),
            "tmean_c": mean([float(r["tmean_c"]) for r in chosen]),
            "precip_mm": mean([float(r["precip_mm"]) for r in chosen])}


def slope_per_decade(rows, field):
    xs, ys = [float(r["year"]) for r in rows], [float(r[field]) for r in rows]
    xb, yb = mean(xs), mean(ys)
    den = sum((x-xb)**2 for x in xs)
    return 10 * sum((x-xb)*(y-yb) for x, y in zip(xs, ys)) / den


def fmt(value, digits=1):
    return "n.d." if math.isnan(value) else f"{value:.{digits}f}"


def build_report(annual):
    baseline, recent = period(annual, 1961, 1990), period(annual, 1991, 2020)
    trend_rows = [r for r in annual if 1950 <= r["year"] <= 2020]
    trend_t = slope_per_decade(trend_rows, "tmean_c")
    trend_p = slope_per_decade(trend_rows, "precip_mm")
    dt = recent["tmean_c"] - baseline["tmean_c"]
    dp = recent["precip_mm"] - baseline["precip_mm"]
    dpp = dp / baseline["precip_mm"] * 100
    summary = {
        "station": {"id": STATION_ID, "name": STATION_NAME, "latitude": STATION_LAT,
                    "longitude": STATION_LON, "elevation_m": STATION_ELEVATION_M},
        "coverage": {"first_complete_year": annual[0]["year"] if annual else None,
                     "last_complete_year": annual[-1]["year"] if annual else None,
                     "complete_years": len(annual)},
        "baseline_1961_1990": baseline, "recent_1991_2020": recent,
        "delta_temperature_c": dt, "delta_precipitation_mm": dp,
        "delta_precipitation_pct": dpp,
        "trend_1950_2020_temperature_c_decade": trend_t,
        "trend_1950_2020_precipitation_mm_decade": trend_p,
    }
    lines = [
        "# Meteo e clima — prova numerica su serie storica lunga", "",
        f"Benchmark: **{STATION_NAME} (WMO {STATION_ID})**, {STATION_LAT:.4f}, {STATION_LON:.4f}, {STATION_ELEVATION_M} m.", "",
        "> Benchmark tecnico vicino alla Versilia: non rappresenta un Comune e non è un dato da pubblicare.", "",
        "## Numeri ottenuti", "",
        "| Indicatore | 1961–1990 | 1991–2020 | Differenza |", "|---|---:|---:|---:|",
        f"| Temperatura media annua | {fmt(baseline['tmean_c'],2)} °C | {fmt(recent['tmean_c'],2)} °C | **{fmt(dt,2)} °C** |",
        f"| Precipitazione media annua | {fmt(baseline['precip_mm'],0)} mm | {fmt(recent['precip_mm'],0)} mm | **{fmt(dp,0)} mm ({fmt(dpp,1)}%)** |", "",
        f"**Trend lineare temperatura 1950–2020:** {fmt(trend_t,3)} °C/decennio.", "",
        f"**Trend lineare precipitazione 1950–2020:** {fmt(trend_p,1)} mm/decennio.", "",
        f"Copertura annuale completa: **{summary['coverage']['first_complete_year']}–{summary['coverage']['last_complete_year']}**, {summary['coverage']['complete_years']} anni.", "",
        "## Lettura", "",
        "- La pipeline costruisce automaticamente serie annuali, normali climatiche e trend senza numeri inseriti a mano.",
        "- La stazione è Pisa/S. Giusto: questi valori non vanno etichettati come Viareggio, Massarosa o Versilia.",
        "- Meteostat può includere dati modellati per colmare lacune: è un benchmark tecnico, non la fonte finale.",
        "- Per la pubblicazione: LaMMA 1 km per la spazializzazione, SIR Toscana per la verifica osservativa, ERA5-Land per la serie lunga.", ""
    ]
    return "\n".join(lines), summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="reports/runtime/meteo-poc")
    args = parser.parse_args()
    out = Path(args.output_dir); out.mkdir(parents=True, exist_ok=True)
    print(f"[meteo-poc] downloading monthly dump for {STATION_NAME}...")
    annual = annualize(fetch_rows())
    if len([r for r in annual if 1961 <= r["year"] <= 2020]) < 55:
        raise RuntimeError(f"Insufficient complete coverage; complete years={len(annual)}")
    report, summary = build_report(annual)
    with (out/"pisa-annual.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["year","tmean_c","precip_mm","source_ids"]); w.writeheader(); w.writerows(annual)
    metadata = {"status":"POC only — benchmark station, not municipal statistics",
                "source":{"provider":"Meteostat monthly station dump","url":SOURCE_URL,"station_id":STATION_ID,
                          "note":"Meteostat may include model data as substitute for missing observations."},
                "processing":{"annual_temperature":"day-weighted mean of monthly mean temperature",
                              "annual_precipitation":"sum of monthly precipitation totals",
                              "comparison_periods":["1961-1990","1991-2020"],
                              "trend":"OLS on complete annual values, 1950-2020"}, "summary":summary}
    (out/"metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    (out/"report.md").write_text(report, encoding="utf-8")
    print(report)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
