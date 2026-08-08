#!/usr/bin/env python3
"""Controlli geometrici, anti-duplicazione e screenshot del layout comunale."""
from __future__ import annotations

import contextlib
import os
import socket
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
REVIEW = ROOT / "artifacts" / "town-layout"


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *_args: object) -> None:
        return


@contextlib.contextmanager
def server(directory: Path):
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


def geometry(page, selector: str) -> dict:
    box = page.locator(selector).bounding_box()
    require(bool(box), f"Elemento senza geometria: {selector}")
    return box


def desktop_checks(page, base: str) -> None:
    page.goto(base + "comuni/seravezza/?tema=salute&indicatore=chronicTotal", wait_until="networkidle")
    page.wait_for_selector(".town-indicator-picker")

    require(page.locator(".town-context-nav .context-nav-row").count() == 0,
            "La riga locale dei Comuni non deve essere renderizzata")
    require(page.locator(".town-context-nav .theme-nav").count() == 1,
            "Deve restare una sola navigazione locale dei temi")
    require(page.locator("#town-topic > .metric-switch").count() == 0,
            "Il catalogo superiore degli indicatori non deve essere renderizzato")
    require(page.locator(".town-history-panel .comparison-bars").count() == 0,
            "Lo storico comunale non deve duplicare il confronto a sette Comuni")
    require(page.locator(".town-history-panel .ux-view-shell").count() == 0,
            "Lo storico comunale non deve essere trasformato dal vecchio selettore attuale/storico")
    require(page.locator('.town-overview [data-indicator="chronicTotal"]').count() == 0,
            "Il dato aperto non deve ricomparire nel Quadro del tema")

    supplementary = page.locator(".town-supplementary")
    require(supplementary.count() == 1, "Salute: dettaglio aggiuntivo assente")
    supplementary_text = supplementary.inner_text().lower()
    for repeated in ("speranza di vita", "accessi al pronto soccorso", "ricoverati", "assistenza domiciliare", "diabete", "demenza"):
        require(repeated not in supplementary_text,
                f"Salute: il dettaglio aggiuntivo ripete un indicatore del quadro: {repeated}")
    for unique in ("ipertensione", "bpco", "tumori", "malattie circolatorie", "malattie respiratorie"):
        require(unique in supplementary_text,
                f"Salute: dettaglio realmente aggiuntivo mancante: {unique}")

    primary = geometry(page, ".town-metric-primary")
    versilia = geometry(page, ".town-versilia-strip")
    history = geometry(page, ".town-history-panel")
    overview = geometry(page, ".town-overview")
    topic = geometry(page, "#town-topic")

    for name, box in (("dato", primary), ("Versilia", versilia), ("storico", history)):
        require(box["width"] >= topic["width"] * .92,
                f"{name}: pannello non sufficientemente largo: {box['width']} / {topic['width']}")
    require(primary["y"] + primary["height"] <= versilia["y"] + 2,
            "Il confronto Versilia deve seguire il dato principale")
    require(versilia["y"] + versilia["height"] <= history["y"] + 2,
            "Lo storico deve seguire il confronto Versilia")
    require(history["y"] + history["height"] <= overview["y"] + 140,
            "Il Quadro del tema deve arrivare dopo lo storico")

    widths = page.evaluate("({client: document.documentElement.clientWidth, scroll: document.documentElement.scrollWidth})")
    require(widths["scroll"] <= widths["client"] + 1, f"Overflow orizzontale desktop: {widths}")

    picker = page.locator("[data-town-metric-select]")
    picker.select_option("diabetes")
    page.wait_for_function("() => new URL(location.href).searchParams.get('indicatore') === 'diabetes'")
    require("64,32" in page.locator(".town-metric-primary").inner_text(),
            "Il cambio indicatore non aggiorna il dato principale")
    require(page.locator('.town-overview [data-indicator="diabetes"]').count() == 0,
            "Il nuovo indicatore selezionato ricompare nel quadro")
    require(page.locator('.town-overview [data-indicator="chronicTotal"]').count() == 1,
            "L'indicatore precedente deve rientrare nel quadro dopo il cambio")
    supplementary_text = page.locator(".town-supplementary").inner_text().lower()
    require("diabete" not in supplementary_text,
            "Il dato selezionato viene ripetuto anche nel dettaglio aggiuntivo")

    benchmark = page.locator(".town-benchmark:not(.benchmark-unavailable)")
    require(benchmark.count() == 1, "Benchmark esterno atteso ma assente")
    require(benchmark.locator(".town-benchmark-values article").count() >= 1,
            "Benchmark esterno privo di valori")
    benchmark_text = benchmark.inner_text().lower()
    require("toscana" in benchmark_text, "Benchmark Toscana assente")
    require("seravezza\n64,32" not in benchmark_text,
            "Il benchmark ripete ancora il valore comunale già mostrato sopra")
    require("qui non viene ripetuto" in benchmark_text,
            "Il benchmark non esplicita la scelta anti-duplicazione")

    page.evaluate("window.scrollTo(0, 0)")
    page.wait_for_timeout(80)
    page.screenshot(path=str(REVIEW / "seravezza-salute-desktop.png"), full_page=True)


def mobile_checks(browser, base: str) -> None:
    context = browser.new_context(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True)
    page = context.new_page()
    page.goto(base + "comuni/massarosa/?tema=demografia&indicatore=population", wait_until="networkidle")
    page.wait_for_selector(".town-indicator-picker")
    require(page.locator(".town-context-nav .context-nav-row").count() == 0,
            "Mobile: la riga dei Comuni non deve ricomparire")
    widths = page.evaluate("({client: document.documentElement.clientWidth, scroll: document.documentElement.scrollWidth})")
    require(widths["scroll"] <= widths["client"] + 1, f"Mobile: overflow orizzontale {widths}")
    require(page.locator('.town-overview [data-indicator="population"]').count() == 0,
            "Mobile: il dato selezionato è duplicato nel quadro")
    page.evaluate("window.scrollTo(0, 0)")
    page.screenshot(path=str(REVIEW / "massarosa-demografia-mobile.png"), full_page=True)
    context.close()


def main() -> None:
    REVIEW.mkdir(parents=True, exist_ok=True)
    chromium_path = os.environ.get("CHROMIUM_PATH")
    launch_args: dict[str, object] = {"headless": True}
    if chromium_path:
        launch_args["executable_path"] = chromium_path

    with server(DIST) as base, sync_playwright() as p:
        browser = p.chromium.launch(**launch_args)
        page = browser.new_page(viewport={"width": 1680, "height": 900})
        desktop_checks(page, base)
        mobile_checks(browser, base)
        browser.close()

    print("Layout comunale verificato: geometria, anti-duplicazione e screenshot di revisione generati.")


if __name__ == "__main__":
    main()
