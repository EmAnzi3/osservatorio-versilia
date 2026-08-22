#!/usr/bin/env python3
from __future__ import annotations

import argparse
from playwright.sync_api import sync_playwright


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--base', default='http://127.0.0.1:8123/')
    args = parser.parse_args()
    base = args.base.rstrip('/') + '/'

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={'width': 390, 'height': 844})

        page.goto(base + 'percorsi/', wait_until='networkidle')
        assert_mobile_list_contract(page, '390x844')

        # Il contratto deve reggere anche su un Android stretto: la lista resta
        # una superficie autonoma e non può tornare a una sola riga sopra la mappa.
        page.set_viewport_size({'width': 360, 'height': 800})
        page.goto(base + 'percorsi/', wait_until='networkidle')
        assert_mobile_list_contract(page, '360x800')

        browser.close()

    print('Contratto Percorsi mobile: lista >=340px, almeno 3 card visibili, scroll reale e nessuna sovrapposizione con la mappa.')


if __name__ == '__main__':
    main()
