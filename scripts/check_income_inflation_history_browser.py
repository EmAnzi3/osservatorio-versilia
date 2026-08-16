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
    require('variazione reale' in copy,
            f'{url}: il grafico non chiarisce che il tooltip contiene la variazione reale')

    note = page.locator(f'{scope} .ux-view-note').inner_text()
    require('2016 = 0%' in note and 'variazione reale' in note and 'rapporto' in note,
            f'{url}: nota metodologica storico non sufficientemente esplicita')

    inflation_line = page.locator(f'{scope} .ux-inflation-reference .ux-series-line')
    require(inflation_line.count() == 1, f'{url}: linea inflazione assente')
    dash = inflation_line.evaluate("el => getComputedStyle(el).strokeDasharray")
    require(dash not in ('none', '', '0px'), f'{url}: linea inflazione non distinguibile visivamente')

    page.locator(f'{scope} [data-history-select="massarosa"]').click()
    massarosa = page.locator(f'{scope} .ux-series-group[data-history-town="massarosa"]')
    require(massarosa.count() == 1 and 'is-selected' in (massarosa.get_attribute('class') or ''),
            f'{url}: selezione comunale non funziona con il riferimento inflazione')
    require(page.locator(f'{scope} .ux-inflation-reference').count() == 1,
            f'{url}: riferimento inflazione scompare dopo selezione comunale')

    point = massarosa.locator('.chart-point').last
    aria = point.get_attribute('aria-label') or ''
    require('Reddito nominale:' in aria and 'Inflazione:' in aria and 'Variazione reale:' in aria,
            f'{url}: aria-label del punto storico incompleta')
    require('Variazione reale: n.d.' not in aria,
            f'{url}: serie della variazione reale non raggiunge il renderer')

    # Focus is an actual supported interaction for chart points and avoids false
    # negatives when two SVG series cross and overlap at the same coordinate.
    point.focus()
    tooltip = point.locator('.chart-tooltip')
    require(tooltip.count() == 1 and tooltip.is_visible(), f'{url}: tooltip storico non visibile')
    tooltip_text = tooltip.inner_text()
    require('Reddito nominale:' in tooltip_text,
            f'{url}: tooltip senza crescita nominale del reddito')
    require('Inflazione:' in tooltip_text,
            f'{url}: tooltip senza inflazione cumulata')
    require('Variazione reale:' in tooltip_text and 'Variazione reale: n.d.' not in tooltip_text,
            f'{url}: tooltip senza variazione reale corretta')

    contained = tooltip.evaluate("""el => {
      const rect = el.querySelector('rect')?.getBBox();
      const texts = [...el.querySelectorAll('text')].map(node => node.getBBox());
      if (!rect || !texts.length) return false;
      const eps = 1;
      return texts.every(box =>
        box.x >= rect.x - eps && box.y >= rect.y - eps &&
        box.x + box.width <= rect.x + rect.width + eps &&
        box.y + box.height <= rect.y + rect.height + eps
      );
    }""")
    require(contained, f'{url}: testo del tooltip esce dal box')


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
            '#compare-bars',
        )
        validate_history(
            page,
            urljoin(base, 'comuni/massarosa/?tema=economia&indicatore=incomeVsInflation'),
            '.history-panel',
        )

        browser.close()

    print('Income/inflation browser QA passed: nominal income, NIC Italia and real change visible in both histories')


if __name__ == '__main__':
    main()
