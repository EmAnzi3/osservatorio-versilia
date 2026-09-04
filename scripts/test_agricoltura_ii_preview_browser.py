#!/usr/bin/env python3
from __future__ import annotations

import argparse

from playwright.sync_api import expect, sync_playwright


def normalize(text: str) -> str:
    return " ".join((text or "").split())


def assert_no_simple_mean_benchmark(text: str) -> None:
    normalized = normalize(text)
    lower = normalized.lower()
    assert "Media comuni Versilia" not in normalized, normalized
    assert "media semplice dei 7" not in lower, normalized
    assert "media semplice dei sette" not in lower, normalized
    assert "media semplice dei comuni" not in lower, normalized


def compare_row(page, town: str):
    rows = page.locator("#compare-bars .bar-row")
    for index in range(rows.count()):
        row = rows.nth(index)
        if row.locator(".bar-town").inner_text().strip() == town:
            return row
    raise AssertionError(f"Riga confronto non trovata: {town}")


def town_current_row(page, town: str):
    rows = page.locator('.history-panel [data-view-pane="current"] .ux-bar-row')
    for index in range(rows.count()):
        row = rows.nth(index)
        if row.locator(".ux-bar-town").inner_text().strip() == town:
            return row
    raise AssertionError(f"Riga grafico comunale non trovata: {town}")


def visual_left(locator) -> float:
    return float(locator.evaluate("el => parseFloat(el.style.left)"))


def assert_point_vs_versilia(page, town: str, relation: str, aggregate_text: str) -> None:
    row = compare_row(page, town)
    expect(row.locator(".comparison-dot")).to_have_count(1)
    expect(row.locator(".comparison-reference")).to_have_count(1)
    dot = visual_left(row.locator(".comparison-dot"))
    reference = visual_left(row.locator(".comparison-reference"))
    aria = row.get_attribute("aria-label") or ""
    assert aggregate_text in aria, aria
    if relation == ">":
        assert dot > reference, f"{town}: punto {dot} non è a destra del benchmark {reference}"
    elif relation == "<":
        assert dot < reference, f"{town}: punto {dot} non è a sinistra del benchmark {reference}"
    else:
        raise AssertionError(f"Relazione inattesa: {relation}")


