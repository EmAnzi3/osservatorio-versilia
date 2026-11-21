#!/usr/bin/env python3
"""Aggiunge in build il confronto Toscana e Italia per l'addizionale comunale IRPEF.

Legge `data/source-snapshots/mef-irpef-benchmark-AAAA.json` (scritto da
`update_source_data.py mef-irpef-benchmarks`) e, se l'anno coincide e la riconciliazione 7/7 è
superata, imposta `meta.benchmark` sullo scenario predefinito (20.000 €) e `meta.benchmarkScenarios`
con i tre scenari. Un ambito sotto il 90% dei residenti coperti resta vuoto.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import irpef_benchmarks as ib

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "site-data.json"
SOURCE = "Dipartimento delle Finanze — elenco delle aliquote dell'addizionale comunale IRPEF"


def count(n: int) -> str:
    return f"{n:,}".replace(",", ".")


def pct(x: float) -> str:
    return f"{x * 100:.1f}".replace(".", ",")


def label(n: int) -> str:
    return f"{n:,.0f} €".replace(",", ".")


def apply(data: dict) -> bool:
    metric = data["metrics"].get(ib.METRIC)
    if not metric:
        return False
    year = int(metric["meta"]["year"])
    path = ROOT / ib.SNAPSHOT.format(year=year)
    if not path.exists():
        return False
    snap = json.loads(path.read_text(encoding="utf-8"))
    if snap["qualityGate"]["status"] != "PASS" or snap["blocked"] or snap["year"] != year or snap["scenarios"] != list(ib.SCENARIOS):
        return False
    for row in metric["rows"]:
        live = snap["towns"][row["code"]]["amounts"]
        for n, part in zip(ib.SCENARIOS, row["parts"]):
            if part["selectorLabel"] != label(n) or not math.isclose(live[str(n)], part["value"], rel_tol=0, abs_tol=1e-9):
                raise RuntimeError(f"Confronto addizionale IRPEF: {row['town']} {n} {live[str(n)]} ≠ {part['value']}")
    scenarios = {}
    for n in ib.SCENARIOS:
        entries = snap["benchmarks"][str(n)]
        scenarios[str(n)] = {
            "label": label(n),
            **{scope: entries[scope].get("value") for scope in ("tuscany", "italy")},
            "coverage": {scope: {k: entries[scope][k] for k in ("municipalities", "municipalitiesTotal", "populationShare")} for scope in ("tuscany", "italy")},
        }
    first = snap["benchmarks"][str(ib.SCENARIOS[0])]
    t, i = first["tuscany"], first["italy"]
    metric["meta"]["benchmark"] = {
        "year": str(year), "tuscany": t.get("value"), "italy": i.get("value"), "source": SOURCE,
        "url": ib.SOURCE_PAGE, "sourceSnapshot": ib.SNAPSHOT.format(year=year), "part": label(ib.SCENARIOS[0]),
        "note": (f"Confronto riferito allo scenario predefinito «{label(ib.SCENARIOS[0])}»: importo che pagherebbe, a parità di "
                 "reddito, il residente medio, cioè la media degli importi comunali pesata per i residenti al 1° gennaio "
                 f"{year + 1}. Toscana: {count(t['municipalities'])} Comuni su {count(t['municipalitiesTotal'])} ({pct(t['populationShare'])}% "
                 f"dei residenti); Italia: {count(i['municipalities'])} su {count(i['municipalitiesTotal'])} ({pct(i['populationShare'])}%). "
                 "Esclusi i Comuni con regole non leggibili senza ambiguità, per esempio esenzioni riservate a certe categorie di reddito. "
                 "La media Versilia resta la media semplice dei sette Comuni."),
    }
    metric["meta"]["benchmarkScenarios"] = scenarios
    return True


def main() -> None:
    data = json.loads(DATA.read_text(encoding="utf-8"))
    done = apply(data)
    DATA.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Confronto addizionale IRPEF: " + ("Toscana e Italia applicate" if done else "snapshot assente o non valido, nessun confronto"))


if __name__ == "__main__":
    main()
