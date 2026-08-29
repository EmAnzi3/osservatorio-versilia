#!/usr/bin/env python3
"""Gate browser desktop/mobile per Costa e mare v1.23.0."""
from __future__ import annotations

import argparse
from pathlib import Path
from urllib.parse import urljoin

from playwright.sync_api import Locator, Page, sync_playwright


METRICS = (
    "bathingWaterQuality",
    "bathingNonCompliantSamples",
    "blueFlagBeaches",
    "shorelineDynamics",
    "rigidDefenceProtectedCoast",
)
COASTAL = ("Camaiore", "Forte dei Marmi", "Pietrasanta", "Viareggio")
NOT_APPLICABLE = ("Massarosa", "Seravezza", "Stazzema")


def no_overflow(page: Page, label: str) -> None:
    overflow = page.evaluate(
        "document.documentElement.scrollWidth - document.documentElement.clientWidth"
    )
    assert overflow <= 1, f"Overflow orizzontale {label}: {overflow}px"


def open_metric(page: Page, key: str) -> None:
    button = page.locator(f'button[data-metric="{key}"]').first
    assert button.count() == 1, f"Indicatore non trovato: {key}"
    if not button.is_visible():
        group = button.locator(
            "xpath=ancestor::section[contains(concat(' ', normalize-space(@class), ' '), ' metric-group ')][1]"
        )
        assert group.count() == 1, f"Gruppo Costa e mare non trovato: {key}"
        group.locator(":scope > .metric-group-heading").click()
        page.wait_for_timeout(160)
    button.scroll_into_view_if_needed()
    button.click()
    page.wait_for_timeout(350)
    assert f"indicatore={key}" in page.url


def visible_bar(page: Page, town: str) -> Locator:
    rows = page.locator("#compare-bars .bar-row:visible").filter(has_text=town)
    assert rows.count() == 1, f"Riga {town} assente o duplicata"
    return rows


def assert_applicability(page: Page, key: str) -> None:
    rows = page.locator("#compare-bars .bar-row:visible")
    assert rows.count() == 7, f"{key}: attese 7 righe, trovate {rows.count()}"
    for town in COASTAL:
        row = visible_bar(page, town)
        assert "n.a." not in row.inner_text().lower(), f"{key}/{town}: valore costiero assente"
        assert row.locator(".comparison-dot").count() == 1, f"{key}/{town}: punto grafico assente"
    for town in NOT_APPLICABLE:
        row = visible_bar(page, town)
        text = row.inner_text().lower()
        assert "n.a." in text and "non applicabile" in text, f"{key}/{town}: n.a. non esplicito ({text})"
        assert row.locator(".comparison-dot").count() == 0, f"{key}/{town}: n.a. trasformato in punto zero"
        assert row.locator(".comparison-missing").count() == 1


def assert_detail(page: Page, key: str, mobile: bool) -> None:
    detail = page.locator("#compare-bars .coast-detail:visible")
    assert detail.count() == 1, f"{key}: dettaglio costiero assente o duplicato"
    if not detail.evaluate("element => element.open"):
        detail.locator("summary").click()
    assert detail.evaluate("element => element.open"), f"{key}: dettaglio costiero non aperto"
    assert detail.locator("tbody tr").count() == 4, f"{key}: dettaglio non limitato ai 4 Comuni costieri"
    text = detail.inner_text()
    assert all(town in text for town in COASTAL), f"{key}: manca un Comune costiero nel dettaglio ({text})"
    assert all(town not in text for town in NOT_APPLICABLE), f"{key}: Comune non costiero presente nel dettaglio ({text})"
    scroller = detail.locator(".indicator-table-scroll")
    state = scroller.evaluate("el => ({scroll:el.scrollWidth, client:el.clientWidth})")
    if mobile:
        assert state["scroll"] >= state["client"], state
    no_overflow(page, f"{key}/dettaglio")


def assert_coast_export(page: Page) -> None:
    with page.expect_download() as download_info:
        page.locator("#compare-tools [data-download]").click()
    download = download_info.value
    assert download.suggested_filename == "osservatorio-versilia-bathingWaterQuality.csv"
    content = Path(download.path()).read_text(encoding="utf-8-sig")
    lines = content.splitlines()
    assert len(lines) == 15, f"Export qualità: attese intestazione + 14 componenti, trovate {len(lines)}"
    assert '"Applicabilità"' in lines[0]
    assert sum('"Comune non costiero"' in line and '"n.a."' in line for line in lines[1:]) == 6
    assert any('"Camaiore"' in line and '"Aree eccellenti"' in line and '66.666' in line for line in lines[1:])


