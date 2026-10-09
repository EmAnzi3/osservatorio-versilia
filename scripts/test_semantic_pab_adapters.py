"""Independent approved/operational references and adversarial PAB boundaries."""
import copy,math
from semantic_query_engine import QueryEngine,ROOT
from test_semantic_query_engine import request,rejected
import semantic_query_pab_adapters as x
# km-intervention, approved codes, approved EUR, in-progress features, completed features, two operational gross amounts, all operational features.
VALUES={'046005':(270.094,341,1060763.74,91,150,246984.54,329096.89,342),'046013':(18.41,27,98194.06,0,13,0,19604.17,27),'046018':(317.413,464,1998372.37,6,1,9024.94,12003.72,469),'046024':(174.004,182,821438.02,43,68,132058.98,205685.93,182),'046028':(50.704,52,370837,26,7,102166.89,67506.08,51),'046030':(71.776,91,392752.72,56,9,154272.8,60084.34,92),'046033':(101.693,102,454075.17,0,0,0,0,102)}

def regressions(path):
 e=QueryEngine(path,layer='effective');checks=0
 for key in x.KEYS:
  for dim in x.dimensions(key):
   r=e.query(request('compare',key,dimension=dim));assert r['status']=='computed',r
   for o in r['observations']:
    row=VALUES[o['geography']];expected=row[x.KEYS.index(key)]
    if dim!='total':expected=expected/row[-1]*100
    assert math.isclose(o['value'],expected,rel_tol=0,abs_tol=1e-8),(key,dim,o);checks+=1
    assert not o['notApplicable'] and not o['dataUnavailable']
    for ev in o['provenance']:
     node=e._catalog if ev['kind']=='catalog_snapshot' else e.file(ev['path'])[0]
     for p in ev.get('valuePointer',ev.get('recordPointer')).split('/')[1:]:node=node[int(p)] if isinstance(node,list) else node[p]
     assert len(ev['sha256'])==64
   assert e.query(request('rank',key,dimension=dim))['status']=='computed'
   if x.weighted(key,dim):
    total=222 if key==x.COUNTS[0] else 248
    r=e.query(request('weighted_ratio',key,dimension=dim));assert r['status']=='computed' and math.isclose(r['result']['value'],total/1265*100),r
    r=e.query(request('weighted_ratio',key,dimension=dim,towns=['046018','046033']));assert r['status']=='computed' and math.isclose(r['result']['value'],(6 if key==x.COUNTS[0] else 1)/571*100),r
   else:rejected(e,request('weighted_ratio',key,dimension=dim),'pab_verified_operational_share_required')
  for op in ('series','absolute_change','relative_change','percentage_points','trend'):rejected(e,request(op,key,towns=['046018']),'pab_history_not_frozen')
  rejected(e,dict(request('benchmark_gap',key),benchmark='tuscany'),'pab_regional_national_scope_not_certified')
  rejected(e,request('anomaly',key),'pab_anomaly_not_reviewed')
  rejected(e,request('compare',key,periods=['2027']),'pab_period_not_frozen')
  rejected(e,dict(operation='correlation',selectors=[dict(metric=key),dict(metric='floodRiskArea')],axis='municipalities',method='spearman',purpose='descriptive'),'pab_approved_operational_or_risk_pair_not_reviewed')
  g=QueryEngine(path,layer='effective');g._catalog['metrics'][key]['rows'][0]['value']=None
  rejected(g,request('compare',key),'partial_coverage_requires_opt_in');assert g.query(dict(request('compare',key),allowPartial=True))['status']=='computed'
 rejected(e,request('compare',x.COUNTS[1],dimension='share:approved'),'dimension_adapter_not_implemented')
 for mode,reason in [('duplicate','pab_duplicate_or_invalid_approved_records'),('fractionalCents','pab_duplicate_or_invalid_approved_records'),('record','pab_approved_records_changed'),('pdfHash','pab_native_reference_changed'),('exportHash','pab_native_reference_changed'),('publishedUnit','pab_native_reference_changed'),('a1count','pab_catalog_source_mismatch'),('exportLength','pab_catalog_source_mismatch'),('match','pab_operational_matching_changed'),('punctual','pab_operational_matching_changed'),('date','pab_operational_reference_or_rule_changed'),('rule','pab_operational_reference_or_rule_changed'),('negative','pab_invalid_operational_components'),('fractionalCount','pab_invalid_operational_components'),('statusCount','pab_catalog_source_mismatch'),('aggregate','pab_catalog_source_mismatch'),('approvedGross','pab_catalog_source_mismatch'),('public','pab_catalog_source_mismatch'),('history','pab_public_identity_or_history_changed')]:
  g=QueryEngine(path,layer='effective');key=x.PLAN[1];s,sref=g.file(x.NATIVE);a,aref=g.file(x.A1);t,tref=g.file(x.STATUS);s=copy.deepcopy(s);a=copy.deepcopy(a);t=copy.deepcopy(t)
  if mode=='duplicate':a['cb1A1']['records'][1][0]=a['cb1A1']['records'][0][0]
  elif mode=='fractionalCents':a['cb1A1']['records'][0][3]=1.5
  elif mode=='record':a['cb1A1']['records'][0][1]='Massarosa'
  elif mode=='pdfHash':s['sources']['pabA1']['sha256']='0'*64
  elif mode=='exportHash':s['portalExports']['files']['Massarosa']['sha256']='0'*64
  elif mode=='publishedUnit':s['published'][x.PLAN[0]]['unit']='physical-km'
  elif mode=='a1count':s['pabA1ByTown']['Massarosa']['interventions']+=1
  elif mode=='exportLength':s['portalExports']['files']['Massarosa']['metres']+=1
  elif mode=='match':t['matching']['uniqueWfsFeatureIds']+=1
  elif mode=='punctual':t['punctualLayer']['sharedIdsWithCbPmoLineare']=0
  elif mode=='date':t['referenceTimestamp']='2026-12-31T23:59:59+01:00'
  elif mode=='rule':t['statusRule']['completato']='lavori_inizio valorizzato'
  elif mode=='negative':t['byTown']['Massarosa']['completato']['grossAmountEur']=-1
  elif mode=='fractionalCount':t['byTown']['Massarosa']['completato']['features']=1.5
  elif mode=='statusCount':t['byTown']['Massarosa']['completato']['features']+=1
  elif mode=='aggregate':t['aggregateSevenTowns']['completato']['grossAmountEur']+=1
  elif mode=='approvedGross':t['economicField']['pabA1ApprovedProgrammedAmountEur']+=1
  elif mode=='public':g._catalog['metrics'][key]['rows'][0]['value']+=1
  elif mode=='history':g._catalog['metrics'][key]['rows'][0]['series']={'years':[2025],'values':[1]}
  g.files.update({x.NATIVE:(s,sref),x.A1:(a,aref),x.STATUS:(t,tref)});rejected(g,request('compare',key),reason)
 # Validation cache is per selector, never inherited after a cached native object mutates.
 g=QueryEngine(path,layer='effective');assert g.query(request('compare',x.COUNTS[1]))['status']=='computed'
 g.file(x.STATUS)[0]['byTown']['Massarosa']['completato']['features']+=1
 rejected(g,request('compare',x.COUNTS[1]),'pab_catalog_source_mismatch')
 print(f'A6 PAB PASS: {checks} fixed observations, four pooled shares, approved cents/codes vs operational features, valid zeros, partial coverage and adversarial guards')
if __name__=='__main__':regressions(ROOT/'dist/data/site-data.json')
