#!/usr/bin/env python3
"""Sportelli bancari per Comune dalla «Lista succursali banche» della Banca d'Italia.

Il file GIAVA è lo storico delle sedi: ogni riga è una versione anagrafica di una
sede (periodo di validità) con il suo periodo di operatività. Una sede si conta al
31 dicembre se è operativa quel giorno nella versione valida quel giorno. La chiave
è la coppia intermediario + sede (ID_INT, ID_SEDE): lo stesso ID_SEDE si ripete fra
banche diverse. Gli uffici di rappresentanza non sono sportelli e restano fuori.

Riconciliazione obbligatoria: al 31 dicembre 2022 i conteggi dei sette Comuni
devono coincidere con la serie Istat «Servizi bancari - dati comunali» (flusso
117_1035_DF_DCAT_SERVBANC_COM_1, che riprende la Banca d'Italia), e il totale
nazionale deve restare vicino ai circa 21.000 sportelli pubblicati per il 2022.
"""
from __future__ import annotations

import csv
import hashlib
import http.cookiejar
import io
import time
import urllib.request
import zipfile
from datetime import date
from typing import Any, Iterable

METRIC = "bankBranchesPer1000"
SNAPSHOT_PREFIX = "data/source-snapshots/bdi-sportelli-bancari-"
PAGE = "https://www.bancaditalia.it/statistiche/basi-dati/giava/index.html"
URL = ("https://infostat.bancaditalia.it/GIAVAInquiry-public/getAreaDownloadExport.do?referenceDate="
       "&product=VFLUSSO_SEDE_BANCHE&language=IT&exportType=CSV&username=OBLIXANONYMOUS&isCompressed=S")
LOC_URL = URL.replace("VFLUSSO_SEDE_BANCHE", "VFLUSSO_LOCALITA")
PUBLISHER = "Banca d'Italia — Lista succursali banche (open data GIAVA)"
UA = "Mozilla/5.0 (compatible; OsservatorioVersilia-data-audit/1.0)"
# Comune Istat → denominazione Banca d'Italia (provincia di Lucca)
TOWNS = {"046005": "CAMAIORE", "046013": "FORTE DEI MARMI", "046018": "MASSAROSA", "046024": "PIETRASANTA",
         "046028": "SERAVEZZA", "046030": "STAZZEMA", "046033": "VIAREGGIO"}
# Istat, Servizi bancari - dati comunali, sportelli al 2022 (sonda del 17 novembre 2026)
ISTAT_2022 = {"046005": 11, "046013": 7, "046018": 5, "046024": 10, "046028": 7, "046030": 1, "046033": 24}
ITALY_2022_RANGE = (20000, 22500)
EXCLUDED_TYPES = {"005"}  # uffici di rappresentanza
FIRST_YEAR = 2018         # primo anno con popolazione comunale al 1° gennaio successivo nel catalogo


class BranchError(RuntimeError):
    pass


def fetch(url: str) -> bytes:
    """Il servizio GIAVA reindirizza impostando un cookie di sessione."""
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
    errors = []
    for attempt in range(1, 4):
        try:
            with opener.open(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=600) as r:
                return r.read()
        except Exception as error:  # noqa: BLE001
            errors.append(f"tentativo {attempt}: {type(error).__name__}: {error}")
            time.sleep(20 * attempt)
    raise BranchError(f"{url}: " + " | ".join(errors))


def csv_rows(archive: bytes) -> tuple[str, list[dict[str, str]]]:
    with zipfile.ZipFile(io.BytesIO(archive)) as z:
        names = [n for n in z.namelist() if n.lower().endswith(".csv")]
        if len(names) != 1:
            raise BranchError(f"archivio GIAVA inatteso: {z.namelist()}")
        text = z.read(names[0]).decode("utf-8-sig", errors="replace")
    rows = [{(k or "").strip(): (v or "").strip() for k, v in row.items()} for row in csv.DictReader(io.StringIO(text), delimiter=";")]
    return names[0], rows


REQUIRED = {"ID_INT", "ID_SEDE", "DATA_I_OPER", "DATA_F_OPER", "DATA_I_VAL", "DATA_F_VAL", "CAB_COM_ITA", "DES_COM_ITA", "STATO", "TIPO_SEDE"}


