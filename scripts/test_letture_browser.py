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
            assert page.locator('.reading-card').count() == 7
            assert page.locator('meta[name="robots"]').get_attribute('content') == 'noindex,nofollow'
            assert page.locator('.site-header .ov-mark-svg').count() == 1
            assert page.locator('.site-footer').count() == 1
            page.goto(base + 'letture/redditi-contro-inflazione/', wait_until='networkidle')
            assert page.locator('.reading-question').is_visible()
            assert page.locator('.reading-metric').count() == 3
            assert page.locator('.reading-answer span').text_content().strip() == 'Risposta breve'
            assert 'Cosa non possiamo concludere' in page.locator('main').inner_text()
            page.goto(base + 'letture/cinquantanni-di-clima/', wait_until='networkidle')
            assert page.locator('.reading-metric').count() == 4
            assert page.locator('.reading-special a[href*="confronta/meteo-clima/"]').count() == 1
            assert not errors, errors
            overflow = page.evaluate('document.documentElement.scrollWidth > document.documentElement.clientWidth + 1')
            assert not overflow, f'Horizontal overflow at {width}px'
            page.close()
        browser.close()
    print('Letture browser OK: desktop/mobile, shell canonica, 7 cards, metriche canoniche, no overflow')


if __name__ == '__main__':
    main()
