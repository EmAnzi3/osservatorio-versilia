#!/usr/bin/env python3
"""Serie storica degli incassi da verifica e controllo per residente (SIOPE, movimenti cumulati di entrata).

Stessa regola del valore pubblicato (`materialize_fiscal_lotto_b.py`): dal file regionale toscano «SIOPE
Movimenti cumulati mensili di Entrata» dell'anno, al mese AAAA/12, si sommano gli importi cumulati dei codici
gestionali la cui descrizione ufficiale riporta «riscossa/o/e a seguito di attività di verifica e controllo»;
il valore per residente divide il totale per la popolazione Istat riportata nello stesso file. Si risale
dall'anno pubblicato finché il file dell'anno è scaricabile e contiene il mese di dicembre per tutti e sette
i Comuni; l'anno pubblicato deve coincidere con i valori del catalogo.
"""
from __future__ import annotations

import csv
import hashlib
import io
import math
import re
from datetime import date
from typing import Any, Callable

SNAPSHOT = "data/source-snapshots/siope-recupero-fiscale-serie.json"
METRIC = "fiscalRecoveryActivity"
FIRST = 2019
URL = "https://bdap-opendata.rgs.mef.gov.it/SpodCkanApi/api/1/rest/dataset/spd_rnd_ent_sio_reg09_01_{year}.csv"
TOWNS = {"046005": "Camaiore", "046013": "Forte dei Marmi", "046018": "Massarosa", "046024": "Pietrasanta",
         "046028": "Seravezza", "046030": "Stazzema", "046033": "Viareggio"}
RECOVERY = re.compile(r"riscoss[aoei] a seguito di attivit\S* di verifica e controllo")


class RecoveryHistoryError(RuntimeError):
    pass


class Unavailable(RecoveryHistoryError):
    """Il file dell'anno non è servito come CSV (il portale risponde con un errore)."""


def _text(raw: bytes) -> str:
    for encoding in ("utf-8-sig", "cp1252"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise RecoveryHistoryError("codifica non riconosciuta")


def read_year(raw: bytes, year: int) -> dict[str, dict[str, Any]]:
    if not raw.lstrip().startswith(b'"Codice istat provincia"'):
        raise Unavailable(f"{year}: risposta non CSV ({raw[:80]!r})")
    month = f"{year}/12"
    out: dict[str, dict[str, Any]] = {}
    for row in csv.DictReader(io.StringIO(_text(raw)), delimiter=";"):
        c = str(row["Codice istat provincia"]).strip().zfill(3) + str(row["Codice istat comune"]).strip().zfill(3)
        if c not in TOWNS or row["Descrizione Tipo Ente BDAP"].strip() != "COMUNI" or row["Anno/Mese calendario"].strip() != month:
            continue
        town = out.setdefault(c, {"total": 0.0, "codes": {}, "population": None})
        pop = int(float(row["Popolazione ISTAT"].replace(",", ".")))
        if town["population"] not in (None, pop):
            raise RecoveryHistoryError(f"{year} {TOWNS[c]}: popolazione incoerente")
        town["population"] = pop
        if RECOVERY.search(row["Descrizione CG"].lower()):
            amount = float(row["Importo cumulato"].replace(",", "."))
            code = row["Codice Gestionale Enti Locali"].strip()
            town["codes"][code] = town["codes"].get(code, 0.0) + amount
            town["total"] += amount
    missing = [TOWNS[c] for c in TOWNS if c not in out]
    if missing:
        raise Unavailable(f"{year}: dicembre assente per {missing}")
    for town in out.values():
        town["perResident"] = town["total"] / town["population"]
    return out


def build_snapshot(fetch: Callable[[str], bytes], published: dict[str, float], last: int) -> dict[str, Any]:
    """`published`: codice Comune → valore per residente pubblicato per l'anno `last`."""
    years: dict[int, Any] = {}
    sources: dict[str, Any] = {}
    stop = None
    for year in range(last, FIRST - 1, -1):
        url = URL.format(year=year)
        try:
            raw = fetch(url)
            years[year] = read_year(raw, year)
        except Unavailable as error:
            if year == last:
                raise
            stop = str(error)
            break
        sources[str(year)] = {"url": url, "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}
    for c, value in published.items():
        live = years[last][c]["perResident"]
        if not math.isclose(live, value, rel_tol=0, abs_tol=1e-9):
            raise RecoveryHistoryError(f"{TOWNS[c]} {last}: fonte {live} ≠ pubblicato {value}")
    ordered = sorted(years)
    if len(ordered) < 2:
        raise RecoveryHistoryError(f"serie di un solo anno ({stop})")
    return {
        "schemaVersion": 1, "version": f"siope-recupero-fiscale-serie-{ordered[0]}-{last}-v1", "retrieved": date.today().isoformat(),
        "publisher": "Ragioneria Generale dello Stato — BDAP Open Data / SIOPE", "urlTemplate": URL, "years": ordered, "stoppedAt": stop,
        "sources": sources,
        "rule": ("Dicembre cumulato; somma dei codici gestionali con descrizione «riscossa/o/e a seguito di attività di verifica e controllo»; "
                 "per residente = totale / popolazione Istat del file; anni consecutivi con file scaricabile e 7/7 Comuni."),
        "towns": {c: {str(y): years[y][c] for y in ordered} for c in TOWNS},
        "qualityGate": {"status": "PASS", "note": f"Anno {last} identico ai valori pubblicati per i 7 Comuni."},
    }


def apply(metrics: dict[str, dict[str, Any]], snapshot: dict[str, Any], path: str) -> None:
    metric = metrics[METRIC]
    years = snapshot["years"]
    if str(years[-1]) != str(metric["meta"]["year"]):
        raise RecoveryHistoryError("serie non allineata all'anno pubblicato")
    for row in metric["rows"]:
        values = [snapshot["towns"][row["code"]][str(y)]["perResident"] for y in years]
        if not math.isclose(values[-1], row["value"], rel_tol=0, abs_tol=1e-9):
            raise RecoveryHistoryError(f"{row['town']}: serie ≠ valore pubblicato")
        row["series"] = {"years": list(years), "values": values}
    metric["meta"].setdefault("sourceMeta", {})["historySnapshot"] = path
    metric["method"]["historyNote"] = (f"Serie {years[0]}–{years[-1]} degli incassi da verifica e controllo per residente, stessa regola SIOPE "
                                       "del valore corrente; il contributo DAIT resta riferito all'anno corrente. Euro correnti.")
