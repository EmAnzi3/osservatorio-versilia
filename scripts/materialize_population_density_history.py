#!/usr/bin/env python3
"""Aggiunge in build la serie della densità abitativa (residenti per km²).

Stessa regola del valore pubblicato (residenti al 1° gennaio 2026 / superficie Istat al 31
dicembre 2021): per ogni anno della serie già pubblicata dei residenti al 1° gennaio, gli stessi
residenti divisi per la stessa superficie 2021. Nessuna nuova acquisizione. La superficie resta
quella del 2021 perché i confini dei sette Comuni non sono cambiati nel periodo; l'ultimo anno
deve coincidere con il valore pubblicato.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "site-data.json"
METRIC = "populationDensity"
POPULATION = "population"


def series(metrics: dict) -> dict[str, dict]:
    density = metrics[METRIC]
    if str(density["meta"].get("year")) != "2026" or str(metrics[POPULATION]["meta"].get("year")) != "2026":
        raise RuntimeError("Densità: anno pubblicato diverso dal 2026")
    population = {r["code"]: r for r in metrics[POPULATION]["rows"]}
    out = {}
    for row in density["rows"]:
        pop = population[row["code"]]
        history = pop.get("series")
        area = row.get("surfaceKm2")
        if not isinstance(history, dict) or not history.get("years") or len(history["years"]) != len(history["values"]):
            raise RuntimeError(f"Densità {row['town']}: serie dei residenti assente")
        if not isinstance(area, (int, float)) or area <= 0:
            raise RuntimeError(f"Densità {row['town']}: superficie non valida")
        years = [int(y) for y in history["years"]]
        if years != list(range(years[0], years[-1] + 1)) or years[-1] != 2026 or history["values"][-1] != pop["value"]:
            raise RuntimeError(f"Densità {row['town']}: serie dei residenti non coerente con il valore 2026")
        if float(row["populationBase"]) != float(pop["value"]):
            raise RuntimeError(f"Densità {row['town']}: residenti {row['populationBase']} ≠ {pop['value']}")
        values = [v / area for v in history["values"]]
        if not math.isclose(values[-1], row["value"], rel_tol=0, abs_tol=1e-9):
            raise RuntimeError(f"Densità {row['town']}: {values[-1]} ≠ {row['value']}")
        out[row["code"]] = {"years": years, "values": values}
    return out


def main() -> None:
    data = json.loads(DATA.read_text(encoding="utf-8"))
    metrics = data["metrics"]
    if METRIC not in metrics:
        print("Densità: metrica assente, serie non applicata")
        return
    computed = series(metrics)
    metric = metrics[METRIC]
    for row in metric["rows"]:
        row["series"] = computed[row["code"]]
    years = next(iter(computed.values()))["years"]
    note = (f" Serie {years[0]}–{years[-1]}: residenti al 1° gennaio di ogni anno sulla stessa superficie del 2021"
            " (confini invariati nel periodo).")
    if note.strip() not in metric["method"].get("caveat", ""):
        metric["method"]["caveat"] = (metric["method"].get("caveat", "").rstrip() + note).strip()
    DATA.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Densità: serie {years[0]}–{years[-1]} materializzata")


if __name__ == "__main__":
    main()
