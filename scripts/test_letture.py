#!/usr/bin/env python3
from __future__ import annotations

import json
import re
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
    require(pilot.get('renderer') == 'demography-story-v3', 'Renderer pilota inatteso')
    require(pilot.get('headline') and pilot.get('standfirst'), 'Headline/standfirst editoriali mancanti')
    require(pilot.get('metrics') == ['population','populationChange','oldAgeIndex','totalResidentialMobility'], 'Metriche della Lettura inattese')
    report_metrics = pilot.get('report', {}).get('metrics')
    require(report_metrics == ['population','populationChange','ageDistribution','oldAgeIndex','foreignResidents','internalResidentialMobility','foreignResidentialMobility','totalResidentialMobility'],
            'Il rapporto demografico non dichiara tutti gli 8 indicatori canonici')

    slugs = [item['slug'] for item in items]
    require(len(slugs) == len(set(slugs)), 'Slug duplicati')
    for item in items:
        require(item.get('question') and item.get('caution'), f'Testi incompleti: {item.get("slug")}')
        for key in item.get('metrics', []):
            require(key in data['metrics'], f'Indicatore inesistente in {item["slug"]}: {key}')
        for key in item.get('report', {}).get('metrics', []):
            require(key in data['metrics'], f'Indicatore rapporto inesistente: {key}')
        forbidden = {'value','values','year','publishedPeriod','source','statusLabel'}
        require(not (forbidden & set(item)), f'Valori/status duplicati nel config: {item["slug"]}')

    require((DIST / 'letture' / 'index.html').exists(), 'Indice Capire la Versilia non generato')
    for slug in slugs:
        path = DIST / 'letture' / slug / 'index.html'
        require(path.exists(), f'Pagina editoriale assente: {slug}')
        text = path.read_text(encoding='utf-8')
        require('noindex,nofollow' in text, f'Pagina indicizzabile prematuramente: {slug}')
        require('class="ov-mark-svg"' in text, f'Brand mark assente: {slug}')
        require('assets/letture.js' in text and 'assets/letture.css' in text and 'assets/letture-v3.css' in text, f'Asset editoriali assenti: {slug}')
        require('assets/pwa.js' in text and 'assets/static.css' in text and 'assets/brand.css' in text, f'Shell canonica incompleta: {slug}')

    report_paths = [DIST / 'rapporti' / 'index.html', DIST / 'rapporti' / 'lettura-una-versilia-che-cambia' / 'index.html']
    for town in data.get('towns', []):
        town_slug = str(town['name']).lower().replace(' ', '-')
        report_paths.append(DIST / 'rapporti' / f'comune-{town_slug}' / 'index.html')
    require(len(report_paths) == 9, f'Attese 9 pagine rapporto, trovate {len(report_paths)}')
    for path in report_paths:
        require(path.exists(), f'Rapporto non generato: {path.relative_to(DIST)}')
        text = path.read_text(encoding='utf-8')
        require('noindex,nofollow' in text, f'Rapporto indicizzabile prematuramente: {path}')
        require('data-report-version="4"' in text, f'Upgrade v4 assente: {path}')
        require('assets/ux-history-core.js' in text, f'Toolkit grafico canonico non caricato: {path}')
        require(text.index('assets/ux-history-core.js') < text.index('assets/rapporti.js'), f'Ordine script errato: {path}')
        require('assets/static.css' in text and 'assets/brand.css' in text and 'assets/pwa.js' in text, f'Asset strutturali rapporto assenti: {path}')

    parts = sorted((ROOT / 'assets' / 'rapporti-parts').glob('*.txt'))
    require(len(parts) == 8, f'Attese 8 parti renderer v4, trovate {len(parts)}')
    source_bundle = ''.join(path.read_text(encoding='utf-8') for path in parts)
    dist_bundle = (DIST / 'assets' / 'rapporti.js').read_text(encoding='utf-8')
    require(source_bundle == dist_bundle, 'Bundle Rapporti in dist non coincide con i sorgenti modulari')
    require('const history = window.OVUXHistory' in dist_bundle, 'Rapporti non dipendono da OVUXHistory')
    require('history.historicalChartMarkup' in dist_bundle and 'history.comparisonBarsMarkup' in dist_bundle and 'history.wireHistorySelection' in dist_bundle,
            'Componenti canonici storico/confronto non riusati')
    require(not re.search(r'function\s+historicalChartMarkup\s*\(', dist_bundle), 'Renderer storico parallelo vietato nei Rapporti')
    require(not re.search(r'function\s+comparisonBarsMarkup\s*\(', dist_bundle), 'Renderer confronto parallelo vietato nei Rapporti')
    require('8 indicatori demografici' in dist_bundle and 'Cinque evidenze che descrivono il cambiamento demografico' in dist_bundle,
            'Rapporto demografico non ha struttura analitica v4')
    require('Sei evidenze per leggere' in dist_bundle and 'Indicatori chiave per tema' in dist_bundle,
            'Rapporto comunale non ha struttura analitica v4')

    css = (ROOT / 'assets' / 'rapporti.css').read_text(encoding='utf-8')
    require('.ux-history-card{' not in css and '.ux-comparison-bars{' not in css,
            'Il CSS Rapporti non deve ridefinire i componenti grafici canonici')
    require('@page{size:A4' in css.replace(' ', ''), 'Layout A4 di stampa assente')

    print('Rapporti v4 OK: 8 indicatori demografici, analisi estesa, 7 rapporti comunali e grafici delegati senza override a OVUXHistory')


if __name__ == '__main__':
    main()
