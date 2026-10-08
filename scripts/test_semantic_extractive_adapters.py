"""Independent RTCave counts, PRC tables, annual volumes and adversarial controls."""
import copy,math
from semantic_query_engine import QueryEngine,ROOT
from test_semantic_query_engine import request,rejected
import semantic_query_extractive_adapters as x
# total, seven statuses, three types, three production classes: independent reviewed counts.
SITES={'046005':(0,)*14,'046013':(0,)*14,'046018':(1,0,1,0,0,0,0,0,1,0,0,0,1,0),'046024':(2,0,0,0,0,0,2,0,2,0,0,2,0,0),'046028':(44,6,0,4,1,0,33,0,43,1,0,44,0,0),'046030':(43,9,1,1,2,0,29,1,36,1,6,42,0,1),'046033':(0,)*14}
# area km2; G/GP/ACC count, hectares, published percent; MOS/pMOS/SED.
PLAN={'046005':(84.69,(0,0,0),(0,0,0),(0,0,0),2,3,25),'046013':(9.14,(0,0,0),(0,0,0),(0,0,0),0,0,0),'046018':(68.56,(0,0,0),(0,0,0),(0,0,0),0,0,53),'046024':(41.99,(0,0,0),(1,11.39,.271),(0,0,0),0,0,22),'046028':(39.36,(2,37.976,.965),(0,0,0),(7,156.322,3.971),1,7,105),'046030':(80.7,(1,19.021,.236),(0,0,0),(12,400.173,4.959),4,0,151),'046033':(32.42,(0,0,0),(0,0,0),(0,0,0),0,0,0)}
PROD={'046028':[31151,46093,52048,57199,53518,53194,55801],'046030':[19894,13619,17804,31658,25328,38372,23651]}

def expected(key,dim,code):
 if key==x.KEYS[0]:return SITES[code][x.dimensions(key).index(dim)]
 if key==x.KEYS[1]:return PROD[code][-1]
 p=PLAN[code];f=x.field(key,dim)
 if f in ('mos','pmos','sed'):return p[('mos','pmos','sed').index(f)+4]
 c,u=f.split('_');v=p[('g','gp','acc').index(c)+1]
 return v[1]/p[0] if dim.startswith('share:') else v[('n','ha','pct').index(u)]

