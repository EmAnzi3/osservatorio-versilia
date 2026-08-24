#!/usr/bin/env python3
"""Gate browser finale del Radar Opportunità pubblicabile."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_NAV = ["Temi", "Comuni", "Opportunità", "Il progetto", "Stato dati", "Segnala"]
FORBIDDEN = [
    "Anteprima tecnica", "Collaudo", "non pubblicata", "revisione interna", "prototipo",
    "Audit indipendente", "capture rate", "buchi baseline", "fonti di controllo",
    "Famiglie presidiate", "Rete di raccolta", "Quality gate", "coverageHold",
    "Le schede sono ordinate per scadenza", "Colore e segno grafico",
]


def labels(page):
    return [" ".join(x.split()) for x in page.locator('header nav[aria-label="Navigazione principale"] a').all_inner_texts()]


def verify_release(base: str) -> None:
    payload = json.loads((ROOT / "data/opportunity-release.json").read_text(encoding="utf-8"))
    total_expected = len(payload.get("opportunities") or [])
    new_expected = sum(bool(item.get("is_new")) for item in payload.get("opportunities") or [])
    y, m, d = payload["referenceDate"].split("-")
    date_expected = f"{d}/{m}/{y}"
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        for width, height in ((1440, 1000), (1024, 768), (390, 844)):
            context = browser.new_context(viewport={"width": width, "height": height}, has_touch=width <= 700)
            page = context.new_page()
            page.goto(base.rstrip('/') + '/', wait_until='networkidle')
            assert labels(page) == EXPECTED_NAV, labels(page)
            home = page.locator('section.opportunity-home-callout')
            assert home.count() == 1 and home.locator('a[href$="opportunita/"]').count() == 1
            assert page.evaluate("""() => {const a=document.querySelector('section.towns-section#comuni'),b=document.querySelector('section.opportunity-home-callout'),c=document.querySelector('section.method-section#metodo');return Boolean(a&&b&&c&&(a.compareDocumentPosition(b)&Node.DOCUMENT_POSITION_FOLLOWING)&&(b.compareDocumentPosition(c)&Node.DOCUMENT_POSITION_FOLLOWING));}""")
            assert not page.evaluate('document.documentElement.scrollWidth > document.documentElement.clientWidth + 2')
            if width == 390:
                opp = page.locator('header nav[aria-label="Navigazione principale"] a', has_text='Opportunità')
                box = opp.bounding_box()
                assert box and box['x'] >= 0 and box['x'] + box['width'] <= width + 1, box

            page.goto(base.rstrip('/') + '/opportunita/', wait_until='networkidle')
            root = page.locator('[data-opportunity-preview]')
            root.wait_for()
            assert labels(page) == EXPECTED_NAV
            assert page.locator('link[rel="canonical"]').get_attribute('href') == 'https://osservatorioversilia.it/opportunita/'
            robots = page.locator('meta[name="robots"]')
            assert robots.count() == 0 or 'noindex' not in (robots.first.get_attribute('content') or '').lower()
            total = int(root.get_attribute('data-total-opportunities') or 0)
            cards = page.locator('[data-opportunity-card]')
            assert total == total_expected == cards.count(), (total, total_expected, cards.count())
            body = page.locator('body').inner_text()
            assert date_expected in body and 'Radar v0.4.4' in body
            assert 'Eventi sportivi di rilevanza nazionale e internazionale 2026' in body
            assert 'LIFE 2026 · Piani locali di riscaldamento e raffrescamento' in body
            for token in FORBIDDEN:
                assert token.lower() not in body.lower(), token

            badges = page.locator('.op-new-badge')
            new_cards = page.locator('[data-opportunity-card][data-new="true"]')
            assert badges.count() == new_expected, (badges.count(), new_expected)
            assert new_cards.count() == new_expected, (new_cards.count(), new_expected)
            if new_expected:
                assert all(text.strip().lower() == 'nuova' for text in badges.all_inner_texts())
                pairs = page.locator('.op-card-badges').evaluate_all(
                    "els=>els.map(e=>{const a=e.querySelector('.op-new-badge').getBoundingClientRect(),b=e.querySelector('.op-lifecycle').getBoundingClientRect();return Math.abs((a.top+a.height/2)-(b.top+b.height/2));})"
                )
                assert pairs and max(pairs) <= 1.5, pairs

            novelty = page.locator('[data-op-new]')
            sorter = page.locator('[data-op-sort]')
            assert novelty.count() == 1 and sorter.count() == 1
            novelty.select_option('new')
            page.wait_for_timeout(120)
            visible_new = page.locator('[data-opportunity-card]:not([hidden])')
            assert visible_new.count() == new_expected, (visible_new.count(), new_expected)
            assert all(x == 'true' for x in visible_new.evaluate_all('els=>els.map(e=>e.dataset.new)'))

            sorter.select_option('recent')
            page.wait_for_timeout(120)
            seen = visible_new.evaluate_all('els=>els.map(e=>e.dataset.firstSeen)')
            assert seen == sorted(seen, reverse=True), seen
            page.locator('[data-op-reset]').click()
            assert novelty.input_value() == '' and sorter.input_value() == 'deadline'
            assert page.locator('[data-opportunity-card]:not([hidden])').count() == total_expected

            source = page.locator('[data-op-source]')
            assert source.count() == 1 and source.locator('option').count() >= 40
            current = source.locator('option[data-current-count]').evaluate_all(
                "els=>els.map(o=>({value:o.value,count:Number(o.dataset.currentCount||0)})).filter(x=>x.value&&x.count>0)"
            )
            assert current
            source.select_option(current[0]['value'])
            page.wait_for_timeout(120)
            assert page.locator('[data-opportunity-card]:not([hidden])').count() >= 1
            page.locator('[data-op-reset]').click()
            lifecycle = page.locator('[data-op-lifecycle]')
            lifecycle.select_option('rolling_open')
            page.wait_for_timeout(120)
            visible = page.locator('[data-opportunity-card]:not([hidden])')
            assert visible.count() >= 1 and all(
                x == 'rolling_open' for x in visible.evaluate_all('els=>els.map(e=>e.dataset.lifecycle)')
            )
            page.locator('[data-op-reset]').click()
            images = page.locator('img[src*="source-favicons/"]')
            assert images.count() >= 1
            assert not images.evaluate_all('els=>els.filter(i=>!i.complete||i.naturalWidth<1).map(i=>i.src)')
            mic = page.locator('img[src*="source-favicons/mic-dgcc.png"]')
            assert mic.count() >= 1 and mic.first.evaluate('i=>i.complete&&i.naturalWidth>0')
            assert not page.evaluate('document.documentElement.scrollWidth > document.documentElement.clientWidth + 2')
            context.close()
        browser.close()
    sitemap = (ROOT / 'dist/sitemap.xml').read_text(encoding='utf-8')
    assert sitemap.count('https://osservatorioversilia.it/opportunita/') == 1
    print(
        f'Radar pubblico browser OK: {total_expected} opportunità · {new_expected} nuove · '
        f'{date_expected} · filtro/ordina · header/home/footer · 1440/1024/390.'
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--base', default='http://127.0.0.1:8123/')
    args = parser.parse_args()
    verify_release(args.base)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
