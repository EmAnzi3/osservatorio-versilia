#!/usr/bin/env python3
from __future__ import annotations

import argparse

from playwright.sync_api import sync_playwright


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="http://127.0.0.1:8123/")
    args = parser.parse_args()
    base = args.base.rstrip("/") + "/"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 1000})

        page.goto(base, wait_until="networkidle")
        hero = page.locator(".hero-facts").inner_text().upper()
        assert "183 INDICATORI" in hero, hero

        page.goto(
            base + "confronta/ambiente/?indicatore=agriculturalRenewalAndLeadership",
            wait_until="networkidle",
        )
        page.wait_for_selector("select[data-composite-choice]")
        body = page.locator("body").inner_text()
        assert "Ricambio e conduzione delle aziende agricole" in body
        selector = page.locator("select[data-composite-choice]")
        selector.select_option(label="Conduttrice donna")
        page.wait_for_function(
            "document.querySelector('[data-composite-primary-label]')?.textContent.includes('conduttrice')"
        )
        aggregate = page.locator("[data-composite-aggregate-value]").first.inner_text().strip()
        assert aggregate in {"35,4%", "35,38%"}, aggregate
        assert "Media comuni Versilia" not in page.locator("body").inner_text(), (
            "Agricoltura II non deve presentare il benchmark come media semplice dei Comuni"
        )

        page.goto(
            base + "confronta/ambiente/?indicatore=agriculturalDiversificationAndModernization",
            wait_until="networkidle",
        )
        page.wait_for_selector("select[data-composite-choice]")
        body = page.locator("body").inner_text()
        assert "Diversificazione e modernizzazione delle aziende agricole" in body
        selector = page.locator("select[data-composite-choice]")
        selector.select_option(label="Informatizzazione")
        page.wait_for_function(
            "document.querySelector('[data-composite-primary-label]')?.textContent.includes('informat')"
        )
        aggregate = page.locator("[data-composite-aggregate-value]").first.inner_text().strip()
        assert aggregate in {"21,1%", "21,11%"}, aggregate

        mobile = browser.new_page(viewport={"width": 390, "height": 844})
        mobile.goto(
            base + "comuni/massarosa/?tema=ambiente&indicatore=agriculturalRenewalAndLeadership",
            wait_until="networkidle",
        )
        mobile.wait_for_selector("select[data-composite-choice]")
        articles = mobile.locator(".composite-town-mobility article")
        if articles.count():
            padding_left = articles.first.evaluate(
                "el => parseFloat(getComputedStyle(el).paddingLeft)"
            )
            padding_right = articles.first.evaluate(
                "el => parseFloat(getComputedStyle(el).paddingRight)"
            )
            assert padding_left >= 16 and padding_right >= 16, (
                padding_left,
                padding_right,
            )
        assert mobile.evaluate("document.documentElement.scrollWidth <= document.documentElement.clientWidth + 1"), (
            "Overflow orizzontale nella scheda comunale Agricoltura II"
        )

        browser.close()

    print("Agricoltura II browser preview: 183 indicatori, selector, benchmark e padding verificati.")


if __name__ == "__main__":
    main()
