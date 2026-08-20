#!/usr/bin/env python3
from __future__ import annotations

import argparse

from playwright.sync_api import sync_playwright


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="http://127.0.0.1:8123/")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    base = args.base.rstrip("/") + "/"

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 1000})

        page.goto(base + "confronta/comunita/?indicatore=pnrrConcluded", wait_until="networkidle")
        general = page.locator('[data-pnrr-general-context="true"]')
        general.wait_for(timeout=15000)
        general_text = general.inner_text()
        assert "101" in general_text
        assert "74" in general_text
        assert "22" in general_text
        assert "36.683.108" in general_text or "36.683.107" in general_text
        assert general.locator('a[href="../../pnrr/"]').count() == 1

        body_text = page.locator("body").inner_text()
        assert "Versilia · 74 su 101" in body_text
        assert "73,3%" in body_text
        assert "Quota Versilia\n50,0%" not in body_text

        page.goto(base + "pnrr/", wait_until="networkidle")
        assert page.locator('[data-data-status-nav="header"]').count() == 1
        assert page.locator('[data-data-status-nav="footer"]').count() == 1
        assert page.locator(".site-header").count() == 1
        assert page.locator(".site-footer").count() == 1
        assert not page.evaluate(
            "document.documentElement.scrollWidth > document.documentElement.clientWidth"
        )

        page.goto(
            base + "comuni/massarosa/?tema=comunita&indicatore=pnrrConcluded",
            wait_until="networkidle",
        )
        town = page.locator('[data-pnrr-town-detail="true"]')
        town.wait_for(timeout=15000)
        text = town.inner_text()
        assert "PNRR a Massarosa" in text
        assert "11" in text
        assert "10" in text
        assert "90,9%" in text
        assert "2 opere individuate" in text
        assert "Asilo nido Girotondo a Piano di Mommio" in text
        assert "Piscina comunale G. Frati" in text
        assert text.count("Collaudo avviato") >= 2
        assert "C78E22000040006" in text
        assert "C75E22000250006" in text
        assert "Cassa, opere e PNRR" not in text
        assert "Pagamenti" not in text
        assert "Incassi" not in text
        assert "67" not in text
        assert "BDAP-MOP" in text
        assert town.locator('a[href="../../pnrr/"]').count() == 1

        mobile = browser.new_page(viewport={"width": 390, "height": 844})
        mobile.goto(
            base + "comuni/massarosa/?tema=comunita&indicatore=pnrrConcluded",
            wait_until="networkidle",
        )
        mobile_town = mobile.locator('[data-pnrr-town-detail="true"]')
        mobile_town.wait_for(timeout=15000)
        fits = mobile_town.evaluate("el => el.scrollWidth <= el.clientWidth + 1")
        assert fits, "Il dettaglio PNRR comunale genera overflow orizzontale su mobile"
        assert mobile_town.locator(".pnrr-town-work").count() == 2

        mobile.goto(base + "pnrr/", wait_until="networkidle")
        assert mobile.locator('[data-data-status-nav="footer"]').count() == 1
        assert not mobile.evaluate(
            "document.documentElement.scrollWidth > document.documentElement.clientWidth"
        )

        browser.close()

    print("PNRR browser QA: quadro Versilia corretto e dettaglio Massarosa con 2 opere senza ambiguità BDAP")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
