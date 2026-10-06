"""Independent arithmetic, complete admitted dimensions/periods, and false-proof guards."""
import copy
import json
import math
import shutil
import tempfile
from pathlib import Path

from semantic_query_engine import QueryEngine, ROOT, dimensions
from test_semantic_query_engine import request, rejected
import semantic_query_distinct_finance_adapters as d


def query(operation, key, dimension='total', **selection):
    return request(operation, key, dimension=dimension, **selection)


def regressions(path):
    e = QueryEngine(path, layer='effective')
    for key in d.KEYS:
        for dimension in dimensions(key):
            r = e.query(query('compare', key, dimension))
            assert r['status'] == 'computed' and r['coverage']['usable'] == 7, (key, dimension, r)
            for code in sorted(e.codes):
                if key == d.WORKS:
                    rejected(e, query('series', key, dimension, towns=[code]), 'distinct_finance_project_history_not_frozen')
                    continue
                r = e.query(query('series', key, dimension, towns=[code]))
                assert r['status'] == 'computed', (key, dimension, code, r)
                assert len(r['observations']) == (7 if key == d.DEBT else 2 if key == d.SECURITY else 1)
                for o in r['observations']:
                    c = e.query(query('compare', key, dimension, towns=[code,next(c for c in sorted(e.codes) if c!=code)], periods=[o['period']]))
                    assert c['status'] == 'computed' and next(x for x in c['observations'] if x['geography']==code)['value'] == o['value'], c
            r = e.query(query('weighted_ratio', key, dimension))
            if d.weighted(key, dimension):
                assert r['status'] == 'computed', r
                observations = r['observations']
                expected = sum(o['numerator'] for o in observations) / sum(o['denominator'] for o in observations) * observations[0]['scale']
                assert math.isclose(r['result']['value'], expected, abs_tol=1e-7)
            else: assert 'verified_ratio_adapter_required' in r['reasons'], r
            rejected(e, dict(query('benchmark_gap', key, dimension, towns=['046018']), benchmark='tuscany'), 'distinct_finance_benchmark_components_or_perimeter_not_frozen')
    # Independent source values, including official scale corrections and verified zero.
    cases = [(d.DEBT, 'part:debtPerResident', 10150552.2 / 21806),
             (d.DEBT, 'part:interestShare', 1382657.67 / 31550784.64 * 100),
             (d.DEBT, 'part:debtSustainability', 7.26),
             (d.FISCAL, 'total', 687088.75 / 21806),
             (d.FISCAL, 'part:recoveryTotal', 687088.75),
             (d.FISCAL, 'part:daitContribution', 0),
             (d.SECURITY, 'total', 55.38237686875173),
             (d.WORKS, 'total', 1409.3119089156185)]
    for key, dimension, value in cases:
        r = e.query(query('compare', key, dimension, towns=['046018','046033']))
        assert math.isclose(r['observations'][0]['value'], value, rel_tol=0, abs_tol=1e-7), r
    r = e.query(query('compare', d.DEBT, 'part:debtSustainability', towns=['046005'], periods=['2023']))
    assert r['observations'][0]['value'] == 9.64 and r['observations'][0]['evidence'][1]['annualProvenance'] == 'pdi_scale_normalized'
    r = e.query(query('compare', d.DEBT, 'part:debtSustainability', towns=['046013'], periods=['2025']))
    assert r['observations'][0]['value'] == 0 and r['coverage']['usable'] == 1
    r = e.query(query('compare', d.FISCAL))
    assert all('denominatorReferenceDate' not in o and o['denominator'] != 0 for o in r['observations'])
    assert next(o for o in r['observations'] if o['geography'] == '046018')['denominator'] == 21806
    r = e.query(query('compare', d.FISCAL, 'part:daitContribution'))
    assert all(o['numeratorPeriod'] == '2024' and o['allocationPeriod'] == '2025' and 'denominator' not in o for o in r['observations'])
    for operation in ('absolute_change','relative_change','trend','percentage_points'):
        rejected(e, query(operation, d.DEBT, 'part:interestShare', towns=['046018'], periods=['2019','2025']), 'distinct_finance_massarosa_osl_temporal_perimeter_not_attested')
    rejected(e, query('trend', d.FISCAL, towns=['046005']), 'distinct_finance_only_one_fiscal_period')
    pair = dict(operation='correlation', selectors=[{'metric':d.FISCAL,'dimension':'part:daitContribution'}, {'metric':d.FISCAL,'dimension':'part:recoveryTotal'}], method='spearman', axis='municipalities', purpose='Separate grant and receipt references')
    rejected(e, pair, 'distinct_finance_dait_allocation_and_underlying_receipt_periods_not_aligned')
    with tempfile.TemporaryDirectory(prefix='a6-distinct-negative-') as directory:
        root = Path(directory)
        for p in (d.DEBT_SNAPSHOT, d.FISCAL_SNAPSHOT, d.BILANCI, d.CANONICAL):
            dest = root / p; dest.parent.mkdir(parents=True, exist_ok=True); shutil.copyfile(ROOT / p, dest)
        original = e.catalog; catalog = root / 'catalog.json'
        def changed(data):
            catalog.write_text(json.dumps(data)); return QueryEngine(catalog, repository_root=root, layer='effective')
        for key in d.KEYS:
            data = copy.deepcopy(original); data['metrics'][key]['rows'][0]['value'] += 1
            rejected(changed(data), query('compare', key), 'distinct_finance_catalog_source_mismatch')
            data = copy.deepcopy(original); data['metrics'][key]['rows'][0]['value'] = None
            rejected(changed(data), query('compare', key), 'partial_coverage_requires_opt_in')
            r = changed(data).query(dict(query('compare', key), allowPartial=True))
            assert r['status'] == 'computed' and r['coverage']['usable'] == 6, r
        data = copy.deepcopy(original); data['metrics'][d.DEBT]['rows'][0]['parts'].append(copy.deepcopy(data['metrics'][d.DEBT]['rows'][0]['parts'][0]))
        rejected(changed(data), query('compare', d.DEBT), 'distinct_finance_missing_or_duplicate_part')
        data = copy.deepcopy(original); data['metrics'][d.DEBT]['rows'][0]['parts'][2]['provenanceSeries'] = []
        rejected(changed(data), query('compare', d.DEBT, 'part:debtSustainability'), 'distinct_finance_pdi_provenance_changed')
        data = copy.deepcopy(original); data['metrics'][d.FISCAL]['rows'][0]['populationIstat'] = 21782
        rejected(changed(data), query('compare', d.FISCAL), 'distinct_finance_fiscal_components_changed')
        data = copy.deepcopy(original); data['metrics'][d.FISCAL]['rows'][0]['parts'][1]['value'] += 1
        rejected(changed(data), query('compare', d.FISCAL, 'part:recoveryTotal'), 'distinct_finance_catalog_source_mismatch')
        data = copy.deepcopy(original); data['metrics'][d.FISCAL]['rows'][0]['series']['values'][0] += 1
        rejected(changed(data), query('series', d.FISCAL, towns=['046018']), 'distinct_finance_catalog_source_mismatch')
        snap = root / d.DEBT_SNAPSHOT; raw = json.loads(snap.read_text()); saved = copy.deepcopy(raw)
        raw['towns']['Camaiore']['debt_sustainability_pdi_raw'][4] += 100; snap.write_text(json.dumps(raw))
        rejected(changed(original), query('compare', d.DEBT, 'part:debtSustainability', towns=['046005'], periods=['2023']), 'distinct_finance_catalog_source_mismatch')
        snap.write_text(json.dumps(saved)); raw = copy.deepcopy(saved); raw['towns']['Forte dei Marmi']['title4_repayment'][-1] = 100; snap.write_text(json.dumps(raw))
        rejected(changed(original), query('compare', d.DEBT, 'part:debtSustainability', towns=['046013']), 'distinct_finance_catalog_source_mismatch')
    print('A6 distinct finance: four carriers, all admitted dimensions × seven towns × periods, explicit dates/perimeters and negative cases PASS')


if __name__ == '__main__': regressions(ROOT / 'dist/data/site-data.json')
