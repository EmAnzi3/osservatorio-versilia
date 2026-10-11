"""Independent frozen GTFS cells, service-day clock arithmetic and hostile edits."""
import math
from semantic_query_engine import QueryEngine, ROOT
from semantic_question_suite import pointer
from test_semantic_query_engine import rejected
import semantic_query_tpl_adapters as t

# Reviewed municipal snapshot transcription, not materializer/adapter output.
# trips, bus, rail, points, first seconds, last seconds, span, population.
CELLS = {
    '046005': (330, 298, 32, 151, 21000, 107470, 24.02, 31763),
    '046013': (110, 110, 0, 31, 23336, 105844, 22.92, 6550),
    '046018': (106, 86, 20, 131, 21120, 77674, 15.71, 21782),
    '046024': (236, 182, 54, 107, 19380, 106860, 24.30, 22678),
    '046028': (119, 65, 54, 102, 19140, 83520, 17.88, 12284),
    '046030': (26, 26, 0, 80, 22232, 72422, 13.94, 2783),
    '046033': (659, 549, 110, 254, 19800, 108240, 24.57, 60680),
}


def query(key, op='compare', **selectors):
    return dict(operation=op, selectors=[dict(metric=key, **selectors)])


def cells():
    for key, index in [(t.TRIPS, 0), (t.POINTS, 3), (t.SPAN, 6)]:
        for dim in t.dimensions(key):
            yield key, dim, {c: v[index]/v[7]*1000 if dim == 'view:normalized' else v[index] for c,v in CELLS.items()}


def regressions(path):
    e = QueryEngine(path, layer='effective')
    for key, dim, expected in cells():
        result = e.query(query(key, dimension=dim)); assert result['status'] == 'computed', result
        for o in result['observations']:
            code = o['geography']; native = CELLS[code]
            assert math.isclose(o['value'], expected[code], abs_tol=1e-9)
            assert o['period'] == t.DATE and o['unit'] == ('per1000' if dim == 'view:normalized' else 'hours' if key == t.SPAN else 'number')
            assert pointer(e.catalog, o['provenance'][0]['valuePointer']) == o['value']
            snap, _ = e.file(t.PATH); raw = snap['raw'][t.TOWNS[code]]
            assert raw['busTrips'] == native[1] and raw['railTrips'] == native[2]
            assert t.clock_seconds(raw['first']) == native[4] and t.clock_seconds(raw['last']) == native[5]
            assert round((native[5]-native[4])/3600, 2) == native[6]
            assert o['provenance'][1]['replayScope'].endswith('not replayed')
            if dim == 'view:normalized': assert o['provenance'][2]['nativeDenominator'] == native[7]
        rank = e.query(query(key, 'rank', dimension=dim)); assert rank['status'] == 'computed', rank
        assert [x['geography'] for x in rank['result']['ranking']] == sorted(expected, key=lambda c: (-expected[c], c))
        same = e.query(query(key, dimension=dim, periods=[t.DATE])); assert same['status'] == 'computed', same
        for date, reason in [('2026','tpl_explicit_service_date_required'),('2026-08-27','tpl_service_date_not_frozen')]:
            rejected(e, query(key, dimension=dim, periods=[date]), reason)
        for op in ('series','absolute_change','relative_change','percentage_points','trend'):
            rejected(e, query(key, op, dimension=dim, towns=['046018']), 'tpl_single_service_day_no_history')
        rejected(e, query(key, 'weighted_ratio', dimension=dim), 'tpl_pooling_not_reviewed_memberships_and_access_ids')
        rejected(e, query(key, 'anomaly', dimension=dim), 'tpl_peer_anomaly_not_reviewed')
        rejected(e, dict(query(key, 'benchmark_gap', dimension=dim, towns=['046018']), benchmark='tuscany'), 'tpl_geographic_benchmark_not_frozen')
    for key in t.KEYS:
        for pair in ([dict(metric=key),dict(metric='population')],[dict(metric='population'),dict(metric=key)]):
            rejected(e, dict(operation='correlation', selectors=pair, axis='municipalities', method='pearson', purpose='descriptive'), 'tpl_pair_not_jointly_reviewed')
        mutations = [lambda m:m['meta'].update(year='2026'), lambda m:m['meta'].update(unit='percent'), lambda m:m['meta'].update(polarity='positive'), lambda m:m.update(sourceUrl='https://example.com'), lambda m:m['method'].update(formula='different'), lambda m:m['rows'][0].update(value=False), lambda m:m['rows'][0].update(benchmarkValue=1), lambda m:m['rows'][0].update(town='Unknown'), lambda m:m['rows'][0].update(code='046005'), lambda m:m['rows'][0].update(dataUnavailable=True), lambda m:m['rows'][0].update(series=dict(years=[2026],values=[1])), lambda m:m['aggregate'].update(value=999), lambda m:m['aggregate'].update(label='Unique territorial trips'), lambda m:m['meta'].update(benchmark=dict(tuscany=1))]
        if key != t.SPAN: mutations += [lambda m:m['rows'][0]['normalized'].update(value=1), lambda m:m['normalizedAggregate'].update(value=1)]
        for mutation in mutations:
            g = QueryEngine(path, layer='effective'); mutation(g._catalog['metrics'][key]); assert g.query(query(key))['status'] == 'not_computable'
        for field in ('path','sha256'):
            g = QueryEngine(path, layer='effective'); _,ref=g.file(t.PATH); ref[field]='changed'; assert g.query(query(key))['status']=='not_computable'
        g=QueryEngine(path,layer='effective');snap,_=g.file(t.PATH);snap['raw']['Camaiore']['railTrips']=0;assert g.query(query(key))['status']=='not_computable'
    for mutate in [lambda m:m['meta'].update(year='2025'),lambda m:m['rows'][0].update(value=False),lambda m:m['rows'][0].update(code='046005')]:
        g=QueryEngine(path,layer='effective');mutate(g._catalog['metrics']['population']);assert g.query(query(t.TRIPS,dimension='view:normalized'))['status']=='not_computable'
    assert CELLS['046013'][2] == CELLS['046030'][2] == 0
    assert CELLS['046033'][5] > 30*3600 and CELLS['046005'][6] > 24
    print('TPL adapters PASS: 35 fixed public cells, 14 mode counts, 14 service-day seconds, explicit dates, denominators and adversarial guards')


if __name__ == '__main__': regressions(ROOT/'dist/data/site-data.json')
