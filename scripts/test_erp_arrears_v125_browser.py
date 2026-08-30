#!/usr/bin/env python3
"""Smoke test browser desktop/mobile e light/dark per Morosità ERP v1.25.0."""
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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="http://127.0.0.1:8123/")
    parser.add_argument("--screenshots-dir", default="reports/erp-arrears-v125-browser")
    args = parser.parse_args()
    output = Path(args.screenshots_dir)
    output.mkdir(parents=True, exist_ok=True)

    compare = urljoin(args.base, "confronta/abitare/?indicatore=erpArrears")
    town = urljoin(args.base, "comuni/massarosa/?tema=abitare&indicatore=erpArrears")
    indicator = urljoin(args.base, "indicatori/erpArrears/")

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
                page.screenshot(path=output / f"compare-{label}-{scheme}.png", full_page=True)

                # Il dettaglio contabile è intenzionalmente chiuso: prima si verifica
                # il summary, poi si apre l'accordion e si controlla il contenuto.
                check_page(page, town, ["Morosità ERP", "3,48%", "Dettaglio contabile 2024"])
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
                assert page.locator("body").evaluate("el => el.scrollWidth <= window.innerWidth + 1"), f"Overflow orizzontale dopo apertura dettaglio: {town}"
                page.screenshot(path=output / f"massarosa-{label}-{scheme}.png", full_page=True)

                check_page(page, indicator, ["Morosità ERP", "8,56%", "2020", "2024", "Fonte originale"])
                context.close()
        browser.close()

    print("Morosità ERP v1.25.0 browser: desktop/mobile 390×844 e light/dark verificati.")


if __name__ == "__main__":
    main()
