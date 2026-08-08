#!/usr/bin/env python3
"""Regression checks for the town profile v2 layout."""
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


def browser_checks() -> None:
    launch = {"headless": True}
    chromium_path = os.environ.get("CHROMIUM_PATH")
    if chromium_path:
        launch["executable_path"] = chromium_path

    with server(DIST) as base, sync_playwright() as p:
        browser = p.chromium.launch(**launch)
        page = browser.new_page(viewport={"width": 1440, "height": 1000})

        page.goto(base + "comuni/seravezza/?tema=salute&indicatore=chronicTotal", wait_until="networkidle")
        page.wait_for_selector("#town-topic.town-layout-v2 .town-v2-picker")
        require(page.locator(".town-v2-picker").count() == 1, "Seravezza/Salute: picker duplicato")
        require("Malattie croniche" in page.locator(".town-v2-picker-current").inner_text(), "Indicatore selezionato non riconosciuto")
        require("Condizioni di salute" in page.locator(".town-v2-picker-current").inner_text(), "Sezione dell'indicatore assente")
        require(
            page.locator(".town-v2-source-controls").evaluate("el => getComputedStyle(el).display") == "none",
            "Il vecchio catalogo superiore è ancora visibile",
        )
        heading = page.locator(".town-v2-overview .section-heading h3").inner_text().strip()
        require(heading == "Quadro della salute a Seravezza", f"Titolo quadro inatteso: {heading!r}")

        geometry = page.evaluate("""
          () => {
            const metric = document.querySelector('#town-topic > .town-metric-layout').getBoundingClientRect();
            const history = document.querySelector('#town-topic > .history-panel').getBoundingClientRect();
            return { metric, history };
          }
        """)
        require(abs(geometry["metric"]["top"] - geometry["history"]["top"]) < 12,
                f"Desktop: dettaglio e storico non sono allineati {geometry}")
        require(geometry["history"]["left"] > geometry["metric"]["left"] + geometry["metric"]["width"] - 4,
                f"Desktop: storico non è affiancato al dettaglio {geometry}")

        primary_background = page.locator(".town-metric-primary").evaluate("el => getComputedStyle(el).backgroundColor")
        history_background = page.locator(".history-panel").evaluate("el => getComputedStyle(el).backgroundColor")
        require(primary_background != history_background, "L'accento cromatico del dato principale è scomparso")

        picker = page.locator(".town-v2-picker")
        picker.locator("summary").click()
        page.locator('[data-town-v2-metric="emergencyAccess"]').click()
        page.wait_for_function("() => new URLSearchParams(location.search).get('indicatore') === 'emergencyAccess'")
        page.wait_for_selector('.town-v2-picker[data-active-metric="emergencyAccess"]')
        require(page.locator(".town-v2-picker").count() == 1, "Cambio indicatore: picker duplicato")
        require(page.locator(".town-v2-source-controls").evaluate("el => getComputedStyle(el).display") == "none",
                "Cambio indicatore: vecchio catalogo riapparso")

        for path, expected in (
            ("comuni/massarosa/?tema=demografia&indicatore=population", "Quadro della demografia a Massarosa"),
            ("comuni/viareggio/?tema=bilanci&indicatore=currentRevenueAccruedPerResident", "Quadro della bilanci comunali a Viareggio"),
        ):
            page.goto(base + path, wait_until="networkidle")
            page.wait_for_selector("#town-topic.town-layout-v2 .town-v2-picker")
            require(page.locator(".town-v2-overview .section-heading h3").inner_text().strip() == expected,
                    f"Layout v2 non coerente su {path}")

        mobile = browser.new_context(viewport={"width": 390, "height": 844}, has_touch=True)
        mobile_page = mobile.new_page()
        mobile_page.goto(base + "comuni/seravezza/?tema=salute&indicatore=chronicTotal", wait_until="networkidle")
        mobile_page.wait_for_selector("#town-topic.town-layout-v2 .town-v2-picker")
        sizes = mobile_page.evaluate("({client: document.documentElement.clientWidth, scroll: document.documentElement.scrollWidth})")
        require(sizes["scroll"] <= sizes["client"], f"Mobile: overflow orizzontale {sizes}")
        mobile_geometry = mobile_page.evaluate("""
          () => {
            const metric = document.querySelector('#town-topic > .town-metric-layout').getBoundingClientRect();
            const history = document.querySelector('#town-topic > .history-panel').getBoundingClientRect();
            const picker = document.querySelector('.town-v2-picker > summary').getBoundingClientRect();
            return { metric, history, picker, viewport: innerWidth };
          }
        """)
        require(mobile_geometry["history"]["top"] >= mobile_geometry["metric"]["bottom"] - 2,
                f"Mobile: storico non impilato sotto il dettaglio {mobile_geometry}")
        require(mobile_geometry["picker"]["right"] <= mobile_geometry["viewport"] + 1,
                f"Mobile: picker fuori viewport {mobile_geometry}")
        mobile_page.locator(".town-v2-picker > summary").tap()
        require(mobile_page.locator(".town-v2-picker").get_attribute("open") is not None,
                "Mobile: selettore indicatori non apribile")
        mobile.close()
        browser.close()


def main() -> None:
    require((DIST / "assets" / "town-layout-v2.js").exists(), "JS layout v2 non copiato in dist")
    require((DIST / "assets" / "town-layout-v2.css").exists(), "CSS layout v2 non copiato in dist")
    browser_checks()
    print("Layout comunale v2 verificato: dettaglio, storico, quadro tema e mobile.")


if __name__ == "__main__":
    main()
