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

        # 80+ resta nella distribuzione principale; 85+ è dettaglio della stessa riga, non box separato.
        page.goto(urljoin(args.base, 'confronta/demografia/?indicatore=ageDistribution'), wait_until='networkidle')
        require(page.get_by_text('Distribuzione per fasce d’età', exact=True).count() >= 1,
                'ageDistribution non visibile')
        require(page.locator('details.age-senior-detail').count() == 0, 'Box separato Grandi anziani ancora presente')
        require(page.get_by_text('80 anni e oltre', exact=True).count() >= 1, '80+ non resta nella distribuzione principale')
        require(page.locator('.age85-inline-detail').count() >= 1, 'Dettaglio 85+ assente nel confronto')
        require(page.get_by_text('85 anni e oltre', exact=True).count() >= 1, 'Quota 85+ non leggibile nel confronto')

        # Scheda comunale: 85+ come dettaglio della distribuzione e piramide con asse/scala.
        page.goto(urljoin(args.base, 'comuni/massarosa/?tema=demografia&indicatore=ageDistribution'), wait_until='networkidle')
        require(page.locator('details.age-senior-detail').count() == 0, 'Box separato 80+/85+ presente nella scheda comunale')
        age85 = page.locator('.age85-inline-detail').first
        require(age85.count() == 1, 'Dettaglio 85+ assente a Massarosa')
        require('85 anni e oltre' in age85.inner_text(), '85+ non leggibile nella distribuzione comunale')
        require(page.locator('select[data-composite-choice] option[value="age85Plus"]').count() == 0,
                '85+ non deve introdurre un controllo separato nel selettore')
        pyramid = page.locator('details.age-pyramid-detail').first
        require(pyramid.count() == 1, 'Piramide per età e sesso assente')
        pyramid.locator('summary').click()
        require(pyramid.locator('svg[role="img"]').count() == 1, 'SVG piramide assente')
        for text in ('Uomini', 'Donne', 'Scala: residenti per classe d’età', 'residenti', '100+'):
            require(pyramid.get_by_text(text, exact=True).count() >= 1, f'Elemento piramide assente: {text}')

        # Componenti della variazione demografica leggibili nel confronto e nel comune.
        page.goto(urljoin(args.base, 'confronta/demografia/?indicatore=populationChange'), wait_until='networkidle')
        compare_components = page.locator('.compare-change-components')
        require(compare_components.count() == 1, 'Approfondimento componenti variazione assente nel confronto')
        compare_body = compare_components.inner_text()
        for label in ('Saldo naturale', 'Saldo migratorio interno', 'Saldo migratorio con l’estero', '2024'):
            require(label in compare_body, f'Componente/anno assente nel confronto: {label}')

        page.goto(urljoin(args.base, 'comuni/massarosa/?tema=demografia&indicatore=populationChange'), wait_until='networkidle')
        components = page.locator('.demographic-change-components').first
        require(components.count() == 1, 'Approfondimento componenti variazione assente')
        body = components.inner_text()
        for label in ('Saldo naturale', 'Saldo migratorio interno', 'Saldo migratorio con l’estero'):
            require(label in body, f'Componente demografica assente: {label}')
        require('2024' in body, 'Anno comune 2024 non visibile nelle componenti')

        # Cittadinanza / paese di nascita: aggregato Versilia nel confronto + dettaglio comunale.
        page.goto(urljoin(args.base, 'confronta/demografia/?indicatore=foreignResidents'), wait_until='networkidle')
        compare_origins = page.locator('details.compare-foreign-origins').first
        require(compare_origins.count() == 1, 'Dettaglio RCS aggregato Versilia assente')
        compare_origins.locator('summary').click()
        compare_text = compare_origins.inner_text()
        for label in ('Versilia', 'Cittadinanze straniere più numerose', 'Paesi esteri di nascita più frequenti'):
            require(label in compare_text, f'Dettaglio RCS aggregato incompleto: {label}')

        page.goto(urljoin(args.base, 'comuni/massarosa/?tema=demografia&indicatore=foreignResidents'), wait_until='networkidle')
        origins = page.locator('details.foreign-origins-detail').first
        require(origins.count() == 1, 'Dettaglio cittadinanza/paese di nascita assente')
        origins.locator('summary').click()
        origins_text = origins.inner_text()
        require('Cittadinanze straniere più numerose' in origins_text, 'Sezione cittadinanze assente')
        require('Paesi esteri di nascita più frequenti' in origins_text, 'Sezione paesi di nascita assente')
        require(origins.locator('.composite-town-detail > div').count() >= 4,
                'Dettaglio RCS troppo povero o non renderizzato')

        # Mobile: i nuovi dettagli non devono introdurre overflow.
        page.set_viewport_size({'width': 390, 'height': 844})
        page.goto(urljoin(args.base, 'comuni/massarosa/?tema=demografia&indicatore=ageDistribution'), wait_until='networkidle')
        page.locator('details.age-pyramid-detail summary').click()
        assert_no_horizontal_overflow(page, 'ageDistribution mobile')
        page.goto(urljoin(args.base, 'confronta/demografia/?indicatore=foreignResidents'), wait_until='networkidle')
        page.locator('details.compare-foreign-origins summary').click()
        assert_no_horizontal_overflow(page, 'foreignResidents compare mobile')
        page.goto(urljoin(args.base, 'comuni/massarosa/?tema=demografia&indicatore=foreignResidents'), wait_until='networkidle')
        page.locator('details.foreign-origins-detail summary').click()
        assert_no_horizontal_overflow(page, 'foreignResidents town mobile')

        browser.close()
    print('Browser Demografia v2 OK: 85+, piramide, componenti variazione e RCS Versilia/comuni sono consultabili anche su mobile.')


if __name__ == '__main__':
    main()
