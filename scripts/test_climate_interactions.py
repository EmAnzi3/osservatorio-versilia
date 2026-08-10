#!/usr/bin/env python3
"""Regression browser test for Ambiente/climate selector interactions and semantics."""
from __future__ import annotations

import argparse
from playwright.sync_api import sync_playwright


def select_metric(page, key: str, scope: str) -> None:
    button = page.locator(f'button[data-metric="{key}"]').first
    assert button.count() == 1, f'Missing {scope} metric button: {key}'
    # Some accordion groups are intentionally collapsed. HTMLElement.click()
    # exercises the same click handlers without making visibility part of the test.
    button.evaluate('(el) => el.click()')
    page.wait_for_timeout(120)
    assert page.evaluate('1 + 1') == 2, f'Browser event loop stopped after selecting {key}'
    assert f'indicatore={key}' in page.url, (key, page.url)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--base-url', default='http://127.0.0.1:8123')
    args = parser.parse_args()
    base = args.base_url.rstrip('/')

    sequence = [
        'recycling',
        'climateTemperatureTrend50y',
        'climatePrecipitationTrend50y',
        'landUse',
        'floodExposure',
        'landslideExposure',
        'climateTminTrend',
        'climateTmaxTrend',
        'recycling',
    ]

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={'width': 1500, 'height': 1000})
        page.set_default_timeout(7000)
        errors: list[str] = []
        page.on('pageerror', lambda exc: errors.append(str(exc)))

        # Repeated selector changes must remain responsive.
        page.goto(f'{base}/confronta/ambiente/', wait_until='networkidle')
        for key in sequence:
            select_metric(page, key, 'Ambiente')
            assert page.locator('#compare-definition h2').count() == 1

        # Climate indicators must use the same current/history grammar as the site,
        # while keeping the current value semantically distinct from the trend.
        select_metric(page, 'climateTemperatureTrend50y', 'Ambiente')
        shell = page.locator('[data-ov-climate-shell="compare-climateTemperatureTrend50y"]')
        shell.wait_for(state='visible')
        assert page.locator('#compare-definition h2').inner_text() == 'Temperatura media annua'
        assert '2025' in page.locator('#compare-definition').inner_text()
        assert shell.locator('[data-ov-climate-view="current"]').count() == 1
        assert shell.locator('[data-ov-climate-view="history"]').count() == 1
        assert shell.locator('.ov-climate-current-row').count() == 7
        assert shell.locator('.bar-rank, .ux-bar-rank').count() == 0, 'Climate current view must not contain rankings'
        assert 'Nessuna graduatoria' in shell.inner_text()

        shell.locator('[data-ov-climate-view="history"]').click()
        assert shell.locator('.ov-climate-compare-lines').is_visible()
        assert shell.locator('.ov-climate-compare-lines .trend').count() == 7
        shell.locator('[data-climate-select="camaiore"]').click()
        assert 'trend 1975–2025' in shell.locator('.ov-climate-selection-summary').inner_text()

        # Town climate page: no "order of value" box, clear current value, sparse
        # years and an explicit trend line in the historical view.
        page.goto(
            f'{base}/comuni/camaiore/?tema=ambiente&indicatore=climateTmaxTrend',
            wait_until='networkidle',
        )
        town_shell = page.locator('[data-ov-climate-shell="town-climateTmaxTrend-camaiore"]')
        town_shell.wait_for(state='visible')
        primary = page.locator('.town-metric-primary')
        assert '19,04 °C' in primary.inner_text(), primary.inner_text()
        assert '2015' in primary.inner_text()
        assert not page.locator('.versilia-position').is_visible(), 'Climate town page must not show ranking/position box'
        assert town_shell.locator('.bar-rank, .ux-bar-rank').count() == 0
        assert 'Non è la temperatura più alta raggiunta nell’anno' in town_shell.inner_text()

        town_shell.locator('[data-ov-climate-view="history"]').click()
        assert town_shell.locator('.ov-climate-trend').is_visible()
        assert town_shell.locator('.ov-climate-annual').is_visible()
        assert 'Trend medio per decennio' in town_shell.inner_text()
        # X axis must be deliberately sparse, never one label for every year.
        year_labels = town_shell.locator('.ov-climate-axis').filter(has_text='19').count() + town_shell.locator('.ov-climate-axis').filter(has_text='20').count()
        assert year_labels < 15, f'Too many year labels: {year_labels}'

        # Risk detail remains conditional outside climate.
        page.goto(
            f'{base}/comuni/viareggio/?tema=ambiente&indicatore=landUse',
            wait_until='networkidle',
        )
        for key in sequence:
            select_metric(page, key, 'town')
            assert page.locator('.town-metric-primary').count() == 1
            deep = page.locator('.topic-deep-dive')
            if key in {'floodExposure', 'landslideExposure'}:
                assert deep.count() == 1 and deep.is_visible(), f'Risk detail not visible for {key}'
            elif deep.count():
                assert not deep.is_visible(), f'Risk detail incorrectly visible for {key}'

        assert not errors, f'Browser page errors: {errors}'
        browser.close()

    print('Climate interaction regression OK: coherent current/history semantics, explicit trends, no rankings')


if __name__ == '__main__':
    main()
