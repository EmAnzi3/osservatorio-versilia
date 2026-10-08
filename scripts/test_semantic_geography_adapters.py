"""Independent geography references, precision checks and mixed-period guards."""
import copy
import math
from semantic_query_engine import QueryEngine,ROOT
from test_semantic_query_engine import request,rejected
import semantic_query_geography_adapters as g

# Surface 2021, residents January 1 2026, forest hectares, published forest index,
# altitude min/mean/max and eight official bands (four decimal precision).
ROWS={
 '046005':(84.6916646245,31763,4552.534,53.754,(-5,283.256624803002,1187),(62.0361,23.1885,11.1745,3.6009,0,0,0,0)),
 '046013':(9.18671486427,6550,23.576,2.566,(-5,3.43602605375458,13),(100,0,0,0,0,0,0,0)),
 '046018':(68.2455922649,21782,1513.583,22.178,(-8,62.603001736041,461),(96.0388,3.9612,0,0,0,0,0,0)),
 '046024':(42.2685463205,22678,1177.275,27.852,(-6,105.019245473328,726),(86.2203,12.8774,.9022,0,0,0,0,0)),
 '046028':(39.4677282042,12284,2902.367,73.538,(-3,546.584067560508,1553),(31.6164,26.0337,20.1453,16.426,5.6358,.1428,0,0)),
 '046030':(80.639757592,2783,6934.268,85.991,(73,784.096788486609,1860),(5.8841,24.2606,33.5819,27.0372,8.0119,1.2243,0,0)),
 '046033':(32.7261333045,60680,580.067,17.725,(-5,2.44748310490747,21),(100,0,0,0,0,0,0,0)),
}
BENCHMARKS={'tuscany':(22989.775575942836,273,3659222,47.407879965451585),
 'italy':(302109.5696553943,7904,58942828,53.60951619684477)}

def regressions(path):
 e=QueryEngine(path,layer='effective');count=0
 for key in g.KEYS:
  for dim in g.dimensions(key):
   r=e.query(request('compare',key,dimension=dim));assert r['status']=='computed',r
   for o in r['observations']:
    area,pop,forest,index,stats,bands=ROWS[o['geography']]
    expected=area if key=='municipalSurface' else pop/area if key=='populationDensity' else forest if dim=='view:hectares' else index if key=='forestCoverIndex' else stats[('min','mean','max').index(dim[5:])] if dim.startswith('stat:') else bands[g.BANDS.index(dim[5:])] if dim.startswith('part:') else round(sum(bands[1:]),1)
    if key=='forestCoverIndex' and dim=='total':
     assert o['publishedValue']==index;expected=forest/(area*100)*100
    assert math.isclose(o['value'],expected,rel_tol=0,abs_tol=1e-8),(o,expected)
    assert o['period']==g.token(key,g.YEARS[key]) and all(len(p['sha256'])==64 for p in o['provenance']);count+=1
    if key=='populationDensity':assert o['numeratorPeriod']=='2026' and o['denominatorPeriod']=='2021'
   if g.weighted(key,dim):
    r=e.query(request('weighted_ratio',key,dimension=dim));assert r['status']=='computed',r
    n=sum(v[1] if key=='populationDensity' else v[2] for v in ROWS.values());d=sum(v[0] if key=='populationDensity' else v[0]*100 for v in ROWS.values());scale=1 if key=='populationDensity' else 100
    assert math.isclose(r['result']['value'],n/d*scale,abs_tol=1e-8)
   else:rejected(e,request('weighted_ratio',key,dimension=dim),'verified_ratio_adapter_required')
  rejected(e,request('series',key,towns=['046018']),'geography_history_not_frozen')
  rejected(e,request('compare',key,periods=['2025']),'geography_period_not_frozen')
 for scope,(area,municipalities,pop,altitude) in BENCHMARKS.items():
  for key in g.KEYS[:3]:
   r=e.query(dict(request('benchmark_gap',key,towns=['046018']),benchmark=scope));assert r['status']=='computed',r
   expected=(ROWS['046018'][0]-area/municipalities if key=='municipalSurface' else ROWS['046018'][1]/ROWS['046018'][0]-pop/area if key=='populationDensity' else 4-altitude)
   assert math.isclose(r['result']['value'],expected,abs_tol=1e-8);count+=1
 rejected(e,dict(request('benchmark_gap','forestCoverIndex',towns=['046018']),benchmark='tuscany'),'geography_benchmark_dimension_not_frozen')
 rejected(e,dict(request('benchmark_gap','altitudeProfile',towns=['046018'],dimension='part:0_299'),benchmark='italy'),'geography_benchmark_dimension_not_frozen')
 f=QueryEngine(path,layer='effective');f._catalog['metrics']['municipalSurface']['rows'][0]['value']=None
 rejected(f,request('compare','municipalSurface'),'partial_coverage_requires_opt_in')
 r=f.query(dict(request('compare','municipalSurface'),allowPartial=True));assert len(r['excluded'])==1
 for key,which,reason in [('municipalSurface','date','geography_native_reference_changed'),('municipalSurface','area','geography_invalid_native_components'),('altitudeProfile','band','altitude_partition_changed'),('altitudeProfile','summary','geography_source_or_component_mismatch'),('forestCoverIndex','forestDate','forest_reference_changed'),('forestCoverIndex','forestArea','geography_invalid_native_components')]:
  f=QueryEngine(path,layer='effective');p=g.FOREST if key=='forestCoverIndex' else g.GEO;snap,ref=f.file(p);snap=copy.deepcopy(snap)
  if which=='date':snap['referenceDate']='2026-12-31'
  elif which=='area':snap['municipalities']['Massarosa']['surfaceKm2']=0
  elif which=='band':snap['municipalities']['Massarosa']['altitudeBandsPct']['0_299']=95
  elif which=='summary':snap['municipalities']['Massarosa']['from300Pct']=5
  elif which=='forestDate':snap['reference']['forestMapNominalYear']=2026
  else:snap['municipalities']['Massarosa']['forestAreaHa']=99999
  f.files[p]=(snap,ref);rejected(f,request('compare',key),reason)
 f=QueryEngine(path,layer='effective');f._catalog['metrics']['population']['meta']['year']='2025'
 rejected(f,request('compare','populationDensity'),'density_population_period_changed')
 f=QueryEngine(path,layer='effective');snap,ref=f.file(g.BENCHMARK);snap=copy.deepcopy(snap);snap['qualityGate']['status']='FAIL';f.files[g.BENCHMARK]=(snap,ref)
 rejected(f,dict(request('benchmark_gap','populationDensity',towns=['046018']),benchmark='tuscany'),'geography_benchmark_gate_changed')
 print(f'A6 geography/forest PASS: {count} independent observations, mixed population/area dates, native pooled components, altitude rounding and adversarial guards')

if __name__=='__main__':regressions(ROOT/'dist/data/site-data.json')
