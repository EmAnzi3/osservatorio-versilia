"""Fixed independently transcribed road cells, missing years and provenance guards."""
import math

from semantic_query_engine import QueryEngine, ROOT
from semantic_question_suite import pointer
from test_semantic_query_engine import rejected
import semantic_query_road_adapters as r

# Incident rate, mortality index, injury index, legacy injured rate, DAIT proceeds.
CURRENT = {
 '046005': (6.43682491836222,1.95121951219512,117.073170731707,75.32011046949535,36.0983071095113),
 '046013': (15.0264077958789,0.,126.732673267327,188.87413309724067,247.638983782175),
 '046018': (4.35071328799432,0.,115.789473684211,50.30871255431054,6.76785583524027),
 '046024': (6.10573016186774,.719424460431655,123.021582733813,75.03949447077409,22.4294826336255),
 '046028': (3.70728562217924,4.34782608695652,108.695652173913,40.20908725371934,39.5120434098519),
 '046030': (1.72562553925798,0.,140.,24.11298656562177,2.19099427381572),
 '046033': (6.62420801990558,1.24378109452736,117.661691542289,77.85367459468357,49.005837367849)}
FIRST = {
 '046005': (7.35656242304851,1.25523012552301,127.196652719665,60.55226199156707,25.4292758956937),
 '046013': (15.4516640253566,0.,128.205128205128,139.22092532695822,184.090501412429),
 '046018': (3.47864867878247,2.56410256410256,128.205128205128,39.32454314133704,2.32421437382921),
 '046024': (7.62378288792211,1.6304347826087,127.173913043478,59.13814845414619,91.4154026024639),
 '046028': (4.31279082964476,0.,133.333333333333,32.096445905746045,36.3057542905149),
 '046030': (.617379225189072,0.,150.,13.522650439486139,2.87826883206634),
 '046033': (6.80928422781601,.936768149882904,122.248243559719,44.453992596509785,29.7584687970171)}
BENCHMARKS = [(4.14689530797407,2.9404986625331),(1.23896138131014,1.74776770263723),(128.278634506393,134.891326919084),None,(47.5484586587964,29.3268396123682)]
CASES = [(r.SAFETY,dim) for dim in r.VIEWS] + [(r.FINES,'total')]


def query(key, dim='total', op='compare', **selection):
    return dict(operation=op, selectors=[dict(metric=key, dimension=dim, **selection)])


