"""Independent census references and adversarial agricultural scope guards."""
import copy
import math
from semantic_query_engine import QueryEngine,ROOT
from test_semantic_query_engine import request,rejected
import semantic_query_agriculture_adapters as a

# Transcribed native carriers: HO, center SAU, FUAA, localized SAU, area km2, IA.
ROWS={'046005':(319,699.11,314,589.78,85.4275,126.58),'046013':(7,22.76,7,19.29,9.1872,.6),
      '046018':(192,985.12,191,1370.61,68.2379,241.67),'046024':(187,384.95,180,329.33,42.1153,44.84),
      '046028':(64,95.54,62,86.33,39.4678,11.3),'046030':(44,139.47,42,175.32,80.1265,2.92),
      '046033':(146,578.6,141,297.78,32.5275,95.85)}
CROPS={'046005':(342.64,115.45,.3,9.42,85.78),'046013':(.83,.6,None,None,16.92),
       '046018':(888.46,165.77,.23,4.09,274.85),'046024':(173.68,104.87,.1,3.96,28.63),
       '046028':(28.79,21.76,1.,5.38,22.48),'046030':(54.62,5.58,None,.45,99.38),
       '046033':(228.37,6.82,None,1.07,13.46)}

def regressions(path):
 e=QueryEngine(path,layer='effective');count=0
 for key in a.KEYS:
  for dim in a.dimensions(key):
   r=e.query(dict(request('compare',key,dimension=dim),allowPartial=True));assert r['status']=='computed',r
   for o in r['observations']:
    farms,center,withsau,localized,area,irrigated=ROWS[o['geography']]
    expected=farms if key=='agriculturalFarms' else center/withsau if key=='averageAgriculturalFarmSize' else localized/(area*100)*100 if key=='agriculturalUsedArea' and dim=='view:normalized' else irrigated/center*100 if key=='irrigatedAgriculturalArea' and dim=='view:normalized' else irrigated if key=='irrigatedAgriculturalArea' else CROPS[o['geography']][a.CROPS.index(dim[5:])] if key=='cropProfile' and dim!='total' else localized
    assert o['value'] is None if expected is None else math.isclose(o['value'],expected,abs_tol=1e-8)
    assert o['period']=='2020' and all(len(p['sha256'])==64 for p in o['provenance']);count+=1
   if a.weighted(key,dim):
    r=e.query(request('weighted_ratio',key,dimension=dim));assert r['status']=='computed',r
    numerator=sum(v[1] if key=='averageAgriculturalFarmSize' else v[3] if key=='agriculturalUsedArea' else v[5] for v in ROWS.values())
    denominator=sum(v[2] if key=='averageAgriculturalFarmSize' else v[4]*100 if key=='agriculturalUsedArea' else v[1] for v in ROWS.values());scale=1 if key=='averageAgriculturalFarmSize' else 100
    assert math.isclose(r['result']['value'],numerator/denominator*scale,abs_tol=1e-8)
   else:rejected(e,request('weighted_ratio',key,dimension=dim),'verified_ratio_adapter_required')
  rejected(e,request('series',key,towns=['046018']),'agriculture_single_census_no_history')
  rejected(e,request('trend',key,towns=['046018'],periods=['2010','2020']),'agriculture_single_census_no_history')
  rejected(e,request('compare',key,periods=['2026']),'agriculture_period_not_frozen')
 for scope,n,d in [('tuscany',651434.43,51621),('italy',12431807.72,1120504)]:
  r=e.query(dict(request('benchmark_gap','averageAgriculturalFarmSize',towns=['046018']),benchmark=scope));assert r['status']=='computed',r
  assert math.isclose(r['result']['value'],985.12/191-n/d,abs_tol=1e-8);count+=1
 for key in ('agriculturalFarms','agriculturalUsedArea','irrigatedAgriculturalArea','cropProfile'):
  rejected(e,dict(request('benchmark_gap',key,towns=['046018']),benchmark='tuscany'),'agriculture_benchmark_extent_or_normalization_not_comparable')
 rejected(e,request('compare','cropProfile',dimension='part:OLIVTTR'),'partial_coverage_requires_opt_in')
 r=e.query(dict(request('compare','cropProfile',dimension='part:OLIVTTR'),allowPartial=True));assert len(r['excluded'])==3
 pair=dict(operation='correlation',selectors=[{'metric':'agriculturalUsedArea'},{'metric':'irrigatedAgriculturalArea'}],axis='municipalities',method='spearman',purpose='Review agricultural scopes')
 rejected(e,pair,'agriculture_localized_and_center_scopes_not_jointly_comparable')
 pair['selectors'][0]['metric']='agriculturalFarms';r=e.query(pair);assert r['status']=='computed' and 'association_not_causation' in r['warnings']
 for what,reason in [('scope','agriculture_geographic_scope_changed'),('denominator','agriculture_positive_denominator_required'),('count','agriculture_invalid_native_count')]:
  f=QueryEngine(path,layer='effective');snap,ref=f.file(a.SNAPSHOT);snap=copy.deepcopy(snap)
  if what=='scope':snap['sources']['localizedCrops']['perspective']='centro aziendale'
  elif what=='denominator':snap['towns']['046018']['farmsWithSau']=0
  else:snap['towns']['046018']['farmsWithSau']=193
  f.files[a.SNAPSHOT]=(snap,ref);rejected(f,request('compare','averageAgriculturalFarmSize'),reason)
 f=QueryEngine(path,layer='effective');f._catalog['metrics']['agriculturalFarms']['rows'][0]['value']=None
 rejected(f,request('compare','agriculturalFarms',periods=['2020']),'partial_coverage_requires_opt_in')
 f=QueryEngine(path,layer='effective');f._catalog['metrics']['irrigatedAgriculturalArea']['rows'][0]['sourceBackedComponents']['denominator']=1370.61
 rejected(f,request('compare','irrigatedAgriculturalArea',dimension='view:normalized'),'agriculture_source_or_component_mismatch')
 f=QueryEngine(path,layer='effective');snap,ref=f.file(a.BENCHMARK);snap=copy.deepcopy(snap);snap['qualityGate']['status']='FAIL';f.files[a.BENCHMARK]=(snap,ref)
 rejected(f,dict(request('benchmark_gap','averageAgriculturalFarmSize',towns=['046018']),benchmark='tuscany'),'agriculture_benchmark_gate_changed')
 print(f'A6 agriculture PASS: {count} independent observations, three native pooled ratios, crop nulls and scope/denominator adversarial guards')

if __name__=='__main__':regressions(ROOT/'dist/data/site-data.json')
