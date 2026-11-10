"""Fixed 2026-S1 references, 76 zone values, semester and hostile-cache guards."""
import math
from fractions import Fraction
from semantic_query_engine import QueryEngine, ROOT
from semantic_question_suite import pointer
from test_semantic_query_engine import rejected
import semantic_query_omi_adapters as a

# Municipal references transcribed from the 2026-S1 snapshot zone midpoints (civil dwellings, normal state).
SALE = {'046005':Fraction(13175,6), '046013':Fraction(5580), '046018':Fraction(10775,7),
        '046024':Fraction(2815), '046028':Fraction(6075,4), '046030':Fraction(2510,3), '046033':Fraction(18125,8)}
RENT = {'046005':Fraction(279,40), '046013':Fraction(1531,100), '046018':Fraction(363,70),
        '046024':Fraction(214,25), '046028':Fraction(24,5), '046030':Fraction(46,15), '046033':Fraction(149,20)}
ZONE_COUNTS = {'046005':6, '046013':5, '046018':7, '046024':5, '046028':4, '046030':3, '046033':8}
ZONES = sum(ZONE_COUNTS.values())


def query(dim='total', op='compare', **selection):
    return dict(operation=op, selectors=[dict(metric='omiResidential', dimension=dim, **selection)])


def regressions(path):
    e = QueryEngine(path, layer='effective')
    for dim in a.dimensions('omiResidential'):
        anchors = RENT if dim == 'rentMean' else SALE
        r = e.query(query(dim)); assert r['status'] == 'computed', r
        for o in r['observations']:
            assert math.isclose(o['value'], float(anchors[o['geography']]), rel_tol=0, abs_tol=1e-10)
            assert o['period'] == '2026-S1' and o['unit'] == ('eurm2month' if dim == 'rentMean' else 'eurm2')
            assert not o['nativeComponentsAvailable'] and not o['nativeRecordReplayAvailable']
            evidence = o['evidence'][0]
            assert pointer(e.catalog, evidence['valuePointer']) == o['value']
            parts = [pointer(e.catalog, p) for p in evidence['zoneValuePointers']]
            assert len(parts) == ZONE_COUNTS[o['geography']]
            assert math.isclose(math.fsum(parts)/len(parts), o['value'], rel_tol=0, abs_tol=1e-10)
        assert set(a.NOTES) <= set(r['warnings'])
        r = e.query(query(dim, 'rank')); assert r['status'] == 'computed', r
        assert [o['geography'] for o in r['result']['ranking']] == sorted(anchors, key=lambda c:(-anchors[c], c))
        assert sorted(o['rank'] for o in r['result']['ranking']) == list(range(1, 8))
        for token in ['2026-S1', '1° semestre 2026']:
            assert e.query(query(dim, periods=[token]))['status'] == 'computed'
        for token in ['2025', '2026', '2025-S1', '2025-S2', '2° semestre 2025', '2026-S2', '2024-S2']:
            rejected(e, query(dim, periods=[token]), 'omi_exact_semester_required')
        for op in ['series', 'absolute_change', 'relative_change', 'percentage_points', 'trend']:
            rejected(e, query(dim, op), 'omi_single_semester_no_comparable_history_frozen')
        for op,reason in [('weighted_ratio','omi_transaction_or_dwelling_weights_not_frozen_no_pooling'),
                          ('benchmark_gap','omi_geographic_benchmark_not_reviewed'), ('anomaly','omi_peer_anomaly_not_reviewed')]:
            rejected(e, dict(query(dim, op), **({'benchmark':'tuscany'} if op == 'benchmark_gap' else {})), reason)
        for pair in [[dict(metric='omiResidential',dimension=dim),dict(metric='income')],
                     [dict(metric='income'),dict(metric='omiResidential',dimension=dim)]]:
            rejected(e,dict(operation='correlation', selectors=pair, axis='municipalities', method='pearson', purpose='descriptive'), 'omi_pair_not_jointly_reviewed')
    for dim in ['zone:B1:sale', 'normalized', 'transactions', 'rentAnnual', 'min', 'max']:
        rejected(e, query(dim), 'dimension_adapter_not_implemented')
    mutations = [lambda m:m['meta'].update(year='2026'),lambda m:m['meta'].update(year='2° semestre 2025'),lambda m:m['meta'].update(unit='currency'),
                 lambda m:m.update(sourceUrl='other'),lambda m:m['method'].update(formula='transaction weighted'),
                 lambda m:m['rows'][0].update(value=99),lambda m:m['rows'][0].update(saleMean=99),
                 lambda m:m['rows'][0].update(rentMean=99),lambda m:m['rows'][0].update(code='046005'),
                 lambda m:m['rows'][0].update(dataUnavailable=True),lambda m:m['aggregate'].update(rentMean=99),
                 lambda m:m['rows'][0]['zones'][0].update(sale=99),lambda m:m['rows'][0]['zones'][0].update(rent=99),
                 lambda m:m['rows'][0]['zones'][0].update(code='other'),lambda m:m['rows'][0]['zones'].pop(),
                 lambda m:m['rows'][0].update(series={'years':[2024], 'values':[1]})]
    for mutation in mutations:
        g = QueryEngine(path,layer='effective'); assert g.query(query())['status'] == 'computed'
        mutation(g._catalog['metrics']['omiResidential'])
        for dim in a.dimensions('omiResidential'):
            rejected(g, query(dim), 'omi_public_definition_or_values_changed')
    g = QueryEngine(path,layer='effective');g._catalog['towns'][0]['name']='Unknown'
    rejected(g,query(), 'omi_municipal_identity_changed')
    # Equal-town means differ from equal-zone means: neither is a transaction mean.
    rows=e.catalog['metrics']['omiResidential']['rows']
    assert sum(len(r['zones']) for r in rows)==ZONES==38
    town_mean=sum(SALE.values())/7
    zone_mean=sum((SALE[c]*ZONE_COUNTS[c] for c in SALE), Fraction(0))/ZONES
    assert town_mean != zone_mean
    assert math.isclose(float(town_mean), e.catalog['metrics']['omiResidential']['aggregate']['saleMean'], abs_tol=1e-10)
    print('OMI PASS: 14 fixed municipal sale/rent anchors (2026-S1), 76 zone values reconciled, alias, distinct ranks, exact semester (2025-S2 refused), distinct units, pointers and hostile-cache/refusal guards')


if __name__=='__main__':regressions(ROOT/'dist/data/site-data.json')
