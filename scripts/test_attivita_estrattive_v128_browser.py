#!/usr/bin/env python3
"""Smoke browser desktop/mobile del lotto Attività estrattive v1.28.0."""
from __future__ import annotations

import argparse
from urllib.parse import urljoin

from playwright.sync_api import Page, sync_playwright


def no_page_overflow(page: Page, label: str) -> None:
    overflow = page.evaluate("() => document.documentElement.scrollWidth - document.documentElement.clientWidth")
    assert overflow <= 2, f"{label}: overflow orizzontale pagina di {overflow}px"


def wait_town_metric(page: Page, metric_key: str) -> None:
    """Attende la selezione reale dell'indicatore nella scheda comunale.

    Nelle schede comunali il titolo completo dell'indicatore non è sempre
    renderizzato come testo visibile: il contratto stabile è il tab attivo
    data-metric e il contenuto del pannello #town-topic.
    """
    page.locator(f'button[data-metric="{metric_key}"].active').first.wait_for()
    page.locator("#town-topic").wait_for()


def compare_sites(page: Page, base: str) -> None:
    page.goto(urljoin(base, "confronta/ambiente/?indicatore=extractiveSites"), wait_until="networkidle")
    page.get_by_text("Siti censiti in RTCave", exact=True).first.wait_for()
    selector = page.locator("#compare-bars select[data-composite-component]:visible")
    assert selector.count() == 1
    assert selector.locator("option").count() == 14
    labels = selector.locator("option").all_inner_texts()
    assert labels[0] == "Tutti"
    assert "Stato · Attivi" in labels
    assert "Tipologia · Piano di recupero" in labels
    assert "Produzione · Ornamentale" in labels
    selector.select_option("part-1")
    page.wait_for_timeout(180)
    text = page.locator("#compare-bars").inner_text()
    assert "Seravezza" in text and "Stazzema" in text
    assert "Attivi" in text and "Chiusi" in text
    no_page_overflow(page, "RTCave confronto")


def town_rtcave(page: Page, base: str) -> None:
    page.goto(urljoin(base, "comuni/massarosa/?tema=ambiente&indicatore=extractiveSites"), wait_until="networkidle")
    wait_town_metric(page, "extractiveSites")
    detail = page.locator("#town-topic .extractive-detail:visible")
    detail.wait_for()
    assert detail.count() == 1
    text = detail.inner_text()
    assert "Anagrafica pubblica RTCave" in text
    assert "09046018002" in text
    assert "SULLA PIEVE" in text
    assert "Inattiva" in text
    assert "INDUSTRIALE" in text
    assert "Fuori Comprensorio" in text
    no_page_overflow(page, "RTCave Massarosa")

    # Regressione segnalata: al primo caricamento Seravezza deve mostrare
    # subito 44/90 = 48,89%, senza passare dal confronto generico con la media.
    page.goto(urljoin(base, "comuni/seravezza/?tema=ambiente&indicatore=extractiveSites"), wait_until="networkidle")
    wait_town_metric(page, "extractiveSites")
    position = page.locator("#town-topic .composite-versilia-position")
    position.wait_for()
    position_text = position.inner_text()
    assert "peso sulla versilia" in position_text.lower()
    assert "48,89%" in position_text or "48.89%" in position_text
    no_page_overflow(page, "RTCave Seravezza")

    # Stazzema resta il caso di regressione per lista lunga, n.d. e scrolling interno.
    page.goto(urljoin(base, "comuni/stazzema/?tema=ambiente&indicatore=extractiveSites"), wait_until="networkidle")
    wait_town_metric(page, "extractiveSites")
    detail = page.locator("#town-topic .extractive-detail:visible")
    detail.wait_for()
    text = detail.inner_text()
    scroll = detail.locator(".extractive-records-scroll")
    assert scroll.count() == 1
    scroll_state = scroll.evaluate("(el) => ({scrollHeight: el.scrollHeight, clientHeight: el.clientHeight, overflowY: getComputedStyle(el).overflowY, left: el.getBoundingClientRect().left, parentLeft: el.closest('.extractive-detail').getBoundingClientRect().left})")
    assert scroll_state["scrollHeight"] > scroll_state["clientHeight"]
    assert scroll_state["overflowY"] in ("auto", "scroll")
    assert scroll_state["left"] - scroll_state["parentLeft"] >= 15
    assert "TOMBACCIO" in text
    assert "Piano di recupero" in text
    assert "COSTRUZIONE" in text
    assert "n.d." in text
    no_page_overflow(page, "RTCave Stazzema")