def assert_compare(page: Page, base: str, mobile: bool) -> None:
    page.goto(
        urljoin(base, f"confronta/ambiente/?indicatore={METRICS[0]}"),
        wait_until="networkidle",
    )
    page.wait_for_timeout(650)
    no_overflow(page, "Costa confronto mobile" if mobile else "Costa confronto desktop")
    body = page.locator("body").inner_text()
    assert "Costa e mare" in body and "Qualità delle aree di balneazione" in body

    for key in METRICS:
        open_metric(page, key)
        no_overflow(page, f"{key}/confronto")
        assert_applicability(page, key)
        assert_detail(page, key, mobile)
        definition = page.locator("#compare-definition").inner_text()
        assert "Versilia" in definition

        selector = page.locator("#compare-bars select[data-composite-component]:visible")
        if key == "bathingWaterQuality":
            assert selector.count() == 1 and selector.locator("option").count() == 2
            selector.select_option("part-1")
            page.wait_for_timeout(260)
            assert "90,1%" in visible_bar(page, "Camaiore").get_attribute("aria-label")
            assert "91,4%" in visible_bar(page, "Camaiore").get_attribute("aria-label")
            if not mobile:
                assert_coast_export(page)
        elif key == "bathingNonCompliantSamples":
            assert selector.count() == 1 and selector.locator("option").count() == 3
            selector.select_option("part-1")
            page.wait_for_timeout(260)
            assert "23,0%" in visible_bar(page, "Viareggio").get_attribute("aria-label")
        elif key == "shorelineDynamics":
            assert selector.count() == 1 and selector.locator("option").count() == 3
            selector.select_option("part-2")
            page.wait_for_timeout(260)
            assert "87,8%" in visible_bar(page, "Camaiore").get_attribute("aria-label")
        else:
            assert selector.count() == 0

    open_metric(page, "rigidDefenceProtectedCoast")
    viareggio = visible_bar(page, "Viareggio")
    aria = viareggio.get_attribute("aria-label") or ""
    assert "0,0%" in aria, f"Lo zero ISPRA di Viareggio non è conservato: {aria}"
    assert viareggio.locator(".comparison-dot").count() == 1

    open_metric(page, "blueFlagBeaches")
    shell = page.locator("#compare-bars > .ux-view-shell")
    assert shell.count() == 1, "Storico Bandiera Blu non disponibile"
    history_button = shell.locator('button[data-view-mode="history"]')
    assert history_button.count() == 1 and not history_button.is_disabled()
    history_button.click()
    page.wait_for_timeout(180)
    history = shell.locator('[data-view-pane="history"]:visible')
    assert "2019" in history.inner_text() and "2026" in history.inner_text()
    groups = history.locator(".ux-series-group")
    assert groups.count() == 5, f"Storico Bandiera Blu: attesi 4 Comuni costieri + Versilia, trovati {groups.count()}"
    legend = history.locator('.ux-history-legend[aria-label="Territori costieri e Versilia"]')
    assert legend.count() == 1 and "Versilia" in legend.inner_text()
    point = history.locator(".chart-point").first
    tooltip = point.locator(".chart-tooltip")
    assert point.count() == tooltip.count() == 1
    if mobile:
        point.click(force=True)
    else:
        point.hover(force=True)
    page.wait_for_timeout(80)
    assert tooltip.get_attribute("hidden") is None and tooltip.is_visible()


def assert_towns(page: Page, base: str, mobile: bool) -> None:
    page.goto(
        urljoin(base, "comuni/viareggio/?tema=ambiente&indicatore=bathingWaterQuality"),
        wait_until="networkidle",
    )
    page.wait_for_timeout(600)
    no_overflow(page, "Viareggio qualità balneazione")
    value = page.locator("#town-topic .town-metric-primary strong").first.inner_text()
    assert "83,3%" in value
    assert page.locator("#town-topic .coast-detail tbody tr").count() == 1
    selector = page.locator("#town-topic select[data-composite-choice]")
    assert selector.count() == 1
    selector.select_option("part-1")
    page.wait_for_timeout(220)
    assert "96,4%" in page.locator("#town-topic .town-metric-primary strong").first.inner_text()

    for key in METRICS:
        page.goto(
            urljoin(base, f"comuni/massarosa/?tema=ambiente&indicatore={key}"),
            wait_until="networkidle",
        )
        page.wait_for_timeout(420)
        no_overflow(page, f"Massarosa/{key}")
        primary = page.locator("#town-topic .town-metric-primary strong").first.inner_text().strip().lower()
        assert primary == "n.a.", f"{key}: Massarosa non è n.a. ({primary})"
        position = page.locator("#town-topic .versilia-position").inner_text().lower()
        assert "n.a." in position and "comune non costiero" in position
        applicability = page.locator("#town-topic .coast-not-applicable")
        assert applicability.count() == 1 and "non applicabile" in applicability.inner_text().lower()
        assert page.locator("#town-topic .trend-chart").count() == 0


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", required=True)
    args = parser.parse_args()
    base = args.base.rstrip("/") + "/"

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        desktop = browser.new_context(viewport={"width": 1440, "height": 1000})
        assert_compare(desktop.new_page(), base, mobile=False)
        assert_towns(desktop.new_page(), base, mobile=False)
        desktop.close()

        mobile = browser.new_context(
            viewport={"width": 390, "height": 844}, is_mobile=True, color_scheme="dark"
        )
        assert_compare(mobile.new_page(), base, mobile=True)
        assert_towns(mobile.new_page(), base, mobile=True)
        mobile.close()
        browser.close()

    print("Browser Costa e mare v1.23.0: selector, tooltip, 4 costieri + 3 n.a. e responsive verificati.")


if __name__ == "__main__":
    main()
