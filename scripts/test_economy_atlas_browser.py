#!/usr/bin/env python3
"""Browser contract for Economia II · Atlante ATECO v1.31."""
from __future__ import annotations

import argparse
import contextlib
import os
import socket
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from playwright.sync_api import sync_playwright

TOWNS = {
    "camaiore": "Camaiore",
    "forte-dei-marmi": "Forte dei Marmi",
    "massarosa": "Massarosa",
    "pietrasanta": "Pietrasanta",
    "seravezza": "Seravezza",
    "stazzema": "Stazzema",
    "viareggio": "Viareggio",
}
SECTION_COUNTS = {
    "redditi": 6,
    "costi-fiscalita": 4,
    "produzione": 10,
    "imprenditorialita": 2,
    "turismo": 9,
    "atlante": 1,
}
CASES = ("30", "301", "56.1", "68.1", "68.2", "68.3", "68.31", "56.10.11")
ATLAS_ROUTE = "confronta/economia/atlante-attivita-economiche/"


class Quiet(SimpleHTTPRequestHandler):
    def log_message(self, *_args: object) -> None:
        return


@contextlib.contextmanager
def server(directory: Path):
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    old = os.getcwd()
    os.chdir(directory)
    httpd = ThreadingHTTPServer(("127.0.0.1", port), Quiet)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{port}/"
    finally:
        httpd.shutdown()
        thread.join(timeout=5)
        os.chdir(old)


def wait_atlas(page):
    page.wait_for_function(
        """() => {
          const el = document.querySelector('ov-economy-atlas');
          return !!el?.shadowRoot?.querySelector('#territory');
        }""",
        timeout=20000,
    )


def wait_catalog(page):
    page.wait_for_selector(".metric-catalog", timeout=15000)
    page.wait_for_timeout(300)


def assert_page_no_overflow(page):
    overflow = page.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth")
    assert overflow <= 1, f"Overflow pagina: {overflow}px"


def assert_atlas_no_overflow(page):
    assert_page_no_overflow(page)
    overflow = page.eval_on_selector(
        "ov-economy-atlas",
        "el => Math.max(0, el.shadowRoot.querySelector('.explorer').scrollWidth - el.getBoundingClientRect().width)",
    )
    assert overflow <= 1, f"Overflow Atlante: {overflow}px"


def choose_code(page, query: str):
    host = page.locator("ov-economy-atlas")
    search = host.locator("#search")
    search.fill(query)
    results = host.locator("#results .result")
    results.first.wait_for(state="visible", timeout=5000)
    target = None
    needle = query.replace(".", "")
    for index in range(results.count()):
        code = results.nth(index).locator(".result-code").inner_text().replace(".", "").replace(" ", "")
        if code.endswith(needle.replace(" ", "")):
            target = results.nth(index)
            break
    (target or results.first).click()
    page.wait_for_timeout(100)
    title = host.locator("#analysis .selected-title code").first.inner_text()
    assert needle in title.replace(".", "").replace(" ", ""), (query, title)


def assert_section_contract(page, town: str | None = None):
    total = 0
    for key, expected in SECTION_COUNTS.items():
        group = page.locator(f'.metric-group[data-section="{key}"]')
        assert group.count() == 1, f"Sezione Economia mancante/duplicata: {key}"
        actual = group.locator(".metric-group-buttons").locator("button, a.metric-route-link").count()
        assert actual == expected, (key, actual, expected)
        total += actual
    assert total == 32, total

    atlas_group = page.locator('.metric-group[data-section="atlante"]')
    assert "atlante delle attività economiche" in atlas_group.inner_text().casefold()
    atlas_link = atlas_group.locator("a.metric-route-link")
    assert atlas_link.count() == 1
    href = atlas_link.get_attribute("href") or ""
    assert "/confronta/economia/atlante-attivita-economiche/" in href
    if town:
        assert f"comune={town}" in href, (town, href)
    else:
        assert "comune=" not in href, href
    assert page.locator('.metric-group[data-section="produzione"] a.metric-route-link').count() == 0

    count_label = atlas_group.locator(".ux-section-tools > span:first-child")
    if count_label.count():
        assert count_label.inner_text().strip() == "1 indicatore"


