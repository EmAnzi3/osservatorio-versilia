"""Independent fixed library records, gap replay and adversarial refusal tests."""
import math

from semantic_query_engine import QueryEngine, ROOT
from test_semantic_query_engine import rejected
from semantic_question_suite import pointer
import semantic_query_library_adapters as lib

# Independent transcription of selected municipal indicator rows (not engine output).
FIXED = {
    '046005': (0.25, 13.64, 56.04), '046013': (0.86, 11.57, 61.96),
    '046018': (None, None, None), '046024': (0.22, 2.83, 47.98),
    '046028': (0.24, 2.81, 40.65), '046030': (None, None, None),
    '046033': (0.15, 8.58, 63.75),
}
BENCH = (0.66, 7.5, 33.16)
MASSAROSA_LOANS = [.01] * 11 + [.02, .02, .04, .09, .13, .12, .12, .13, .07, .13, .09, .01, .01, .01, None, None]
MASSAROSA_BORROWERS = [None, 3.48, 2.96, 2.45, 2.16, .47, .37, .46, None, .18, .29, .38, .83, 1.76, 2.27, 6.39, 2.75, 2.76, 1.57, 3.22, 5.76, 1.17, .26, .22, None, None, None]
HISTORY = (MASSAROSA_LOANS, MASSAROSA_BORROWERS, [7, None, None])


def query(key, op='compare', **selection):
    return dict(operation=op, selectors=[dict(metric=key, **selection)])


