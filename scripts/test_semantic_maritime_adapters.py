"""Literal SID totals, exact component ratios, source pointers and territorial guards."""
import copy, math
from semantic_query_engine import QueryEngine, ROOT
from test_semantic_query_engine import request, rejected
import semantic_query_maritime_adapters as m

# Reviewed values, independent of the adapter's field map and query outputs.
FIXED={
 '046005':(130,124,28,1,852515.21,850257.45,6404.7),
 '046013':(187,161,76,2,1449307.39,1373433.51,5668.66),
 '046024':(123,116,8,1,1552876.15,1540796.44,12268.38),
 '046033':(359,174,156,12,2669422.99,1704536.28,3796.44)}

def expected(key,dim,code):
 total,tour,minimum,expiry,due,tour_due,median=FIXED[code]
 values={m.KEYS[0]:{'total':(total,None,None,1),'view:tourist':(tour,None,None,1),
  'share:tourist':(tour/total*100,tour,total,100),'view:minimumCount':(minimum,None,None,1),
  'share:minimum':(minimum/total*100,minimum,total,100),'view:expiryMissing':(expiry,None,None,1)},
 m.KEYS[1]:{'total':(due,None,None,1),'view:touristDue':(tour_due,None,None,1),
  'share:touristDue':(tour_due/due*100,tour_due,due,100),'view:mean':(due/total,due,total,1),
  'view:touristMean':(tour_due/tour,tour_due,tour,1),'view:median':(median,None,None,1)}}
 return values[key][dim]

