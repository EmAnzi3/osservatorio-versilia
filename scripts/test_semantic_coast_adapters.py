"""Literal coastal source inputs, independent arithmetic and adversarial universes."""
import copy, math
from semantic_query_engine import QueryEngine, ROOT
from test_semantic_query_engine import request, rejected
import semantic_query_coast_adapters as c

REFERENCE={
 '046005':(3.238942133,2.9440775904766894,.2117937358575105,2.91846344786501,.0100189572193096,.0795608627726403,2.82888362787306),
 '046013':(5.195521714,4.776514706292495,.20801519928834244,4.7692408179442705,.378408351146785,1.1059056060405954,3.28492686075689),
 '046024':(4.737747793,4.3444820108490285,.2137802007528477,4.3036029253380805,.0202974114120675,.033068293355833056,4.25023722057018),
 '046033':(13.598604591,8.689269742678789,0.,7.99007096439557,.117421940399078,.6979617723803617,7.17468725161613),
}

def expected(key,dimension,n):
 if key==c.KEYS[0]:return n[0],None,None
 if key==c.KEYS[1]:return (n[2]/n[1]*100,n[2],n[1]) if dimension=='total' else (n[2] if dimension=='view:protectedKm' else n[1],None,None)
 category='erosion' if dimension=='total' else dimension.split(':',1)[1]
 if dimension=='view:analysedKm':return n[3],None,None
 num=n[4+c.CATEGORIES.index(category)]
 return (num,None,None) if dimension.startswith('kilometres:') else (num/n[3]*100,num,n[3])

