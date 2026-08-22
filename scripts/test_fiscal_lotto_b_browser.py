#!/usr/bin/env python3
from __future__ import annotations

import argparse
from playwright.sync_api import sync_playwright


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def no_horizontal_overflow(page, label: str) -> None:
    dims = page.evaluate("""() => ({
      viewport: window.innerWidth,
      doc: document.documentElement.scrollWidth,
      body: document.body.scrollWidth
    })""")
    actual = max(int(dims['doc']), int(dims['body']))
    require(actual <= int(dims['viewport']) + 2, f'Overflow orizzontale in {label}: {dims}')


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--base', default='http://127.0.0.1:8123/')
    args = parser.parse_args()
    base = args.base.rstrip('/') + '/'

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={'width': 1440, 'height': 900})
        page_errors: list[str] = []
        page.on('pageerror', lambda error: page_errors.append(str(error)))

        page.goto(base + 'confronta/economia/?indicatore=fiscalRecoveryActivity', wait_until='networkidle')
        page.locator('[data-metric="fiscalRecoveryActivity"]').wait_for(state='visible')
        selector = page.locator('select[data-composite-component]')
        bars_html = page.locator('#compare-bars').inner_html()
        require(
            selector.count() == 1 and selector.is_visible(),
            'Selettore Lotto B assente nel confronto. '
            f'page_errors={page_errors!r}; compare-bars={bars_html[:2400]!r}',
        )
        labels = selector.locator('option').all_text_contents()
        require(labels == ['Recupero €/residente', 'Recupero totale', 'Contributo accertamento'], f'Opzioni inattese: {labels}')
        require('Non è un tasso di evasione fiscale' in page.locator('#compare-definition').inner_text(), 'Disclaimer metodologico non visibile')
        no_horizontal_overflow(page, 'confronto Fiscalità Lotto B desktop')

        selector.select_option('part-1')
        page.wait_for_timeout(100)
        compare_text = page.locator('#compare-bars').inner_text()
        require('4.929.520' in compare_text and 'Camaiore' in compare_text, 'Totale recupero Camaiore non leggibile nel confronto')

        selector.select_option('part-2')
        page.wait_for_timeout(100)
        compare_text = page.locator('#compare-bars').inner_text()
        require('Pietrasanta' in compare_text and '165' in compare_text, 'Contributo DAIT Pietrasanta non leggibile')
        # La grammatica canonica `currency` del sito visualizza gli euro senza decimali:
        # il dato ufficiale DAIT 82,50 € di Viareggio viene quindi reso come 83 €.
        require('Viareggio' in compare_text and '83' in compare_text, 'Contributo DAIT Viareggio non leggibile')

        page.goto(base + 'comuni/massarosa/?tema=economia&indicatore=fiscalRecoveryActivity', wait_until='networkidle')
        town_metric = page.locator('[data-metric="fiscalRecoveryActivity"]')
        require(town_metric.count() == 1 and town_metric.is_visible(), 'Indicatore non selezionabile nella scheda comunale')
        require('active' in (town_metric.get_attribute('class') or '').split(), 'Indicatore Lotto B non attivo nella scheda Massarosa')
        require('Recupero e accertamento' in town_metric.inner_text(), 'Etichetta Lotto B non visibile nella scheda Massarosa')
        town_selector = page.locator('select[data-composite-choice]')
        require(town_selector.count() == 1 and town_selector.is_visible(), 'Selettore Lotto B assente nella scheda Massarosa')
        town_labels = town_selector.locator('option').all_text_contents()
        require(town_labels == ['Recupero €/residente', 'Recupero totale', 'Contributo accertamento'], f'Letture Lotto B inattese nella scheda Massarosa: {town_labels}')
        require('Non è un tasso di evasione fiscale' in page.locator('.town-metric-primary').inner_text(), 'Disclaimer Lotto B assente nella scheda Massarosa')
        no_horizontal_overflow(page, 'scheda Massarosa Fiscalità Lotto B desktop')

        page.set_viewport_size({'width': 390, 'height': 844})
        page.goto(base + 'confronta/economia/?indicatore=fiscalRecoveryActivity', wait_until='networkidle')
        require(page.locator('select[data-composite-component]').is_visible(), 'Selettore Lotto B non visibile su mobile')
        no_horizontal_overflow(page, 'confronto Fiscalità Lotto B mobile')
        page.locator('select[data-composite-component]').select_option('part-2')
        page.wait_for_timeout(100)
        require(page.locator('#compare-bars').is_visible(), 'Confronto contributo DAIT non visibile su mobile')

        page.goto(base + 'comuni/forte-dei-marmi/?tema=economia&indicatore=fiscalRecoveryActivity', wait_until='networkidle')
        mobile_metric = page.locator('[data-metric="fiscalRecoveryActivity"]')
        require(mobile_metric.count() == 1, 'Indicatore non selezionabile a Forte dei Marmi mobile')
        require(page.locator('select[data-composite-choice]').is_visible(), 'Selettore Lotto B non visibile a Forte dei Marmi mobile')
        no_horizontal_overflow(page, 'scheda Forte dei Marmi Fiscalità Lotto B mobile')
        browser.close()

    print('Fiscalità Lotto B browser: confronto/schede e selector desktop-mobile verificati senza overflow.')


if __name__ == '__main__':
    main()
