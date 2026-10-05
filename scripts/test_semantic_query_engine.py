#!/usr/bin/env python3
"""Independent numeric references, guarded queries, and actual catalog adapters."""
import copy
import json
import math
import tempfile
from pathlib import Path

from semantic_query_engine import QueryEngine, ROOT, SNAPSHOT, calculate, coefficient, ranks


def request(operation, metric='population', **selection):
    return {'operation':operation,'selectors':[dict(metric=metric,**selection)]}


def rejected(engine, query, reason):
    report = engine.query(query)
    assert report['status']=='not_computable' and any(reason in r for r in report['reasons']),report
    assert report['result'] is None
    return report


def regressions():
    assert ranks([1,2,2,4])==[1,2.5,2.5,4]
    assert math.isclose(coefficient([1,2,3],[1,4,9],'pearson'),4*math.sqrt(3)/7,rel_tol=1e-12)
    assert math.isclose(coefficient([1,2,2,4],[4,1,1,3],'spearman'),-1/3,abs_tol=1e-12)
    assert coefficient([1,1,1],[1,2,3],'pearson') is None
    assert math.isclose(coefficient([1e200,2e200,3e200],[3e200,2e200,1e200],'pearson'),-1,abs_tol=1e-12)
    rows=[dict(value=v,geography=str(i),period=p,unit='number') for i,(v,p) in enumerate([(1,'2019'),(3,'2020'),(9,'2023')])]
    assert math.isclose(calculate('trend',rows,{'timeAxis':[2019,2020,2023]})['slope'],2,abs_tol=1e-12)
    rank=calculate('rank',[dict(value=v,geography=str(i)) for i,v in enumerate([9,5,5,1])],{})
    assert [r['rank'] for r in rank['ranking']]==[1,2,2,4]
    assert calculate('relative_change',[{'value':50,'period':'2020','unit':'number'},{'value':55,'period':'2021','unit':'number'}],{})['value']==10

    engine=QueryEngine(ROOT/'data/site-data.json')
    q=request('absolute_change',towns=['046018'],periods=['2019','2026'])
    report=engine.query(q)
    assert report['status']=='computed' and report['result']['value']==86,report
    assert report==engine.query(q) # no runtime timestamp/randomness in results
    q['selectors'][0]['periods'][0]='2020'
    assert report['query']['selectors'][0]['periods'][0]=='2019'
    assert all(len(o['provenance'][0]['sha256'])==64 for o in report['observations'])
    assert report['observations'][0]['source'].endswith('POSAS_2019_it_046_Lucca.zip')
    assert report['observations'][0]['provenance'][0]['valuePointer']=='/metrics/population/rows/0/series/values/0'
    assert report['catalogPath']=='data/site-data.json'
    other=engine.catalog;other['metrics']['population']['rows'][0]['value']=1
    assert engine.catalog['metrics']['population']['rows'][0]['value']!=1
    report['observations'][0]['provenance'][1]['status']['posas_2026']='mutated'
    assert engine.query(request('absolute_change',towns=['046018'],periods=['2019','2026']))['observations'][0]['provenance'][1]['status']['posas_2026']!='mutated'
    income=engine.query(request('absolute_change','income',towns=['046018'],periods=['2011','2024']))
    assert income['status']=='computed' and math.isclose(income['result']['value'],5174.99,abs_tol=1e-8)
    assert 'raw_income_archive_not_verified_by_adapter' in income['warnings']
    rejected(engine,request('compare','fuelPrices'),'adapter_not_implemented')
    rejected(engine,request('compare',dimension='women'),'dimension_adapter_not_implemented')
    rejected(engine,request('series',towns=['046018'],periods=['2024/25']),'unsupported_annual_period')
    rejected(engine,request('series',towns=['046018'],periods=['2026','2019']),'ordered_periods')
    rejected(engine,request('series',towns=['046018'],periods=['2025','2025']),'duplicate_period')
    rejected(engine,request('compare',towns=['unknown']),'unknown_or_duplicate_geography')
    rejected(engine,request('compare',towns=['046018','046018']),'unknown_or_duplicate_geography')
    rejected(engine,request('series',towns=['046018'],periods=['2018']),'period_not_available')
    rejected(engine,request('percentage_points'),'operation_not_implemented')
    rejected(engine,dict(request('compare'),allowPartial='yes'),'allowPartial_must_be_boolean')
    rejected(engine,dict(request('compare'),method='ignored'),'fields_not_applicable')
    rejected(engine,dict(request('compare'),definition='injected'),'invalid_query_fields')
    corr={'operation':'correlation','selectors':[{'metric':'population'},{'metric':'income'}],
          'axis':'municipalities','method':'pearson','purpose':'Technical alignment regression, no territorial policy inference'}
    rejected(engine,corr,'paired_period_mismatch')
    for s in corr['selectors']:s['periods']=['2024']
    r=engine.query(corr)
    assert r['status']=='computed' and r['result']['n']==7,r
    assert r['pairCoverage']=={'requested':7,'paired':7,'excludedKeys':[]}
    assert len(r['result']['leaveOneOut'])==7 and r['result']['pValue'] is None
    assert 'association_not_causation' in r['warnings']
    bad=copy.deepcopy(corr);bad.pop('purpose');rejected(engine,bad,'selection_purpose')
    bad=copy.deepcopy(corr);bad['method']='unknown';rejected(engine,bad,'correlation_method')

    with tempfile.TemporaryDirectory(prefix='a6-query-') as temporary:
        root=Path(temporary)
        snapshot=root/SNAPSHOT;snapshot.parent.mkdir(parents=True)
        snapshot.write_bytes((ROOT/SNAPSHOT).read_bytes())
        path=root/'catalog.json'
        canonical=copy.deepcopy(engine.catalog)
        canonical['metrics']['population']['rows'][0]['series']['values'][0]=0
        path.write_text(json.dumps(canonical))
        altered=QueryEngine(path,repository_root=root)
        rejected(altered,request('absolute_change',towns=['046018'],periods=['2019','2026']),'snapshot_mismatch')
        canonical=copy.deepcopy(engine.catalog)
        canonical['metrics']['income']['rows'][0]['series']['values'][0]=0
        path.write_text(json.dumps(canonical))
        altered=QueryEngine(path,repository_root=root)
        rejected(altered,request('relative_change','income',towns=['046018'],periods=['2011','2024']),'zero_baseline')
        canonical=copy.deepcopy(engine.catalog)
        # The shared eligibility guard refuses implicit exclusion of missing values.
        canonical['metrics']['population']['rows'][0]['value']=None
        path.write_text(json.dumps(canonical));altered=QueryEngine(path,repository_root=root)
        rejected(altered,request('compare'),'partial_coverage_requires_opt_in')
        partial=altered.query(dict(request('compare'),allowPartial=True))
        assert partial['status']=='computed' and len(partial['excluded'])==1
        assert partial['coverage']['requested']==7 and partial['coverage']['usable']==6
        historical=altered.query(request('series',towns=['046018'],periods=['2024','2026']))
        assert historical['status']=='computed' and historical['coverage']['usable']==2
        # Non-overlapping variables retain the exact keys excluded from pairing.
        canonical=copy.deepcopy(engine.catalog)
        canonical['metrics']['population']['rows'][0]['series']['values'][5]=None # 2024
        path.write_text(json.dumps(canonical));altered=QueryEngine(path,repository_root=root)
        partial=altered.query(dict(corr,allowPartial=True))
        assert partial['status']=='computed' and partial['result']['n']==6,partial
        assert partial['pairCoverage']['excludedKeys']==['046018']
        assert any(x.get('pairingKey')=='046018' for x in partial['excluded'])
        canonical=copy.deepcopy(engine.catalog)
        for row in canonical['metrics']['income']['rows']:
            row['value']=123
            row['series']['values'][-1]=123
        path.write_text(json.dumps(canonical));altered=QueryEngine(path,repository_root=root)
        rejected(altered,corr,'constant_variable')
        canonical=copy.deepcopy(engine.catalog)
        canonical['metrics']['population']['rows'][0]['series']['values'][5]=None
        # A selected observation with no corresponding catalog series is refused,
        # rather than treated as an implicit null or silently narrowed selection.
        canonical['metrics']['population']['rows'][0]['series']['years'].pop()
        canonical['metrics']['population']['rows'][0]['series']['values'].pop()
        path.write_text(json.dumps(canonical));altered=QueryEngine(path,repository_root=root)
        rejected(altered,request('series',towns=['046018'],periods=['2026']),'period_not_available')


