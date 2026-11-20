#!/usr/bin/env python3
"""Aggiunge in build il confronto Toscana per incassi e saldo di cassa SIOPE per residente.

Legge `data/source-snapshots/siope-cash-benchmark-AAAA.json` (scritto da
`update_source_data.py siope-cash-benchmarks`) e imposta `meta.benchmark` se l'anno coincide e
la riconciliazione 7/7 è superata; l'Italia resta vuota, con il motivo nella nota.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import siope_cash_benchmarks as cb

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "site-data.json"
SOURCE = "Ragioneria Generale dello Stato — OpenBDAP/SIOPE, flussi regionali dei Comuni"


def count(n: int) -> str:
    return f"{n:,}".replace(",", ".")


def apply(data: dict) -> int:
    updated = 0
    for key in cb.METRICS:
        metric = data["metrics"][key]
        year = int(metric["meta"]["year"])
        path = ROOT / cb.SNAPSHOT.format(year=year)
        if not path.exists():
            continue
        snap = json.loads(path.read_text(encoding="utf-8"))
        entry = snap["benchmarks"][key]["tuscany"]
        if snap["qualityGate"]["status"] != "PASS" or entry.get("value") is None:
            continue
        for row in metric["rows"]:
            t = snap["towns"][row["code"]]
            live = (t["receipts"] if key == "cashReceiptsPerResident" else t["receipts"] - t["payments"]) / t["residents"]
            if not math.isclose(live, row["value"], rel_tol=0, abs_tol=1e-6):
                raise RuntimeError(f"Confronto cassa: {key} {row['town']} {live} ≠ {row['value']}")
        share = f"{entry['populationShare'] * 100:.1f}".replace(".", ",")
        metric["meta"]["benchmark"] = {
            "year": str(year), "tuscany": entry["value"], "italy": None, "source": SOURCE,
            "url": "https://bdap-opendata.rgs.mef.gov.it/", "sourceSnapshot": cb.SNAPSHOT.format(year=year),
            "note": (f"Toscana: {count(entry['municipalities'])} Comuni su {count(entry['municipalitiesTotal'])} presenti in entrambi i flussi "
                     f"SIOPE di dicembre ({share}% dei residenti); somma degli importi / residenti al 1° gennaio {year + 1}. "
                     "Italia non calcolata: il flusso SIOPE è pubblicato per regione."),
        }
        updated += 1
    return updated


def main() -> None:
    data = json.loads(DATA.read_text(encoding="utf-8"))
    n = apply(data)
    DATA.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Confronto cassa SIOPE: {n} indicatori con la Toscana")


if __name__ == "__main__":
    main()
