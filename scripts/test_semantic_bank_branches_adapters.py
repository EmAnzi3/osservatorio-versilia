"""Bank branches: independent counts, native rates, Istat 2022 reconciliation and refusal guards."""
import math

from semantic_query_engine import QueryEngine, ROOT
from semantic_question_suite import pointer
from test_semantic_query_engine import rejected
import semantic_query_bank_branches_adapters as b

KEY = b.KEYS[0]
# Sportelli al 31 dicembre 2018–2025, trascritti dalla sonda Banca d'Italia del 17 novembre 2026
# (data/source-probes/bdi-sportelli-conteggi.json, chiave sede; nessun ID_SEDE condiviso in Versilia).
COUNTS = {'046005': [14, 13, 13, 11, 11, 10, 10, 10], '046013': [7, 7, 7, 7, 7, 7, 7, 7], '046018': [6, 6, 6, 5, 5, 5, 4, 4],
          '046024': [12, 11, 10, 10, 10, 10, 10, 10], '046028': [9, 8, 8, 7, 7, 7, 6, 6], '046030': [1, 1, 1, 1, 1, 1, 1, 0],
          '046033': [31, 27, 26, 24, 24, 22, 22, 22]}
# Istat «Servizi bancari - dati comunali», sportelli 2022 (flusso 117_1035_DF_DCAT_SERVBANC_COM_1).
ISTAT_2022 = {'046005': 11, '046013': 7, '046018': 5, '046024': 10, '046028': 7, '046030': 1, '046033': 24}
POP_2026 = {'046005': 31763, '046013': 6550, '046018': 21782, '046024': 22678, '046028': 12284, '046030': 2783, '046033': 60680}
YEARS = [str(y) for y in range(2018, 2026)]


def query(op='compare', **selection):
    return dict(operation=op, selectors=[dict(metric=KEY, **selection)])


def regressions(path):
    e = QueryEngine(path, layer='effective'); catalog = e.catalog
    assert {c: v[YEARS.index('2022')] for c, v in COUNTS.items()} == ISTAT_2022
    r = e.query(query()); assert r['status'] == 'computed', r
    for o in r['observations']:
        code = o['geography']
        assert o['period'] == '2025' and o['unit'] == 'per1000' and not o['notApplicable'] and not o['dataUnavailable']
        assert o['numerator'] == COUNTS[code][-1] and o['denominator'] == POP_2026[code]
        assert math.isclose(o['value'], COUNTS[code][-1] / POP_2026[code] * 1000, abs_tol=1e-12)
        assert pointer(catalog, o['provenance'][0]['valuePointer']) == o['value']
        snap, _ = e.file(o['provenance'][1]['path'])
        assert pointer(snap, o['provenance'][1]['recordPointer']) == COUNTS[code][-1]
        assert pointer(snap, o['provenance'][1]['denominatorPointer']) == POP_2026[code]
    stazzema = next(o for o in r['observations'] if o['geography'] == '046030')
    assert stazzema['value'] == 0 and stazzema['numerator'] == 0, 'nessuno sportello a Stazzema nel 2025: zero reale, non dato mancante'
    ranked = e.query(query('rank')); assert ranked['status'] == 'computed'
    values = {c: COUNTS[c][-1] / POP_2026[c] for c in COUNTS}
    assert [x['geography'] for x in ranked['result']['ranking']] == sorted(values, key=lambda c: (-values[c], c))
    for code in COUNTS:
        s = e.query(query('series', towns=[code])); assert s['status'] == 'computed', s
        assert [o['period'] for o in s['observations']] == YEARS
        assert [o['numerator'] for o in s['observations']] == COUNTS[code]
    for op in ('absolute_change', 'relative_change', 'percentage_points', 'trend'):
        rejected(e, query(op, towns=['046033']), 'bank_branches_temporal_analysis_not_reviewed')
    rejected(e, query('weighted_ratio'), 'bank_branches_pooling_not_reviewed')
    rejected(e, query('anomaly'), 'bank_branches_peer_anomaly_not_reviewed')
    for period in ('2017', '2026'):
        rejected(e, query(periods=[period]), 'bank_branches_period_not_frozen')
    for dim in ('normalized', 'numerator', 'count'):
        rejected(e, query(dimension=dim), 'dimension_adapter_not_implemented')
    for pair in ([dict(metric=KEY), dict(metric='population')], [dict(metric='population'), dict(metric=KEY)]):
        rejected(e, dict(operation='correlation', selectors=pair, axis='municipalities', method='pearson', purpose='descriptive'), 'bank_branches_pair_not_jointly_reviewed')
    snap, _ = e.file(catalog['metrics'][KEY]['meta']['sourceMeta']['snapshot'])
    for scope in ('tuscany', 'italy'):
        expected = snap['scopes'][scope] / snap['population'][scope] * 1000
        g = e.query(dict(query('benchmark_gap', towns=['046033']), benchmark=scope)); assert g['status'] == 'computed', g
        assert math.isclose(g['observations'][1]['value'], expected, abs_tol=1e-12)
        assert math.isclose(g['result']['value'], 22 / 60680 * 1000 - expected, abs_tol=1e-12)
    assert 19000 < snap['scopes']['italy'] < 20000 and snap['qualityGate']['italy2022'] == 20979
    rejected(e, dict(query('benchmark_gap', towns=['046033']), benchmark='versilia'), 'bank_branches_benchmark_scope_not_reviewed')
    mutations = [lambda m: m['meta'].update(unit='percent'), lambda m: m['meta'].update(polarity='positive'), lambda m: m['meta'].update(theme='comunita'),
                 lambda m: m['rows'][0].update(value=999), lambda m: m['rows'][0]['series']['values'].__setitem__(0, 9.9),
                 lambda m: m['rows'][0].update(town='Unknown'), lambda m: m['aggregate'].update(value=999),
                 lambda m: m['meta']['benchmark'].update(tuscany=999), lambda m: m['method'].update(formula='Altro'),
                 lambda m: m['meta']['sourceMeta'].update(snapshot='data/source-snapshots/altro.json')]
    for mutation in mutations:
        g = QueryEngine(path, layer='effective'); mutation(g._catalog['metrics'][KEY]); assert g.query(query())['status'] == 'not_computable'
    for field in ('sha256', 'path'):
        g = QueryEngine(path, layer='effective'); _, ref = g.file(catalog['metrics'][KEY]['meta']['sourceMeta']['snapshot']); ref[field] = 'changed'
        assert g.query(query())['status'] == 'not_computable'
    g = QueryEngine(path, layer='effective'); data, _ = g.file(catalog['metrics'][KEY]['meta']['sourceMeta']['snapshot']); data['branches']['046033'][-1] = 23
    assert g.query(query())['status'] == 'not_computable'
    g = QueryEngine(path, layer='effective'); g._catalog['metrics']['population']['rows'][0]['series']['values'][-1] += 1
    assert g.query(query())['status'] == 'not_computable'
    print('Bank branches adapters PASS: 56 independent yearly counts, Istat 2022 reconciled 7/7, 7 native rates, 2 benchmark gaps, zero at Stazzema and adversarial guards')


if __name__ == '__main__': regressions(ROOT / 'dist/data/site-data.json')
