"""Indice dell'interprete statico delle domande (Chiedi): solo etichette e letture
disponibili nel runtime pubblicato, mai valori. Usato in build e nei test."""
import gzip
import json
from pathlib import Path

PROFILES = {'observe': 'current', 'lookup': 'current', 'compare': 'comparison', 'series': 'history', 'rank': 'ranking',
            'benchmark_gap': 'benchmark', 'weighted_ratio': 'aggregation', 'absolute_change': 'changes',
            'relative_change': 'changes', 'percentage_points': 'changes', 'trend': 'trends', 'anomaly': 'outliers'}


def ask_index(catalog, runtime, view_labels=None):
    """view_labels: {metrica: {dimensione: etichetta}} dalla presentazione della build."""
    view_labels = view_labels or {}
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
                            view=view['dimension'], operations=operations, views=others, featured=summary['metric'] in featured))
    associations = []
    plan = (root.get('associationPlan') or {}).get('plan')
    for step in (plan or {}).get('steps', []):
        left, right = (s['metric'] for s in step['request']['selectors'])
        associations.append(dict(id=step['id'], left=left, right=right))
    return dict(schemaVersion=1, metrics=metrics, towns=root['towns'], associations=associations)