def regressions(path):
    e = QueryEngine(path, layer='effective'); checked = replay = 0
    for i, key in enumerate(lib.KEYS):
        rejected(e, query(key), 'partial_coverage_requires_opt_in')
        q = dict(query(key), allowPartial=True)
        r = e.query(q); assert r['status'] == 'computed', r
        assert r['coverage']['requested'] == 7 and r['coverage']['usable'] == 5
        for o in r['observations']:
            assert o['value'] == FIXED[o['geography']][i]
            assert o['period'] == '2024' and o['unit'] == lib.UNITS[key]
            assert o['nativeComponentsAvailable'] is False
            assert 'numerator' not in o and 'denominator' not in o
            assert pointer(e.catalog, o['provenance'][0]['valuePointer']) == o['value']
            native, _ = e.file(lib.NATIVE)
            assert pointer(native, o['provenance'][1]['recordPointer']) == o['value']
            if o['value'] is None:
                assert o['dataUnavailable'] and not o['notApplicable'] and o['missingReason']
            checked += 1
        missing = {o['geography']: o['missingReason'] for o in r['observations'] if o['value'] is None}
        assert missing == {'046018': 'regional_indicator_value_not_reported', '046030': 'row_absent_from_regional_monitoring'}
        rank = e.query(dict(query(key, op='rank'), allowPartial=True))
        assert rank['status'] == 'computed' and len(rank['result']['ranking']) == 5, rank
        assert rank['result']['ranking'][0]['geography'] == ('046013' if key == lib.LOANS else '046005' if key == lib.BORROWERS else '046033')
        gap = e.query(dict(query(key, op='benchmark_gap', towns=['046005']), benchmark='tuscany'))
        assert gap['status'] == 'computed', gap
        assert gap['observations'][1]['value'] == BENCH[i]
        assert math.isclose(gap['result']['value'], FIXED['046005'][i] - BENCH[i], abs_tol=1e-9)
        hist = e.query(dict(query(key, op='series', towns=['046018']), allowPartial=True))
        assert [o['value'] for o in hist['observations']] == HISTORY[i], hist
        # Series permits a single observation; this never certifies a change or trend.
        assert hist['status'] == 'computed', hist
        if key == lib.HOURS: assert hist['coverage']['usable'] == 1
        for code, name in lib.TOWNS.items():
            h = e.query(dict(query(key, op='series', towns=[code]), allowPartial=True))
            vals = native['series'][key]['values'][name]
            assert [o['value'] for o in h['observations']] == vals, h
            assert [o['period'] for o in h['observations']] == list(map(str, native['series'][key]['years']))
            for o in h['observations']:
                assert pointer(native, o['provenance'][1]['recordPointer']) == o['value']
                if o['value'] is not None:
                    assert pointer(e.catalog, o['provenance'][0]['valuePointer']) == o['value']
                else: assert o['provenance'][0]['absentPeriod'] == o['period']
            replay += len(vals)
        rejected(e, query(key, op='series', towns=['046018']), 'partial_coverage_requires_opt_in')
        rejected(e, dict(query(key, op='series', towns=['046030']), allowPartial=True), 'insufficient_observations')
        rejected(e, dict(query(key, op='benchmark_gap', towns=['046018']), benchmark='tuscany', allowPartial=True), 'insufficient_observations')
        for op in ('absolute_change', 'relative_change', 'percentage_points', 'trend'):
            rejected(e, query(key, op=op, towns=['046005']), 'library_temporal_continuity_not_reviewed')
        rejected(e, query(key, op='weighted_ratio'), 'library_published_indices_not_poolable')
        rejected(e, query(key, op='anomaly'), 'library_peer_anomaly_not_reviewed')
        rejected(e, query(key, periods=['2025']), 'library_period_not_frozen')
        rejected(e, query(key, dimension='numerator'), 'dimension_adapter_not_implemented')
        rejected(e, dict(query(key, op='benchmark_gap', towns=['046005']), benchmark='italy'), 'library_benchmark_scope_or_period_not_reviewed')
        rejected(e, dict(query(key, op='benchmark_gap', towns=['046005'], periods=['2022']), benchmark='tuscany'), 'library_benchmark_scope_or_period_not_reviewed')
        for selectors in ([{'metric': key}, {'metric': 'population'}], [{'metric': 'population'}, {'metric': key}]):
            rejected(e, dict(operation='correlation', selectors=selectors, axis='municipalities', method='pearson', purpose='descriptive'), 'library_pair_not_jointly_reviewed')
        mutations = [lambda m: m['meta'].update(year='2025'), lambda m: m['meta'].update(unit='number'),
                     lambda m: m.update(sourceUrl='https://example.com'), lambda m: m['rows'][0].update(value=0),
                     lambda m: m['rows'][0].update(value=next(v for v in reversed(HISTORY[i]) if v is not None)),
                     lambda m: m['rows'][0].update(town='Camaiore'), lambda m: m['rows'][0].update(code='046005'),
                     lambda m: m['rows'][1].update(notApplicable=True), lambda m: m['rows'][1].update(dataUnavailable=True),
                     lambda m: m['rows'][1]['series']['values'].__setitem__(0, 999),
                     lambda m: m['aggregate'].update(value=999), lambda m: m['method'].update(coverage='7/7'),
                     lambda m: m['rows'][1].update(ratioComponents={'numerator': 1, 'denominator': 100})]
        for mutation in mutations:
            g = QueryEngine(path, layer='effective'); assert g.query(q)['status'] == 'computed'
            mutation(g._catalog['metrics'][key]); assert g.query(q)['status'] == 'not_computable'
        for field, value in [('year', '2023'), ('italy', 1), ('tuscany', 999), ('unit', 'number'), ('sourceSnapshot', 'other.json')]:
            g = QueryEngine(path, layer='effective'); g._catalog['metrics'][key]['meta']['benchmark'][field] = value
            assert g.query(dict(query(key, op='benchmark_gap', towns=['046005']), benchmark='tuscany'))['status'] == 'not_computable'
    rejected(e, query(lib.HOURS, op='series', towns=['046005'], periods=['2021']), 'library_period_not_frozen')
    for path_ in (lib.NATIVE, lib.BENCHMARK):
        g = QueryEngine(path, layer='effective')
        q = dict(query(lib.LOANS, op='benchmark_gap', towns=['046005']), benchmark='tuscany')
        assert g.query(q)['status'] == 'computed'
        g.file(path_)[0]['unexpectedMutation'] = True; rejected(g, q, 'library_frozen_input_changed')
        g = QueryEngine(path, layer='effective'); g.file(path_)[1]['sha256'] = '0' * 64
        rejected(g, q, 'library_frozen_input_changed')
    print(f'Library adapters PASS: {checked} fixed current cells, three fixed Tuscany benchmarks, 57 fixed Massarosa historical cells; {replay} frozen historical cells replayed including nulls; sparse pointers, current missingness, min observations and adversarial guards')


if __name__ == '__main__': regressions(ROOT / 'dist/data/site-data.json')