def localities(rows: list[dict[str, str]]) -> tuple[dict[str, str], set[str]]:
    """CAB dei sette Comuni (validi oggi, provincia di Lucca) e CAB dei Comuni toscani."""
    today = date.today().isoformat()
    current = [r for r in rows if r.get("DATA_I_VAL", "") <= today <= r.get("DATA_F_VAL", "9999-12-31") and r.get("STATO") == "86"]
    cabs = {}
    for code, name in TOWNS.items():
        found = {r["CAB_COMUNE"] for r in current if r.get("DEN_COMUNE") == name and r.get("DEN_PROVINCIA") == "LUCCA"}
        if len(found) != 1:
            raise BranchError(f"località {name}: CAB non univoco {sorted(found)}")
        cabs[code] = found.pop()
    tuscany = {r["CAB_COMUNE"] for r in rows if r.get("DEN_REGIONE") == "TOSCANA" and r.get("CAB_COMUNE") not in ("", "0")}
    if not 250 <= len(tuscany) <= 400:
        raise BranchError(f"Comuni toscani nell'elenco località: {len(tuscany)}")
    return cabs, tuscany


def counts(rows: Iterable[dict[str, str]], cabs: dict[str, str], tuscany: set[str], days: list[str]) -> dict[str, dict[str, int]]:
    """{giorno: {codice Istat | tuscany | italy: sedi operative}}."""
    rows = list(rows)
    missing = REQUIRED - set(rows[0]) if rows else REQUIRED
    if missing:
        raise BranchError(f"colonne GIAVA mancanti: {sorted(missing)}")
    by_cab = {cab: code for code, cab in cabs.items()}
    out: dict[str, dict[str, set[tuple[str, str]]]] = {d: {} for d in days}
    for r in rows:
        if r["STATO"] != "86" or r["TIPO_SEDE"] in EXCLUDED_TYPES:
            continue
        key = (r["ID_INT"], r["ID_SEDE"])
        for day in days:
            if r["DATA_I_OPER"] <= day <= r["DATA_F_OPER"] and r["DATA_I_VAL"] <= day <= r["DATA_F_VAL"]:
                scopes = ["italy"] + (["tuscany"] if r["CAB_COM_ITA"] in tuscany else []) + ([by_cab[r["CAB_COM_ITA"]]] if r["CAB_COM_ITA"] in by_cab else [])
                for scope in scopes:
                    out[day].setdefault(scope, set()).add(key)
    return {d: {scope: len(keys) for scope, keys in v.items()} for d, v in out.items()}


def reconcile(table: dict[str, dict[str, int]]) -> None:
    day = "2022-12-31"
    got = {code: table[day].get(code, 0) for code in TOWNS}
    if got != ISTAT_2022:
        raise BranchError(f"conteggi 2022 diversi dalla serie Istat: {got} ≠ {ISTAT_2022}")
    italy = table[day].get("italy", 0)
    if not ITALY_2022_RANGE[0] <= italy <= ITALY_2022_RANGE[1]:
        raise BranchError(f"sportelli Italia 2022 fuori intervallo: {italy}")


def build_snapshot(year: int, archive: bytes, loc_archive: bytes, population: dict[str, Any]) -> dict[str, Any]:
    """`population`: {"towns": {codice: {anno: residenti al 1° gennaio}}, "tuscany": n, "italy": n, "year": anno}."""
    if f"{year}-12-31" >= date.today().isoformat():
        raise BranchError(f"anno {year} non ancora concluso")
    member, rows = csv_rows(archive)
    _, loc_rows = csv_rows(loc_archive)
    cabs, tuscany = localities(loc_rows)
    years = list(range(FIRST_YEAR, year + 1))
    days = sorted({f"{y}-12-31" for y in years} | {"2022-12-31"})
    table = counts(rows, cabs, tuscany, days)
    reconcile(table)
    for y in years:
        for code in TOWNS:
            if y + 1 not in population["towns"][code]:
                raise BranchError(f"popolazione al 1° gennaio {y + 1} assente per {code}")
    if int(population["year"]) != year + 1:
        raise BranchError(f"popolazione Toscana/Italia al 1° gennaio {population['year']}, attesa {year + 1}")
    day = f"{year}-12-31"
    return {
        "schemaVersion": 1, "version": f"bdi-sportelli-bancari-{year}-v1", "retrieved": date.today().isoformat(),
        "publisher": PUBLISHER, "sourceUrl": PAGE, "dataUrl": URL, "localityUrl": LOC_URL,
        "archive": {"member": member, "bytes": len(archive), "sha256": hashlib.sha256(archive).hexdigest(), "records": len(rows)},
        "localityArchive": {"bytes": len(loc_archive), "sha256": hashlib.sha256(loc_archive).hexdigest()},
        "rule": "Sedi operative al 31 dicembre nella versione anagrafica valida quel giorno, chiave intermediario + sede, "
                "Stato Italia, esclusi gli uffici di rappresentanza.",
        "cab": cabs,
        "years": years,
        "branches": {code: [table[f"{y}-12-31"].get(code, 0) for y in years] for code in TOWNS},
        "scopes": {"tuscany": table[day].get("tuscany", 0), "italy": table[day].get("italy", 0)},
        "population": {"year": year + 1, "tuscany": population["tuscany"], "italy": population["italy"],
                       "towns": {code: [population["towns"][code][y + 1] for y in years] for code in TOWNS}},
        "qualityGate": {"status": "PASS", "istat2022": ISTAT_2022, "italy2022": table["2022-12-31"].get("italy", 0),
                        "note": "Conteggi dei sette Comuni al 31 dicembre 2022 identici alla serie Istat «Servizi bancari - dati comunali»."},
    }


