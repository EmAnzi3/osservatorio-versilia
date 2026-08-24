#!/usr/bin/env python3
"""Smoke browser della release Welfare sulle schede comunali."""
from __future__ import annotations

import argparse
from playwright.sync_api import sync_playwright


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="http://127.0.0.1:8123/")
    args = parser.parse_args()
    base = args.base.rstrip("/") + "/"

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 1100})

        page.goto(base + "comuni/pietrasanta/?tema=comunita&indicatore=socialSpendingByUserArea", wait_until="networkidle")
        detail = page.locator(".composite-town-detail").first
        detail.wait_for(state="visible")
        text = detail.inner_text()
        assert "NaN" not in text, text
        assert "NaN residenti" not in page.locator("body").inner_text()
        assert "Famiglia e minori" in text and "44,\u00a0?" not in text

        page.goto(base + "comuni/camaiore/?tema=comunita&indicatore=socialSpendingPerResident", wait_until="networkidle")
        body = page.locator("body").inner_text()
        assert "135,76" in body, body[:4000]
        assert "135,761" not in body

        browser.close()

    print("OK browser Welfare: nessun NaN residenti e spesa sociale esposta a due decimali.")


if __name__ == "__main__":
    main()
