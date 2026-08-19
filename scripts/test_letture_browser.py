#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
from playwright.sync_api import sync_playwright


def no_overflow(page, width: int) -> None:
    overflow = page.evaluate('document.documentElement.scrollWidth > document.documentElement.clientWidth + 1')
    assert not overflow, f'Horizontal overflow at {width}px on {page.url}'


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
            assert page.locator('.town-report-grid a').count() == 7
            assert page.locator('meta[name="robots"]').get_attribute('content') == 'noindex,nofollow'
            assert page.locator('.site-header .ov-mark-svg').count() == 1
            nav_text = page.locator('.site-header-actions nav').text_content() or ''
            assert 'Confronta' in nav_text and 'Capire' in nav_text
            no_overflow(page, width)

            page.goto(base + 'letture/una-versilia-che-cambia/', wait_until='networkidle')
            assert page.locator('.story-hero--editorial h1').text_content().strip() == 'La Versilia cambia poco nel totale, ma molto nella sua struttura'
            assert page.locator('[data-story-chapter]').count() == 3
            assert page.locator('.story-facts article').count() == 3
            assert page.locator('.story-source-link').count() == 4
            assert page.locator('.trend-chart').count() >= 3
            assert page.locator('.story-axis-title').count() >= 4
            assert page.locator('.chart-tooltip').count() > 0
            assert page.locator('.story-scatter-chart').count() == 1
            assert page.locator('.story-scatter-point').count() == 7
            assert page.locator('.story-analysis-grid article').count() == 4
            assert page.locator('.story-limit-panel').count() == 1
            assert page.locator('a[href*="rapporti/lettura-una-versilia-che-cambia/"]').count() >= 1
            assert page.locator('[data-aging-town]').count() == 1
            assert page.locator('.story-canonical-bars .bar-row').count() == 14

            first_point = page.locator('.story-canonical-chart .chart-point').first
            first_point.hover()
            assert first_point.locator('.chart-tooltip').get_attribute('hidden') is None
            page.locator('[data-aging-town]').select_option(label='Massarosa')
            assert 'Massarosa' in (page.locator('[data-aging-chart-host] svg').get_attribute('aria-label') or '')
            assert not errors, errors
            no_overflow(page, width)

            page.goto(base + 'rapporti/lettura-una-versilia-che-cambia/', wait_until='networkidle')
            assert page.locator('.report-document.report-reading').count() == 1
            assert page.locator('[data-report-print]').count() == 1
            assert page.locator('.report-table').first.locator('tbody tr').count() == 7
            assert page.locator('.report-columns h3').count() == 4
            assert page.locator('meta[name="robots"]').get_attribute('content') == 'noindex,nofollow'
            no_overflow(page, width)

            page.goto(base + 'rapporti/comune-massarosa/', wait_until='networkidle')
            assert page.locator('.report-document.report-town').count() == 1
            assert page.locator('.report-town-facts article').count() == 5
            assert page.locator('.report-theme').count() >= 8
            assert page.locator('.report-theme .report-table').count() >= 8
            assert page.locator('[data-report-print]').count() == 1
            assert 'Massarosa' in (page.locator('.report-cover h1').text_content() or '')
            assert not errors, errors
            no_overflow(page, width)

            page.goto(base + 'letture/redditi-contro-inflazione/', wait_until='networkidle')
            assert page.locator('.planned-reading').count() == 1
            assert page.locator('[data-story-chapter]').count() == 0
            assert not errors, errors
            no_overflow(page, width)
            page.close()
        browser.close()

    print('Capire la Versilia browser OK: assi+tooltip canonici, scatter, analisi estesa, rapporto Lettura e rapporto comunale, desktop/mobile')


if __name__ == '__main__':
    main()
