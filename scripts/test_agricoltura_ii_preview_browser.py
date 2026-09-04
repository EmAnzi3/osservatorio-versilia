#!/usr/bin/env python3
from __future__ import annotations

import argparse

from playwright.sync_api import sync_playwright


def normalize(text: str) -> str:
    return " ".join((text or "").split())


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

        # Card 1: il confronto usa il select reale del renderer e deve mostrare
        # il benchmark Versilia derivato da 334/944, non la media dei 7 rapporti.
        page.goto(
            base + "confronta/ambiente/?indicatore=agriculturalRenewalAndLeadership",
            wait_until="networkidle",
        )
        page.wait_for_selector("select[data-composite-component]")
        body = page.locator("body").inner_text()
        assert "Ricambio e conduzione delle aziende agricole" in body
        selector = page.locator("select[data-composite-component]")
        selector.select_option(label="Conduttrice donna")
        page.wait_for_function(
            "document.querySelector('select[data-composite-component]')?.selectedOptions[0]?.textContent.includes('Conduttrice')"
        )
        definition = normalize(page.locator("#compare-definition").inner_text())
        assert "Versilia · Aziende con conduttrice donna" in definition, definition
        assert any(value in definition for value in ("35,4%", "35,38%")), definition
        assert "Media comuni Versilia" not in definition, definition
        assert "media semplice" not in definition.lower(), definition

        # Card 2: stessa regola sul benchmark per l'informatizzazione (202/957).
        page.goto(
            base + "confronta/ambiente/?indicatore=agriculturalDiversificationAndModernization",
            wait_until="networkidle",
        )
        page.wait_for_selector("select[data-composite-component]")
        body = page.locator("body").inner_text()
        assert "Diversificazione e modernizzazione delle aziende agricole" in body
        selector = page.locator("select[data-composite-component]")
        selector.select_option(label="Informatizzazione")
        page.wait_for_function(
            "document.querySelector('select[data-composite-component]')?.selectedOptions[0]?.textContent.includes('Informatizzazione')"
        )
        definition = normalize(page.locator("#compare-definition").inner_text())
        assert "Versilia · Aziende informatizzate" in definition, definition
        assert any(value in definition for value in ("21,1%", "21,11%")), definition
        assert "Media comuni Versilia" not in definition, definition
        assert "media semplice" not in definition.lower(), definition

        # Scheda comunale: il selettore town usa data-composite-choice.
        # Il benchmark deve essere il rapporto Versilia, non la quota del Comune
        # sul totale della coltura (logica storica di agricultureProfile).
        mobile = browser.new_page(viewport={"width": 390, "height": 844})
        mobile.goto(
            base + "comuni/massarosa/?tema=ambiente&indicatore=agriculturalRenewalAndLeadership",
            wait_until="networkidle",
        )
        mobile.wait_for_selector("select[data-composite-choice]")
        town_selector = mobile.locator("select[data-composite-choice]")
        town_selector.select_option(label="Conduttrice donna")
        mobile.wait_for_function(
            "document.querySelector('select[data-composite-choice]')?.selectedOptions[0]?.textContent.includes('Conduttrice')"
        )
        position_text = normalize(mobile.locator(".composite-versilia-position").inner_text())
        assert "Versilia · Aziende con conduttrice donna" in position_text, position_text
        assert any(value in position_text for value in ("35,4%", "35,38%")), position_text
        assert "Quota sul totale Versilia" not in position_text, position_text
        assert "del totale della coltura" not in position_text, position_text

        articles = mobile.locator(".composite-town-mobility article")
        assert articles.count() >= 2, "Card composite comunale non materializzate"
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
        assert mobile.evaluate(
            "document.documentElement.scrollWidth <= document.documentElement.clientWidth + 1"
        ), "Overflow orizzontale nella scheda comunale Agricoltura II"

        browser.close()

    print(
        "Agricoltura II browser preview: 183 indicatori, selettori reali, "
        "benchmark a rapporto tra somme e padding verificati."
    )


if __name__ == "__main__":
    main()
