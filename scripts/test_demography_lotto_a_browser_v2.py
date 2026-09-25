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


def assert_pyramid(pyramid, scope: str) -> None:
    require(pyramid.count() == 1, f'{scope}: piramide per età e sesso assente')
    pyramid.locator('summary').click()
    require(pyramid.locator('.trend-chart.age-pyramid-trend').count() == 1,
            f'{scope}: piramide fuori dalla superficie chart canonica')
    require(pyramid.locator('.age-pyramid-point.chart-point').count() == 42,
            f'{scope}: piramide non ha 21 classi x 2 sessi')
    require(pyramid.locator('.chart-tooltip').count() == 42,
            f'{scope}: tooltip canonici assenti nella piramide')
    require(pyramid.locator('title').count() == 0,
            f'{scope}: piramide usa tooltip SVG <title> non conformi')
    point = pyramid.locator('.age-pyramid-point').nth(8)
    tooltip = point.locator('.chart-tooltip')
    require(tooltip.get_attribute('hidden') is not None,
            f'{scope}: tooltip piramide visibile prima dell’interazione')
    point.hover()
    require(tooltip.get_attribute('hidden') is None,
            f'{scope}: tooltip piramide non si apre con l’interazione canonica')
    for text in ('Uomini', 'Donne', 'Scala: residenti per classe d’età', 'residenti', '100+'):
        require(pyramid.get_by_text(text, exact=True).count() >= 1, f'{scope}: elemento piramide assente: {text}')


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--base', default='http://127.0.0.1:8123/')
    args = parser.parse_args()

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={'width': 1440, 'height': 1100})

        # A5 town golden contract: municipal chrome must reuse the thematic components.
        page.goto(urljoin(args.base, 'confronta/demografia/?indicatore=population'), wait_until='networkidle')
        compare_theme_styles = page.locator('.compare-context-nav .context-nav-links a').evaluate_all(
            '''links => links.map(link => ({
              key: link.dataset.contextTheme,
              bg: getComputedStyle(link).backgroundColor,
              border: getComputedStyle(link).borderColor,
              color: getComputedStyle(link).color,
              radius: getComputedStyle(link).borderRadius,
            }))'''
        )
        require(len(compare_theme_styles) == 11, f'A5 compare: temi non 11/11: {len(compare_theme_styles)}')

        def assert_a5_town(metric_key: str, benchmark_selector: str) -> None:
            page.goto(urljoin(args.base, f'comuni/viareggio/?tema=demografia&indicatore={metric_key}'), wait_until='networkidle')
            require(page.locator('main.a5-town-pilot[data-theme="demografia"]').count() == 1,
                    f'{metric_key}: pilot comunale A5 assente')
            town_theme_links = page.locator('.town-theme-row .context-nav-links a')
            require(town_theme_links.count() == 11, f'{metric_key}: temi comunali non 11/11')
            require(page.locator('.town-context-nav .theme-nav').count() == 0,
                    f'{metric_key}: vecchia theme-nav ancora presente')
            town_theme_styles = town_theme_links.evaluate_all(
                '''links => links.map(link => ({
                  key: link.dataset.contextTheme,
                  bg: getComputedStyle(link).backgroundColor,
                  border: getComputedStyle(link).borderColor,
                  color: getComputedStyle(link).color,
                  radius: getComputedStyle(link).borderRadius,
                }))'''
            )
            require(town_theme_styles == compare_theme_styles,
                    f'{metric_key}: cromie/pill temi diverse dalla pagina tematica')

            shell = page.locator('#town-topic .history-panel.a5-shared-chart .ux-view-shell')
            require(shell.count() == 1, f'{metric_key}: chart shell condivisa assente')
            selected_track = shell.locator('[data-view-pane="current"] .bar-row.selected .bar-track').first
            require(selected_track.count() == 1, f'{metric_key}: riga del Comune selezionato assente')
            selected_track.hover()
            tooltip = shell.locator('[data-view-pane="current"] .bar-row.selected .bar-hover-label').first.inner_text()
            require('Media semplice dei 7 comuni' in tooltip,
                    f'{metric_key}: tooltip senza valore medio: {tooltip!r}')

            benchmark = page.locator(f'#town-topic > .town-benchmark-host {benchmark_selector}')
            require(benchmark.count() == 1,
                    f'{metric_key}: benchmark non usa il componente condiviso {benchmark_selector}')
            tools = page.locator('#town-topic > .town-post-benchmark-tools')
            require(tools.count() == 1, f'{metric_key}: tools post-chart condivisi assenti')
            method = tools.locator(':scope > .method-disclosure')
            scale = tools.locator(':scope > .reading-scale')
            require(method.count() == 1 and scale.count() == 1,
                    f'{metric_key}: Metodo/Scala non presenti nello stesso host')
            boxes = page.evaluate('''() => {
              const topic = document.querySelector('#town-topic');
              const benchmark = document.querySelector('#town-topic > .town-benchmark-host');
              const tools = document.querySelector('#town-topic > .town-post-benchmark-tools');
              const method = tools?.querySelector(':scope > .method-disclosure');
              const scale = tools?.querySelector(':scope > .reading-scale');
              const r = el => el ? el.getBoundingClientRect() : null;
              return { topic:r(topic), benchmark:r(benchmark), tools:r(tools), method:r(method), scale:r(scale) };
            }''')
            require(abs(boxes['benchmark']['width'] - boxes['topic']['width']) <= 2,
                    f'{metric_key}: benchmark non allineato alla larghezza standard: {boxes}')
            require(abs(boxes['tools']['width'] - boxes['topic']['width']) <= 2,
                    f'{metric_key}: tools non allineati alla larghezza standard: {boxes}')
            require(abs(boxes['method']['width'] - boxes['scale']['width']) <= 2,
                    f'{metric_key}: Metodo/Scala con larghezze diverse: {boxes}')
            require(abs(boxes['method']['height'] - boxes['scale']['height']) <= 2,
                    f'{metric_key}: Metodo/Scala con altezze diverse: {boxes}')

        assert_a5_town('population', '.benchmark-unavailable')
        assert_a5_town('oldAgeIndex', '.benchmark-section')

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

        # La stessa vista deve includere la piramide aggregata dell'intera Versilia.
        versilia_pyramid = page.locator('details.age-pyramid-detail').first
        assert_pyramid(versilia_pyramid, 'Versilia desktop')
        require('Versilia' in (versilia_pyramid.locator('svg').get_attribute('aria-label') or ''),
                'Piramide confronto non identificata come Versilia')

        # Scheda comunale: otto valori nella stessa griglia, nessun box aggiuntivo.
        page.goto(urljoin(args.base, 'comuni/forte-dei-marmi/?tema=demografia&indicatore=ageDistribution'), wait_until='networkidle')
        require(page.locator('.age85-inline-detail').count() == 0, 'Box 85+ autonomo presente nella scheda comunale')
        cells = page.locator('.composite-town-stack-shell > .composite-town-detail > div')
        require(cells.count() == 8, f'Griglia comunale non ha 8 valori: {cells.count()}')
        cell_text = '\n'.join(cells.all_inner_texts())
        require('80–84 anni' in cell_text and '85 anni e oltre' in cell_text,
                '80–84 / 85+ non sono nella stessa griglia degli altri valori')

        # Piramide comunale: stesso sistema tooltip dei grafici storici, niente <title> browser-native.
        pyramid = page.locator('details.age-pyramid-detail').first
        assert_pyramid(pyramid, 'Comune desktop')

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

        # Mobile: piramidi e nuovi dettagli non devono introdurre overflow o clipping.
        page.set_viewport_size({'width': 390, 'height': 844})
        page.goto(urljoin(args.base, 'confronta/demografia/?indicatore=ageDistribution'), wait_until='networkidle')
        mobile_versilia_pyramid = page.locator('details.age-pyramid-detail').first
        assert_pyramid(mobile_versilia_pyramid, 'Versilia mobile')
        assert_no_horizontal_overflow(page, 'ageDistribution compare mobile')
        page.goto(urljoin(args.base, 'comuni/massarosa/?tema=demografia&indicatore=ageDistribution'), wait_until='networkidle')
        page.locator('details.age-pyramid-detail summary').click()
        assert_no_horizontal_overflow(page, 'ageDistribution town mobile')
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
    print('Browser Demografia v2 OK: 85+ inline, piramidi comuni + Versilia con tooltip canonici, RCS senza clipping e nessun duplicato variazione.')


if __name__ == '__main__':
    main()
