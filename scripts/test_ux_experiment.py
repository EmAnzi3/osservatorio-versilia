#!/usr/bin/env python3
"""Controlli dell’esperimento UX su sezioni e serie storiche comparative."""
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
    for name in (
        "ux-experiment.css",
        "ux-accordion.js",
        "ux-history-core.js",
        "ux-history.js",
    ):
        require((DIST / "assets" / name).exists(), f"Asset UX mancante: {name}")

    comparable = {
        key: common_years(metric)
        for key, metric in data["metrics"].items()
        if len(common_years(metric)) >= 2
    }
    require(len(comparable) >= 20, "Troppo pochi indicatori dispongono di uno storico comparabile")
    require(len(comparable.get("currentRevenueAccruedPerResident", [])) == 2,
            "I bilanci devono offrire il confronto 2024–2025")
    require(len(comparable.get("population", [])) >= 3,
            "La popolazione deve offrire una serie storica estesa")

    for label, path in {
        "bilanci": DIST / "confronta" / "bilanci" / "index.html",
        "massarosa": DIST / "comuni" / "massarosa" / "index.html",
    }.items():
        require(path.exists(), f"Pagina non generata: {label}")
        text = path.read_text(encoding="utf-8")
        for token in (
            "assets/ux-experiment.css",
            "assets/ux-accordion.js",
            "assets/ux-history-core.js",
            "assets/ux-history.js",
        ):
            require(token in text, f"{label}: manca il collegamento a {token}")

    return len(comparable)


def browser_assertions() -> None:
    chromium_path = os.environ.get("CHROMIUM_PATH")
    launch_args = {"headless": True}
    if chromium_path:
        launch_args["executable_path"] = chromium_path

    with server(DIST) as base, sync_playwright() as playwright:
        browser = playwright.chromium.launch(**launch_args)

        page = browser.new_page(viewport={"width": 1440, "height": 950})
        page.goto(
            base + "confronta/bilanci/?indicatore=currentRevenueAccruedPerResident",
            wait_until="networkidle",
        )
        page.wait_for_selector(".ux-view-shell")
        require(page.locator(".ux-section-toggle").count() >= 4,
                "Bilanci: sezioni espandibili non installate")
        require(page.locator('[data-view-mode="current"].active').count() == 1,
                "Bilanci: vista attuale non selezionata inizialmente")
        page.locator('[data-view-mode="history"]').click()
        require(page.locator('[data-view-mode="history"].active').count() == 1,
                "Bilanci: selettore storico non attivato")
        require(page.locator('.ux-view-pane[data-view-pane="history"]').is_visible(),
                "Bilanci: pannello storico non visibile")
        require(page.locator(".ux-two-point-row").count() == 7,
                "Bilanci: il confronto a due punti non contiene sette Comuni")
        require("Confronto a due punti 2024–2025" in page.locator(".ux-history-head").inner_text(),
                "Bilanci: confronto a due anni non riconosciuto")
        page.locator('[data-history-select="massarosa"]').click()
        require(page.locator('.ux-two-point-row[data-history-town="massarosa"].is-selected').count() == 1,
                "Bilanci: selezione di Massarosa non applicata")

        page.goto(
            base + "comuni/massarosa/?tema=demografia&indicatore=population",
            wait_until="networkidle",
        )
        page.wait_for_selector(".history-panel .ux-view-shell")
        require(page.locator(".history-panel .ux-bar-row").count() == 7,
                "Scheda comunale: confronto attuale non contiene sette comuni")
        page.locator('.history-panel [data-view-mode="history"]').click()
        require(page.locator(".history-panel .ux-series-group").count() == 7,
                "Scheda comunale: storico comparato incompleto")
        require(page.locator('.history-panel .ux-series-group[data-history-town="massarosa"].is-selected').count() == 1,
                "Scheda comunale: comune aperto non evidenziato")

        mobile = browser.new_context(viewport={"width": 390, "height": 844})
        mobile_page = mobile.new_page()
        mobile_page.goto(
            base + "confronta/bilanci/?indicatore=currentRevenueAccruedPerResident",
            wait_until="networkidle",
        )
        mobile_page.wait_for_selector(".ux-section-toggle")
        visible_groups = mobile_page.locator(".topic-controls .metric-group-buttons:not([hidden])")
        require(visible_groups.count() == 1,
                f"Mobile: devono essere aperte una sola sezione, trovate {visible_groups.count()}")
        mobile_page.locator('[data-view-mode="history"]').click()
        require(mobile_page.locator(".ux-two-point-row").count() == 7,
                "Mobile: confronto a due punti incompleto")
        widths = mobile_page.evaluate("({client: document.documentElement.clientWidth, scroll: document.documentElement.scrollWidth})")
        require(widths["scroll"] <= widths["client"],
                f"Mobile: overflow orizzontale della pagina {widths}")
        require("€" in mobile_page.locator(".ux-history-card").inner_text(),
                "Mobile: unità monetaria assente nello storico")
        headings = mobile_page.locator(".topic-controls .ux-section-toggle")
        require(headings.count() >= 2, "Mobile: sezioni insufficienti per il test")
        headings.nth(1).click()
        require(visible_groups.count() == 1,
                "Mobile: l’apertura di una sezione non ha chiuso la precedente")

        mobile_page.goto(
            base + "comuni/massarosa/?tema=demografia&indicatore=population",
            wait_until="networkidle",
        )
        mobile_page.wait_for_selector(".history-panel .ux-view-shell")
        mobile_page.locator('.history-panel [data-view-mode="history"]').click()
        widths = mobile_page.evaluate("({client: document.documentElement.clientWidth, scroll: document.documentElement.scrollWidth})")
        require(widths["scroll"] <= widths["client"],
                f"Mobile storico lungo: overflow orizzontale della pagina {widths}")
        scroll = mobile_page.locator(".history-panel .ux-history-scroll")
        require(scroll.evaluate("el => el.scrollWidth > el.clientWidth"),
                "Mobile storico lungo: il grafico non scorre nel proprio contenitore")
        require(mobile_page.locator(".history-panel .ux-series-group").count() == 7,
                "Mobile storico lungo: serie comunali incomplete")
        mobile.close()
        browser.close()


def main() -> None:
    data = json.loads(DATA.read_text(encoding="utf-8"))
    comparable_count = static_assertions(data)
    browser_assertions()
    print(
        "Esperimento UX validato: sezioni espandibili, vista attuale e storico comparato "
        f"su {comparable_count} indicatori."
    )


if __name__ == "__main__":
    main()
