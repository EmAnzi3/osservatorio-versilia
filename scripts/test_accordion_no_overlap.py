#!/usr/bin/env python3
"""Regression visuale: le intestazioni a fisarmonica non devono sovrapporre testo e strumenti."""
from __future__ import annotations

import contextlib
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import os
from pathlib import Path
import socket
import threading
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


def overlaps(a: dict | None, b: dict | None, tolerance: float = 0.5) -> bool:
    if not a or not b:
        return False
    return not (
        a["x"] + a["width"] <= b["x"] + tolerance
        or b["x"] + b["width"] <= a["x"] + tolerance
        or a["y"] + a["height"] <= b["y"] + tolerance
        or b["y"] + b["height"] <= a["y"] + tolerance
    )


def check_headings(page, label: str) -> None:
    headings = page.locator(".metric-group-heading.ux-section-toggle")
    require(headings.count() > 0, f"Nessuna intestazione fisarmonica trovata in {label}")
    for index in range(headings.count()):
        heading = headings.nth(index)
        title = heading.locator(":scope > strong")
        description = heading.locator(":scope > span:not(.ux-section-tools)")
        tools = heading.locator(":scope > .ux-section-tools")
        if not tools.count():
            continue
        tools_box = tools.bounding_box()
        if title.count():
            require(
                not overlaps(title.bounding_box(), tools_box),
                f"Titolo sovrapposto a contatore/chevron in {label}: {heading.inner_text()!r}",
            )
        if description.count():
            require(
                not overlaps(description.bounding_box(), tools_box),
                f"Descrizione sovrapposta a contatore/chevron in {label}: {heading.inner_text()!r}",
            )


def main() -> None:
    compare_pages = sorted(
        path.parent.name for path in (DIST / "confronta").glob("*/index.html")
    )
    town_pages = sorted(
        path.parent.name for path in (DIST / "comuni").glob("*/index.html")
    )
    require(compare_pages, "Pagine di confronto non trovate")
    require(town_pages, "Pagine comunali non trovate")

    with server(DIST) as base, sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1680, "height": 1000})

        for theme in compare_pages:
            page.goto(base + f"confronta/{theme}/", wait_until="networkidle")
            check_headings(page, f"confronta/{theme}")

        for town in town_pages:
            page.goto(base + f"comuni/{town}/?tema=mobilita", wait_until="networkidle")
            check_headings(page, f"comuni/{town}?tema=mobilita")

        # Il nuovo ingresso Percorsi deve essere nel flusso visibile della pagina Mobilità.
        page.goto(base + "confronta/mobilita/", wait_until="networkidle")
        quick = page.locator('[data-percorsi-quick="versilia"]')
        overview = page.locator('[data-percorsi-stats="versilia"]')
        require(quick.count() == 1 and quick.is_visible(), "Ingresso compatto Percorsi non visibile in Mobilità")
        require(overview.count() == 1 and overview.is_visible(), "Statistiche Percorsi non visibili in Mobilità")
        require(quick.locator('a[href="#percorsi-statistiche"]').count() == 1,
                "Link rapido alle statistiche Percorsi assente")

        page.goto(base + "comuni/camaiore/?tema=mobilita", wait_until="networkidle")
        order = page.evaluate("""() => {
          const topic = document.querySelector('#town-topic');
          if (!topic) return null;
          const children = [...topic.children];
          return {
            catalog: children.indexOf(topic.querySelector(':scope > .metric-switch.metric-catalog')),
            paths: children.indexOf(topic.querySelector(':scope > [data-percorsi-stats="town"]')),
            metric: children.indexOf(topic.querySelector(':scope > .town-metric-layout'))
          };
        }""")
        require(order is not None, "Struttura della scheda comunale non trovata")
        require(order["catalog"] >= 0 and order["paths"] == order["catalog"] + 1,
                "Percorsi deve comparire subito dopo il catalogo indicatori comunale")
        require(order["metric"] > order["paths"],
                "Percorsi deve precedere il dato comunale selezionato")

        browser.close()

    print("Fisarmoniche verificate: nessuna sovrapposizione testo/strumenti; Percorsi visibile nel flusso Mobilità.")


if __name__ == "__main__":
    main()
