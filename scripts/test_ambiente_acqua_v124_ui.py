#!/usr/bin/env python3
"""Regression gate for the v1.24 Ambiente water/remediation UI."""

from __future__ import annotations

import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SITE = json.loads((ROOT / "data/site-data.json").read_text(encoding="utf-8"))
APP = (ROOT / "assets/app-parts/03.txt").read_text(encoding="utf-8")
CSS = (ROOT / "assets/fidelity.css").read_text(encoding="utf-8")
HISTORY = (ROOT / "assets/ux-history.js").read_text(encoding="utf-8")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def function_source(name: str, next_name: str) -> str:
    start = APP.index(f"  function {name}")
    end = APP.index(f"  function {next_name}", start)
    return APP[start:end]


def main() -> None:
    require("drinkingWaterQuality" in SITE["metrics"] and "remediationProceedings" in SITE["metrics"],
            "Gli indicatori Ambiente v1.24 devono restare nel catalogo")

    quality = SITE["metrics"]["drinkingWaterQuality"]
    require(len(quality["parameterDefinitions"]) == 17, "GAIA: attesi 17 parametri")
    require(sum(len(row["localities"]) for row in quality["rows"]) == 70, "GAIA: attese 70 località")
    require(
        sum(len(locality["values"]) for row in quality["rows"] for locality in row["localities"]) == 1190,
        "GAIA: attesi 1.190 valori",
    )
    require(
        any(str(value).startswith("<") for row in quality["rows"] for locality in row["localities"] for value in locality["values"]),
        "I valori censurati GAIA devono restare testuali",
    )

    quality_compare = function_source("drinkingWaterQualityCompareMarkup", "waterQualitySelectedMarkup")
    quality_town = function_source("drinkingWaterQualityTownMarkup", "remediationPartValue")
    require("data-water-quality-parameter-compare" in quality_compare, "Confronto: selettore parametro assente")
    require("water-quality-range-chart" in quality_compare, "Confronto: grafico comunale min–max assente")
    require("waterQualityChartSeries" in APP and "waterQualityCensoredLimit" in APP,
            "Confronto: intervalli o valori censurati non gestiti")
    require("water-quality-values-disclosure" not in quality_compare,
            "Confronto: la granularità per località non deve comparire nella pagina tematica")
    require("località GAIA disponibili" not in quality_compare,
            "Confronto: ricompare il conteggio delle località al posto del grafico")
    require("Valore di sintesi" not in quality_compare, "Confronto: ricompare il falso valore sintetico")
    require("data-water-quality-locality" in quality_town, "Scheda: selettore località assente")
    require("data-water-quality-parameter-town" in quality_town, "Scheda: selettore parametro assente")
    require("water-quality-town-disclosure" in quality_town,
            "Scheda: il dettaglio per località deve stare in un accordion chiuso")
    require("Mostra tutti i ${defs.length} parametri" in APP, "Scheda: accordion dei 17 parametri assente")
    require("water-quality-coverage" not in APP,
            "Scheda: non deve ricomparire un confronto o una copertura laterale fuorviante")
    require("town-metric-layout${drinkingQuality?' single-column':''}" in APP,
            "Scheda: il riepilogo GAIA deve occupare tutta la larghezza senza benchmark")

    remediation = SITE["metrics"]["remediationProceedings"]
    active = sum(next(part["value"] for part in row["parts"] if part["key"] == "active") for row in remediation["rows"])
    closed = sum(next(part["value"] for part in row["parts"] if part["key"] == "closed") for row in remediation["rows"])
    procedures = [item for row in remediation["rows"] for item in row["procedures"]]
    require((active, closed, len(procedures)) == (56, 96, 152), "SISBON: conteggi attesi 56/96/152")
    require(len({item["id"] for item in procedures}) == 152, "SISBON: codice regionale non univoco")

    camaiore = next(row for row in remediation["rows"] if row["slug"] == "camaiore")
    camaiore_active = next(part["value"] for part in camaiore["parts"] if part["key"] == "active")
    camaiore_closed = next(part["value"] for part in camaiore["parts"] if part["key"] == "closed")
    require((camaiore_active, camaiore_closed) == (9, 22), "Camaiore: conteggi attesi 9/22")
    require(math.isclose((camaiore_active - 56 / 7) / (56 / 7) * 100, 12.5), "Benchmark attivi errato")
    require(math.isclose(96 / 7, 13.714285714285714), "Benchmark chiusi errato")

    remediation_compare = function_source("remediationCompareMarkup", "signedNumber")
    remediation_town = function_source("remediationTownMarkup", "compositeCompareDefaults")
    require("remediation-count-active" in remediation_compare and "remediation-count-closed" in remediation_compare,
            "Confronto: attivi e chiusi non sono entrambi visibili")
    require("%" not in remediation_compare, "Confronto: i conteggi SISBON non devono diventare percentuali")
    require("<details data-remediation-status" in remediation_town, "Scheda: procedimenti non resi come accordion")
    require("Rispetto alla media dei Comuni della Versilia" in APP, "Benchmark comunale non esplicitato")
    require("details[open] summary i::before{content:\"−\"}" in CSS, "Accordion: icona meno nello stato aperto assente")
    require("padding:14px" in CSS and "padding:16px" in CSS, "Padding minimo dei nuovi componenti non verificabile")
    require("background:#fff" in CSS, "Le superfici operative dei nuovi componenti devono essere bianche")
    history_guards = [
        line for line in HISTORY.splitlines()
        if ".includes" in line and "selected.metric?.meta?.compositeType" in line
    ]
    require(
        len(history_guards) >= 2
        and all("'drinkingWaterQuality'" in line and "'remediationProceedings'" in line for line in history_guards),
        "La UX storica generica deve ignorare entrambi i renderer descrittivi",
    )

    print("Ambiente acqua e bonifiche v1.24 UI: PASS")


if __name__ == "__main__":
    main()
