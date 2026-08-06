#!/usr/bin/env python3
from __future__ import annotations

import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = json.loads((ROOT / "data" / "site-data.json").read_text(encoding="utf-8"))
SNAPSHOT = json.loads((ROOT / "data" / "source-snapshots" / "siope-history-v1.6.0.json").read_text(encoding="utf-8"))
YEARS = range(2019, 2026)
TOWNS = ["Camaiore", "Forte dei Marmi", "Massarosa", "Pietrasanta", "Seravezza", "Stazzema", "Viareggio"]
KEYS = ["siopePayments", "currentPayments", "capitalPayments", "cashReceiptsPerResident", "cashBalancePerResident"]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def close(actual: float, expected: float, message: str) -> None:
    if not math.isclose(float(actual), float(expected), rel_tol=1e-10, abs_tol=1e-7):
        raise AssertionError(f"{message}: {actual} != {expected}")


def expected(key: str, town: str, year: int) -> float:
    item = SNAPSHOT["raw"][town][str(year)]
    numerator = {
        "siopePayments": item["cash_payments"],
        "currentPayments": item["current_payments"],
        "capitalPayments": item["capital_payments"],
        "cashReceiptsPerResident": item["cash_receipts"],
        "cashBalancePerResident": item["cash_balance"],
    }[key]
    return numerator / item["population_resident"]


def main() -> None:
    require(list(SNAPSHOT["selection_rules"]["years"]) == list(YEARS), "Intervallo SIOPE inatteso")
    require(SNAPSHOT["selection_rules"]["entity_type_bdap"] == "CO", "Filtro Comuni SIOPE assente")
    require(SNAPSHOT["selection_rules"]["no_estimates"] is True, "Divieto di stima SIOPE non dichiarato")
    require(SNAPSHOT["coverage"].startswith("7/7"), "Copertura SIOPE incompleta")
    require(set(SNAPSHOT["raw"]) == set(TOWNS), "Comuni SIOPE incompleti")
    require(set(SNAPSHOT["metrics"]) == set(KEYS), "Indicatori SIOPE inattesi")
    require(len(SNAPSHOT["source"]["resources"]) == 14, "Risorse SIOPE 2019–2025 incomplete")
    for source in SNAPSHOT["source"]["resources"].values():
        require(len(source["sha256"]) == 64, "Hash SIOPE assente")
        require(source["bytes"] > 1000, "Risorsa SIOPE vuota")
        require(source["url"].startswith("https://bdap-opendata.rgs.mef.gov.it/"), "URL SIOPE non ufficiale")

    for town in TOWNS:
        require(sorted(map(int, SNAPSHOT["raw"][town])) == list(YEARS), f"Annualità SIOPE incomplete: {town}")
        for year in YEARS:
            item = SNAPSHOT["raw"][town][str(year)]
            require(item["population_resident"] > 0, f"Popolazione SIOPE assente: {town} {year}")
            close(item["cash_balance"], item["cash_receipts"] - item["cash_payments"], f"Saldo SIOPE errato: {town} {year}")
            require(item["selected_rows"]["entrata"] > 0 and item["selected_rows"]["spesa"] > 0, f"Righe SIOPE assenti: {town} {year}")

    for key in KEYS:
        metric_snapshot = SNAPSHOT["metrics"][key]
        require(list(metric_snapshot["years"]) == list(YEARS), f"Anni errati per {key}")
        require(metric_snapshot["coverage"] == "7/7", f"Copertura errata per {key}")
        rows = {row["town"]: row for row in DATA["metrics"][key]["rows"]}
        require(set(rows) == set(TOWNS), f"Righe sito incomplete per {key}")
        require(str(DATA["metrics"][key]["method"]["coverage"]).startswith("7/7"), f"Copertura sito assente per {key}")
        for town in TOWNS:
            series = rows[town]["series"]
            require(list(series["years"]) == list(YEARS), f"Serie anni errata: {key}/{town}")
            require(len(series["values"]) == len(YEARS), f"Serie valori incompleta: {key}/{town}")
            for year, value in zip(YEARS, series["values"], strict=True):
                close(value, expected(key, town, year), f"Serie SIOPE errata: {key}/{town}/{year}")
            close(rows[town]["value"], expected(key, town, 2025), f"Valore corrente SIOPE errato: {key}/{town}")
            close(metric_snapshot["values"][town]["2025"], rows[town]["value"], f"Validazione 2025 incoerente: {key}/{town}")

    print("Tutti i controlli delle serie SIOPE 2018–2025 sono superati.")


if __name__ == "__main__":
    main()
