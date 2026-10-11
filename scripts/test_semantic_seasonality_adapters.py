"""Fixed public references, distinct month selection and hostile cached inputs."""
import math
from semantic_query_engine import QueryEngine, ROOT
from semantic_question_suite import pointer
from test_semantic_query_engine import rejected
import semantic_query_seasonality_adapters as s

VALUES={'046005':55.69144840034739,'046013':60.05249044331603,'046018':50.85756504301019,
        '046024':56.81186156006498,'046028':50.33885934730476,'046030':56.92045212198763,'046033':63.71711502971945}
TUSCANY=48.24943209489199


def query(op='compare', **selection):
    return dict(operation=op,selectors=[dict(dict(metric='tourismSeasonality',dimension='total'),**selection)])


def regressions(path):
    e=QueryEngine(path,layer='effective');r=e.query(query());assert r['status']=='computed',r
    for o in r['observations']:
        assert math.isclose(o['value'],VALUES[o['geography']],rel_tol=0,abs_tol=1e-10)
        assert o['period']=='2025' and o['unit']=='percent' and not o['nativeComponentsAvailable']
        assert pointer(e.catalog,o['provenance'][0]['valuePointer'])==o['value']
        assert not o['notApplicable'] and not o['dataUnavailable']
        gap=e.query(dict(query('benchmark_gap',towns=[o['geography']]),benchmark='tuscany'))
        assert gap['status']=='computed',gap
        assert math.isclose(gap['result']['value'],VALUES[o['geography']]-TUSCANY,rel_tol=0,abs_tol=1e-10)
        assert gap['observations'][1]['source'].endswith('5-movimento-comune_mese-2025-agg-maggio-2026-')
        assert gap['observations'][1]['value']==TUSCANY and not gap['observations'][1]['nativeComponentsAvailable']
    assert set(s.NOTES)<=set(r['warnings'])
    rank=e.query(query('rank'));assert rank['status']=='computed'
    assert [o['geography'] for o in rank['result']['ranking']]==sorted(VALUES,key=lambda c:(-VALUES[c],c))
    for op in ['series','absolute_change','relative_change','percentage_points','trend']:
        rejected(e,query(op),'seasonality_single_annual_measure_no_monthly_or_historical_panel')
    for op,reason in [('weighted_ratio','seasonality_monthly_panels_not_frozen_no_pooling'),('anomaly','seasonality_peer_anomaly_not_reviewed')]:
        rejected(e,query(op),reason)
    for scope in ['italy','versilia']:
        rejected(e,dict(query('benchmark_gap',towns=['046018']),benchmark=scope),'seasonality_benchmark_scope_or_period_not_reviewed')
    for period in ['2024','2026','2025-07']:
        rejected(e,query(periods=[period]),'seasonality_period_not_frozen' if '-' not in period else 'unsupported_annual_period')
    for dim in ['month:07','numerator','denominator','nativeRatio','view:normalized']:
        rejected(e,query(dimension=dim),'dimension_adapter_not_implemented')
    for pair in [[dict(metric='tourismSeasonality'),dict(metric='tourismPresences')],[dict(metric='tourismPresences'),dict(metric='tourismSeasonality')]]:
        rejected(e,dict(operation='correlation',selectors=pair,axis='municipalities',method='pearson',purpose='descriptive'),'seasonality_pair_not_jointly_reviewed')
    mutations=[lambda m:m['meta'].update(year='2026'),lambda m:m['meta'].update(unit='number'),
               lambda m:m['meta'].update(polarity='positive'),lambda m:m.update(sourceUrl='https://example.com'),
               lambda m:m['rows'][0].update(value=False),lambda m:m['rows'][0].update(value=9),
               lambda m:m['rows'][0].update(benchmarkValue=99),lambda m:m['rows'][0].update(town='Unknown'),
               lambda m:m['rows'][0].update(code='046005'),lambda m:m['rows'][0].update(dataUnavailable=True),
               lambda m:m['rows'][0].update(notApplicable=True),lambda m:m['rows'][0].update(series={'years':[2024],'values':[1]}),
               lambda m:m['rows'][0].update(ratioComponents={'numerator':1,'denominator':1}),
               lambda m:m['aggregate'].update(value=99),lambda m:m['method'].update(formula='Fixed summer quarter'),
               lambda m:m['meta']['benchmark'].update(tuscany=1)]
    for mutation in mutations:
        g=QueryEngine(path,layer='effective');assert g.query(query())['status']=='computed'
        mutation(g._catalog['metrics']['tourismSeasonality'])
        rejected(g,query(),'seasonality_public_definition_or_values_changed')
    for mutate in [lambda snap:snap['benchmarks']['tourismSeasonality'].update(tuscany=1),
                   lambda snap:snap['sources'].update(monthly='https://example.com')]:
        g=QueryEngine(path,layer='effective');assert g.query(dict(query('benchmark_gap',towns=['046018']),benchmark='tuscany'))['status']=='computed'
        mutate(g.files[s.BENCHMARK][0])
        rejected(g,dict(query('benchmark_gap',towns=['046018']),benchmark='tuscany'),'seasonality_frozen_benchmark_changed')
    g=QueryEngine(path,layer='effective');g._catalog['towns'][0]['name']='Unknown'
    rejected(g,query(),'seasonality_municipal_identity_changed')
    # Selection does not commute with aggregation: local top-three numerators cannot be pooled.
    a=[10,10,10]+[0]*9;b=[0]*3+[10,10,10]+[0]*6
    assert sum(sorted(a,reverse=True)[:3])+sum(sorted(b,reverse=True)[:3])==60
    assert sum(sorted([x+y for x,y in zip(a,b)],reverse=True)[:3])==30
    print('Seasonality adapters PASS: 7 fixed shares and 7 Tuscany gaps; provenance, post-cache guards and noncommuting month-selection example; no monthly/native replay claimed')


if __name__=='__main__':regressions(ROOT/'dist/data/site-data.json')
