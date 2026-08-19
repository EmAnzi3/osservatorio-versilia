#!/usr/bin/env python3
"""Browser regression della pagina Meteo e clima canonica."""
from __future__ import annotations

import argparse
from playwright.sync_api import sync_playwright


def no_overflow(page, label: str) -> None:
    overflow = page.evaluate("document.documentElement.scrollWidth - window.innerWidth")
    assert overflow <= 1, f"Overflow orizzontale {label}: {overflow}px"


def towns(page) -> list[str]:
    rows = page.locator(".climate-compare-row")
    return [rows.nth(i).locator("button").inner_text().strip() for i in range(rows.count())]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="http://127.0.0.1:8123/")
    args = parser.parse_args()
    url = args.base.rstrip("/") + "/confronta/meteo-clima/"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        for width, height in ((1440, 1000), (390, 844)):
            page = browser.new_page(viewport={"width": width, "height": height})
            errors: list[str] = []
            page.on("pageerror", lambda exc: errors.append(str(exc)))
            page.goto(url, wait_until="networkidle")

            assert page.locator('meta[name="robots"]').get_attribute("content") == "noindex,nofollow"
            assert page.locator(".climate-metric-tabs [data-metric]").count() == 4
            assert page.locator(".climate-summary-card").count() == 3
            assert page.locator(".climate-compare-row").count() == 7
            current_towns = towns(page)
            assert current_towns == sorted(current_towns, key=str.casefold), current_towns
            assert page.locator(".bar-rank, .ux-bar-rank").count() == 0
            assert page.locator("#climate-status-list article").count() == 4
            assert page.locator("#climate-status").is_visible()
            assert "anno in corso" not in page.locator("main").inner_text().lower()

            for metric in ("tmin", "tmax", "precipitation", "temperature"):
                page.locator(f'[data-metric="{metric}"]').click()
                page.wait_for_timeout(120)
                assert page.locator(".climate-summary-card").count() == 3
                assert page.locator(".climate-compare-row").count() == 7
                assert towns(page) == current_towns
                assert f"indicatore={metric}" in page.url

            page.locator('[data-metric="tmin"]').click()
            assert "minima" in page.locator("#climate-chart-title").inner_text().lower()
            page.locator('[data-metric="tmax"]').click()
            assert "massima" in page.locator("#climate-chart-title").inner_text().lower()
            no_overflow(page, f"Meteo e clima {width}px")
            assert not errors, f"Browser errors {width}px: {errors}"
            page.close()
        browser.close()
    print("Meteo e clima browser OK: 4 indicatori, stato, alfabetico, no ranking, desktop/mobile.")


if __name__ == "__main__":
    main()
