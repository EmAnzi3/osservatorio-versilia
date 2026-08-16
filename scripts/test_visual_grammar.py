#!/usr/bin/env python3
"""Checks for the v1.8 comparison grammar and territorial reading scale."""

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
    visual_css = (ROOT / "assets" / "visual-grammar.css").read_text(encoding="utf-8")

    assert "assets/visual-grammar.css" in home
    assert "assets/visual-grammar.js" in home
    assert "comparison-legend" in home, "Confronto prerenderizzato senza nuova grammatica"
    assert "bar-rank" not in home, "Numerazione ordinale ancora presente nel confronto home"
    assert "Differenze, non podi" in home
    assert "Il Comune non è sempre il sistema" in home
    assert "Comune e sistema territoriale" in home
    assert "Quota sulla Versilia" in massarosa
    assert "13,7%" in massarosa
    assert "della popolazione versiliese" in massarosa
    assert "Scala di lettura" in massarosa
    assert "Ordine del valore" not in massarosa
    assert "° valore" not in massarosa
    assert "pagelle, podi o giudizi politici automatici" in project
    assert "Sette amministrazioni, un territorio interdipendente" in project
    assert "Basi numeriche diverse" in project
    assert "Viareggio e Stazzema" in project

    # Regressioni qualitative: nessun significato cromatico assegnato alla
    # posizione in elenco e riferimento Versilia promosso nella gerarchia.
    assert ".bar-row:nth-child(-n+2) .bar-fill" in visual_css
    assert "background: var(--theme-color, var(--sage));" in visual_css
    assert ".indicator-definition dl div:last-child dd" in visual_css
    assert ".versilia-position > div b" in visual_css


def assert_reading_scale(page, expected: str) -> None:
    scale = page.locator(".reading-scale").first
    scale.wait_for(state="visible")
    label = scale.locator("strong").inner_text().strip().lower()
    assert label == expected.lower(), f"Scala inattesa: {label!r}, attesa {expected!r}"


def assert_post_benchmark_tools(page, town: bool = False) -> None:
    selectors = {
        "benchmark": "#town-topic > .town-benchmark" if town else "#compare-benchmark",
        "method": "#town-topic > .method-disclosure" if town else "#compare-tools > .method-disclosure",
        "scale": "#town-topic > .reading-scale" if town else "#compare-tools > .reading-scale",
        "actions": "#town-topic > .town-data-actions" if town else "#compare-tools > .data-actions",
    }
    result = page.evaluate(
        """selectors => {
          const nodes = Object.fromEntries(
            Object.entries(selectors).map(([key, selector]) => [key, document.querySelector(selector)])
          );
          const order = ['benchmark', 'method', 'scale', 'actions'];
          return {
            present: Object.fromEntries(Object.entries(nodes).map(([key, node]) => [key, Boolean(node)])),
            ordered: order.slice(0, -1).every((key, index) =>
              Boolean(nodes[key]?.compareDocumentPosition(nodes[order[index + 1]]) & Node.DOCUMENT_POSITION_FOLLOWING)
            ),
          };
        }""",
        selectors,
    )
    assert all(result["present"].values()), f"Blocchi post-confronto mancanti: {result}"
    assert result["ordered"], f"Ordine post-confronto errato: {result}"


