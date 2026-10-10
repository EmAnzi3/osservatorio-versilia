"""Independent fixed AGCOM values, missing counts, dated provenance and guards."""
import math

from semantic_query_engine import QueryEngine, ROOT
from semantic_question_suite import pointer
from test_semantic_query_engine import rejected
import semantic_query_connectivity_adapters as c

# Independently transcribed official CSV cells: households, DESI counts, 20m counts,
# DESI published percentage, 20m published percentage. Do not derive missing counts.
FIXED = {'046005': (13119,11978,10512,91.3,80.1), '046013': (2707,None,None,0.,0.),
         '046018': (8982,4219,3084,47.,34.3), '046024': (9353,5546,4133,59.3,44.2),
         '046028': (5068,35,4,.7,.1), '046030': (1148,1009,889,87.9,77.4),
         '046033': (25039,23734,21536,94.8,86.)}
BENCHMARKS = {c.DESI: {'tuscany':73.22531610387755,'italy':82.89952077416727}, c.NEAR:{'tuscany':64.58685444439853,'italy':74.25960016740227}}
UNREACHED = {'046005':1141,'046013':None,'046018':4763,'046024':3807,'046028':5033,'046030':139,'046033':1305}


def query(key, op='compare', **selection): return dict(operation=op,selectors=[dict(metric=key,**selection)])


