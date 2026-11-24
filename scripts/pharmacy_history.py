#!/usr/bin/env python3
"""Serie delle farmacie ogni 1.000 residenti nei sette Comuni (31 dicembre 2019–2025).

Stessa regola del valore pubblicato (`a3-health-pharmacies-benchmark-2025.json`): sedi con codice ministeriale
univoco valide al 31 dicembre secondo gli intervalli di validità del file del Ministero della Salute, incluse
succursali e dispensari. Il file corrente contiene anche le registrazioni chiuse con la data di fine (dal 2005),
quindi ogni anno si ricostruisce dallo stesso file. Controlli:
- il 2025 ricostruito coincide, Comune per Comune, con i conteggi dello snapshot pubblicato;
- se il file di fine 2024 è ancora online, il 2024 ricostruito coincide con quello dichiarato allora.
Il denominatore (residenti al 1° gennaio dell'anno dopo) viene dalla serie pubblicata della popolazione in build.
"""
from __future__ import annotations

import csv
import datetime as dt
import hashlib
import io
import re
from typing import Any, Callable

DATASET = "https://www.dati.salute.gov.it/it/dataset/farmacie"
FILE = "https://www.dati.salute.gov.it/sites/default/files/opendata/FRM_FARMA_5_{stamp}.csv"
CHECK_STAMP = "20241231"
SNAPSHOT = "data/source-snapshots/salute-farmacie-serie.json"
PUBLISHED = "data/source-snapshots/a3-health-pharmacies-benchmark-2025.json"
METRIC = "pharmaciesPer1000"
TOWNS = ("046005", "046013", "046018", "046024", "046028", "046030", "046033")
YEARS = tuple(range(2019, 2026))
FIELDS = ("cod_farmacia", "cod_comune", "codice_tipologia", "data_inizio_validita", "data_fine_validita")


class PharmacyError(RuntimeError):
    pass


def _date(value: str) -> dt.date | None:
    value = str(value or "").strip()
    if value in ("", "-"):
        return None
    try:
        return dt.datetime.strptime(value, "%d/%m/%Y").date()
    except ValueError as exc:
        raise PharmacyError(f"data di validità non leggibile: {value!r}") from exc


def town_rows(raw: bytes) -> list[dict[str, str]]:
    """Righe dei sette Comuni, con i campi della regola."""
    text = raw.decode("utf-8-sig")
    if "<html" in text[:500].lower():
        raise PharmacyError("risposta HTML invece del CSV")
    reader = csv.DictReader(io.StringIO(text), delimiter=";")
    if not set(FIELDS) <= set(reader.fieldnames or []):
        raise PharmacyError(f"intestazioni attese assenti: {sorted(set(FIELDS) - set(reader.fieldnames or []))}")
    rows = [{f: str(r[f]).strip() for f in FIELDS} for r in reader if str(r.get("cod_comune") or "").strip() in TOWNS]
    if {r["cod_comune"] for r in rows} != set(TOWNS):
        raise PharmacyError("righe assenti per almeno un Comune")
    return rows


def counts_at(rows: list[dict[str, str]], day: dt.date) -> dict[str, int]:
    """Sedi con codice univoco valide in quel giorno, per Comune."""
    sites: dict[str, set[str]] = {c: set() for c in TOWNS}
    for r in rows:
        start, end = _date(r["data_inizio_validita"]), _date(r["data_fine_validita"])
        if start is None or (end is not None and end < start):
            raise PharmacyError(f"intervallo di validità incompleto o invertito: {r['cod_farmacia']}")
        if start <= day and (end is None or day <= end):
            sites[r["cod_comune"]].add(r["cod_farmacia"])
    return {c: len(v) for c, v in sites.items()}


def current_stamp(page: bytes) -> str:
    stamps = sorted(set(re.findall(rb"FRM_FARMA_5_(\d{8})\.csv", page)))
    if len(stamps) != 1:
        raise PharmacyError(f"file corrente non univoco nella pagina del dataset: {stamps}")
    return stamps[0].decode()


