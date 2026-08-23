#!/usr/bin/env python3
"""Collaudo browser della route definitiva /opportunita/, ancora non pubblica."""
from __future__ import annotations

import argparse
from playwright.sync_api import sync_playwright

EXPECTED_NAV = ["Temi", "Comuni", "Il progetto", "Stato dati", "Segnala"]


def run(base: str) -> None:
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        for width, height in ((1440, 1000), (1024, 768), (390, 844)):
            context = browser.new_context(viewport={"width": width, "height": height})
            page = context.new_page()
            page.goto(base.rstrip("/") + "/opportunita/", wait_until="domcontentloaded")

            root = page.locator("[data-opportunity-preview]")
            root.wait_for()
            total = int(root.get_attribute("data-total-opportunities") or 0)
            cards = page.locator("[data-opportunity-card]")
            assert total == cards.count() and total > 0, (total, cards.count())

            nav = page.locator('header nav[aria-label="Navigazione principale"] a').all_inner_texts()
            assert [" ".join(x.split()) for x in nav] == EXPECTED_NAV, nav
            assert page.locator(".global-search-trigger").count() == 1
            assert page.locator(".site-footer").count() == 1
            assert page.locator('meta[name="robots"]').get_attribute("content") == "noindex,nofollow,noarchive"
            assert page.locator("body").inner_text().find("Collaudo integrazione") >= 0

            source = page.locator("[data-op-source]")
            assert source.count() == 1
            options = source.locator("option")
            assert options.count() >= 40
            assert "Tutte le fonti monitorate" in options.nth(0).inner_text()
            assert "UE · URBACT · monitorata" in source.inner_text()

            current = source.locator('option[data-current-count]').evaluate_all(
                "els => els.map(o => ({value:o.value,count:Number(o.dataset.currentCount||0)})).filter(x => x.value && x.count>0)"
            )
            assert current, "Nessuna fonte con opportunità corrente"
            source.select_option(current[0]["value"])
            page.wait_for_timeout(100)
            assert page.locator("[data-opportunity-card]:not([hidden])").count() >= 1

            page.locator("[data-op-reset]").click()
            lifecycle = page.locator("[data-op-lifecycle]")
            lifecycle.select_option("rolling_open")
            page.wait_for_timeout(100)
            visible = page.locator("[data-opportunity-card]:not([hidden])")
            assert visible.count() >= 1
            assert all(v == "rolling_open" for v in visible.evaluate_all("els=>els.map(e=>e.dataset.lifecycle)"))
            page.locator("[data-op-reset]").click()

            images = page.locator('img[src*="source-favicons/"]')
            assert images.count() >= 1
            broken = images.evaluate_all("els => els.filter(i => !i.complete || i.naturalWidth < 1).map(i => i.src)")
            assert not broken, broken

            assert not page.evaluate("document.documentElement.scrollWidth > document.documentElement.clientWidth")
            body = page.locator("body").inner_text()
            assert "Quality gate" not in body and "Da verificare" not in body and "coverageHold" not in body
            context.close()
        browser.close()
    print("Radar /opportunita/: header/footer canonici, filtri, favicon e responsive OK desktop/laptop/mobile.")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="http://127.0.0.1:8123/")
    args = parser.parse_args()
    run(args.base)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
