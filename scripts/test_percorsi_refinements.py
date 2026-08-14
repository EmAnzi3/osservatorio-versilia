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


def require_no_horizontal_overflow(page, label: str, tolerance: int = 2) -> None:
    dims = page.evaluate("""() => ({
      viewport: window.innerWidth,
      documentWidth: document.documentElement.scrollWidth,
      bodyWidth: document.body.scrollWidth
    })""")
    actual = max(int(dims["documentWidth"]), int(dims["bodyWidth"]))
    require(actual <= int(dims["viewport"]) + tolerance,
            f"Overflow orizzontale mobile in {label}: viewport={dims['viewport']} contenuto={actual}")


def require_box_inside_viewport(page, selector: str, label: str, tolerance: int = 2) -> None:
    box = page.locator(selector).bounding_box()
    require(box is not None, f"Elemento mobile non misurabile: {label}")
    width = page.evaluate("window.innerWidth")
    require(box["x"] >= -tolerance and box["x"] + box["width"] <= width + tolerance,
            f"Elemento mobile fuori viewport ({label}): {box}, viewport={width}")


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

        page.goto(base + "confronta/sicurezza/?indicatore=roadSafety", wait_until="networkidle")
        order = page.evaluate("""() => {
          const main = document.querySelector('main');
          const nodes = [...main.children];
          return [
            nodes.indexOf(document.querySelector('#compare-benchmark')),
            nodes.indexOf(document.querySelector('#polizia-locale')),
            nodes.indexOf(document.querySelector('#criminalita')),
            nodes.indexOf(document.querySelector('#compare-tools'))
          ];
        }""")
        require(order[0] >= 0 and order[0] < order[1] < order[2] < order[3],
                f"Ordine benchmark/Polizia Locale/criminalità/metodo errato: {order}")

        page.goto(base + "percorsi/?comune=Camaiore&tipo=trekking", wait_until="networkidle")
        require(page.locator('.safetyNotice').count() == 1 and page.locator('.safetyNotice').is_visible(),
                "Avvertenza di sicurezza non visibile nella cartografia")
        active = page.locator('.chip.active').get_attribute('data-mode')
        require(active == "trekking", f"Filtro tipologia non applicato dalla URL: {active}")
        legend_colors = page.locator('.legend .leg span').evaluate_all("els => els.map(el => el.style.background)")
        require(len(set(legend_colors)) == 4, f"Palette legenda non sufficientemente distinta: {legend_colors}")

        page.set_viewport_size({"width": 1365, "height": 768})
        page.goto(base + "percorsi/", wait_until="networkidle")
        page.wait_for_selector("#routeList .card")
        visible_routes = page.evaluate("routesLayer.getLayers().length")
        listed_routes = page.locator("#routeList .card").count()
        require(visible_routes == listed_routes and visible_routes > 1,
                f"Mappa e lista Percorsi non allineate prima della selezione: {visible_routes}/{listed_routes}")
        page.locator("#routeList .card").first.click()
        require(page.locator("#detail").is_visible(), "Dettaglio del percorso selezionato non visibile")
        require(page.locator("#routeList .card.active").count() == 1,
                "La lista non evidenzia un solo percorso selezionato")
        require(page.evaluate("routesLayer.getLayers().length") == 1,
                "La mappa non esclude gli altri percorsi dopo la selezione")
        require(page.locator("#routeList .card").count() == listed_routes,
                "La selezione ha modificato indebitamente la lista filtrata")
        page.locator("#detailClose").click()
        require(not page.locator("#detail").is_visible(), "Dettaglio ancora visibile dopo la chiusura")
        require(page.evaluate("routesLayer.getLayers().length") == visible_routes,
                "La chiusura del dettaglio non ripristina i percorsi filtrati")
        list_size = page.locator("#routeList").evaluate(
            "element => ({clientHeight: element.clientHeight, scrollHeight: element.scrollHeight})"
        )
        require(list_size["clientHeight"] >= 180,
                f"Lista Percorsi troppo compressa su laptop: {list_size}")
        require(list_size["scrollHeight"] > list_size["clientHeight"],
                f"Lista Percorsi non scorrevole su laptop: {list_size}")

        # Verifica mobile esplicita: la nuova architettura deve restare leggibile e usabile
        # senza overflow della pagina, CTA perse o controlli cartografici fuori viewport.
        page.set_viewport_size({"width": 390, "height": 844})

        page.goto(base + "confronta/mobilita/?indicatore=slowMobilityRoutes", wait_until="networkidle")
        require_no_horizontal_overflow(page, "confronto Mobilità lenta")
        require(page.locator('[data-section="mobilita-lenta"]').count() == 1,
                "Sezione Mobilità lenta assente su mobile")
        require(page.locator('[data-metric="slowMobilityRoutes"]').is_visible(),
                "Percorsi disponibili non selezionabile su mobile")
        require(page.locator('.comparison-axis').is_visible(),
                "Grafico confronto Mobilità lenta non visibile su mobile")

        page.goto(base + "comuni/camaiore/?tema=mobilita&indicatore=slowMobilityRoutes", wait_until="networkidle")
        require_no_horizontal_overflow(page, "scheda comunale Camaiore / Mobilità lenta")
        require(page.locator('.slow-mobility-map-entry').is_visible(),
                "Richiamo alla cartografia assente su mobile nella scheda comunale")
        require_box_inside_viewport(page, '.slow-mobility-map-entry a', "CTA Esplora sulla mappa")
        page.locator('[data-metric="slowMobilityBici"]').click()
        page.wait_for_timeout(150)
        mobile_href = page.locator('.slow-mobility-map-entry a').get_attribute('href') or ''
        require("comune=Camaiore" in mobile_href and "tipo=bicycle" in mobile_href,
                f"Cambio indicatore mobile non aggiorna il deep link cartografico: {mobile_href}")

        page.goto(base + "confronta/sicurezza/?indicatore=roadSafety", wait_until="networkidle")
        require_no_horizontal_overflow(page, "Sicurezza e territorio")
        crime = page.locator('#criminalita')
        local_police = page.locator('#polizia-locale')
        require(crime.count() == 1 and crime.is_visible(),
                "Criminalità e delitti denunciati non visibile su mobile")
        require(local_police.count() == 1 and local_police.is_visible(),
                "Contesto Polizia Locale non visibile su mobile")
        require_box_inside_viewport(page, '#criminalita', "box Criminalità e delitti denunciati")
        require_box_inside_viewport(page, '#polizia-locale', "box Polizia Locale")

        page.goto(base + "percorsi/?comune=Camaiore&tipo=trekking", wait_until="networkidle")
        require_no_horizontal_overflow(page, "cartografia Percorsi")
        require(page.locator('#municipality').input_value() == "Camaiore",
                "Filtro Comune non applicato nella cartografia mobile")
        require(page.locator('.chip.active').get_attribute('data-mode') == "trekking",
                "Filtro Trekking non applicato nella cartografia mobile")
        require(page.locator('.map-back').is_visible(),
                "Ritorno a Mobilità non visibile nella cartografia mobile")
        require_box_inside_viewport(page, '.map-back', "Torna a Mobilità e infrastrutture")
        map_box = page.locator('#map').bounding_box()
        require(map_box is not None and map_box["width"] >= 380 and map_box["height"] >= 450,
                f"Mappa troppo piccola o collassata su mobile: {map_box}")
        require(page.locator('.leaflet-control-zoom').is_visible(), "Zoom Leaflet non visibile su mobile")
        require(page.locator('.leaflet-control-home').is_visible(), "Home Leaflet non visibile su mobile")
        require(page.locator('.legend .leg').count() == 4 and page.locator('.legend').is_visible(),
                "Legenda cartografica mobile incompleta")
        require_box_inside_viewport(page, '.legend', "legenda cartografica")

        # Seconda larghezza reale, più stretta, per intercettare regressioni tipiche Android.
        page.set_viewport_size({"width": 360, "height": 800})
        page.goto(base + "percorsi/?comune=Camaiore&tipo=bicycle", wait_until="networkidle")
        require_no_horizontal_overflow(page, "cartografia Percorsi 360px")
        require(page.locator('.chip.active').get_attribute('data-mode') == "bicycle",
                "Filtro Bici non applicato a 360px")
        narrow_map = page.locator('#map').bounding_box()
        require(narrow_map is not None and narrow_map["width"] >= 350,
                f"Cartografia non occupa correttamente la larghezza a 360px: {narrow_map}")

        browser.close()

    print("Rifiniture Percorsi verificate anche su mobile: 390px e 360px senza overflow, CTA e cartografia operative.")


if __name__ == "__main__":
    main()