"""Independent census shares and explicit separation from work-matrix margins."""
import math
from semantic_query_engine import QueryEngine, ROOT
from semantic_question_suite import pointer
from test_semantic_query_engine import rejected
import semantic_query_outside_municipality_adapters as a

SHARES = {'046005':484, '046013':493, '046018':629, '046024':491,
          '046028':642, '046030':632, '046033':318}  # tenths of a percent


def query(op='compare', **selection):
    return dict(operation=op, selectors=[dict(metric='outsideMunicipality', **selection)])


def regressions(path):
    e=QueryEngine(path, layer='effective');r=e.query(query());assert r['status']=='computed',r
    assert len(r['observations'])==7 and set(a.NOTES)<=set(r['warnings'])
    for o in r['observations']:
        assert o['value']==SHARES[o['geography']]/10
        assert o['unit']=='percent' and o['period']=='2021'
        assert not o['nativeComponentsAvailable'] and not o['nativeRecordReplayAvailable']
        assert 'numerator' not in o and 'denominator' not in o
        ref=o['evidence'][0];assert ref['sha256']==e.catalog_hash
        assert pointer(e.catalog, ref['valuePointer'])==o['value']
    ranked=e.query(query('rank'));assert ranked['status']=='computed',ranked
    assert [o['geography'] for o in ranked['result']['ranking']]==['046028','046030','046018','046013','046024','046005','046033']
    assert math.isclose(sum(SHARES.values())/70,e.catalog['metrics']['outsideMunicipality']['aggregate']['value'],abs_tol=1e-12)
    # Work-matrix Massarosa: 5,568 external / 7,800 daily resident commuters.
    assert not math.isclose(SHARES['046018']/10,5568/7800*100,abs_tol=1e-9)
    for period in ['2020','2022','2026','2021-01-01']:
        rejected(e,query(periods=[period]),'outside_only_census_2021_frozen')
    for op in ['series','absolute_change','relative_change','percentage_points','trend']:
        rejected(e,query(op),'outside_single_census_no_comparable_history_frozen')
    for op,reason in [('weighted_ratio','outside_census_components_not_frozen_no_pooling'),
                      ('anomaly','outside_peer_anomaly_not_reviewed')]: rejected(e,query(op),reason)
    for scope in ['tuscany','italy','versilia']:
        rejected(e,dict(query('benchmark_gap'),benchmark=scope),'outside_geographic_benchmark_not_reconciled')
    for key in ['selfContainment','outboundCommuters','outboundCommutersRate','population','income']:
        for pair in [[dict(metric='outsideMunicipality'),dict(metric=key)], [dict(metric=key),dict(metric='outsideMunicipality')]]:
            rejected(e,dict(operation='correlation',selectors=pair,axis='municipalities',method='pearson',purpose='descriptive'),'outside_pair_not_jointly_reviewed')
    for dim in ['numerator','denominator','nativeRatio','normalized','sex:women','study','outsideVersilia']:
        rejected(e,query(dimension=dim),'dimension_adapter_not_implemented')
    mutations=[lambda m:m['meta'].update(year='2026'),lambda m:m['meta'].update(description='daily commuters'),
               lambda m:m['meta'].update(unit='number'),lambda m:m['meta'].update(polarity='positive'),
               lambda m:m.update(sourceUrl='other'),lambda m:m['method'].update(formula='100-selfContainment'),
               lambda m:m['rows'][0].update(value=None),lambda m:m['rows'][0].update(value=0),
               lambda m:m['rows'][0].update(value=False),lambda m:m['rows'][0].update(benchmarkValue=1),
               lambda m:m['rows'][0].update(code='046005'),lambda m:m['rows'][0].update(dataUnavailable=True),
               lambda m:m['rows'][0].update(ratioComponents={'numerator':5568,'denominator':7800}),
               lambda m:m['rows'][0].update(series={'years':[2020],'values':[1]}),
               lambda m:m['aggregate'].update(value=99),lambda m:m['meta'].update(benchmark={'tuscany':50})]
    for mutate in mutations:
        g=QueryEngine(path,layer='effective');assert g.query(query())['status']=='computed'
        mutate(g._catalog['metrics']['outsideMunicipality'])
        rejected(g,query(),'outside_public_definition_or_values_changed')
    g=QueryEngine(path,layer='effective');g._catalog['towns'][0]['name']='Unknown'
    rejected(g,query(),'outside_municipal_identity_changed')
    print('Outside municipality PASS: seven independent census shares, ranks/pointers, Massarosa non-complement, separate universes, native-count/territorial pooling refusals and hostile-cache guards; public catalog replay only')


if __name__=='__main__':regressions(ROOT/'dist/data/site-data.json')
