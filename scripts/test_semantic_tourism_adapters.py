"""Fixed tourism references, frozen history replay and adversarial boundaries."""
import math
from semantic_query_engine import QueryEngine, ROOT
from test_semantic_query_engine import rejected
import semantic_query_tourism_adapters as t

# Independent fixed transcription: arrivals, nights, foreign nights (2025),
# hotel beds, other beds, structures (2024), estimated residents (1 January 2026).
FIXED = {
 '046005': (154693,528521,244191,4666,2386,267,31763),
 '046013': (108324,350540,216264,3453,826,137,6550),
 '046018': (9936,37898,18130,141,727,52,21782),
 '046024': (128700,435828,190648,5446,935,208,22678),
 '046028': (3249,9591,1683,482,102,16,12284),
 '046030': (2247,4689,1336,78,178,19,2783),
 '046033': (224210,858865,346270,4096,11187,205,60680),
}
BENCH = {t.ARRIVALS:(15141534,None),t.PRESENCES:(45769090,None),t.STAY:(45769090/15141534,None),t.FOREIGN:(57.948436379224496,None),t.BEDS:(617143,5498773),t.BED_RATE:(617143/3659222*1000,5498773/58942828*1000),t.STRUCTURE_RATE:(22379/3659222*1000,265319/58942828*1000)}


def query(key, dim='total', op='compare', **selection):
    return dict(operation=op, selectors=[dict(metric=key, dimension=dim, **selection)])


def values(n):
    a,p,f,h,o,s,r=n
    return {t.ARRIVALS:a,t.PRESENCES:p,t.STAY:p/a,t.FOREIGN:round(f/p*100,1),t.BEDS:h+o,t.BED_RATE:(h+o)/r*1000,t.STRUCTURE_RATE:s/r*1000}


