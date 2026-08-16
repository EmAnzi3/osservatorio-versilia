#!/usr/bin/env python3
"""Browser QA for the income-vs-inflation historical comparison."""
from __future__ import annotations

import argparse
from urllib.parse import urljoin

from playwright.sync_api import sync_playwright


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def validate_history(page, url: str, scope: str) -> None:
    page.goto(url, wait_until='networkidle')
    page.wait_for_selector(f'{scope} .ux-view-shell')
    history = page.locator(f'{scope} [data-view-mode="history"]')
    require(history.count() == 1 and not history.is_disabled(), f'{url}: storico non disponibile')
    history.click()
    page.wait_for_selector(f'{scope} .ux-inflation-reference')

    require(page.locator(f'{scope} .ux-series-group').count() == 7,
            f'{url}: devono restare sette serie comunali selezionabili')
    require(page.locator(f'{scope} .ux-inflation-reference').count() == 1,
            f'{url}: riferimento inflazione assente o duplicato')
    require(page.locator(f'{scope} .ux-history-reference').count() == 1,
            f'{url}: legenda inflazione assente o duplicata')
    require('NIC Italia' in page.locator(f'{scope} .ux-history-reference').inner_text(),
            f'{url}: etichetta NIC Italia assente')

    copy = page.locator(f'{scope} .ux-history-head').inner_text()
    require('2016' in copy and '2024' in copy, f'{url}: intervallo 2016–2024 non riconosciuto')
    require('Redditi nominali e inflazione' in copy,
            f'{url}: spiegazione del confronto nominale/inflazione assente')

    note = page.locator(f'{scope} .ux-view-note').inner_text()
    require('2016 = 0%' in note and 'variazione reale' in note,
            f'{url}: nota metodologica storico non sufficientemente esplicita')

    inflation_line = page.locator(f'{scope} .ux-inflation-reference .ux-series-line')
    require(inflation_line.count() == 1, f'{url}: linea inflazione assente')
    dash = inflation_line.evaluate("el => getComputedStyle(el).strokeDasharray")
    require(dash not in ('none', '', '0px'), f'{url}: linea inflazione non distinguibile visivamente')

    page.locator(f'{scope} [data-history-select="massarosa"]').click()
    require(page.locator(f'{scope} .ux-series-group[data-history-town="massarosa"].is-selected').count() == 1,
            f'{url}: selezione comunale non funziona con il riferimento inflazione')
    require(page.locator(f'{scope} .ux-inflation-reference').count() == 1,
            f'{url}: riferimento inflazione scompare dopo selezione comunale')


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--base', default='http://127.0.0.1:8123/')
    args = parser.parse_args()
    base = args.base if args.base.endswith('/') else args.base + '/'

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(viewport={'width': 1440, 'height': 950})

        validate_history(
            page,
            urljoin(base, 'confronta/economia/?indicatore=incomeVsInflation'),
            '.topic-bars',
        )
        validate_history(
            page,
            urljoin(base, 'comuni/massarosa/?tema=economia&indicatore=incomeVsInflation'),
            '.history-panel',
        )

        browser.close()

    print('Income/inflation browser QA passed: NIC Italia visible in compare and town histories')


if __name__ == '__main__':
    main()
