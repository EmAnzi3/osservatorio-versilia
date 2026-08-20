#!/usr/bin/env python3
"""Smoke test browser dei quattro candidati Redditi Lotto A v2."""
from __future__ import annotations

import argparse
from urllib.parse import urljoin

from playwright.sync_api import sync_playwright


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--base', default='http://127.0.0.1:8123/')
    args = parser.parse_args()

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={'width': 1440, 'height': 1100})

        # 1. Un solo indicatore con selettore delle fonti di reddito.
        page.goto(urljoin(args.base, 'confronta/economia/?indicatore=incomeSourceProfile'), wait_until='networkidle')
        require(page.get_by_text('Reddito medio dichiarato per fonte', exact=True).count() >= 1,
                'Indicatore reddito per fonte non visibile')
        select = page.locator('select[data-composite-component]')
        require(select.count() == 1, 'Selettore fonti reddito assente')
        require(len(select.locator('option').all()) == 7, 'Il selettore non espone le 7 fonti MEF')
        select.select_option(label='Pensione')
        require('Pensione' in select.locator('option:checked').inner_text(), 'Selezione Pensione non applicata')

        # 2. Distribuzione: dettaglio 8 fasce espandibile nel confronto.
        page.goto(urljoin(args.base, 'confronta/economia/?indicatore=incomeDistribution'), wait_until='networkidle')
        detail = page.locator('details.income-bands-detail').first
        require(detail.count() == 1, 'Disclosure dettaglio 8 fasce assente nel confronto')
        detail.locator('summary').click()
        require(page.get_by_text('Oltre 120.000 €', exact=True).count() >= 1, 'Fascia oltre 120.000 € non visibile')
        require(page.get_by_text('0–10.000 €', exact=True).count() >= 1, 'Fascia 0–10.000 € non visibile')

        # La stessa vista deve esistere nella scheda comunale.
        page.goto(urljoin(args.base, 'comuni/massarosa/?tema=economia&indicatore=incomeDistribution'), wait_until='networkidle')
        town_detail = page.locator('details.income-bands-detail').first
        require(town_detail.count() == 1, 'Disclosure 8 fasce assente nella scheda comunale')
        town_detail.locator('summary').click()
        require(page.get_by_text('55.000–75.000 €', exact=True).count() >= 1, 'Dettaglio fasce comunale incompleto')

        # 3. Peso pensioni resta una card autonoma.
        page.goto(urljoin(args.base, 'confronta/economia/?indicatore=pensionIncomeShare'), wait_until='networkidle')
        require(page.get_by_text('Peso dei redditi da pensione', exact=True).count() >= 1,
                'Peso redditi da pensione non visibile')

        # 4. Contribuenti / maggiorenni con unità ogni 100.
        page.goto(urljoin(args.base, 'confronta/economia/?indicatore=taxpayersAdultPopulationRate'), wait_until='networkidle')
        require(page.get_by_text('Contribuenti ogni 100 maggiorenni', exact=True).count() >= 1,
                'Indicatore contribuenti/maggiorenni non visibile')
        body = page.locator('body').inner_text()
        require('ogni 100' in body, 'Unità ogni 100 non resa nel frontend')
        require('residenti di 18 anni e più' in body, 'Definizione del denominatore 18+ non visibile')

        browser.close()
    print('Browser Redditi Lotto A v2 OK: fonti, 8 fasce, pensioni e contribuenti/maggiorenni consultabili.')


if __name__ == '__main__':
    main()
