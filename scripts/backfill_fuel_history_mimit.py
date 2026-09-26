#!/usr/bin/env python3
"""Backfill mensile dei prezzi carburanti MIMIT per i sette Comuni della Versilia.

Per ogni giorno disponibile:
- associa gli impianti al Comune usando snapshot anagrafici dello stesso mese;
- considera esclusivamente Benzina/Gasolio in modalità self-service;
- calcola la mediana comunale giornaliera tra gli impianti;
- calcola la media mensile delle mediane giornaliere.

Gli archivi nazionali trimestrali sono scaricati e processati uno alla volta.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import re
import statistics
import tarfile
import tempfile
import unicodedata
import urllib.request
from collections import defaultdict
from datetime import date
from pathlib import Path
from typing import Any

TOWNS = ["Camaiore", "Forte dei Marmi", "Massarosa", "Pietrasanta", "Seravezza", "Stazzema", "Viareggio"]
FUELS = {"benzina": "Benzina self", "gasolio": "Gasolio self"}
BASE = "https://opendatacarburanti.mise.gov.it/categorized"
UA = {"User-Agent": "Mozilla/5.0 (compatible; OsservatorioVersilia/1.0; +https://osservatorioversilia.it/)"}
DATE_RE = re.compile(r"(20\d{2})(\d{2})(\d{2})\.csv$")


def norm(value: str) -> str:
    text = unicodedata.normalize("NFKD", value or "")
    text = "".join(char for char in text if not unicodedata.combining(char)).lower().strip()
    return re.sub(r"[^a-z0-9]+", " ", text).strip()


def archive_url(kind: str, year: int, quarter: int) -> str:
    return f"{BASE}/{kind}/{year}/{year}_{quarter}_tr.tar.gz"


def download(url: str, target: Path) -> None:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=600) as response, target.open("wb") as handle:
        while chunk := response.read(1024 * 1024):
            handle.write(chunk)


def decode(raw: bytes) -> str:
    for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise RuntimeError("encoding MIMIT non riconosciuto")


def rows_from_member(archive: tarfile.TarFile, member: tarfile.TarInfo) -> list[dict[str, str]]:
    stream = archive.extractfile(member)
    if stream is None:
        return []
    text = decode(stream.read())
    lines = text.splitlines()
    header_index = next((i for i, line in enumerate(lines) if "idimpianto" in norm(line)), None)
    if header_index is None:
        return []
    header = lines[header_index]
    delimiter = "|" if header.count("|") > header.count(";") else ";"
    return list(csv.DictReader(io.StringIO("\n".join(lines[header_index:])), delimiter=delimiter))


def member_dates(archive: tarfile.TarFile) -> dict[date, tarfile.TarInfo]:
    result: dict[date, tarfile.TarInfo] = {}
    for member in archive.getmembers():
        if not member.isfile():
            continue
        match = DATE_RE.search(member.name)
        if not match:
            continue
        y, m, d = (int(part) for part in match.groups())
        result[date(y, m, d)] = member
    return result


def field(row: dict[str, str], *names: str) -> str:
    mapping = {norm(key): key for key in row}
    for name in names:
        wanted = norm(name)
        if wanted in mapping:
            return mapping[wanted]
    for normalized, key in mapping.items():
        if any(norm(name) in normalized for name in names):
            return key
    raise RuntimeError(f"campo non trovato: {names}; disponibili={list(row)}")


def station_map(archive: tarfile.TarFile, members: list[tarfile.TarInfo]) -> dict[str, str]:
    wanted = {norm(town): town for town in TOWNS}
    mapping: dict[str, str] = {}
    for member in members:
        rows = rows_from_member(archive, member)
        if not rows:
            continue
        aid = field(rows[0], "idimpianto")
        atown = field(rows[0], "Comune")
        aprov = field(rows[0], "Provincia")
        for row in rows:
            town = wanted.get(norm(row.get(atown, "")))
            if not town:
                continue
            province = norm(row.get(aprov, ""))
            if province not in {"lu", "lucca"} and "lucca" not in province:
                continue
            station = str(row.get(aid, "")).strip()
            if station:
                mapping[station] = town
    return mapping


def representative_anag_members(
    by_date: dict[date, tarfile.TarInfo],
    year: int,
    month: int,
) -> list[tarfile.TarInfo]:
    candidates = sorted(day for day in by_date if day.year == year and day.month == month)
    if not candidates:
        return []
    targets = (1, 15, 31)
    selected: list[date] = []
    for target in targets:
        chosen = min(candidates, key=lambda item: abs(item.day - target))
        if chosen not in selected:
            selected.append(chosen)
    return [by_date[item] for item in selected]


def daily_town_medians(
    archive: tarfile.TarFile,
    member: tarfile.TarInfo,
    stations: dict[str, str],
) -> dict[str, dict[str, float | None]]:
    rows = rows_from_member(archive, member)
    if not rows:
        return {town: {fuel: None for fuel in FUELS} for town in TOWNS}
    pid = field(rows[0], "idimpianto")
    pfuel = field(rows[0], "descCarburante")
    pprice = field(rows[0], "prezzo")
    pself = field(rows[0], "isSelf")
    values: dict[str, dict[str, list[float]]] = {
        town: {fuel: [] for fuel in FUELS} for town in TOWNS
    }
    seen: set[tuple[str, str]] = set()
    for row in rows:
        station = str(row.get(pid, "")).strip()
        town = stations.get(station)
        if not town or str(row.get(pself, "")).strip() not in {"1", "1.0"}:
            continue
        fuel = norm(row.get(pfuel, ""))
        if fuel not in FUELS:
            continue
        try:
            price = float(str(row.get(pprice, "")).strip().replace(",", "."))
        except ValueError:
            continue
        if not 0.5 <= price <= 5:
            continue
        key = (station, fuel)
        if key in seen:
            continue
        seen.add(key)
        values[town][fuel].append(price)
    return {
        town: {
            fuel: statistics.median(values[town][fuel]) if values[town][fuel] else None
            for fuel in FUELS
        }
        for town in TOWNS
    }


def quarter_for_month(month: int) -> int:
    return (month - 1) // 3 + 1


def iter_quarters(start: tuple[int, int], end: tuple[int, int]):
    year, month = start
    seen: set[tuple[int, int]] = set()
    while (year, month) <= end:
        key = (year, quarter_for_month(month))
        if key not in seen:
            seen.add(key)
            yield key
        month += 1
        if month == 13:
            year += 1
            month = 1


def in_range(day: date, start: tuple[int, int], end: tuple[int, int]) -> bool:
    return start <= (day.year, day.month) <= end


def build(start: tuple[int, int], end: tuple[int, int], cache_dir: Path) -> dict[str, Any]:
    monthly: dict[tuple[int, int], dict[str, dict[str, list[float]]]] = defaultdict(
        lambda: {town: {fuel: [] for fuel in FUELS} for town in TOWNS}
    )
    daily_counts: dict[tuple[int, int], int] = defaultdict(int)
    provenance: list[dict[str, Any]] = []

    for year, quarter in iter_quarters(start, end):
        anag_path = cache_dir / f"anagrafica-{year}-q{quarter}.tar.gz"
        price_path = cache_dir / f"prezzi-{year}-q{quarter}.tar.gz"
        anag_url = archive_url("anagrafica_impianti_attivi", year, quarter)
        price_url = archive_url("prezzo_alle_8", year, quarter)
        print(f"Scarico {year} Q{quarter} anagrafica...")
        download(anag_url, anag_path)
        print(f"Scarico {year} Q{quarter} prezzi...")
        download(price_url, price_path)

        with tarfile.open(anag_path, "r:gz") as anag, tarfile.open(price_path, "r:gz") as prices:
            anag_dates = member_dates(anag)
            price_dates = member_dates(prices)
            station_maps: dict[tuple[int, int], dict[str, str]] = {}
            for month in range((quarter - 1) * 3 + 1, quarter * 3 + 1):
                if not (start <= (year, month) <= end):
                    continue
                reps = representative_anag_members(anag_dates, year, month)
                if not reps:
                    continue
                station_maps[(year, month)] = station_map(anag, reps)

            used_days = 0
            for day in sorted(price_dates):
                if not in_range(day, start, end):
                    continue
                month_key = (day.year, day.month)
                stations = station_maps.get(month_key)
                if not stations:
                    continue
                medians = daily_town_medians(prices, price_dates[day], stations)
                daily_counts[month_key] += 1
                used_days += 1
                for town in TOWNS:
                    for fuel in FUELS:
                        value = medians[town][fuel]
                        if value is not None:
                            monthly[month_key][town][fuel].append(float(value))

        provenance.append({
            "year": year,
            "quarter": quarter,
            "anagraficaUrl": anag_url,
            "prezziUrl": price_url,
            "priceDaysUsed": used_days,
        })
        anag_path.unlink(missing_ok=True)
        price_path.unlink(missing_ok=True)

    points: list[dict[str, Any]] = []
    for month_key in sorted(monthly):
        year, month = month_key
        observed_days = daily_counts[month_key]
        towns: dict[str, Any] = {}
        for town in TOWNS:
            item: dict[str, Any] = {"observationDays": observed_days}
            for fuel in FUELS:
                values = monthly[month_key][town][fuel]
                item[fuel] = round(statistics.fmean(values), 3) if values else None
                item[f"{fuel}Days"] = len(values)
            towns[town] = item
        points.append({
            "referenceDate": f"{year:04d}-{month:02d}",
            "observationDays": observed_days,
            "towns": towns,
        })

    return {
        "schemaVersion": 2,
        "source": "MIMIT - Archivio storico prezzi praticati e anagrafica impianti",
        "frequency": "monthly",
        "statistic": "media mensile delle mediane comunali giornaliere, self-service",
        "method": "Per ogni giorno si calcola la mediana tra gli impianti attivi del Comune; il valore mensile è la media aritmetica delle mediane giornaliere.",
        "periodStart": f"{start[0]:04d}-{start[1]:02d}",
        "periodEnd": f"{end[0]:04d}-{end[1]:02d}",
        "towns": TOWNS,
        "fuels": FUELS,
        "points": points,
        "provenance": provenance,
    }


def parse_month(value: str) -> tuple[int, int]:
    match = re.fullmatch(r"(20\d{2})-(0[1-9]|1[0-2])", value)
    if not match:
        raise argparse.ArgumentTypeError("usa YYYY-MM")
    return int(match.group(1)), int(match.group(2))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", type=parse_month, default=(2024, 1))
    parser.add_argument("--end", type=parse_month, default=(2026, 6))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.start > args.end:
        raise SystemExit("--start deve precedere --end")
    with tempfile.TemporaryDirectory(prefix="ov-mimit-fuel-") as temp:
        result = build(args.start, args.end, Path(temp))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Creati {len(result['points'])} mesi: {result['periodStart']} → {result['periodEnd']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
