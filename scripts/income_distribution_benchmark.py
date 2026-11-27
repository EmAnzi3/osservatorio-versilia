#!/usr/bin/env python3
"""Confronto Toscana/Italia della distribuzione dei dichiaranti per fascia di reddito (MEF).

Stesso file e stessa regola del valore comunale pubblicato: dal file comunale MEF «Redditi e
principali variabili IRPEF su base comunale» dell'anno d'imposta si sommano, sui Comuni del
territorio, le frequenze delle otto classi di reddito complessivo nelle quattro fasce pubblicate.
Entrano solo i Comuni in cui il MEF oscura al più le due classi estreme (come nei valori comunali);
la copertura è la quota dei contribuenti del territorio che vivono in quei Comuni ed è dichiarata;
il territorio è pubblicato solo con almeno il 90%. I sette Comuni ricalcolati devono coincidere con
le quote pubblicate.
"""
from __future__ import annotations

import csv
import hashlib
import io
import math
from datetime import date
from typing import Any, Callable

import income_distribution_history as idh
import taxpayers_history as th

SNAPSHOT = "data/source-snapshots/mef-fasce-reddito-benchmark-{year}.json"
METRIC = idh.METRIC
MIN_COVERAGE = 0.90
TUSCANY = ("045", "046", "047", "048", "049", "050", "051", "052", "053", "100")


class DistributionBenchmarkError(RuntimeError):
    pass


def build_snapshot(raw: bytes, url: str, year: int, published: dict[str, list[float]]) -> dict[str, Any]:
    member, text = th._member(raw, f"MEF {year}")
    reader = csv.reader(io.StringIO(text), delimiter=";")
    header = [idh._norm(c) for c in next(reader)]
    def col(name: str) -> int:
        hits = [i for i, c in enumerate(header) if c == name]
        if len(hits) != 1:
            raise DistributionBenchmarkError(f"colonna {name!r} non univoca")
        return hits[0]
    code_i, taxpayers_i = col("codice istat comune"), col("numero contribuenti")
    cols = {}
    for key, variants in idh.CLASSES:
        hits = [i for i, c in enumerate(header) if any(c == f"reddito complessivo {v} - frequenza" for v in variants)]
        if len(hits) != 1:
            raise DistributionBenchmarkError(f"classe {key} non univoca")
        cols[key] = hits[0]
    scopes = {"tuscany": {"counts": [0] * len(idh.CLASSES), "covered": 0, "total": 0, "n": 0, "nTotal": 0},
              "italy": {"counts": [0] * len(idh.CLASSES), "covered": 0, "total": 0, "n": 0, "nTotal": 0}}
    towns: dict[str, list[float]] = {}
    for row in reader:
        if len(row) <= max(max(cols.values()), code_i, taxpayers_i):
            continue
        code = row[code_i].strip().zfill(6)
        counts = [None if row[cols[k]].strip() == "" else th._int(row[cols[k]], f"{code} {k}") for k, _ in idh.CLASSES]
        taxpayers = th._int(row[taxpayers_i], f"{code} contribuenti")
        masked = {k for (k, _), v in zip(idh.CLASSES, counts) if v is None}
        usable = masked <= idh.MASKABLE
        if code in idh.TOWNS and usable:
            total = sum(v for v in counts if v is not None)
            towns[code] = [sum(counts[i] or 0 for i, (k, _) in enumerate(idh.CLASSES) if k in group) / total * 100 for group in idh.GROUPS]
        for scope in (["italy"] + (["tuscany"] if code.startswith(TUSCANY) else [])):
            s = scopes[scope]
            s["total"] += taxpayers
            s["nTotal"] += 1
            if usable:
                s["covered"] += taxpayers
                s["n"] += 1
                s["counts"] = [a + (b or 0) for a, b in zip(s["counts"], counts)]
    for code, shares in published.items():
        live = towns.get(code)
        if live is None or any(not math.isclose(a, b, rel_tol=0, abs_tol=1e-9) for a, b in zip(live, shares)):
            raise DistributionBenchmarkError(f"{code}: fonte {live} ≠ pubblicato {shares}")
    benchmarks = {}
    for scope, s in scopes.items():
        share = s["covered"] / s["total"]
        entry = {"municipalities": s["n"], "municipalitiesTotal": s["nTotal"], "taxpayersCovered": s["covered"],
                 "taxpayersTotal": s["total"], "coverageShare": share}
        if share >= MIN_COVERAGE:
            total = sum(s["counts"])
            entry["shares"] = [sum(s["counts"][i] for i, (k, _) in enumerate(idh.CLASSES) if k in group) / total * 100 for group in idh.GROUPS]
            entry["classCounts"] = dict(zip([k for k, _ in idh.CLASSES], s["counts"]))
        else:
            entry["shares"] = None
            entry["reason"] = f"copertura {share:.1%} sotto la soglia del 90%"
        benchmarks[scope] = entry
    return {
        "schemaVersion": 1, "version": f"mef-fasce-reddito-benchmark-{year}-v1", "retrieved": date.today().isoformat(),
        "publisher": "Dipartimento delle Finanze — MEF", "year": year, "source": {"url": url, "member": member, "sha256": hashlib.sha256(raw).hexdigest()},
        "rule": ("Somma delle frequenze delle otto classi sui Comuni del territorio con al più le classi estreme oscurate, nelle quattro fasce "
                 "pubblicate; copertura = quota dei contribuenti del territorio in quei Comuni; pubblicato con almeno il 90%."),
        "benchmarks": benchmarks,
        "qualityGate": {"status": "PASS", "note": f"Quote {year} dei 7 Comuni ricalcolate identiche alle pubblicate."},
    }


def apply(metric: dict[str, Any], snap: dict[str, Any], path: str) -> None:
    year = int(metric["meta"]["year"])
    if snap["year"] != year or snap["qualityGate"]["status"] != "PASS":
        raise DistributionBenchmarkError("confronto non allineato all'anno pubblicato")
    t, i = snap["benchmarks"]["tuscany"], snap["benchmarks"]["italy"]
    pct = lambda x: f"{x * 100:.1f}".replace(".", ",")
    count = lambda n: f"{n:,}".replace(",", ".")
    label = metric["rows"][0]["parts"][0]["label"]
    metric["meta"]["benchmark"] = {
        "year": str(year), "tuscany": t["shares"][0] if t["shares"] else None, "italy": i["shares"][0] if i["shares"] else None,
        "source": "Dipartimento delle Finanze — MEF, Redditi e principali variabili IRPEF su base comunale", "url": snap["source"]["url"],
        "sourceSnapshot": path, "part": label,
        "parts": {"tuscany": t["shares"], "italy": i["shares"]},
        "note": (f"Confronto riferito alla quota «{label}». Somma dei dichiaranti dei Comuni del territorio per classe di reddito: "
                 f"Toscana {count(t['municipalities'])} Comuni su {count(t['municipalitiesTotal'])} ({pct(t['coverageShare'])}% dei contribuenti), "
                 f"Italia {count(i['municipalities'])} su {count(i['municipalitiesTotal'])} ({pct(i['coverageShare'])}%). Esclusi i Comuni in cui il "
                 "MEF oscura per riservatezza una classe intermedia. Anche la quota Versilia è calcolata sul totale dei dichiaranti dei sette Comuni."),
    }
