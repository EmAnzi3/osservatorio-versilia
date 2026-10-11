"""Independent published references, zero/ties and hostile post-cache changes."""
import math
from semantic_query_engine import QueryEngine, ROOT
from semantic_question_suite import pointer
from test_semantic_query_engine import rejected
import semantic_query_hospital_adapters as h

COUNTS = {'046005':1,'046013':1,'046018':0,'046024':0,'046028':0,'046030':0,'046033':1}
RATES = {'046005':131.91449170418412,'046013':210.68702290076337,'046018':0,
         '046024':0,'046028':0,'046030':0,'046033':5.273566249176005}


def query(dim='total', op='compare', **selection):
    return dict(operation=op,selectors=[dict(metric='hospitals',dimension=dim,**selection)])


def regressions(path):
    e=QueryEngine(path,layer='effective')
    for dim,expected in [('total',COUNTS),('view:normalized',RATES)]:
        r=e.query(query(dim));assert r['status']=='computed',r
        for o in r['observations']:
            assert math.isclose(o['value'],expected[o['geography']],rel_tol=0,abs_tol=1e-10)
            assert o['period']=='2025' and not o['nativeComponentsAvailable']
            assert o['unit']==('number' if dim=='total' else 'per10k')
            assert pointer(e.catalog,o['provenance'][0]['valuePointer'])==o['value']
            assert not o['notApplicable'] and not o['dataUnavailable']
        assert set(h.NOTES)<=set(r['warnings'])
        rank=e.query(query(dim,'rank'));assert rank['status']=='computed'
        assert [o['geography'] for o in rank['result']['ranking']]==sorted(expected,key=lambda c:(-expected[c],c))
        for op in ['series','absolute_change','relative_change','percentage_points','trend']:
            rejected(e,query(dim,op),'hospital_single_public_snapshot_no_history')
        for op,reason in [('weighted_ratio','hospital_native_components_not_frozen_no_pooling'),('anomaly','hospital_peer_anomaly_not_reviewed'),('benchmark_gap','hospital_geographic_benchmark_not_frozen')]:
            rejected(e,dict(query(dim,op),**({'benchmark':'tuscany'} if op=='benchmark_gap' else {})),reason)
        for period in ['2024','2026']:
            rejected(e,query(dim,periods=[period]),'hospital_period_not_frozen')
        for pair in [[dict(metric='hospitals',dimension=dim),dict(metric='population')],[dict(metric='population'),dict(metric='hospitals',dimension=dim)]]:
            rejected(e,dict(operation='correlation',selectors=pair,axis='municipalities',method='pearson',purpose='descriptive'),'hospital_pair_not_jointly_reviewed')
    for dim in ['normalized','numerator','denominator','beds','sex:women']:
        rejected(e,query(dim),'dimension_adapter_not_implemented')
    mutations=[lambda m:m['meta'].update(year='2026'),lambda m:m['meta'].update(unit='percent'),
               lambda m:m['meta'].update(polarity='positive'),lambda m:m.update(sourceUrl='https://example.com'),
               lambda m:m['rows'][0].update(value=False),lambda m:m['rows'][0].update(value=9),
               lambda m:m['rows'][0]['normalized'].update(value=99),lambda m:m['rows'][0]['normalized'].update(unit='percent'),
               lambda m:m['rows'][0].update(benchmarkValue=99),lambda m:m['rows'][0].update(town='Unknown'),
               lambda m:m['rows'][0].update(code='046005'),lambda m:m['rows'][0].update(slug='unknown'),
               lambda m:m['rows'][0].update(dataUnavailable=True),lambda m:m['rows'][0].update(notApplicable=True),
               lambda m:m['rows'][0].update(series={'years':[2024],'values':[1]}),
               lambda m:m['rows'][0].update(ratioComponents={'numerator':1,'denominator':1}),
               lambda m:m['aggregate'].update(value=99),lambda m:m['normalizedAggregate'].update(value=99),
               lambda m:m['method'].update(formula='Other'),lambda m:m['meta'].update(benchmark={'tuscany':1})]
    for mutation in mutations:
        g=QueryEngine(path,layer='effective');assert g.query(query())['status']=='computed'
        mutation(g._catalog['metrics']['hospitals'])
        for dim in h.dimensions('hospitals'):
            rejected(g,query(dim),'hospital_public_definition_or_values_changed')
    g=QueryEngine(path,layer='effective');g._catalog['towns'][0]['name']='Unknown'
    rejected(g,query(),'hospital_municipal_identity_changed')
    print('Hospital adapters PASS: 14 fixed public observations, zeros/ties, distinct site/bed-rate definitions, provenance and hostile post-cache/refusal guards; no native-record replay claimed')


if __name__=='__main__':regressions(ROOT/'dist/data/site-data.json')
