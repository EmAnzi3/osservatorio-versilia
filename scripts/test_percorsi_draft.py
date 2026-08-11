#!/usr/bin/env python3
"""Controlli specifici per cartografia e statistiche di Percorsi Versilia."""
from __future__ import annotations

import base64
from collections import Counter, defaultdict
import contextlib
import gzip
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import socket
import subprocess
import threading
from typing import Iterable

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "percorsi"
DIST_ROOT = ROOT / "dist"
DIST = DIST_ROOT / "percorsi"
TOWN_SLUGS = {
    "Camaiore": "camaiore",
    "Forte dei Marmi": "forte-dei-marmi",
    "Massarosa": "massarosa",
    "Pietrasanta": "pietrasanta",
    "Seravezza": "seravezza",
    "Stazzema": "stazzema",
    "Viareggio": "viareggio",
}
MODES = ("trekking", "cammino", "bicycle", "mtb")


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *_args: object) -> None:
        return


@contextlib.contextmanager
def server(directory: Path) -> Iterable[str]:
    old = Path.cwd()
    os.chdir(directory)
    try:
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        httpd = ThreadingHTTPServer(("127.0.0.1", port), QuietHandler)
        thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        thread.start()
        try:
            yield f"http://127.0.0.1:{port}/"
        finally:
            httpd.shutdown()
            thread.join(timeout=5)
    finally:
        os.chdir(old)


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


def expected_municipality_stats(records: list[dict]) -> dict[str, dict]:
    counts: dict[str, dict] = defaultdict(lambda: {"routes": 0, "by_mode": Counter()})
    for record in records:
        props = record.get("p", {})
        mode = props.get("primary_mode")
        for municipality in props.get("municipalities", []):
            counts[municipality]["routes"] += 1
            counts[municipality]["by_mode"][mode] += 1
    return counts


def check_source() -> None:
    index = (SRC / "index.html").read_text(encoding="utf-8")
    method = (SRC / "metodo.html").read_text(encoding="utf-8")
    app = (SRC / "app.js").read_text(encoding="utf-8")
    summary = json.loads((SRC / "data" / "master_summary.json").read_text(encoding="utf-8"))
    site_stats = json.loads((SRC / "data" / "site_stats.json").read_text(encoding="utf-8"))
    integration_js = (ROOT / "assets" / "percorsi-integration.js").read_text(encoding="utf-8")
    integration_css = ROOT / "assets" / "percorsi-integration.css"
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
    require("assets/percorsi-integration.js" in index,
            "Supporto ai deep link comunali non collegato alla mappa")
    require(integration_css.exists() and integration_css.stat().st_size > 0,
            "CSS di integrazione Percorsi assente")
    require("data-percorsi-stats=\"versilia\"" in integration_js,
            "Modulo statistico Versilia assente")
    require("data-percorsi-stats=\"town\"" in integration_js,
            "Modulo statistico comunale assente")
    require("searchParams.set('comune'" in integration_js,
            "Deep link della mappa per Comune assente")

    subprocess.run(["node", "--check", str(ROOT / "assets" / "percorsi-integration.js")], check=True)

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

    versilia = site_stats.get("versilia", {})
    require(versilia.get("routes") == summary.get("public_total") == 41,
            "Totale statistico Versilia non coerente con il master")
    require(abs(float(versilia.get("km", 0)) - float(summary.get("public_versilia_km", 0))) < 0.05,
            "Chilometri Versilia non coerenti con il master")
    require(versilia.get("by_mode") == summary.get("by_mode"),
            "Ripartizione per modalità non coerente con il master")

    calculated = expected_municipality_stats(records)
    published = site_stats.get("municipalities", {})
    require(set(published) == set(TOWN_SLUGS.values()), "Statistiche comunali incomplete")
    for name, slug in TOWN_SLUGS.items():
        actual = published[slug]
        expected = calculated[name]
        require(actual.get("routes") == expected["routes"],
                f"Conteggio percorsi errato per {name}")
        actual_modes = actual.get("by_mode", {})
        for mode in MODES:
            require(int(actual_modes.get(mode, 0)) == int(expected["by_mode"].get(mode, 0)),
                    f"Conteggio {mode} errato per {name}")

    note = site_stats.get("definition", {})
    require("non sono sommabili" in note.get("municipality_count_note", ""),
            "Manca l'avvertenza sui conteggi comunali non additivi")
    require("non sono pubblicati" in note.get("municipality_km_note", ""),
            "Manca la cautela sui km comunali")


def check_dist() -> None:
    require(DIST.exists(), "Percorsi non copiato nella build dist")
    for relative in ("index.html", "metodo.html", "app.js", "data-loader.js", "styles.css",
                     "data/master_summary.json", "data/site_stats.json"):
        path = DIST / relative
        require(path.exists() and path.stat().st_size > 0, f"File Percorsi assente dalla build: {relative}")
    built = (DIST / "index.html").read_text(encoding="utf-8")
    require("Percorsi Versilia" in built and "Geometria corroborata" not in built,
            "Pagina Percorsi non copiata correttamente nella build")

    for asset in ("percorsi-integration.css", "percorsi-integration.js"):
        path = DIST_ROOT / "assets" / asset
        require(path.exists() and path.stat().st_size > 0, f"Asset integrazione assente dalla build: {asset}")

    compare = (DIST_ROOT / "confronta" / "mobilita" / "index.html").read_text(encoding="utf-8")
    require("assets/percorsi-integration.css" in compare and "assets/percorsi-integration.js" in compare,
            "Statistiche Percorsi non collegate alla pagina Mobilità")
    for slug in TOWN_SLUGS.values():
        page = (DIST_ROOT / "comuni" / slug / "index.html").read_text(encoding="utf-8")
        require("assets/percorsi-integration.css" in page and "assets/percorsi-integration.js" in page,
                f"Statistiche Percorsi non collegate al profilo comunale {slug}")


def check_browser_integration() -> None:
    with server(DIST_ROOT) as base, sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 1000})

        page.goto(base + "confronta/mobilita/", wait_until="networkidle")
        overview = page.locator('[data-percorsi-stats="versilia"]')
        overview.wait_for(state="visible", timeout=10000)
        text = overview.inner_text()
        require("41" in text and "343" in text, "Sintesi Versilia non visibile nella pagina Mobilità")
        require(overview.locator("tbody tr").count() == 7, "La tabella comunale deve contenere 7 Comuni")
        camaiore_link = overview.locator('a[href*="comune=Camaiore"]')
        require(camaiore_link.count() == 1, "Link cartografico filtrato di Camaiore assente")

        page.goto(base + "comuni/camaiore/?tema=mobilita", wait_until="networkidle")
        town = page.locator('[data-percorsi-stats="town"]')
        town.wait_for(state="visible", timeout=10000)
        town_text = town.inner_text()
        require("11" in town_text and "Camaiore" in town_text,
                "Statistiche di Camaiore non visibili nella scheda Mobilità")
        require("Bici" in town_text and "5" in town_text,
                "Composizione dei percorsi di Camaiore non visibile")
        require(town.locator('a[href*="comune=Camaiore"]').count() == 1,
                "Deep link Camaiore verso la cartografia assente")

        browser.close()


def main() -> None:
    check_source()
    check_dist()
    check_browser_integration()
    print("Percorsi Versilia verificato nel sito: cartografia + statistiche Versilia e 7 Comuni coerenti con 41 percorsi pubblici.")


if __name__ == "__main__":
    main()
