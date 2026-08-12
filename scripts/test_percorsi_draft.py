#!/usr/bin/env python3
"""Controlli del draft Percorsi integrato nella grammatica dell'Osservatorio."""
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
SLOW_KEYS = (
    "slowMobilityRoutes",
    "slowMobilityTrekking",
    "slowMobilityCammini",
    "slowMobilityBici",
    "slowMobilityMtb",
)


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
    records = read_records()

    require('rel="canonical" href="https://osservatorioversilia.it/percorsi/"' in index, "Canonical Percorsi assente")
    require('type="application/ld+json"' in index, "JSON-LD Percorsi assente")
    require('class="site-header"' in index and 'class="site-brand"' in index,
            "La cartografia non usa l'header dell'Osservatorio")
    require("Percorsi e mobilità lenta" in index, "Titolo cartografia non allineato alla tassonomia")
    require("Torna a Mobilità e infrastrutture" in index, "Ritorno a Mobilità poco esplicito o assente")
    require("ovmark" not in index, "Vecchio logo testuale ancora presente")
    require("Geometria corroborata" not in index, "Voce tecnica ancora presente nella legenda")
    require(index.count('class="leg"') == 4, "La legenda deve contenere quattro categorie")
    require("L.control.scale" not in app, "La scala metrica non deve essere presente")
    require("Home: torna alla vista generale Versilia" in app, "Controllo Home assente")
    require('rel="canonical"' in method and 'type="application/ld+json"' in method,
            "Metadati della pagina Metodo incompleti")

    require(summary.get("public_total") == 41, "Totale pubblico diverso da 41")
    require(summary.get("by_quality") == {"A0": 30, "B1": 11}, "Ripartizione A0/B1 inattesa")
    require(summary.get("public_zero_length_count") == 0, "Sono presenti percorsi pubblici a 0 km")
    require(summary.get("cammini_public_count") == 2, "I Cammini pubblici devono essere 2")
    require(abs(float(summary.get("public_versilia_km", 0)) - 342.65) < 0.1,
            "Il totale km Versilia deve derivare dalle lunghezze territoriali validate")
    require(len(records) == 41, f"Record web attesi 41, trovati {len(records)}")

    versilia = site_stats.get("versilia", {})
    require(versilia.get("routes") == 41 and abs(float(versilia.get("km", 0)) - 342.7) < 0.1,
            "Sintesi Versilia incoerente")
    calculated = expected_municipality_stats(records)
    published = site_stats.get("municipalities", {})
    for name, slug in TOWN_SLUGS.items():
        actual = published[slug]
        expected = calculated[name]
        require(actual.get("routes") == expected["routes"], f"Conteggio percorsi errato per {name}")
        for mode in MODES:
            require(int(actual.get("by_mode", {}).get(mode, 0)) == int(expected["by_mode"].get(mode, 0)),
                    f"Conteggio {mode} errato per {name}")


def check_dist_data() -> None:
    require(DIST.exists(), "Percorsi non copiato nella build dist")
    for relative in ("index.html", "metodo.html", "app.js", "data-loader.js", "styles.css", "osservatorio.css"):
        path = DIST / relative
        require(path.exists() and path.stat().st_size > 0, f"File Percorsi assente dalla build: {relative}")

    data = json.loads((DIST_ROOT / "data" / "site-data.json").read_text(encoding="utf-8"))
    mobility = data["themes"]["mobilita"]
    security = data["themes"].get("sicurezza")
    require(security is not None and security.get("label") == "Sicurezza e territorio",
            "Tema Sicurezza e territorio assente")
    require("roadInjuries" not in mobility["metrics"], "Sicurezza stradale ancora dentro Mobilità")
    require(data["metrics"]["roadInjuries"]["meta"]["theme"] == "sicurezza",
            "Feriti su strada non assegnato al nuovo tema")
    slow_section = next((s for s in mobility["sections"] if s.get("key") == "mobilita-lenta"), None)
    require(slow_section is not None, "Sezione Mobilità lenta assente dalla grammatica standard")
    require(tuple(slow_section["metrics"]) == SLOW_KEYS, "Indicatori Mobilità lenta incompleti")
    for key in SLOW_KEYS:
        require(key in data["metrics"] and len(data["metrics"][key]["rows"]) == 7,
                f"Indicatore Percorsi non valido: {key}")
    require(data["metrics"]["slowMobilityRoutes"]["rows"][2]["value"] >= 0,
            "Indicatore percorsi non valorizzato")
    require((DIST_ROOT / "confronta" / "sicurezza" / "index.html").exists(),
            "Pagina confronto Sicurezza e territorio assente")

    bundle = (DIST_ROOT / "assets" / "app-bundle.js").read_text(encoding="utf-8")
    require("percorsiQuickMarkup(data)" not in bundle, "Vecchio box rapido Percorsi ancora nel renderer")
    require("percorsiCompareMarkup(data)" not in bundle, "Vecchio box statistico standalone ancora nel renderer")
    require("percorsiTownMarkup(data, town)" not in bundle, "Vecchio box comunale standalone ancora nel renderer")
    require("themeKey === 'sicurezza' ? crimeMarkup(data)" in bundle,
            "Criminalità non spostata nel tema Sicurezza")
    subprocess.run(["node", "--check", str(DIST_ROOT / "assets" / "app-bundle.js")], check=True)


