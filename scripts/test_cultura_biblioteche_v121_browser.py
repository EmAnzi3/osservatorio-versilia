#!/usr/bin/env python3
"""Browser gate del lotto Cultura e biblioteche v1.21.0 sul dist reale."""
from __future__ import annotations

import argparse
from urllib.parse import urljoin

from playwright.sync_api import sync_playwright

METRICS = (
    ("libraryLoansPerResident", "Prestiti bibliotecari"),
    ("libraryActiveBorrowersPer100", "Utenti attivi del prestito"),
    ("libraryWeeklyOpeningHours", "Apertura settimanale"),
)
KEYS = tuple(key for key, _ in METRICS)


def no_overflow(page, label: str) -> None:
    overflow = page.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth")
    assert overflow <= 1, f"Overflow orizzontale {label}: {overflow}px"


def open_metric(page, key: str) -> None:
    button = page.locator(f'button[data-metric="{key}"]').first
    assert button.count() == 1, f"Indicatore non trovato nel confronto: {key}"
    if not button.is_visible():
        group = button.locator("xpath=ancestor::section[contains(concat(' ', normalize-space(@class), ' '), ' metric-group ')][1]")
        assert group.count() == 1, f"Gruppo indicatore non trovato: {key}"
        heading = group.locator(":scope > .metric-group-heading")
        assert heading.count() == 1 and heading.get_attribute("role") == "button"
        heading.click()
        page.wait_for_timeout(180)
    assert button.is_visible(), f"Indicatore non visibile: {key}"
    button.scroll_into_view_if_needed()
    button.click()
    page.wait_for_timeout(300)
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


def assert_town_missing_metrics(page, base: str, slug: str, town: str) -> None:
    # Le schede comunali selezionano tema e indicatore via query string. Il renderer
    # usa nella barra di controllo lo shortLabel, mentre il contenuto principale
    # mostra direttamente valore e descrizione: il gate verifica quindi la selezione
    # effettiva della card e il valore n.d., senza richiedere il long label nel body.
    for key, short_label in METRICS:
        page.goto(
            urljoin(base, f"comuni/{slug}/?tema=comunita&indicatore={key}"),
            wait_until="networkidle",
        )
        page.wait_for_timeout(450)
        no_overflow(page, f"{town}/{key}")
        assert "tema=comunita" in page.url and f"indicatore={key}" in page.url
        topic = page.locator("#town-topic")
        assert topic.count() == 1, f"{town}/{key}: contenitore tema assente"

        selected = topic.locator(f'button[data-metric="{key}"]').first
        assert selected.count() == 1, f"{town}/{key}: controllo indicatore assente"
        assert selected.is_visible(), f"{town}/{key}: controllo indicatore non visibile"
        assert short_label in selected.inner_text(), f"{town}/{key}: short label inatteso"
        assert selected.get_attribute("aria-selected") == "true", f"{town}/{key}: indicatore non selezionato"

        value = topic.locator(".town-metric-primary strong[data-composite-primary-value]")
        assert value.count() == 1, f"{town}/{key}: valore principale assente"
        assert value.inner_text().strip().lower() == "n.d.", (
            f"{town}/{key}: mancante non mostrato come n.d. ({value.inner_text()})"
        )


def assert_compare(page, base: str, mobile: bool) -> None:
    page.goto(urljoin(base, "confronta/comunita/?indicatore=libraryLoansPerResident"), wait_until="networkidle")
    page.wait_for_timeout(500)
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

    assert_town_missing_metrics(page, base, "massarosa", "Massarosa")
    assert_town_missing_metrics(page, base, "stazzema", "Stazzema")


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

    print("Browser Cultura v1.21 verificato: confronto 7 righe con n.d. espliciti, card comunali selezionate via URL, 5/7, desktop/mobile e chiaro/scuro.")


if __name__ == "__main__":
    main()
