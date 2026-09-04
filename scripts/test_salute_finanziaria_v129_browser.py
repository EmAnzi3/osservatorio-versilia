#!/usr/bin/env python3
"""Browser gate per le tre letture finanziarie v1.29.0."""
from __future__ import annotations

import argparse
from urllib.parse import urljoin

from playwright.sync_api import Page, sync_playwright


READINGS = (
    ("part-0", "10.4", "Debito finanziario pro capite", "€/ab."),
    ("part-1", "6.1", "Interessi sulle entrate correnti", "%"),
    ("part-2", "10.3", "Sostenibilità dei debiti finanziari", "%"),
)
INTERNAL_UNITS = ("currencyPerResident", "eurPerResident", "percent2")
VERSILIA_2025 = {"part-0": "707,91", "part-1": "1,70", "part-2": "4,88"}


def no_overflow(page: Page, label: str) -> None:
    overflow = page.evaluate(
        "() => document.documentElement.scrollWidth - document.documentElement.clientWidth"
    )
    assert overflow <= 2, f"{label}: overflow orizzontale di {overflow}px"


def no_internal_units(page: Page, label: str) -> None:
    visible = page.locator("main").inner_text()
    for token in INTERNAL_UNITS:
        assert token not in visible, f"{label}: unità tecnica esposta ({token})"


def padded(page: Page, selector: str, label: str) -> None:
    values = page.locator(selector).first.evaluate(
        "el => ['paddingTop','paddingRight','paddingBottom','paddingLeft'].map(k => parseFloat(getComputedStyle(el)[k]) || 0)"
    )
    assert min(values) >= 12, f"{label}: padding insufficiente {values}"


def check_tooltip(page: Page, root: str, unit: str, label: str) -> None:
    point = page.locator(f"{root} .chart-point").last
    point.focus()
    tooltip = point.locator(".chart-tooltip:not([hidden])")
    tooltip.wait_for()
    assert unit in (tooltip.text_content() or ""), f"{label}: unità tooltip assente"


def check_compare(page: Page, base: str) -> None:
    page.goto(urljoin(base, "confronta/bilanci/?indicatore=financialDebtProfile"), wait_until="networkidle")
    selector = page.locator("#compare-bars select[data-composite-component]")
    selector.wait_for()
    assert selector.locator("option").all_inner_texts() == [item[2] for item in READINGS]
    for choice, code, title, unit in READINGS:
        selector.select_option(choice)
        selector = page.locator("#compare-bars select[data-composite-component]")
        definition = page.locator("#compare-definition")
        assert code in definition.inner_text() and title in definition.inner_text()
        assert unit in definition.inner_text() and VERSILIA_2025[choice] in definition.inner_text()
        assert page.locator("#compare-bars .bar-row").count() == 7
        history = page.locator("#compare-bars .financial-aggregate-history")
        assert "2019" in history.inner_text() and "2025" in history.inner_text()
        assert unit in history.inner_text()
        assert code in page.locator("#compare-tools .financial-method-disclosure").text_content()
        check_tooltip(page, "#compare-bars .financial-aggregate-history", unit, f"confronto {code}")
    padded(page, "#compare-definition .financial-definition", "definizione confronto")
    padded(page, "#compare-bars .financial-aggregate-history", "storico Versilia")
    no_internal_units(page, "confronto")
    no_overflow(page, "confronto")


def check_indicator(page: Page, base: str) -> None:
    page.goto(
        urljoin(base, "indicatori/debito-finanziario-e-costo-degli-interessi/"),
        wait_until="networkidle",
    )
    selector = page.locator(".indicator-current select[data-composite-component]")
    selector.wait_for()
    assert selector.locator("option").all_inner_texts() == [item[2] for item in READINGS]
    for choice, code, title, unit in READINGS:
        selector.select_option(choice)
        selector = page.locator(".indicator-current select[data-composite-component]")
        assert code in page.locator("[data-financial-indicator-hero-title]").inner_text()
        assert title in page.locator("[data-financial-indicator-title]").inner_text()
        aggregate = page.locator("[data-financial-indicator-aggregate]").inner_text()
        assert unit in aggregate and VERSILIA_2025[choice] in aggregate
        history = page.locator("[data-financial-indicator-history]")
        assert "2019" in history.inner_text() and "2025" in history.inner_text()
        assert unit in history.inner_text()
        method = page.locator("[data-financial-indicator-method]").text_content()
        assert code in method and unit in method
    padded(page, ".financial-indicator-comparison .compare-chart-toolbar", "selettore indicatore")
    no_internal_units(page, "indicatore")
    no_overflow(page, "indicatore")


def check_town(page: Page, base: str, slug: str, expected: dict[str, str]) -> None:
    page.goto(
        urljoin(base, f"comuni/{slug}/?tema=bilanci&indicatore=financialDebtProfile"),
        wait_until="networkidle",
    )
    selector = page.locator("#town-topic select[data-composite-choice]")
    selector.wait_for()
    assert selector.locator("option").all_inner_texts() == [item[2] for item in READINGS]
    for choice, code, title, unit in READINGS:
        selector.select_option(choice)
        value = page.locator("#town-topic [data-composite-primary-value]").inner_text()
        assert expected[choice] in value and unit in value
        assert title in page.locator("#town-topic [data-composite-primary-label]").inner_text()
        assert code in page.locator("#town-topic [data-financial-panel-overline]").inner_text()
        history = page.locator("#town-topic [data-financial-profile-history]")
        assert "2019" in history.inner_text() and "2025" in history.inner_text()
        assert unit in history.inner_text()
        method = page.locator("#town-topic [data-financial-profile-method]").text_content()
        assert code in method and unit in method
        check_tooltip(page, "#town-topic [data-financial-profile-history]", unit, f"{slug} {code}")
    town_text = page.locator("#town-topic").text_content()
    if slug == "massarosa":
        selector.select_option("part-0")
        town_text = page.locator("#town-topic").text_content()
        assert "OSL" in town_text and "intero insieme delle passività" in town_text
    elif slug == "forte-dei-marmi":
        assert "numeratore ufficiale verificato nullo" in town_text
    elif slug == "camaiore":
        assert "9,64" in town_text and "10,82" in town_text
    padded(page, "#town-topic .town-metric-primary", f"card {slug}")
    padded(page, "#town-topic .financial-profile-history", f"storico {slug}")
    no_internal_units(page, slug)
    no_overflow(page, slug)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="http://127.0.0.1:8123/")
    args = parser.parse_args()
    base = args.base.rstrip("/") + "/"
    errors: list[str] = []

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        for width, height, label in ((1440, 1000, "desktop"), (1024, 900, "desktop-1024"), (390, 844, "mobile")):
            page = browser.new_page(viewport={"width": width, "height": height})
            page.on("pageerror", lambda error: errors.append(str(error)))
            check_compare(page, base)
            check_indicator(page, base)
            check_town(page, base, "massarosa", {"part-0": "465,49", "part-1": "4,38", "part-2": "7,26"})
            check_town(page, base, "forte-dei-marmi", {"part-0": "0,00", "part-1": "0,00", "part-2": "0,00"})
            check_town(page, base, "camaiore", {"part-0": "1.641,94", "part-1": "3,50", "part-2": "10,99"})
            page.close()
            print(f"Salute finanziaria browser {label}: OK")
        browser.close()

    assert not errors, f"Errori JavaScript nel browser: {' | '.join(errors)}"


if __name__ == "__main__":
    main()