def regressions(path):
    e=QueryEngine(path,layer='effective'); checked=0; replay=0
    for key in t.KEYS:
        q=e.query(query(key)); assert q['status']=='computed',q
        for o in q['observations']:
            assert math.isclose(o['value'],values(FIXED[o['geography']])[key],rel_tol=0,abs_tol=1e-9)
            assert o['source'] and o['provenance'] and o['period']==('2025' if key in t.MOVEMENT else '2024');checked+=1
            if key in (t.BED_RATE,t.STRUCTURE_RATE): assert o['denominatorPeriod']=='2026-01-01' and o['numeratorPeriod']=='2024'
        for scope,value in zip(('tuscany','italy'),BENCH[key]):
            if value is None: continue
            gap=e.query(dict(query(key,op='benchmark_gap',towns=['046005']),benchmark=scope)); assert gap['status']=='computed',gap
            assert math.isclose(gap['observations'][1]['value'],value,rel_tol=0,abs_tol=1e-9)
    legacy=e.query(query(t.PRESENCES,op='absolute_change',towns=['046018'],periods=['2023','2025'])); assert legacy['status']=='computed' and legacy['result']['value']==2791
    totals=[sum(n[i] for n in FIXED.values()) for i in range(7)]
    for key,dim,num,den,scale in ((t.STAY,'total',totals[1],totals[0],1),(t.FOREIGN,'nativeRatio',totals[2],totals[1],100),(t.BED_RATE,'total',totals[3]+totals[4],totals[6],1000),(t.STRUCTURE_RATE,'total',totals[5],totals[6],1000)):
        q=e.query(query(key,dim,'weighted_ratio'));assert q['status']=='computed',q
        assert math.isclose(q['result']['value'],num/den*scale,rel_tol=0,abs_tol=1e-9)
    q=e.query(query(t.FOREIGN,'nativeRatio')); assert q['status']=='computed',q
    for o in q['observations']:
        n=FIXED[o['geography']];assert math.isclose(o['value'],n[2]/n[1]*100,rel_tol=0,abs_tol=1e-9);checked+=1
    assert not math.isclose(totals[2]/totals[1]*100,e._catalog['metrics'][t.FOREIGN]['aggregate']['value'],rel_tol=0,abs_tol=1e-9)
    # This is replay of frozen extraction, not another independent acquisition or fixed transcription.
    move,_=e.file(t.MOVE);cap,_=e.file(t.CAP)
    for key in (*t.MOVEMENT,t.BEDS):
        for code in FIXED:
            q=e.query(query(key,op='series',towns=[code]));assert q['status']=='computed',q
            for o in q['observations']:
                y=int(o['period'])
                if key==t.BEDS: expected=cap['municipalBedsHistory']['valuesByCode'][code][y-2002]
                else:
                    n=move['municipalMovementHistory']['countsByYear'][str(y)][code];a,p,f=(n[k] for k in ('arrivals','presences','foreignPresences'))
                    expected={t.ARRIVALS:a,t.PRESENCES:p,t.STAY:p/a,t.FOREIGN:round(f/p*100,1)}[key]
                assert math.isclose(o['value'],expected,rel_tol=0,abs_tol=1e-9);replay+=1
    for key in t.KEYS:
        for op in (() if key == t.PRESENCES else ('trend','absolute_change','relative_change','percentage_points')): rejected(e,query(key,op=op,towns=['046005']),'tourism_temporal_continuity_not_reviewed')
        if key != t.PRESENCES: rejected(e,query(key,op='anomaly'),'tourism_peer_anomaly_not_reviewed')
        for pair in (() if key == t.PRESENCES else ([{'metric':key},{'metric':'population'}],[{'metric':'population'},{'metric':key}])): rejected(e,dict(operation='correlation',selectors=pair,axis='municipalities',method='pearson',purpose='descriptive'),'tourism_pair_not_jointly_reviewed')
        rejected(e,query(key,periods=['2027']),'tourism_period_not_frozen')
    for key in (t.BED_RATE,t.STRUCTURE_RATE): rejected(e,query(key,op='series',towns=['046005']),'tourism_historical_resident_ratio_not_frozen')
    rejected(e,query(t.FOREIGN,op='weighted_ratio'),'tourism_native_ratio_dimension_required')
    rejected(e,dict(query(t.FOREIGN,'nativeRatio','benchmark_gap',towns=['046005']),benchmark='tuscany'),'tourism_benchmark_dimension_not_reviewed')
    rejected(e,dict(query(t.ARRIVALS,op='benchmark_gap',towns=['046005']),benchmark='italy'),'tourism_benchmark_scope_or_period_not_reviewed')
    rejected(e,query(t.PRESENCES,'normalized'),'dimension_adapter_not_implemented')
    mutations=[
     (t.ARRIVALS,lambda g,m:m['rows'][0].update(town='Camaiore')),
     (t.PRESENCES,lambda g,m:m['rows'][0].update(value=None)),
     (t.STAY,lambda g,m:m['rows'][0].update(value=3.81)),
     (t.FOREIGN,lambda g,m:m['rows'][0].update(value=18130/37898*100)),
     (t.FOREIGN,lambda g,m:m['aggregate'].update(value=totals[2]/totals[1]*100)),
     (t.ARRIVALS,lambda g,m:m['rows'].append(dict(m['rows'][0]))),
     (t.BEDS,lambda g,m:m['meta'].update(year='2025')),
     (t.BED_RATE,lambda g,m:g._catalog['metrics']['population']['meta'].update(year='2024')),
     (t.BED_RATE,lambda g,m:g._catalog['metrics']['population']['rows'][0].update(value=21865)),
     (t.STRUCTURE_RATE,lambda g,m:m['meta']['sourceMeta'].update(populationSnapshot='different.json')),
     (t.BED_RATE,lambda g,m:m['aggregate'].update(value=sum(values(n)[t.BED_RATE] for n in FIXED.values())/7)),
     (t.BEDS,lambda g,m:m.update(sourceUrl='https://example.com/')),
    ]
    for key,mutate in mutations:
        g=QueryEngine(path,layer='effective');assert g.query(query(key))['status']=='computed';mutate(g,g._catalog['metrics'][key]);assert g.query(query(key))['status']=='not_computable'
    for key, native in ((t.ARRIVALS,t.MOVE),(t.BEDS,t.CAP),(t.BED_RATE,t.DEMO),(t.STRUCTURE_RATE,t.POSAS)):
        g=QueryEngine(path,layer='effective');assert g.query(query(key))['status']=='computed';s,ref=g.file(native);s['referenceYear']=2030;rejected(g,query(key),'tourism_frozen_input_changed')
        g=QueryEngine(path,layer='effective');g.file(native)[1]['sha256']='0'*64;rejected(g,query(key),'tourism_frozen_input_changed')
    g=QueryEngine(path,layer='effective');series=g._catalog['metrics'][t.ARRIVALS]['rows'][0].get('series')
    if series:
        series['years'][0]=2022;assert g.query(query(t.ARRIVALS))['status']=='not_computable'
    g=QueryEngine(path,layer='effective');m=g._catalog['metrics'][t.BEDS];m['meta']['benchmark']['year']='2025';rejected(g,dict(query(t.BEDS,op='benchmark_gap',towns=['046005']),benchmark='italy'),'tourism_benchmark_definition_changed')
    print(f'Tourism adapters PASS: {checked} fixed current observations, four native pooled ratios, ten official benchmarks; {replay} frozen historical cells replayed separately; precision/date/identity/cache and methodology guards')


if __name__=='__main__': regressions(ROOT/'dist/data/site-data.json')
