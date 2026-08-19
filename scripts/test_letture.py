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
    require(config.get('schemaVersion') == 3, 'Schema Capire la Versilia v3 non aggiornato')
    require(config.get('label') == 'Capire la Versilia', 'Label editoriale inattesa')
    require(len(items) == 7, f'Attese 7 ipotesi editoriali, trovate {len(items)}')
    pilots = [item for item in items if item.get('status') == 'pilot']
    planned = [item for item in items if item.get('status') == 'planned']
    require(len(pilots) == 1 and len(planned) == 6, 'Attesi 1 pilota e 6 temi pianificati')
    pilot = pilots[0]
    require(pilot.get('slug') == 'una-versilia-che-cambia', 'Pilota inatteso')
    require(pilot.get('renderer') == 'demography-story-v3', 'Renderer pilota v3 inatteso')
    require(pilot.get('headline') and pilot.get('standfirst'), 'Headline/standfirst editoriali mancanti')
    require(pilot.get('metrics') == ['population','populationChange','oldAgeIndex','totalResidentialMobility'], 'Metriche pilota inattese')
    require(pilot.get('report', {}).get('enabled') is True, 'Rapporto pilota non abilitato')

    slugs = [item['slug'] for item in items]
    require(len(slugs) == len(set(slugs)), 'Slug duplicati')
    for item in items:
        require(item.get('question') and item.get('caution'), f'Testi incompleti: {item.get("slug")}')
        for key in item.get('metrics', []):
            require(key in data['metrics'], f'Indicatore inesistente in {item["slug"]}: {key}')
        forbidden = {'value','values','year','publishedPeriod','source','statusLabel'}
        require(not (forbidden & set(item)), f'Valori/status duplicati nel config: {item["slug"]}')

    require((DIST / 'letture' / 'index.html').exists(), 'Indice Capire la Versilia non generato')
    for slug in slugs:
        path = DIST / 'letture' / slug / 'index.html'
        require(path.exists(), f'Pagina editoriale assente: {slug}')
        text = path.read_text(encoding='utf-8')
        require('noindex,nofollow' in text, f'Pagina indicizzabile prematuramente: {slug}')
        require('class="ov-mark-svg"' in text, f'Brand mark assente: {slug}')
        require('assets/letture.js' in text and 'assets/letture.css' in text and 'assets/letture-v3.css' in text,
                f'Asset editoriali v3 assenti: {slug}')
        require('assets/pwa.js' in text and 'assets/pwa.css' in text, f'PWA shell assente: {slug}')
        require('assets/static.css' in text and 'assets/brand.css' in text, f'CSS strutturali del sito assenti: {slug}')

    report_paths = [
        DIST / 'rapporti' / 'index.html',
        DIST / 'rapporti' / 'lettura-una-versilia-che-cambia' / 'index.html',
    ]
    for town in data.get('towns', []):
        slug = str(town['name']).lower().replace(' ', '-')
        if town['name'] == 'Forte dei Marmi':
            slug = 'forte-dei-marmi'
        report_paths.append(DIST / 'rapporti' / f'comune-{slug}' / 'index.html')
    require(len(report_paths) == 9, f'Attese 9 pagine rapporto, trovate {len(report_paths)}')
    for path in report_paths:
        require(path.exists(), f'Rapporto non generato: {path.relative_to(DIST)}')
        text = path.read_text(encoding='utf-8')
        require('noindex,nofollow' in text, f'Rapporto indicizzabile prematuramente: {path}')
        require('class="ov-mark-svg"' in text, f'Shell canonica assente nel rapporto: {path}')
        require('assets/rapporti.js' in text and 'assets/rapporti.css' in text, f'Asset rapporto assenti: {path}')
        require('assets/static.css' in text and 'assets/brand.css' in text and 'assets/pwa.js' in text,
                f'Asset strutturali rapporto assenti: {path}')

    js = (ROOT / 'assets' / 'letture.js').read_text(encoding='utf-8')
    require('data/site-data.json' in js and 'data/source-registry.json' in js and 'data/source-monitor-state.json' in js,
            'Renderer non usa le autorità canoniche')
    require('demography-story-v3' in js and 'data-story-chapter' in js, 'Grammatica narrativa pilota v3 assente')
    require('.trend-chart' in js and '.chart-tooltip' in js, 'Grafico storico canonico/tooltips non riusati')
    require('story-axis-title' in js and 'story-axis-label' in js, 'Assi espliciti assenti dai grafici editoriali')
    require('story-scatter-chart' in js and 'Residenti e trasferimenti: due dimensioni diverse' in js,
            'Scatter residenti/trasferimenti assente')
    require('data-aging-town' in js, 'Selettore serie storica indice di vecchiaia assente')
    require("unit === 'percent'" in js and "unit === 'per1000'" in js, 'Unità percent/per1000 non gestite')
    require("sort((a,b)=>townName(a).localeCompare(townName(b),'it'))" in js, 'Comuni non ordinati alfabeticamente')
    require('bar-rank' not in js and '.sort((a,b)=>b.value' not in js, 'Logica di ranking rilevata nel renderer Letture')
    require('/percorsi/' not in json.dumps(config, ensure_ascii=False), 'Collisione con /percorsi/')

    report_js = (ROOT / 'assets' / 'rapporti.js').read_text(encoding='utf-8')
    require('data/site-data.json' in report_js and 'data/source-monitor-state.json' in report_js,
            'Rapporti non dipendono dai dati/stato canonici')
    require('window.print()' in report_js and 'report-table' in report_js, 'Export/struttura tabellare rapporti assenti')
    require('featuredKeys(theme)' in report_js, 'Rapporti comunali non riusano gli indicatori featured canonici')

    print('Capire la Versilia v3 OK: grafici canonici con assi/tooltip, scatter coerente, analisi estesa, 1 rapporto Lettura + 7 rapporti comunali')


if __name__ == '__main__':
    main()
