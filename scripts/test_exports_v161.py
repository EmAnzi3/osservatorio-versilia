#!/usr/bin/env python3
"""Regressioni degli export CSV e PDF introdotti nella v1.6.1."""
from __future__ import annotations

import contextlib
import csv
import io
import os
import socket
import tempfile
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Iterable

from playwright.sync_api import Page, sync_playwright
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"


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


def static_assertions() -> None:
    for asset in ("export-v161.js", "export-v161.css"):
        require((DIST / "assets" / asset).exists(), f"Asset export mancante: {asset}")

    for page in (
        DIST / "confronta" / "demografia" / "index.html",
        DIST / "comuni" / "massarosa" / "index.html",
    ):
        text = page.read_text(encoding="utf-8")
        require("assets/export-v161.js?v=" in text,
                f"Script export non incluso in {page}")
        require("assets/export-v161.css?v=" in text,
                f"Stili di stampa non inclusi in {page}")

    atlas_runtime = DIST / "assets" / "economy-atlas.js"
    require(atlas_runtime.exists(), "Runtime Atlante Economia mancante")
    atlas_text = atlas_runtime.read_text(encoding="utf-8")
    require("data-actions atlas-export-actions" in atlas_text,
            "Atlante: azioni export non allineate al componente data-actions")
    require("data-download" in atlas_text and "data-print" in atlas_text,
            "Atlante: attributi standard export mancanti")
    require('id="atlasDownloadCsv" data-download>Scarica CSV</button>' in atlas_text,
            "Atlante: bottone CSV non standard")
    require('id="atlasPrint" data-print>Stampa / PDF</button>' in atlas_text,
            "Atlante: bottone Stampa/PDF non standard")


def download_csv(page: Page, path: str, selector: str = "[data-download]") -> list[list[str]]:
    with page.expect_download() as download_info:
        page.locator(selector).click()
    download = download_info.value
    target = Path(path)
    download.save_as(target)
    return list(csv.reader(io.StringIO(target.read_text(encoding="utf-8-sig")), delimiter=";"))


def pdf_text(path: Path) -> tuple[int, str]:
    reader = PdfReader(path)
    text = "\n".join(page.extract_text() or "" for page in reader.pages)
    return len(reader.pages), text