def rate(count: int, residents: int) -> float:
    return count / residents * 1000


def build_metric(snapshot: dict[str, Any], rows_meta: list[dict[str, Any]], path: str) -> dict[str, Any]:
    years = snapshot["years"]
    last = years[-1]
    pop = snapshot["population"]
    rows = []
    for base in rows_meta:
        code = base["code"]
        values = [rate(n, p) for n, p in zip(snapshot["branches"][code], pop["towns"][code])]
        rows.append({"town": base["town"], "code": code, "slug": base["slug"], "value": values[-1],
                     "formatted": f"{values[-1]:.2f}".replace(".", ",") + " ogni 1.000",
                     "series": {"years": years, "values": values}, "normalized": None, "benchmarkValue": values[-1]})
    total = sum(snapshot["branches"][c][-1] for c in TOWNS)
    residents = sum(pop["towns"][c][-1] for c in TOWNS)
    first_total = sum(snapshot["branches"][c][0] for c in TOWNS)
    return {
        "meta": {
            "key": METRIC, "theme": "economia", "label": "Sportelli bancari ogni 1.000 residenti", "shortLabel": "Sportelli bancari",
            "description": (f"Sportelli bancari aperti al 31 dicembre {last} secondo l'elenco delle succursali della Banca d'Italia, "
                            f"rapportati ai residenti al 1° gennaio {last + 1}."),
            "unit": "per1000", "year": str(last), "source": "Banca d'Italia — Lista succursali banche", "polarity": "neutral",
            "benchmark": {"year": str(last), "tuscany": rate(snapshot["scopes"]["tuscany"], pop["tuscany"]),
                          "italy": rate(snapshot["scopes"]["italy"], pop["italy"]), "source": "Banca d'Italia / Istat",
                          "url": snapshot["dataUrl"], "sourceSnapshot": path,
                          "note": (f"Sportelli in Toscana ({snapshot['scopes']['tuscany']}) e in Italia ({snapshot['scopes']['italy']}) "
                                   f"al 31 dicembre {last}, con la stessa regola dei Comuni, su residenti al 1° gennaio {last + 1}.")},
            "sourceMeta": {"snapshot": path, "note": "Conteggi 2022 riconciliati 7/7 con la serie Istat «Servizi bancari - dati comunali»."},
        },
        "sourceUrl": snapshot["sourceUrl"],
        "rows": rows,
        "aggregate": {"value": rate(total, residents), "label": "Densità Versilia",
                      "note": f"{total} sportelli nei sette Comuni al 31 dicembre {last} ({first_total} nel {years[0]}), ogni 1.000 residenti."},
        "normalizedAggregate": None,
        "method": {
            "type": "Elaborazione Osservatorio",
            "formula": (f"Sportelli bancari aperti al 31 dicembre di ogni anno / popolazione residente al 1° gennaio successivo × 1.000. "
                        f"Uno sportello si conta se è operativo quel giorno nella versione dell'elenco valida quel giorno."),
            "caveat": ("Conta le succursali delle banche, non gli sportelli automatici (bancomat), gli uffici postali né gli uffici di "
                       "rappresentanza. Non dice quanto sono aperti né quali servizi offrono. Nei Comuni piccoli uno sportello in più o "
                       "in meno sposta molto il valore."),
            "coverage": f"7/7 per ciascun anno ({years[0]}–{last})",
        },
    }
