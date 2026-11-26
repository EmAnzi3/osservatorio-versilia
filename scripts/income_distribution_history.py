#!/usr/bin/env python3
"""Serie storica della distribuzione dei dichiaranti per fascia di reddito nei sette Comuni.

Stessa regola del valore pubblicato: dal file comunale MEF «Redditi e principali variabili IRPEF su
base comunale» dell'anno d'imposta A si prendono le frequenze delle otto classi di reddito complessivo
e si sommano nelle quattro fasce pubblicate (fino a 15.000 €, 15.000–26.000 €, 26.000–55.000 €, oltre
55.000 €); il denominatore è il totale dei dichiaranti presenti nelle classi valorizzate.

Il MEF oscura alcune celle per riservatezza. Come nel valore pubblicato, possono mancare soltanto le
due classi estreme («fino a 0 €» e «oltre 120.000 €»): se in un anno manca un'altra classe, la
distribuzione di quel Comune per quell'anno resta n.d. Le classi oscurate sono registrate nello
snapshot Comune per Comune. Si usano solo anni consecutivi che terminano con l'anno pubblicato;
l'ultimo anno deve coincidere con le quote pubblicate.
"""
from __future__ import annotations

import csv
import hashlib
import io
import math
import re
from datetime import date
from typing import Any, Callable

import taxpayers_history as th

SNAPSHOT = "data/source-snapshots/mef-fasce-reddito-serie.json"
METRIC = "incomeDistribution"
FIRST = 2012
TOWNS = th.TOWNS
CLASSES = (  # chiave, intestazione MEF (dopo «reddito complessivo »), varianti di scrittura ammesse
    ("le0", ("minore o uguale a zero euro", "minore di zero euro")),
    ("0to10k", ("da 0 a 10000 euro",)),
    ("10to15k", ("da 10000 a 15000 euro",)),
    ("15to26k", ("da 15000 a 26000 euro",)),
    ("26to55k", ("da 26000 a 55000 euro",)),
    ("55to75k", ("da 55000 a 75000 euro",)),
    ("75to120k", ("da 75000 a 120000 euro",)),
    ("over120k", ("oltre 120000 euro",)),
)
GROUPS = (("le0", "0to10k", "10to15k"), ("15to26k",), ("26to55k",), ("55to75k", "75to120k", "over120k"))
MASKABLE = {"le0", "over120k"}


class IncomeDistributionError(RuntimeError):
    pass


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "").strip().lower())


def read_year(raw: bytes, year: int) -> dict[str, Any]:
    member, text = th._member(raw, f"MEF {year}")
    reader = csv.reader(io.StringIO(text), delimiter=";")
    header = [_norm(c) for c in next(reader)]
    codes = [i for i, c in enumerate(header) if c == "codice istat comune"]
    if len(codes) != 1:
        raise IncomeDistributionError(f"{year}: colonna Codice Istat Comune non trovata")
    columns = {}
    for key, variants in CLASSES:
        found = [i for i, c in enumerate(header)
                 if any(c == f"reddito complessivo {v} - frequenza" for v in variants)]
        if len(found) != 1:
            raise IncomeDistributionError(f"{year}: classe {key} non trovata in modo univoco")
        columns[key] = found[0]
    towns: dict[str, Any] = {}
    for row in reader:
        if len(row) <= max(columns.values()):
            continue
        code = row[codes[0]].strip().zfill(6)
        if code not in TOWNS:
            continue
        if code in towns:
            raise IncomeDistributionError(f"{year} {TOWNS[code]}: righe duplicate")
        counts = {}
        for key, index in columns.items():
            cell = row[index].strip()
            counts[key] = None if cell == "" else th._int(cell, f"{year} {TOWNS[code]} {key}")
        masked = [k for k, v in counts.items() if v is None]
        entry: dict[str, Any] = {"counts": counts, "masked": masked}
        if set(masked) - MASKABLE:
            entry["shares"] = None
            entry["note"] = "classe intermedia oscurata dal MEF: distribuzione non confrontabile"
        else:
            total = sum(v for v in counts.values() if v is not None)
            if not total:
                raise IncomeDistributionError(f"{year} {TOWNS[code]}: nessun dichiarante nelle classi")
            entry["total"] = total
            entry["shares"] = [sum(counts[k] or 0 for k in group) / total * 100 for group in GROUPS]
        towns[code] = entry
    if set(towns) != set(TOWNS):
        raise IncomeDistributionError(f"{year}: Comuni assenti {sorted(set(TOWNS) - set(towns))}")
    return {"member": member, "towns": towns}


