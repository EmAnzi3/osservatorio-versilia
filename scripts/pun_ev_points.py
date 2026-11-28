#!/usr/bin/env python3
"""Punti di ricarica pubblici ogni 1.000 residenti dai livelli aperti della Piattaforma Unica Nazionale (GSE/MASE).

La pagina «Installazione dei punti di ricarica» della PUN legge livelli ArcGIS pubblici: il conteggio dei punti di
ricarica per ogni Comune italiano (`Comuni_Italiani`), per Regione (`Regioni_Italiane`) e lo storico nazionale
(`Installazioni_storico`). La data di riferimento è l'ultima data dello storico nazionale, il cui totale deve
coincidere con la somma dei Comuni e con quella delle Regioni. Denominatore: residenti al 1° gennaio 2026, come
per le farmacie (Comuni dall'indicatore «Popolazione residente», Toscana e Italia dallo snapshot demografico
2026). Lo storico comunale non esiste alla fonte (lo storico PUN è solo nazionale).
"""
from __future__ import annotations

import hashlib
import json
import math
from datetime import date, datetime, timezone
from typing import Any, Callable
from urllib.parse import urlencode

SNAPSHOT = "data/source-snapshots/pun-punti-ricarica-{date}.json"
METRIC = "evPoints"
BASE = "https://services-eu1.arcgis.com/iIOeNeT2w8BczYEP/arcgis/rest/services/{layer}/FeatureServer/0"
PAGE = "https://www.piattaformaunicanazionale.it/territory-idr"
POPULATION = "data/source-snapshots/a3-istat-demography-benchmark-2026.json"
TOWNS = {"046005": "Camaiore", "046013": "Forte dei Marmi", "046018": "Massarosa", "046024": "Pietrasanta",
         "046028": "Seravezza", "046030": "Stazzema", "046033": "Viareggio"}
MONTHS = ("gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre")


class PunError(RuntimeError):
    pass


def _get(fetch: Callable[[str], bytes], url: str) -> dict[str, Any]:
    payload = json.loads(fetch(url).decode("utf-8"))
    if "error" in payload:
        raise PunError(f"{url}: {payload['error']}")
    return payload


def query(fetch: Callable[[str], bytes], layer: str, fields: str) -> list[dict[str, Any]]:
    """Tutte le righe di un livello, a pagine (il servizio restituisce al più `maxRecordCount` righe per chiamata)."""
    rows: list[dict[str, Any]] = []
    while True:
        params = {"where": "1=1", "outFields": fields, "returnGeometry": "false", "orderByFields": "FID",
                  "resultOffset": len(rows), "resultRecordCount": 1000, "f": "json"}
        page = _get(fetch, BASE.format(layer=layer) + "/query?" + urlencode(params))
        features = [f["attributes"] for f in page.get("features", [])]
        rows += features
        if not features or not page.get("exceededTransferLimit"):
            return rows


def label(day: date) -> str:
    return f"{day.day} {MONTHS[day.month - 1]} {day.year}"