def assert_uniform_comparison_color(page, selector: str) -> None:
    colors = page.locator(selector).evaluate_all(
        "els => els.map(el => getComputedStyle(el).backgroundColor)"
    )
    assert len(colors) == 7, f"Attesi 7 segni comunali, trovati {len(colors)}"
    assert len(set(colors)) == 1, f"Colori comunali non uniformi: {colors}"


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
        assert page.locator(".system-reading-link").count() == 1
        assert_uniform_comparison_color(page, "#home-explorer .comparison-dot")

        page.goto(base + "comuni/massarosa/?tema=demografia&indicatore=population", wait_until="networkidle")
        page.wait_for_selector(".versilia-position")
        population_overline = page.locator(".versilia-position .overline").inner_text().strip().lower()
        assert population_overline == "quota sulla versilia", f"Etichetta popolazione inattesa: {population_overline!r}"
        population_text = page.locator(".versilia-position").inner_text().lower()
        assert "13,7%" in population_text, f"Quota popolazione Massarosa inattesa: {population_text!r}"
        assert "della popolazione versiliese" in population_text
        assert "sopra la versilia" not in population_text
        assert "sotto la versilia" not in population_text
        assert page.locator(".metric-switch.metric-catalog").count() == 1
        assert page.locator(".all-indicators, .indicator-groups").count() == 0
        assert page.locator('[data-metric="population"]').count() == 1
        assert_reading_scale(page, "Territoriale")

        page.goto(base + "confronta/istruzione/?indicatore=diplomaPlus", wait_until="networkidle")
        page.wait_for_selector("#compare-bars .comparison-dot")
        assert page.locator("#compare-bars .comparison-bars").get_attribute("data-viz") == "percent-dotplot"
        axis_text = page.locator("#compare-bars .comparison-axis").inner_text().lower()
        assert "scala 0–100%" in axis_text
        assert "%" in axis_text
        assert_reading_scale(page, "Territoriale")
        assert_post_benchmark_tools(page)

        page.goto(base + "confronta/economia/?indicatore=businessValueAdded", wait_until="networkidle")
        page.wait_for_selector("#compare-bars .comparison-dot")
        assert_reading_scale(page, "Funzionale")
        scale_text = page.locator(".reading-scale").inner_text().lower()
        assert "supera strutturalmente i confini comunali" in scale_text

        page.goto(base + "confronta/bilanci/?indicatore=currentExpenditureCommittedPerResident", wait_until="networkidle")
        page.wait_for_selector("#compare-bars .comparison-dot")
        assert_reading_scale(page, "Amministrativo")

        # Temi misti: la scala dipende dall'indicatore, non solo dal tema.
        page.goto(base + "confronta/salute/?indicatore=lifeExpectancy", wait_until="networkidle")
        assert_reading_scale(page, "Territoriale")
        page.goto(base + "confronta/salute/?indicatore=hospitals", wait_until="networkidle")
        assert_reading_scale(page, "Funzionale")

        page.goto(base + "confronta/istruzione/?indicatore=diplomaPlus", wait_until="networkidle")
        assert_reading_scale(page, "Territoriale")
        page.goto(base + "confronta/istruzione/?indicatore=schoolSites", wait_until="networkidle")
        assert_reading_scale(page, "Funzionale")

        page.goto(base + "confronta/mobilita/?indicatore=outsideMunicipality", wait_until="networkidle")
        assert_reading_scale(page, "Funzionale")
        page.goto(base + "confronta/mobilita/?indicatore=ftthCoverageDesi", wait_until="networkidle")
        assert_reading_scale(page, "Territoriale")

        # Il composito Sicurezza deve usare la stessa grammatica: niente podio
        # implicito, tutti i Comuni col colore del tema e Versilia ben leggibile.
        page.goto(base + "confronta/sicurezza/?indicatore=roadSafety", wait_until="networkidle")
        page.wait_for_selector("#compare-bars .comparison-dot")
        assert page.locator("#compare-bars .bar-rank").count() == 0
        assert_uniform_comparison_color(page, "#compare-bars .comparison-dot")
        reference_opacity = float(
            page.locator("#compare-bars .comparison-reference").first.evaluate(
                "el => getComputedStyle(el).opacity"
            )
        )
        assert reference_opacity >= 0.7, f"Riferimento Versilia troppo debole: {reference_opacity}"
        summary = page.locator(".indicator-definition dl div:last-child")
        assert "versilia" in summary.inner_text().lower()
        summary_value_size = float(
            summary.locator("dd").evaluate("el => parseFloat(getComputedStyle(el).fontSize)")
        )
        assert summary_value_size >= 16, f"Valore Versilia poco evidente: {summary_value_size}px"

        page.goto(base + "comuni/massarosa/?tema=economia&indicatore=businessValueAdded", wait_until="networkidle")
        page.wait_for_selector(".town-metric-layout")
        assert_reading_scale(page, "Funzionale")
        assert_post_benchmark_tools(page, town=True)

        page.goto(base + "comuni/massarosa/?tema=istruzione&indicatore=diplomaPlus", wait_until="networkidle")
        page.wait_for_selector(".versilia-position")
        overline_text = page.locator(".versilia-position .overline").inner_text().strip().lower()
        assert overline_text == "rispetto alla versilia", f"Etichetta inattesa: {overline_text!r}"
        position_text = page.locator(".versilia-position").inner_text().lower()
        assert "su 7" not in position_text
        assert "punti" in position_text, "Scostamento percentuale non espresso in punti"
        assert page.locator(".all-indicators, .indicator-groups").count() == 0
        assert page.locator('[data-metric="diplomaPlus"]').count() == 1
        town_reference = page.locator(".versilia-position > div")
        assert "versilia" in town_reference.inner_text().lower()
        town_reference_size = float(
            town_reference.locator("b").evaluate("el => parseFloat(getComputedStyle(el).fontSize)")
        )
        assert town_reference_size >= 18, f"Riferimento Versilia comunale troppo piccolo: {town_reference_size}px"

        page.goto(base + "progetto/", wait_until="networkidle")
        page.wait_for_selector("#sistema-territoriale")
        assert page.locator("#sistema-territoriale .system-reading-grid article").count() == 3
        assert page.locator(".base-size-principle").count() == 1
        project_text = page.locator("#sistema-territoriale").inner_text().lower()
        assert "viareggio e stazzema" in project_text
        assert "sistema produttivo" in project_text

        browser.close()


def main() -> None:
    static_checks()
    browser_checks()
    print("Grammatica visuale e scala territoriale verificate.")


if __name__ == "__main__":
    main()
