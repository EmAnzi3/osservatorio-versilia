"""Fixed transcription, separate historical replay, and regional refusal boundaries."""
import math
from semantic_query_engine import QueryEngine, ROOT
from test_semantic_query_engine import rejected
import semantic_query_regional_adapters as r

# Fixed municipal transcription: ind05, ind10, ind14, ind16, ind18, ind19.
FIXED = {
 '046005': (6.20175997079088,9.56569543705333,10.8166666666667,6.64996977286467,75,6.98158051099228),
 '046013': (7.88433291387651,7.4235807860262,7.5,5.27160210864084,35.294117647,5.71151984511133),
 '046018': (6.01649783701882,12.861136999068,13.7666666666667,8.71112201705417,33.333333333,8.70818915801615),
 '046024': (6.96695107846779,11.7123795404003,9.03333333333333,7.48098321493682,95,6.27537836840162),
 '046028': (6.73719009172747,14.3533123028391,8.7,7.84893641223979,6.6666666667,5.4421768707483),
 '046030': (7.75701353743076,13.4328358208955,21.2166666666667,10.3499260719566,54.545454545,5.23809523809524),
 '046033': (6.7105179355484,19.5686647637171,7.58333333333333,8.02992973811479,56.25,10.1537097250961),
}
BENCH = (5.8305374855463,24.0749483313925,14.9,5.73,33.6538461538462,8.9178377031752)
# Independently fixed Massarosa time cells, not obtained from QueryEngine output.
HISTORY = (
 [6.25,5.49,6.32,6.5,5.09,6.01649783701882],
 [11.64,12.15,12.33,13.19,15.5,13.18,12.861136999068],
 [11.4,12,12.2,13,13.7,13.42,13.7666666666667],
 [4.32,5.34,3.66,5.46,4.9,3.22,8.71112201705417],
 [0,33.333333333],
 [7.97,8.07,7.9,8.06,8.4,8.6,8.70818915801615],
)


def query(key, op='compare', **selection):
    return dict(operation=op, selectors=[dict(metric=key, **selection)])


def regressions(path):
    e=QueryEngine(path,layer='effective');checked=0;replay=0
    for i,key in enumerate(r.KEYS):
        q=e.query(query(key));assert q['status']=='computed',q
        for o in q['observations']:
            assert math.isclose(o['value'],FIXED[o['geography']][i],rel_tol=0,abs_tol=1e-9)
            assert o['period']==r.year(key) and o['unit']==r.UNITS[key]
            assert o['nativeComponentsAvailable'] is False and 'numerator' not in o and 'denominator' not in o
            assert o['provenance'][1]['recordPointer'] and o['definition'] and o['population'];checked+=1
        rank=e.query(query(key,op='rank'));assert rank['status']=='computed',rank
        top=max(FIXED,key=lambda code:FIXED[code][i]);assert rank['result']['ranking'][0]['geography']==top
        gap=e.query(dict(query(key,op='benchmark_gap',towns=['046005']),benchmark='tuscany'));assert gap['status']=='computed',gap
        assert math.isclose(gap['observations'][1]['value'],BENCH[i],rel_tol=0,abs_tol=1e-9)
        assert 'official published regional row' in gap['observations'][1]['benchmarkAggregation']
        hist=e.query(query(key,op='series',towns=['046018']));assert hist['status']=='computed',hist
        assert [o['value'] for o in hist['observations']]==HISTORY[i]
        assert [o['period'] for o in hist['observations']]==list(map(str,r.years(key)))
        # Replay other frozen cells separately; not a new source acquisition.
        s,_=e.file(r.SERVICES if key==r.ONLINE else r.NATIVE)
        for code,name in r.TOWNS.items():
            h=e.query(query(key,op='series',towns=[code]));assert h['status']=='computed',h
            vals=[s['towns'][name][str(y)] for y in r.years(key)] if key==r.ONLINE else next(n['values'] for n in s['indicators'][key]['rows'] if n['code']==code)
            assert [o['value'] for o in h['observations']]==vals;replay+=len(vals)
        for op in ('trend','absolute_change','relative_change','percentage_points'):
            rejected(e,query(key,op=op,towns=['046018']),'regional_temporal_continuity_not_reviewed')
        rejected(e,query(key,op='weighted_ratio'),'regional_native_components_or_joint_distribution_not_frozen')
        rejected(e,query(key,op='anomaly'),'regional_peer_anomaly_not_reviewed')
        rejected(e,query(key,periods=['2025']),'regional_period_not_frozen')
        rejected(e,query(key,dimension='numerator'),'dimension_adapter_not_implemented')
        rejected(e,dict(query(key,op='benchmark_gap',towns=['046018']),benchmark='italy'),'regional_benchmark_scope_or_period_not_reviewed')
        for selectors in ([{'metric':key},{'metric':'population'}],[{'metric':'population'},{'metric':key}]):
            rejected(e,dict(operation='correlation',selectors=selectors,axis='municipalities',method='pearson',purpose='descriptive'),'regional_pair_not_jointly_reviewed')
        mutations=[lambda m:m['meta'].update(year='2025'),lambda m:m['meta'].update(unit='number'),lambda m:m.update(sourceUrl='https://example.com'),lambda m:m['rows'][0].update(code='046005'),lambda m:m['rows'][0].update(value=1),lambda m:m['rows'][0]['series']['values'].__setitem__(0,999),lambda m:m['aggregate'].update(value=999),lambda m:m['rows'][0].update(ratioComponents={'numerator':1,'denominator':10}),lambda m:m['rows'][0].update(notApplicable=True)]
        for mutation in mutations:
            g=QueryEngine(path,layer='effective');assert g.query(query(key))['status']=='computed';mutation(g._catalog['metrics'][key]);assert g.query(query(key))['status']=='not_computable'
        for field,value in [('year','2025'),('italy',10),('tuscany',1),('sourceSnapshot','other.json')]:
            g=QueryEngine(path,layer='effective');g._catalog['metrics'][key]['meta']['benchmark'][field]=value
            assert g.query(dict(query(key,op='benchmark_gap',towns=['046018']),benchmark='tuscany'))['status']=='not_computable'
    rejected(e,query(r.YOUTH,op='series',towns=['046018'],periods=['2020']),'regional_period_not_frozen')
    rejected(e,query(r.ONLINE,periods=['2024']),'regional_period_not_frozen')
    rejected(e,dict(query(r.ONLINE,op='benchmark_gap',towns=['046018'],periods=['2018']),benchmark='tuscany'),'regional_benchmark_scope_or_period_not_reviewed')
    for key,path_ in [(r.YOUTH,r.NATIVE),(r.ONLINE,r.SERVICES),(r.EMS,r.BENCHMARK)]:
        g=QueryEngine(path,layer='effective');q=dict(query(key,op='benchmark_gap',towns=['046018']),benchmark='tuscany');assert g.query(q)['status']=='computed'
        g.file(path_)[0]['unexpectedMutation']=True;rejected(g,q,'regional_frozen_input_changed')
        g=QueryEngine(path,layer='effective');g.file(path_)[1]['sha256']='0'*64;rejected(g,q,'regional_frozen_input_changed')
    print(f'Regional adapters PASS: {checked} fixed current observations, six fixed regional benchmarks and 36 fixed Massarosa historical cells; {replay} frozen historical cells replayed separately; definitions, no inferred components, identities, cached input and refusal guards')


if __name__=='__main__':regressions(ROOT/'dist/data/site-data.json')