def test_standalone(page, base: str, width: int):
    page.set_viewport_size({"width": width, "height": 980})
    page.goto(base + ATLAS_ROUTE, wait_until="networkidle")
    wait_atlas(page)
    assert page.locator('link[rel="canonical"]').get_attribute("href") == "https://osservatorioversilia.it/confronta/economia/atlante-attivita-economiche/"
    assert page.locator("ov-economy-atlas").count() == 1
    assert not page.locator('script[src*="ateco-detail"],link[href*="ateco-detail"]').count()
    host = page.locator("ov-economy-atlas")
    assert host.locator("#territory option").count() == 8
    assert host.locator("#territory").input_value() == ""
    assert "versilia" in host.locator("#donutCenter").inner_text().casefold()
    assert host.locator(".hero-symbol svg").count() == 1
    assert "AT" not in host.locator(".hero-symbol").inner_text()
    assert_atlas_no_overflow(page)

    if width == 1440:
        selects = host.locator("#selectors select")
        selects.nth(0).select_option("G")
        page.wait_for_timeout(100)
        assert "commercio" in host.locator("#donutCenter").inner_text().casefold()
        for case in CASES:
            choose_code(page, case)
        choose_code(page, "09")
        singleton_title = host.locator("#analysis .selected-title code").first.inner_text()
        assert "09.90.09" in singleton_title, singleton_title
        host.locator("#modeNavigation").click()
        host.locator("#tabHistory").click()
        assert host.locator("#analysis .history-chart").count() == 1
        host.locator("#tabCurrent").click()
        host.locator("#modeComposition").click()
        assert host.locator("#analysis .kpis").count() == 1
    assert_atlas_no_overflow(page)


def test_territory(page, base: str):
    page.set_viewport_size({"width": 1440, "height": 1000})
    page.goto(base + ATLAS_ROUTE + "?comune=viareggio", wait_until="networkidle")
    wait_atlas(page)
    host = page.locator("ov-economy-atlas")
    territory = host.locator("#territory")
    assert territory.input_value() == "viareggio"
    center = host.locator("#donutCenter").inner_text()
    assert "Viareggio" in center, center
    assert "7.809" in center, center
    assert "Viareggio" in host.locator(".hero h1").inner_text()
    assert "Viareggio" in host.locator(".quick-title").inner_text()

    choose_code(page, "68.31")
    assert "Viareggio" in host.locator("#analysisHeading").inner_text()

    territory.select_option("massarosa")
    page.wait_for_timeout(150)
    assert "comune=massarosa" in page.url
    center = host.locator("#donutCenter").inner_text()
    assert "Massarosa" in center, center
    assert "1.815" in center, center
    assert "Massarosa" in host.locator(".hero h1").inner_text()
    assert "Massarosa" in host.locator(".quick-title").inner_text()

    territory.select_option("")
    page.wait_for_timeout(150)
    assert "comune=" not in page.url
    assert "Versilia" in host.locator("#donutCenter").inner_text()
    assert_atlas_no_overflow(page)


def test_compare_catalog(page, base: str, screenshots: Path):
    page.set_viewport_size({"width": 1440, "height": 1000})
    page.goto(base + "confronta/economia/?indicatore=industryValueAddedShare", wait_until="networkidle")
    wait_catalog(page)
    assert_section_contract(page)
    atlas_heading = page.locator('.metric-group[data-section="atlante"] .metric-group-heading')
    atlas_heading.click()
    page.wait_for_timeout(100)
    assert page.locator('.metric-group[data-section="atlante"] a.metric-route-link').is_visible()
    page.screenshot(path=str(screenshots / "economia-catalogo-32.png"), full_page=True)
    assert_page_no_overflow(page)