def assert_compare_legend(page, expected_label: str) -> None:
    legend = normalize(page.locator("#compare-bars .comparison-legend").inner_text())
    assert expected_label in legend, legend
    assert_no_simple_mean_benchmark(legend)


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

        # Card 1 — lettura iniziale: la linea grafica deve essere il rapporto
        # Versilia 69/957 = 7,2%, non la media semplice dei sette rapporti.
        page.goto(
            base + "confronta/ambiente/?indicatore=agriculturalRenewalAndLeadership",
            wait_until="networkidle",
        )
        page.wait_for_selector("#compare-bars .comparison-reference")
        assert_compare_legend(page, "Capi azienda fino a 40 anni")
        assert_point_vs_versilia(page, "Forte dei Marmi", ">", "7,2%")
        assert_point_vs_versilia(page, "Camaiore", "<", "7,2%")

        # Cambiando lettura devono cambiare insieme numero stampato, posizione
        # del punto e linea Versilia: 334/944 = 35,4%.
        selector = page.locator("#compare-bars select[data-composite-component]")
        selector.select_option(label="Conduttrice donna")
        expect(compare_row(page, "Forte dei Marmi").locator("strong")).to_have_text("42,9%")
        page.wait_for_selector("#compare-bars .comparison-reference")
        assert_compare_legend(page, "Aziende con conduttrice donna")
        assert_point_vs_versilia(page, "Forte dei Marmi", ">", "35,4%")
        assert_point_vs_versilia(page, "Seravezza", "<", "35,4%")
        definition = normalize(page.locator("#compare-definition").inner_text())
        assert "Versilia · Aziende con conduttrice donna" in definition, definition
        assert "35,4%" in definition or "35,38%" in definition, definition
        assert_no_simple_mean_benchmark(definition)

        # Card 2 — l'informatizzazione è il caso che prima mostrava Forte 28,6%
        # con il punto a zero perché il grafico usava ancora le attività connesse.
        page.goto(
            base + "confronta/ambiente/?indicatore=agriculturalDiversificationAndModernization",
            wait_until="networkidle",
        )
        selector = page.locator("#compare-bars select[data-composite-component]")
        selector.select_option(label="Informatizzazione")
        expect(compare_row(page, "Forte dei Marmi").locator("strong")).to_have_text("28,6%")
        page.wait_for_selector("#compare-bars .comparison-reference")
        assert_compare_legend(page, "Aziende informatizzate")
        assert_point_vs_versilia(page, "Forte dei Marmi", ">", "21,1%")
        assert_point_vs_versilia(page, "Massarosa", "<", "21,1%")
        definition = normalize(page.locator("#compare-definition").inner_text())
        assert "Versilia · Aziende informatizzate" in definition, definition
        assert "21,1%" in definition or "21,11%" in definition, definition
        assert_no_simple_mean_benchmark(definition)

        selector = page.locator("#compare-bars select[data-composite-component]")
        selector.select_option(label="Innovazione 2018–2020")
        expect(compare_row(page, "Stazzema").locator("strong")).to_have_text("14,0%")
        page.wait_for_selector("#compare-bars .comparison-reference")
        assert_compare_legend(page, "Aziende con investimenti finalizzati all’innovazione")
        assert_point_vs_versilia(page, "Stazzema", ">", "11,5%")
        assert_point_vs_versilia(page, "Seravezza", "<", "11,5%")

        # Scheda comunale — il grafico "Valore attuale" deve seguire il
        # selettore, non restare congelato sulla prima lettura.
        town = browser.new_page(viewport={"width": 1440, "height": 1000})
        town.goto(
            base + "comuni/stazzema/?tema=ambiente&indicatore=agriculturalRenewalAndLeadership",
            wait_until="networkidle",
        )
        expect(town_current_row(town, "Forte dei Marmi").locator("strong")).to_have_text("28,6%")
        town_selector = town.locator("#town-topic select[data-composite-choice]")
        town_selector.select_option(label="Conduttrice donna")
        expect(town.locator("[data-composite-primary-value]")).to_have_text("34,9%")
        expect(town_current_row(town, "Forte dei Marmi").locator("strong")).to_have_text("42,9%")
        position_text = normalize(town.locator(".composite-versilia-position").inner_text())
        assert "Versilia · Aziende con conduttrice donna" in position_text, position_text
        assert "35,4%" in position_text or "35,38%" in position_text, position_text
        assert "media" not in position_text.lower(), position_text
        assert "Quota sul totale Versilia" not in position_text, position_text
        assert "del totale della coltura" not in position_text, position_text

        town.goto(
            base + "comuni/stazzema/?tema=ambiente&indicatore=agriculturalDiversificationAndModernization",
            wait_until="networkidle",
        )
        expect(town_current_row(town, "Forte dei Marmi").locator("strong")).to_have_text("0,0%")
        town_selector = town.locator("#town-topic select[data-composite-choice]")
        town_selector.select_option(label="Informatizzazione")
        expect(town.locator("[data-composite-primary-value]")).to_have_text("23,3%")
        expect(town_current_row(town, "Forte dei Marmi").locator("strong")).to_have_text("28,6%")
        town_selector = town.locator("#town-topic select[data-composite-choice]")
        town_selector.select_option(label="Innovazione 2018–2020")
        expect(town.locator("[data-composite-primary-value]")).to_have_text("14,0%")
        expect(town_current_row(town, "Stazzema").locator("strong")).to_have_text("14,0%")

        # Padding e overflow restano un gate esplicito anche su mobile.
        mobile = browser.new_page(viewport={"width": 390, "height": 844})
        mobile.goto(
            base + "comuni/massarosa/?tema=ambiente&indicatore=agriculturalRenewalAndLeadership",
            wait_until="networkidle",
        )
        mobile.wait_for_selector(".composite-town-mobility article")
        articles = mobile.locator(".composite-town-mobility article")
        assert articles.count() >= 2, "Card composite comunale non materializzate"
        padding_left = articles.first.evaluate("el => parseFloat(getComputedStyle(el).paddingLeft)")
        padding_right = articles.first.evaluate("el => parseFloat(getComputedStyle(el).paddingRight)")
        assert padding_left >= 16 and padding_right >= 16, (padding_left, padding_right)
        assert mobile.evaluate(
            "document.documentElement.scrollWidth <= document.documentElement.clientWidth + 1"
        ), "Overflow orizzontale nella scheda comunale Agricoltura II"

        browser.close()

    print(
        "Agricoltura II browser preview: rapporti Versilia, posizioni grafiche, "
        "refresh dei grafici comunali e padding verificati."
    )


if __name__ == "__main__":
    main()
