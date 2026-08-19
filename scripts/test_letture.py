#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / 'dist'


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    config = json.loads((ROOT / 'data' / 'letture.json').read_text(encoding='utf-8'))
    data = json.loads((ROOT / 'data' / 'site-data.json').read_text(encoding='utf-8'))
    items = config.get('items', [])
    require(len(items) == 7, f'Attese 7 Letture, trovate {len(items)}')
    slugs = [item['slug'] for item in items]
    require(len(slugs) == len(set(slugs)), 'Slug Letture duplicati')
    for item in items:
        require(item.get('question') and item.get('answer') and item.get('caution'), f'Testi incompleti: {item.get("slug")}')
        for key in item.get('metrics', []):
            require(key in data['metrics'], f'Indicatore inesistente in {item["slug"]}: {key}')
    require((DIST / 'letture' / 'index.html').exists(), 'Indice Letture non generato')
    for slug in slugs:
        path = DIST / 'letture' / slug / 'index.html'
        require(path.exists(), f'Pagina Lettura assente: {slug}')
        text = path.read_text(encoding='utf-8')
        require('noindex,nofollow' in text, f'Lettura indicizzabile prematuramente: {slug}')
        require('class="ov-mark-svg"' in text, f'Brand mark assente: {slug}')
        require('assets/letture.js' in text and 'assets/letture.css' in text, f'Asset Letture assenti: {slug}')
        require('assets/pwa.js' in text and 'assets/pwa.css' in text, f'PWA shell assente: {slug}')
    js = (ROOT / 'assets' / 'letture.js').read_text(encoding='utf-8')
    require('data/site-data.json' in js, 'Letture non leggono site-data')
    require('data/source-registry.json' in js, 'Letture non leggono source-registry')
    require('data/source-monitor-state.json' in js, 'Letture non leggono source-monitor-state')
    require('.sort((a,b)=>townName(a).localeCompare(townName(b)' in js, 'Valori comunali non ordinati alfabeticamente')
    require('bar-rank' not in js and 'classifica' not in js.lower(), 'Renderer Letture contiene logica di ranking')
    require('/percorsi/' not in json.dumps(config, ensure_ascii=False), 'Letture collidono con /percorsi/')
    print('Letture OK: 7 percorsi, soli indicatori canonici, noindex, no ranking, nessuna collisione con Percorsi')


if __name__ == '__main__':
    main()
