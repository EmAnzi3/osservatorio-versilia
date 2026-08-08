#!/usr/bin/env python3
"""Controlli UX su fisarmoniche comparative e storico comunale lineare."""
from __future__ import annotations

import contextlib
import json
import os
import socket
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Iterable

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
DATA = ROOT / "data" / "site-data.json"


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


def common_years(metric: dict) -> list[str]:
    sets: list[set[str]] = []
    for row in metric.get("rows", []):
        series = row.get("series") or {}
        years = series.get("years") or []
        values = series.get("values") or []
        valid = {
            str(year)
            for year, value in zip(years, values, strict=False)
            if isinstance(value, (int, float))
        }
        sets.append(valid)
    if not sets:
        return []
    return sorted(set.intersection(*sets), key=lambda value: int(value))


def static_assertions(data: dict) -> int:
    for name in ("ux-experiment.css", "ux-accordion.js", "ux-history-core.js", "ux-history.js"):
        require((DIST / "assets" / name).exists(), f"Asset UX mancante: {name}")

    comparable = {
        key: common_years(metric)
        for key, metric in data["metrics"].items()
        if len(common_years(metric)) >= 2
    }
    require(len(comparable) >= 20, "Troppo pochi indicatori dispongono di uno storico comparabile")
    require(len(comparable.get("currentRevenueAccruedPerResident", [])) >= 7,
            "I bilanci devono offrire una serie storica estesa con copertura 7/7")
    require(len(comparable.get("population", [])) >= 3,
            "La popolazione deve offrire una serie storica estesa")

    for label, path in {
        "bilanci": DIST / "confronta" / "bilanci" / "index.html",
        "massarosa": DIST / "comuni" / "massarosa" / "index.html",
    }.items():
        require(path.exists(), f"Pagina non generata: {label}")
        text = path.read_text(encoding="utf-8")
        for token in ("assets/ux-experiment.css", "assets/ux-accordion.js", "assets/ux-history-core.js", "assets/ux-history.js"):
            require(token in text, f"{label}: manca il collegamento a {token}")

    return len(comparable)


