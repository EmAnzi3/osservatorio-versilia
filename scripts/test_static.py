#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from urllib.request import urlopen

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"


def run(command: list[str]) -> None:
    subprocess.run(command, cwd=ROOT, check=True)


def wait_http(url: str, attempts: int = 40) -> None:
    last_error: Exception | None = None
    for _ in range(attempts):
        try:
            with urlopen(url, timeout=1) as response:
                if response.status < 500:
                    return
        except Exception as exc:  # pragma: no cover - retry helper
            last_error = exc
        time.sleep(0.25)
    raise RuntimeError(f"Server non disponibile: {url}: {last_error}")


def static_assertions() -> None:
    assert DIST.exists(), "Build dist assente"
    html_pages = list(DIST.rglob("*.html"))
    assert html_pages, "Nessuna pagina HTML nella build"
    for path in html_pages:
        text = path.read_text(encoding="utf-8")
        assert "app-loading" not in text, f"Skeleton residuo: {path.relative_to(DIST)}"
        assert '<html lang="it"' in text, f"Lingua assente: {path.relative_to(DIST)}"
        assert '<meta name="viewport"' in text, f"Viewport assente: {path.relative_to(DIST)}"


def browser_assertions() -> None:
    server = subprocess.Popen(
        [sys.executable, "scripts/preview_dist.py", "--port", "8124", "--directory", "dist"],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        base = "http://127.0.0.1:8124/"
        wait_http(base)
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": 1440, "height": 1000})
            page.goto(base, wait_until="networkidle")
            page.wait_for_selector(".global-search-trigger")
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
            public_catalog = json.loads((DIST / "data" / "site-data.json").read_text(encoding="utf-8"))
            expected_indicator_count = len(public_catalog["metrics"]) + len(public_catalog.get("specialExplorers", {}))
            assert f"{expected_indicator_count} INDICATORI" in hero_facts, (
                f"Conteggio complessivo degli indicatori errato in home: attesi {expected_indicator_count}, trovato {hero_facts!r}"
            )
            mobile_icon = mobile_page.locator(".global-search-trigger .search-icon")
            assert mobile_icon.is_visible(), "Lente della ricerca non visibile su smartphone"
            icon_box = mobile_icon.bounding_box()
            assert icon_box and icon_box["width"] >= 17 and icon_box["height"] >= 17, f"Lente mobile troppo piccola: {icon_box}"
            assert mobile_page.locator(".global-search-trigger span").last.is_hidden(), "Testo Cerca non nascosto su smartphone"

            population_values = mobile_page.locator("#home-explorer .bar-row strong").all_text_contents()
            assert "6.550" in population_values, f"Separatore assente per 6550: {population_values}"
            assert "2.783" in population_values, f"Separatore assente per 2783: {population_values}"

            mobile_page.click('.theme-card[data-theme="economia"]')
            mobile_page.wait_for_timeout(80)
            economy_card = mobile_page.locator('.theme-card[data-theme="economia"] .theme-card-meta').inner_text()
            assert "32 indicatori" in economy_card, f"Conteggio Economia non aggiornato: {economy_card!r}"

            mobile_page.click('.global-search-trigger')
            mobile_page.fill('.global-search-dialog input[type="search"]', 'atlante attività economiche')
            mobile_page.wait_for_timeout(100)
            atlas_result = mobile_page.locator('.global-search-results a', has_text='Atlante delle attività economiche')
            assert atlas_result.count() == 1, "Atlante assente dalla ricerca globale"
            href = atlas_result.get_attribute('href') or ''
            assert "confronta/economia/atlante-attivita-economiche/" in href, f"Route Atlante errata nella ricerca: {href!r}"

            browser.close()
    finally:
        server.terminate()
        try:
            server.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server.kill()


def main() -> None:
    static_assertions()
    browser_assertions()
    print("Tutti i test del build statico sono superati.")


if __name__ == "__main__":
    main()
