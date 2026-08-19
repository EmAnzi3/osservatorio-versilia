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

            page.goto(base + 'letture/', wait_until='networkidle')
            assert page.locator('h1').text_content().strip() == 'Capire la Versilia'
            assert page.locator('.reading-pilot').count() == 1
            assert page.locator('.reading-plan-card').count() == 6
            assert page.locator('.reading-plan-icon svg').count() == 6
            assert page.locator('meta[name="robots"]').get_attribute('content') == 'noindex,nofollow'
            assert page.locator('.site-header .ov-mark-svg').count() == 1
            nav_text = page.locator('.site-header-actions nav').text_content() or ''
            assert 'Confronta' in nav_text and 'Capire' in nav_text

            page.goto(base + 'letture/una-versilia-che-cambia/', wait_until='networkidle')
            assert page.locator('[data-story-chapter]').count() == 3
            assert page.locator('.story-facts article').count() == 3
            assert page.locator('.story-source-link').count() == 4
            assert page.locator('.story-change-row').count() == 7
            assert page.locator('.story-age-row').count() == 7
            assert page.locator('.story-mobility-row').count() == 7
            text = page.locator('main').inner_text()
            assert 'La storia in una frase' in text
            assert '%' in text
            assert 'ogni 1.000' in text
            assert 'persone 65+ ogni 100 residenti 0–14' in text
            assert page.locator('.story-hero svg').count() >= 2

            page.goto(base + 'letture/redditi-contro-inflazione/', wait_until='networkidle')
            assert page.locator('.planned-reading').count() == 1
            assert page.locator('[data-story-chapter]').count() == 0

            assert not errors, errors
            overflow = page.evaluate('document.documentElement.scrollWidth > document.documentElement.clientWidth + 1')
            assert not overflow, f'Horizontal overflow at {width}px'
            page.close()
        browser.close()
    print('Capire la Versilia browser OK: pilot story, icons, units, navigation, desktop/mobile, no overflow')


if __name__ == '__main__':
    main()
