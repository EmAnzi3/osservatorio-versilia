#!/usr/bin/env python3
"""Regression tests for the pre-rendered static build."""

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


def static_assertions() -> None:
    html_files = sorted(DIST.rglob("*.html"))
    assert len(html_files) >= 20, f"Pagine HTML insufficienti: {len(html_files)}"
    for path in html_files:
        text = path.read_text(encoding="utf-8")
        assert "app-loading" not in text, f"Skeleton residuo: {path}"
        assert "127.0.0.1" not in text, f"URL temporaneo serializzato: {path}"
        assert re.search(r"<h1[ >]", text, re.I), f"H1 assente: {path}"
        assert 'rel="canonical"' in text, f"Canonical assente: {path}"
        assert 'type="application/ld+json"' in text, f"JSON-LD assente: {path}"
        assert "app-parts/" not in text, f"Riferimento ai moduli .txt: {path}"
        assert "assets/app.js" not in text, f"Vecchio loader presente: {path}"
        assert "assets/app-bundle.js" in text, f"Bundle assente: {path}"
        assert "assets/fonts.css" in text, f"Font Geist non collegato: {path}"
        assert "search-icon" in text, f"Icona vettoriale della ricerca assente: {path}"

    massarosa = (DIST / "comuni" / "massarosa" / "index.html").read_text(encoding="utf-8")
    assert "Massarosa" in massarosa
    assert "Fonte" in massarosa or "fonte" in massarosa
    assert (DIST / "sitemap.xml").exists()
    assert (DIST / "assets" / "app-bundle.js").stat().st_size > 50_000
    fonts_css = (DIST / "assets" / "fonts.css").read_text(encoding="utf-8")
    assert "./fonts/geist-latin.woff2" in fonts_css
    assert "cdn.jsdelivr.net" not in fonts_css


def browser_assertions() -> None:
    chromium_path = os.environ.get("CHROMIUM_PATH")
    launch_args = {"headless": True}
    if chromium_path:
        launch_args["executable_path"] = chromium_path

    with server(DIST) as base, sync_playwright() as p:
        browser = p.chromium.launch(**launch_args)

        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.goto(base + "comuni/massarosa/?tema=demografia&indicatore=population", wait_until="networkidle")
        page.wait_for_selector(".town-profile")
        page.wait_for_timeout(200)
        assert page.locator("h1").first.text_content().strip() == "Massarosa"
        assert "Geist" in page.evaluate("getComputedStyle(document.body).fontFamily"), "Font Geist non applicato"
        assert page.evaluate("document.fonts.check('16px Geist')"), "File del font Geist non caricato"
        assert page.locator(".global-search-trigger .search-icon").is_visible(), "Lente desktop assente"
        assert page.locator(".chart-y-label").count() >= 3, "Valori dell'ordinata assenti"
        broken = page.evaluate("[...document.images].filter(img => !img.complete || img.naturalWidth === 0).map(img => img.src)")
        assert not broken, f"Immagini non caricate: {broken}"
        page.evaluate("window.scrollTo(0, 1500)")
        page.wait_for_timeout(100)
        header_top = page.locator("#site-header-mount").bounding_box()["y"]
        nav_top = page.locator(".town-profile .theme-nav").bounding_box()["y"]
        assert abs(header_top) <= 1, f"Header non sticky: {header_top}"
        assert 68 <= nav_top <= 72, f"Navigazione temi non sticky: {nav_top}"

        mobile = browser.new_context(viewport={"width": 390, "height": 844})
        mobile_page = mobile.new_page()
        mobile_page.goto(base, wait_until="networkidle")
        mobile_page.wait_for_selector(".global-search-trigger")
        mobile_icon = mobile_page.locator(".global-search-trigger .search-icon")
        assert mobile_icon.is_visible(), "Lente della ricerca non visibile su smartphone"
        icon_box = mobile_icon.bounding_box()
        assert icon_box and icon_box["width"] >= 17 and icon_box["height"] >= 17, f"Lente mobile troppo piccola: {icon_box}"
        assert mobile_page.locator(".global-search-trigger span").last.is_hidden(), "Testo Cerca non nascosto su smartphone"
        mobile.close()

        no_js = browser.new_context(java_script_enabled=False, viewport={"width": 1280, "height": 900})
        no_js_page = no_js.new_page()
        no_js_page.goto(base + "comuni/massarosa/", wait_until="networkidle")
        assert no_js_page.locator("h1").first.text_content().strip() == "Massarosa"
        assert no_js_page.locator("#app main").count() == 1
        assert "Caricamento dei dati" not in no_js_page.locator("body").inner_text()
        no_js_broken = no_js_page.evaluate("[...document.images].filter(img => !img.complete || img.naturalWidth === 0).map(img => img.src)")
        assert not no_js_broken, f"Immagini rotte senza JavaScript: {no_js_broken}"
        no_js.close()
        browser.close()


def main() -> None:
    static_assertions()
    browser_assertions()
    print("Tutti i test del build statico sono superati.")


if __name__ == "__main__":
    main()
