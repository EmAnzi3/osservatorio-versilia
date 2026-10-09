"""Fixed independently computed climate references and external-storage boundaries."""
import copy,math
from pathlib import Path
from semantic_query_engine import QueryEngine,ROOT
from test_semantic_query_engine import request,rejected
import semantic_query_climate_adapters as x
# Four exact annual 2025 values; four OLS 50-year changes (Decimal centred at 2000);
# precipitation fitted-start percentage. These are not rewritten from engine outputs.
VALUES={
'046005':(15.739,1705.,12.359,19.491,2.0643574660633486,-38.33212669683258,1.94210407239819,2.047009049773756,-2.5249196500866837),
'046013':(17.353,1486.2,13.848,21.321,2.0973348416289594,-34.15248868778281,2.0085927601809956,2.053185520361991,-2.5463574053179086),
'046018':(16.619,1336.5,12.656,20.959,2.0463257918552036,-18.600904977375567,1.948846153846154,2.0293574660633484,-1.60928437711153),
'046024':(16.726,1596.3,13.29,20.616,2.078782805429864,-42.41628959276018,1.9879276018099548,2.0424660633484164,-2.9801486619639053),
'046028':(14.486,1987.6,11.479,17.899,2.0766787330316743,-99.28054298642535,1.9764162895927602,2.0754660633484163,-5.37614823967348),
'046030':(13.196,2239.8,10.433,16.333,2.062027149321267,-83.24298642533937,1.8785339366515836,2.1337239819004523,-3.9289181054134863),
'046033':(16.869,1269.4,12.882,21.244,2.0360678733031676,-31.838009049773756,1.9491357466063348,2.011823529411765,-2.9491273231506483)}

def regressions(path):
 e=QueryEngine(path,layer='effective');checks=replayed=0
 for i,key in enumerate(x.KEYS):
  for dim in x.dimensions(key):
   r=e.query(request('compare',key,dimension=dim));assert r['status']=='computed',r
   for o in r['observations']:
    expected=VALUES[o['geography']][i if dim=='total' else 4+i if dim==x.TREND else 8]
    assert math.isclose(o['value'],expected,rel_tol=0,abs_tol=1e-8),(key,dim,o);checks+=1
    assert o['period']==x.default_period(dim) and not o['dataUnavailable']
    assert o['unit']==('percent' if dim==x.PERCENT else 'mm' if i==1 else 'celsius')
    for ev in o['provenance']:
     assert len(ev['sha256'])==64
     if 'valuePointer' not in ev:continue
     node=e._catalog if ev['kind']=='catalog_snapshot' else e.file(ev['path'])[0]
     for p in ev['valuePointer'].split('/')[1:]:node=node[int(p)] if isinstance(node,list) else node[p]
   assert e.query(request('rank',key,dimension=dim))['status']=='computed'
  for code in VALUES:
   r=e.query(request('series',key,towns=[code]));assert r['status']=='computed',r
   source=e.file(x.path(key))[0]['municipalities'];name=next(t['name'] for t in e._catalog['towns'] if t['code']==code)
   assert len(r['observations'])==(76 if i<2 else 51)
   assert [o['period'] for o in r['observations']]==list(map(str,source[name]['years']))
   assert [o['value'] for o in r['observations']]==source[name][x.field(key)];replayed+=len(r['observations'])
   if i>=2:
    trend=e.query(request('trend',key,towns=[code]));assert trend['status']=='computed',trend
    assert math.isclose(trend['result']['slope'],VALUES[code][4+i]/50,rel_tol=0,abs_tol=1e-10)
    q=request('absolute_change',key,towns=[code],periods=['1975','2025']);a=e.query(q);assert a['status']=='computed'
    assert math.isclose(a['result']['value'],source[name][x.field(key)][-1]-source[name][x.field(key)][0],abs_tol=1e-10)
   else:
    for op in ('trend','absolute_change'):rejected(e,request(op,key,towns=[code]),'climate_stitched_sources_no_arbitrary_temporal_change')
  for op,reason in [('relative_change','climate_relative_change_not_reviewed_celsius_not_ratio_scale'),('weighted_ratio','climate_no_native_spatial_components_for_pooling'),('benchmark_gap','climate_normals_are_temporal_not_geographic_benchmarks'),('anomaly','climate_peer_anomaly_not_reviewed'),('percentage_points','climate_annual_values_not_percentages')]:
   rejected(e,request(op,key,towns=['046018']),reason)
  rejected(e,request('series',key,dimension=x.TREND,towns=['046018']),'climate_fitted_window_is_not_annual_series')
  rejected(e,request('compare',key,periods=['2026']),'climate_annual_period_not_frozen')
  rejected(e,request('compare',key,periods=['1975–2025']),'climate_annual_period_not_frozen')
  rejected(e,request('compare',key,dimension=x.TREND,periods=['2025']),'climate_fitted_window_period_required')
  if i>=2:rejected(e,request('compare',key,periods=['1950']),'climate_annual_period_not_frozen')
  rejected(e,dict(operation='correlation',selectors=[dict(metric=key),dict(metric='floodRiskArea')],axis='municipalities',method='spearman',purpose='descriptive'),'climate_pair_not_jointly_reviewed')
  for mode in ('year','value','null','calibration','hash','metadata','inline','identity'):
   g=QueryEngine(path,layer='effective');s,ref=g.file(x.path(key));s=copy.deepcopy(s);ref=copy.deepcopy(ref)
   reason='climate_frozen_series_changed'
   if mode=='year':s['municipalities']['Massarosa']['years'][0]+=1
   elif mode=='value':s['municipalities']['Massarosa'][x.field(key)][0]+=1
   elif mode=='null':s['municipalities']['Massarosa'][x.field(key)][0]=None
   elif mode=='calibration':s['method']='slope corrected'
   elif mode=='hash':ref['sha256']='0'*64
   elif mode=='metadata':g._catalog['metrics'][key]['dataStorage']['trendFrom']=1980;reason='climate_external_catalog_contract_changed'
   elif mode=='inline':g._catalog['metrics'][key]['rows']=[{'value':0}];reason='climate_external_catalog_contract_changed'
   elif mode=='identity':g._catalog['towns'][0]['code']=g._catalog['towns'][1]['code'];reason='climate_native_cohort_changed'
   g.files[x.path(key)]=(s,ref);rejected(g,request('compare',key),reason)
 # A validation cached during one query cannot hide mutation before the next query.
 g=QueryEngine(path,layer='effective');assert g.query(request('compare',x.KEYS[2]))['status']=='computed'
 g.file(x.MINMAX)[0]['municipalities']['Massarosa']['tmin'][0]+=1
 rejected(g,request('compare',x.KEYS[2]),'climate_frozen_series_changed')
 assert checks==63 and replayed==1778
 print(f'A6 climate PASS: {checks} fixed annual/fitted references, {replayed} frozen annual cells replayed; homogeneous minmax slopes, native periods, source/runtime distinction and adversarial refusals')

if __name__=='__main__':regressions(ROOT/'dist/data/site-data.json')
