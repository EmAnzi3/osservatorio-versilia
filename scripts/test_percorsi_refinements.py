#!/usr/bin/env python3
from __future__ import annotations

import contextlib
import os
import re
import socket
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Iterable

from playwright.sync_api import sync_playwright

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


def main() -> None:
    map_app = (DIST / "percorsi" / "app.js").read_text(encoding="utf-8")
    map_index = (DIST / "percorsi" / "index.html").read_text(encoding="utf-8")
    for color in ("#176b4a", "#c66a00", "#0077a8", "#b23a48"):
        require(color in map_app and color in map_index, f"Colore cartografico mancante: {color}")
    require("applyInitialUrlFilters" in map_app and 'params.get("tipo")' in map_app,
            "Deep link tipologia cartografica non attivo")

    with server(DIST) as base, sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1680, "height": 1000})

        page.goto(base + "confronta/mobilita/?indicatore=slowMobilityRoutes", wait_until="networkidle")
        axis = page.locator(".comparison-axis")
        axis.wait_for(state="visible")
        axis_text = axis.inner_text()
        require(not re.search(r"\d+,\d+\s+count", axis_text),
                f"Asse conteggi ancora decimale: {axis_text!r}")

        page.goto(base + "comuni/camaiore/?tema=mobilita&indicatore=slowMobilityRoutes", wait_until="networkidle")
        cta = page.locator(".slow-mobility-map-entry a")
        require(cta.count() == 1 and cta.is_visible(), "CTA cartografia vicino alla selezione non visibile")
        require("comune=Camaiore" in (cta.get_attribute("href") or ""), "CTA non mantiene Camaiore")

        page.goto(base + "comuni/camaiore/?tema=mobilita&indicatore=slowMobilityTrekking", wait_until="networkidle")
        href = page.locator(".slow-mobility-map-entry a").get_attribute("href") or ""
        require("comune=Camaiore" in href and "tipo=trekking" in href,
                f"CTA Trekking non mantiene i filtri: {href}")

        page.goto(base + "confronta/sicurezza/?indicatore=roadInjuries", wait_until="networkidle")
        order = page.evaluate("""() => {
          const main = document.querySelector('main');
          const nodes = [...main.children];
          return [nodes.indexOf(document.querySelector('#compare-benchmark')), nodes.indexOf(document.querySelector('.crime-context')), nodes.indexOf(document.querySelector('#compare-tools'))];
        }""")
        require(order[0] >= 0 and order[0] < order[1] < order[2],
                f"Ordine benchmark/criminalità/metodo errato: {order}")

        page.goto(base + "percorsi/?comune=Camaiore&tipo=trekking", wait_until="networkidle")
        active = page.locator('.chip.active').get_attribute('data-mode')
        require(active == "trekking", f"Filtro tipologia non applicato dalla URL: {active}")
        legend_colors = page.locator('.legend .leg span').evaluate_all("els => els.map(el => el.style.background)")
        require(len(set(legend_colors)) == 4, f"Palette legenda non sufficientemente distinta: {legend_colors}")

        browser.close()

    print("Rifiniture Percorsi verificate: assi interi, CTA contestuale, ordine Sicurezza e palette distinta.")


if __name__ == "__main__":
    main()
