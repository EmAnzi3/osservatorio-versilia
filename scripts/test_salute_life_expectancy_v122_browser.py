#!/usr/bin/env python3
"""Browser regression for lifeExpectancy sex selector and canonical lollipops."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from urllib.parse import urljoin

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
HISTORY_YEARS = len(json.loads((ROOT / 'data' / 'source-snapshots' / 'ars-life-expectancy-1290-2008-2022.json').read_text(encoding='utf-8'))['scope']['years'])


def parse_left(style: str) -> float:
    token = next((item for item in style.split(';') if item.strip().startswith('left:')), '')
    if not token:
        raise AssertionError(f"left missing from style: {style!r}")
    return float(token.split(':', 1)[1].strip().rstrip('%'))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--base', default='http://127.0.0.1:8123/')
    args = parser.parse_args()

    site = json.loads((ROOT / 'data' / 'site-data.json').read_text(encoding='utf-8'))
    metric = site['metrics']['lifeExpectancy']
    expected_rows = {
        choice: {
            row['town']: next(part['value'] for part in row['parts'] if part['key'] == choice)
            for row in metric['rows']
        }
        for choice in ('totale', 'maschi', 'femmine')
    }
    expected_versilia = {
        choice: next(part['value'] for part in metric['aggregate']['parts'] if part['key'] == choice)
        for choice in ('totale', 'maschi', 'femmine')
    }
    labels = {'totale': 'Totale', 'maschi': 'Maschi', 'femmine': 'Femmine'}

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={'width': 1440, 'height': 1000})
        page.goto(urljoin(args.base, 'confronta/salute/?indicatore=lifeExpectancy'), wait_until='networkidle')
        page.wait_for_selector('select[data-composite-component]')

        for choice in ('totale', 'maschi', 'femmine'):
            page.locator('select[data-composite-component]').select_option(choice)
            page.wait_for_function(
                "choice => document.querySelector('.comparison-bars')?.dataset.compositeChoice === choice",
                arg=choice,
            )
            page.wait_for_selector('.comparison-bars .comparison-dot')

            legend = page.locator('.comparison-legend').inner_text()
            expected_legend = f"Versilia (ARS) · {labels[choice]}"
            assert expected_legend in legend, (choice, legend)
            assert 'Media semplice' not in legend, (choice, legend)

            rows = page.locator('.comparison-bars > .bar-row')
            assert rows.count() == 7, rows.count()
            seen = set()
            for index in range(rows.count()):
                row = rows.nth(index)
                town = row.locator('.bar-town').inner_text().strip()
                seen.add(town)
                expected = float(expected_rows[choice][town])
                dot_left = parse_left(row.locator('.comparison-dot').get_attribute('style') or '')
                # For this indicator the canonical zero-origin scale resolves to 0–100 years,
                # therefore the lollipop percentage must equal the ARS year value.
                assert abs(dot_left - expected) < 0.03, (choice, town, expected, dot_left)

            assert seen == set(expected_rows[choice]), (choice, seen)

            references = page.locator('.comparison-bars .comparison-reference')
            assert references.count() == 7, references.count()
            expected_ref = float(expected_versilia[choice])
            for index in range(references.count()):
                ref_left = parse_left(references.nth(index).get_attribute('style') or '')
                assert abs(ref_left - expected_ref) < 0.03, (choice, expected_ref, ref_left)

            axis = page.locator('.comparison-bars > .comparison-axis').inner_text()
            assert '0,0 anni' in axis and '100 anni' in axis, (choice, axis)

            history = page.locator('[data-view-pane="history"]')
            history.wait_for(state='attached')
            page.wait_for_function(
                "label => document.querySelector('[data-view-pane=\"history\"] .ux-history-chart svg')?.getAttribute('aria-label')?.includes(label)",
                arg=labels[choice],
            )
            page.wait_for_selector('[data-view-pane="history"] .ux-history-chart[data-ov-tooltip-wired="1"]', state='attached')
            chart = history.locator('.ux-history-chart')
            assert chart.get_attribute('data-ov-tooltip-wired') == '1'
            assert 'sette Comuni e della Versilia' in (chart.locator('svg').get_attribute('aria-label') or '')
            assert history.locator('.ux-history-legend').get_attribute('aria-label') == 'Territori'
            assert history.locator('.ux-history-legend [data-history-select]').count() == 8
            groups = chart.locator('[data-history-town]')
            assert groups.count() == 8
            assert chart.locator('.chart-point').count() == 8 * HISTORY_YEARS
            assert chart.locator('.chart-point .chart-tooltip').count() == 8 * HISTORY_YEARS
            versilia_history = chart.locator('[data-history-town="versilia"]')
            assert versilia_history.count() == 1
            assert versilia_history.locator('.chart-point').count() == HISTORY_YEARS
            versilia_button = history.locator('[data-history-select="versilia"]')
            assert float(versilia_button.get_attribute('data-end') or 'nan') == float(expected_versilia[choice])

        # Regression explicitly covering the discrepancy reported during review: each dot must sit
        # where the selected sex value puts it on the shared axis, for every town (Stazzema included).
        for choice in ('femmine', 'maschi'):
            page.locator('select[data-composite-component]').select_option(choice)
            page.wait_for_function("choice => document.querySelector('.comparison-bars')?.dataset.compositeChoice === choice", arg=choice)
            points = []
            for town, value in expected_rows[choice].items():
                row = page.locator('.comparison-bars > .bar-row', has=page.locator('.bar-town', has_text=town))
                assert row.count() == 1, (choice, town)
                points.append((float(value), parse_left(row.locator('.comparison-dot').get_attribute('style') or '')))
            (low_v, low_x), (high_v, high_x) = min(points), max(points)
            assert high_v > low_v and high_x > low_x, (choice, points)
            for value, left in points:
                expected = low_x + (value - low_v) * (high_x - low_x) / (high_v - low_v)
                assert abs(left - expected) < 0.03, (choice, value, left, expected)

        browser.close()

    print('lifeExpectancy browser: lollipop, valore e Versilia ARS coerenti per Totale/Maschi/Femmine: OK')


if __name__ == '__main__':
    main()
