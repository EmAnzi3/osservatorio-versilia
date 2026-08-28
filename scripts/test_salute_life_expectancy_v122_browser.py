#!/usr/bin/env python3
"""Browser regression for lifeExpectancy sex selector and canonical lollipops."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from urllib.parse import urljoin

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]


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
                choice,
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
                aria = row.get_attribute('aria-label') or ''
                assert labels[choice] not in aria or town in aria

            assert seen == set(expected_rows[choice]), (choice, seen)

            references = page.locator('.comparison-bars .comparison-reference')
            assert references.count() == 7, references.count()
            expected_ref = float(expected_versilia[choice])
            for index in range(references.count()):
                ref_left = parse_left(references.nth(index).get_attribute('style') or '')
                assert abs(ref_left - expected_ref) < 0.03, (choice, expected_ref, ref_left)

            axis = page.locator('.comparison-bars > .comparison-axis').inner_text()
            assert '0,0 anni' in axis and '100 anni' in axis, (choice, axis)

        # Regression explicitly covering the discrepancy reported during review.
        page.locator('select[data-composite-component]').select_option('femmine')
        page.wait_for_function("() => document.querySelector('.comparison-bars')?.dataset.compositeChoice === 'femmine'")
        stazzema = page.locator('.comparison-bars > .bar-row', has=page.locator('.bar-town', has_text='Stazzema'))
        assert stazzema.count() == 1
        assert abs(parse_left(stazzema.locator('.comparison-dot').get_attribute('style') or '') - 84.24) < 0.03

        page.locator('select[data-composite-component]').select_option('maschi')
        page.wait_for_function("() => document.querySelector('.comparison-bars')?.dataset.compositeChoice === 'maschi'")
        stazzema = page.locator('.comparison-bars > .bar-row', has=page.locator('.bar-town', has_text='Stazzema'))
        assert abs(parse_left(stazzema.locator('.comparison-dot').get_attribute('style') or '') - 74.22) < 0.03

        browser.close()

    print('lifeExpectancy browser: lollipop, valore e Versilia ARS coerenti per Totale/Maschi/Femmine: OK')


if __name__ == '__main__':
    main()
