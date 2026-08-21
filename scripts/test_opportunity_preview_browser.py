#!/usr/bin/env python3
from __future__ import annotations

import argparse
from playwright.sync_api import sync_playwright


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="http://127.0.0.1:8123/")
    return parser.parse_args()


def assert_shell(page) -> None:
    page.locator(".site-header").wait_for()
    assert page.locator(".site-brand .ov-mark-svg").count() == 1
    assert page.locator(".site-brand-copy strong").inner_text().strip() == "Osservatorio Versilia"
    assert page.locator(".global-search-trigger").count() == 1
    assert page.locator(".site-footer").count() == 1
    assert page.locator('.footer-social[data-social-placement="footer"]').count() == 0
    assert page.locator('meta[name="robots"]').get_attribute("content") == "noindex,nofollow,noarchive"


def visible_count(page) -> int:
    return page.locator("[data-opportunity-card]:not([hidden])").count()


def reset(page) -> None:
    page.locator("[data-op-reset]").click()
    page.wait_for_function("() => document.querySelectorAll('[data-opportunity-card]:not([hidden])').length === 11")


def check_view(page, base: str, width: int, height: int) -> None:
    page.set_viewport_size({"width": width, "height": height})
    page.goto(base + "opportunita-preview/", wait_until="networkidle")
    assert_shell(page)

    assert page.locator("h1").inner_text() == "Opportunità per i Comuni della Versilia."
    assert page.locator("[data-opportunity-card]").count() == 11
    assert visible_count(page) == 11
    assert "11 opportunità" in page.locator("[data-op-visible]").inner_text().lower()
    body = page.locator("body").inner_text()
    assert "Quality gate" not in body
    assert "Perché compare" not in body
    assert "Da verificare" not in body
    assert "ore 16:00" in body

    overflow = page.evaluate("document.documentElement.scrollWidth > document.documentElement.clientWidth")
    assert not overflow, f"Overflow orizzontale preview a {width}px"

    accents = page.locator("[data-opportunity-card]").evaluate_all(
        "(cards) => [...new Set(cards.map(card => getComputedStyle(card).getPropertyValue('--card-accent').trim()))]"
    )
    assert len(accents) >= 5, f"Palette troppo uniforme: {accents}"

    page.locator("[data-op-source]").select_option("fondazione-cr-lucca")
    page.wait_for_function("() => document.querySelectorAll('[data-opportunity-card]:not([hidden])').length === 2")
    assert visible_count(page) == 2

    reset(page)
    page.locator("[data-op-access]").select_option("specific_requirement")
    page.wait_for_function("() => document.querySelectorAll('[data-opportunity-card]:not([hidden])').length === 6")
    assert visible_count(page) == 6

    reset(page)
    page.locator("[data-op-town]").select_option("forte-dei-marmi")
    page.wait_for_function("() => document.querySelectorAll('[data-opportunity-card]:not([hidden])').length === 9")
    assert visible_count(page) == 9

    page.locator("[data-op-access]").select_option("specific_requirement")
    page.wait_for_function("() => document.querySelectorAll('[data-opportunity-card]:not([hidden])').length === 4")
    assert visible_count(page) == 4

    reset(page)
    page.locator("[data-op-search]").fill("parcheggi")
    page.wait_for_function("() => document.querySelectorAll('[data-opportunity-card]:not([hidden])').length === 1")
    assert "parcheggi" in page.locator("[data-opportunity-card]:not([hidden]) h3").inner_text().lower()

    if width >= 700:
        trigger = page.locator(".global-search-trigger")
        trigger.click()
        page.locator(".search-overlay").wait_for()
        assert page.locator(".search-overlay").is_visible()
        page.keyboard.press("Escape")
        page.locator(".search-overlay").wait_for(state="hidden")


def main() -> None:
    args = parse_args()
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        check_view(page, args.base, 1440, 1000)
        check_view(page, args.base, 390, 844)
        browser.close()
    print("Opportunity preview v0.2.4 browser checks passed: shell, source/access filters, palette, mobile and no overflow.")


if __name__ == "__main__":
    main()
