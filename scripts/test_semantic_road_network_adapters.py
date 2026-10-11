"""Fixed clipped results, independent arithmetic, partitions and cached attacks."""
import math
from semantic_query_engine import QueryEngine, ROOT
from semantic_question_suite import pointer
from test_semantic_query_engine import rejected
import semantic_query_road_network_adapters as r

# km, km2, printed density, municipal/provincial/regional/state/private km,
# paved/unpaved/unclassified km. Transcribed references, not engine output.
FIXED = {
 '046005':(480.955860,84.817881,5.670454,425.237490,19.639895,3.155223,10.413793,22.509459,475.290999,5.519912,.144949),
 '046013':(139.038100,9.255013,15.023005,131.628986,2.536438,0.,4.872676,0.,138.372650,.426455,.238995),
 '046018':(313.923233,67.910451,4.622606,258.255865,9.039223,15.108455,27.882542,3.637148,313.045615,.877618,0.),
 '046024':(411.130550,42.228170,9.735931,383.630925,3.864267,0.,20.848506,2.786851,407.840671,3.064411,.225468),
 '046028':(153.945273,39.520172,3.895359,132.312936,15.798446,0.,5.101915,.731976,152.944568,1.000705,0.),
 '046030':(120.352216,80.265310,1.499430,94.193736,26.158480,0.,0.,0.,116.612686,2.659124,1.080406),
 '046033':(410.309849,32.753597,12.527169,362.518993,.041747,0.,46.267078,1.482030,379.456067,29.455270,1.398512)}
INDEX={'length':0,'density':2,'adminMunicipal':3,'adminProvincial':4,'adminRegional':5,
       'adminState':6,'adminPrivate':7,'paved':8,'unpaved':9,'pavementUnclassified':10}


def query(dim='total',op='compare',**selection):
    return dict(operation=op,selectors=[dict(metric='roadNetworkProfile',dimension=dim,**selection)])


def expected(dim,code):
    f=FIXED[code]
    return f[0]/f[1] if dim=='nativeRatio' else f[INDEX['length' if dim=='total' else dim.split(':',1)[1]]]


