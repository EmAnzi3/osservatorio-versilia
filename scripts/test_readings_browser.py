#!/usr/bin/env python3
"""Regression browser desktop/mobile per le Letture."""
from __future__ import annotations

import argparse
from playwright.sync_api import sync_playwright


def no_overflow(page, label: str) -> None:
    overflow = page.evaluate("document.documentElement.scrollWidth - window.innerWidth")
    assert overflow <= 1, f"Overflow orizzontale {label}: {overflow}px"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="http://127.0.0.1:8123/")
    args = parser.parse_args()
    base = args.base.rstrip("/")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        for width, height in ((1440, 1000), (390, 844)):
            page = browser.new_page(viewport={"width": width, "height": height})
            errors: list[str] = []
            page.on("pageerror", lambda exc: errors.append(str(exc)))

            page.goto(f"{base}/letture/", wait_until="networkidle")
            assert page.locator(".reading-index-card").count() == 7
            assert page.locator(".site-brand").count() == 1
            assert page.locator('meta[name="robots"]').get_attribute("content") == "noindex,nofollow"
            no_overflow(page, f"indice {width}px")

            page.goto(f"{base}/letture/una-versilia-che-cambia/", wait_until="networkidle")
            assert page.locator(".reading-primary-table tbody tr").count() == 7
            assert page.locator(".reading-evidence-card").count() == 6
            assert page.locator(".site-brand").count() == 1
            assert page.locator(".site-footer").count() == 1
            assert "Periodo pubblicato" in page.locator("main").inner_text()
            no_overflow(page, f"demografia {width}px")

            page.goto(f"{base}/letture/cinquantanni-di-clima/", wait_until="networkidle")
            rows = page.locator(".reading-primary-table tbody tr")
            assert rows.count() == 7
            towns = [rows.nth(i).locator("th").inner_text().strip() for i in range(rows.count())]
            assert towns == sorted(towns, key=str.casefold), towns
            assert page.locator(".bar-rank, .ux-bar-rank").count() == 0
            assert "ricostruzioni territoriali" in page.locator("main").inner_text()
            no_overflow(page, f"clima {width}px")

            assert not errors, f"Browser errors {width}px: {errors}"
            page.close()
        browser.close()
    print("Letture browser OK: desktop/mobile, no overflow, clima senza classifiche.")


if __name__ == "__main__":
    main()