def regressions(path):
    e=QueryEngine(path,layer='effective'); catalog=e.catalog
    expected = {c.DESI:{k:v[3] for k,v in FIXED.items()},c.NEAR:{k:v[4] for k,v in FIXED.items()},c.REACHED:{k:v[1] for k,v in FIXED.items()},c.UNREACHED:UNREACHED}
    for key in c.KEYS:
        q=query(key)
        if key in c.COUNTS:
            rejected(e,q,'partial_coverage_requires_opt_in');q['allowPartial']=True
        r=e.query(q); assert r['status']=='computed',r
        assert r['coverage']['requested']==7 and r['coverage']['usable']==(6 if key in c.COUNTS else 7)
        for o in r['observations']:
            code=o['geography']; assert o['value']==expected[key][code] and o['period']=='2025-12-31'
            assert o['unit']==('percent' if key in c.PERCENTAGES else 'number')
            assert o['dataUnavailable']==(o['value'] is None) and not o['notApplicable']
            assert pointer(catalog,o['provenance'][0]['valuePointer'])==o['value']
            p=o['provenance'][1]; snap,_=e.file(c.NATIVE); native=pointer(snap,p['recordPointer'])
            assert tuple(native[f] for f in ('famiglie_residenti','famiglie_ftth','famiglie_ftth_20m','copertura_ftth_desi_pct','copertura_ftth_20m_pct'))==FIXED[code]
            assert p['nativeFields']['famiglie_residenti']==FIXED[code][0] and p['referenceDate']=='2025-12-31'
        ranked=e.query(dict(q,operation='rank')); assert ranked['status']=='computed'
        wanted=sorted((k for k,v in expected[key].items() if v is not None),key=lambda k:(-expected[key][k],k))
        assert [x['geography'] for x in ranked['result']['ranking']]==wanted
        # Explicit reference aliases share the same full date; not a 2026 observation.
        for period in ('2025',c.LABEL,'2025-12-31'):
            dated=e.query(dict(q,selectors=[dict(metric=key,periods=[period])]))
            assert dated['status']=='computed' and all(o['period']=='2025-12-31' for o in dated['observations'])
        rejected(e,query(key,periods=['2026']),'connectivity_reference_date_not_frozen')
        for op in ('series','absolute_change','relative_change','percentage_points','trend'):
            rejected(e,query(key,op,towns=['046018']),'connectivity_single_reference_no_history')
        for op,reason in [('weighted_ratio','connectivity_rounded_percentages_not_native_pooling'),('anomaly','connectivity_peer_anomaly_not_reviewed')]: rejected(e,query(key,op),reason)
        for order in ([key,'population'],['population',key]):
            rejected(e,dict(operation='correlation',selectors=[dict(metric=k) for k in order],axis='municipalities',method='pearson',purpose='descriptive'),'connectivity_pair_not_jointly_reviewed')
        for dim in ('normalized','numerator','denominator','sex:women'):
            rejected(e,query(key,dimension=dim),'dimension_adapter_not_implemented')
        changes=[lambda m:m['meta'].update(year='2026'),lambda m:m['meta'].update(unit='per1000'),lambda m:m['meta'].update(polarity='positive'),lambda m:m.update(sourceUrl='https://example.invalid'),lambda m:m['method'].update(formula='Other'),lambda m:m['method'].update(coverage='7/7' if key in c.COUNTS else '6/7'),lambda m:m['rows'][0].update(value=999),lambda m:m['rows'][0].update(value=False),lambda m:m['rows'][0].update(benchmarkValue=999),lambda m:m['rows'][0].update(code='046005'),lambda m:m['rows'][0].update(town='Unknown'),lambda m:m['rows'][0].update(slug='unknown'),lambda m:m['rows'][0].update(notApplicable=True),lambda m:m['rows'][0].update(dataUnavailable=True),lambda m:m['rows'][0].update(series={'years':[2025],'values':[1]}),lambda m:m['rows'][0].update(ratioComponents={'numerator':1}),lambda m:m['aggregate'].update(value=999),lambda m:m['aggregate'].update(label='Totale Versilia')]
        if key in c.PERCENTAGES:changes += [lambda m:m['meta']['benchmark'].update(tuscany=999),lambda m:m['meta']['benchmark'].update(sourceSnapshot=c.NATIVE)]
        else: changes += [lambda m:next(r for r in m['rows'] if r['code']=='046013').update(value=0),lambda m:m['meta'].update(benchmark={'tuscany':999})]
        for change in changes:
            g=QueryEngine(path,layer='effective');change(g._catalog['metrics'][key]);assert g.query(q)['status']=='not_computable'
    for key in c.PERCENTAGES:
        for scope,b in BENCHMARKS[key].items():
            for code in FIXED:
                r=e.query(dict(query(key,'benchmark_gap',towns=[code]),benchmark=scope));assert r['status']=='computed',r
                assert math.isclose(r['result']['value'],expected[key][code]-b,abs_tol=1e-12)
                assert r['observations'][1]['benchmarkAggregation'].startswith('frozen A3 audited')
        rejected(e,dict(query(key,'benchmark_gap',towns=['046018']),benchmark='versilia'),'connectivity_benchmark_scope_not_reviewed')
    for key in c.COUNTS: rejected(e,dict(query(key,'benchmark_gap',towns=['046018']),benchmark='tuscany'),'connectivity_absolute_benchmarks_incomplete')
    assert catalog['metrics'][c.REACHED]['aggregate']['value']==46521
    assert catalog['metrics'][c.UNREACHED]['aggregate']['value']==16188
    for key,want in [(c.DESI,71.12488687782805),(c.NEAR,61.37692766295708)]:
        assert math.isclose(catalog['metrics'][key]['aggregate']['value'],want,abs_tol=1e-12)
        weights=sum(v[0] for v in FIXED.values()); j=3 if key==c.DESI else 4
        assert math.isclose(sum(v[0]*v[j] for v in FIXED.values())/weights,want,abs_tol=1e-12)
    assert e.query(query(c.DESI))['observations'][1]['value']==0
    for p in c.HASHES:
        key=c.DESI
        for field in ('sha256','path'):
            g=QueryEngine(path,layer='effective');_,ref=g.file(p);ref[field]='changed';assert g.query(query(key))['status']=='not_computable'
        g=QueryEngine(path,layer='effective');data,_=g.file(p);data['schemaVersion']=999;assert g.query(query(key))['status']=='not_computable'
    print('Connectivity PASS: 28 fixed public cells, 35 native cells, 28 gaps, 4 aggregates, dated provenance, missing/zero and adversarial guards')


if __name__=='__main__': regressions(ROOT/'dist/data/site-data.json')
