"""Standard needs: independent OpenCivitas values, native euro components, benchmarks and refusal guards."""
import math

from semantic_query_engine import QueryEngine, ROOT
from semantic_question_suite import pointer
from test_semantic_query_engine import rejected
import semantic_query_standard_needs_adapters as n

SPEND, SERV = n.KEYS
# Spesa storica, spesa standard (euro) e scostamento dei servizi 2023, trascritti dalla sonda OpenCivitas del
# 17 novembre 2026 (data/source-probes/opencivitas-totale-2023.json), indipendenti dallo snapshot.
PROBE = {'046005': (29101909.98, 31185682.46, 15.39143729), '046013': (23349412.38, 10590362.97, 254.897841),
         '046018': (14357945.62, 15508425.97, -6.115557831), '046024': (29952245.92, 24129575.89, 99.50314734),
         '046028': (11551204.9, 9647934.301, 0.231967868), '046030': (3623293.527, 2409708.515, -0.432686629),
         '046033': (67452176.99, 58725210.89, 16.17809167)}
PER_RESIDENT = {'046005': (913.3162811, 978.7121034), '046013': (3445.390642, 1562.691895), '046018': (656.6634175, 709.2808585)}


def query(op='compare', key=SPEND, **selection):
    return dict(operation=op, selectors=[dict(metric=key, **selection)])


def regressions(path):
    e = QueryEngine(path, layer='effective'); catalog = e.catalog
    expected = {SPEND: {c: (s / f - 1) * 100 for c, (s, f, _) in PROBE.items()}, SERV: {c: g for c, (_, _, g) in PROBE.items()}}
    for key in n.KEYS:
        r = e.query(query(key=key)); assert r['status'] == 'computed', r
        for o in r['observations']:
            code = o['geography']
            assert o['period'] == '2023' and o['unit'] == 'percent' and not o['notApplicable'] and not o['dataUnavailable']
            assert math.isclose(o['value'], expected[key][code], abs_tol=1e-9), (key, code, o['value'])
            assert pointer(catalog, o['provenance'][0]['valuePointer']) == o['value']
            native = o['provenance'][1]['nativeComponents']
            if key == SPEND:
                assert (native['historicalSpending'], native['standardSpending']) == PROBE[code][:2]
                if code in PER_RESIDENT:
                    assert (native['historicalSpendingPerResident'], native['standardSpendingPerResident']) == PER_RESIDENT[code]
            else:
                assert native['serviceGapPct'] == PROBE[code][2]
            assert 'numerator' not in o, 'scostamento, non rapporto: niente componenti da sommare'
        assert any(w.startswith('standard_needs_') for w in r['warnings'])
        ranked = e.query(query('rank', key=key)); assert ranked['status'] == 'computed'
        assert [x['geography'] for x in ranked['result']['ranking']] == sorted(expected[key], key=lambda c: (-expected[key][c], c))
        assert ranked['result']['ranking'][0]['geography'] == '046013', 'Forte dei Marmi primo in entrambe le letture'
        for op in ('series', 'absolute_change', 'relative_change', 'percentage_points', 'trend'):
            r = e.query(query(op, key=key, towns=['046033'])); assert r['status'] != 'computed', (op, r)
        rejected(e, query('weighted_ratio', key=key), 'standard_needs_pooling_not_reviewed')
        rejected(e, query('anomaly', key=key), 'standard_needs_peer_anomaly_not_reviewed')
        for period in ('2022', '2024'):
            rejected(e, query(key=key, periods=[period]), 'standard_needs_period_not_frozen')
        for dim in ('normalized', 'numerator', 'count'):
            rejected(e, query(key=key, dimension=dim), 'dimension_adapter_not_implemented')
        rejected(e, dict(query('benchmark_gap', key=key, towns=['046033']), benchmark='versilia'), 'standard_needs_benchmark_scope_not_reviewed')
    rejected(e, dict(operation='correlation', selectors=[dict(metric=SPEND), dict(metric=SERV)], axis='municipalities', method='pearson', purpose='descriptive'),
             'standard_needs_pair_not_jointly_reviewed')
    snap, _ = e.file(catalog['metrics'][SPEND]['meta']['sourceMeta']['snapshot'])
    for scope in ('tuscany', 'italy'):
        s = snap['scopes'][scope]
        for key, bench in ((SPEND, (s['spesaStorica'] / s['spesaStandard'] - 1) * 100), (SERV, s['serviceGapWeightedSum'] / s['spesaStandard'])):
            g = e.query(dict(query('benchmark_gap', key=key, towns=['046018']), benchmark=scope)); assert g['status'] == 'computed', g
            assert math.isclose(g['observations'][1]['value'], bench, abs_tol=1e-9)
            assert math.isclose(g['result']['value'], expected[key]['046018'] - bench, abs_tol=1e-9)
    assert abs((snap['scopes']['italy']['spesaStorica'] / snap['scopes']['italy']['spesaStandard'] - 1) * 100) < 0.5, 'spesa standard riproporzionata: Italia ≈ 0'
    assert 230 <= snap['scopes']['tuscany']['evaluable'] <= 290 and 6000 <= snap['scopes']['italy']['evaluable'] <= 7000
    for key in n.KEYS:
        mutations = [lambda m: m['meta'].update(unit='per1000'), lambda m: m['meta'].update(polarity='positive'), lambda m: m['meta'].update(theme='economia'),
                     lambda m: m['rows'][0].update(value=999), lambda m: m['rows'][0].update(town='Unknown'), lambda m: m['aggregate'].update(value=999),
                     lambda m: m['meta']['benchmark'].update(tuscany=999), lambda m: m['method'].update(formula='Altro'),
                     lambda m: m['meta']['sourceMeta'].update(snapshot='data/source-snapshots/altro.json')]
        for mutation in mutations:
            g = QueryEngine(path, layer='effective'); mutation(g._catalog['metrics'][key]); assert g.query(query(key=key))['status'] == 'not_computable'
        for field in ('sha256', 'path'):
            g = QueryEngine(path, layer='effective'); _, ref = g.file(catalog['metrics'][key]['meta']['sourceMeta']['snapshot']); ref[field] = 'changed'
            assert g.query(query(key=key))['status'] == 'not_computable'
        g = QueryEngine(path, layer='effective'); data, _ = g.file(catalog['metrics'][key]['meta']['sourceMeta']['snapshot']); data['towns']['046033']['spesaStorica'] += 1
        assert g.query(query(key=key))['status'] == 'not_computable'
    print('Standard needs adapters PASS: 14 independent OpenCivitas values, native euro components, 4 benchmark gaps, single vintage and adversarial guards')


if __name__ == '__main__': regressions(ROOT / 'dist/data/site-data.json')
