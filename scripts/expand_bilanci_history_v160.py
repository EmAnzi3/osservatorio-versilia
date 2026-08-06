#!/usr/bin/env python3
"""Extend the validated OpenBDAP snapshot with homogeneous historical years."""
from __future__ import annotations

import io
import json
import math
import time
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

import requests
import build_bilanci_snapshot as base

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "site-data.json"
SNAPSHOT_PATH = ROOT / "data" / "source-snapshots" / "bilanci-v1.6.0.json"
CACHE_DIR = ROOT / ".cache" / "openbdap"
FIRST_YEAR = 2019
LAST_YEAR = 2025
TRANSPORTS: dict[str, str] = {}


def archive_paths(year: int) -> dict[str, str]:
    prefix = f"/Datasets_FET/Rendiconto/{year}/{year}_Rendiconto"
    return {
        f"{year}-schemi": prefix + " - Schemi di bilancio_TOSCANA.zip",
        f"{year}-indicatori": prefix + " - Piano degli indicatori_TOSCANA.zip",
    }


def cache_path(path: str) -> Path:
    return CACHE_DIR / path.lstrip("/")


def validate_zip(content: bytes, label: str) -> None:
    if len(content) < 10_000 or not content.startswith(b"PK"):
        raise RuntimeError(f"Risposta non ZIP o troppo piccola per {label}: {len(content)} byte")
    with zipfile.ZipFile(io.BytesIO(content)) as archive:
        if not archive.infolist():
            raise RuntimeError(f"Archivio vuoto: {label}")
        bad = archive.testzip()
        if bad:
            raise RuntimeError(f"Archivio corrotto {label}, primo file errato: {bad}")


def read_cached_archive(path: str, official_url: str) -> tuple[bytes, str] | None:
    target = cache_path(path)
    if not target.exists():
        return None
    try:
        content = target.read_bytes()
        validate_zip(content, f"cache {target}")
    except (OSError, RuntimeError, zipfile.BadZipFile):
        target.unlink(missing_ok=True)
        return None
    TRANSPORTS[official_url] = "cache persistente GitHub Actions"
    print(f"Archivio OpenBDAP riutilizzato dalla cache: {target}")
    return content, official_url


def save_cached_archive(path: str, content: bytes) -> None:
    target = cache_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(target.suffix + ".tmp")
    temporary.write_bytes(content)
    temporary.replace(target)


def download_archive(session: requests.Session, path: str) -> tuple[bytes, str]:
    official_url = base.BASE + quote(path, safe="/:_-.")
    cached = read_cached_archive(path, official_url)
    if cached is not None:
        return cached

    encoded = quote(official_url, safe="")
    transports = [
        ("diretto RGS", official_url),
        ("proxy raw AllOrigins", f"https://api.allorigins.win/raw?url={encoded}"),
        ("proxy raw CorsProxy", f"https://corsproxy.io/?url={encoded}"),
    ]
    errors: list[str] = []
    for round_number in range(1, 5):
        for label, transport_url in transports:
            try:
                response = session.get(transport_url, timeout=base.TIMEOUT)
                response.raise_for_status()
                validate_zip(response.content, f"{path} via {label}")
                save_cached_archive(path, response.content)
                TRANSPORTS[official_url] = label
                print(f"Archivio OpenBDAP acquisito al tentativo {round_number}: {official_url}")
                return response.content, official_url
            except (requests.RequestException, RuntimeError, zipfile.BadZipFile, OSError) as exc:
                errors.append(
                    f"round {round_number}, {label}: {type(exc).__name__}: {exc}"
                )
        if round_number < 4:
            time.sleep(10 * round_number)
    raise RuntimeError(
        f"Archivio OpenBDAP non recuperabile: {official_url}\n" + "\n".join(errors)
    )


