#!/usr/bin/env python3
"""Aggiunge in build il confronto Toscana/Italia agli indicatori di rendiconto dei Comuni.

Legge l'ultimo `data/source-snapshots/openbdap-benchmark-AAAA.json` (scritto da
`update_source_data.py openbdap-benchmarks`) e imposta `meta.benchmark` per gli
indicatori dello stesso anno. Un territorio sotto il 90% dei residenti coperti resta
vuoto. Ricontrolla prima che i valori dei sette Comuni nello snapshot coincidano
con quelli del catalogo.
"""
from __future__ import annotations

import json
import math
import re
from pathlib import Path

import openbdap_benchmarks as ob

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "site-data.json"
SOURCE = "Ragioneria generale dello Stato — OpenBDAP, rendiconti dei Comuni"


def latest_snapshot(root: Path | None = None) -> str:
    found = ((root or ROOT) / "data" / "source-snapshots").glob("openbdap-benchmark-*.json")
    years = sorted((int(m.group(1)), p.name) for p in found if (m := re.fullmatch(r"openbdap-benchmark-(20\d\d)\.json", p.name)))
    if not years:
        raise RuntimeError("Confronto bilanci: nessuno snapshot")
    return f"data/source-snapshots/{years[-1][1]}"


def share(x: float) -> str:
    return f"{x * 100:.1f}".replace(".", ",") + "%"


def count(n: int) -> str:
    return f"{n:,}".replace(",", ".")


def note(entries: dict) -> str:
    parts = []
    for scope, label in (("tuscany", "Toscana"), ("italy", "Italia")):
        e = entries[scope]
        text = f"{label}: {count(e['municipalities'])} Comuni su {count(e['municipalitiesTotal'])} ({share(e['populationShare'])} dei residenti)"
        if e.get("value") is None:
            text += ", sotto la soglia del 90%: non pubblicato"
        parts.append(text)
    return ("Aggregato sui Comuni che hanno trasmesso il rendiconto: somma degli importi diviso la popolazione degli stessi "
            "Comuni al 1° gennaio (per le quote, somma dei numeratori su somma dei denominatori). " + "; ".join(parts) + ".")


def apply(data: dict) -> int:
    path = latest_snapshot()
    snap = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if snap.get("qualityGate", {}).get("status") != "PASS":
        raise RuntimeError("Confronto bilanci: snapshot senza controllo di qualità")
    year = str(snap["year"])
    updated = 0
    for key in ob.METRICS:
        metric = data["metrics"].get(key)
        if metric is None:
            raise RuntimeError(f"Confronto bilanci: indicatore assente {key}")
        if str(metric["meta"].get("year")) != year:
            continue
        entries = snap["benchmarks"].get(key)
        if entries is None:  # indicatore aggiunto dopo l'ultima acquisizione: nessun confronto finché non è acquisito
            continue
        if all(entries[s].get("value") is None for s in ("tuscany", "italy")):
            continue
        for row in metric["rows"]:
            town = snap["towns"][row["code"]]
            n, d = town[key]
            live = n / d * 100 if key in ob.RATIOS else n / town["population"]
            if row.get("value") is None or not math.isclose(live, row["value"], rel_tol=0, abs_tol=1e-6):
                raise RuntimeError(f"Confronto bilanci: {key} {row['town']} {live} ≠ {row.get('value')}")
        metric["meta"]["benchmark"] = {
            "year": year, "tuscany": entries["tuscany"].get("value"), "italy": entries["italy"].get("value"),
            "source": SOURCE, "url": ob.PORTAL, "sourceSnapshot": path, "note": note(entries),
        }
        updated += 1
    return updated


def main() -> None:
    data = json.loads(DATA.read_text(encoding="utf-8"))
    n = apply(data)
    DATA.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Confronto bilanci: {n} indicatori con Toscana/Italia")


if __name__ == "__main__":
    main()