def build_snapshot(fetch: Callable[[str], bytes], population: dict[str, int], tus_pop: int, ita_pop: int) -> dict[str, Any]:
    """`population`: codice Istat → residenti al 1° gennaio 2026 dei sette Comuni."""
    comuni = query(fetch, "Comuni_Italiani", "FID,COMUNE,DEN_PROV,DEN_REG,Conteggio")
    regioni = query(fetch, "Regioni_Italiane", "FID,DEN_REG,Conteggio")
    storico = query(fetch, "Installazioni_storico", "FID,Storico,Punti_di_ricarica")
    if not 7800 <= len(comuni) <= 8000 or len(regioni) != 20 or not storico:
        raise PunError(f"copertura inattesa: {len(comuni)} Comuni, {len(regioni)} Regioni, {len(storico)} date")
    if any(not isinstance(r.get("Conteggio"), int) or r["Conteggio"] < 0 for r in comuni + regioni):
        raise PunError("conteggio mancante o negativo: nessuna imputazione")
    last = max(storico, key=lambda r: r["Storico"])
    ref = datetime.fromtimestamp(last["Storico"] / 1000, tz=timezone.utc).date()
    total_c, total_r = sum(r["Conteggio"] for r in comuni), sum(r["Conteggio"] for r in regioni)
    if not total_c == total_r == last["Punti_di_ricarica"]:
        raise PunError(f"totali incoerenti: Comuni {total_c}, Regioni {total_r}, storico {last['Punti_di_ricarica']} al {ref}")
    tus = [r for r in comuni if r["DEN_REG"] == "Toscana"]
    tus_region = next(r["Conteggio"] for r in regioni if r["DEN_REG"] == "Toscana")
    if len(tus) != 273 or sum(r["Conteggio"] for r in tus) != tus_region:
        raise PunError(f"Toscana: {len(tus)} Comuni, somma ≠ conteggio regionale {tus_region}")
    towns = {}
    for code, name in TOWNS.items():
        hits = [r for r in comuni if r["COMUNE"] == name and r["DEN_PROV"] == "Lucca"]
        if len(hits) != 1:
            raise PunError(f"{name}: {len(hits)} righe")
        towns[code] = {"town": name, "points": hits[0]["Conteggio"], "population": population[code],
                       "per1000": hits[0]["Conteggio"] / population[code] * 1000}
    return {
        "schemaVersion": 1, "version": f"pun-punti-ricarica-{ref.isoformat()}-v1", "retrieved": date.today().isoformat(),
        "publisher": "GSE / MASE — Piattaforma Unica Nazionale", "page": PAGE, "referenceDate": ref.isoformat(),
        "layers": {k: BASE.format(layer=k) for k in ("Comuni_Italiani", "Regioni_Italiane", "Installazioni_storico")},
        "recordsSha256": hashlib.sha256(json.dumps(sorted((r["COMUNE"], r["DEN_PROV"], r["Conteggio"]) for r in comuni),
                                                   ensure_ascii=False).encode()).hexdigest(),
        "nationalHistory": [{"date": datetime.fromtimestamp(r["Storico"] / 1000, tz=timezone.utc).date().isoformat(), "points": r["Punti_di_ricarica"]}
                            for r in sorted(storico, key=lambda r: r["Storico"])],
        "towns": towns,
        "benchmarks": {"tuscany": {"points": tus_region, "population": tus_pop, "per1000": tus_region / tus_pop * 1000, "municipalities": 273},
                       "italy": {"points": total_c, "population": ita_pop, "per1000": total_c / ita_pop * 1000, "municipalities": len(comuni)}},
        "rule": ("Punti di ricarica per Comune del livello PUN `Comuni_Italiani`, ultima data dello storico nazionale (totali coerenti tra "
                 "Comuni, Regioni e storico); residenti al 1° gennaio 2026 come denominatore per Comuni, Toscana e Italia."),
        "qualityGate": {"status": "PASS", "note": f"Totale nazionale {total_c} = somma Regioni = storico al {ref}; Toscana 273/273."},
    }


def apply(metric: dict[str, Any], snap: dict[str, Any], path: str) -> None:
    ref = date.fromisoformat(snap["referenceDate"])
    pts = lambda x: f"{x:,}".replace(",", ".")
    dec = lambda x: f"{x:.2f}".replace(".", ",")
    for row in metric["rows"]:
        t = snap["towns"][row["code"]]
        row["value"] = row["benchmarkValue"] = t["per1000"]
        row["formatted"] = f"{dec(t['per1000'])} ogni 1.000"
        row["count"] = t["points"]
    pop = sum(t["population"] for t in snap["towns"].values())
    points = sum(t["points"] for t in snap["towns"].values())
    metric["aggregate"]["value"] = points / pop * 1000
    metric["aggregate"]["note"] = (f"{pts(points)} punti di ricarica dei sette Comuni ogni 1.000 residenti complessivi; non è la media dei sette rapporti.")
    metric["meta"]["year"] = label(ref)
    metric["sourceUrl"] = snap["page"]
    metric["method"]["formula"] = "punti di ricarica pubblici del Comune (PUN) / residenti al 1° gennaio 2026 × 1.000"
    metric["method"]["caveat"] = (f"Conteggio della Piattaforma Unica Nazionale al {label(ref)} (livello pubblico per Comune). Lo storico PUN è "
                                  "solo nazionale: una serie comunale non esiste alla fonte. Un punto di ricarica è una singola presa utilizzabile.")
    metric["meta"].setdefault("sourceMeta", {})["snapshot"] = path
    t, i = snap["benchmarks"]["tuscany"], snap["benchmarks"]["italy"]
    metric["meta"]["benchmark"] = {
        "year": label(ref), "tuscany": t["per1000"], "italy": i["per1000"], "sourceSnapshot": path,
        "source": "GSE / MASE — Piattaforma Unica Nazionale, punti di ricarica per Comune e Regione", "url": snap["page"],
        "note": (f"Stesso livello e stessa data dei valori comunali: Toscana {pts(t['points'])} punti (273/273 Comuni) e Italia "
                 f"{pts(i['points'])}, rapportati ai residenti al 1° gennaio 2026 ({pts(t['population'])} e {pts(i['population'])})."),
    }