def main() -> None:
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    snapshot = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
    populations = base.population_lookup(data)
    years = list(range(FIRST_YEAR, LAST_YEAR + 1))
    for town in base.TOWN_CODES:
        missing = [year for year in years if year not in populations[town]]
        if missing:
            raise RuntimeError(f"Popolazione Istat mancante per {town}: {missing}")

    # The already validated 2024–2025 snapshot is retained unchanged. Only missing
    # historical years are downloaded and appended.
    for year in (2024, 2025):
        for town in base.TOWN_CODES:
            if str(year) not in snapshot["raw"][town]["years"]:
                raise RuntimeError(f"Snapshot base validato incompleto: {town}, {year}")

    session = requests.Session()
    session.headers.update({
        "User-Agent": "OsservatorioVersilia/1.0 (+https://emanzi3.github.io/osservatorio-versilia/)",
        "Accept": "application/zip,*/*;q=0.8",
    })

    sources = dict(snapshot["source"].get("years", {}))
    added_years: list[int] = []
    for year in years:
        key = str(year)
        if all(key in snapshot["raw"][town]["years"] for town in base.TOWN_CODES):
            continue
        downloaded = {
            label: download_archive(session, path)
            for label, path in archive_paths(year).items()
        }
        year_raw, sources[key] = base.build_year(year, populations, downloaded)
        if set(year_raw) != set(base.TOWN_CODES):
            raise RuntimeError(f"Copertura comunale incompleta per {year}: {sorted(year_raw)}")
        for town, values in year_raw.items():
            snapshot["raw"][town]["years"][key] = values
        added_years.append(year)

    metric_keys = list(base.compute_values(snapshot["raw"]["Massarosa"]["years"][str(LAST_YEAR)]))
    metrics: dict[str, dict] = {}
    excluded_rigid: dict[str, dict[str, float]] = {}
    for metric_key in metric_keys:
        accepted = []
        for year in years:
            values = {
                town: float(base.compute_values(snapshot["raw"][town]["years"][str(year)])[metric_key])
                for town in base.TOWN_CODES
            }
            if not all(math.isfinite(value) for value in values.values()):
                raise RuntimeError(f"Valore non finito per {metric_key}, {year}")
            if metric_key == "rigidExpenditureShare" and not all(0 <= value <= 100 for value in values.values()):
                excluded_rigid[str(year)] = values
                continue
            accepted.append(year)
        metrics[metric_key] = {
            "coverage": "7/7",
            "years": accepted,
            "values": {
                town: {
                    str(year): base.compute_values(snapshot["raw"][town]["years"][str(year)])[metric_key]
                    for year in accepted
                }
                for town in base.TOWN_CODES
            },
        }

    for key, metric in metrics.items():
        minimum = 2 if key == "rigidExpenditureShare" else len(years)
        if len(metric["years"]) < minimum:
            raise RuntimeError(f"Serie insufficiente per {key}: {metric['years']}")

    previous_audit = snapshot.get("history_audit", {})
    previous_transports = dict(previous_audit.get("download_transport", {}))
    previous_transports.update(TRANSPORTS)

    snapshot["version"] = "2026.08.05-local-v1.6.0-bilanci-storici"
    if added_years or not snapshot.get("generated_at"):
        snapshot["generated_at"] = datetime.now(timezone.utc).isoformat()
    snapshot["scope"] = f"Rendiconti OpenBDAP {FIRST_YEAR}–{LAST_YEAR} dei sette Comuni dell’Osservatorio Versilia."
    snapshot["source"]["years"] = dict(sorted(sources.items(), key=lambda item: int(item[0])))
    snapshot["selection_rules"]["years"] = years
    snapshot["metrics"] = metrics
    snapshot["history_audit"] = {
        "accepted_years": years,
        "coverage": "7/7 per ogni annualità e indicatore ammesso",
        "population_denominator": "Serie Istat al 1° gennaio già materializzata nel progetto.",
        "download_transport": previous_transports,
        "integrity": "Ogni risposta deve essere un archivio ZIP integro; SHA-256 degli archivi e dei CSV selezionati conservati nello snapshot.",
        "rigid_expenditure_excluded_years": excluded_rigid,
    }
    caveat = (
        "Le serie storiche sono mostrate soltanto per annualità con copertura completa 7/7 e denominatore "
        "demografico Istat omogeneo; nessun valore è interpolato o stimato."
    )
    if caveat not in snapshot["caveats"]:
        snapshot["caveats"].append(caveat)
    SNAPSHOT_PATH.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if added_years:
        print(f"Serie OpenBDAP estese al periodo {FIRST_YEAR}–{LAST_YEAR} con copertura 7/7; aggiunti gli anni {added_years}.")
    else:
        print(f"Serie OpenBDAP {FIRST_YEAR}–{LAST_YEAR} già complete e nuovamente validate 7/7.")


if __name__ == "__main__":
    main()
