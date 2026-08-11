#!/usr/bin/env python3
"""Controlli specifici per la mini-app cartografica Percorsi Versilia."""
from __future__ import annotations

import base64
import gzip
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "percorsi"
DIST = ROOT / "dist" / "percorsi"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def read_records() -> list[dict]:
    records: list[dict] = []
    parts = sorted((SRC / "data").glob("routes-part-*.b64"))
    require(len(parts) == 5, f"Attese 5 parti dati, trovate {len(parts)}")
    for path in parts:
        raw = base64.b64decode(path.read_text(encoding="utf-8").strip())
        payload = json.loads(gzip.decompress(raw).decode("utf-8"))
        require(isinstance(payload, list), f"Parte dati non valida: {path.name}")
        records.extend(payload)
    return records


def check_source() -> None:
    index = (SRC / "index.html").read_text(encoding="utf-8")
    method = (SRC / "metodo.html").read_text(encoding="utf-8")
    app = (SRC / "app.js").read_text(encoding="utf-8")
    summary = json.loads((SRC / "data" / "master_summary.json").read_text(encoding="utf-8"))
    records = read_records()

    require('rel="canonical" href="https://osservatorioversilia.it/percorsi/"' in index,
            "Canonical Percorsi assente")
    require('type="application/ld+json"' in index, "JSON-LD Percorsi assente")
    require('rel="canonical"' in method and 'type="application/ld+json"' in method,
            "Metadati della pagina Metodo incompleti")
    require("Geometria corroborata" not in index,
            "Voce tecnica ancora presente nella legenda pubblica")
    require(index.count('class="leg"') == 4, "La legenda deve contenere quattro categorie")
    for label in ("Trekking", "Cammini", "Bici", "MTB"):
        require(label in index, f"Categoria legenda assente: {label}")
    require("L.control.scale" not in app and "leaflet-control-scale" not in index,
            "La scala metrica non deve essere presente")
    require("Home: torna alla vista generale Versilia" in app,
            "Controllo Home assente")

    require(summary.get("public_total") == 41, "Totale pubblico diverso da 41")
    require(summary.get("by_quality") == {"A0": 30, "B1": 11}, "Ripartizione A0/B1 inattesa")
    require(summary.get("public_zero_length_count") == 0, "Sono presenti percorsi pubblici a 0 km")
    require(summary.get("cammini_public_count") == 2, "I Cammini pubblici devono essere 2")
    require(len(records) == 41, f"Record web attesi 41, trovati {len(records)}")

    qualities = {record.get("p", {}).get("quality_code") for record in records}
    require(qualities <= {"A0", "B1"}, f"Classi non pubblicabili nel dataset web: {qualities}")
    zero = [record.get("p", {}).get("name") for record in records
            if float(record.get("p", {}).get("length_km") or 0) <= 0]
    require(not zero, f"Percorsi web a lunghezza zero: {zero}")


def check_dist() -> None:
    require(DIST.exists(), "Percorsi non copiato nella build dist")
    for relative in ("index.html", "metodo.html", "app.js", "data-loader.js", "styles.css",
                     "data/master_summary.json"):
        path = DIST / relative
        require(path.exists() and path.stat().st_size > 0, f"File Percorsi assente dalla build: {relative}")
    built = (DIST / "index.html").read_text(encoding="utf-8")
    require("Percorsi Versilia" in built and "Geometria corroborata" not in built,
            "Pagina Percorsi non copiata correttamente nella build")


def main() -> None:
    check_source()
    check_dist()
    print("Percorsi Versilia verificato: 41 pubblici, 30 A0 + 11 B1, 2 Cammini, 0 lunghezze zero.")


if __name__ == "__main__":
    main()
