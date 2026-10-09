"""Fixed census counts, organic annual values, independent arithmetic and refusals."""
import copy,math
from semantic_query_engine import QueryEngine,ROOT
from test_semantic_query_engine import request,rejected
import semantic_query_agriculture_profile_adapters as x
COUNTS={'046005':((14,319),(104,317),(15,319),(60,319),(38,319)),'046013':((2,7),(3,7),(0,7),(2,7),(1,7)),'046018':((15,192),(68,191),(16,192),(34,192),(18,192)),'046024':((19,187),(78,182),(23,187),(38,187),(24,187)),'046028':((5,63),(16,61),(3,64),(13,63),(4,63)),'046030':((4,43),(15,43),(9,44),(10,43),(6,43)),'046033':((10,146),(50,143),(8,146),(45,146),(19,146))}
ORGANIC={'046018':(3.55,3.89,3.99,4.01,2.9,3.02,4.30272899101345),'046033':(5.36,6.14,7.19,4.14,6.3,3.97,4.08454773885472),'046005':(6.79,8.98,11.42,5.42,5.1,5.84,6.25655376895405),'046024':(1.62,1.25,1.29,2.86,2.4,2.3,6.86842706193545),'046028':(1.51,0.,2.49,3.2,3.7,3.89,8.10702094156546),'046013':(0.,0.,0.,0.,1.5,1.51,1.51614991696822),'046030':(19.8,18.24,20.59,21.16,20.6,11.05,9.66115955114865)}
PARTS=('youngManagers','femaleHolders','connectedActivities','informatization','innovation')
TOTALS=((69,957),(334,944),(74,959),(202,957),(110,957))
def regressions(path):
 e=QueryEngine(path,layer='effective');checks=0;pooled=0;history=0
 for key in x.KEYS:
  for dim in x.dimensions(key):
   r=e.query(request('compare',key,dimension=dim));assert r['status']=='computed',r
   for o in r['observations']:
    if key in x.PARTS:
     j=PARTS.index(x.part(key,dim));n,d=COUNTS[o['geography']][j];expected=n/d*100;assert (o['numerator'],o['denominator'],o['scale'])==(n,d,100)
    else:expected=ORGANIC[o['geography']][-1]
    assert math.isclose(o['value'],expected,rel_tol=0,abs_tol=1e-8),(key,dim,o);checks+=1
    for ev in o['provenance']:
     node=e._catalog if ev['kind']=='catalog_snapshot' else e.file(ev['path'])[0]
     for p in ev.get('valuePointer',ev.get('recordPointer')).split('/')[1:]:node=node[int(p)] if isinstance(node,list) else node[p]
     assert len(ev['sha256'])==64
   assert e.query(request('rank',key,dimension=dim))['status']=='computed'
   if key in x.PARTS:
    j=PARTS.index(x.part(key,dim));n,d=TOTALS[j];q=e.query(request('weighted_ratio',key,dimension=dim));assert q['status']=='computed' and math.isclose(q['result']['value'],n/d*100),q;pooled+=1
    q=e.query(request('weighted_ratio',key,dimension=dim,towns=['046013','046018']));a,b=COUNTS['046013'][j],COUNTS['046018'][j];assert q['status']=='computed' and math.isclose(q['result']['value'],(a[0]+b[0])/(a[1]+b[1])*100),q;pooled+=1
    rejected(e,request('series',key,dimension=dim,towns=['046018']),'agriculture_profiles_temporal_change_not_reviewed')
    rejected(e,request('compare',key,dimension=dim,periods=['2021']),'agriculture_profiles_census_period_not_frozen')
   for op in ['absolute_change','relative_change','trend','percentage_points']:rejected(e,request(op,key,dimension=dim,towns=['046018']),'agriculture_profiles_temporal_change_not_reviewed')
  rejected(e,request('anomaly',key),'agriculture_profiles_peer_anomaly_not_reviewed')
  rejected(e,dict(operation='correlation',selectors=[dict(metric=key),dict(metric='agriculturalFarms')],axis='municipalities',method='spearman',purpose='descriptive'),'agriculture_profiles_pair_not_jointly_reviewed')
  for mode in ['value','identity','unit','part','native','hash','date','null']:
   g=QueryEngine(path,layer='effective');m=g._catalog['metrics'][key];p=x.CENSUS if key in x.PARTS else x.ORGANIC;s,ref=g.file(p);s=copy.deepcopy(s);ref=copy.deepcopy(ref);reason='agriculture_profiles_public_native_mismatch'
   if mode=='value':m['rows'][0]['value']+=1
   elif mode=='null':m['rows'][0]['value']=None
   elif mode=='identity':m['rows'][0]['town']='wrong';reason='agriculture_profiles_public_identity_changed'
   elif mode=='unit':m['meta']['unit']='number';reason='agriculture_profiles_definition_changed'
   elif mode=='date':m['meta']['year']='2026';reason='agriculture_profiles_definition_changed'
   elif mode=='part':
    if key in x.PARTS:m['rows'][0]['parts'][0]['universe']='all farms';reason='agriculture_profiles_public_parts_changed'
    else:m['rows'][0]['series']['values'][0]+=1;reason='agriculture_profiles_public_series_changed'
   elif mode=='native':s['title' if key in x.PARTS else 'note']='changed';reason='agriculture_profiles_frozen_input_changed'
   elif mode=='hash':ref['sha256']='0'*64;reason='agriculture_profiles_frozen_input_changed'
   g.files[p]=(s,ref);rejected(g,request('compare',key),reason)
 key=x.KEYS[2]
 for code,values in ORGANIC.items():
  r=e.query(request('series',key,towns=[code]));assert r['status']=='computed',r;assert [o['period'] for o in r['observations']]==list(map(str,range(2018,2025)));assert [o['value'] for o in r['observations']]==list(values);history+=7
  r=e.query(dict(request('benchmark_gap',key,towns=[code]),benchmark='tuscany'));assert r['status']=='computed' and math.isclose(r['result']['value'],values[-1]-33.57),r
 rejected(e,request('weighted_ratio',key),'agriculture_profiles_no_organic_area_components')
 rejected(e,dict(request('benchmark_gap',key,towns=['046018']),benchmark='italy'),'agriculture_profiles_benchmark_scope_or_period_not_reviewed')
 rejected(e,dict(request('benchmark_gap',key,towns=['046018'],periods=['2023']),benchmark='tuscany'),'agriculture_profiles_benchmark_scope_or_period_not_reviewed')
 rejected(e,request('compare',key,periods=['2025']),'agriculture_profiles_organic_period_not_frozen')
 g=QueryEngine(path,layer='effective');assert g.query(request('compare',key))['status']=='computed';g.file(x.ORGANIC)[0]['note']='changed';rejected(g,request('compare',key),'agriculture_profiles_frozen_input_changed')
 assert (checks,pooled,history)==(56,14,49)
 print('A6 agriculture profiles PASS: 56 fixed current observations including aliases, 14 pooled ratios, 49 fixed annual values, seven official Tuscany gaps and adversarial boundaries')
if __name__=='__main__':regressions(ROOT/'dist/data/site-data.json')
