"""Independent reviewed SISBON counts and fail-closed mutation checks."""
import copy,math
from semantic_query_engine import QueryEngine,ROOT
from test_semantic_query_engine import request,rejected
import semantic_query_remediation_adapters as x
COUNTS={'046005':(9,22),'046013':(10,11),'046018':(6,10),'046024':(10,13),'046028':(3,6),'046030':(3,4),'046033':(15,30)}

def regressions(path):
 e=QueryEngine(path,layer='effective');checks=0
 for dim in x.dimensions(x.KEYS[0]):
  r=e.query(request('compare',x.KEYS[0],dimension=dim));assert r['status']=='computed',r
  for o in r['observations']:
   a,c=COUNTS[o['geography']];expected=a/(a+c)*100 if dim=='share:active' else a+c if dim=='view:all' else c if dim=='view:closed' else a
   assert math.isclose(o['value'],expected,rel_tol=0,abs_tol=1e-8);checks+=1
   for ev in o['provenance']:
    node=e._catalog if ev['kind']=='catalog_snapshot' else e.file(ev['path'])[0]
    for p in ev.get('valuePointer',ev.get('recordPointer')).split('/')[1:]:node=node[int(p)] if isinstance(node,list) else node[p]
    assert len(ev['sha256'])==64
  assert e.query(request('rank',x.KEYS[0],dimension=dim))['status']=='computed'
  if dim!='share:active':rejected(e,request('weighted_ratio',x.KEYS[0],dimension=dim),'remediation_verified_ratio_required')
 r=e.query(request('weighted_ratio',x.KEYS[0],dimension='share:active'));assert r['status']=='computed' and math.isclose(r['result']['value'],56/152*100),r
 r=e.query(request('weighted_ratio',x.KEYS[0],dimension='share:active',towns=['046018','046033']));assert r['status']=='computed' and math.isclose(r['result']['value'],21/61*100),r
 for op in ('series','absolute_change','relative_change','percentage_points','trend'):rejected(e,request(op,x.KEYS[0],towns=['046018']),'remediation_history_not_frozen')
 rejected(e,dict(request('benchmark_gap',x.KEYS[0]),benchmark='versilia'),'remediation_benchmark_not_reviewed')
 rejected(e,request('anomaly',x.KEYS[0]),'remediation_anomaly_not_reviewed')
 rejected(e,dict(operation='correlation',selectors=[dict(metric=x.KEYS[0]),dict(metric='population')],axis='municipalities',method='spearman',purpose='descriptive'),'remediation_pair_not_reviewed')
 rejected(e,request('compare',x.KEYS[0],periods=['2027']),'remediation_period_not_frozen')
 g=QueryEngine(path,layer='effective');g._catalog['metrics'][x.KEYS[0]]['rows'][0]['value']=None
 rejected(g,request('compare',x.KEYS[0]),'partial_coverage_requires_opt_in');assert g.query(dict(request('compare',x.KEYS[0]),allowPartial=True))['status']=='computed'
 for mode,reason in [('duplicate','remediation_duplicate_or_invalid_id'),('status','remediation_state_partition_changed'),('state','remediation_state_partition_changed'),('identity','remediation_native_identity_changed'),('hash','remediation_native_reference_changed'),('partition','remediation_state_partition_changed'),('public','remediation_public_records_changed'),('parts','remediation_catalog_source_mismatch'),('aggregate','remediation_catalog_source_mismatch'),('history','remediation_public_identity_or_history_changed')]:
  g=QueryEngine(path,layer='effective');s,ref=g.file(x.NATIVE);s=copy.deepcopy(s);rs=s['remediationProceedings']['procedures'];row=g._catalog['metrics'][x.KEYS[0]]['rows'][0]
  if mode=='duplicate':rs[1]['id']=rs[0]['id']
  elif mode=='status':rs[0]['status']='active'
  elif mode=='state':rs[0]['stateCode']='999'
  elif mode=='identity':rs[0]['townCode']='000000'
  elif mode=='hash':s['sources']['sisbon']['validatedCsvSha256']='0'*64
  elif mode=='partition':s['remediationProceedings']['closedStateCodes'].pop()
  elif mode=='public':row['procedures'].pop()
  elif mode=='parts':row['parts'][0]['value']+=1
  elif mode=='aggregate':m,mref=g.file(x.MANIFEST);m=copy.deepcopy(m);m['versilia']['remediationProceedings']['total']+=1;g.files[x.MANIFEST]=(m,mref)
  elif mode=='history':row['series']={'years':[2025],'values':[1]}
  g.files[x.NATIVE]=(s,ref);rejected(g,request('compare',x.KEYS[0]),reason)
 print(f'A6 remediation PASS: {checks} fixed observations, aliases, two pooled shares, resolvable evidence, administrative state partition and adversarial guards')
if __name__=='__main__':regressions(ROOT/'dist/data/site-data.json')
