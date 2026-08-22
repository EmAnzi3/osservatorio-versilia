#!/usr/bin/env python3
from __future__ import annotations

import argparse
from playwright.sync_api import sync_playwright


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="http://127.0.0.1:8123/")
    args = parser.parse_args()

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page()
        for width, height in ((1440, 1000), (390, 844)):
            page.set_viewport_size({"width": width, "height": height})
            page.goto(args.base + "opportunita-preview/", wait_until="domcontentloaded")
            root = page.locator("[data-opportunity-preview]")
            root.wait_for()
            total = int(root.get_attribute("data-total-opportunities") or 0)
            assert total >= 10
            assert page.locator(".op-overview-grid .op-stat").count() == 6
            assert page.locator(".op-audit-summary").count() == 1
            assert page.locator(".op-monitor-source").count() == 0
            assert page.locator("[data-op-source-quick]").count() == 0
            assert page.locator("[data-op-source]").count() == 1
            assert page.locator("[data-op-lifecycle]").count() == 1
            assert page.locator('[data-opportunity-card][data-lifecycle="application_open"]').count() >= 1
            assert page.locator('[data-opportunity-card][data-lifecycle="rolling_open"]').count() >= 1
            assert page.locator('[data-opportunity-card][data-lifecycle="announced_upcoming"]').count() >= 1
            assert not page.evaluate("document.documentElement.scrollWidth>document.documentElement.clientWidth")

            result_list = page.locator(".op-preview-list")
            assert result_list.count() == 1
            scroll = result_list.evaluate("el=>({overflow:getComputedStyle(el).overflowY, client:el.clientHeight, scroll:el.scrollHeight})")
            assert scroll["overflow"] == "auto"
            assert scroll["scroll"] > scroll["client"]

            lifecycle = page.locator("[data-op-lifecycle]")
            lifecycle.select_option("rolling_open")
            page.wait_for_timeout(80)
            visible = page.locator("[data-opportunity-card]:not([hidden])")
            assert visible.count() >= 1
            assert all(value == "rolling_open" for value in visible.evaluate_all("els=>els.map(e=>e.dataset.lifecycle)"))

            page.locator("[data-op-reset]").click()
            lifecycle.select_option("announced_upcoming")
            page.wait_for_timeout(80)
            body = page.locator("body").inner_text()
            assert "Fondo investimenti stradali piccoli Comuni" in body
            assert page.locator("[data-opportunity-card]:not([hidden])").count() >= 1

            for query in ("capitale italiana del mare", "crescere nei piccoli comuni", "tratta", "vita & opportunità", "town twinning", "assistenti sociali"):
                page.locator("[data-op-reset]").click()
                page.locator("[data-op-search]").fill(query)
                page.wait_for_timeout(80)
                assert page.locator("[data-opportunity-card]:not([hidden])").count() >= 1, query

            text = page.locator("body").inner_text()
            assert "Quality gate" not in text
            assert "Da verificare" not in text
            assert "coverageHold" not in text
        browser.close()
    print("Opportunity preview v0.4.2 browser checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
