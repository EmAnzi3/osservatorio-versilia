#!/usr/bin/env python3
"""Checks for the v1.8 comparison grammar and reduced ranking emphasis."""

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


def static_checks() -> None:
    home = (DIST / "index.html").read_text(encoding="utf-8")
    massarosa = (DIST / "comuni" / "massarosa" / "index.html").read_text(encoding="utf-8")
    project = (DIST / "progetto" / "index.html").read_text(encoding="utf-8")

    assert "assets/visual-grammar.css" in home
    assert "assets/visual-grammar.js" in home
    assert "comparison-legend" in home, "Confronto prerenderizzato senza nuova grammatica"
    assert "bar-rank" not in home, "Numerazione ordinale ancora presente nel confronto home"
    assert "Differenze, non podi" in home
    assert "Rispetto alla Versilia" in massarosa
    assert "Ordine del valore" not in massarosa
    assert "° valore" not in massarosa
    assert "pagelle, podi o giudizi politici automatici" in project


def browser_checks() -> None:
    chromium_path = os.environ.get("CHROMIUM_PATH")
    launch_args = {"headless": True}
    if chromium_path:
        launch_args["executable_path"] = chromium_path

    with server(DIST) as base, sync_playwright() as p:
        browser = p.chromium.launch(**launch_args)
        page = browser.new_page(viewport={"width": 1280, "height": 900})

        page.goto(base, wait_until="networkidle")
        page.wait_for_selector("#home-explorer .comparison-dot")
        assert page.locator("#home-explorer .bar-rank").count() == 0
        assert page.locator("#home-explorer .comparison-dot").count() == 7
        assert page.locator("#home-explorer .comparison-reference").count() == 7
        assert page.locator("#home-explorer .comparison-note").count() == 1

        page.goto(base + "confronta/demografia/?indicatore=share65", wait_until="networkidle")
        page.wait_for_selector("#compare-bars .comparison-dot")
        assert page.locator("#compare-bars .comparison-bars").get_attribute("data-viz") == "percent-dotplot"
        axis_text = page.locator("#compare-bars .comparison-axis").inner_text().lower()
        assert "scala 0–100%" in axis_text
        assert "%" in axis_text

        page.goto(base + "comuni/massarosa/?tema=demografia&indicatore=share65", wait_until="networkidle")
        page.wait_for_selector(".versilia-position")
        assert page.locator(".versilia-position .overline").inner_text().strip() == "Rispetto alla Versilia"
        assert "su 7" not in page.locator(".versilia-position").inner_text()
        assert "punti" in page.locator(".versilia-position").inner_text(), "Scostamento percentuale non espresso in punti"
        card_notes = page.locator(".indicator-card-grid button small").all_text_contents()
        assert card_notes and all("° valore" not in text for text in card_notes)

        browser.close()


def main() -> None:
    static_checks()
    browser_checks()
    print("Grammatica visuale v1.8 verificata.")


if __name__ == "__main__":
    main()