def regressions(path):
 e=QueryEngine(path,layer='effective');checks=0
 for key in m.KEYS:
  if key not in e._catalog['metrics']:continue
  for dim in m.dimensions(key):
   rejected(e,request('compare',key,dimension=dim),'partial_coverage_requires_opt_in')
   r=e.query(dict(request('compare',key,dimension=dim),allowPartial=True));assert r['status']=='computed',r
   assert len(r['excluded'])==3 and {x['observation']['geography'] for x in r['excluded']}==set(m.NA)
   for o in r['observations']:
    for ev in o['provenance']:
     node=e._catalog if ev['kind']=='catalog_snapshot' else e.file(ev['path'])[0]
     for p in ev.get('valuePointer',ev.get('recordPointer')).split('/')[1:]:node=node[int(p)] if isinstance(node,list) else node[p]
     assert len(ev['sha256'])==64
    assert o['period']=='2026-08'
    if o['geography'] in m.NA:assert o['value'] is None and o['notApplicable'] and not o['dataUnavailable'];continue
    value,num,den,scale=expected(key,dim,o['geography']);checks+=1
    assert math.isclose(o['value'],value,rel_tol=0,abs_tol=1e-8),(key,dim,o)
    assert o['unit']==('percent' if dim.startswith('share:') else 'number' if key==m.KEYS[0] else 'currency2')
    assert 'sid_due_not_collected_or_municipal_revenue' in r['warnings']
    if num is not None:assert (o['numerator'],o['denominator'],o['scale'])==(num,den,scale)
   if m.weighted(key,dim):
    r=e.query(dict(request('weighted_ratio',key,dimension=dim),allowPartial=True));assert r['status']=='computed',r
    c=[expected(key,dim,code) for code in m.COASTAL]
    assert math.isclose(r['result']['value'],math.fsum(v[1] for v in c)/math.fsum(v[2] for v in c)*c[0][3],rel_tol=0,abs_tol=1e-8)
   else:rejected(e,request('weighted_ratio',key,dimension=dim),'maritime_median_not_additive' if dim=='view:median' else 'maritime_verified_ratio_required')
   rejected(e,dict(request('benchmark_gap',key,dimension=dim,towns=['046005']),benchmark='versilia'),'maritime_benchmark_not_reviewed')
  for op in ('series','absolute_change','relative_change','percentage_points','trend'):
   rejected(e,request(op,key,towns=['046005']),'maritime_previous_snapshots_not_harmonized')
  rejected(e,request('compare',key,periods=['2026']),'maritime_period_not_frozen')
  r=e.query(request('compare',key,towns=list(m.COASTAL),periods=['2026-08']));assert r['status']=='computed',r
  r=e.query(dict(request('rank',key),allowPartial=True));assert r['status']=='computed',r
  rejected(e,request('anomaly',key),'maritime_anomaly_not_reviewed')
  rejected(e,dict(operation='correlation',selectors=[{'metric':key},{'metric':'population'}],axis='municipalities',method='spearman',purpose='descriptive',allowPartial=True),'maritime_context_pair_not_reviewed')
  rejected(e,request('compare',key,dimension='view:occupiedSurface'),'dimension_adapter_not_implemented')
  g=QueryEngine(path,layer='effective');next(r for r in g._catalog['metrics'][key]['rows'] if r['code']=='046018')['value']=0
  rejected(g,dict(request('compare',key),allowPartial=True),'maritime_not_applicable_changed')
  g=QueryEngine(path,layer='effective');next(r for r in g._catalog['metrics'][key]['rows'] if r['code']=='046005')['value']=None
  rejected(g,request('compare',key,towns=list(m.COASTAL)),'partial_coverage_requires_opt_in')
  r=g.query(dict(request('compare',key,towns=list(m.COASTAL)),allowPartial=True));assert r['status']=='computed' and len(r['excluded'])==1,r
 for mode,reason in [
  ('identity','maritime_row_identity_changed'),('slug','maritime_row_identity_changed'),
  ('hash','maritime_native_reference_changed'),('status','maritime_deduplication_or_status_changed'),
  ('duplicateRows','maritime_deduplication_or_status_changed'),('unfrozen','maritime_deduplication_or_status_changed'),
  ('port','maritime_territorial_assignment_changed'),('duplicateId','maritime_territorial_assignment_changed'),
  ('removedId','maritime_territorial_assignment_changed'),('swappedId','maritime_territorial_assignment_changed'),('wrongTown','maritime_territorial_assignment_changed'),
  ('authority','maritime_territorial_assignment_changed'),('usage','maritime_catalog_source_mismatch'),
  ('fractional','maritime_invalid_native_components'),('negative','maritime_invalid_native_components'),
  ('touristTooLarge','maritime_invalid_native_components'),('mean','maritime_catalog_source_mismatch'),
  ('share','maritime_catalog_source_mismatch'),('public','maritime_public_components_changed'),
  ('parts','maritime_catalog_source_mismatch'),('cohort','maritime_native_cohort_changed')]:
  g=QueryEngine(path,layer='effective');s,ref=g.file(m.NATIVE);s=copy.deepcopy(s);n=s['towns']['Camaiore']
  row=next(r for r in g._catalog['metrics'][m.KEYS[0]]['rows'] if r['code']=='046005')
  a=s['quality']['territorialAssignment'];cap=a['nonMunicipalAssignments']['Capitaneria di Porto Viareggio']
  if mode=='identity':n['code']='046018'
  elif mode=='slug':row['slug']='massarosa'
  elif mode=='hash':s['source']['files']['concessioni-epsg4326.csv']['sha256']='0'*64
  elif mode=='status':s['quality']['allRowsStatus']='Scaduto'
  elif mode=='duplicateRows':s['quality']['perfectDuplicateRows']=0
  elif mode=='unfrozen':a['frozen']=False
  elif mode=='port':a['nonMunicipalAssignments']['Autorità Portuale Regione Toscana']['to']='Camaiore'
  elif mode=='duplicateId':cap['Camaiore'][0]=cap['Viareggio'][0]
  elif mode=='swappedId':cap['Camaiore'][0],cap['Viareggio'][0]=cap['Viareggio'][0],cap['Camaiore'][0]
  elif mode=='removedId':cap['Viareggio'].pop()
  elif mode=='wrongTown':cap['Camaiore'].append(cap['Viareggio'].pop())
  elif mode=='authority':a['municipalAuthorityCounts']['Camaiore']+=1
  elif mode=='usage':n['usageBreakdown'][0]['count']+=1
  elif mode=='fractional':n['minimumCanoneCount']=28.5
  elif mode=='negative':n['canoneDovutoEur']=-1
  elif mode=='touristTooLarge':n['touristRecreationalCanoneDovutoEur']=n['canoneDovutoEur']+1
  elif mode=='mean':n['meanCanoneEur']+=.1
  elif mode=='share':n['minimumCanoneShare']+=.01
  elif mode=='public':row['coastDetail']['medianCanoneEur']+=1
  elif mode=='parts':row['parts'][1]['value']+=1
  elif mode=='cohort':s['coverage']['coastalMunicipalities'].append('Massarosa')
  g.files[m.NATIVE]=(s,ref);rejected(g,dict(request('compare',m.KEYS[0]),allowPartial=True),reason)
 print(f'A6 maritime PASS: {checks} fixed-reference current observations; 4 coastal/3 n.a., frozen SID territorial assignment, exact native ratios/means, native median, due != receipts and adversarial guards')

if __name__=='__main__':regressions(ROOT/'dist/data/site-data.json')
