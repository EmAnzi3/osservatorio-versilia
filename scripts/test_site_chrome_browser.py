#!/usr/bin/env python3
"""Regressione browser: shell canonica, qualità responsive e budget Lighthouse."""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
from urllib.parse import urljoin

from playwright.sync_api import Page, sync_playwright

from test_browser_quality_gate import run_gate
from test_lighthouse_budget import run_budget
from test_opportunity_release_browser import verify_release as verify_opportunity_release


ROOT = Path(__file__).resolve().parents[1]
REFERENCE = "stato-dati/"
SPECIAL_ROUTES = (
    "pnrr/",
    "opportunita/",
    "percorsi/",
    "percorsi/metodo.html",
    "confronta/meteo-clima/",
)
GEOMETRY_SELECTORS = (
    ".site-header",
    ".site-header-inner",
    ".site-brand",
    ".site-brand-mark",
    ".site-brand-copy",
    ".global-search-trigger",
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def open_page(page: Page, base: str, route: str) -> None:
    page.goto(urljoin(base, route), wait_until="domcontentloaded")
    page.wait_for_selector(".site-header .global-search-trigger", state="visible")
    page.wait_for_function("document.fonts ? document.fonts.status === 'loaded' : true")
    # Alcune route rimontano la shell subito dopo DOMContentLoaded. Aspettiamo il
    # remount e richiediamo nuovamente l'header visibile prima delle misure.
    page.wait_for_timeout(350)
    page.wait_for_selector(".site-header .global-search-trigger", state="visible")


def stable_box(page: Page, selector: str) -> dict[str, float]:
    locator = page.locator(selector).first
    for _ in range(20):
        try:
            locator.wait_for(state="visible", timeout=500)
            box = locator.bounding_box()
            if box is not None:
                page.wait_for_timeout(50)
                confirm = locator.bounding_box()
                if confirm is not None:
                    return confirm
        except Exception:
            pass
        page.wait_for_timeout(50)
    raise AssertionError(f"Elemento senza geometria stabile: {selector}")


def geometry(page: Page) -> dict[str, dict[str, float]]:
    result: dict[str, dict[str, float]] = {}
    for selector in GEOMETRY_SELECTORS:
        box = stable_box(page, selector)
        result[selector] = {key: round(float(box[key]), 2) for key in ("x", "y", "width", "height")}
    return result


def assert_geometry(reference: dict[str, dict[str, float]], actual: dict[str, dict[str, float]], route: str) -> None:
    for selector, expected_box in reference.items():
        for key, expected in expected_box.items():
            found = actual[selector][key]
            require(
                abs(found - expected) <= 0.75,
                f"Geometria header diversa in {route}: {selector} {key}={found}, atteso {expected}",
            )


def style_fingerprint(page: Page) -> dict[str, str]:
    return page.evaluate(
        """() => {
          const header = getComputedStyle(document.querySelector('.site-header'));
          const brand = getComputedStyle(document.querySelector('.site-brand-copy strong'));
          const search = getComputedStyle(document.querySelector('.global-search-trigger'));
          const mark = getComputedStyle(document.querySelector('.site-brand-mark'));
          return {
            headerBackground: header.backgroundColor,
            headerBorder: header.borderBottomColor,
            brandColor: brand.color,
            brandFont: brand.fontFamily,
            brandWeight: brand.fontWeight,
            searchColor: search.color,
            searchBorder: search.borderColor,
            markWidth: mark.width,
            markHeight: mark.height
          };
        }"""
    )


def assert_search(page: Page, route: str) -> None:
    trigger = page.locator(".global-search-trigger")
    require(trigger.evaluate("node => node.tagName") == "BUTTON", f"Cerca non è un pulsante in {route}")
    require(trigger.locator("kbd").inner_text().strip() == "/", f"Scorciatoia / assente in {route}")
    trigger.click()
    overlay = page.locator(".search-overlay")
    overlay.wait_for(state="visible")
    require(trigger.get_attribute("aria-expanded") == "true", f"Cerca non si apre in {route}")
    page.keyboard.press("Escape")
    overlay.wait_for(state="hidden")


def header_capture(page: Page) -> bytes:
    return page.locator(".site-header").screenshot(animations="disabled")


def verify_viewport(base: str, width: int, height: int) -> None:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": width, "height": height}, device_scale_factor=1)
        open_page(page, base, REFERENCE)
        reference_geometry = geometry(page)
        reference_style = style_fingerprint(page)
        reference_image = header_capture(page)
        reference_digest = hashlib.sha256(reference_image).hexdigest()

        for route in SPECIAL_ROUTES:
            open_page(page, base, route)
            assert_geometry(reference_geometry, geometry(page), route)
            actual_style = style_fingerprint(page)
            require(
                actual_style == reference_style,
                f"Stili header diversi in {route}: {actual_style} != {reference_style}",
            )
            capture = header_capture(page)
            require(
                capture == reference_image,
                f"Header raster diverso in {route}: {hashlib.sha256(capture).hexdigest()} != {reference_digest}",
            )
            assert_search(page, route)

        browser.close()


def verify_method_background(base: str) -> None:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        open_page(page, base, REFERENCE)
        reference = page.evaluate(
            "() => ({color:getComputedStyle(document.body).backgroundColor,image:getComputedStyle(document.body).backgroundImage})"
        )
        open_page(page, base, "percorsi/metodo.html")
        actual = page.evaluate(
            "() => ({color:getComputedStyle(document.body).backgroundColor,image:getComputedStyle(document.body).backgroundImage})"
        )
        require(actual == reference, f"Sfondo Metodo diverso dal sito: {actual} != {reference}")
        browser.close()


def verify_climate_tooltips(base: str) -> None:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 1000})
        open_page(page, base, "confronta/meteo-clima/?comune=Massarosa&indicatore=temperature")
        hit = page.locator(".climate-minmax-hit").first
        hit.wait_for(state="attached")
        hit.focus()
        tooltip = page.locator("#climate-tooltip")
        tooltip.wait_for(state="visible")
        content = tooltip.inner_text()
        require("Tmin" in content and "Tmax" in content and "°C" in content, "Tooltip Tmin/Tmax incompleto")
        hit.blur()
        tooltip.wait_for(state="hidden")
        hit.hover()
        tooltip.wait_for(state="visible")
        browser.close()


def verify_custom_404(base: str) -> None:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        response = page.goto(urljoin(base, "comuni/viaregfgio/"), wait_until="domcontentloaded")
        require(response is not None and response.status == 404, "La route inesistente non restituisce HTTP 404")
        page.wait_for_selector(".site-header .global-search-trigger")
        require("Questo indirizzo non esiste" in page.locator("h1").inner_text(), "404 OV non renderizzata")
        require(page.locator(".site-brand .ov-mark-svg").count() == 1, "Logo OV assente dalla 404")
        browser.close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    base = args.base.rstrip("/") + "/"
    verify_viewport(base, 1440, 900)
    verify_viewport(base, 390, 844)
    verify_method_background(base)
    verify_climate_tooltips(base)
    verify_custom_404(base)
    verify_opportunity_release(base)
    print("Chrome browser gate passed: raster, geometry, styles, search, background, Tmin/Tmax tooltip and 404.")

    run_gate(base, ROOT / "dist", ROOT / "reports" / "browser-quality")
    run_budget(base, ROOT / "reports" / "lighthouse")


if __name__ == "__main__":
    main()