def regressions(path):
 e=QueryEngine(path,layer='effective');count=0
 for key in c.KEYS:
  if key not in e._catalog['metrics']:continue
  for dim in c.dimensions(key):
   rejected(e,request('compare',key,dimension=dim),'partial_coverage_requires_opt_in')
   r=e.query(dict(request('compare',key,dimension=dim),allowPartial=True));assert r['status']=='computed',r
   assert len(r['excluded'])==3 and all(x['reason']=='not_applicable' for x in r['excluded'])
   assert {o['geography'] for o in r['observations'] if o['value'] is not None}==set(REFERENCE)
   for o in r['observations']:
    for evidence in o['provenance']:
     node=e._catalog if evidence['kind']=='catalog_snapshot' else e.file(evidence['path'])[0]
     pointer=evidence.get('valuePointer',evidence.get('recordPointer'))
     for part in pointer.split('/')[1:]:node=node[int(part)] if isinstance(node,list) else node[part]
    if o['geography'] not in REFERENCE:
     assert o['value'] is None and o['notApplicable'] is True and o['dataUnavailable'] is False;continue
    value,num,den=expected(key,dim,REFERENCE[o['geography']]);assert math.isclose(o['value'],value,rel_tol=0,abs_tol=1e-8);count+=1
    assert all(len(x['sha256'])==64 for x in o['provenance']) and o['period']==c.PERIODS[key]
    if num is not None:assert o['numerator']==num and o['denominator']==den
   if c.weighted(key,dim):
    r=e.query(dict(request('weighted_ratio',key,dimension=dim),allowPartial=True));assert r['status']=='computed',r
    nums=[expected(key,dim,n)[1] for n in REFERENCE.values()];dens=[expected(key,dim,n)[2] for n in REFERENCE.values()]
    assert math.isclose(r['result']['value'],math.fsum(nums)/math.fsum(dens)*100,rel_tol=0,abs_tol=1e-8)
   else:rejected(e,request('weighted_ratio',key,dimension=dim),'coast_verified_ratio_required')
   if c.scopes(key,dim):
    for code,n in REFERENCE.items():
     for scope,v in [('tuscany',83.685/652.037*100),('italy',1516.2069999999999/8329.045000000002*100)]:
      r=e.query(dict(request('benchmark_gap',key,dimension=dim,towns=[code]),benchmark=scope));assert r['status']=='computed',r
      assert math.isclose(r['result']['value'],n[2]/n[1]*100-v,rel_tol=0,abs_tol=1e-8);count+=1
   else:rejected(e,dict(request('benchmark_gap',key,dimension=dim,towns=['046005']),benchmark='tuscany'),'coast_benchmark_not_comparable')
  for op in ('series','absolute_change','relative_change','trend','percentage_points'):rejected(e,request(op,key,towns=['046005']),'coast_history_not_frozen')
  rejected(e,request('compare',key,periods=['2026']),'coast_period_not_frozen')
  rejected(e,request('anomaly',key),'coast_anomaly_not_reviewed')
  r=e.query(dict(request('rank',key),allowPartial=True));assert r['status']=='computed',r
  rejected(e,dict(operation='correlation',selectors=[{'metric':key},{'metric':'population'}],allowPartial=True,method='spearman',axis='municipalities',purpose='descriptive'),'coast_universes_not_jointly_comparable')
  g=QueryEngine(path,layer='effective');row=next(r for r in g._catalog['metrics'][key]['rows'] if r['code']=='046005');row['value']=None
  rejected(g,request('compare',key,towns=list(c.COASTAL)),'partial_coverage_requires_opt_in')
  r=g.query(dict(request('compare',key,towns=list(c.COASTAL)),allowPartial=True));assert r['status']=='computed' and len(r['excluded'])==1
  g=QueryEngine(path,layer='effective');row=next(r for r in g._catalog['metrics'][key]['rows'] if r['code']=='046018');row['value']=0
  rejected(g,dict(request('compare',key),allowPartial=True),'coast_not_applicable_changed')
 for mode,reason in [('denominator','coast_invalid_native_components'),('partition','coast_catalog_source_mismatch'),('public','coast_public_components_changed'),('definition','coast_native_definition_changed'),('identity','coast_row_identity_changed'),('hash','coast_native_reference_changed'),('bench','coast_catalog_source_mismatch')]:
  key=c.KEYS[1] if mode in ('denominator','public','identity','hash','bench') else c.KEYS[2];g=QueryEngine(path,layer='effective');s,ref=g.file(c.NATIVE);s=copy.deepcopy(s)
  family='rigidDefenceProtectedCoast2020' if key==c.KEYS[1] else 'shorelineDynamics2006_2020';n=s[family]['towns']['046005']
  if mode=='denominator':n['coastKm']=0
  elif mode=='partition':n['stableKm']+=1
  elif mode=='public':next(r for r in g._catalog['metrics'][key]['rows'] if r['code']=='046005')['coastDetail']['coastKm']+=1
  elif mode=='definition':s[family]['definition']['erosion']='Arretramento superiore a 1 m'
  elif mode=='identity':n['name']='Massarosa'
  elif mode=='hash':s['sources']['ispraProtectedCoast']['sha256']='0'*64
  else:
   b,br=g.file(c.BENCHMARK);b=copy.deepcopy(b);b['components']['toscana']['protectedKm']+=1;g.files[c.BENCHMARK]=(b,br)
  g.files[c.NATIVE]=(s,ref)
  q=dict(request('benchmark_gap',key,towns=['046005']),benchmark='tuscany') if mode=='bench' else dict(request('compare',key),allowPartial=True)
  rejected(g,q,reason)
 if c.KEYS[0] in e._catalog['metrics']:
  g=QueryEngine(path,layer='effective');s,ref=g.file(c.LINE_BENCHMARK);s=copy.deepcopy(s);next(r for r in s['records'] if r['code']=='046005')['lengthKm']+=.01;g.files[c.LINE_BENCHMARK]=(s,ref)
  rejected(g,dict(request('compare',c.KEYS[0]),allowPartial=True),'coast_catalog_source_mismatch')
 print(f'A6 coast PASS: {count} fixed-reference observations including aliases and benchmark repetitions; independent coastal universes, 4 coastal/3 n.a., native length weighting, zero protection, interval and totals refusals')

if __name__=='__main__':regressions(ROOT/'dist/data/site-data.json')
