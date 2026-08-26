#!/usr/bin/env python3
"""Browser gate TPL: semantica, tooltip, layout e contesto sul dist reale."""
from __future__ import annotations

import argparse
from pathlib import Path
from urllib.parse import urljoin

from playwright.sync_api import Locator, sync_playwright


TRIPS = "scheduledTplTripsPer1000"
ACCESS = "activeTplAccessPoints"
SPAN = "tplServiceSpan"
FTTH = "ftthCoverageDesi"
FLOW = "outsideMunicipality"
TOWNS = (
    "Camaiore",
    "Forte dei Marmi",
    "Massarosa",
    "Pietrasanta",
    "Seravezza",
    "Stazzema",
    "Viareggio",
)


def assert_no_overflow(page, label: str) -> None:
    overflow = page.evaluate(
        "document.documentElement.scrollWidth - document.documentElement.clientWidth"
    )
    assert overflow <= 1, f"Overflow orizzontale {label}: {overflow}px"


def assert_element_not_clipped(locator: Locator, label: str) -> None:
    assert locator.count() == 1, f"Elemento non univoco: {label}"
    result = locator.evaluate(
        """el => {
          const r = el.getBoundingClientRect();
          const cs = getComputedStyle(el);
          return {
            scrollW: el.scrollWidth, clientW: el.clientWidth,
            scrollH: el.scrollHeight, clientH: el.clientHeight,
            left: r.left, right: r.right,
            overflowX: cs.overflowX, overflowY: cs.overflowY
          };
        }"""
    )
    if result["overflowX"] in {"hidden", "clip"}:
        assert result["scrollW"] <= result["clientW"] + 1, (
            f"Testo tagliato orizzontalmente in {label}: {result}"
        )
    if result["overflowY"] in {"hidden", "clip"}:
        assert result["scrollH"] <= result["clientH"] + 1, (
            f"Testo tagliato verticalmente in {label}: {result}"
        )


def assert_visible_metric_controls_not_clipped(page) -> None:
    for button in page.locator(".topic-controls button[data-metric]:visible").all():
        assert_element_not_clipped(button, f"pulsante indicatore {button.inner_text()[:45]}")


def open_metric_section(page, button: Locator, key: str) -> None:
    if button.is_visible():
        return
    group = button.locator(
        "xpath=ancestor::section[contains(concat(' ', normalize-space(@class), ' '), ' metric-group ')][1]"
    )
    assert group.count() == 1, f"Gruppo indicatore non trovato: {key}"
    heading = group.locator(":scope > .metric-group-heading")
    assert heading.count() == 1 and heading.get_attribute("role") == "button"
    heading.click()
    page.wait_for_timeout(180)
    assert button.is_visible(), f"La sezione accordion non rende visibile {key}"


def select_metric(page, key: str) -> None:
    button = page.locator(f'button[data-metric="{key}"]').first
    assert button.count() == 1, f"Indicatore non trovato: {key}"
    open_metric_section(page, button, key)
    button.scroll_into_view_if_needed()
    button.click()
    page.wait_for_timeout(320)
    assert f"indicatore={key}" in page.url


def screenshot(page, directory: Path | None, name: str) -> None:
    if directory is None:
        return
    directory.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(directory / name), full_page=True)


def screenshot_locator(locator: Locator, directory: Path | None, name: str) -> None:
    if directory is None:
        return
    directory.mkdir(parents=True, exist_ok=True)
    locator.screenshot(path=str(directory / name))