def production(page: Page, base: str) -> None:
    page.goto(urljoin(base, "confronta/ambiente/?indicatore=extractiveProduction"), wait_until="networkidle")
    page.get_by_text("Produzione estrattiva", exact=True).first.wait_for()
    assert "79.452" in page.locator("#compare-definition").inner_text()
    detail = page.locator("#compare-bars .extractive-detail:visible")
    detail.wait_for()
    assert detail.count() == 1
    text = detail.inner_text()
    assert "2019" in text and "2025" in text
    assert "Seravezza" in text and "Stazzema" in text
    assert "55.801" in text and "23.651" in text
    no_page_overflow(page, "Produzione confronto")

    page.goto(urljoin(base, "comuni/seravezza/?tema=ambiente&indicatore=extractiveProduction"), wait_until="networkidle")
    wait_town_metric(page, "extractiveProduction")
    detail = page.locator("#town-topic .extractive-detail:visible")
    detail.wait_for()
    assert "55.801" in detail.inner_text()
    chart = page.locator("#town-topic .history-panel .trend-chart:visible")
    chart.wait_for()
    chart_text = chart.inner_text()
    assert "2019" in chart_text and "2025" in chart_text
    position = page.locator("#town-topic .versilia-position")
    position.wait_for()
    pos_text = position.inner_text()
    assert "79.452" in pos_text
    assert "n.d." not in pos_text.lower()
    table = detail.locator("table.indicator-values-table:visible")
    assert table.count() == 1
    table_text = table.inner_text()
    assert "2019" in table_text and "2025" in table_text
    assert "55.801" in table_text
    no_page_overflow(page, "Produzione Seravezza")

    page.goto(urljoin(base, "comuni/camaiore/?tema=ambiente&indicatore=extractiveProduction"), wait_until="networkidle")
    wait_town_metric(page, "extractiveProduction")
    page.get_by_text("Produzione comunale n.d.", exact=True).wait_for()
    assert "n.d." in page.locator("#town-topic").inner_text().lower()


def planning(page: Page, base: str) -> None:
    page.goto(urljoin(base, "confronta/ambiente/?indicatore=extractivePlanning"), wait_until="networkidle")
    page.get_by_text("Quadro estrattivo PRC", exact=True).first.wait_for()
    selector = page.locator("#compare-bars select[data-composite-component]:visible")
    assert selector.count() == 1
    assert selector.locator("option").count() == 9
    labels = selector.locator("option").all_inner_texts()
    assert "Giacimenti · superficie" in labels
    assert "Giacimenti potenziali · % territorio" in labels
    assert "ACC · numero" in labels
    selector.select_option("part-6")
    page.wait_for_timeout(180)
    detail = page.locator("#compare-bars .extractive-detail:visible")
    detail.wait_for()
    text = detail.inner_text()
    assert "156,32" in text or "156.32" in text
    assert "400,17" in text or "400.17" in text
    dom_text = detail.text_content() or ""
    assert "SED censiti" in dom_text
    no_page_overflow(page, "PRC confronto")

    page.goto(urljoin(base, "comuni/seravezza/?tema=ambiente&indicatore=extractivePlanning"), wait_until="networkidle")
    wait_town_metric(page, "extractivePlanning")
    select = page.locator("#town-topic select[data-composite-choice]")
    select.wait_for()
    select.select_option("part-1")
    page.wait_for_timeout(250)
    position = page.locator("#town-topic .composite-versilia-position")
    position_text = position.inner_text()
    assert "quota territoriale versilia" in position_text.lower()
    assert ("0,16%" in position_text or "0.16%" in position_text)
    assert ("0,97%" in position_text or "0.97%" in position_text)
    assert "603" not in position_text
    no_page_overflow(page, "PRC quota territorio Seravezza")

    page.goto(urljoin(base, "comuni/pietrasanta/?tema=ambiente&indicatore=extractivePlanning"), wait_until="networkidle")
    wait_town_metric(page, "extractivePlanning")
    detail = page.locator("#town-topic .extractive-detail:visible")
    detail.wait_for()
    text = detail.inner_text()
    assert "11,39" in text or "11.39" in text
    assert "22" in text
    no_page_overflow(page, "PRC Pietrasanta")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", required=True)
    args = parser.parse_args()
    base = args.base.rstrip("/") + "/"

    with sync_playwright() as p:
        browser = p.chromium.launch()
        for width, height, label in ((1366, 900, "desktop"), (390, 844, "mobile")):
            page = browser.new_page(viewport={"width": width, "height": height})
            compare_sites(page, base)
            town_rtcave(page, base)
            production(page, base)
            planning(page, base)
            page.close()
            print(f"Attività estrattive browser {label}: OK")
        browser.close()


if __name__ == "__main__":
    main()
