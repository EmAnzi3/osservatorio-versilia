#!/usr/bin/env python3
"""Browser gate desktop/mobile e light/dark per Morosità ERP v1.25.0."""
from __future__ import annotations

import argparse
from pathlib import Path
from urllib.parse import urljoin

from playwright.sync_api import sync_playwright


def body_text(page) -> str:
    return page.locator("body").inner_text()


def check_page(page, url: str, required: list[str]) -> None:
    response = page.goto(url, wait_until="networkidle")
    assert response is None or response.ok, (url, response.status if response else None)
    text = body_text(page)
    for token in required:
        assert token in text, (url, token)
    assert page.locator("body").evaluate("el => el.scrollWidth <= window.innerWidth + 1"), f"Overflow orizzontale: {url}"


def css_number(locator, property_name: str) -> float:
    return float(locator.evaluate(f"el => parseFloat(getComputedStyle(el).{property_name})"))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="http://127.0.0.1:8123/")
    parser.add_argument("--screenshots-dir", default="reports/erp-arrears-v125-browser")
    args = parser.parse_args()
    output = Path(args.screenshots_dir)
    output.mkdir(parents=True, exist_ok=True)

    compare = urljoin(args.base, "confronta/abitare/?indicatore=erpArrears")
    town = urljoin(args.base, "comuni/massarosa/?tema=abitare&indicatore=erpArrears")
    indicator = urljoin(args.base, "indicatori/morosita-erp/")

    configurations = [
        ("desktop", {"width": 1440, "height": 1000}),
        ("mobile", {"width": 390, "height": 844}),
    ]
    schemes = ["light", "dark"]

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        for label, viewport in configurations:
            for scheme in schemes:
                context = browser.new_context(viewport=viewport, color_scheme=scheme)
                page = context.new_page()

                check_page(page, compare, ["Morosità ERP", "8,56%", "Viareggio", "10,83%", "Massarosa", "3,48%"])
                page.locator(".comparison-legend").wait_for(state="visible")
                legend = page.locator(".comparison-legend").inner_text()
                assert "Versilia · 7 Comuni" in legend, legend
                assert "Media semplice" not in legend, legend
                assert "percent2" not in body_text(page), "L'unità tecnica percent2 non deve essere visibile"

                camaiore = page.locator(".comparison-bars > .bar-row").filter(has_text="Camaiore").first
                reference = camaiore.locator(".comparison-reference")
                dot = camaiore.locator(".comparison-dot")
                assert reference.count() == 1 and dot.count() == 1
                reference_left = float(reference.evaluate("el => parseFloat(el.style.left)"))
                dot_left = float(dot.evaluate("el => parseFloat(el.style.left)"))
                assert reference_left > dot_left, (reference_left, dot_left, "8,56% deve stare a destra di Camaiore 7,37%")
                page.screenshot(path=output / f"compare-{label}-{scheme}.png", full_page=True)

                check_page(page, town, ["Morosità ERP", "3,48%", "Dettaglio contabile 2024"])
                primary_value = page.locator(".town-metric-primary [data-composite-primary-value]").inner_text().strip()
                assert primary_value == "3,48%", primary_value

                history_button = page.locator('.history-panel [data-view-mode="history"]')
                assert history_button.count() == 1, "Comando Storico assente nella scheda comunale ERP"
                assert not history_button.is_disabled(), "Vista Storico ERP disabilitata nonostante la serie 2020–2024"
                history_button.click()
                history_card = page.locator(".history-panel .ux-history-card")
                history_card.wait_for(state="visible")
                y_labels = history_card.locator(".ux-history-axis-label").all_inner_texts()
                assert any("%" in item for item in y_labels), y_labels
                history_summary = history_card.locator(".ux-history-summary").inner_text()
                assert "%" in history_summary, history_summary
                assert "percent2" not in body_text(page)

                detail = page.locator("details.erp-arrears-detail")
                assert detail.count() == 1, "Accordion dettaglio contabile ERP assente o duplicato"
                detail.evaluate("el => el.open = true")
                expanded = body_text(page)
                for token in (
                    "Importi emessi cumulati",
                    "Morosità cumulata",
                    "2.078.965,36",
                    "72.398,09",
                ):
                    assert token in expanded, (town, token)

                summary = detail.locator(":scope > summary")
                first_card = detail.locator(".composite-town-detail > div").first
                assert css_number(summary, "paddingLeft") >= 16
                assert css_number(first_card, "paddingLeft") >= 14
                detail_background = detail.evaluate("el => getComputedStyle(el).backgroundColor")
                card_background = first_card.evaluate("el => getComputedStyle(el).backgroundColor")
                assert detail_background != card_background, (detail_background, card_background)
                assert page.locator("body").evaluate("el => el.scrollWidth <= window.innerWidth + 1"), f"Overflow orizzontale dopo apertura dettaglio: {town}"
                page.screenshot(path=output / f"massarosa-{label}-{scheme}.png", full_page=True)

                check_page(page, indicator, ["Morosità ERP", "8,56%", "2020", "2024", "Fonte originale"])
                context.close()
        browser.close()

    print("Morosità ERP v1.25.0 browser: benchmark Versilia 8,56%, unità %, contrasto e padding verificati desktop/mobile light/dark.")


if __name__ == "__main__":
    main()
