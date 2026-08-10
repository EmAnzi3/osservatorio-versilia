#!/usr/bin/env python3
"""Regression browser test for Ambiente/climate selector interactions."""
from __future__ import annotations

import argparse
from playwright.sync_api import sync_playwright


def select_metric(page, key: str, scope: str) -> None:
    button = page.locator(f'button[data-metric="{key}"]').first
    assert button.count() == 1, f'Missing {scope} metric button: {key}'
    # Some accordion groups are intentionally collapsed. Calling HTMLElement.click()
    # exercises the same DOM click handlers without making visibility part of this
    # regression: the failure we guard against is a render/event-loop freeze.
    button.evaluate('(el) => el.click()')
    page.wait_for_timeout(80)
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
        page.set_default_timeout(5000)
        errors: list[str] = []
        page.on('pageerror', lambda exc: errors.append(str(exc)))

        page.goto(f'{base}/confronta/ambiente/', wait_until='networkidle')
        for key in sequence:
            select_metric(page, key, 'Ambiente')
            assert page.locator('#compare-definition h2').count() == 1

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

    print('Climate interaction regression OK: repeated Ambiente and town selections remain responsive')


if __name__ == '__main__':
    main()
