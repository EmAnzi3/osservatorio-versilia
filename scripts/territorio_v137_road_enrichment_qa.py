#!/usr/bin/env python3
import re
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE = 'http://127.0.0.1:8765'
OUT = Path('reports/territorio-v137-road-enrichment')
EXPECTED = [
    'Lunghezza del grafo', 'Densità del grafo', 'Strade comunali',
    'Strade provinciali', 'Strade regionali', 'Strade statali',
    'Strade private', 'Elementi pavimentati', 'Elementi non pavimentati',
    'Pavimentazione non classificata',
]


def verify_indicator(page, mode):
    response = page.goto(f'{BASE}/indicatori/grafo-viario-iter-net/', wait_until='networkidle')
    if not response or response.status != 200:
        raise RuntimeError(f'{mode}: indicator HTTP {response.status if response else None}')
    select = page.locator('.indicator-current select[data-composite-component]').first
    select.wait_for(state='visible')
    labels = [x.strip() for x in select.locator('option').all_text_contents()]
    if labels != EXPECTED:
        raise RuntimeError(f'{mode}: opzioni inattese {labels}')
    values = select.locator('option').evaluate_all('(els)=>els.map(e=>e.value)')
    for value in values:
        select.select_option(value)
        page.wait_for_timeout(180)
        comparison = page.locator('.indicator-current .comparison-bars').first
        page.wait_for_function("el => ['lollipop','percent-dotplot','signed-dotplot'].includes(el.dataset.viz)", arg=comparison.element_handle())
        rows = comparison.locator('.bar-row[aria-label]')
        if rows.count() != 7:
            raise RuntimeError(f'{mode}/{value}: righe valorizzate {rows.count()}/7')
        row_labels = [x or '' for x in rows.evaluate_all('(els)=>els.map(e=>e.getAttribute("aria-label"))')]
        if not all(re.search(r'\d', label) for label in row_labels):
            raise RuntimeError(f'{mode}/{value}: valori non leggibili {row_labels}')
        if comparison.locator('.comparison-dot').count() < 1 or comparison.locator('.comparison-stem').count() < 1:
            raise RuntimeError(f'{mode}/{value}: lollipop incompleto')
    page.screenshot(path=str(OUT / f'grafo-viario-iter-net-{mode}.png'), full_page=True)


def verify_town(page):
    response = page.goto(f'{BASE}/comuni/massarosa/?tema=ambiente&indicatore=roadNetworkProfile', wait_until='networkidle')
    if not response or response.status != 200:
        raise RuntimeError(f'Massarosa: HTTP {response.status if response else None}')
    panel = page.locator('#town-topic').first
    panel.wait_for(state='visible')
    body = panel.inner_text()
    required = [
        'Grafo viario', 'Strade comunali', 'Strade provinciali', 'Strade regionali',
        'Strade statali', 'Strade private', 'Elementi pavimentati',
        'Elementi non pavimentati',
    ]
    missing = [label for label in required if label not in body]
    if missing:
        raise RuntimeError(f'Massarosa: dati stradali non visibili {missing}')
    if not re.search(r'\d', body):
        raise RuntimeError('Massarosa: nessun valore numerico visibile')
    page.screenshot(path=str(OUT / 'massarosa-grafo-viario-desktop.png'), full_page=True)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        for mode, viewport in [('desktop', {'width': 1440, 'height': 1100}), ('mobile', {'width': 390, 'height': 844})]:
            page = browser.new_page(viewport=viewport)
            errors = []
            page.on('pageerror', lambda exc, errors=errors: errors.append(str(exc)))
            verify_indicator(page, mode)
            if errors:
                raise RuntimeError(f'{mode}: browser errors {errors}')
            page.close()
        town = browser.new_page(viewport={'width': 1440, 'height': 1200})
        verify_town(town)
        town.close()
        browser.close()


if __name__ == '__main__':
    main()
