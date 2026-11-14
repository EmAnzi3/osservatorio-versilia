"""Indice dell'interprete statico delle domande (Chiedi): solo etichette e letture
disponibili nel runtime pubblicato, mai valori. Usato in build e nei test."""
import gzip
import json
import re
import unicodedata
from pathlib import Path

PROFILES = {'observe': 'current', 'lookup': 'current', 'compare': 'comparison', 'series': 'history', 'rank': 'ranking',
            'benchmark_gap': 'benchmark', 'weighted_ratio': 'aggregation', 'absolute_change': 'changes',
            'relative_change': 'changes', 'percentage_points': 'changes', 'trend': 'trends', 'anomaly': 'outliers'}


def indicator_slug(label):
    """Stesso slug delle pagine canoniche `indicatori/<slug>/` di build_static."""
    value = unicodedata.normalize('NFD', str(label or '').lower())
    value = ''.join(ch for ch in value if unicodedata.category(ch) != 'Mn')
    return re.sub(r'[^a-z0-9]+', '-', value).strip('-')


def indicator_pages(catalog, site):
    """{metrica: percorso relativo a /chiedi/} per le sole pagine indicatore presenti nel sito."""
    data = json.loads(Path(catalog).read_text(encoding='utf-8'))
    pages = {}
    for key, metric in data['metrics'].items():
        slug = indicator_slug(metric.get('meta', {}).get('label'))
        if slug and (Path(site)/'indicatori'/slug/'index.html').is_file():
            pages[key] = f'../indicatori/{slug}/'
    return pages


def ask_index(catalog, runtime, view_labels=None, pages=None):
    """view_labels: {metrica: {dimensione: etichetta}} dalla presentazione della build;
    pages: {metrica: pagina dell'Osservatorio con fonte e metodo}."""
    view_labels = view_labels or {}
    pages = pages or {}
    catalog = json.loads(Path(catalog).read_text(encoding='utf-8'))
    runtime = Path(runtime)
    root = json.loads((runtime/'release.json').read_text(encoding='utf-8'))
    themes = {key: theme.get('label', key) for key, theme in catalog.get('themes', {}).items()}
    featured = {key for theme in catalog.get('themes', {}).values() for key in theme.get('featured', []) or []}
    sections = {}
    for theme in catalog.get('themes', {}).values():
        for section in theme.get('sections', []) or []:
            for key in section.get('metrics', []):
                sections.setdefault(key, section.get('label', ''))
    metrics = []
    for summary in root['metrics']:
        detail = json.loads(gzip.decompress((runtime/summary['detail']['path']).read_bytes()))
        views = detail['views']
        view = next((v for v in views if v['dimension'] == 'total'), views[0] if views else None)
        if view is None:
            continue
        def available(v):
            scopes = detail['declaration'].get('benchmarkScopesByDimension', {}).get(v['dimension']) or []
            return [op for op in v.get('declaredOperations', [])
                    if PROFILES.get(op) in v['shards']
                    and (op != 'benchmark_gap' or any(s in ('tuscany', 'italy') for s in scopes))
                    and (op != 'anomaly' or root.get('outlierSelection'))]
        operations = available(view)
        labels = view_labels.get(summary['metric'], {})
        # Dettagli con nome leggibile (età, sesso, voci…): servono a «giovani», «donne»…
        others = [dict(dimension=v['dimension'], label=labels[v['dimension']], operations=available(v))
                  for v in views[:40] if v is not view and labels.get(v['dimension']) and available(v)]
        meta = catalog['metrics'].get(summary['metric'], {}).get('meta', {})
        metrics.append(dict(key=summary['metric'], label=summary['label'], short=meta.get('shortLabel') or '',
                            terms=meta.get('searchTerms') or [], description=(meta.get('description') or '')[:200],
                            themeLabel=themes.get(summary['theme'], summary['theme']), section=sections.get(summary['metric'], ''),
                            view=view['dimension'], operations=operations, views=others, featured=summary['metric'] in featured,
                            page=pages.get(summary['metric'])))
    associations = []
    plan = (root.get('associationPlan') or {}).get('plan')
    for step in (plan or {}).get('steps', []):
        left, right = (s['metric'] for s in step['request']['selectors'])
        associations.append(dict(id=step['id'], left=left, right=right))
    return dict(schemaVersion=1, metrics=metrics, towns=root['towns'], associations=associations)
