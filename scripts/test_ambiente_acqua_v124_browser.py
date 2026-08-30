#!/usr/bin/env python3
"""Browser gate for the v1.24 GAIA/SISBON presentation."""

from __future__ import annotations

import argparse
from pathlib import Path
from urllib.parse import urljoin

from playwright.sync_api import Page, sync_playwright


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def no_horizontal_overflow(page: Page, label: str) -> None:
    widths = page.evaluate(
        """() => ({
          document: [document.documentElement.scrollWidth, document.documentElement.clientWidth],
          body: [document.body.scrollWidth, document.body.clientWidth]
        })"""
    )
    require(widths["document"][0] <= widths["document"][1] + 1, f"{label}: overflow document {widths}")
    require(widths["body"][0] <= widths["body"][1] + 1, f"{label}: overflow body {widths}")


def require_white(page: Page, selector: str, label: str) -> None:
    color = page.locator(selector).first.evaluate("node => getComputedStyle(node).backgroundColor")
    require(color == "rgb(255, 255, 255)", f"{label}: atteso sfondo bianco, trovato {color}")


def capture(page: Page, directory: Path | None, name: str) -> None:
    if directory is None:
        return
    directory.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(directory / name), full_page=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="http://127.0.0.1:8123/")
    parser.add_argument("--screenshots-dir", type=Path)
    args = parser.parse_args()

    errors: list[str] = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 1000})
        page.on("pageerror", lambda error: errors.append(str(error)))

        page.goto(urljoin(args.base, "confronta/ambiente/?indicatore=drinkingWaterQuality"), wait_until="networkidle")
        page.locator(".water-quality-range-chart").wait_for()
        require(page.locator(".water-quality-range-row").count() == 7, "GAIA: il grafico deve avere 7 righe comunali")
        require(page.locator(".water-quality-values-disclosure").count() == 0, "GAIA: granularità presente nella pagina tematica")
        require("CASE ROSSE" not in page.locator("#compare-bars").inner_text(), "GAIA: nome di località presente nella pagina tematica")
        require_white(page, ".water-quality-selector select", "Selettore parametro GAIA")
        require_white(page, ".water-quality-parameter-meta div", "Metadati parametro GAIA")
        require_white(page, ".water-quality-range-chart", "Grafico comunale GAIA")
        no_horizontal_overflow(page, "Confronto GAIA desktop")
        capture(page, args.screenshots_dir, "compare-water-desktop.png")

        page.locator("[data-water-quality-parameter-compare]").select_option("5")
        page.locator(".water-quality-censored-band").first.wait_for()
        require(page.locator(".water-quality-censored-band").count() == 7, "GAIA: parametro censurato non rappresentato per 7 Comuni")

        page.goto(urljoin(args.base, "comuni/massarosa/?tema=ambiente&indicatore=drinkingWaterQuality"), wait_until="networkidle")
        disclosure = page.locator(".water-quality-town-disclosure")
        disclosure.wait_for()
        require(not disclosure.evaluate("node => node.open"), "GAIA: dettaglio comunale aperto per default")
        require(page.locator(".town-metric-layout.single-column .versilia-position").count() == 0, "GAIA: benchmark laterale ancora presente")
        require("Rispetto alla media" not in page.locator("#town-topic").inner_text(), "GAIA: confronto con la media ancora presente")
        disclosure.locator(":scope > summary").click()
        page.locator(".water-quality-parameter-card").wait_for()
        require_white(page, ".water-quality-town-controls select", "Selettore comunale GAIA")
        require_white(page, ".water-quality-parameter-card > dl > div", "Campi comunali GAIA")
        no_horizontal_overflow(page, "Scheda GAIA desktop")
        capture(page, args.screenshots_dir, "town-water-desktop.png")

        page.goto(urljoin(args.base, "comuni/viareggio/?tema=ambiente&indicatore=remediationProceedings"), wait_until="networkidle")
        page.locator(".remediation-procedure-list details").first.locator("summary").click()
        require_white(page, ".remediation-selector select", "Selettore SISBON")
        require_white(page, ".remediation-benchmark article", "Benchmark SISBON")
        require_white(page, ".remediation-procedure-list details", "Accordion SISBON")
        require_white(page, ".remediation-procedure-list details[open] dl > div", "Campi SISBON")
        no_horizontal_overflow(page, "Scheda SISBON desktop")
        capture(page, args.screenshots_dir, "town-remediation-desktop.png")

        page.set_viewport_size({"width": 390, "height": 844})
        page.goto(urljoin(args.base, "confronta/ambiente/?indicatore=drinkingWaterQuality"), wait_until="networkidle")
        page.locator(".water-quality-range-chart").wait_for()
        no_horizontal_overflow(page, "Confronto GAIA mobile")
        capture(page, args.screenshots_dir, "compare-water-mobile.png")
        page.goto(urljoin(args.base, "comuni/massarosa/?tema=ambiente&indicatore=drinkingWaterQuality"), wait_until="networkidle")
        page.locator(".water-quality-town-disclosure > summary").click()
        page.locator(".water-quality-parameter-card").wait_for()
        no_horizontal_overflow(page, "Scheda GAIA mobile")
        capture(page, args.screenshots_dir, "town-water-mobile.png")

        browser.close()

    require(not errors, f"Errori JavaScript nel browser: {' | '.join(errors)}")
    print("Ambiente acqua e bonifiche v1.24 browser: PASS")


if __name__ == "__main__":
    main()