def browser_assertions() -> None:
    chromium_path = os.environ.get("CHROMIUM_PATH")
    launch_args: dict[str, object] = {"headless": True}
    if chromium_path:
        launch_args["executable_path"] = chromium_path

    with server(DIST) as base, sync_playwright() as playwright:
        browser = playwright.chromium.launch(**launch_args)
        page = browser.new_page(viewport={"width": 1440, "height": 950})

        # Le pagine di confronto mantengono il selettore Valore attuale / Storico.
        page.goto(base + "confronta/bilanci/", wait_until="networkidle")
        page.wait_for_selector(".ux-view-shell")
        require(not page.locator('[data-view-mode="history"]').is_disabled(),
                "Percorso pubblico Bilanci: vista storica disabilitata sul primo indicatore")
        page.locator('[data-view-mode="history"]').click()
        require(page.locator('.ux-view-pane[data-view-pane="history"]').is_visible(),
                "Percorso pubblico Bilanci: vista storica non attivabile")

        page.evaluate("sessionStorage.clear()")
        page.goto(base + "confronta/bilanci/?indicatore=currentRevenueAccruedPerResident", wait_until="networkidle")
        page.wait_for_selector(".ux-view-shell")
        require(page.locator(".topic-controls .ux-section-toggle").count() >= 4,
                "Bilanci: sezioni espandibili non installate")
        require(page.locator('[data-view-mode="current"].active').count() == 1,
                "Bilanci: vista attuale non selezionata inizialmente")
        current_background = page.locator(".topic-bars").evaluate("el => getComputedStyle(el).backgroundColor")
        page.locator('[data-view-mode="history"]').click()
        history_background = page.locator(".ux-history-card").evaluate("el => getComputedStyle(el).backgroundColor")
        require(history_background == current_background,
                f"Sfondo storico diverso dal pannello attuale: {history_background} != {current_background}")
        require(page.locator(".ux-series-group").count() == 7,
                "Bilanci: lo storico esteso non contiene sette serie comunali")
        require("Andamento 2019–2025" in page.locator(".ux-history-head").inner_text(),
                "Bilanci: intervallo storico esteso non riconosciuto")
        page.locator('[data-history-select="massarosa"]').click()
        require(page.locator('.ux-series-group[data-history-town="massarosa"].is-selected').count() == 1,
                "Bilanci: selezione di Massarosa non applicata")

        page.goto(base + "confronta/economia/?indicatore=income", wait_until="networkidle")
        page.wait_for_selector(".ux-view-shell")
        page.locator('[data-view-mode="history"]').click()
        require(page.locator(".ux-two-point-row").count() == 7,
                "Economia: confronto a due punti incompleto")
        require("Confronto a due punti 2023–2024" in page.locator(".ux-history-head").inner_text(),
                "Economia: intervallo a due punti non riconosciuto")

        page.goto(base + "confronta/bilanci/?indicatore=rigidExpenditureShare", wait_until="networkidle")
        page.wait_for_selector(".ux-view-shell")
        require(page.locator('[data-view-mode="history"]').is_disabled(),
                "Spese rigide: la vista storica deve restare disabilitata")

        # La scheda comunale mostra direttamente la serie del solo Comune aperto.
        page.goto(base + "comuni/massarosa/?tema=demografia&indicatore=population", wait_until="networkidle")
        page.wait_for_selector(".town-history-panel")
        require(page.locator(".town-history-panel .ux-view-shell").count() == 0,
                "Scheda comunale: il vecchio selettore attuale/storico non deve essere installato")
        require(page.locator(".town-history-panel .comparison-bars").count() == 0,
                "Scheda comunale: il confronto a sette Comuni è duplicato nello storico")
        require(page.locator(".town-history-panel .trend-chart").count() == 1,
                "Scheda comunale: serie storica del Comune non renderizzata")
        require(page.locator(".town-history-panel .chart-point").count() >= 3,
                "Scheda comunale: serie della popolazione troppo corta")

        mobile = browser.new_context(viewport={"width": 390, "height": 844})
        mobile_page = mobile.new_page()
        mobile_page.goto(base + "confronta/bilanci/?indicatore=currentRevenueAccruedPerResident", wait_until="networkidle")
        mobile_page.wait_for_selector(".ux-section-toggle")
        visible_groups = mobile_page.locator(".topic-controls .metric-group-buttons:not([hidden])")
        require(visible_groups.count() == 1,
                f"Mobile confronto: deve essere aperta una sola sezione, trovate {visible_groups.count()}")
        mobile_page.locator('[data-view-mode="history"]').click()
        require(mobile_page.locator(".ux-series-group").count() == 7,
                "Mobile: storico esteso dei bilanci incompleto")
        widths = mobile_page.evaluate("({client: document.documentElement.clientWidth, scroll: document.documentElement.scrollWidth})")
        require(widths["scroll"] <= widths["client"], f"Mobile confronto: overflow orizzontale {widths}")
        require("€" in mobile_page.locator(".ux-history-card").inner_text(),
                "Mobile: unità monetaria assente nello storico")
        headings = mobile_page.locator(".topic-controls .ux-section-toggle")
        headings.nth(1).click()
        require(visible_groups.count() == 1,
                "Mobile confronto: l’apertura di una sezione non ha chiuso la precedente")

        mobile_page.goto(base + "comuni/massarosa/?tema=demografia&indicatore=population", wait_until="networkidle")
        mobile_page.wait_for_selector(".town-history-panel")
        widths = mobile_page.evaluate("({client: document.documentElement.clientWidth, scroll: document.documentElement.scrollWidth})")
        require(widths["scroll"] <= widths["client"], f"Mobile scheda comunale: overflow orizzontale {widths}")
        chart_shell = mobile_page.locator(".town-history-panel .chart-shell")
        require(chart_shell.count() == 1, "Mobile scheda comunale: grafico storico assente")
        require(chart_shell.evaluate("el => el.scrollWidth >= el.clientWidth"),
                "Mobile scheda comunale: contenitore del grafico storico non valido")
        require(mobile_page.locator(".town-history-panel .chart-point").count() >= 3,
                "Mobile scheda comunale: punti della serie incompleti")
        mobile.close()
        browser.close()


def main() -> None:
    data = json.loads(DATA.read_text(encoding="utf-8"))
    comparable_count = static_assertions(data)
    browser_assertions()
    print(
        "UX validata: fisarmoniche e storico comparato nelle pagine di confronto; "
        f"storico comunale lineare; {comparable_count} indicatori con serie omogenee."
    )


if __name__ == "__main__":
    main()