def assert_detail_note_fully_visible(detail: Locator, label: str) -> None:
    note = detail.locator(":scope > .tpl-detail-note")
    assert note.count() == 1, f"Nota TPL non univoca: {label}"
    state = detail.evaluate(
        """el => {
          const note = el.querySelector(':scope > .tpl-detail-note');
          const detailRect = el.getBoundingClientRect();
          const noteRect = note.getBoundingClientRect();
          const css = getComputedStyle(note);
          return {
            text: note.textContent.trim(),
            detailBottom: detailRect.bottom,
            noteBottom: noteRect.bottom,
            detailScrollH: el.scrollHeight,
            detailClientH: el.clientHeight,
            noteScrollH: note.scrollHeight,
            noteClientH: note.clientHeight,
            paddingBottom: parseFloat(css.paddingBottom)
          };
        }"""
    )
    assert state["text"], f"Nota TPL vuota: {label}"
    assert state["noteBottom"] <= state["detailBottom"] + 1, f"Nota oltre il box {label}: {state}"
    assert state["detailScrollH"] <= state["detailClientH"] + 1, f"Contenuto tagliato nel box {label}: {state}"
    assert state["noteScrollH"] <= state["noteClientH"] + 1, f"Testo nota tagliato {label}: {state}"
    assert state["paddingBottom"] >= 12, f"Spazio inferiore insufficiente {label}: {state}"


def assert_town_tpl_detail(detail: Locator, expected: dict[str, str]) -> None:
    cards = detail.locator(".tpl-town-service-grid > .deep-fact")
    assert cards.count() == 6, f"Dettaglio comunale TPL incompleto: {cards.count()} blocchi"
    by_label: dict[str, Locator] = {}
    for card in cards.all():
        # text_content conserva il testo sorgente: inner_text applica il
        # text-transform: uppercase della card e rende fragile il contratto.
        label = (card.locator(":scope > span").text_content() or "").strip()
        by_label[label] = card
        sizes = card.evaluate("el => ({scrollH:el.scrollHeight, clientH:el.clientHeight})")
        assert sizes["scrollH"] <= sizes["clientH"] + 1, f"Testo tagliato nella card {label}: {sizes}"
    assert tuple(by_label) == (
        "Corse programmate",
        "Bus",
        "Ferrovia",
        "Punti di accesso GTFS",
        "Route GTFS attive",
        "Finestra di servizio",
    )
    for label, value in expected.items():
        assert label in by_label, label
        assert by_label[label].locator(":scope > strong").inner_text().strip() == value, (
            label,
            by_label[label].inner_text(),
        )
    service = by_label["Finestra di servizio"]
    assert service.locator(".tpl-town-service-range").count() == 1
    assert service.locator(".tpl-town-service-span").count() == 1
    assert_detail_note_fully_visible(detail, "dettaglio comunale TPL")


def assert_bar_tooltip(page) -> None:
    row = page.locator("#compare-bars .bar-row").first
    label = row.locator(".bar-hover-label")
    assert row.count() == label.count() == 1
    row.hover()
    page.wait_for_timeout(120)
    state = label.evaluate(
        """el => {
          const r = el.getBoundingClientRect();
          return {opacity:getComputedStyle(el).opacity, left:r.left, right:r.right, text:el.textContent};
        }"""
    )
    assert float(state["opacity"]) > 0.9, f"Tooltip barra non visibile: {state}"
    assert "·" in state["text"] and state["text"].strip(), state
    viewport = page.viewport_size["width"]
    assert state["left"] >= -1 and state["right"] <= viewport + 1, f"Tooltip fuori viewport: {state}"


