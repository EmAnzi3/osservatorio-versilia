#!/usr/bin/env python3
"""Extract annual observed climate indicators from SIR Toscana for validation.

The script uses only the public SIR archive endpoints exposed by the official
archive UI. It records the SIR validation state for each station/year.

Primary precipitation validation is intentionally restricted to years marked
"Validato" by SIR. Temperature data are downloaded for all available years in
1995-2025, but the output preserves validation status and daily completeness so
strict downstream metrics can filter to validated, sufficiently complete years.
"""
from __future__ import annotations

import argparse
import calendar
import csv
import html
import json
import math
import re
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path

from bs4 import BeautifulSoup

BASE = "https://www.sir.toscana.it"
UA = "OsservatorioVersilia-SIRValidation/1.0"
START_YEAR = 1995
END_YEAR = 2025

# Stations deliberately span coastal/plain, valley and Apuan mountain settings.
# municipality is the municipal areal series used for the point-vs-area check.
STATIONS = [
    # precipitation
    {"station_id": "TOS02004059", "station_label": "Camaiore", "sensor": "pluvio", "municipality": "Camaiore"},
    {"station_id": "TOS02004081", "station_label": "Torre del Lago", "sensor": "pluvio", "municipality": "Viareggio"},
    {"station_id": "TOS02004091", "station_label": "Viareggio 1", "sensor": "pluvio", "municipality": "Viareggio"},
    {"station_id": "TOS02004045", "station_label": "Ponte Tavole", "sensor": "pluvio", "municipality": "Seravezza"},
    {"station_id": "TOS02000077", "station_label": "Cardoso", "sensor": "pluvio", "municipality": "Stazzema"},
    {"station_id": "TOS02000081", "station_label": "Cervaiole", "sensor": "pluvio", "municipality": "Seravezza"},
    {"station_id": "TOS02000083", "station_label": "Azzano", "sensor": "pluvio", "municipality": "Seravezza"},
    {"station_id": "TOS02000079", "station_label": "Retignano", "sensor": "pluvio", "municipality": "Stazzema"},
    # temperature
    {"station_id": "TOS02004059", "station_label": "Camaiore", "sensor": "termo", "municipality": "Camaiore"},
    {"station_id": "TOS02004081", "station_label": "Torre del Lago", "sensor": "termo", "municipality": "Viareggio"},
    {"station_id": "TOS02004055", "station_label": "Forte dei Marmi", "sensor": "termo", "municipality": "Forte dei Marmi"},
    {"station_id": "TOS02004029", "station_label": "Seravezza 2", "sensor": "termo", "municipality": "Seravezza"},
    {"station_id": "TOS03000091", "station_label": "Pietrasanta", "sensor": "termo", "municipality": "Pietrasanta"},
    {"station_id": "TOS03000481", "station_label": "Viareggio Lungomare", "sensor": "termo", "municipality": "Viareggio"},
]

YEAR_RE = re.compile(
    r"dati\.php\?A=(\d{4})&IDS=[^&'\"]+&IDST=([^'\"]+).*?title=\"(Validato|Prevalidato)\"",
    re.I | re.S,
)


