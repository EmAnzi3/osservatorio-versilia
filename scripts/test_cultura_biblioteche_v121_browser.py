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
APP_BUNDLE_VERSION = "20260827-v121-history-ui3"
HISTORY_ASSET_VERSION = "20260827-v121-history-ui6"


def assert_production_bundle_version(page) -> None:
    scripts = page.locator('script[src*="assets/app-bundle.js"]')
    assert scripts.count() == 1, f"Bundle applicativo di produzione assente o duplicato: {scripts.count()}"
    src = scripts.first.get_attribute("src") or ""
    assert f"v={APP_BUNDLE_VERSION}" in src, f"Cache-buster bundle inatteso: {src}"


def assert_town_history(page, base: str, mobile: bool) -> None:
    for key, _short_label in METRICS:
        page.goto(
            urljoin(base, f"comuni/camaiore/?tema=comunita&indicatore={key}"),
            wait_until="networkidle",
        )
        page.wait_for_timeout(450)
        assert_production_bundle_version(page)
        history_script = page.locator(
            f'script[src*="assets/ux-history.js?v={HISTORY_ASSET_VERSION}"]'
        )
        assert history_script.count() == 1, f"Camaiore/{key}: asset storico non aggiornato"
        no_overflow(page, f"Camaiore/{key}/storico")
        topic = page.locator("#town-topic")
        assert topic.count() == 1, f"Camaiore/{key}: contenitore tema assente"
        selected = topic.locator(f'button[data-metric="{key}"]').first
        assert selected.count() == 1 and selected.get_attribute("aria-selected") == "true", f"Camaiore/{key}: indicatore non selezionato"
        shell = topic.locator(".history-panel .ux-view-shell")
        assert shell.count() == 1, f"Camaiore/{key}: switch Attuale/Storico assente"
        current_button = shell.locator('button[data-view-mode="current"]')
        history_button = shell.locator('button[data-view-mode="history"]')
        assert current_button.count() == 1 and history_button.count() == 1, f"Camaiore/{key}: toggle incompleto"
        assert not history_button.is_disabled(), f"Camaiore/{key}: Storico disabilitato nonostante la serie disponibile"
        history_button.click()
        page.wait_for_timeout(120)
        history_pane = shell.locator('[data-view-pane="history"]')
        assert history_pane.is_visible(), f"Camaiore/{key}: pannello Storico non visibile dopo click"
        chart = history_pane.locator(".trend-chart")
        assert chart.count() == 1 and chart.locator("svg").count() == 1, f"Camaiore/{key}: grafico storico non renderizzato"
        points = chart.locator(".chart-point")
        assert points.count() >= 3, f"Camaiore/{key}: punti storici insufficienti"
        point = points.nth(2)
        tooltip = point.locator(".chart-tooltip")
        assert tooltip.count() == 1, f"Camaiore/{key}: markup tooltip assente"
        assert tooltip.get_attribute("hidden") is not None, f"Camaiore/{key}: tooltip aperto prima dell'interazione"
        if mobile:
            point.click(force=True)
        else:
            point.hover(force=True)
        page.wait_for_timeout(100)
        assert tooltip.get_attribute("hidden") is None, f"Camaiore/{key}: tooltip non attivato"
        assert tooltip.is_visible(), f"Camaiore/{key}: tooltip attivato ma non visibile"
        current_button.click()
        page.wait_for_timeout(80)
        assert shell.locator('[data-view-pane="current"] .ux-comparison-bars').count() == 1, f"Camaiore/{key}: vista Valore attuale assente"


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
    assert bars.count() == 7, f"{key}: attese 7 righe comunali, trovate {bars.count()}"
    for town in ("Massarosa", "Stazzema"):
        row = bars.filter(has_text=town)
        assert row.count() == 1, f"{key}: riga {town} assente o duplicata"
        text = row.inner_text().lower()
        assert "n.d." in text, f"{key}/{town}: il mancante non è mostrato come n.d. ({text})"


def assert_town_missing_metrics(page, base: str, slug: str, town: str) -> None:
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
    assert_production_bundle_version(page)
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
        shell = page.locator("#compare-bars > .ux-view-shell")
        assert shell.count() == 1, f"{key}: switch Attuale/Storico assente nel confronto"
        current_button = shell.locator('button[data-view-mode="current"]')
        history_button = shell.locator('button[data-view-mode="history"]')
        assert current_button.count() == 1 and history_button.count() == 1, f"{key}: toggle confronto incompleto"
        assert not history_button.is_disabled(), f"{key}: Storico disabilitato nel confronto"
        current_pane = shell.locator('[data-view-pane="current"]')
        assert current_pane.is_visible(), f"{key}: Valore attuale non visibile inizialmente"
        assert_missing_rows(current_pane.locator(".bar-row"), key)

        history_button.click()
        page.wait_for_timeout(120)
        history_pane = shell.locator('[data-view-pane="history"]')
        assert history_pane.is_visible(), f"{key}: Storico non visibile dopo click"
        history = history_pane.locator(".library-history-chart")
        assert history.count() == 1, f"{key}: grafico storico non visibile nel pannello Storico"
        assert history.locator("table").count() == 0, f"{key}: lo storico non deve essere tabellare"
        chart = history.locator(".ux-history-chart")
        assert chart.count() == 1 and chart.locator("svg").count() == 1, f"{key}: SVG storico assente"
        assert chart.locator(".ux-series-group").count() == 6, f"{key}: attese 6 serie comunali osservate"
        assert chart.locator(".chart-point").count() >= 12, f"{key}: punti storici insufficienti"
        first_point = chart.locator(".chart-point").first
        tooltip = first_point.locator(".chart-tooltip")
        assert tooltip.count() == 1, f"{key}: markup tooltip storico assente"
        first_point.dispatch_event("mouseenter")
        page.wait_for_timeout(60)
        assert tooltip.get_attribute("hidden") is None, f"{key}: tooltip storico non viene attivato"
        first_point.dispatch_event("mouseleave")
        assert tooltip.get_attribute("hidden") is not None, f"{key}: tooltip storico non viene chiuso"
        history_text = history.inner_text()
        assert "Stazzema · n.d." in history_text, f"{key}: assenza storica Stazzema non esplicita"
        if key in ("libraryLoansPerResident", "libraryActiveBorrowersPer100"):
            assert "1998" in history_text and "2024" in history_text and "2020" in history_text
        else:
            assert "2022" in history_text and "2024" in history_text and "2021" not in history_text

        current_button.click()
        page.wait_for_timeout(80)
        assert current_pane.is_visible(), f"{key}: ritorno a Valore attuale non riuscito"

    assert_town_history(page, base, mobile)
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

    print("Browser Cultura v1.21 verificato: storici grafici con tooltip, switch Attuale/Storico, n.d. espliciti, desktop/mobile e chiaro/scuro.")


if __name__ == "__main__":
    main()
