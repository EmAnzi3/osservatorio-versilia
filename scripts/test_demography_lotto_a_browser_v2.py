#!/usr/bin/env python3
"""Smoke test browser degli approfondimenti Demografia Lotto A v2."""
from __future__ import annotations

import argparse
from urllib.parse import urljoin

from playwright.sync_api import sync_playwright


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def assert_no_horizontal_overflow(page, label: str) -> None:
    values = page.evaluate('''() => ({
      inner: window.innerWidth,
      doc: document.documentElement.scrollWidth,
      body: document.body.scrollWidth
    })''')
    require(max(values['doc'], values['body']) <= values['inner'] + 2,
            f'{label}: overflow orizzontale {values}')


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--base', default='http://127.0.0.1:8123/')
    args = parser.parse_args()

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={'width': 1440, 'height': 1100})

        # 80+/85+ nel confronto, senza nuova card.
        page.goto(urljoin(args.base, 'confronta/demografia/?indicatore=ageDistribution'), wait_until='networkidle')
        require(page.get_by_text('Distribuzione per fasce d’età', exact=True).count() >= 1,
                'ageDistribution non visibile')
        senior = page.locator('details.age-senior-detail').first
        require(senior.count() == 1, 'Dettaglio 80+/85+ assente nel confronto')
        senior.locator('summary').click()
        require(page.get_by_text('85 anni e oltre', exact=True).count() >= 1, 'Quota 85+ non leggibile nel confronto')
        require(page.get_by_text('80 anni e oltre', exact=True).count() >= 1, 'Quota 80+ non leggibile nel confronto')

        # Scheda comunale: dettaglio 80+/85+ e piramide.
        page.goto(urljoin(args.base, 'comuni/massarosa/?tema=demografia&indicatore=ageDistribution'), wait_until='networkidle')
        town_senior = page.locator('details.age-senior-detail').first
        require(town_senior.count() == 1, 'Dettaglio 80+/85+ assente nella scheda comunale')
        town_senior.locator('summary').click()
        require(page.get_by_text('85 anni e oltre', exact=True).count() >= 1, '85+ assente a Massarosa')
        pyramid = page.locator('details.age-pyramid-detail').first
        require(pyramid.count() == 1, 'Piramide per età e sesso assente')
        pyramid.locator('summary').click()
        require(pyramid.locator('svg[role="img"]').count() == 1, 'SVG piramide assente')
        require(pyramid.get_by_text('Uomini', exact=True).count() >= 1, 'Etichetta uomini assente')
        require(pyramid.get_by_text('Donne', exact=True).count() >= 1, 'Etichetta donne assente')
        require(pyramid.get_by_text('100+', exact=True).count() >= 1, 'Fascia 100+ assente dalla piramide')

        # Componenti della variazione demografica leggibili insieme.
        page.goto(urljoin(args.base, 'comuni/massarosa/?tema=demografia&indicatore=populationChange'), wait_until='networkidle')
        components = page.locator('.demographic-change-components')
        require(components.count() == 1, 'Approfondimento componenti variazione assente')
        body = components.inner_text()
        for label in ('Saldo naturale', 'Saldo migratorio interno', 'Saldo migratorio con l’estero'):
            require(label in body, f'Componente demografica assente: {label}')
        require('2024' in body, 'Anno comune 2024 non visibile nelle componenti')

        # Cittadinanza / paese di nascita dentro la card già esistente dei residenti stranieri.
        page.goto(urljoin(args.base, 'comuni/massarosa/?tema=demografia&indicatore=foreignResidents'), wait_until='networkidle')
        origins = page.locator('details.foreign-origins-detail').first
        require(origins.count() == 1, 'Dettaglio cittadinanza/paese di nascita assente')
        origins.locator('summary').click()
        origins_text = origins.inner_text()
        require('Cittadinanze straniere più numerose' in origins_text, 'Sezione cittadinanze assente')
        require('Paesi esteri di nascita più frequenti' in origins_text, 'Sezione paesi di nascita assente')
        require(origins.locator('.composite-town-detail > div').count() >= 4,
                'Dettaglio RCS troppo povero o non renderizzato')

        # Mobile: i nuovi disclosure e la piramide non devono introdurre overflow.
        page.set_viewport_size({'width': 390, 'height': 844})
        page.goto(urljoin(args.base, 'comuni/massarosa/?tema=demografia&indicatore=ageDistribution'), wait_until='networkidle')
        page.locator('details.age-pyramid-detail summary').click()
        assert_no_horizontal_overflow(page, 'ageDistribution mobile')
        page.goto(urljoin(args.base, 'comuni/massarosa/?tema=demografia&indicatore=foreignResidents'), wait_until='networkidle')
        page.locator('details.foreign-origins-detail summary').click()
        assert_no_horizontal_overflow(page, 'foreignResidents mobile')

        browser.close()
    print('Browser Demografia v2 OK: 80+/85+, piramide, componenti variazione e RCS sono consultabili anche su mobile.')


if __name__ == '__main__':
    main()
