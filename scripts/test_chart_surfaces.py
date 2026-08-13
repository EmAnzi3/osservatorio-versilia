#!/usr/bin/env python3
"""Verifica la superficie grafica comune su tutte le famiglie di pagine."""
from __future__ import annotations

import contextlib
import json
import os
import socket
import threading
import unicodedata
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import quote

from playwright.sync_api import Locator, Page, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
DATA = json.loads((ROOT / "data" / "site-data.json").read_text(encoding="utf-8"))


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


def slug(value: str) -> str:
    normalized = unicodedata.normalize("NFD", value)
    normalized = "".join(char for char in normalized if unicodedata.category(char) != "Mn")
    out = []
    previous_dash = False
    for char in normalized.lower():
        if char.isalnum():
            out.append(char)
            previous_dash = False
        elif not previous_dash:
            out.append("-")
            previous_dash = True
    return "".join(out).strip("-")


def expected_surface(page: Page) -> str:
    return page.evaluate(
        """() => {
          const probe = document.createElement('div');
          probe.style.background = 'var(--surface)';
          document.body.appendChild(probe);
          const value = getComputedStyle(probe).backgroundColor;
          probe.remove();
          return value;
        }"""
    )


def surface_style(locator: Locator) -> dict:
    return locator.evaluate(
        """element => {
          const style = getComputedStyle(element);
          return {
            background: style.backgroundColor,
            borderWidth: style.borderTopWidth,
            borderStyle: style.borderTopStyle,
            radius: style.borderTopLeftRadius
          };
        }"""
    )


def px(value: str) -> float:
    try:
        return float(value.removesuffix("px"))
    except ValueError:
        return 0.0


def assert_surface(page: Page, selector: str, label: str, *, visible: bool = True) -> None:
    locator = page.locator(selector).first
    require(locator.count() == 1, f"{label}: contenitore grafico mancante ({selector})")
    if visible:
        require(locator.is_visible(), f"{label}: contenitore grafico non visibile")
    style = surface_style(locator)
    expected = expected_surface(page)
    require(
        style["background"] == expected,
        f"{label}: sfondo {style['background']} diverso da superficie {expected}",
    )
    require(
        style["borderStyle"] != "none" and px(style["borderWidth"]) >= 1,
        f"{label}: bordo del pannello assente: {style}",
    )
    require(px(style["radius"]) >= 10, f"{label}: raggio del pannello insufficiente: {style}")


def verify_stylesheet_is_global() -> None:
    pages = [path for path in DIST.rglob("*.html") if path.name != "offline.html"]
    require(pages, "Build priva di pagine HTML")
    missing = [
        str(path.relative_to(DIST))
        for path in pages
        if "assets/chart-surfaces.css" not in path.read_text(encoding="utf-8")
    ]
    require(not missing, f"Foglio grafici non caricato in {len(missing)} pagine: {missing[:8]}")


def verify_home(page: Page, base: str) -> None:
    page.goto(base, wait_until="networkidle")
    page.wait_for_selector(".explorer-chart")
    assert_surface(page, ".explorer-chart", "Home · confronto in evidenza")


def verify_all_theme_pages(page: Page, base: str) -> None:
    themes = DATA.get("themes", {})
    require(len(themes) == 11, f"Attesi 11 temi, trovati {len(themes)}")
    for theme_key, theme in themes.items():
        metrics = theme.get("metrics") or []
        require(metrics, f"Tema {theme_key}: nessun indicatore")
        metric = metrics[0]
        url = f"{base}confronta/{quote(theme_key)}/?indicatore={quote(metric)}"
        page.goto(url, wait_until="networkidle")
        page.wait_for_selector("#compare-bars .topic-bars")
        assert_surface(page, "#compare-bars .topic-bars", f"Tema {theme_key} · confronto corrente")