def regressions(path):
 e=QueryEngine(path,layer='effective');checks=0
 for key in x.KEYS:
  if key not in e._catalog['metrics']:continue
  for dim in x.dimensions(key):
   q=request('compare',key,dimension=dim)
   if key==x.KEYS[1]:rejected(e,q,'partial_coverage_requires_opt_in');q['allowPartial']=True
   r=e.query(q);assert r['status']=='computed',r
   assert len(r['excluded'])==(5 if key==x.KEYS[1] else 0)
   for o in r['observations']:
    for ev in o['provenance']:
     node=e._catalog if ev['kind']=='catalog_snapshot' else e.file(ev['path'])[0]
     for p in ev.get('valuePointer',ev.get('recordPointer')).split('/')[1:]:node=node[int(p)] if isinstance(node,list) else node[p]
     assert len(ev['sha256'])==64
    assert not o['notApplicable']
    if o['value'] is None:assert o['dataUnavailable'] and o['geography'] not in PROD;continue
    assert math.isclose(o['value'],expected(key,dim,o['geography']),rel_tol=0,abs_tol=1e-8),(key,dim,o);checks+=1
   if x.weighted(key,dim):
    r=e.query(request('weighted_ratio',key,dimension=dim));assert r['status']=='computed',r
    c=('g','gp','acc').index(dim.split(':')[1])+1;v=math.fsum(p[c][1] for p in PLAN.values())/math.fsum(p[0] for p in PLAN.values())
    assert math.isclose(r['result']['value'],v,rel_tol=0,abs_tol=1e-8)
   else:rejected(e,request('weighted_ratio',key,dimension=dim),'extractive_verified_area_ratio_required')
   rejected(e,dict(request('benchmark_gap',key,dimension=dim,towns=['046028']),benchmark='versilia'),'extractive_totals_not_municipal_reference')
  for op in ('absolute_change','relative_change','percentage_points','trend'):rejected(e,request(op,key,towns=['046028']),'extractive_history_continuity_not_reviewed')
  if key!=x.KEYS[1]:rejected(e,request('series',key,towns=['046028']),'extractive_history_continuity_not_reviewed')
  rejected(e,request('anomaly',key),'extractive_anomaly_not_reviewed')
  rejected(e,dict(operation='correlation',selectors=[dict(metric=key),dict(metric='population')],method='spearman',axis='municipalities',purpose='descriptive',allowPartial=True),'extractive_universes_not_jointly_comparable')
  r=e.query(dict(request('rank',key),allowPartial=True));assert r['status']=='computed',r
  rejected(e,request('compare',key,periods=['2027']),'extractive_period_not_frozen')
  g=QueryEngine(path,layer='effective');next(r for r in g._catalog['metrics'][key]['rows'] if r['code']=='046028')['value']=None
  rejected(g,request('compare',key),'partial_coverage_requires_opt_in');r=g.query(dict(request('compare',key),allowPartial=True));assert r['status']==('not_computable' if key==x.KEYS[1] else 'computed'),r
 for code,values in PROD.items():
  r=e.query(request('series',x.KEYS[1],towns=[code]));assert r['status']=='computed' and [o['value'] for o in r['observations']]==values,r;checks+=7
 r=e.query(request('series',x.KEYS[1],towns=['046018']));assert r['status']=='not_computable' and all(o['dataUnavailable'] and not o['notApplicable'] for o in r['observations']),r
 for mode,reason in [('duplicate','extractive_duplicate_or_invalid_records'),('identity','extractive_native_identity_changed'),('category','extractive_unreviewed_native_category'),('hash','extractive_native_reference_changed'),('denominator','extractive_invalid_native_components'),('negativeArea','extractive_invalid_native_components'),('fractionalCount','extractive_invalid_native_components'),('areaSum','extractive_catalog_source_mismatch'),('percent','extractive_catalog_source_mismatch'),('crs','extractive_planning_method_changed'),('years','extractive_production_period_or_identity_changed'),('volume','extractive_catalog_source_mismatch'),('cohort','extractive_production_cohort_changed'),('publicRecords','extractive_public_records_changed'),('publicPlan','extractive_public_components_changed'),('missingZero','extractive_missing_production_not_zero')]:
  g=QueryEngine(path,layer='effective');s,ref=g.file(x.NATIVE);s=copy.deepcopy(s);key=x.KEYS[0];n=s['prc']['towns']['046028']
  if mode=='duplicate':s['rtcave']['records'][1]['codice_rt']=s['rtcave']['records'][0]['codice_rt']
  elif mode=='identity':s['rtcave']['records'][0]['nome_comune']='Massarosa'
  elif mode=='category':s['rtcave']['records'][0]['stato']='Dismessa'
  elif mode=='hash':s['rtcave']['sha256']='0'*64
  elif mode=='denominator':n['municipalKm2']=0
  elif mode=='negativeArea':n['g'][1]=-1
  elif mode=='fractionalCount':n['g'][0]=2.5
  elif mode=='areaSum':s['prc']['aggregate']['g'][1]+=1
  elif mode=='percent':n['acc'][2]+=.01
  elif mode=='crs':s['prc']['crs']='EPSG:4326'
  elif mode=='years':s['production']['046028']['years'][0]=2018
  elif mode=='volume':s['production']['046030']['components'][0]['cardosoApuane']+=1
  elif mode=='cohort':s['production']['046018']=copy.deepcopy(s['production']['046028'])
  elif mode=='publicRecords':next(r for r in g._catalog['metrics'][key]['rows'] if r['code']=='046028')['extractiveDetail']['records'].pop()
  elif mode=='publicPlan':key=x.KEYS[2];next(r for r in g._catalog['metrics'][key]['rows'] if r['code']=='046028')['prcDetail']['g'][1]+=1
  elif mode=='missingZero':key=x.KEYS[1];next(r for r in g._catalog['metrics'][key]['rows'] if r['code']=='046018')['value']=0
  g.files[x.NATIVE]=(s,ref);rejected(g,dict(request('compare',key),allowPartial=True),reason)
 print(f'A6 extractive PASS: {checks} fixed-reference observations including alias and 14 historical values; RTCave unique records, PRC published/rounded-derived percentages distinct, 2/7 extraction coverage, native components and adversarial guards')
if __name__=='__main__':regressions(ROOT/'dist/data/site-data.json')