def assert_tpl_service_table(detail: Locator, mobile: bool = False) -> None:
    detail.locator("summary").click()
    assert detail.locator("tbody tr").count() == 7
    table_scroll = detail.locator(".indicator-table-scroll")
    sizes = table_scroll.evaluate("el => ({scroll:el.scrollWidth, client:el.clientWidth})")
    if mobile:
        assert sizes["scroll"] > sizes["client"], f"La tabella mobile non scorre internamente: {sizes}"
    else:
        assert sizes["scroll"] <= sizes["client"] + 1, f"La tabella desktop richiede scroll: {sizes}"
    for cell in detail.locator(".tpl-service-cell").all():
        service_range = cell.locator(".tpl-service-range")
        service_span = cell.locator(".tpl-service-span")
        assert service_range.count() == service_span.count() == 1
        range_box, span_box = service_range.bounding_box(), service_span.bounding_box()
        assert range_box and span_box
        assert span_box["y"] >= range_box["y"] + range_box["height"] + 2, cell.inner_text()
        font_sizes = cell.evaluate(
            "el => [getComputedStyle(el.querySelector('.tpl-service-range')).fontSize, getComputedStyle(el.querySelector('.tpl-service-span')).fontSize]"
        )
        assert font_sizes[0] == font_sizes[1], f"Font-size incoerente: {font_sizes}"
        assert "\n" in cell.inner_text(), f"Finestra di servizio non separata: {cell.inner_text()}"
    assert_detail_note_fully_visible(detail, "tabella TPL 7/7")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", required=True)
    parser.add_argument("--screenshots-dir")
    args = parser.parse_args()
    base = args.base.rstrip("/") + "/"
    shots = Path(args.screenshots_dir) if args.screenshots_dir else None

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()

        desktop = browser.new_context(viewport={"width": 1440, "height": 1000})
        page = desktop.new_page()
        page.goto(urljoin(base, f"confronta/mobilita/?indicatore={ACCESS}"), wait_until="networkidle")
        page.wait_for_timeout(700)
        assert_no_overflow(page, "confronto desktop")
        assert_visible_metric_controls_not_clipped(page)
        body = page.locator("body").inner_text()
        assert "Mobilità e infrastrutture" in body
        assert "Punti di accesso GTFS attivi" in body
        assert all(town in body for town in TOWNS)

        toolbar = page.locator("#compare-bars .tpl-chart-toolbar")
        assert toolbar.count() == 1
        assert page.locator("#compare-definition .scale-switch").count() == 0
        assert toolbar.locator('[data-scale="raw"]').count() == 1
        assert toolbar.locator('[data-scale="normalized"]').count() == 1
        bars_box = page.locator("#compare-bars").bounding_box()
        toggle_box = toolbar.locator(".scale-switch").bounding_box()
        assert bars_box and toggle_box
        assert bars_box["x"] <= toggle_box["x"]
        assert toggle_box["x"] + toggle_box["width"] <= bars_box["x"] + bars_box["width"] + 1

        definition = page.locator("#compare-definition").inner_text()
        assert "Media dei 7 Comuni" in definition
        assert "Totale nei 7 Comuni" not in definition
        assert "856" not in definition
        assert_bar_tooltip(page)
        screenshot(page, shots, "01-confronto-accessi-desktop.png")

        detail = page.locator(".tpl-compare-detail")
        assert detail.count() == 1
        assert_element_not_clipped(detail.locator("summary"), "summary dettaglio TPL")
        assert_tpl_service_table(detail)
        screenshot_locator(detail, shots, "02-dettaglio-tpl-desktop.png")

        page.locator('#compare-bars [data-scale="normalized"]').click()
        page.wait_for_timeout(260)
        normalized_definition = page.locator("#compare-definition").inner_text()
        assert "ogni 1.000" in normalized_definition
        assert "Media ponderata dei 7 Comuni" in normalized_definition
        assert page.locator("#compare-bars .tpl-chart-toolbar").count() == 1
        assert page.locator("#compare-definition .scale-switch").count() == 0
        assert "5,40 ogni 1.000" in normalized_definition

        select_metric(page, TRIPS)
        assert "Media dei 7 Comuni" in page.locator("#compare-definition").inner_text()
        select_metric(page, SPAN)
        assert "Media dei 7 Comuni" in page.locator("#compare-definition").inner_text()
        assert "h" in page.locator("#compare-bars").inner_text()
        desktop.close()

        mid = browser.new_context(viewport={"width": 1024, "height": 900})
        page = mid.new_page()
        page.goto(urljoin(base, f"confronta/mobilita/?indicatore={ACCESS}"), wait_until="networkidle")
        page.wait_for_timeout(650)
        assert_no_overflow(page, "confronto 1024")
        assert_visible_metric_controls_not_clipped(page)
        assert page.locator("#compare-bars .tpl-chart-toolbar").count() == 1
        screenshot(page, shots, "03-confronto-accessi-1024.png")
        mid.close()

        town = browser.new_context(viewport={"width": 1440, "height": 1000})
        page = town.new_page()
        page.goto(urljoin(base, f"comuni/viareggio/?tema=mobilita&indicatore={ACCESS}"), wait_until="networkidle")
        page.wait_for_timeout(700)
        assert_no_overflow(page, "Viareggio accessi")
        position_text = page.locator(".versilia-position").inner_text()
        assert "Media dei 7 Comuni" in position_text
        assert "856" not in position_text
        assert "sopra" in position_text.lower()
        assert "+107" in position_text.replace("−", "-")
        deep = page.locator(".tpl-town-deep-dive")
        assert deep.count() == 1
        assert "Trasporto pubblico programmato" in deep.inner_text()
        assert "Mostra origini e destinazioni" not in deep.inner_text()
        town_detail = deep.locator(".tpl-town-detail")
        town_detail.locator("summary").click()
        assert_town_tpl_detail(town_detail, {
            "Corse programmate": "659",
            "Bus": "549",
            "Ferrovia": "110",
            "Punti di accesso GTFS": "254",
            "Route GTFS attive": "21",
            "Finestra di servizio": "05:30–06:04 (+1 giorno)",
        })
        screenshot(page, shots, "04-viareggio-accessi-comune.png")
        screenshot_locator(town_detail, shots, "04b-viareggio-dettaglio-tpl.png")

        select_metric(page, FTTH)
        assert page.locator(".tpl-town-deep-dive").count() == 0
        town_topic = page.locator("#town-topic").inner_text()
        assert "Trasporto pubblico programmato" not in town_topic
        assert "Flussi di pendolarismo" not in town_topic
        select_metric(page, FLOW)
        town_topic = page.locator("#town-topic").inner_text()
        assert "Flussi di pendolarismo" in town_topic
        assert "Trasporto pubblico programmato" not in town_topic
        town.close()

        mobile = browser.new_context(viewport={"width": 390, "height": 844})
        page = mobile.new_page()
        page.goto(urljoin(base, f"confronta/mobilita/?indicatore={ACCESS}"), wait_until="networkidle")
        page.wait_for_timeout(700)
        assert_no_overflow(page, "confronto mobile")
        assert page.locator("#compare-bars .tpl-chart-toolbar").count() == 1
        detail = page.locator(".tpl-compare-detail")
        assert_element_not_clipped(detail.locator("summary"), "summary dettaglio mobile")
        assert_tpl_service_table(detail, mobile=True)
        assert_no_overflow(page, "dettaglio confronto mobile")
        screenshot(page, shots, "05-confronto-mobile.png")
        screenshot_locator(detail, shots, "05b-dettaglio-tpl-mobile.png")

        page.goto(urljoin(base, f"comuni/massarosa/?tema=mobilita&indicatore={TRIPS}"), wait_until="networkidle")
        page.wait_for_timeout(600)
        assert_no_overflow(page, "Massarosa TPL mobile")
        town_detail = page.locator(".tpl-town-detail")
        assert town_detail.count() == 1
        town_detail.locator("summary").click()
        assert_town_tpl_detail(town_detail, {
            "Corse programmate": "106",
            "Bus": "86",
            "Ferrovia": "20",
            "Punti di accesso GTFS": "131",
            "Route GTFS attive": "6",
            "Finestra di servizio": "05:52–21:34",
        })
        assert "15,71 h" in town_detail.locator(".tpl-town-service-span").inner_text()
        assert "Mostra origini e destinazioni" not in page.locator("#town-topic").inner_text()
        screenshot(page, shots, "06-massarosa-tpl-mobile.png")
        screenshot_locator(town_detail, shots, "06b-massarosa-dettaglio-tpl-mobile.png")

        page.goto(urljoin(base, f"comuni/forte-dei-marmi/?tema=mobilita&indicatore={TRIPS}"), wait_until="networkidle")
        page.wait_for_timeout(450)
        town_detail = page.locator(".tpl-town-detail")
        town_detail.locator("summary").click()
        assert_town_tpl_detail(town_detail, {"Ferrovia": "0"})
        assert "n.d." not in town_detail.inner_text().lower()
        mobile.close()

        browser.close()

    print(
        "Browser gate Mobilità TPL superato: tooltip, benchmark medi, toggle nel grafico, "
        "nessun clipping e deep dive contestuale."
    )


if __name__ == "__main__":
    main()