def build_snapshot(fetch: Callable[[str], bytes], published: dict[str, int], check: Callable[[str], bytes | None]) -> dict[str, Any]:
    """`published`: codice → sedi pubblicate al 31/12/2025. `check(url)` restituisce None se il file 2024 non c'è più."""
    stamp = current_stamp(fetch(DATASET))
    url = FILE.format(stamp=stamp)
    raw = fetch(url)
    rows = town_rows(raw)
    counts = {y: counts_at(rows, dt.date(y, 12, 31)) for y in YEARS}
    if counts[2025] != {c: int(published[c]) for c in TOWNS}:
        raise PharmacyError(f"2025 ricostruito {counts[2025]} ≠ pubblicato {published}")
    cross = None
    old = check(FILE.format(stamp=CHECK_STAMP))
    if old is not None:
        then = counts_at(town_rows(old), dt.date(2024, 12, 31))
        if then != counts[2024]:
            raise PharmacyError(f"2024 ricostruito {counts[2024]} ≠ file di fine 2024 {then}")
        cross = {"url": FILE.format(stamp=CHECK_STAMP), "sha256": hashlib.sha256(old).hexdigest(), "year": 2024, "status": "PASS"}
    return {
        "schemaVersion": 1, "version": f"salute-farmacie-serie-2019-2025-{stamp}-v1", "retrieved": dt.date.today().isoformat(),
        "publisher": "Ministero della Salute — Open data farmacie", "sourceUrl": url, "sha256": hashlib.sha256(raw).hexdigest(),
        "rule": "Sedi con codice ministeriale univoco valide al 31 dicembre (ordinarie, succursali, dispensari) dagli intervalli di validità del file corrente.",
        "years": list(YEARS),
        "counts": {c: [counts[y][c] for y in YEARS] for c in TOWNS},
        "rows": sorted(([r[f] for f in FIELDS] for r in rows)),
        "crossCheck": cross,
        "qualityGate": {"status": "PASS", "note": "31/12/2025 identico ai conteggi pubblicati per i 7 Comuni"
                        + ("; 31/12/2024 identico al file di fine 2024." if cross else "; file di fine 2024 non più online.")},
    }


def published_counts(snapshot: dict[str, Any]) -> dict[str, int]:
    return {c: sum(r[2] == c for r in snapshot["records"]) for c in TOWNS}


def apply(metrics: dict[str, dict[str, Any]], snapshot: dict[str, Any], path: str) -> None:
    """Serie del tasso: sedi al 31/12/Y / residenti al 1/1/(Y+1) × 1.000, arrotondato come il valore pubblicato."""
    metric = metrics[METRIC]
    if str(metric["meta"]["year"]) != "2025" or snapshot["years"] != list(YEARS):
        raise PharmacyError("anno pubblicato o anni della serie cambiati")
    population = {r["code"]: r.get("series") or {} for r in metrics["population"]["rows"]}
    for row in metric["rows"]:
        pop = population[row["code"]]
        by_year = dict(zip((int(y) for y in pop.get("years") or []), pop.get("values") or []))
        if any(y + 1 not in by_year for y in YEARS):
            raise PharmacyError(f"{row['town']}: residenti al 1° gennaio mancanti per la serie")
        values = [round(n / by_year[y + 1] * 1000, 2) for n, y in zip(snapshot["counts"][row["code"]], YEARS)]
        if values[-1] != row["value"]:
            raise PharmacyError(f"{row['town']}: serie {values[-1]} ≠ valore pubblicato {row['value']}")
        row["series"] = {"years": list(YEARS), "values": values}
    metric["meta"].setdefault("sourceMeta", {})["historySnapshot"] = path
    note = (" Serie dal 2019 al 2025 con la stessa regola, ricostruita dagli intervalli di validità del file ministeriale corrente "
            "e con i residenti al 1° gennaio dell'anno successivo.")
    if note.strip() not in metric["method"].get("caveat", ""):
        metric["method"]["caveat"] = (metric["method"].get("caveat", "").rstrip() + note).strip()
