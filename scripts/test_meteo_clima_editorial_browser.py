#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
from playwright.sync_api import sync_playwright


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--base', default='http://127.0.0.1:8123/')
    args = ap.parse_args()
    base = args.base.rstrip('/') + '/'
    launch = {'headless': True}
    chromium_path = os.environ.get('CHROMIUM_PATH')
    if chromium_path:
        launch['executable_path'] = chromium_path
    with sync_playwright() as p:
        browser = p.chromium.launch(**launch)
        for width, height in ((1440, 1000), (390, 844)):
            page = browser.new_page(viewport={'width': width, 'height': height})
            errors: list[str] = []
            page.on('pageerror', lambda exc: errors.append(str(exc)))
            page.goto(base + 'confronta/meteo-clima/', wait_until='networkidle')
            assert page.locator('meta[name="robots"]').get_attribute('content') == 'noindex,nofollow'
            assert page.locator('[data-climate-metric]').count() == 4
            assert page.locator('#climate-town option').count() == 7
            towns = page.locator('#climate-town option').all_text_contents()
            assert towns == sorted(towns, key=lambda value: value.casefold()), towns
            assert page.locator('#climate-town-list a').count() == 7
            assert 'media aritmetica semplice dei sette Comuni' in page.locator('main').inner_text()
            assert page.locator('.site-header .ov-mark-svg').count() == 1
            assert page.locator('.site-footer').count() == 1
            for metric in ('temperature', 'tmin', 'tmax', 'precipitation'):
                page.locator(f'[data-climate-metric="{metric}"]').click()
                page.wait_for_timeout(80)
                assert page.locator('#climate-current-value').inner_text().strip() != '—'
                assert page.locator('#climate-chart svg').count() == 1
                assert page.locator('#climate-town-list a').count() == 7
            assert not errors, errors
            overflow = page.evaluate('document.documentElement.scrollWidth > document.documentElement.clientWidth + 1')
            assert not overflow, f'Horizontal overflow at {width}px'
            page.close()
        browser.close()
    print('Meteo e clima browser OK: desktop/mobile, shell canonica, 4 indicatori, 7 Comuni alfabetici, no overflow')


if __name__ == '__main__':
    main()
