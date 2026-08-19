#!/usr/bin/env python3
"""Contratto statico della pagina Meteo e clima canonica di collaudo."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    html = (ROOT / "confronta" / "meteo-clima" / "index.html").read_text(encoding="utf-8")
    js = (ROOT / "assets" / "meteo-clima-canonical.js").read_text(encoding="utf-8")
    css = (ROOT / "assets" / "meteo-clima-canonical.css").read_text(encoding="utf-8")
    main_data = json.loads((ROOT / "data" / "meteo-clima-poc.json").read_text(encoding="utf-8"))
    minmax = json.loads((ROOT / "data" / "meteo-clima-minmax-poc.json").read_text(encoding="utf-8"))

    require('name="robots" content="noindex,nofollow"' in html, "Meteo e clima deve restare noindex")
    require("meteo-clima-canonical.js" in html and "meteo-clima-canonical.css" in html, "Renderer canonico non collegato")
    require(html.count('role="tab" data-metric=') == 4, "Devono essere presenti quattro indicatori climatici")
    require("Anno in corso" not in html and "dato parziale" not in html.lower(), "La pagina non deve prevedere YTD")
    require("ordine alfabetico" in html.lower() and "non costruisce una graduatoria" in html.lower(), "Semantica no-ranking assente")
    require("data/data-status.json" in js, "Stato dati non derivato dal modello pubblico")
    require(".sort((a, b) => a.town.localeCompare(b.town, 'it'))" in js, "Confronto comuni non alfabetico")
    require("Media semplice dei 7 trend" in js, "Benchmark dei sette Comuni non qualificato")
    require("year 2026" not in js.lower() and "2026-ytd" not in js.lower(), "Residuo YTD nel renderer")
    require("climate-compare-marker" in css and "climate-status-grid" in css, "Stile del confronto/stato incompleto")

    expected = {'Camaiore','Forte dei Marmi','Massarosa','Pietrasanta','Seravezza','Stazzema','Viareggio'}
    require(set(main_data["municipalities"]) == expected, "Copertura comuni Tmedia/P non valida")
    require(set(minmax["municipalities"]) == expected, "Copertura comuni Tmin/Tmax non valida")
    require(main_data["coverage"]["partial"] is None, "Dataset principale contiene ancora un periodo parziale")
    for series in main_data["municipalities"].values():
        require(series["latestComplete"]["year"] == series["years"][-1], "Anno completo principale incoerente")
    for series in minmax["municipalities"].values():
        require(series["latestComplete"]["year"] == series["years"][-1], "Anno completo Tmin/Tmax incoerente")

    print("Meteo e clima canonico: 4 indicatori, noindex, no YTD, comuni alfabetici e stato derivato.")


if __name__ == "__main__":
    main()