def main() -> None:
    static_assertions()
    chromium_path = os.environ.get("CHROMIUM_PATH")
    launch_args: dict[str, object] = {"headless": True}
    if chromium_path:
        launch_args["executable_path"] = chromium_path

    with tempfile.TemporaryDirectory() as temporary, server(DIST) as base, sync_playwright() as playwright:
        temp = Path(temporary)
        browser = playwright.chromium.launch(**launch_args)
        page = browser.new_page(viewport={"width": 1440, "height": 950}, accept_downloads=True)

        page.goto(base + "confronta/demografia/?indicatore=population", wait_until="networkidle")
        page.wait_for_selector(".ux-view-shell")
        population = download_csv(page, str(temp / "population.csv"))
        require(population[0] == ["Comune", "Codice Istat", "Indicatore", "Anno", "Valore", "Unità", "Fonte"],
                "CSV: intestazione inattesa")
        require(len(population) == 57,
                f"CSV popolazione: attese 56 righe storiche, trovate {len(population) - 1}")
        require({row[0] for row in population[1:]} == {
            "Camaiore", "Forte dei Marmi", "Massarosa", "Pietrasanta", "Seravezza", "Stazzema", "Viareggio"
        }, "CSV popolazione: copertura comunale incompleta")
        require({row[3] for row in population[1:]} == {str(year) for year in range(2019, 2027)},
                "CSV popolazione: annualità 2019–2026 incomplete")

        page.goto(base + "confronta/salute/?indicatore=lifeExpectancy", wait_until="networkidle")
        life = download_csv(page, str(temp / "life.csv"))
        require(life[0] == [
            "Territorio", "Codice Istat", "Indicatore", "Anno",
            "Sesso", "Valore", "Unità", "Fonte",
        ], "CSV speranza di vita: intestazione inattesa")
        life_rows = life[1:]
        expected_life_territories = {
            "Camaiore", "Forte dei Marmi", "Massarosa", "Pietrasanta",
            "Seravezza", "Stazzema", "Viareggio", "Versilia",
        }
        expected_life_years = {str(year) for year in range(2008, 2023)}
        expected_life_sexes = {"Totale", "Maschi", "Femmine"}
        require(len(life_rows) == 360,
                f"CSV speranza di vita: attese 360 osservazioni, trovate {len(life_rows)}")
        require({row[0] for row in life_rows} == expected_life_territories,
                "CSV speranza di vita: copertura territoriale incompleta")
        require({row[3] for row in life_rows} == expected_life_years,
                "CSV speranza di vita: annualità 2008–2022 incomplete")
        require({row[4] for row in life_rows} == expected_life_sexes,
                "CSV speranza di vita: disaggregazione per sesso incompleta")
        require({row[6] for row in life_rows} == {"years"},
                "CSV speranza di vita: unità inattesa")
        require({row[1] for row in life_rows if row[0] == "Versilia"} == {"202M"},
                "CSV speranza di vita: codice ufficiale Versilia mancante")
        for territory in expected_life_territories:
            for sex in expected_life_sexes:
                rows = [row for row in life_rows if row[0] == territory and row[4] == sex]
                require(len(rows) == 15 and {row[3] for row in rows} == expected_life_years,
                        f"CSV speranza di vita: serie incompleta per {territory}, {sex}")

        page.goto(base + "confronta/economia/?indicatore=tourismPresences", wait_until="networkidle")
        page.locator('[data-scale="normalized"]').click()
        normalized = download_csv(page, str(temp / "tourism-normalized.csv"))
        require(len(normalized) == 8,
                "CSV rapportato: non deve mescolare lo storico assoluto alla vista normalizzata")
        require({row[5] for row in normalized[1:]} == {"decimal"},
                "CSV rapportato: unità inattesa")

        page.goto(base + "confronta/economia/atlante-attivita-economiche/", wait_until="networkidle")
        page.wait_for_function(
            "() => !!document.querySelector('ov-economy-atlas')?.shadowRoot?.querySelector('.atlas-export-actions')",
            timeout=20000,
        )
        atlas = page.locator("ov-economy-atlas")
        actions = atlas.locator(".data-actions.atlas-export-actions")
        require(actions.count() == 1, "Atlante: barra azioni standard assente o duplicata")
        buttons = actions.locator("button")
        require(buttons.count() == 2, "Atlante: attesi due semplici bottoni di export")
        require(buttons.all_inner_texts() == ["Scarica CSV", "Stampa / PDF"],
                "Atlante: etichette dei bottoni export inattese")
        require(actions.locator("svg").count() == 0, "Atlante: i bottoni export non devono avere icone custom")
        button_style = buttons.first.evaluate(
            "el => ({radius:getComputedStyle(el).borderRadius,size:getComputedStyle(el).fontSize,"
            "paddingTop:getComputedStyle(el).paddingTop,paddingLeft:getComputedStyle(el).paddingLeft})"
        )
        require(button_style == {
            "radius": "9px", "size": "10px", "paddingTop": "9px", "paddingLeft": "11px"
        }, f"Atlante: stile bottoni non allineato alle altre pagine: {button_style}")
        atlas_csv = download_csv(page, str(temp / "atlante.csv"), "ov-economy-atlas [data-download]")
        require(atlas_csv[0] == [
            "Territorio", "Codice ATECO", "Livello", "Descrizione", "Anno",
            "UL attive", "UL artigiane (2025)", "Fonte",
        ], "Atlante CSV: intestazione inattesa")
        require(len(atlas_csv) > 1000, "Atlante CSV: esportazione anormalmente ridotta")
        require({row[0] for row in atlas_csv[1:]} == {"Versilia"},
                "Atlante CSV: territorio iniziale inatteso")

        pdf_cases = (
            ("confronta/bilanci/?indicatore=currentRevenueAccruedPerResident", "bilanci.pdf", "Andamento 2019–2025"),
            ("confronta/economia/?indicatore=income", "economia.pdf", "2011–2024"),
            ("comuni/massarosa/?tema=demografia&indicatore=population", "massarosa.pdf", "Andamento 2019–2026"),
        )
        for route, filename, expected in pdf_cases:
            page.goto(base + route, wait_until="networkidle")
            page.wait_for_selector(".ux-view-shell")
            target = temp / filename
            page.pdf(path=str(target), print_background=True, prefer_css_page_size=True)
            pages, text = pdf_text(target)
            require(pages == 2, f"PDF {filename}: attese 2 pagine A4, trovate {pages}")
            require(expected in text, f"PDF {filename}: storico non incluso")
            require(target.stat().st_size > 50_000, f"PDF {filename}: output anormalmente piccolo")

        browser.close()

    print("Export validati: CSV/PDF standard e Atlante con azioni coerenti alle altre pagine.")


if __name__ == "__main__":
    main()
