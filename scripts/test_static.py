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

        if path.name == "offline.html":
            assert "Sei offline" in text, "Messaggio della pagina offline assente"
            assert "Riprova" in text, "Azione di recupero della pagina offline assente"
            assert "assets/app-bundle.js" not in text, "La pagina offline non deve avviare l'app completa"
            assert 'rel="canonical"' not in text, "La pagina offline non deve essere indicizzabile come contenuto"
            continue

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

    bundle_path = DIST / "assets" / "app-bundle.js"
    assert bundle_path.stat().st_size > 50_000
    bundle = bundle_path.read_text(encoding="utf-8")
    assert bundle.count("useGrouping: 'always'") >= 4, "Raggruppamento delle migliaia non forzato"

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
        assert page.locator(".chart-y-label, .ux-history-axis-label").count() >= 3, "Valori dell'ordinata assenti"
        broken = page.evaluate("[...document.images].filter(img => !img.complete || img.naturalWidth === 0).map(img => img.src)")
        assert not broken, f"Immagini non caricate: {broken}"
        page.evaluate("window.scrollTo(0, 1500)")
        page.wait_for_timeout(100)
        header_box = page.locator("#site-header-mount").bounding_box()
        context_box = page.locator(".town-context-nav").bounding_box()
        theme_box = page.locator(".town-context-nav .theme-nav").bounding_box()
        assert header_box and abs(header_box["y"]) <= 1, f"Header non sticky: {header_box}"
        assert context_box and 68 <= context_box["y"] <= 72, f"Navigazione contestuale non sticky: {context_box}"
        assert theme_box, "Navigazione dei temi assente dalla barra contestuale"
        assert context_box["y"] <= theme_box["y"], "Navigazione temi sopra il contenitore sticky"
        assert theme_box["y"] + theme_box["height"] <= context_box["y"] + context_box["height"] + 2, (
            f"Navigazione temi fuori dal contenitore sticky: tema={theme_box}, contenitore={context_box}"
        )

        mobile = browser.new_context(viewport={"width": 390, "height": 844})
        mobile_page = mobile.new_page()
        mobile_page.goto(base, wait_until="networkidle")
        mobile_page.wait_for_selector(".global-search-trigger")
        hero_facts = mobile_page.locator(".hero-facts").inner_text()
        assert "115 INDICATORI" in hero_facts and "111 INDICATORI" not in hero_facts, (
            f"Conteggio complessivo degli indicatori errato in home: {hero_facts!r}"
        )
        mobile_icon = mobile_page.locator(".global-search-trigger .search-icon")
        assert mobile_icon.is_visible(), "Lente della ricerca non visibile su smartphone"
        icon_box = mobile_icon.bounding_box()
        assert icon_box and icon_box["width"] >= 17 and icon_box["height"] >= 17, f"Lente mobile troppo piccola: {icon_box}"
        assert mobile_page.locator(".global-search-trigger span").last.is_hidden(), "Testo Cerca non nascosto su smartphone"

        population_values = mobile_page.locator("#home-explorer .bar-row strong").all_text_contents()
        assert "6.550" in population_values, f"Separatore assente per 6550: {population_values}"
        assert "2.783" in population_values, f"Separatore assente per 2783: {population_values}"

        mobile_page.locator('.theme-card[data-theme="economia"]').click()
        mobile_page.wait_for_timeout(900)
        explorer = mobile_page.locator("#home-explorer")
        assert explorer.get_attribute("data-theme") == "economia", "Il pannello non è stato aggiornato sul tema scelto"
        explorer_top = explorer.bounding_box()["y"]
        header_height = mobile_page.locator("#site-header-mount").bounding_box()["height"]
        assert header_height + 5 <= explorer_top <= header_height + 30, f"Salto al confronto non allineato: {explorer_top}"

        mobile_page.goto(base + "comuni/massarosa/", wait_until="networkidle")
        mobile_page.locator('[data-profile-theme="economia"]').click()
        mobile_page.wait_for_timeout(900)
        town_topic = mobile_page.locator("#town-topic")
        assert town_topic.get_attribute("data-theme") == "economia", "Tema comunale non aggiornato"
        town_topic_top = town_topic.bounding_box()["y"]
        mobile_header_height = mobile_page.locator("#site-header-mount").bounding_box()["height"]
        mobile_context_height = mobile_page.locator(".town-context-nav").bounding_box()["height"]
        expected_top = mobile_header_height + mobile_context_height
        assert expected_top + 5 <= town_topic_top <= expected_top + 30, f"Salto ai dati comunali non allineato: {town_topic_top}"
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