def test_towns(page, base: str, screenshots: Path):
    page.set_viewport_size({"width": 1280, "height": 950})
    for slug, name in TOWNS.items():
        page.goto(base + f"comuni/{slug}/?tema=economia&indicatore=incomeDistribution", wait_until="networkidle")
        wait_catalog(page)
        assert page.locator("ov-economy-atlas").count() == 0, f"Atlante incorporato indebitamente in {name}"
        assert page.locator("text=Principali settori per addetti").count() == 0
        assert_section_contract(page, slug)
        assert_page_no_overflow(page)
        if slug == "viareggio":
            atlas_group = page.locator('.metric-group[data-section="atlante"]')
            atlas_group.locator(".metric-group-heading").click()
            page.wait_for_timeout(100)
            page.screenshot(path=str(screenshots / "viareggio-economia-catalogo.png"), full_page=True)
            atlas_group.locator("a.metric-route-link").click()
            page.wait_for_url(f"**/{ATLAS_ROUTE}?comune=viareggio", timeout=10000)
            wait_atlas(page)
            assert page.locator("ov-economy-atlas").locator("#territory").input_value() == "viareggio"
            assert "Viareggio" in page.locator("ov-economy-atlas").locator("#donutCenter").inner_text()


def test_catalog_and_search(page, base: str):
    page.set_viewport_size({"width": 1440, "height": 980})
    page.goto(base, wait_until="networkidle")
    assert "184 indicatori" in page.locator("body").inner_text().casefold()
    economy_card = page.locator('[data-theme="economia"]')
    assert "32 indicatori" in economy_card.inner_text().casefold()
    page.locator(".global-search-trigger").click()
    search = page.locator(".search-overlay input")
    search.fill("atlante attività economiche")
    result = page.locator('.search-results a[href*="atlante-attivita-economiche"]').first
    result.wait_for(state="visible", timeout=5000)
    assert "atlante delle attività economiche" in result.inner_text().casefold()


def capture_atlas(page, base: str, screenshots: Path):
    page.set_viewport_size({"width": 1440, "height": 1000})
    page.goto(base + ATLAS_ROUTE, wait_until="networkidle")
    wait_atlas(page)
    page.screenshot(path=str(screenshots / "atlante-versilia.png"), full_page=True)

    page.goto(base + ATLAS_ROUTE + "?comune=viareggio", wait_until="networkidle")
    wait_atlas(page)
    page.screenshot(path=str(screenshots / "atlante-viareggio.png"), full_page=True)

    page.set_viewport_size({"width": 390, "height": 1000})
    page.screenshot(path=str(screenshots / "atlante-mobile.png"), full_page=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--directory", default="dist")
    parser.add_argument("--screenshots-dir", default="reports/economia-atlas-browser")
    args = parser.parse_args()
    directory = Path(args.directory).resolve()
    screenshots = Path(args.screenshots_dir).resolve()
    screenshots.mkdir(parents=True, exist_ok=True)

    with server(directory) as base, sync_playwright() as pw:
        launch_kwargs = {"headless": True}
        if os.environ.get("OV_CHROMIUM_EXECUTABLE"):
            launch_kwargs["executable_path"] = os.environ["OV_CHROMIUM_EXECUTABLE"]
        browser = pw.chromium.launch(**launch_kwargs)
        page = browser.new_page()
        console_errors: list[str] = []
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)

        for width in (1440, 1024, 390):
            test_standalone(page, base, width)
        test_territory(page, base)
        test_compare_catalog(page, base, screenshots)
        test_towns(page, base, screenshots)
        test_catalog_and_search(page, base)
        capture_atlas(page, base, screenshots)

        browser.close()
        blocking = [item for item in console_errors if "favicon" not in item.lower()]
        assert not blocking, f"Console errors: {blocking[:5]}"

    print("Atlante browser OK: 32 visibili, sezione autonoma, 7 deep link comunali, territorio esclusivo, responsive.")


if __name__ == "__main__":
    main()
