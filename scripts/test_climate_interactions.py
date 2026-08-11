#!/usr/bin/env python3
"""Regression browser test for Ambiente/climate semantics and shared visual grammar."""
from __future__ import annotations

import argparse
from playwright.sync_api import sync_playwright


def select_metric(page, key: str, scope: str) -> None:
    button = page.locator(f'button[data-metric="{key}"]').first
    assert button.count() == 1, f'Missing {scope} metric button: {key}'
    button.evaluate('(el) => el.click()')
    page.wait_for_timeout(150)
    assert page.evaluate('1 + 1') == 2, f'Browser event loop stopped after selecting {key}'
    assert f'indicatore={key}' in page.url, (key, page.url)


def assert_tooltip_works(point) -> None:
    point.hover()
    tooltip = point.locator('.chart-tooltip')
    assert tooltip.count() == 1, 'Missing chart tooltip'
    assert tooltip.get_attribute('hidden') is None, 'Tooltip did not open on hover'


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

        page.goto(f'{base}/confronta/ambiente/', wait_until='networkidle')
        for key in sequence:
            select_metric(page, key, 'Ambiente')
            assert page.locator('#compare-definition h2').count() == 1

        # Climate uses the same current/history grammar and the same chart surfaces
        # as the other indicators, while remaining ranking-free.
        select_metric(page, 'climateTemperatureTrend50y', 'Ambiente')
        shell = page.locator('[data-ov-climate-shell="compare-climateTemperatureTrend50y"]')
        shell.wait_for(state='visible')
        assert page.locator('#compare-definition h2').inner_text() == 'Temperatura media annua'
        assert '2025' in page.locator('#compare-definition').inner_text()
        assert shell.locator('[data-ov-climate-view="current"]').count() == 1
        assert shell.locator('[data-ov-climate-view="history"]').count() == 1
        assert shell.locator('[data-ov-climate-pane="current"] > .topic-bars').count() == 1, 'Current climate view must use the shared topic-bars surface'
        assert shell.locator('.ov-climate-current-row').count() == 7
        assert shell.locator('.bar-rank, .ux-bar-rank').count() == 0, 'Climate current view must not contain rankings'
        assert 'Nessuna graduatoria' in shell.inner_text()

        shell.locator('[data-ov-climate-view="history"]').click()
        assert shell.locator('[data-ov-climate-pane="history"] > .ux-history-card').is_visible(), 'Climate history must use the shared history card surface'
        chart = shell.locator('.ov-climate-compare-lines')
        assert chart.is_visible()
        assert chart.locator('.trend').count() == 7
        shell.locator('[data-climate-select="camaiore"]').click()
        assert 'trend 1975–2025' in shell.locator('.ux-history-summary').inner_text()
        compare_point = chart.locator('[data-climate-series="camaiore"] .chart-point').first
        assert_tooltip_works(compare_point)

        # Tmin/Tmax current values must now use real 2025 data and history must extend
        # to 2025, still without rankings.
        select_metric(page, 'climateTminTrend', 'Ambiente')
        tmin_shell = page.locator('[data-ov-climate-shell="compare-climateTminTrend"]')
        tmin_shell.wait_for(state='visible')
        assert '2025' in page.locator('#compare-definition').inner_text()
        assert '1995–2025' in tmin_shell.inner_text()
        assert tmin_shell.locator('.ov-climate-current-row').count() == 7
        assert tmin_shell.locator('.bar-rank, .ux-bar-rank').count() == 0
        tmin_shell.locator('[data-ov-climate-view="history"]').click()
        assert tmin_shell.locator('.chart-point[aria-label*="2025"]').count() >= 7, 'Tmin history must contain 2025 for all towns'
        assert 'Trend lineare 1995–2025' in tmin_shell.inner_text()

        # Town climate page: current annual value + Versilia benchmark card, but no
        # ranking. Historical chart has sparse years, trend and the standard tooltip.
        page.goto(
            f'{base}/comuni/camaiore/?tema=ambiente&indicatore=climateTmaxTrend',
            wait_until='networkidle',
        )
        town_shell = page.locator('[data-ov-climate-shell="town-climateTmaxTrend-camaiore"]')
        town_shell.wait_for(state='visible')
        primary = page.locator('.town-metric-primary')
        assert '19,49 °C' in primary.inner_text(), primary.inner_text()
        assert '2025' in primary.inner_text()

        versilia = page.locator('.versilia-position')
        assert versilia.is_visible(), 'Climate town page must retain the Versilia comparison card'
        versilia_text = versilia.inner_text()
        versilia_lower = versilia_text.lower()
        assert 'rispetto alla versilia' in versilia_lower, versilia_text
        assert 'media semplice dei 7 comuni' in versilia_lower, versilia_text
        assert 'ordine del valore' not in versilia_lower, versilia_text
        assert '2025' in versilia_text, versilia_text
        assert town_shell.locator('.bar-rank, .ux-bar-rank').count() == 0

        town_shell.locator('[data-ov-climate-view="history"]').click()
        assert town_shell.locator('.ov-climate-town-trend').is_visible()
        assert town_shell.locator('.chart-line').is_visible()
        assert 'Non è la temperatura più alta raggiunta nell’anno' in town_shell.inner_text()
        assert 'Trend lineare 1995–2025' in town_shell.inner_text()
        assert 'Trend medio per decennio' in town_shell.inner_text()
        assert town_shell.locator('.chart-point[aria-label*="2025"]').count() >= 1
        year_labels = town_shell.locator('.trend-chart svg > text.chart-label:not(.chart-y-label)').count()
        assert year_labels < 15, f'Too many year labels: {year_labels}'
        town_point = town_shell.locator('.trend-chart .chart-point').first
        assert_tooltip_works(town_point)

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

    print('Climate interaction regression OK: shared surfaces, Tmin/Tmax through 2025, working tooltips, Versilia benchmark, explicit trends, no rankings')


if __name__ == '__main__':
    main()