def verify_all_town_pages(page: Page, base: str) -> None:
    towns = DATA.get("towns", [])
    require(len(towns) == 7, f"Attesi 7 comuni, trovati {len(towns)}")
    for town in towns:
        town_slug = slug(town["name"])
        url = f"{base}comuni/{town_slug}/?tema=demografia&indicatore=population"
        page.goto(url, wait_until="networkidle")
        page.wait_for_selector(".history-panel")
        assert_surface(page, ".history-panel", f"Comune {town['name']} · pannello grafico")


def verify_history_variants(page: Page, base: str) -> None:
    # Reddito: due annualità, cioè lo stesso pannello mostrato nello screenshot di riferimento.
    page.goto(base + "confronta/economia/?indicatore=income", wait_until="networkidle")
    page.wait_for_selector("#compare-bars .ux-history-card", state="attached")
    assert_surface(
        page,
        "#compare-bars .ux-history-card",
        "Economia · confronto storico a due punti",
        visible=False,
    )

    # Popolazione: serie lunga a linee, per verificare anche l'altro renderer storico.
    page.goto(base + "confronta/demografia/?indicatore=population", wait_until="networkidle")
    page.wait_for_selector("#compare-bars .ux-history-card", state="attached")
    assert_surface(
        page,
        "#compare-bars .ux-history-card",
        "Demografia · serie storica a linee",
        visible=False,
    )
    page.locator('[data-view-mode="history"]').click()
    point = page.locator("#compare-bars .ux-history-chart .chart-point").last
    require(point.count() == 1, "Punto interattivo assente nello storico ordinario")
    require(point.locator("title").count() == 0, "Tooltip nativo del browser ancora presente")
    point.hover()
    tooltip = point.locator(".chart-tooltip")
    require(tooltip.is_visible(), "Tooltip grafico personalizzato non visibile")
    require("·" in (tooltip.text_content() or ""), "Tooltip privo di comune e anno")
    fill = tooltip.locator("rect").evaluate("element => getComputedStyle(element).fill")
    require(fill == "rgb(16, 47, 69)", f"Tooltip non allineato allo stile scuro del clima: {fill}")


def verify_economy_specials(page: Page, base: str) -> None:
    page.goto(base + "confronta/economia/?indicatore=localUnits", wait_until="networkidle")
    page.wait_for_selector(".ateco-panel")
    assert_surface(page, ".ateco-panel", "Economia · confronto ATECO")

    page.goto(base + "comuni/massarosa/?tema=economia&indicatore=localUnits", wait_until="networkidle")
    page.wait_for_selector(".ateco-town-detail")
    assert_surface(page, ".ateco-town-detail", "Massarosa · dettaglio ATECO")

    disclosure = page.locator(".topic-deep-dive .detail-disclosure").first
    if disclosure.count() == 1:
        summary = disclosure.locator(":scope > summary")
        if disclosure.get_attribute("open") is None:
            summary.click()
        page.wait_for_selector(".topic-deep-dive .deep-bar-list", state="visible")
        assert_surface(page, ".topic-deep-dive .deep-bar-list", "Massarosa · barre struttura economica")


def main() -> None:
    verify_stylesheet_is_global()

    chromium_path = os.environ.get("CHROMIUM_PATH")
    launch_args: dict[str, object] = {"headless": True}
    if chromium_path:
        launch_args["executable_path"] = chromium_path

    with server(DIST) as base, sync_playwright() as p:
        browser = p.chromium.launch(**launch_args)
        context = browser.new_context(viewport={"width": 1440, "height": 1000})
        page = context.new_page()
        errors: list[str] = []
        page.on("pageerror", lambda error: errors.append(str(error)))

        verify_home(page, base)
        verify_all_theme_pages(page, base)
        verify_all_town_pages(page, base)
        verify_history_variants(page, base)
        verify_economy_specials(page, base)

        require(not errors, f"Errori JavaScript durante audit superfici grafiche: {errors}")
        context.close()
        browser.close()

    print("Superfici grafiche verificate: home, 11 temi, 7 comuni, storico a due punti/linee e pannelli ATECO.")


if __name__ == "__main__":
    main()
