"""Fixed published references, 92 zone values, semester and hostile-cache guards."""
import math
from fractions import Fraction
from semantic_query_engine import QueryEngine, ROOT
from semantic_question_suite import pointer
from test_semantic_query_engine import rejected
import semantic_query_omi_adapters as a

# Independently transcribed municipal references; not original OMI range anchors.
SALE = {'046005':Fraction(2200), '046013':Fraction(5520), '046018':Fraction(10750,7),
        '046024':Fraction(2750), '046028':Fraction(6325,4), '046030':Fraction(8985,11), '046033':Fraction(2200)}
RENT = {'046005':Fraction(7), '046013':Fraction(382,25), '046018':Fraction(26,5),
        '046024':Fraction(212,25), '046028':Fraction(81,16), '046030':Fraction(133,55), '046033':Fraction(579,80)}
ZONE_COUNTS = {'046005':6, '046013':5, '046018':7, '046024':5, '046028':4, '046030':11, '046033':8}


def query(dim='total', op='compare', **selection):
    return dict(operation=op, selectors=[dict(metric='omiResidential', dimension=dim, **selection)])


def regressions(path):
    e = QueryEngine(path, layer='effective')
    for dim in a.dimensions('omiResidential'):
        anchors = RENT if dim == 'rentMean' else SALE
        r = e.query(query(dim)); assert r['status'] == 'computed', r
        for o in r['observations']:
            assert math.isclose(o['value'], float(anchors[o['geography']]), rel_tol=0, abs_tol=1e-10)
            assert o['period'] == '2025-S2' and o['unit'] == ('eurm2month' if dim == 'rentMean' else 'eurm2')
            assert not o['nativeComponentsAvailable'] and not o['nativeRecordReplayAvailable']
            evidence = o['evidence'][0]
            assert pointer(e.catalog, evidence['valuePointer']) == o['value']
            parts = [pointer(e.catalog, p) for p in evidence['zoneValuePointers']]
            assert len(parts) == ZONE_COUNTS[o['geography']]
            assert math.isclose(math.fsum(parts)/len(parts), o['value'], rel_tol=0, abs_tol=1e-10)
        assert set(a.NOTES) <= set(r['warnings'])
        r = e.query(query(dim, 'rank')); assert r['status'] == 'computed', r
        assert [o['geography'] for o in r['result']['ranking']] == sorted(anchors, key=lambda c:(-anchors[c], c))
        if dim != 'rentMean':
            ties = [o['rank'] for o in r['result']['ranking'] if o['geography'] in ('046005', '046033')]
            assert len(ties) == 2 and ties[0] == ties[1]
        for token in ['2025-S2', '2° semestre 2025']:
            assert e.query(query(dim, periods=[token]))['status'] == 'computed'
        for token in ['2025', '2026', '2025-S1', '2024-S2']:
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
    mutations = [lambda m:m['meta'].update(year='2026'),lambda m:m['meta'].update(unit='currency'),
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
    assert sum(len(r['zones']) for r in rows)==46
    town_mean=sum(SALE.values())/7
    zone_mean=sum((SALE[c]*ZONE_COUNTS[c] for c in SALE), Fraction(0))/46
    assert town_mean != zone_mean
    assert math.isclose(float(town_mean), e.catalog['metrics']['omiResidential']['aggregate']['saleMean'], abs_tol=1e-10)
    print('OMI PASS: 14 fixed municipal sale/rent anchors, 92 published zone values reconciled, alias/ties, exact semester, distinct units, pointers and hostile-cache/refusal guards; original ranges not replayed')


if __name__=='__main__':regressions(ROOT/'dist/data/site-data.json')
