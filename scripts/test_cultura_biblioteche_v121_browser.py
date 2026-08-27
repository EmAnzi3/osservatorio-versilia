#!/usr/bin/env python3
"""Browser gate del lotto Cultura e biblioteche v1.21.0 sul dist reale."""
from __future__ import annotations

import argparse
from urllib.parse import urljoin

from playwright.sync_api import sync_playwright

KEYS = (
    "libraryLoansPerResident",
    "libraryActiveBorrowersPer100",
    "libraryWeeklyOpeningHours",
)


def no_overflow(page, label: str) -> None:
    overflow = page.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth")
    assert overflow <= 1, f"Overflow orizzontale {label}: {overflow}px"


def open_metric(page, key: str) -> None:
    button = page.locator(f'button[data-metric="{key}"]').first
    assert button.count() == 1, f"Indicatore non trovato nel confronto: {key}"
    if not button.is_visible():
        group = button.locator("xpath=ancestor::section[contains(concat(' ', normalize-space(@class), ' '), ' metric-group ')][1]")
        assert group.count() == 1, f"Gruppo non trovato per {key}"
        heading = group.locator(":scope > .metric-group-heading")
        assert heading.count() == 1
        heading.click()
        page.wait_for_timeout(150)
    assert button.is_visible(), f"Indicatore non visibile: {key}"
    button.scroll_into_view_if_needed()
    button.click()
    page.wait_for_timeout(250)
    assert f"indicatore={key}" in page.url


def assert_missing_rows(bars, key: str) -> None:
    # Il confronto mantiene tutti e sette i Comuni: i due mancanti devono essere
    # righe esplicite n.d., non essere eliminati e soprattutto non diventare zeri.
    assert bars.count() == 7, f"{key}: attese 7 righe comunali, trovate {bars.count()}"
    for town in ("Massarosa", "Stazzema"):
        row = bars.filter(has_text=town)
        assert row.count() == 1, f"{key}: riga {town} assente o duplicata"
        text = row.inner_text().lower()
        assert "n.d." in text, f"{key}/{town}: il mancante non è mostrato come n.d. ({text})"


def assert_compare(page, base: str, mobile: bool) -> None:
    page.goto(urljoin(base, "confronta/comunita/?indicatore=libraryLoansPerResident"), wait_until="networkidle")
    page.wait_for_timeout(450)
    no_overflow(page, "confronto mobile" if mobile else "confronto desktop")
    body = page.locator("body").inner_text()
    assert "Cultura e biblioteche" in body
    assert "Prestiti bibliotecari per residente" in body
    assert "Massarosa" in body and "Stazzema" in body
    assert body.count("n.d.") >= 2, "I mancanti 2024 non sono resi come n.d."
    assert "5/7" in body, "La copertura parziale dell'aggregato non è dichiarata"

    for key in KEYS:
        open_metric(page, key)
        no_overflow(page, f"{key} confronto")
        definition = page.locator("#compare-definition").inner_text()
        assert "5/7" in definition or "5/7" in page.locator("body").inner_text(), f"{key}: copertura non visibile"
        assert_missing_rows(page.locator("#compare-bars .bar-row"), key)

    page.goto(urljoin(base, "comuni/massarosa/"), wait_until="networkidle")
    page.wait_for_timeout(350)
    no_overflow(page, "Massarosa")
    text = page.locator("body").inner_text()
    assert "Cultura e biblioteche" in text
    assert "Prestiti bibliotecari per residente" in text
    assert "n.d." in text

    page.goto(urljoin(base, "comuni/stazzema/"), wait_until="networkidle")
    page.wait_for_timeout(350)
    no_overflow(page, "Stazzema")
    text = page.locator("body").inner_text()
    assert "Cultura e biblioteche" in text and "n.d." in text


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", required=True)
    args = parser.parse_args()
    base = args.base.rstrip("/") + "/"

    with sync_playwright() as p:
        browser = p.chromium.launch()
        desktop = browser.new_context(viewport={"width": 1440, "height": 1000}, color_scheme="light")
        assert_compare(desktop.new_page(), base, mobile=False)
        desktop.close()

        mobile = browser.new_context(viewport={"width": 390, "height": 844}, color_scheme="dark", is_mobile=True)
        assert_compare(mobile.new_page(), base, mobile=True)
        mobile.close()
        browser.close()

    print("Browser Cultura v1.21 verificato: 7 righe comunali con n.d. espliciti, 5/7, schede comunali, desktop/mobile e chiaro/scuro.")


if __name__ == "__main__":
    main()
