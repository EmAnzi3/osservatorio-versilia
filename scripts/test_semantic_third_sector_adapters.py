"""Fixed independent RUNTS anchors, pooling arithmetic and hostile cache checks."""
import copy
import math
import tempfile
from pathlib import Path
from semantic_query_engine import QueryEngine, ROOT
from semantic_question_suite import pointer
from test_semantic_query_engine import rejected
import semantic_query_third_sector_adapters as a

# Reviewed municipal counts and Istat denominators, not adapter-generated answers.
ANCHORS = {'046005':(85,31763),'046013':(24,6550),'046018':(53,21782),
           '046024':(67,22678),'046028':(50,12284),'046030':(13,2783),'046033':(173,60680)}


def query(dim='total',op='compare',**selection):
    return dict(operation=op,selectors=[dict(metric='thirdSector',dimension=dim,**selection)])


def regressions(path):
    e=QueryEngine(path,layer='effective')
    for dim in a.dimensions('thirdSector'):
        r=e.query(query(dim));assert r['status']=='computed',r
        for o in r['observations']:
            n,d=ANCHORS[o['geography']];wanted=n if dim=='registeredEntities' else n/d*1000
            assert math.isclose(o['value'],wanted,rel_tol=0,abs_tol=1e-12)
            assert o['period']=='2026-10-11' and not o['nativeRecordReplayAvailable']
            assert pointer(e.catalog,o['evidence'][0]['valuePointer'])==o['value']
            snap,ref=e.file(a.PATH);cell=pointer(snap,o['evidence'][1]['recordPointer'])
            assert (cell['count'],cell['population'])==(n,d)
            if dim=='nativeRatio':
                assert (o['numerator'],o['denominator'],o['scale'])==(n,d,1000)
                assert o['numeratorPeriod']=='2026-10-11' and o['denominatorPeriod']=='2026-01-01'
        rank=e.query(query(dim,'rank'));assert rank['status']=='computed'
        ordered=sorted(ANCHORS,key=lambda c:(-(ANCHORS[c][0] if dim=='registeredEntities' else ANCHORS[c][0]/ANCHORS[c][1]),c))
        assert [o['geography'] for o in rank['result']['ranking']]==ordered
        for op in ['series','absolute_change','relative_change','percentage_points','trend']:
            rejected(e,query(dim,op),'third_sector_legal_seat_history_not_frozen')
        for op,reason in [('benchmark_gap','third_sector_geographic_benchmark_not_reviewed'),('anomaly','third_sector_peer_anomaly_not_reviewed')]:
            rejected(e,dict(query(dim,op),**({'benchmark':'tuscany'} if op=='benchmark_gap' else {})),reason)
        for period in ['2025','2026-01-01','2026-10-10','2027']:
            rejected(e,query(dim,periods=[period]),'third_sector_period_not_frozen')
        assert e.query(query(dim,periods=['2026']))['observations'][0]['period']=='2026-10-11'
        for selectors in [[dict(metric='thirdSector',dimension=dim),dict(metric='population')],[dict(metric='population'),dict(metric='thirdSector',dimension=dim)]]:
            rejected(e,dict(operation='correlation',selectors=selectors,axis='municipalities',method='pearson',purpose='descriptive'),'third_sector_pair_not_jointly_reviewed')
        if dim!='nativeRatio': rejected(e,query(dim,'weighted_ratio'),'third_sector_native_ratio_dimension_required')
    for codes,n,d in [(None,465,158520),(['046005','046018'],138,53545)]:
        r=e.query(query('nativeRatio','weighted_ratio',**({'towns':codes} if codes else {})))
        assert r['status']=='computed',r
        assert math.isclose(r['result']['value'],n/d*1000,rel_tol=0,abs_tol=1e-12)
    assert not math.isclose(sum(n/d*1000 for n,d in ANCHORS.values())/7,465/158520*1000,abs_tol=1e-3)
    for mutation in [lambda m:m['rows'][0].update(value=99),lambda m:m['rows'][0].update(registeredEntities=54),
                     lambda m:m['rows'][0].update(residentPopulation=999),lambda m:m['rows'][0].update(populationReference='2025-01-01'),
                     lambda m:m['meta'].update(year='2025'),lambda m:m['meta'].update(unit='percent'),
                     lambda m:m.update(sourceUrl='https://example.com'),lambda m:m['aggregate'].update(value=99),
                     lambda m:m['rows'][0].update(series={'years':[2025],'values':[1]})]:
        g=QueryEngine(path,layer='effective');assert g.query(query())['status']=='computed'
        mutation(g._catalog['metrics']['thirdSector'])
        rejected(g,query(),'third_sector_public_definition_or_values_changed')
    for mutation in [lambda s:s['rows'][0].update(count=54),lambda s:s['rows'][0].update(populationReference='2025-01-01'),
                     lambda s:s.update(sourceSha256='0'*64),lambda s:s.update(method='other'),
                     lambda s:s['versilia'].update(count=466),lambda s:s['rows'].append(copy.deepcopy(s['rows'][0]))]:
        g=QueryEngine(path,layer='effective');assert g.query(query())['status']=='computed'
        mutation(g.files[a.PATH][0]);rejected(g,query(),'third_sector_frozen_input_changed')
    g=QueryEngine(path,layer='effective');assert g.query(query())['status']=='computed'
    g.files[a.PATH][1]['sha256']='0'*64;rejected(g,query(),'third_sector_frozen_input_changed')
    g=QueryEngine(path,layer='effective');g._catalog['towns'][0]['name']='Unknown'
    rejected(g,query(),'third_sector_municipal_identity_changed')
    with tempfile.TemporaryDirectory() as folder:
        g=QueryEngine(path,layer='effective');g.root=Path(folder)
        target=g.root/a.PATH;target.parent.mkdir(parents=True);target.write_text('{}')
        rejected(g,query(),'third_sector_frozen_input_changed')
    print('RUNTS adapters PASS: 21 fixed observations, 14 components, separately dated ratios, two pooled results, provenance and hostile input/cache guards; normalized replay only')


if __name__=='__main__':regressions(ROOT/'dist/data/site-data.json')
