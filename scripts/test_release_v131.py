#!/usr/bin/env python3
"""Release regression checks for Osservatorio Versilia v1.3.1."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
TOWNS = [
    "camaiore", "forte-dei-marmi", "massarosa", "pietrasanta",
    "seravezza", "stazzema", "viareggio",
]
THEMES = [
    "abitare", "ambiente", "comunita", "demografia", "economia",
    "istruzione", "lavoro", "mobilita", "salute",
]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    source = json.loads((ROOT / "data" / "site-data.json").read_text(encoding="utf-8"))
    built = json.loads((DIST / "data" / "site-data.json").read_text(encoding="utf-8"))

    require(source == built, "Il dataset pubblicato non coincide con il sorgente")
    require(source.get("version") == "2026.08.05-v1.3.1", "Versione pubblica inattesa")
    require("local" not in source.get("version", "").lower(), "Versione marcata come locale")
    require("anteprima" not in source.get("updated", "").lower(), "Data marcata come anteprima")
    require(len(source.get("towns", [])) == 7, "Copertura comunale diversa da 7")
    require(len(source.get("themes", {})) == 9, "Numero temi diverso da 9")
    require(len(source.get("metrics", {})) == 69, "Numero indicatori diverso da 69")

    expected_towns = set(TOWNS)
    for key, metric in source["metrics"].items():
        rows = metric.get("rows", [])
        slugs = {row.get("slug") for row in rows}
        require(expected_towns <= slugs, f"{key}: copertura inferiore a 7/7")
        meta = metric.get("meta", {})
        require(meta.get("year") not in (None, ""), f"{key}: anno mancante")
        require(meta.get("source") not in (None, ""), f"{key}: fonte mancante")

    bundle = (DIST / "assets" / "app-bundle.js").read_text(encoding="utf-8")
    for token in (
        "function compareContextNav",
        "function townContextNav",
        "function updateTownContextLinks",
    ):
        require(token in bundle, f"Funzione di navigazione assente: {token}")
    require("Anteprima locale" not in bundle, "Badge di anteprima ancora nel bundle")

    for theme in THEMES:
        text = (DIST / "confronta" / theme / "index.html").read_text(encoding="utf-8")
        require("compare-context-nav" in text, f"{theme}: navigazione tra temi assente")
        require(text.count("data-context-theme=") == 9, f"{theme}: collegamenti tema diversi da 9")
        require("prototype-badge" not in text, f"{theme}: badge locale presente")

    for town in TOWNS:
        text = (DIST / "comuni" / town / "index.html").read_text(encoding="utf-8")
        require("town-context-nav" in text, f"{town}: navigazione tra Comuni assente")
        require(text.count("data-town-link=") == 7, f"{town}: collegamenti Comune diversi da 7")
        require(text.count("data-profile-theme=") == 9, f"{town}: temi comunali diversi da 9")
        require("tema=demografia" in text and "indicatore=population" in text,
                f"{town}: contesto tema/indicatore non conservato")
        require("prototype-badge" not in text, f"{town}: badge locale presente")

    css = (DIST / "assets" / "fidelity.css").read_text(encoding="utf-8")
    for token in (".compare-context-nav", ".town-context-nav", "overflow-x: auto"):
        require(token in css, f"Regola di navigazione assente: {token}")

    manifest = json.loads((DIST / "build-manifest.json").read_text(encoding="utf-8"))
    require(manifest.get("dataVersion") == source["version"], "Manifest non allineato")
    print("Release v1.3.1 validata: 69 indicatori, 9 temi, 7 Comuni e navigazione contestuale.")


if __name__ == "__main__":
    main()
