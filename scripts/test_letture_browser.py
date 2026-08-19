#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
from playwright.sync_api import sync_playwright


def no_overflow(page, width: int) -> None:
    overflow = page.evaluate('document.documentElement.scrollWidth > document.documentElement.clientWidth + 1')
    assert not overflow, f'Horizontal overflow at {width}px on {page.url}'


def assert_tooltip(page) -> None:
    point = page.locator('.report-history .chart-point').first
    assert point.count() == 1
    point.focus()
    tooltip = point.locator('.chart-tooltip')
    assert tooltip.count() == 1
    assert tooltip.get_attribute('hidden') is None


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
            nav_text = page.locator('.site-header-actions nav').text_content() or ''
            assert 'Confronta' in nav_text and 'Capire' in nav_text
            no_overflow(page, width)

            page.goto(base + 'letture/una-versilia-che-cambia/', wait_until='networkidle')
            assert page.locator('.story-hero--editorial h1').text_content().strip() == 'La Versilia cambia poco nel totale, ma molto nella sua struttura'
            assert page.locator('[data-story-chapter]').count() == 3
            assert page.locator('.story-scatter-chart').count() == 1
            assert page.locator('.story-analysis-grid article').count() == 4
            assert page.locator('a[href*="rapporti/lettura-una-versilia-che-cambia/"]').count() >= 1
            assert not errors, errors
            no_overflow(page, width)

            page.goto(base + 'rapporti/lettura-una-versilia-che-cambia/', wait_until='networkidle')
            assert page.locator('body[data-report-version="4"]').count() == 1
            assert page.locator('.report-document.report-reading.report-mature').count() == 1
            assert page.locator('.report-toc li').count() == 8
            assert page.locator('.report-findings article').count() == 5
            assert page.locator('.report-figure').count() >= 6
            assert page.locator('.ux-history-card').count() >= 3
            assert page.locator('.ux-history-axis-label').count() > 0
            assert page.locator('.ux-history-legend button').count() >= 7
            assert page.locator('.composite-distribution-row').count() == 7
            assert page.locator('.composite-mobility-row').count() == 7
            assert page.locator('.report-current-comparison').count() >= 1
            assert page.locator('.report-method-grid article').count() == 4
            assert page.locator('.report-pdf-download').count() == 1
            assert '/rapporti/pdf/lettura-una-versilia-che-cambia.pdf' in (page.locator('.report-pdf-download').get_attribute('href') or '')
            assert_tooltip(page)
            assert page.locator('meta[name="robots"]').get_attribute('content') == 'noindex,nofollow'
            assert not errors, errors
            no_overflow(page, width)

            page.goto(base + 'rapporti/comune-massarosa/', wait_until='networkidle')
            assert page.locator('.report-document.report-town.report-mature').count() == 1
            assert page.locator('.report-town-identity img').count() == 1
            assert page.locator('.report-toc li').count() == 9
            assert page.locator('.report-findings article').count() == 6
            assert page.locator('.report-figure').count() >= 15
            assert page.locator('.ux-history-card').count() >= 8
            assert page.locator('.ux-history-axis-label').count() > 0
            assert page.locator('.report-current-comparison').count() >= 5
            assert page.locator('.town-benchmark').count() >= 4
            assert page.locator('.report-appendix-theme').count() >= 10
            assert page.locator('.report-method-grid article').count() == 4
            assert page.locator('.report-pdf-download').count() == 1
            assert '/rapporti/pdf/comune-massarosa.pdf' in (page.locator('.report-pdf-download').get_attribute('href') or '')
            assert 'Massarosa' in (page.locator('.report-cover h1').text_content() or '')
            assert_tooltip(page)
            assert not errors, errors
            no_overflow(page, width)

            page.goto(base + 'comuni/massarosa/', wait_until='networkidle')
            assert page.locator('[data-town-report-link]').count() == 1
            assert '/rapporti/comune-massarosa/' in (page.locator('[data-town-report-link]').get_attribute('href') or '')
            assert not errors, errors
            no_overflow(page, width)

            page.goto(base + 'letture/redditi-contro-inflazione/', wait_until='networkidle')
            assert page.locator('.planned-reading').count() == 1
            assert page.locator('[data-story-chapter]').count() == 0
            assert not errors, errors
            no_overflow(page, width)
            page.close()
        browser.close()

    print('Rapporti v4 browser OK: componenti OVUXHistory identici, analisi estesa, 8 indicatori demografici, rapporti comunali, desktop/mobile')


if __name__ == '__main__':
    main()
