#!/usr/bin/env python3
from __future__ import annotations

import argparse
from playwright.sync_api import sync_playwright


def no_overflow(page, label: str) -> None:
    widths = page.evaluate("({client: document.documentElement.clientWidth, scroll: document.documentElement.scrollWidth})")
    assert widths["scroll"] <= widths["client"], f"Overflow {label}: {widths}"


def check_compare(page, base: str, key: str, expected_label: str) -> None:
    page.goto(f"{base}confronta/bilanci/?indicatore={key}", wait_until="networkidle")
    page.wait_for_selector("#compare-bars")
    assert expected_label in page.locator("body").inner_text()
    assert page.locator("#compare-bars .bar-row").count() == 7
    no_overflow(page, f"confronto/{key}")


def check_age_compare(page, base: str) -> None:
    page.goto(f"{base}confronta/bilanci/?indicatore=municipalStaffAgeStructure", wait_until="networkidle")
    page.wait_for_selector("select[data-composite-component]")
    selector = page.locator("select[data-composite-component]")
    assert selector.locator("option").count() == 3
    assert page.locator("#compare-bars .bar-row").count() == 7
    first_axis = page.locator("#compare-bars .comparison-axis").inner_text()
    selector.select_option("part-2")
    page.wait_for_function(
        "() => document.querySelector('#compare-bars .comparison-bars')?.dataset.compositeChoice === 'part-2'"
    )
    changed_axis = page.locator("#compare-bars .comparison-axis").inner_text()
    assert first_axis != changed_axis
    no_overflow(page, "confronto/eta-personale")


def check_town(page, base: str, key: str, expected_label: str) -> None:
    page.goto(f"{base}comuni/massarosa/?tema=bilanci&indicatore={key}", wait_until="networkidle")
    assert expected_label in page.locator("body").inner_text()
    no_overflow(page, f"massarosa/{key}")


def check_age_town(page, base: str) -> None:
    page.goto(
        f"{base}comuni/massarosa/?tema=bilanci&indicatore=municipalStaffAgeStructure",
        wait_until="networkidle",
    )
    page.wait_for_selector("select[data-composite-choice]")
    selector = page.locator("select[data-composite-choice]")
    assert selector.locator("option").count() == 3
    selector.select_option("part-2")
    page.wait_for_function(
        "() => document.querySelector('[data-view-pane=\"current\"]')?.dataset.compositeChoice === 'part-2'"
    )
    assert page.locator('[data-view-pane="current"] .ux-bar-row').count() == 7
    no_overflow(page, "massarosa/eta-personale")


def run(base: str) -> None:
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        for viewport in ({"width": 1440, "height": 1000}, {"width": 390, "height": 844}):
            context = browser.new_context(viewport=viewport)
            page = context.new_page()
            check_compare(page, base, "municipalEmployeesPer1000", "Dipendenti comunali per 1.000 residenti")
            check_compare(page, base, "municipalStaffTurnover", "Turnover netto del personale comunale")
            check_age_compare(page, base)
            check_town(page, base, "municipalEmployeesPer1000", "Dipendenti comunali per 1.000 residenti")
            check_town(page, base, "municipalStaffTurnover", "Turnover netto del personale comunale")
            check_age_town(page, base)
            context.close()
        browser.close()
    print("Amministrazione Lotto A browser: confronto e scheda comunale OK su desktop e mobile, nessun overflow.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="http://127.0.0.1:8123/")
    args = parser.parse_args()
    run(args.base.rstrip("/") + "/")
