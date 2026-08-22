#!/usr/bin/env python3
from __future__ import annotations

import argparse
from playwright.sync_api import sync_playwright


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def assert_scroll_recovery(page, label: str) -> None:
    runtime = page.evaluate("""() => ({
      hasMap: Boolean(window.__ovPercorsiMap),
      dragging: window.__ovPercorsiMap?.dragging?.enabled?.() ?? null,
      touchZoom: window.__ovPercorsiMap?.touchZoom?.enabled?.() ?? null,
      scrollWheelZoom: window.__ovPercorsiMap?.scrollWheelZoom?.enabled?.() ?? null,
      touchAction: getComputedStyle(document.querySelector('#map')).touchAction,
      listOverscrollY: getComputedStyle(document.querySelector('#routeList')).overscrollBehaviorY
    })""")
    require(runtime['hasMap'], f'Mappa Leaflet non inizializzata in {label}: {runtime}')
    require(runtime['dragging'] is False, f'Leaflet dragging deve essere disattivato su mobile in {label}: {runtime}')
    require(runtime['touchZoom'] is False, f'Leaflet touchZoom deve essere disattivato su mobile in {label}: {runtime}')
    require(runtime['scrollWheelZoom'] is False, f'Leaflet scrollWheelZoom deve essere disattivato su mobile in {label}: {runtime}')
    require('pan-y' in runtime['touchAction'], f'La mappa deve consentire lo scroll verticale della pagina in {label}: {runtime}')
    require(runtime['listOverscrollY'] != 'contain', f'La lista non deve intrappolare lo scroll a fine corsa in {label}: {runtime}')

    back = page.locator('#mapReturnToList')
    require(back.is_visible(), f'Controllo ↑ Percorsi non visibile in {label}')
    require(page.locator('.leaflet-control-zoom-in').is_visible(), f'Zoom mappa non disponibile in {label}')

    # Porta la pagina in fondo, dove nello scenario reale la mappa occupa il viewport.
    page.evaluate("window.scrollTo(0, document.documentElement.scrollHeight)")
    page.wait_for_timeout(100)
    before_wheel = page.evaluate('window.scrollY')
    map_box = page.locator('.mapWrap').bounding_box()
    require(map_box is not None, f'Mappa non misurabile per scroll recovery in {label}')

    # Anche un gesto di scroll iniziato sulla mappa deve poter risalire la pagina.
    page.mouse.move(map_box['x'] + map_box['width'] / 2, map_box['y'] + map_box['height'] / 2)
    page.mouse.wheel(0, -420)
    page.wait_for_timeout(180)
    after_wheel = page.evaluate('window.scrollY')
    require(after_wheel < before_wheel - 40, f'La mappa intrappola lo scroll verticale in {label}: {before_wheel=} {after_wheel=}')

    # Via di uscita esplicita: deve funzionare indipendentemente dal browser/touch stack.
    page.evaluate("window.scrollTo(0, document.documentElement.scrollHeight)")
    page.wait_for_timeout(100)
    before_button = page.evaluate('window.scrollY')
    back.click()
    page.wait_for_timeout(700)
    after_button = page.evaluate('window.scrollY')
    results_top = page.locator('.resultsHead').evaluate('el => el.getBoundingClientRect().top')
    require(after_button < before_button - 100, f'Il controllo ↑ Percorsi non risale la pagina in {label}: {before_button=} {after_button=}')
    require(-2 <= results_top <= 220, f'Il controllo ↑ Percorsi non riporta all’elenco in {label}: results_top={results_top}')


def assert_mobile_list_contract(page, label: str) -> None:
    page.locator('#routeList .card').first.wait_for(state='visible')

    metrics = page.locator('#routeList').evaluate("""el => {
      const rect = el.getBoundingClientRect();
      const cards = [...el.querySelectorAll('.card')];
      const fullyVisible = cards.filter(card => {
        const box = card.getBoundingClientRect();
        return box.top >= rect.top - 1 && box.bottom <= rect.bottom + 1;
      }).length;
      const before = el.scrollTop;
      el.scrollTop = el.scrollHeight;
      const after = el.scrollTop;
      el.scrollTop = before;
      return {
        clientHeight: el.clientHeight,
        scrollHeight: el.scrollHeight,
        fullyVisible,
        scrollable: after > 0,
        rect: {top: rect.top, bottom: rect.bottom, height: rect.height}
      };
    }""")
    map_box = page.locator('.mapWrap').bounding_box()
    require(map_box is not None, f'Mappa non misurabile in {label}')

    require(
        metrics['clientHeight'] >= 340,
        f'Lista Percorsi mobile troppo compressa in {label}: {metrics}',
    )
    require(
        metrics['fullyVisible'] >= 3,
        f'La lista deve mostrare almeno 3 percorsi completi in {label}: {metrics}',
    )
    require(
        metrics['scrollHeight'] > metrics['clientHeight'] and metrics['scrollable'],
        f'Lista Percorsi non realmente scorrevole in {label}: {metrics}',
    )
    require(
        map_box['y'] >= metrics['rect']['bottom'] - 2,
        f'La mappa invade/taglia la lista Percorsi in {label}: list={metrics["rect"]}, map={map_box}',
    )

    widths = page.evaluate("""() => ({
      viewport: window.innerWidth,
      documentWidth: document.documentElement.scrollWidth,
      bodyWidth: document.body.scrollWidth
    })""")
    require(
        max(int(widths['documentWidth']), int(widths['bodyWidth'])) <= int(widths['viewport']) + 2,
        f'Overflow orizzontale in {label}: {widths}',
    )

    assert_scroll_recovery(page, label)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--base', default='http://127.0.0.1:8123/')
    args = parser.parse_args()
    base = args.base.rstrip('/') + '/'

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={'width': 390, 'height': 844}, has_touch=True)

        page.goto(base + 'percorsi/', wait_until='networkidle')
        assert_mobile_list_contract(page, '390x844')

        # Il contratto deve reggere anche su un Android stretto.
        page.set_viewport_size({'width': 360, 'height': 800})
        page.goto(base + 'percorsi/', wait_until='networkidle')
        assert_mobile_list_contract(page, '360x800')

        browser.close()

    print('Contratto Percorsi mobile: lista utilizzabile, scroll di pagina recuperabile dalla mappa e controllo ↑ Percorsi sempre disponibile.')


if __name__ == '__main__':
    main()
