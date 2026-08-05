#!/usr/bin/env python3
"""Extend the validated OpenBDAP snapshot with homogeneous historical years."""
from __future__ import annotations

import io
import json
import math
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

import requests
import build_bilanci_snapshot as base

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "site-data.json"
SNAPSHOT_PATH = ROOT / "data" / "source-snapshots" / "bilanci-v1.6.0.json"
FIRST_YEAR = 2019
LAST_YEAR = 2025
TRANSPORTS: dict[str, str] = {}


def archive_paths(year: int) -> dict[str, str]:
    prefix = f"/Datasets_FET/Rendiconto/{year}/{year}_Rendiconto"
    return {
        f"{year}-schemi": prefix + " - Schemi di bilancio_TOSCANA.zip",
        f"{year}-indicatori": prefix + " - Piano degli indicatori_TOSCANA.zip",
    }


def validate_zip(content: bytes, label: str) -> None:
    if len(content) < 10_000 or not content.startswith(b"PK"):
        raise RuntimeError(f"Risposta non ZIP o troppo piccola per {label}: {len(content)} byte")
    with zipfile.ZipFile(io.BytesIO(content)) as archive:
        if not archive.infolist():
            raise RuntimeError(f"Archivio vuoto: {label}")
        bad = archive.testzip()
        if bad:
            raise RuntimeError(f"Archivio corrotto {label}, primo file errato: {bad}")


def download_archive(session: requests.Session, path: str) -> tuple[bytes, str]:
    official_url = base.BASE + quote(path, safe="/:_-.")
    encoded = quote(official_url, safe="")
    attempts = [
        ("diretto RGS", official_url),
        ("proxy raw AllOrigins", f"https://api.allorigins.win/raw?url={encoded}"),
        ("proxy raw CorsProxy", f"https://corsproxy.io/?url={encoded}"),
    ]
    errors = []
    for label, transport_url in attempts:
        try:
            response = session.get(transport_url, timeout=base.TIMEOUT)
            response.raise_for_status()
            validate_zip(response.content, f"{path} via {label}")
            TRANSPORTS[official_url] = label
            return response.content, official_url
        except (requests.RequestException, RuntimeError, zipfile.BadZipFile) as exc:
            errors.append(f"{label}: {type(exc).__name__}: {exc}")
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

    snapshot["version"] = "2026.08.05-local-v1.6.0-bilanci-storici"
    snapshot["generated_at"] = datetime.now(timezone.utc).isoformat()
    snapshot["scope"] = f"Rendiconti OpenBDAP {FIRST_YEAR}–{LAST_YEAR} dei sette Comuni dell’Osservatorio Versilia."
    snapshot["source"]["years"] = dict(sorted(sources.items(), key=lambda item: int(item[0])))
    snapshot["selection_rules"]["years"] = years
    snapshot["metrics"] = metrics
    snapshot["history_audit"] = {
        "accepted_years": years,
        "coverage": "7/7 per ogni annualità e indicatore ammesso",
        "population_denominator": "Serie Istat al 1° gennaio già materializzata nel progetto.",
        "download_transport": TRANSPORTS,
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
    print(f"Serie OpenBDAP estese al periodo {FIRST_YEAR}–{LAST_YEAR} con copertura 7/7.")


if __name__ == "__main__":
    main()