def audit(path, layer):
    engine=QueryEngine(path,layer=layer)
    matrix=engine.coverage()
    assert len(matrix)==len(engine.catalog['metrics'])
    assert {r['metric'] for r in matrix}==set(engine.catalog['metrics'])
    adapters=[r['metric'] for r in matrix if r['engine']['status']=='adapter_present_query_preconditions_apply']
    assert set(adapters)=={'population','income'}
    assert all('reason' in r['engine'] for r in matrix if r['metric'] not in adapters)
    for key in adapters:
        report=engine.query(request('compare',key))
        assert report['status']=='computed',report
        assert report['coverage']['requested']==7
    print(f'A6.4 query audit {layer}: {len(matrix)} indicators, {len(adapters)} adapters; remaining exclusions explicit')


def main():
    regressions()
    audit(ROOT/'data/site-data.json','source')
    if (ROOT/'dist/data/site-data.json').exists():
        audit(ROOT/'dist/data/site-data.json','effective')
    engine=QueryEngine(ROOT/'data/site-data.json')
    examples=json.loads((ROOT/'ci/semantic-query-examples.json').read_text())['examples']
    for example in examples:
        report=engine.query(example['query'])
        expected='not_computable' if example['id']=='associazione_periodi_correnti_rifiutata' else 'computed'
        assert report['status']==expected,(example['id'],report)
    print('A6.4 deterministic query engine regression PASS')


if __name__=='__main__':
    main()
