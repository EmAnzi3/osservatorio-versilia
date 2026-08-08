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


def download_csv(page: Page, path: str) -> list[list[str]]:
    with page.expect_download() as download_info:
        page.locator("[data-download]").click()
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
        require(len(life) == 8,
                "CSV senza storico: deve restare una riga corrente per ciascun Comune")

        page.goto(base + "confronta/economia/?indicatore=tourismPresences", wait_until="networkidle")
        page.locator('[data-scale="normalized"]').click()
        normalized = download_csv(page, str(temp / "tourism-normalized.csv"))
        require(len(normalized) == 8,
                "CSV rapportato: non deve mescolare lo storico assoluto alla vista normalizzata")
        require({row[5] for row in normalized[1:]} == {"decimal"},
                "CSV rapportato: unità inattesa")

        pdf_cases = (
            ("confronta/bilanci/?indicatore=currentRevenueAccruedPerResident", "bilanci.pdf", ".ux-view-shell", "Andamento 2019–2025"),
            ("confronta/economia/?indicatore=income", "economia.pdf", ".ux-view-shell", "Confronto a due punti 2023–2024"),
            ("comuni/massarosa/?tema=demografia&indicatore=population", "massarosa.pdf", ".town-history-panel", "Residenti nel tempo"),
        )
        for route, filename, ready_selector, expected in pdf_cases:
            page.goto(base + route, wait_until="networkidle")
            page.wait_for_selector(ready_selector)
            target = temp / filename
            page.pdf(path=str(target), print_background=True, prefer_css_page_size=True)
            pages, text = pdf_text(target)
            require(pages == 2, f"PDF {filename}: attese 2 pagine A4, trovate {pages}")
            require(expected in text, f"PDF {filename}: contenuto storico non incluso")
            require(target.stat().st_size > 50_000, f"PDF {filename}: output anormalmente piccolo")

        browser.close()

    print("Export v1.6.1 validati: CSV storico completo e PDF A4 in due pagine, incluso lo storico comunale lineare.")


if __name__ == "__main__":
    main()