def regressions(path):
    e = QueryEngine(path, layer='effective'); replay = 0
    for j, (key, dim) in enumerate(CASES):
        q = query(key,dim); v=e.query(q); assert v['status']=='computed',v
        assert v['coverage']['usable']==7 and v['coverage']['requested']==7
        for o in v['observations']:
            equal = CURRENT[o['geography']][j]; assert o['value']==equal and o['period']=='2024'
            assert o['unit']==['per1000','per100','per100','per10k','currency'][j]
            assert pointer(e.catalog,o['provenance'][0]['valuePointer'])==equal
            evidence=o['provenance'][1]; frozen,_=e.file(evidence['path'])
            assert pointer(frozen,evidence['recordPointer'])==equal
            assert evidence['kind']==('canonical_legacy_carrier' if j==3 else 'source_snapshot')
        aggregate=e.catalog['metrics'][key]['aggregate']
        actual=aggregate['parts'][j]['value'] if key==r.SAFETY else aggregate['value']
        assert math.isclose(actual,math.fsum(c[j] for c in CURRENT.values())/7,rel_tol=0,abs_tol=1e-12)
        rank=e.query(dict(q,operation='rank')); assert rank['status']=='computed'
        wanted=sorted(CURRENT,key=lambda code:(-CURRENT[code][j],code))
        assert [x['geography'] for x in rank['result']['ranking']]==wanted
        for code in CURRENT:
            request=query(key,dim,'series',towns=[code]); request['allowPartial']=True
            series=e.query(request);assert series['status']=='computed',series
            observations=series['observations']; replay+=len(observations)
            assert len(observations)==[11,11,11,5,4][j]
            assert observations[0]['value']==FIRST[code][j] and observations[-1]['value']==CURRENT[code][j]
            assert observations[0]['period']==['2014','2014','2014','2020','2021'][j]
            for o in observations:
                evidence=o['provenance'][1]; frozen,_=e.file(evidence['path'])
                assert pointer(frozen,evidence['recordPointer'])==o['value']
                if o['value'] is not None: assert pointer(e.catalog,o['provenance'][0]['valuePointer'])==o['value']
        for op in ('absolute_change','relative_change','percentage_points','trend'):
            rejected(e,query(key,dim,op,towns=['046018']), 'road_temporal_continuity_not_reviewed')
        for op,reason in [('weighted_ratio','road_native_counts_and_denominators_not_frozen'),('anomaly','road_peer_anomaly_not_reviewed')]:rejected(e,query(key,dim,op),reason)
        for order in [[dict(metric=key,dimension=dim),dict(metric='population')],[dict(metric='population'),dict(metric=key,dimension=dim)]]:
            rejected(e,dict(operation='correlation',selectors=order,axis='municipalities',method='pearson',purpose='descriptive'),'road_pair_not_jointly_reviewed')
        rejected(e,query(key,dim,periods=['2025']),'road_period_not_frozen')
        rejected(e,query(key,'sex:women'),'dimension_adapter_not_implemented')
        if BENCHMARKS[j]:
            for scope,b in zip(('tuscany','italy'),BENCHMARKS[j]):
                for code in CURRENT:
                    v=e.query(dict(query(key,dim,'benchmark_gap',towns=[code]),benchmark=scope)); assert v['status']=='computed',v
                    assert math.isclose(v['result']['value'],CURRENT[code][j]-b,rel_tol=0,abs_tol=1e-12)
                    assert 'no workbook' in v['observations'][1]['benchmarkAggregation']
            rejected(e,dict(query(key,dim,'benchmark_gap',towns=['046018'],periods=['2023']),benchmark='tuscany'),'road_benchmark_scope_or_period_not_reviewed')
        else:rejected(e,dict(query(key,dim,'benchmark_gap',towns=['046018']),benchmark='tuscany'),'road_injured_benchmark_not_frozen')
        changes=[lambda m:m['meta'].update(year='2025'),lambda m:m['meta'].update(unit='number'),lambda m:m['meta'].update(polarity='positive'),lambda m:m.update(sourceUrl='https://example.invalid'),lambda m:m['method'].update(formula='Other'),lambda m:m['method'].update(coverage='6/7'),lambda m:m['rows'][0].update(value=999),lambda m:m['rows'][0].update(value=False),lambda m:m['rows'][0].update(benchmarkValue=999),lambda m:m['rows'][0].update(code='999999'),lambda m:m['rows'][0].update(town='Unknown'),lambda m:m['rows'][0].update(slug='unknown'),lambda m:m['rows'][0].update(notApplicable=True),lambda m:m['rows'][0].update(dataUnavailable=True),lambda m:m['rows'][0].update(ratioComponents={'numerator':1}),lambda m:m['aggregate'].update(value=999),lambda m:m['aggregate'].update(label='Totale Versilia'),lambda m:m['meta']['benchmark'].update(tuscany=999),lambda m:m['rows'][0]['series']['values'].__setitem__(0,999)]
        if key==r.SAFETY:changes += [lambda m:m['rows'][0]['parts'][2].update(unit='percent'),lambda m:m['rows'][0]['componentSeries']['Mortalità']['values'].__setitem__(0,999),lambda m:m['aggregate']['parts'][2].update(value=999)]
        for change in changes:
            g=QueryEngine(path);change(g._catalog['metrics'][key]);assert g.query(q)['status']=='not_computable'
    assert replay==294
    # Primary aliases carry exactly the same observations, not extra data.
    for op in ('compare','series'):
        a=e.query(dict(query(r.SAFETY,'total',op,towns=['046018'] if op=='series' else list(CURRENT)),allowPartial=True));b=e.query(dict(query(r.SAFETY,r.INCIDENTS,op,towns=['046018'] if op=='series' else list(CURRENT)),allowPartial=True))
        assert a['status']==b['status']=='computed'
        assert [(o['geography'],o['period'],o['value']) for o in a['observations']]==[(o['geography'],o['period'],o['value']) for o in b['observations']]
    for dim in [r.INCIDENTS,r.MORTALITY,r.INJURY]:
        q=query(r.SAFETY,dim,'series',towns=['046030'])
        rejected(e,q,'partial_coverage_requires_opt_in');v=e.query(dict(q,allowPartial=True));assert v['status']=='computed'
        missing=next(o for o in v['observations'] if o['period']=='2017');assert missing['value'] is None and missing['dataUnavailable']
        assert v['coverage']['requested']==11 and v['coverage']['usable']==10
        public=pointer(e.catalog,missing['provenance'][0]['valuePointer']);assert 2017 not in public['years']
        g=QueryEngine(path);row=next(row for row in g._catalog['metrics'][r.SAFETY]['rows'] if row['code']=='046030');row['componentSeries'][r.SPECS[dim][1]]['years'].insert(3,2017);row['componentSeries'][r.SPECS[dim][1]]['values'].insert(3,0)
        assert g.query(query(r.SAFETY,dim))['status']=='not_computable'
    for filename in (r.NATIVE,r.CANONICAL):
        for field in ('path','sha256'):
            g=QueryEngine(path);_,ref=g.file(filename);ref[field]='changed';assert g.query(query(r.SAFETY))['status']=='not_computable'
    g=QueryEngine(path);data,_=g.file(r.NATIVE);data['towns']['Camaiore']['roadIncidentRate']['values'][0]=999;assert g.query(query(r.SAFETY))['status']=='not_computable'
    g=QueryEngine(path);data,_=g.file(r.CANONICAL);data['metrics'][r.SAFETY]['rows'][0]['componentSeries']['Feriti']['values'][0]=999;assert g.query(query(r.SAFETY,r.INJURED))['status']=='not_computable'
    print('Road PASS: 35 fixed current cells + 7 primary aliases, 35 historical anchors, 56 gaps, 294 historical cells replayed (3 native null), guards and provenance')


if __name__=='__main__': regressions(ROOT/'data/site-data.json')
