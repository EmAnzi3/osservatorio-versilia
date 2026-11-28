#!/usr/bin/env python3
"""Confronto Toscana/Italia dei prezzi carburanti self-service (MIMIT, stessa estrazione dei valori comunali).

Stessa regola del valore comunale (`update_fuel_prices_mimit.py`): impianti attivi dell'anagrafica, prezzi
self-service di Benzina e Gasolio tra 0,5 e 5 €/l, un solo prezzo per impianto e carburante (il primo
dell'export). Il valore del territorio è la mediana dei prezzi degli impianti del territorio, come quello di
ciascun Comune. I due file (anagrafica e prezzi) devono essere della stessa estrazione e i sette Comuni
ricalcolati devono coincidere con i valori pubblicati.
"""
from __future__ import annotations

import hashlib
import statistics
from datetime import date
from typing import Any

import audit_fuel_prices_mimit as audit

SNAPSHOT = "data/source-snapshots/mimit-carburanti-benchmark-{year}.json"
METRIC = "fuelPrices"
TUSCANY = {"AR", "FI", "GR", "LI", "LU", "MS", "PI", "PO", "PT", "SI"}


class FuelBenchmarkError(RuntimeError):
    pass


def station_prices(anag_text: str, prices_text: str) -> tuple[str, dict[str, dict[str, Any]], dict[tuple[str, str], float]]:
    anag_date, anag = audit.parse_export(anag_text)
    price_date, prices = audit.parse_export(prices_text)
    if not anag or not prices:
        raise FuelBenchmarkError("dataset MIMIT vuoto")
    if anag_date != price_date:
        raise FuelBenchmarkError(f"estrazioni diverse: anagrafica {anag_date}, prezzi {price_date}")
    aid, atown, aprov = (audit.find_field(anag[0], n) for n in ("idimpianto", "Comune", "Provincia"))
    pid, pfuel, pprice, pself = (audit.find_field(prices[0], n) for n in ("idimpianto", "descCarburante", "prezzo", "isSelf"))
    stations = {str(r.get(aid, "")).strip(): {"town": audit.norm(r.get(atown, "")), "province": str(r.get(aprov, "")).strip().upper()}
                for r in anag}
    values: dict[tuple[str, str], float] = {}
    for row in prices:
        station = str(row.get(pid, "")).strip()
        if station not in stations or str(row.get(pself, "")).strip() not in {"1", "1.0"}:
            continue
        fuel = audit.norm(row.get(pfuel, ""))
        if fuel not in audit.FUELS:
            continue
        try:
            price = float(str(row.get(pprice, "")).strip().replace(",", "."))
        except ValueError:
            continue
        if not 0.5 <= price <= 5:
            continue
        values.setdefault((station, fuel), price)  # come nei valori comunali: vale il primo prezzo dell'impianto
    return price_date, stations, values


def build_snapshot(anag: bytes, prices: bytes, published: dict[str, dict[str, float | None]], year: str) -> dict[str, Any]:
    """`published`: Comune → {benzina, gasolio} pubblicati per l'estrazione `year` (AAAA-MM-GG)."""
    ref, stations, values = station_prices(anag.decode("utf-8-sig", errors="replace"), prices.decode("utf-8-sig", errors="replace"))
    if ref != year:
        raise FuelBenchmarkError(f"estrazione {ref} diversa dalla pubblicata {year}")
    wanted = {audit.norm(t): t for t in audit.TOWNS}
    towns = {t: {f: [] for f in audit.FUELS} for t in audit.TOWNS}
    scopes = {s: {f: [] for f in audit.FUELS} for s in ("tuscany", "italy")}
    for (station, fuel), price in values.items():
        info = stations[station]
        scopes["italy"][fuel].append(price)
        if info["province"] in TUSCANY:
            scopes["tuscany"][fuel].append(price)
        town = wanted.get(info["town"])
        if town and info["province"] == "LU":
            towns[town][fuel].append(price)
    for town, pub in published.items():
        for fuel in audit.FUELS:
            live = round(statistics.median(towns[town][fuel]), 3) if towns[town][fuel] else None
            if live != pub.get(fuel):
                raise FuelBenchmarkError(f"{town} {fuel}: fonte {live} ≠ pubblicato {pub.get(fuel)}")
    bench = {s: {f: {"median": statistics.median(v), "stations": len(v)} for f, v in by_fuel.items()} for s, by_fuel in scopes.items()}
    if not 1000 <= bench["tuscany"]["benzina"]["stations"] <= 2000 or bench["italy"]["benzina"]["stations"] < 15000:
        raise FuelBenchmarkError(f"copertura inattesa: {bench}")
    return {
        "schemaVersion": 1, "version": f"mimit-carburanti-benchmark-{year}-v1", "retrieved": date.today().isoformat(), "year": year,
        "publisher": "MIMIT — Osservaprezzi carburanti", "sources": {
            "anagrafica": {"url": audit.ANAG, "sha256": hashlib.sha256(anag).hexdigest(), "bytes": len(anag)},
            "prezzi": {"url": audit.PRICES, "sha256": hashlib.sha256(prices).hexdigest(), "bytes": len(prices)}},
        "rule": ("Mediana dei prezzi self-service degli impianti attivi del territorio (Toscana: province AR, FI, GR, LI, LU, MS, PI, PO, "
                 "PT, SI; Italia: tutti), stessi filtri e stessa estrazione dei valori comunali."),
        "benchmarks": bench,
        "qualityGate": {"status": "PASS", "note": f"Mediane {year} dei sette Comuni ricalcolate identiche alle pubblicate."},
    }


def apply(metric: dict[str, Any], snap: dict[str, Any], path: str) -> None:
    if str(metric["meta"]["year"]) != snap["year"]:
        raise FuelBenchmarkError("confronto non allineato all'estrazione pubblicata")
    t, i = snap["benchmarks"]["tuscany"], snap["benchmarks"]["italy"]
    n = lambda x: f"{x:,}".replace(",", ".")
    c3 = lambda x: f"{x:.3f}".replace(".", ",")
    label = metric["rows"][0]["parts"][0]["label"]
    metric["meta"]["benchmark"] = {
        "year": snap["year"], "tuscany": t["benzina"]["median"], "italy": i["benzina"]["median"],
        "source": "MIMIT — Osservaprezzi carburanti, prezzi praticati e anagrafica impianti", "url": snap["sources"]["prezzi"]["url"],
        "sourceSnapshot": path, "part": label,
        "parts": {"tuscany": [t["benzina"]["median"], t["gasolio"]["median"]], "italy": [i["benzina"]["median"], i["gasolio"]["median"]]},
        "note": (f"Confronto riferito alla «{label}»: mediana dei prezzi self-service degli impianti attivi, come il valore di ciascun Comune "
                 f"(Toscana {n(t['benzina']['stations'])} impianti, Italia {n(i['benzina']['stations'])}), stessa estrazione del {snap['year']}. "
                 f"Gasolio self: Toscana {c3(t['gasolio']['median'])} €/l, Italia {c3(i['gasolio']['median'])} €/l. Il valore Versilia è la "
                 "media delle mediane comunali."),
    }