def fetch_text(path: str, retries: int = 3, timeout: int = 40) -> str:
    url = urllib.parse.urljoin(BASE, path)
    last = None
    for attempt in range(1, retries + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/html,*/*"})
            with urllib.request.urlopen(req, timeout=timeout) as response:
                raw = response.read()
                enc = response.headers.get_content_charset() or "utf-8"
                return raw.decode(enc, errors="replace")
        except Exception as exc:
            last = exc
            if attempt < retries:
                time.sleep(1.5 * attempt)
    raise RuntimeError(f"SIR request failed after {retries} attempts: {url}: {last!r}")


def parse_station_panel(text: str) -> dict:
    soup = BeautifulSoup(text, "html.parser")
    plain = soup.get_text(" ", strip=True)
    name_match = re.search(r"(.+?)\s*\[([A-Z0-9]+)\]", plain)
    lat_match = re.search(r"LAT\s*([0-9.]+)\s*LON\s*([0-9.]+)", plain, re.I)
    elev_match = re.search(r"Quota\s*slm\s*\[m\]\s*([0-9.]+)", plain, re.I)
    locality_match = re.search(r"Localit[aà]\s+(.+?)\s+GB\s*\[m\]", plain, re.I)

    years = []
    # BeautifulSoup is more robust than relying on attribute ordering.
    for a in soup.find_all("a"):
        onclick = a.get("href", "") + " " + a.get("onclick", "")
        m = re.search(r"dati\.php\?A=(\d{4})&IDS=([^&'\"]+)&IDST=([^'\"]+)", onclick)
        if not m:
            continue
        title = (a.get("title") or "").strip().casefold()
        status = "VALIDATED" if title == "validato" else "PREVALIDATED" if title == "prevalidato" else "UNKNOWN"
        years.append({"year": int(m.group(1)), "station_id": m.group(2), "sensor": m.group(3), "validation_status": status})

    return {
        "official_name": html.unescape(name_match.group(1).strip()) if name_match else None,
        "station_id": name_match.group(2) if name_match else None,
        "latitude": float(lat_match.group(1)) if lat_match else None,
        "longitude": float(lat_match.group(2)) if lat_match else None,
        "elevation_m": float(elev_match.group(1)) if elev_match else None,
        "locality": html.unescape(locality_match.group(1).strip()) if locality_match else None,
        "years": years,
    }


def parse_precip_year(text: str) -> dict:
    soup = BeautifulSoup(text, "html.parser")
    plain = soup.get_text(" ", strip=True)
    status = "VALIDATED" if "Anno VALIDATO" in plain and "PRE-VALIDATO" not in plain else "PREVALIDATED" if "PRE-VALIDATO" in plain else "UNKNOWN"

    annual = None
    rainy = None
    for tag in soup.find_all(string=re.compile(r"Cumulata annuale", re.I)):
        td = tag.find_parent("td")
        if td is None:
            continue
        next_td = td.find_next_sibling("td")
        if next_td is None:
            continue
        vals = re.findall(r"-?\d+(?:[.,]\d+)?", next_td.get_text(" ", strip=True))
        if vals:
            annual = float(vals[0].replace(",", "."))
        if len(vals) > 1:
            rainy = int(float(vals[1].replace(",", ".")))
        break

    # Fallback: sum the monthly TOT row if the explicit annual box changes.
    if annual is None:
        for tr in soup.find_all("tr"):
            cells = [c.get_text(" ", strip=True) for c in tr.find_all(["td", "th"], recursive=False)]
            if cells and cells[0].strip().upper() == "TOT" and len(cells) >= 13:
                nums = []
                for x in cells[1:13]:
                    try:
                        nums.append(float(x.replace(",", ".")))
                    except ValueError:
                        nums.append(float("nan"))
                if all(math.isfinite(x) for x in nums):
                    annual = sum(nums)
                break

    if annual is None:
        raise ValueError("Could not parse SIR annual precipitation")
    return {"validation_status_table": status, "precip_mm_observed": annual, "rainy_days_observed": rainy}


def parse_temperature_year(text: str, year: int) -> dict:
    soup = BeautifulSoup(text, "html.parser")
    plain = soup.get_text(" ", strip=True)
    status = "VALIDATED" if "Anno VALIDATO" in plain and "PRE-VALIDATO" not in plain else "PREVALIDATED" if "PRE-VALIDATO" in plain else "UNKNOWN"
    daily = []
    month_count = 12
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
        for month in range(1, month_count + 1):
            try:
                calendar.monthrange(year, month)
                if day > calendar.monthrange(year, month)[1]:
                    continue
            except Exception:
                continue
            cell = cells[month]
            max_span = cell.find("span", class_=lambda c: c and "text-danger" in (c if isinstance(c, list) else str(c)))
            min_span = cell.find("span", class_=lambda c: c and "text-primary" in (c if isinstance(c, list) else str(c)))
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
            daily.append((tmax + tmin) / 2.0)

    expected = 366 if calendar.isleap(year) else 365
    completeness = len(daily) / expected
    tmean = sum(daily) / len(daily) if daily else None
    if tmean is None:
        raise ValueError("Could not parse any SIR daily Tmax/Tmin pairs")
    return {
        "validation_status_table": status,
        "tmean_c_observed": tmean,
        "temperature_days": len(daily),
        "temperature_completeness": completeness,
    }


def extract_one(task: dict) -> dict:
    sid = task["station_id"]
    sensor = task["sensor"]
    year = task["year"]
    path = f"/archivio/dati.php?A={year}&IDS={sid}&IDST={sensor}"
    text = fetch_text(path)
    parsed = parse_precip_year(text) if sensor == "pluvio" else parse_temperature_year(text, year)
    return {**task, **parsed, "source_url": urllib.parse.urljoin(BASE, path)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output-dir", default="reports/runtime/sir-validation")
    ap.add_argument("--workers", type=int, default=2)
    args = ap.parse_args()
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    metadata = []
    tasks = []
    for cfg in STATIONS:
        sid, sensor = cfg["station_id"], cfg["sensor"]
        panel_path = f"/archivio/stazione.php?IDST={sensor}&IDS={sid}"
        print(f"[sir] panel {cfg['station_label']} {sensor}", flush=True)
        try:
            panel = parse_station_panel(fetch_text(panel_path))
        except Exception as exc:
            metadata.append({**cfg, "panel_error": repr(exc)})
            print(f"[sir] panel failed {sid}/{sensor}: {exc!r}", flush=True)
            continue
        metadata.append({**cfg, **{k: v for k, v in panel.items() if k != "years"}, "available_years": panel["years"]})

        available = [y for y in panel["years"] if START_YEAR <= y["year"] <= END_YEAR and y["sensor"] == sensor]
        if sensor == "pluvio":
            selected = [y for y in available if y["validation_status"] == "VALIDATED"]
        else:
            # Temperature histories are often much shorter; retain all statuses,
            # then downstream metrics can enforce VALIDATED + completeness >= 95%.
            selected = available
        for y in selected:
            tasks.append({
                **cfg,
                "year": y["year"],
                "validation_status_panel": y["validation_status"],
            })
        print(f"[sir] {cfg['station_label']} {sensor}: {len(selected)} years selected of {len(available)} available", flush=True)

    rows = []
    errors = []
    with ThreadPoolExecutor(max_workers=max(1, min(args.workers, 3))) as pool:
        futures = {pool.submit(extract_one, task): task for task in tasks}
        for future in as_completed(futures):
            task = futures[future]
            try:
                row = future.result()
                rows.append(row)
                print(f"[sir] OK {task['station_label']} {task['sensor']} {task['year']}", flush=True)
            except Exception as exc:
                errors.append({**task, "error": repr(exc)})
                print(f"[sir] FAIL {task['station_label']} {task['sensor']} {task['year']}: {exc!r}", flush=True)

    rows.sort(key=lambda r: (r["sensor"], r["station_label"], r["year"]))

    fields = [
        "municipality", "station_label", "station_id", "sensor", "year",
        "validation_status_panel", "validation_status_table",
        "precip_mm_observed", "rainy_days_observed",
        "tmean_c_observed", "temperature_days", "temperature_completeness",
        "source_url",
    ]
    with (out_dir / "sir-annual-observed.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for row in rows:
            w.writerow(row)

    summary = {
        "source": "Regione Toscana - Servizio Idrologico Regionale (SIR)",
        "source_base": BASE,
        "period_requested": [START_YEAR, END_YEAR],
        "precipitation_selection": "SIR years marked VALIDATED only",
        "temperature_selection": "all available years downloaded; use VALIDATED and >=95% daily Tmax/Tmin completeness for strict metrics",
        "station_config": STATIONS,
        "station_metadata": metadata,
        "rows": len(rows),
        "errors": errors,
    }
    (out_dir / "sir-validation-meta.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[sir] wrote {len(rows)} annual station observations; errors={len(errors)}", flush=True)
    if not rows:
        return 2
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
