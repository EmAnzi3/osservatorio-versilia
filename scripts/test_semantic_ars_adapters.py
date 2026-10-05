#!/usr/bin/env python3
"""ARS exact source fields, arithmetic references and refused reconstructions."""
import copy
import json
import math
import tempfile
from pathlib import Path

from semantic_query_engine import QueryEngine, ROOT, operations
import semantic_query_ars_adapters as ars
from test_semantic_query_engine import rejected, request


def regressions(catalog_path):
    engine=QueryEngine(catalog_path,layer='effective')
    # Every reviewed dimension, all seven towns and both official current references.
    for key in ars.KEYS:
        for dimension in ars.dimensions(key):
            result=engine.query(request('compare',key,dimension=dimension))
            assert result['status']=='computed',(key,dimension,result['reasons'])
            assert result['coverage']['usable']==7
            assert all('numerator' not in o and 'denominator' not in o for o in result['observations'])
            for scope in (['versilia'] if key in ars.LEGACY_ONLY else ['tuscany','versilia']):
                gap=engine.query(dict(request('benchmark_gap',key,dimension=dimension,towns=['046018']),benchmark=scope))
                assert gap['status']=='computed',(key,dimension,scope,gap['reasons'])
                assert gap['observations'][0]['dimension']==gap['observations'][1]['dimension']
                assert gap['observations'][1]['provenance'][0]['officialGeography']
            rejected(engine,request('weighted_ratio',key,dimension=dimension),'verified_ratio_adapter_required')
            temporal=key=='lifeExpectancy' or dimension=='total'
            if not temporal:
                rejected(engine,request('series',key,dimension=dimension,towns=['046018']),'ars_historical_dimension_not_available')
                continue
            series=engine.query(request('series',key,dimension=dimension,towns=['046018']))
            assert series['status']=='computed',(key,dimension,series['reasons'])
            assert len(series['observations'])==len(ars.available_periods(engine,key,dimension))
            periods=[o['period'] for o in series['observations']]
            assert periods==sorted(periods,key=ars.order)
            change=engine.query(request('absolute_change',key,dimension=dimension,towns=['046018'],periods=[periods[0],periods[-1]]))
            assert change['status']=='computed'
            assert math.isclose(change['result']['value'],series['observations'][-1]['value']-series['observations'][0]['value'],rel_tol=0,abs_tol=1e-10)
            if '-' in periods[-1]:
                assert 'overlapping_windows_not_independent_years' in series['warnings']
                rejected(engine,request('trend',key,towns=['046018']),'ars_window_trend_not_supported')
            else:
                trend=engine.query(request('trend',key,dimension=dimension,towns=['046018']))
                assert trend['status']=='computed',(key,dimension,trend['reasons'])
    # Values independently transcribed from official ARS records, not generated expectations.
    for key,dimension,expected in [('hypertensionPrevalence','total',245.595),('hypertensionPrevalence','age:65-84|total',681.808),('diabetes','total',67.033),('lifeExpectancy','total',82.2371),('mortalityAll','total',945.211)]:
        result=engine.query(request('compare',key,dimension=dimension))
        value=next(o['value'] for o in result['observations'] if o['geography']=='046018')
        assert math.isclose(value,expected,rel_tol=0,abs_tol=1e-8)
    age=engine.query(request('compare','hypertensionPrevalence',dimension='age:65-84|total'))
    assert 'age_specific_raw_rate_not_standardized' in age['warnings']
    assert all(o['provenance'][1]['ci95Low'] is None for o in age['observations'])
    life=engine.query(request('compare','lifeExpectancy'))
    assert all(o['provenance'][1]['ci95Low'] is None for o in life['observations'])
    rejected(engine,dict(request('benchmark_gap','diabetes',towns=['046018']),benchmark='italy'),'ars_benchmark_scope_not_available')
    rejected(engine,request('compare','mortalityAll',periods=['2022']),'ars_history_period_not_available')
    rejected(engine,request('absolute_change','mortalityAll',towns=['046018'],periods=['2002-2011','2021-2025']),'ars_window_width_mismatch')
    rejected(engine,dict(operation='correlation',selectors=[dict(metric='mortalityAll',towns=['046018']),dict(metric='mortalityCancer',towns=['046018'])],axis='periods',method='spearman',purpose='Explicit test of dependent rolling windows'),'ars_overlapping_window_correlation_not_supported')
    # Altering a carrier/source context must fail; null stays missing, even with raw numeric source.
    with tempfile.TemporaryDirectory(prefix='a6-ars-') as directory:
        root=Path(directory);path=root/'catalog.json'
        for name in (ars.DEMOGRAPHIC,ars.LEGACY,ars.HISTORY,ars.LIFE):
            p=root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/name).read_bytes())
        original=engine.catalog
        def changed(data):
            path.write_text(json.dumps(data));return QueryEngine(path,repository_root=root,layer='effective')
        data=copy.deepcopy(original);data['metrics']['hypertensionPrevalence']['rows'][0]['parts'][0]['measurement']='raw'
        rejected(changed(data),request('compare','hypertensionPrevalence'),'ars_measurement_changed')
        data=copy.deepcopy(original);data['metrics']['diabetes']['rows'][0]['parts'][0]['value']+=1
        rejected(changed(data),request('compare','diabetes'),'ars_catalog_source_reconciliation_failed')
        data=copy.deepcopy(original);data['metrics']['hypertensionPrevalence']['tuscany']['period']='2024'
        rejected(changed(data),dict(request('benchmark_gap','hypertensionPrevalence',towns=['046018']),benchmark='tuscany'),'ars_published_benchmark_period_changed')
        data=copy.deepcopy(original);data['metrics']['diabetes']['rows'][0]['parts'][0]['value']=None
        e=changed(data);rejected(e,request('compare','diabetes'),'partial_coverage_requires_opt_in')
        partial=e.query(dict(request('compare','diabetes'),allowPartial=True))
        assert partial['status']=='computed' and partial['coverage']['usable']==6 and partial['excluded'][0]['observation']['value'] is None
        data=copy.deepcopy(original);data['metrics']['mortalityCancer']['rows'][0]['series']['years'][0]='2001-2010'
        rejected(changed(data),request('series','mortalityCancer',towns=[data['metrics']['mortalityCancer']['rows'][0]['code']]),'ars_history_carrier_periods_mismatch')
        e=changed(original);snap=json.loads((root/ars.DEMOGRAPHIC).read_text());record=next(r for r in snap['indicators']['271']['rows'] if r['sex']=='maschi' and r['strato1']=='totale');snap['indicators']['271']['rows'].append(copy.deepcopy(record));(root/ars.DEMOGRAPHIC).write_text(json.dumps(snap))
        rejected(e,request('compare','diabetes',dimension='sex:men'),'ars_record_not_unique')
    print('A6 ARS: all reviewed dimensions, histories, official references and negative guards PASS')


if __name__=='__main__':regressions(ROOT/'dist/data/site-data.json')
