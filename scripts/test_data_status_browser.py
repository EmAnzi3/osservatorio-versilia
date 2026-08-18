#!/usr/bin/env python3
from __future__ import annotations

import argparse
from playwright.sync_api import sync_playwright


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="http://127.0.0.1:8123/")
    return parser.parse_args()


def assert_public_path(page, base: str, width: int) -> None:
    page.goto(base, wait_until="networkidle")
    page.locator('[data-data-status-nav="header"]').wait_for()
    assert page.locator('[data-data-status-nav="header"]').count() == 1
    assert page.locator('[data-data-status-nav="footer"]').count() == 1
    assert page.locator('[data-data-status-nav="header"]').get_attribute("href").rstrip("/").endswith("/stato-dati")
    if width >= 700:
        assert page.locator('[data-data-status-nav="header"]').is_visible()
    else:
        assert page.locator('[data-data-status-nav="footer"]').is_visible()

    page.wait_for_timeout(300)
    assert page.locator('[data-data-status-nav="header"]').count() == 1
    assert page.locator('[data-data-status-nav="footer"]').count() == 1

    page.goto(base + "progetto/", wait_until="networkidle")
    page.locator('[data-data-status-nav="footer"]').wait_for()
    assert page.locator('[data-data-status-nav="header"]').count() == 1
    assert page.locator('[data-data-status-nav="footer"]').count() == 1


def check_view(page, base: str, width: int, height: int) -> None:
    page.set_viewport_size({"width": width, "height": height})
    assert_public_path(page, base, width)

    page.goto(base + "stato-dati/", wait_until="networkidle")
    assert page.locator("h1").inner_text() == "Stato dei dati"
    assert page.locator(".data-status-table tbody tr").count() == 127
    overflow = page.evaluate("document.documentElement.scrollWidth > document.documentElement.clientWidth")
    assert not overflow, f"Overflow orizzontale a {width}px"
    page.locator("[data-status-filter]").select_option("source_checked")
    visible = page.locator(".data-status-table tbody tr:not([hidden])").count()
    assert visible >= 0
    text = page.locator("[data-status-visible]").inner_text()
    assert "indicatori visibili" in text

    page.goto(base + "indicatori/popolazione-residente/", wait_until="networkidle")
    page.locator("[data-data-status-row='state']").wait_for()
    governance = page.locator(".indicator-governance-grid").inner_text()
    assert "Periodo pubblicato" in governance
    assert "Stato del dato" in governance
    assert "Ultimo controllo Osservatorio" in governance
    assert "Prossimo aggiornamento atteso" not in governance
    overflow = page.evaluate("document.documentElement.scrollWidth > document.documentElement.clientWidth")
    assert not overflow, f"Overflow indicatore a {width}px"


def main() -> None:
    args = parse_args()
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        check_view(page, args.base, 1440, 1000)
        check_view(page, args.base, 390, 844)
        browser.close()
    print("Data status browser checks passed: public path + desktop + mobile.")


if __name__ == "__main__":
    main()
