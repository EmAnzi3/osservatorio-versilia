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

        def assert_a5_town(metric_key: str, reference_geometry: dict | None = None) -> dict:
            page.goto(urljoin(args.base, f'comuni/viareggio/?tema=demografia&indicatore={metric_key}'), wait_until='networkidle')
            require(page.locator('main.a5-town-pilot[data-theme="demografia"]').count() == 1,
                    f'{metric_key}: pilot comunale A5 assente')

            # Navigation: same shared link component and exact computed pill styling as thematic golden master.
            town_theme_links = page.locator('.town-theme-row .context-nav-links a')
            require(town_theme_links.count() == 11, f'{metric_key}: temi comunali non 11/11')
            require(page.locator('.town-context-nav .theme-nav').count() == 0,
                    f'{metric_key}: vecchia theme-nav ancora presente')
            town_theme_styles = town_theme_links.evaluate_all(
                '''links => links.map(link => {
                  const s = getComputedStyle(link);
                  const r = link.getBoundingClientRect();
                  return {
                    key: link.dataset.contextTheme,
                    bg: s.backgroundColor,
                    border: s.borderColor,
                    color: s.color,
                    radius: s.borderRadius,
                    padding: s.padding,
                    fontSize: s.fontSize,
                    height: Math.round(r.height * 10) / 10,
                  };
                })'''
            )
            compare_styles = page.evaluate(
                '''() => window.__a5CompareThemeStyles || null'''
            )
            if compare_styles is None:
                compare_styles = compare_theme_styles
            require(town_theme_styles == compare_styles,
                    f'{metric_key}: pill temi diverse dalla pagina tematica')

            # Stable municipal shell.
            topic = page.locator('#town-topic')
            sidebar = topic.locator(':scope > .topic-controls')
            metric_layout = topic.locator(':scope > .town-metric-layout')
            primary = metric_layout.locator('.town-metric-primary')
            position = metric_layout.locator('.versilia-position')
            shell = topic.locator(':scope > .history-panel.a5-shared-chart .ux-view-shell')
            require(sidebar.count() == 1, f'{metric_key}: sidebar condivisa assente')
            require(metric_layout.count() == 1 and primary.count() == 1 and position.count() == 1,
                    f'{metric_key}: KPI comunali non rispettano lo shell stabile')
            require(shell.count() == 1, f'{metric_key}: chart shell condivisa assente')
            require(shell.locator(':scope > .ux-view-toolbar').count() == 1,
                    f'{metric_key}: toolbar duplicata o assente')
            require(shell.locator(':scope > .ux-view-toolbar > .town-data-actions').count() == 1,
                    f'{metric_key}: export/stampa non sono nella toolbar condivisa')
            require(topic.locator(':scope > .town-data-actions').count() == 0,
                    f'{metric_key}: toolbar parallela rimasta fuori dallo shared chart shell')

            # Current chart: when a lollipop row exists it must expose the exact shared reference tooltip.
            current_pane = shell.locator('[data-view-pane="current"]')
            require(current_pane.count() == 1 and current_pane.locator('.comparison-bars').count() >= 1,
                    f'{metric_key}: vista corrente non usa la superficie di confronto condivisa')
            selected_track = current_pane.locator('.bar-row.selected .bar-track').first
            if selected_track.count() == 1:
                selected_track.hover()
                tooltip = current_pane.locator('.bar-row.selected .bar-hover-label').first.inner_text()
                require(('Media semplice dei 7 comuni' in tooltip) or ('Versilia' in tooltip),
                        f'{metric_key}: tooltip senza riferimento territoriale condiviso: {tooltip!r}')

            # History: if enabled it must be a real rendered pane; otherwise the control must be disabled.
            history_button = shell.locator('[data-view-mode="history"]')
            require(history_button.count() == 1, f'{metric_key}: toggle storico assente')
            if history_button.is_enabled():
                history_button.click()
                history_pane = shell.locator('[data-view-pane="history"]')
                require(history_pane.count() == 1 and not history_pane.is_hidden(),
                        f'{metric_key}: storico abilitato ma pannello non visibile')
                require(history_pane.locator('.trend-chart, .ux-history-card, svg').count() >= 1,
                        f'{metric_key}: storico abilitato ma senza visualizzazione')
                shell.locator('[data-view-mode="current"]').click()
            else:
                require(history_button.get_attribute('disabled') is not None,
                        f'{metric_key}: storico non disponibile ma controllo non disabilitato')

            # Benchmark/method/reading scale: one stable slot each, irrespective of benchmark availability.
            benchmark_host = topic.locator(':scope > .town-benchmark-host')
            require(benchmark_host.count() == 1, f'{metric_key}: slot benchmark condiviso assente')
            require(benchmark_host.locator(':scope > .benchmark-section, :scope > .benchmark-unavailable').count() == 1,
                    f'{metric_key}: benchmark non usa un solo componente condiviso')
            tools = topic.locator(':scope > .town-post-benchmark-tools')
            require(tools.count() == 1, f'{metric_key}: tools post-chart condivisi assenti')
            method = tools.locator(':scope > .method-disclosure')
            scale = tools.locator(':scope > .reading-scale')
            require(method.count() == 1 and scale.count() == 1,
                    f'{metric_key}: Metodo/Scala non presenti nello stesso host')

            geometry = page.evaluate('''() => {
              const q = selector => document.querySelector(selector);
              const r = el => {
                if (!el) return null;
                const box = el.getBoundingClientRect();
                const style = getComputedStyle(el);
                return {
                  x: Math.round(box.x * 10) / 10,
                  width: Math.round(box.width * 10) / 10,
                  minHeight: style.minHeight,
                  radius: style.borderRadius,
                  padding: style.padding,
                };
              };
              const topic = q('#town-topic');
              const tools = q('#town-topic > .town-post-benchmark-tools');
              return {
                topic:r(topic),
                sidebar:r(q('#town-topic > .topic-controls')),
                metricLayout:r(q('#town-topic > .town-metric-layout')),
                primary:r(q('#town-topic .town-metric-primary')),
                position:r(q('#town-topic .versilia-position')),
                chart:r(q('#town-topic > .history-panel.a5-shared-chart')),
                benchmark:r(q('#town-topic > .town-benchmark-host')),
                tools:r(tools),
                method:r(tools?.querySelector(':scope > .method-disclosure')),
                scale:r(tools?.querySelector(':scope > .reading-scale')),
                topicGrid:getComputedStyle(topic).gridTemplateColumns,
                toolsGrid:getComputedStyle(tools).gridTemplateColumns,
              };
            }''')
            require(abs(geometry['benchmark']['width'] - geometry['topic']['width']) <= 2,
                    f'{metric_key}: benchmark non allineato alla larghezza standard: {geometry}')
            require(abs(geometry['tools']['width'] - geometry['topic']['width']) <= 2,
                    f'{metric_key}: tools non allineati alla larghezza standard: {geometry}')
            require(abs(geometry['method']['width'] - geometry['scale']['width']) <= 2,
                    f'{metric_key}: Metodo/Scala con larghezze diverse: {geometry}')
            require(abs(method.bounding_box()['height'] - scale.bounding_box()['height']) <= 2,
                    f'{metric_key}: Metodo/Scala con altezze diverse')
            assert_no_horizontal_overflow(page, f'A5 Viareggio {metric_key}')

            if reference_geometry is not None:
                for key in ('topic', 'sidebar', 'metricLayout', 'primary', 'position', 'chart', 'benchmark', 'tools', 'method', 'scale'):
                    require(abs(geometry[key]['width'] - reference_geometry[key]['width']) <= 2,
                            f'{metric_key}: larghezza {key} cambia rispetto a population: {geometry[key]} vs {reference_geometry[key]}')
                    require(geometry[key]['radius'] == reference_geometry[key]['radius'],
                            f'{metric_key}: radius {key} cambia rispetto a population')
                    require(geometry[key]['padding'] == reference_geometry[key]['padding'],
                            f'{metric_key}: padding {key} cambia rispetto a population')
                require(geometry['topicGrid'] == reference_geometry['topicGrid'],
                        f'{metric_key}: griglia shell cambia rispetto a population')
                require(geometry['toolsGrid'] == reference_geometry['toolsGrid'],
                        f'{metric_key}: griglia Metodo/Scala cambia rispetto a population')
            return geometry

        # Preserve the thematic golden-master computed navigation as the municipal reference.
        page.evaluate('(styles) => { window.__a5CompareThemeStyles = styles; }', compare_theme_styles)

        a5_demography_matrix = [
            'population',
            'ageDistribution',
            'oldAgeIndex',
            'dependencyIndices',
            'foreignResidents',
            'internalResidentialMobility',
            'foreignResidentialMobility',
            'totalResidentialMobility',
            'naturalDemographicDynamics',
            'populationChange',
        ]
        golden_geometry = assert_a5_town('population')
        for metric_key in a5_demography_matrix[1:]:
            assert_a5_town(metric_key, golden_geometry)
        print('A5 Viareggio/Demografia QA matrix OK: ' + ', '.join(a5_demography_matrix))

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
