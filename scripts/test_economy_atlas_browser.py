#!/usr/bin/env python3
from __future__ import annotations

import argparse
from urllib.parse import urljoin
from playwright.sync_api import sync_playwright


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--base', default='http://127.0.0.1:8123/')
    args = parser.parse_args()
    url = urljoin(args.base, 'confronta/economia/atlante-attivita-economiche/')

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 1200})
        page.goto(url, wait_until='networkidle')
        page.wait_for_selector('#selectors select[data-level="0"]')

        assert page.locator('header.site-header').count() == 1
        assert page.locator('footer.site-footer').count() == 1
        assert page.locator('h1').inner_text().strip() == 'Atlante delle attività economiche'
        assert page.locator('.quick button').count() == 5
        assert page.locator('#modeComposition').inner_text().strip() == 'Composizione %'
        assert page.locator('#modeComposition').evaluate('(el) => getComputedStyle(el).whiteSpace') == 'nowrap'

        section = page.locator('#selectors select[data-level="0"]')
        section.select_option('I')
        page.locator('#selectors select[data-level="2"]').select_option('55')
        group = page.locator('#selectors select[data-level="3"]')
        assert group.locator('option[value="552"]').count() == 1
        label_552 = group.locator('option[value="552"]').inner_text()
        assert 'ALLOGGI PER VACANZE' in label_552.upper(), label_552

        page.locator('#clear').click()
        section.select_option('N')
        page.locator('#selectors select[data-level="2"]').select_option('78')
        page.wait_for_timeout(100)
        analysis = page.locator('#analysis').inner_text()
        assert '6 UL attive in Versilia' in analysis, analysis
        assert '3' in analysis and '2' in analysis, analysis

        page.locator('#modeNavigation').click()
        assert page.locator('#analysisHeading').inner_text().strip() == 'Il codice nei sette Comuni'
        page.locator('#modeComposition').click()
        assert page.locator('#analysisHeading').inner_text().strip() == 'Il nodo nei sette Comuni'

        page.locator('#tabHistory').click()
        assert page.locator('.history-chart').count() == 1
        assert page.locator('.breaktext').filter(has_text='ATECO 2022').count() == 1

        overflow = page.evaluate('document.documentElement.scrollWidth - document.documentElement.clientWidth')
        assert overflow <= 1, f'Overflow orizzontale desktop: {overflow}px'

        mobile = browser.new_page(viewport={"width": 390, "height": 844})
        mobile.goto(url, wait_until='networkidle')
        mobile.wait_for_selector('#selectors select[data-level="0"]')
        mobile_overflow = mobile.evaluate('document.documentElement.scrollWidth - document.documentElement.clientWidth')
        assert mobile_overflow <= 1, f'Overflow orizzontale mobile: {mobile_overflow}px'
        assert mobile.locator('#modeComposition').evaluate('(el) => getComputedStyle(el).whiteSpace') == 'nowrap'
        browser.close()

    print('Atlante attività economiche: browser contract verificato.')


if __name__ == '__main__':
    main()
