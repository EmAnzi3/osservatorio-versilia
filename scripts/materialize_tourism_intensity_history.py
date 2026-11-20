#!/usr/bin/env python3
"""Aggiunge in build la serie 2023–2025 dell'intensità turistica (presenze per residente).

Stessa regola del valore pubblicato (presenze 2025 / residenti al 1° gennaio 2026): presenze
dell'anno A dalla storia del movimento comunale già congelata (Regione Toscana, al netto delle
locazioni) e residenti POSAS al 1° gennaio A+1 dallo snapshot demografico. Nessuna nuova
acquisizione; l'ultimo anno deve coincidere con il valore pubblicato.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "site-data.json"
TOURISM = "data/source-snapshots/a3-regione-toscana-tourism-benchmark-2025.json"
POSAS = "data/source-snapshots/istat-demography-lotto-a-2026-08.json"
METRIC = "tourismIntensity"


def series(data: dict, tourism: dict, posas: dict) -> dict[str, dict]:
    history = tourism["municipalMovementHistory"]
    if tourism["qualityGate"]["status"] != "PASS" or history["scope"] != "al netto delle locazioni" or history["years"] != [2023, 2024, 2025]:
        raise RuntimeError("Intensità turistica: storia del movimento non valida")
    out = {}
    for row in data["metrics"][METRIC]["rows"]:
        records = {int(r["year"]): r["population"] for r in posas["posas"]["towns"][row["town"]]}
        values = []
        for year in history["years"]:
            presences = history["countsByYear"][str(year)][row["code"]]["presences"]
            residents = records.get(year + 1)
            if not isinstance(residents, int) or residents <= 0:
                raise RuntimeError(f"Intensità turistica: residenti {row['town']} 1.1.{year + 1} assenti")
            values.append(presences / residents)
        if not math.isclose(values[-1], row["value"], rel_tol=0, abs_tol=1e-12):
            raise RuntimeError(f"Intensità turistica {row['town']}: {values[-1]} ≠ {row['value']}")
        out[row["code"]] = {"years": list(history["years"]), "values": values}
    return out


def main() -> None:
    data = json.loads(DATA.read_text(encoding="utf-8"))
    tourism = json.loads((ROOT / TOURISM).read_text(encoding="utf-8"))
    posas = json.loads((ROOT / POSAS).read_text(encoding="utf-8"))
    metric = data["metrics"][METRIC]
    if str(metric["meta"]["year"]) != "2025":
        print("Intensità turistica: anno pubblicato diverso dal 2025, serie non applicata")
        return
    computed = series(data, tourism, posas)
    for row in metric["rows"]:
        row["series"] = computed[row["code"]]
    metric["meta"].setdefault("sourceMeta", {})["historySnapshot"] = TOURISM
    note = " Serie 2023–2025: presenze dell'anno sui residenti al 1° gennaio dell'anno dopo, come il valore pubblicato."
    if note.strip() not in metric["method"].get("caveat", ""):
        metric["method"]["caveat"] = (metric["method"].get("caveat", "").rstrip() + note).strip()
    DATA.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Intensità turistica: serie 2023–2025 materializzata")


if __name__ == "__main__":
    main()