def build_snapshot(fetcher: Callable[[str], bytes], published: dict[str, list[float]], last: int) -> dict[str, Any]:
    """`published`: codice Istat → quote pubblicate delle quattro fasce per l'anno `last`."""
    years: dict[int, dict[str, Any]] = {}
    stop = None
    for year in range(last, FIRST - 1, -1):
        url = th.MEF_URL.format(year=year)
        try:
            raw = fetcher(url)
            parsed = read_year(raw, year)
        except (th.Unavailable, IncomeDistributionError, th.TaxpayersError) as why:
            if year == last:
                raise IncomeDistributionError(f"anno corrente {year}: {why}") from why
            stop = f"{year}: {why}"
            break
        years[year] = {"url": url, "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw), **parsed}
    for code, shares in published.items():
        live = years[last]["towns"][code]["shares"]
        if live is None or any(not math.isclose(a, b, rel_tol=0, abs_tol=1e-9) for a, b in zip(live, shares)):
            raise IncomeDistributionError(f"{code} {last}: fonte {live} ≠ pubblicato {shares}")
    ordered = sorted(years)
    if len(ordered) < 2:
        raise IncomeDistributionError(f"serie di un solo anno ({stop})")
    series = {code: [[None if years[y]["towns"][code]["shares"] is None else years[y]["towns"][code]["shares"][g]
                      for y in ordered] for g in range(len(GROUPS))] for code in TOWNS}
    return {
        "schemaVersion": 1, "version": f"mef-fasce-reddito-serie-{ordered[0]}-{last}-v1", "retrieved": date.today().isoformat(),
        "publisher": "Dipartimento delle Finanze — MEF", "dataset": "Redditi e principali variabili IRPEF su base comunale",
        "years": ordered, "groups": [list(g) for g in GROUPS],
        "rule": ("Frequenze delle otto classi MEF di reddito complessivo dell'anno d'imposta A sommate nelle quattro fasce pubblicate; "
                 "denominatore = dichiaranti nelle classi valorizzate. Possono mancare solo le classi estreme (≤ 0 € e oltre 120.000 €); "
                 "con un'altra classe oscurata la distribuzione del Comune per quell'anno resta n.d."),
        "stoppedAt": stop,
        "sources": {str(y): {"url": d["url"], "sha256": d["sha256"], "bytes": d["bytes"], "member": d["member"]} for y, d in years.items()},
        "towns": {code: {str(y): years[y]["towns"][code] for y in ordered} for code in TOWNS},
        "series": series,
        "qualityGate": {"status": "PASS", "note": f"Anno {last} identico alle quote pubblicate per i 7 Comuni nelle quattro fasce."},
    }


def apply(metrics: dict[str, dict[str, Any]], snapshot: dict[str, Any], path: str) -> None:
    metric = metrics[METRIC]
    years = snapshot["years"]
    if str(years[-1]) != str(metric["meta"]["year"]) or len(snapshot["groups"]) != len(GROUPS):
        raise IncomeDistributionError("serie non allineata al valore pubblicato")
    for row in metric["rows"]:
        series = snapshot["series"][row["code"]]
        if len(row["parts"]) != len(GROUPS):
            raise IncomeDistributionError(f"{row['town']}: fasce pubblicate inattese")
        for values, part in zip(series, row["parts"]):
            if not math.isclose(values[-1], part["value"], rel_tol=0, abs_tol=1e-9):
                raise IncomeDistributionError(f"{row['town']} {part['label']}: serie {values[-1]} ≠ valore {part['value']}")
        # gli anni n.d. (classe intermedia oscurata) si omettono: le serie pubblicate non contengono valori nulli
        row["componentSeries"] = {f"part-{g}": {"years": [y for y, v in zip(years, values) if v is not None],
                                                "values": [v for v in values if v is not None]} for g, values in enumerate(series)}
        row["series"] = dict(row["componentSeries"]["part-0"])
    metric["meta"].setdefault("sourceMeta", {})["historySnapshot"] = path
    masked = sorted({f"{TOWNS[c]} {y}" for c, t in snapshot["towns"].items() for y, d in t.items() if d["shares"] is None})
    note = (f"Serie {years[0]}–{years[-1]} dai file comunali MEF di ciascun anno, con le stesse classi e la stessa regola; "
            "le fasce sono in euro correnti, quindi risentono anche dell'inflazione.")
    if masked:
        note += " Restano n.d. gli anni in cui il MEF oscura una classe intermedia: " + ", ".join(masked) + "."
    metric["method"]["historyNote"] = note