def regressions(path):
    e=QueryEngine(path,layer='effective');observations=0
    for dim in r.dimensions('roadNetworkProfile'):
        result=e.query(query(dim));assert result['status']=='computed',result
        for o in result['observations']:
            observations+=1;code=o['geography'];value=expected(dim,code)
            assert math.isclose(o['value'],value,rel_tol=0,abs_tol=1e-10)
            assert o['period']==r.PERIOD and o['unit']==('km_per_km2' if dim in ('view:density','nativeRatio') else 'km')
            assert pointer(e.catalog,o['provenance'][0]['valuePointer'])==o['publishedValue']
            assert o['provenance'][1]['recordPointer'].endswith(r.TOWNS[code])
            assert not o['notApplicable'] and not o['dataUnavailable']
            if dim=='nativeRatio':assert (o['numerator'],o['denominator'],o['scale'])==(FIXED[code][0],FIXED[code][1],1)
        assert set(r.NOTES)<=set(result['warnings'])
        ranked=e.query(query(dim,'rank'));assert ranked['status']=='computed',ranked
        assert [o['geography'] for o in ranked['result']['ranking']]==sorted(FIXED,key=lambda c:(-expected(dim,c),c))
        for op in ['series','absolute_change','relative_change','percentage_points','trend']:
            rejected(e,query(dim,op),'road_network_single_snapshot_no_history')
        for op,reason in [('benchmark_gap','road_network_geographic_benchmark_not_reviewed'),('anomaly','road_network_peer_anomaly_not_reviewed')]:
            rejected(e,dict(query(dim,op),**({'benchmark':'tuscany'} if op=='benchmark_gap' else {})),reason)
        if dim!='nativeRatio':rejected(e,query(dim,'weighted_ratio'),'road_network_only_native_density_pooling_reviewed')
    assert observations==84
    for codes in [list(FIXED),['046005','046018']]:
        pooled=e.query(query('nativeRatio','weighted_ratio',towns=codes));assert pooled['status']=='computed',pooled
        wanted=math.fsum(FIXED[c][0] for c in codes)/math.fsum(FIXED[c][1] for c in codes)
        assert math.isclose(pooled['result']['value'],wanted,rel_tol=0,abs_tol=1e-10)
    assert math.isclose(sum(v[0] for v in FIXED.values()),2029.655081,rel_tol=0,abs_tol=1e-8)
    assert math.isclose(sum(v[1] for v in FIXED.values()),356.750593,rel_tol=0,abs_tol=1.1e-6)
    for f in FIXED.values():
        assert math.isclose(sum(f[3:8]),f[0],rel_tol=0,abs_tol=3e-6)
        assert math.isclose(sum(f[8:]),f[0],rel_tol=0,abs_tol=3e-6)
        assert math.isclose(f[2],f[0]/f[1],rel_tol=0,abs_tol=1.4e-6)
    assert math.isclose(expected('nativeRatio','046013'),15.023004289675226,rel_tol=0,abs_tol=1e-12)
    assert expected('nativeRatio','046013')!=FIXED['046013'][2]
    for period in ['2021','2026','2022-06']:
        rejected(e,query(periods=[period]),'road_network_period_not_frozen')
    assert e.query(query(periods=[r.PERIOD]))['status']=='computed'
    for dim in ['numerator','denominator','share:paved','view:normalized']:
        rejected(e,query(dim),'dimension_adapter_not_implemented')
    for pair in [[dict(metric='roadNetworkProfile'),dict(metric='population')],[dict(metric='population'),dict(metric='roadNetworkProfile')]]:
        rejected(e,dict(operation='correlation',selectors=pair,axis='municipalities',method='pearson',purpose='descriptive'),'road_network_pair_not_jointly_reviewed')
    mutations=[lambda m:m['meta'].update(year='2026'),lambda m:m['meta'].update(unit='number'),
               lambda m:m.update(sourceUrl='https://example.com'),lambda m:m['rows'][0].update(value=False),
               lambda m:m['rows'][0]['parts'][0].update(value=1),lambda m:m['rows'][0].update(municipalAreaKm2=1),
               lambda m:m['rows'][0].update(town='Unknown'),lambda m:m['rows'][0].update(dataUnavailable=True),
               lambda m:m['rows'][0].update(series={'years':[2021],'values':[1]}),
               lambda m:m['aggregate'].update(value=1),lambda m:m['method'].update(caveat='Unique road kilometers')]
    for mutate in mutations:
        g=QueryEngine(path,layer='effective');assert g.query(query())['status']=='computed';mutate(g._catalog['metrics']['roadNetworkProfile'])
        rejected(g,query(),'road_network_public_definition_or_values_changed')
    attacks=[lambda s:s['roadNetworkProfile']['municipalities']['Camaiore'].update(graphKm=1),
             lambda s:s['roadNetworkProfile']['municipalities']['Camaiore'].update(municipalAreaKm2=0),
             lambda s:s['roadNetworkProfile']['versilia'].update(unionAreaKm2=1),
             lambda s:s['sources']['regioneIterNet'].update(reference='2026'),
             lambda s:s['measurementBoundary'].update(reference='2022 boundaries')]
    for attack in attacks:
        g=QueryEngine(path,layer='effective');assert g.query(query())['status']=='computed';attack(g.files[r.SNAPSHOT][0])
        rejected(g,query(),'road_network_frozen_snapshot_changed')
    g=QueryEngine(path,layer='effective');g._catalog['towns'][0]['name']='Unknown'
    rejected(g,query(),'road_network_municipal_identity_changed')
    print('Road network PASS: 84 fixed current observations including aliases/native ratios; 14 native components, two pooled densities, separate partitions, zero/ties, map/boundary dates and hostile cached edits; original geometry not replayed')


if __name__=='__main__':regressions(ROOT/'dist/data/site-data.json')
