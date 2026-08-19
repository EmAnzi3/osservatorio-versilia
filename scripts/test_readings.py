#!/usr/bin/env python3
"""Contratto statico dei Percorsi di lettura."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
FORBIDDEN = {
    "year", "period", "publishedPeriod", "source", "sourceUrl",
    "value", "formatted", "statusLabel", "lastChecked",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    config = json.loads((ROOT / "data" / "readings.json").read_text(encoding="utf-8"))
    data = json.loads((ROOT / "data" / "site-data.json").read_text(encoding="utf-8"))
    readings = config["readings"]
    require(config.get("status") == "draft-noindex", "Le Letture devono restare noindex in collaudo")
    require(len(readings) == 7, f"Attese 7 Letture, trovate {len(readings)}")
    slugs = [item["slug"] for item in readings]
    require(len(slugs) == len(set(slugs)), "Slug Letture duplicati")

    for item in readings:
        require(not (FORBIDDEN & set(item)), f"Metadata canonici duplicati in {item['slug']}")
        require(item["primaryMetric"] in item["metrics"], f"Primary fuori perimetro: {item['slug']}")
        for key in item["metrics"]:
            require(key in data["metrics"], f"Indicatore inesistente in {item['slug']}: {key}")
        page = DIST / "letture" / item["slug"] / "index.html"
        require(page.exists() and page.stat().st_size > 0, f"Pagina Lettura assente: {item['slug']}")
        text = page.read_text(encoding="utf-8")
        require('name="robots" content="noindex,nofollow"' in text, f"noindex assente: {item['slug']}")
        require('data-page="reading"' in text, f"Marker runtime assente: {item['slug']}")
        require("Periodo pubblicato" in text and "Stato" in text and "Fonte" in text, f"Tracciabilità incompleta: {item['slug']}")
        require("rilevazione → validazione → pubblicazione" in text, f"Sequenza editoriale assente: {item['slug']}")

    index = (DIST / "letture" / "index.html").read_text(encoding="utf-8")
    require('data-page="readings"' in index, "Indice Letture non protetto dal runtime")
    require(index.count('class="reading-index-card"') == 7, "Indice Letture incompleto")
    require('name="robots" content="noindex,nofollow"' in index, "Indice Letture non noindex")

    bundle = (DIST / "assets" / "app-bundle.js").read_text(encoding="utf-8")
    require("pageType === 'reading' || pageType === 'readings'" in bundle, "Runtime non protegge le Letture prerenderizzate")
    require((ROOT / "percorsi" / "index.html").exists(), "/percorsi/ cartografico non deve essere sostituito")
    require((ROOT / "percorsi" / "metodo.html").exists(), "Metodo Percorsi cartografici mancante")

    climate = (DIST / "letture" / "cinquantanni-di-clima" / "index.html").read_text(encoding="utf-8")
    require("non sono misure osservate da una singola stazione" in climate, "Caveat climatico assente")
    require("bar-rank" not in climate and "ux-bar-rank" not in climate, "La Lettura clima non deve introdurre classifiche")
    print("Letture verificate: 7 pagine noindex, dati canonici, tracciabilità e /percorsi/ preservato.")


if __name__ == "__main__":
    main()
