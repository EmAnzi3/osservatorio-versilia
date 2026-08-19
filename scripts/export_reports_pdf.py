#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import unicodedata
from pathlib import Path

from playwright.sync_api import sync_playwright
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]


def slugify(value: str) -> str:
    value = unicodedata.normalize('NFD', value.lower())
    value = ''.join(ch for ch in value if unicodedata.category(ch) != 'Mn')
    return re.sub(r'[^a-z0-9]+', '-', value).strip('-')


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--base', default='http://127.0.0.1:8123/')
    ap.add_argument('--output', default='dist/rapporti/pdf')
    args = ap.parse_args()
    base = args.base.rstrip('/') + '/'
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)

    data = json.loads((ROOT / 'data' / 'site-data.json').read_text(encoding='utf-8'))
    targets: list[tuple[str, str, int]] = [
        ('rapporti/lettura-una-versilia-che-cambia/', 'lettura-una-versilia-che-cambia.pdf', 7),
    ]
    for town in data.get('towns', []):
        town_slug = slugify(str(town['name']))
        targets.append((f'rapporti/comune-{town_slug}/', f'comune-{town_slug}.pdf', 10))

    launch: dict[str, object] = {'headless': True}
    chromium_path = os.environ.get('CHROMIUM_PATH')
    if chromium_path:
        launch['executable_path'] = chromium_path

    generated: list[tuple[str, int]] = []
    with sync_playwright() as p:
        browser = p.chromium.launch(**launch)
        for route, filename, minimum_pages in targets:
            page = browser.new_page(viewport={'width': 1440, 'height': 1000})
            errors: list[str] = []
            page.on('pageerror', lambda exc, errors=errors: errors.append(str(exc)))
            response = page.goto(base + route, wait_until='networkidle')
            if response is None or not response.ok:
                raise RuntimeError(f'Impossibile caricare {route}: {response.status if response else "nessuna risposta"}')
            if page.locator('.report-mature').count() != 1:
                raise RuntimeError(f'Rapporto maturo non renderizzato: {route}')
            if errors:
                raise RuntimeError(f'Errori browser in {route}: {errors}')
            pdf_path = output / filename
            page.pdf(
                path=str(pdf_path),
                format='A4',
                print_background=True,
                display_header_footer=False,
                prefer_css_page_size=True,
                margin={'top': '0', 'right': '0', 'bottom': '0', 'left': '0'},
            )
            page.close()
            pages = len(PdfReader(str(pdf_path)).pages)
            if pages < minimum_pages:
                raise RuntimeError(f'{filename}: solo {pages} pagine, minimo atteso {minimum_pages}')
            if pdf_path.stat().st_size < 80_000:
                raise RuntimeError(f'{filename}: PDF troppo piccolo ({pdf_path.stat().st_size} byte)')
            generated.append((filename, pages))
        browser.close()

    if len(generated) != 8:
        raise RuntimeError(f'Attesi 8 PDF, generati {len(generated)}')
    print('Rapporti PDF generati senza header/footer del browser: ' + ', '.join(f'{name} ({pages}p)' for name, pages in generated))


if __name__ == '__main__':
    main()
