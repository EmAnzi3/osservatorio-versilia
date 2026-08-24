#!/usr/bin/env python3
"""Collaudo browser della route definitiva /opportunita/, ancora non pubblica."""
from __future__ import annotations

import argparse
from playwright.sync_api import sync_playwright

EXPECTED_NAV = ["Temi", "Comuni", "Opportunità", "Il progetto", "Stato dati", "Segnala"]


def nav_labels(page):
    nav = page.locator('header nav[aria-label="Navigazione principale"] a').all_inner_texts()
    return [" ".join(x.split()) for x in nav]


def opportunity_link(page, scope: str):
    links = page.locator(f'{scope} a').filter(has_text="Opportunità")
    assert links.count() == 1, (scope, links.count())
    link = links.first
    assert link.evaluate("a => new URL(a.href).pathname") == "/opportunita/"
    return link


def wait_for_runtime_placement(page, *, home: bool) -> None:
    page.wait_for_function(
        r"""({expected, home}) => {
          const clean = value => String(value || '').replace(/\s+/g, ' ').trim();
          const nav = document.querySelector('header nav[aria-label="Navigazione principale"]');
          if (!nav) return false;
          const labels = [...nav.querySelectorAll('a')].map(a => clean(a.textContent));
          if (JSON.stringify(labels) !== JSON.stringify(expected)) return false;
          const header = [...nav.querySelectorAll('a')]
            .filter(a => clean(a.textContent) === 'Opportunità' && new URL(a.href).pathname === '/opportunita/');
          const footer = [...document.querySelectorAll('footer .footer-links a')]
            .filter(a => clean(a.textContent) === 'Opportunità' && new URL(a.href).pathname === '/opportunita/');
          if (header.length !== 1 || footer.length !== 1) return false;
          if (home && !document.querySelector('section.opportunity-home-callout')) return false;
          return document.documentElement.dataset.opportunityIntegrationReady === '1';
        }""",
        arg={"expected": EXPECTED_NAV, "home": home},
        timeout=15000,
    )
    page.wait_for_timeout(300)
    assert nav_labels(page) == EXPECTED_NAV
    opportunity_link(page, 'header nav[aria-label="Navigazione principale"]')
    opportunity_link(page, "footer .footer-links")
    if home:
        assert page.locator("section.opportunity-home-callout").count() == 1


def run(base: str) -> None:
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        for width, height in ((1440, 1000), (1024, 768), (390, 844)):
            context = browser.new_context(viewport={"width": width, "height": height})
            page = context.new_page()

            page.goto(base.rstrip("/") + "/", wait_until="domcontentloaded")
            wait_for_runtime_placement(page, home=True)
            home_callout = page.locator("section.opportunity-home-callout")
            assert "Radar Opportunità" in home_callout.inner_text()
            home_link = home_callout.locator("a").filter(has_text="Esplora le opportunità")
            assert home_link.count() == 1
            assert home_link.evaluate("a => new URL(a.href).pathname") == "/opportunita/"
            assert not page.evaluate(
                "document.documentElement.scrollWidth > document.documentElement.clientWidth"
            )

            page.goto(base.rstrip("/") + "/opportunita/", wait_until="domcontentloaded")
            root = page.locator("[data-opportunity-preview]")
            root.wait_for()
            wait_for_runtime_placement(page, home=False)
            total = int(root.get_attribute("data-total-opportunities") or 0)
            cards = page.locator("[data-opportunity-card]")
            assert total == cards.count() and total > 0, (total, cards.count())

            header_link = opportunity_link(page, 'header nav[aria-label="Navigazione principale"]')
            footer_link = opportunity_link(page, "footer .footer-links")
            assert header_link.get_attribute("aria-current") == "page"
            assert footer_link.get_attribute("aria-current") == "page"
            assert page.locator(".global-search-trigger").count() == 1
            assert page.locator(".site-footer").count() == 1
            assert page.locator('meta[name="robots"]').get_attribute("content") == "noindex,nofollow,noarchive"

            source = page.locator("[data-op-source]")
            assert source.count() == 1
            options = source.locator("option")
            assert options.count() >= 40
            assert "Tutte le fonti monitorate" in options.nth(0).inner_text()
            assert "UE · URBACT · monitorata" in source.inner_text()

            current = source.locator("option[data-current-count]").evaluate_all(
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
            broken = images.evaluate_all(
                "els => els.filter(i => !i.complete || i.naturalWidth < 1).map(i => i.src)"
            )
            assert not broken, broken
            mic_dgcc = page.locator('img[src*="source-favicons/mic-dgcc.png"]')
            assert mic_dgcc.count() >= 1, "Favicon pinned mic-dgcc non esposta"
            assert mic_dgcc.first.evaluate("i => i.complete && i.naturalWidth > 0")

            assert not page.evaluate(
                "document.documentElement.scrollWidth > document.documentElement.clientWidth"
            )
            body = page.locator("body").inner_text()
            assert "Quality gate" not in body and "Da verificare" not in body and "coverageHold" not in body
            context.close()
        browser.close()
    print(
        "Radar /opportunita/: runtime stabile dopo mount JS; header/home/footer, filtri, favicon e responsive OK desktop/laptop/mobile."
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="http://127.0.0.1:8123/")
    args = parser.parse_args()
    run(args.base)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
