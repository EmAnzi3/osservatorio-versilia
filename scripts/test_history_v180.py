#!/usr/bin/env python3
"""Controlli del primo lotto storico comunale Istat della v1.8."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = json.loads((ROOT / "data" / "site-data.json").read_text(encoding="utf-8"))
SNAPSHOT = json.loads(
    (ROOT / "data" / "source-snapshots" / "istat-sections-history-v1.8.0.json")
    .read_text(encoding="utf-8")
)

EXPECTED = {
    "femaleEmploymentRate": lambda row: 100 * row["P103"] / row["female1564"],
    "maleEmploymentRate": lambda row: 100 * row["P102"] / row["male1564"],
    "employmentGenderGap": lambda row: (
        100 * row["P102"] / row["male1564"]
        - 100 * row["P103"] / row["female1564"]
    ),
    "housingStockPer1000": lambda row: 1000 * row["A8"] / row["P1"],
    "nonOccupiedHomesPer1000": lambda row: 1000 * row["A3"] / row["P1"],
    "vacantHomes": lambda row: 100 * row["A3"] / row["A8"],
    "singleHouseholds": lambda row: 100 * row["PF3"] / row["PF1"],
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    # Questo è un test di retrocompatibilità del lotto storico v1.8: non deve
    # vincolare la release corrente del catalogo, che può avanzare indipendentemente.
    require(SNAPSHOT["scope"]["coverage"] == "7/7", "Copertura snapshot incompleta")
    require(SNAPSHOT["scope"]["years"] == [2021, 2023], "Annualità snapshot inattese")
    require(SNAPSHOT["comparabilityCheck"]["result"] == "accepted", "Comparabilità non accettata")

    raw = {
        year: {row["town"]: row for row in SNAPSHOT["raw"][year]}
        for year in ("2021", "2023")
    }
    require(set(raw["2021"]) == set(raw["2023"]), "Comuni diversi tra 2021 e 2023")
    require(len(raw["2021"]) == 7, "Lo snapshot non contiene sette Comuni")

    for metric_key, formula in EXPECTED.items():
        metric = DATA["metrics"][metric_key]
        require(len(metric["rows"]) == 7, f"Copertura incompleta: {metric_key}")
        for row in metric["rows"]:
            series = row.get("series") or {}
            require(series.get("years") == [2021, 2023], f"Annualità errate: {metric_key}/{row['town']}")
            require(len(series.get("values", [])) == 2, f"Serie incompleta: {metric_key}/{row['town']}")
            expected_2021 = formula(raw["2021"][row["town"]])
            expected_2023 = formula(raw["2023"][row["town"]])
            require(abs(series["values"][0] - expected_2021) < 1e-9, f"Valore 2021 errato: {metric_key}/{row['town']}")
            tolerance = 0.051 if metric_key in {"vacantHomes", "singleHouseholds"} else 1e-9
            require(abs(series["values"][1] - expected_2023) <= tolerance, f"Valore 2023 errato: {metric_key}/{row['town']}")
            require(series["values"][1] == row["value"], f"Ultimo punto non coincide col valore corrente: {metric_key}/{row['town']}")

    require(
        all(not row.get("series") for row in DATA["metrics"]["cohabitingHouseholds"]["rows"]),
        "Famiglie coabitanti non deve avere uno storico: PF9 manca nel tracciato 2021",
    )
    require(
        all(not row.get("series") for row in DATA["metrics"]["householdSize"]["rows"]),
        "Componenti medi non deve avere uno storico: PF8 non consente un valore esatto",
    )
    history_count = sum(
        1 for metric in DATA["metrics"].values()
        if any(row.get("series") for row in metric["rows"])
    )
    require(history_count >= 43, "Copertura storica inferiore al livello v1.8")
    print("Storico v1.8 verificato: 7 nuove serie, 7/7 Comuni, 2021–2023.")


if __name__ == "__main__":
    main()
