#!/usr/bin/env python3
"""Contratto dati per lifeExpectancy: storico ARS 2008–2022 e sesso."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = json.loads((ROOT / "data" / "site-data.json").read_text(encoding="utf-8"))
SNAPSHOT = json.loads((ROOT / "data" / "source-snapshots" / "ars-life-expectancy-1290-2008-2022.json").read_text(encoding="utf-8"))

YEARS = list(range(2008, 2023))
SEXES = ["totale", "maschi", "femmine"]
EXPECTED_SHA = "ba1d0e9580eedf4a9b495032bb0fde70afc1b8ec14aae3752c7c7da847ba51f3"
TOWN_CODES = {"046005", "046013", "046018", "046024", "046028", "046030", "046033"}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def rounded(value: float) -> float:
    return round(float(value) + 1e-12, 2)


def main() -> None:
    require(SNAPSHOT["indicator"]["id"] == 1290, "Snapshot: indicatore ARS diverso da 1290")
    require(SNAPSHOT["source"]["csvSha256"] == EXPECTED_SHA, "Snapshot: hash dati.csv inatteso")
    require(SNAPSHOT["scope"]["years"] == YEARS, "Snapshot: annualità diverse da 2008–2022")
    require(SNAPSHOT["scope"]["sexes"] == SEXES, "Snapshot: sessi diversi da Totale/Maschi/Femmine")
    require(SNAPSHOT["scope"]["coverage"] == "7/7", "Snapshot: copertura diversa da 7/7")
    require(SNAPSHOT["scope"]["expectedRows"] == 405, "Snapshot: numero osservazioni diverso da 405")

    metric = SITE["metrics"]["lifeExpectancy"]
    meta = metric["meta"]
    require(meta.get("compositeType") == "sexBreakdown", "lifeExpectancy: compositeType sexBreakdown mancante")
    require(meta.get("defaultSex") == "totale", "lifeExpectancy: defaultSex deve essere totale")
    require([item["key"] for item in meta.get("sexOptions", [])] == SEXES, "lifeExpectancy: opzioni sesso incoerenti")
    require(metric.get("history", {}).get("years") == YEARS, "lifeExpectancy: storico 2008–2022 mancante")
    require(metric.get("history", {}).get("coverage") == "7/7", "lifeExpectancy: copertura storica diversa da 7/7")
    require(metric.get("method", {}).get("coverage") == "7/7", "lifeExpectancy: metodo privo di copertura 7/7")

    rows = metric["rows"]
    require(len(rows) == 7, f"lifeExpectancy: attese 7 righe comunali, trovate {len(rows)}")
    require({row["code"] for row in rows} == TOWN_CODES, "lifeExpectancy: perimetro comunale non canonico")

    for row in rows:
        code = row["code"]
        parts = row.get("parts", [])
        require([part["key"] for part in parts] == SEXES, f"{row['town']}: parti sesso incomplete")
        for part in parts:
            sex = part["key"]
            series = part.get("series", {})
            require(series.get("years") == YEARS, f"{row['town']} {sex}: anni incompleti")
            values = series.get("values", [])
            require(len(values) == len(YEARS), f"{row['town']} {sex}: valori incompleti")
            expected = [rounded(v) for v in SNAPSHOT["series"][code][sex]]
            require(values == expected, f"{row['town']} {sex}: valori diversi dallo snapshot")
            require(rounded(part["value"]) == expected[-1], f"{row['town']} {sex}: valore corrente non allineato al 2022")
        require(rounded(row["value"]) == rounded(parts[0]["value"]), f"{row['town']}: totale corrente diverso dalla parte Totale")
        require(row.get("series") == parts[0]["series"], f"{row['town']}: serie base non coincide con Totale")

    aggregate = metric["aggregate"]
    aggregate_parts = aggregate.get("parts", [])
    require([part["key"] for part in aggregate_parts] == SEXES, "Versilia: parti sesso incomplete")
    for part in aggregate_parts:
        sex = part["key"]
        expected = [rounded(v) for v in SNAPSHOT["series"]["VERSILIA"][sex]]
        require(part["series"]["years"] == YEARS, f"Versilia {sex}: anni incompleti")
        require(part["series"]["values"] == expected, f"Versilia {sex}: valori diversi dallo snapshot")
        require(rounded(part["value"]) == expected[-1], f"Versilia {sex}: valore corrente non allineato al 2022")
    require(rounded(aggregate["value"]) == rounded(aggregate_parts[0]["value"]), "Versilia: aggregato base diverso dal Totale ufficiale")
    require("pubblicato direttamente" in aggregate.get("note", "").lower(), "Versilia: deve essere esplicito che l'aggregato è ufficiale ARS")

    benchmarks = meta.get("benchmarksBySex", {})
    require(set(benchmarks) == set(SEXES), "Benchmark Toscana per sesso incompleti")
    for sex in SEXES:
        expected = rounded(SNAPSHOT["series"]["TOSCANA"][sex][-1])
        require(rounded(benchmarks[sex]["tuscany"]) == expected, f"Toscana {sex}: benchmark 2022 incoerente")
        require(str(benchmarks[sex]["year"]) == "2022", f"Toscana {sex}: anno benchmark incoerente")

    print("lifeExpectancy v1.22: 2008–2022, Totale/Maschi/Femmine, 7/7, Versilia e Toscana ufficiali ARS: OK")


if __name__ == "__main__":
    main()
