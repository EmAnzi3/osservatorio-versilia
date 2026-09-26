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
        require(len(compare_theme_styles) == 11, f'A5 compare: temi non 11/11: {len(compare_theme_styles)}')
        demography_active_bg = page.locator('.compare-context-nav a[data-context-theme="demografia"].active').evaluate(
            "el => getComputedStyle(el).backgroundColor"
        )
        demography_geometry = page.evaluate('''() => {
          const rect = selector => {
            const el=document.querySelector(selector);
            const r=el.getBoundingClientRect();
            const s=getComputedStyle(el);
            return {width:Math.round(r.width*10)/10, radius:s.borderRadius};
          };
          return {
            hero:rect('.topic-hero'),
            sidebar:rect('.topic-controls'),
            chart:rect('#compare-bars'),
            dashboard:getComputedStyle(document.querySelector('.topic-dashboard')).gridTemplateColumns,
          };
        }''')

        # A5.5 lotto 1: Economia uses the exact A5 shell, with theme-parametric accents.
        page.goto(urljoin(args.base, 'confronta/economia/'), wait_until='networkidle')
        require(page.locator('main.a5-editorial-pilot[data-theme="economia"]').count() == 1,
                'A5.5 Economia: shell condiviso A5 assente')
        require(page.locator('.brain-drain-context').count() == 0,
                'A5.5 Economia: contenuto Demografia propagato nel tema sbagliato')
        require(page.locator('.topic-controls').count() == 1 and page.locator('#compare-bars.a5-shared-chart').count() == 1,
                'A5.5 Economia: workspace condiviso incompleto')
        require(page.locator('#compare-territori .topic-town-card').count() == 7,
                'A5.5 Economia: schede comunali non 7/7')
        facts = page.locator('.compare-showcase-facts').inner_text()
        require('indicatori Economia' in facts and 'indicatori Demografia' not in facts,
                f'A5.5 Economia: hero non parametrico: {facts!r}')
        economy_style = page.evaluate('''() => {
          const active=document.querySelector('.compare-context-nav a[data-context-theme="economia"].active');
          const symbol=document.querySelector('.topic-symbol');
          return {
            activeBg:getComputedStyle(active).backgroundColor,
            symbolColor:getComputedStyle(symbol).color,
            soft:getComputedStyle(document.querySelector('main.a5-editorial-pilot')).getPropertyValue('--ds-theme-soft').trim(),
          };
        }''')
        require(economy_style['activeBg'] == economy_style['symbolColor'],
                f'A5.5 Economia: accento DS2 incoerente: {economy_style}')
        require(economy_style['activeBg'] != demography_active_bg,
                'A5.5 Economia: accento rimasto Demografia')
        economy_geometry = page.evaluate('''() => {
          const rect = selector => {
            const el=document.querySelector(selector);
            const r=el.getBoundingClientRect();
            const s=getComputedStyle(el);
            return {width:Math.round(r.width*10)/10, radius:s.borderRadius};
          };
          return {
            hero:rect('.topic-hero'),
            sidebar:rect('.topic-controls'),
            chart:rect('#compare-bars'),
            dashboard:getComputedStyle(document.querySelector('.topic-dashboard')).gridTemplateColumns,
          };
        }''')
        require(economy_geometry == demography_geometry,
                f'A5.5 Economia: geometria diverge dal golden Demografia: {economy_geometry} != {demography_geometry}')
        assert_no_horizontal_overflow(page, 'A5.5 Economia desktop')
        page.set_viewport_size({'width': 390, 'height': 844})
        page.goto(urljoin(args.base, 'confronta/economia/'), wait_until='networkidle')
        assert_no_horizontal_overflow(page, 'A5.5 Economia mobile 390px')
        require(page.locator('main.a5-editorial-pilot[data-theme="economia"]').count() == 1,
                'A5.5 Economia mobile: shell A5 assente')
        page.set_viewport_size({'width': 1440, 'height': 1100})

        # A5.5 lotto 2: Lavoro reuses the same shell across every indicator in the theme.
        page.goto(urljoin(args.base, 'confronta/lavoro/'), wait_until='networkidle')
        require(page.locator('main.a5-editorial-pilot[data-theme="lavoro"]').count() == 1,
                'A5.5 Lavoro: shell condiviso A5 assente')
        lavoro_geometry = page.evaluate('''() => {
          const rect = selector => {
            const el=document.querySelector(selector);
            const r=el.getBoundingClientRect();
            const s=getComputedStyle(el);
            return {width:Math.round(r.width*10)/10, radius:s.borderRadius};
          };
          return {
            hero:rect('.topic-hero'),
            sidebar:rect('.topic-controls'),
            chart:rect('#compare-bars'),
            dashboard:getComputedStyle(document.querySelector('.topic-dashboard')).gridTemplateColumns,
          };
        }''')
        require(lavoro_geometry == demography_geometry,
                f'A5.5 Lavoro: geometria diverge dal golden Demografia: {lavoro_geometry} != {demography_geometry}')
        lavoro_style = page.evaluate('''() => {
          const active=document.querySelector('.compare-context-nav a[data-context-theme="lavoro"].active');
          const symbol=document.querySelector('.topic-symbol');
          return {
            activeBg:getComputedStyle(active).backgroundColor,
            symbolColor:getComputedStyle(symbol).color,
          };
        }''')
        require(lavoro_style['activeBg'] == lavoro_style['symbolColor'],
                f'A5.5 Lavoro: accento DS2 incoerente: {lavoro_style}')
        require(lavoro_style['activeBg'] != demography_active_bg,
                'A5.5 Lavoro: accento rimasto Demografia')
        lavoro_metrics = page.locator('.topic-controls [data-metric]').evaluate_all(
            "els => els.map(el => el.dataset.metric).filter(Boolean)"
        )
        require(len(lavoro_metrics) >= 1, 'A5.5 Lavoro: nessun indicatore trovato nella sidebar')
        for metric_key in lavoro_metrics:
            page.goto(urljoin(args.base, f'confronta/lavoro/?indicatore={metric_key}'), wait_until='networkidle')
            require(page.locator('main.a5-editorial-pilot[data-theme="lavoro"]').count() == 1,
                    f'A5.5 Lavoro/{metric_key}: shell A5 assente')
            require(page.locator('#compare-bars.a5-shared-chart').count() == 1,
                    f'A5.5 Lavoro/{metric_key}: chart shell condiviso assente')
            require(page.locator('.brain-drain-context').count() == 0,
                    f'A5.5 Lavoro/{metric_key}: contenuto Demografia presente')
            assert_no_horizontal_overflow(page, f'A5.5 Lavoro/{metric_key} desktop')
            pyramid = page.locator('#compare-demographic-pyramid .demographic-rate-pyramid')
            if pyramid.count():
                sizes = pyramid.evaluate('''el => ({
                  client:el.clientWidth,
                  scroll:el.scrollWidth,
                  svgClient:el.querySelector('svg')?.clientWidth || 0
                })''')
                require(sizes['scroll'] <= sizes['client'] + 2,
                        f'A5.5 Lavoro/{metric_key}: piramide con overflow {sizes}')
        page.set_viewport_size({'width': 390, 'height': 844})
        page.goto(urljoin(args.base, 'confronta/lavoro/'), wait_until='networkidle')
        assert_no_horizontal_overflow(page, 'A5.5 Lavoro mobile 390px')
        require(page.locator('main.a5-editorial-pilot[data-theme="lavoro"]').count() == 1,
                'A5.5 Lavoro mobile: shell A5 assente')
        page.set_viewport_size({'width': 1440, 'height': 1100})
        print('A5.5 Lavoro compare QA OK: tutti gli indicatori desktop + shell mobile 390px')

        # A5.5 bulk gate: every thematic compare route and every sidebar indicator.
        bulk_theme_keys = [item['key'] for item in compare_theme_styles]
        require(len(bulk_theme_keys) == 11 and len(set(bulk_theme_keys)) == 11,
                f'A5.5 bulk: temi inattesi {bulk_theme_keys}')

        def assert_bulk_theme(theme_key: str, mobile: bool = False) -> int:
            page.goto(urljoin(args.base, f'confronta/{theme_key}/'), wait_until='networkidle')
            require(page.locator(f'main.a5-editorial-pilot[data-theme="{theme_key}"]').count() == 1,
                    f'A5.5 bulk {theme_key}: shell A5 assente')
            require(page.locator(f'.compare-context-nav a[data-context-theme="{theme_key}"].active').count() == 1,
                    f'A5.5 bulk {theme_key}: navigazione tema attivo incoerente')
            require(page.locator('#compare-territori .topic-town-card').count() == 7,
                    f'A5.5 bulk {theme_key}: card comunali non 7/7')
            if theme_key != 'demografia':
                require(page.locator('.brain-drain-context').count() == 0,
                        f'A5.5 bulk {theme_key}: contenuto Demografia presente')
            if theme_key == 'sicurezza':
                require(page.locator('.crime-context').count() <= 1,
                        'A5.5 bulk sicurezza: contesto sicurezza duplicato')

            theme_geometry = page.evaluate('''() => {
              const rect = selector => {
                const el=document.querySelector(selector);
                const r=el.getBoundingClientRect();
                const s=getComputedStyle(el);
                return {width:Math.round(r.width*10)/10, radius:s.borderRadius};
              };
              return {
                hero:rect('.topic-hero'),
                sidebar:rect('.topic-controls'),
                chart:rect('#compare-bars'),
                dashboard:getComputedStyle(document.querySelector('.topic-dashboard')).gridTemplateColumns,
              };
            }''')
            require(theme_geometry == demography_geometry,
                    f'A5.5 bulk {theme_key}: geometria diverge dal golden: {theme_geometry} != {demography_geometry}')

            accent = page.evaluate(f'''() => {{
              const active=document.querySelector('.compare-context-nav a[data-context-theme="{theme_key}"].active');
              const symbol=document.querySelector('.topic-symbol');
              return {{
                active:getComputedStyle(active).backgroundColor,
                symbol:getComputedStyle(symbol).color,
              }};
            }}''')
            require(accent['active'] == accent['symbol'],
                    f'A5.5 bulk {theme_key}: accento tema incoerente {accent}')

            metric_keys = page.locator('.topic-controls [data-metric]').evaluate_all(
                "els => [...new Set(els.map(el => el.dataset.metric).filter(Boolean))]"
            )
            require(len(metric_keys) >= 1, f'A5.5 bulk {theme_key}: nessun indicatore')

            for metric_key in metric_keys:
                button = page.locator(f'.topic-controls [data-metric="{metric_key}"]').first
                button.click()
                require(button.get_attribute('aria-selected') == 'true',
                        f'A5.5 bulk {theme_key}/{metric_key}: controllo non attivo dopo click')
                require(page.locator('#compare-bars.a5-shared-chart').count() == 1,
                        f'A5.5 bulk {theme_key}/{metric_key}: chart shell assente')
                chart_state = page.locator('#compare-bars').evaluate('''el => ({
                  childCount:el.children.length,
                  text:el.innerText.trim(),
                  client:el.clientWidth,
                  scroll:el.scrollWidth,
                })''')
                require(chart_state['childCount'] > 0 or bool(chart_state['text']),
                        f'A5.5 bulk {theme_key}/{metric_key}: chart vuoto')
                require(chart_state['scroll'] <= chart_state['client'] + 2,
                        f'A5.5 bulk {theme_key}/{metric_key}: chart overflow {chart_state}')
                require(page.locator('#compare-tools.compare-post-benchmark-tools').count() == 1,
                        f'A5.5 bulk {theme_key}/{metric_key}: tools host assente')
                if metric_key.startswith('slowMobility'):
                    require(page.locator('#compare-tools .a5-special-route-actions a[href*="percorsi/"]').count() == 1,
                            f'A5.5 bulk {theme_key}/{metric_key}: CTA cartografia contestuale assente')
                    require(page.locator('.compare-panel-heading .data-actions a[href*="percorsi/"]').count() == 0,
                            f'A5.5 bulk {theme_key}/{metric_key}: CTA cartografia duplicata nella toolbar')
                assert_no_horizontal_overflow(
                    page,
                    f'A5.5 bulk {theme_key}/{metric_key} {"mobile" if mobile else "desktop"}'
                )

                pyramid = page.locator('#compare-demographic-pyramid .demographic-rate-pyramid')
                if pyramid.count():
                    pyramid_state = pyramid.evaluate('''el => ({
                      client:el.clientWidth,
                      scroll:el.scrollWidth,
                    })''')
                    require(pyramid_state['scroll'] <= pyramid_state['client'] + 2,
                            f'A5.5 bulk {theme_key}/{metric_key}: pyramid overflow {pyramid_state}')
            return len(metric_keys)

        bulk_counts = {}
        page.set_viewport_size({'width': 1440, 'height': 1100})
        for theme_key in bulk_theme_keys:
            bulk_counts[theme_key] = assert_bulk_theme(theme_key, mobile=False)

        page.set_viewport_size({'width': 390, 'height': 844})
        for theme_key in bulk_theme_keys:
            mobile_count = assert_bulk_theme(theme_key, mobile=True)
            require(mobile_count == bulk_counts[theme_key],
                    f'A5.5 bulk {theme_key}: numero indicatori diverso desktop/mobile')
        page.set_viewport_size({'width': 1440, 'height': 1100})
        print('A5.5 bulk compare QA OK: ' + ', '.join(
            f'{theme}={count}' for theme, count in bulk_counts.items()
        ))

        # Shared graph controls: the municipal selectors must compute to the same DS2 styles.
        page.goto(urljoin(args.base, 'confronta/demografia/?indicatore=internalResidentialMobility'), wait_until='networkidle')
        compare_control_styles = page.evaluate('''() => {
          const root = document.querySelector('#compare-bars .compare-chart-toolbar .compare-view-controls');
          const select = root?.querySelector('.compare-choice-select select');
          const switchRoot = root?.querySelector('.scale-switch');
          const active = switchRoot?.querySelector('button.active');
          const pack = el => {
            if (!el) return null;
            const s = getComputedStyle(el);
            return {
              background:s.backgroundColor,
              borderColor:s.borderColor,
              color:s.color,
              radius:s.borderRadius,
              padding:s.padding,
              minHeight:s.minHeight,
            };
          };
          return {root:pack(root), select:pack(select), switchRoot:pack(switchRoot), active:pack(active)};
        }''')
        require(compare_control_styles['root'] is not None and compare_control_styles['select'] is not None,
                'A5 compare: riferimento cromatico controlli non disponibile')

        def assert_a5_town(metric_key: str, reference_geometry: dict | None = None, town_slug: str = 'viareggio') -> dict:
            page.goto(urljoin(args.base, f'comuni/{town_slug}/?tema=demografia&indicatore={metric_key}'), wait_until='networkidle')
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
            primary_label = primary.locator(':scope > [data-composite-primary-label]')
            require(primary_label.count() == 1 and primary_label.inner_text().strip(),
                    f'{town_slug}/{metric_key}: label KPI primaria assente')
            label_style = primary_label.evaluate('''el => {
              const s=getComputedStyle(el);
              const bg=getComputedStyle(el.parentElement).backgroundColor;
              return {color:s.color, opacity:s.opacity, background:bg, display:s.display};
            }''')
            require(label_style['display'] != 'none' and label_style['opacity'] == '1',
                    f'{town_slug}/{metric_key}: label KPI non visibile: {label_style}')
            require(label_style['color'] != label_style['background'],
                    f'{town_slug}/{metric_key}: label KPI senza contrasto: {label_style}')
            require(shell.count() == 1, f'{metric_key}: chart shell condivisa assente')
            require(shell.locator(':scope > .ux-view-toolbar').count() == 1,
                    f'{metric_key}: toolbar duplicata o assente')
            require(shell.locator(':scope > .ux-view-toolbar > .town-data-actions').count() == 1,
                    f'{metric_key}: export/stampa non sono nella toolbar condivisa')
            require(topic.locator(':scope > .town-data-actions').count() == 0,
                    f'{metric_key}: toolbar parallela rimasta fuori dallo shared chart shell')

            # Correct graph family is part of the golden contract.
            current_pane = shell.locator('[data-view-pane="current"]')
            visual = current_pane.locator(':scope > .a5-town-current-visual')
            require(current_pane.count() == 1 and visual.count() == 1,
                    f'{metric_key}: superficie corrente condivisa assente')
            primary_selector = primary.locator('.composite-read-selector')
            if primary_selector.count() == 1:
                require(primary_selector.is_hidden(),
                        f'{metric_key}: selettore duplicato ancora visibile nel KPI')

            if metric_key == 'ageDistribution':
                require(visual.locator('.composite-distribution-list').count() == 1,
                        'ageDistribution: manca lo stacked distribution condiviso')
                require(visual.locator('.composite-distribution-row').count() == 7,
                        'ageDistribution: stacked comparison non 7/7')
                require(visual.locator('.composite-distribution-row.selected').count() == 1,
                        'ageDistribution: Comune aperto non evidenziato')
                require(visual.locator('.comparison-bars').count() == 0,
                        'ageDistribution: non deve degradare al lollipop dell’età media')
                require(current_pane.locator(':scope > .a5-town-current-detail .composite-town-stack-shell').count() == 1,
                        'ageDistribution: dettaglio comunale scollegato dal grafico')
            else:
                require(visual.locator('.comparison-bars').count() >= 1,
                        f'{metric_key}: renderer comparativo condiviso assente')
                selected_track = visual.locator('.bar-row.selected .bar-track').first
                if selected_track.count() == 1:
                    selected_track.hover()
                    tooltip = visual.locator('.bar-row.selected .bar-hover-label').first.inner_text()
                    require(('Media semplice dei 7 comuni' in tooltip) or ('Versilia' in tooltip),
                            f'{metric_key}: tooltip senza riferimento territoriale condiviso: {tooltip!r}')

            if metric_key in ('dependencyIndices','foreignResidents','internalResidentialMobility',
                              'foreignResidentialMobility','totalResidentialMobility','naturalDemographicDynamics'):
                controls = visual.locator('.compare-chart-toolbar .compare-view-controls')
                require(controls.count() == 1, f'{metric_key}: controlli grafico condivisi assenti')
                control_styles = controls.evaluate('''root => {
                  const select = root.querySelector('.compare-choice-select select');
                  const switchRoot = root.querySelector('.scale-switch');
                  const active = switchRoot?.querySelector('button.active');
                  const pack = el => {
                    if (!el) return null;
                    const s = getComputedStyle(el);
                    return {
                      background:s.backgroundColor,
                      borderColor:s.borderColor,
                      color:s.color,
                      radius:s.borderRadius,
                      padding:s.padding,
                      minHeight:s.minHeight,
                    };
                  };
                  return {root:pack(root), select:pack(select), switchRoot:pack(switchRoot), active:pack(active)};
                }''')
                require(control_styles['root'] == compare_control_styles['root'],
                        f'{metric_key}: cromia/geometria host controlli diversa dal confronto tematico')
                if control_styles['select'] is not None:
                    require(control_styles['select'] == compare_control_styles['select'],
                            f'{metric_key}: select non conforme al controllo tematico')
                if control_styles['switchRoot'] is not None:
                    require(control_styles['switchRoot'] == compare_control_styles['switchRoot'],
                            f'{metric_key}: switch non conforme al controllo tematico')
                    require(control_styles['active'] == compare_control_styles['active'],
                            f'{metric_key}: stato attivo switch non conforme al controllo tematico')

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
            assert_no_horizontal_overflow(page, f'A5 {town_slug} {metric_key}')

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

        # The thematic golden-master computed navigation is the municipal reference.

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

        # Second-town proof: the approved Viareggio shell must be data-driven, not Viareggio-specific.
        for metric_key in a5_demography_matrix:
            assert_a5_town(metric_key, golden_geometry, 'massarosa')
        page.goto(urljoin(args.base, 'comuni/massarosa/?tema=demografia&indicatore=population'), wait_until='networkidle')
        require(page.locator('.town-hero-shell').count() == 1, 'Massarosa: hero A5 condiviso assente')
        require(page.locator('.town-headline-stats > div').count() == 3, 'Massarosa: headline stats non 3/3')
        require(page.locator('.town-brief > article').count() == 3, 'Massarosa: sintesi non 3/3')
        require('1869' in page.locator('.town-headline-stats').inner_text(),
                'Massarosa: anno di istituzione 1869 assente dal profilo A5')
        massarosa_hero = page.locator('.town-hero')
        massarosa_bg = massarosa_hero.evaluate("el => getComputedStyle(el).backgroundImage")
        require('MassarosaPanorama.JPG' in massarosa_bg,
                f'Massarosa: immagine hero dedicata assente: {massarosa_bg}')
        require(page.locator('.town-hero-photo-credit').count() == 1,
                'Massarosa: attribuzione foto hero assente')
        print('A5 Massarosa/Demografia second-town proof OK: 10/10 indicatori')

        def assert_a5_town_responsive(metric_key: str, width: int, height: int, town_slug: str = 'viareggio') -> None:
            page.set_viewport_size({'width': width, 'height': height})
            page.goto(urljoin(args.base, f'comuni/{town_slug}/?tema=demografia&indicatore={metric_key}'), wait_until='networkidle')
            layout = page.evaluate('''() => {
              const q = selector => document.querySelector(selector);
              const rect = el => {
                if (!el) return null;
                const r = el.getBoundingClientRect();
                return {
                  x:Math.round(r.x * 10) / 10,
                  top:Math.round(r.top * 10) / 10,
                  bottom:Math.round(r.bottom * 10) / 10,
                  width:Math.round(r.width * 10) / 10,
                  clientWidth:el.clientWidth,
                  scrollWidth:el.scrollWidth,
                };
              };
              const topic = q('#town-topic');
              const sidebar = q('#town-topic > .topic-controls');
              const metric = q('#town-topic > .town-metric-layout');
              const primary = q('#town-topic .town-metric-primary');
              const position = q('#town-topic .versilia-position');
              const chart = q('#town-topic > .history-panel.a5-shared-chart');
              const benchmark = q('#town-topic > .town-benchmark-host');
              const tools = q('#town-topic > .town-post-benchmark-tools');
              const children = [...topic.children];
              const directExtras = [...topic.children].filter(el =>
                el.classList.contains('a5-town-extra-context') ||
                el.classList.contains('detail-disclosure') ||
                el.classList.contains('topic-deep-dive')
              );
              const columns = el => getComputedStyle(el).gridTemplateColumns.trim().split(/\\s+/).filter(Boolean).length;
              return {
                topicColumns:columns(topic),
                metricColumns:columns(metric),
                sidebar:rect(sidebar),
                metric:rect(metric),
                primary:rect(primary),
                position:rect(position),
                chart:rect(chart),
                benchmark:rect(benchmark),
                tools:rect(tools),
                order:[children.indexOf(chart), children.indexOf(benchmark), children.indexOf(tools)],
                extraBeforeTools:directExtras.some(el => children.indexOf(el) > -1 && children.indexOf(el) < children.indexOf(tools)),
                fixedDetailInsideChart:Boolean(chart?.querySelector(':scope > .composite-fixed-detail')),
                overflow:[
                  ['primary',primary],['position',position],['benchmark',benchmark],['tools',tools]
                ].filter(([,el]) => el && el.scrollWidth > el.clientWidth + 2).map(([name]) => name),
              };
            }''')
            require(layout['topicColumns'] == 1, f'{metric_key}@{width}: shell comunale non monocolonna: {layout}')
            require(layout['metricColumns'] == 1, f'{metric_key}@{width}: KPI/Versilia ancora affiancati: {layout}')
            require(layout['position']['top'] >= layout['primary']['bottom'] - 2,
                    f'{metric_key}@{width}: KPI e Versilia non sono realmente impilati: {layout}')
            require(abs(layout['primary']['width'] - layout['metric']['width']) <= 2,
                    f'{metric_key}@{width}: KPI primario non occupa la colonna: {layout}')
            require(abs(layout['position']['width'] - layout['metric']['width']) <= 2,
                    f'{metric_key}@{width}: KPI Versilia non occupa la colonna: {layout}')
            require(layout['metric']['top'] >= layout['sidebar']['bottom'] - 2,
                    f'{metric_key}@{width}: KPI sovrapposto alla sidebar: {layout}')
            require(layout['chart']['top'] >= layout['metric']['bottom'] - 2,
                    f'{metric_key}@{width}: grafico fuori ordine dopo i KPI: {layout}')
            require(layout['benchmark']['top'] >= layout['chart']['bottom'] - 2,
                    f'{metric_key}@{width}: benchmark precede il grafico: {layout}')
            require(layout['tools']['top'] >= layout['benchmark']['bottom'] - 2,
                    f'{metric_key}@{width}: Metodo/Scala precedono il benchmark: {layout}')
            require(layout['order'][0] < layout['order'][1] < layout['order'][2],
                    f'{metric_key}@{width}: ordine DOM chart/benchmark/tools non canonico: {layout}')
            require(not layout['extraBeforeTools'],
                    f'{metric_key}@{width}: contenuto opzionale inserito prima di Metodo/Scala: {layout}')
            require(not layout['fixedDetailInsideChart'],
                    f'{metric_key}@{width}: dettaglio composito ancora dentro lo shared chart shell')
            require(not layout['overflow'],
                    f'{metric_key}@{width}: testo/contenuto esce dai box {layout["overflow"]}')
            assert_no_horizontal_overflow(page, f'A5 {town_slug} {metric_key} responsive {width}px')

        for viewport in ((768, 1024), (390, 844)):
            for metric_key in a5_demography_matrix:
                assert_a5_town_responsive(metric_key, *viewport)
        massarosa_responsive_probe = (
            'population',
            'ageDistribution',
            'foreignResidents',
            'foreignResidentialMobility',
        )
        for viewport in ((768, 1024), (390, 844)):
            for metric_key in massarosa_responsive_probe:
                assert_a5_town_responsive(metric_key, *viewport, town_slug='massarosa')
        page.set_viewport_size({'width': 1440, 'height': 1100})
        print('A5 Viareggio responsive QA OK: 10/10 indicatori a 768px e 390px')
        print('A5 Massarosa responsive proof OK: scalar/distribution/stock/mobility a 768px e 390px')

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
