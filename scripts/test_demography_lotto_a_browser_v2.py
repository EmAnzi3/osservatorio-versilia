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


def assert_foreign_detail_not_clipped(detail, label: str) -> None:
    values = detail.evaluate('''root => {
      const note = root.querySelector('.foreign-origins-note');
      const cells = [...root.querySelectorAll('.foreign-origin-section .composite-town-detail > div')];
      return {
        rootClient: root.clientWidth,
        rootScroll: root.scrollWidth,
        noteClient: note ? note.clientWidth : -1,
        noteScroll: note ? note.scrollWidth : -1,
        noteWhiteSpace: note ? getComputedStyle(note).whiteSpace : '',
        overflowingCells: cells.filter(cell => cell.scrollWidth > cell.clientWidth + 2).length,
      };
    }''')
    require(values['rootScroll'] <= values['rootClient'] + 2, f'{label}: contenitore RCS tagliato {values}')
    require(values['noteClient'] > 0 and values['noteScroll'] <= values['noteClient'] + 2,
            f'{label}: nota RCS tagliata {values}')
    require(values['noteWhiteSpace'] != 'nowrap', f'{label}: nota RCS forzata su una riga')
    require(values['overflowingCells'] == 0, f'{label}: celle RCS con testo tagliato {values}')


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--base', default='http://127.0.0.1:8123/')
    args = parser.parse_args()

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={'width': 1440, 'height': 1100})

        # 85+ deve essere una vera fascia della distribuzione, non un box autonomo.
        page.goto(urljoin(args.base, 'confronta/demografia/?indicatore=ageDistribution'), wait_until='networkidle')
        require(page.get_by_text('Distribuzione per fasce d’età', exact=True).count() >= 1,
                'ageDistribution non visibile')
        require(page.locator('.age85-inline-detail').count() == 0, 'Box 85+ autonomo ancora presente nel confronto')
        require(page.locator('details.age-senior-detail').count() == 0, 'Box grandi anziani ancora presente')
        legend = page.locator('.composite-legend').first.inner_text()
        require('80–84 anni' in legend, 'Fascia 80–84 assente dalla distribuzione')
        require('85 anni e oltre' in legend, 'Fascia 85+ assente dalla distribuzione')
        require(page.locator('.composite-distribution-row').count() == 7, 'Confronto distribuzione non 7/7')
        require(page.locator('.composite-segment').count() == 56, 'Distribuzione non composta da 8 fasce per 7 comuni')
        color_6 = page.locator('.composite-segment.part-6').first.evaluate('(el) => getComputedStyle(el).backgroundColor')
        color_7 = page.locator('.composite-segment.part-7').first.evaluate('(el) => getComputedStyle(el).backgroundColor')
        require(color_6 and color_7 and color_6 != color_7 and color_7 not in ('rgba(0, 0, 0, 0)', 'transparent'),
                f'Ottava fascia senza livello cromatico distinto: {color_6=} {color_7=}')

        # Scheda comunale: otto valori nella stessa griglia, nessun box aggiuntivo.
        page.goto(urljoin(args.base, 'comuni/forte-dei-marmi/?tema=demografia&indicatore=ageDistribution'), wait_until='networkidle')
        require(page.locator('.age85-inline-detail').count() == 0, 'Box 85+ autonomo presente nella scheda comunale')
        cells = page.locator('.composite-town-stack-shell > .composite-town-detail > div')
        require(cells.count() == 8, f'Griglia comunale non ha 8 valori: {cells.count()}')
        cell_text = '\n'.join(cells.all_inner_texts())
        require('80–84 anni' in cell_text and '85 anni e oltre' in cell_text,
                '80–84 / 85+ non sono nella stessa griglia degli altri valori')

        # Piramide: stesso sistema tooltip dei grafici storici (.chart-point/.chart-tooltip), niente <title> browser-native.
        pyramid = page.locator('details.age-pyramid-detail').first
        require(pyramid.count() == 1, 'Piramide per età e sesso assente')
        pyramid.locator('summary').click()
        require(pyramid.locator('.trend-chart.age-pyramid-trend').count() == 1, 'Piramide fuori dalla superficie chart canonica')
        require(pyramid.locator('.age-pyramid-point.chart-point').count() == 42, 'Piramide non ha 21 classi x 2 sessi')
        require(pyramid.locator('.chart-tooltip').count() == 42, 'Tooltip canonici assenti nella piramide')
        require(pyramid.locator('title').count() == 0, 'Piramide usa ancora tooltip SVG <title> non conformi')
        point = pyramid.locator('.age-pyramid-point').nth(8)
        tooltip = point.locator('.chart-tooltip')
        require(tooltip.get_attribute('hidden') is not None, 'Tooltip piramide visibile prima dell’interazione')
        point.hover()
        require(tooltip.get_attribute('hidden') is None, 'Tooltip piramide non si apre con l’interazione canonica')
        for text in ('Uomini', 'Donne', 'Scala: residenti per classe d’età', 'residenti', '100+'):
            require(pyramid.get_by_text(text, exact=True).count() >= 1, f'Elemento piramide assente: {text}')

        # Le componenti della variazione sono già indicatori autonomi: nessun pataccone duplicato.
        page.goto(urljoin(args.base, 'confronta/demografia/?indicatore=populationChange'), wait_until='networkidle')
        require(page.locator('.compare-change-components').count() == 0,
                'Blocco duplicato componenti variazione ancora presente nel confronto')
        require(page.locator('.demographic-change-components').count() == 0,
                'Blocco componenti variazione ancora presente nel confronto')
        page.goto(urljoin(args.base, 'comuni/massarosa/?tema=demografia&indicatore=populationChange'), wait_until='networkidle')
        require(page.locator('.demographic-change-components').count() == 0,
                'Blocco duplicato componenti variazione ancora presente nel comune')

        # Cittadinanza / paese di nascita: nessun testo può essere tagliato.
        page.goto(urljoin(args.base, 'confronta/demografia/?indicatore=foreignResidents'), wait_until='networkidle')
        compare_origins = page.locator('details.compare-foreign-origins').first
        require(compare_origins.count() == 1, 'Dettaglio RCS aggregato Versilia assente')
        compare_origins.locator('summary').click()
        compare_text = compare_origins.inner_text()
        for label in ('Versilia', 'Cittadinanze straniere più numerose', 'Paesi esteri di nascita più frequenti'):
            require(label in compare_text, f'Dettaglio RCS aggregato incompleto: {label}')
        assert_foreign_detail_not_clipped(compare_origins, 'foreignResidents confronto desktop')

        page.goto(urljoin(args.base, 'comuni/massarosa/?tema=demografia&indicatore=foreignResidents'), wait_until='networkidle')
        origins = page.locator('details.foreign-origins-detail').first
        require(origins.count() == 1, 'Dettaglio cittadinanza/paese di nascita assente')
        origins.locator('summary').click()
        origins_text = origins.inner_text()
        require('Cittadinanze straniere più numerose' in origins_text, 'Sezione cittadinanze assente')
        require('Paesi esteri di nascita più frequenti' in origins_text, 'Sezione paesi di nascita assente')
        require(origins.locator('.composite-town-detail > div').count() >= 4,
                'Dettaglio RCS troppo povero o non renderizzato')
        assert_foreign_detail_not_clipped(origins, 'foreignResidents comune desktop')

        # Mobile: i nuovi dettagli non devono introdurre overflow o clipping.
        page.set_viewport_size({'width': 390, 'height': 844})
        page.goto(urljoin(args.base, 'comuni/massarosa/?tema=demografia&indicatore=ageDistribution'), wait_until='networkidle')
        page.locator('details.age-pyramid-detail summary').click()
        assert_no_horizontal_overflow(page, 'ageDistribution mobile')
        page.goto(urljoin(args.base, 'confronta/demografia/?indicatore=foreignResidents'), wait_until='networkidle')
        compare_origins = page.locator('details.compare-foreign-origins').first
        compare_origins.locator('summary').click()
        assert_foreign_detail_not_clipped(compare_origins, 'foreignResidents confronto mobile')
        assert_no_horizontal_overflow(page, 'foreignResidents compare mobile')
        page.goto(urljoin(args.base, 'comuni/massarosa/?tema=demografia&indicatore=foreignResidents'), wait_until='networkidle')
        origins = page.locator('details.foreign-origins-detail').first
        origins.locator('summary').click()
        assert_foreign_detail_not_clipped(origins, 'foreignResidents comune mobile')
        assert_no_horizontal_overflow(page, 'foreignResidents town mobile')

        browser.close()
    print('Browser Demografia v2 OK: 85+ inline con scala cromatica completa, tooltip piramide canonici, RCS senza clipping e nessun duplicato variazione.')


if __name__ == '__main__':
    main()