def check_browser() -> None:
    with server(DIST_ROOT) as base, sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1680, "height": 1000})

        page.goto(base + "confronta/mobilita/?indicatore=slowMobilityRoutes", wait_until="networkidle")
        require(page.locator('[data-section="mobilita-lenta"]').count() == 1,
                "Mobilità lenta non compare nella fisarmonica di Mobilità")
        require(page.locator('[data-metric="slowMobilityRoutes"]').count() == 1,
                "Indicatore Percorsi disponibili assente")
        require(page.locator('[data-percorsi-quick], [data-percorsi-stats]').count() == 0,
                "Persistono box Percorsi fuori dalla grammatica degli indicatori")
        definition = page.locator("#compare-definition").inner_text()
        require("Percorsi pubblici" in definition, "Definizione Percorsi non renderizzata come indicatore")
        require(page.locator('#compare-tools a[href*="percorsi/"]').count() == 1,
                "CTA cartografia assente dall'indicatore Percorsi")
        require(page.locator(".crime-context").count() == 0,
                "Criminalità deve essere fuori da Mobilità")

        page.goto(base + "comuni/camaiore/?tema=mobilita&indicatore=slowMobilityRoutes", wait_until="networkidle")
        require(page.locator('[data-section="mobilita-lenta"]').count() == 1,
                "Mobilità lenta assente nella scheda di Camaiore")
        require(page.locator(".town-metric-primary strong").first.inner_text().strip() == "11",
                "Camaiore deve mostrare 11 percorsi nel normale indicatore")
        require(page.locator('.town-data-actions a[href*="percorsi/"][href*="comune=Camaiore"]').count() == 1,
                "CTA cartografia filtrata Camaiore assente")
        require(page.locator('[data-percorsi-stats]').count() == 0,
                "Persistono box comunali Percorsi standalone")

        page.goto(base + "confronta/sicurezza/?indicatore=roadInjuries", wait_until="networkidle")
        require("Sicurezza e territorio" in page.locator("main").inner_text(),
                "Nuovo tema Sicurezza non renderizzato")
        crime = page.locator(".crime-context")
        require(crime.count() == 1 and crime.is_visible(),
                "Criminalità non visibile nel nuovo tema Sicurezza")
        require("Criminalità e delitti denunciati" in crime.inner_text(),
                "Contesto criminalità incompleto")

        page.goto(base + "percorsi/?comune=Camaiore", wait_until="networkidle")
        require(page.locator(".site-brand").count() == 1,
                "Header Osservatorio assente dalla cartografia")
        require(page.locator(".map-back").count() == 1 and page.locator(".map-back").is_visible(),
                "Pulsante di ritorno a Mobilità assente")
        require(page.locator(".legend .leg").count() == 4, "Legenda cartografia non valida")

        browser.close()


def main() -> None:
    check_source()
    check_dist_data()
    check_browser()
    print("Percorsi verificato: una sola grammatica Mobilità, Sicurezza separata, cartografia nel design Osservatorio.")


if __name__ == "__main__":
    main()
