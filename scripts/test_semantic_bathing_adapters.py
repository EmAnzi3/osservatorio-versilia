"""Literal ARPAT components/FEE counts, resolvable evidence and adversarial guards."""
import copy,math
from semantic_query_engine import QueryEngine,ROOT
from test_semantic_query_engine import request,rejected
import semantic_query_bathing_adapters as b

QUALITY={
 '046005':((2,0,0,1,3),(2.92,0.,0.,.32,3.24)),
 '046013':((3,0,0,0,3),(5.2,0.,0.,0.,5.2)),
 '046024':((4,5,0,0,9),(3.56,1.19,0.,0.,4.75)),
 '046033':((5,1,0,0,6),(7.16,.27,0.,0.,7.43))}
SAMPLES={'046005':((8,28),(7,18),(1,10)),'046013':((4,22),(4,18),(0,4)),'046024':((17,73),(12,54),(5,19)),'046033':((6,44),(6,36),(0,8))}
AWARDS={'046005':(1,1,1,1,1,1,1,1),'046013':(1,1,1,1,1,1,1,1),'046024':(1,1,0,2,2,2,2,2),'046033':(2,2,2,2,2,2,2,2)}

def expected(key,dim,code):
 if key==b.KEYS[2]:return AWARDS[code][-1],None,None
 if key==b.KEYS[0]:
  p=('share','areas','excellent') if dim=='total' else tuple(dim.split(':'))
  if len(p)==2:p=('count','kilometres',p[1])
  kind,basis,category=p;v=QUALITY[code][0 if basis=='areas' else 1];num=v[(*b.CLASSES,'total').index(category)];den=v[-1]
 else:
  kind,scope=('share','all') if dim=='total' else dim.split(':');num,den=SAMPLES[code][b.SAMPLES.index(scope)]
  if kind=='samples':num=den
 return (num/den*100,num,den) if kind=='share' else (num,None,None)

def regressions(path):
 e=QueryEngine(path,layer='effective');nchecks=0
 for key in b.KEYS:
  if key not in e._catalog['metrics']:continue
  for dim in b.dimensions(key):
   rejected(e,request('compare',key,dimension=dim),'partial_coverage_requires_opt_in')
   r=e.query(dict(request('compare',key,dimension=dim),allowPartial=True));assert r['status']=='computed',r
   assert len(r['excluded'])==3 and {x['observation']['geography'] for x in r['excluded']}==set(b.NA)
   for o in r['observations']:
    for ev in o['provenance']:
     node=e._catalog if ev['kind']=='catalog_snapshot' else e.file(ev['path'])[0]
     for part in ev.get('valuePointer',ev.get('recordPointer')).split('/')[1:]:node=node[int(part)] if isinstance(node,list) else node[part]
     assert len(ev['sha256'])==64
    if o['geography'] in b.NA:assert o['value'] is None and o['notApplicable'] and not o['dataUnavailable'];continue
    v,num,den=expected(key,dim,o['geography']);assert math.isclose(o['value'],v,rel_tol=0,abs_tol=1e-8);nchecks+=1
    assert o['period']==b.PERIODS[key]
    if num is not None:assert o['numerator']==num and o['denominator']==den
   if b.weighted(key,dim):
    r=e.query(dict(request('weighted_ratio',key,dimension=dim),allowPartial=True));assert r['status']=='computed',r
    components=[expected(key,dim,c) for c in b.COASTAL]
    assert math.isclose(r['result']['value'],math.fsum(v[1] for v in components)/math.fsum(v[2] for v in components)*100,rel_tol=0,abs_tol=1e-8)
   else:rejected(e,request('weighted_ratio',key,dimension=dim),'bathing_verified_ratio_required')
   rejected(e,dict(request('benchmark_gap',key,dimension=dim,towns=['046005']),benchmark='tuscany'),'bathing_totals_not_municipal_reference')
  for op in ('absolute_change','relative_change','percentage_points','trend'):
   rejected(e,request(op,key,towns=['046005']),'bathing_historical_change_not_reviewed' if key==b.KEYS[2] else 'bathing_classification_or_samples_history_not_frozen')
  if key!=b.KEYS[2]:rejected(e,request('series',key,towns=['046005']),'bathing_classification_or_samples_history_not_frozen')
  rejected(e,request('compare',key,periods=['2027']),'bathing_period_not_frozen')
  rejected(e,request('anomaly',key),'bathing_anomaly_not_reviewed')
  rejected(e,dict(operation='correlation',selectors=[{'metric':key},{'metric':'population'}],axis='municipalities',method='spearman',purpose='descriptive',allowPartial=True),'bathing_universes_not_jointly_comparable')
  r=e.query(dict(request('rank',key),allowPartial=True));assert r['status']=='computed',r
  g=QueryEngine(path,layer='effective');next(r for r in g._catalog['metrics'][key]['rows'] if r['code']=='046018')['value']=0
  rejected(g,dict(request('compare',key),allowPartial=True),'bathing_not_applicable_changed')
  g=QueryEngine(path,layer='effective');next(r for r in g._catalog['metrics'][key]['rows'] if r['code']=='046005')['value']=None
  rejected(g,request('compare',key,towns=list(b.COASTAL)),'partial_coverage_requires_opt_in')
  r=g.query(dict(request('compare',key,towns=list(b.COASTAL)),allowPartial=True));assert r['status']=='computed' and len(r['excluded'])==1,r
 for code,values in AWARDS.items():
  r=e.query(request('series',b.KEYS[2],towns=[code]));assert r['status']=='computed',r
  assert [o['value'] for o in r['observations']]==list(values);nchecks+=8
  assert [o['period'] for o in r['observations']]==[str(y) for y in range(2019,2027)]
  for o in r['observations']:
   assert o['source']==b.BLUE.replace('2026',o['period'])
 r=e.query(request('series',b.KEYS[2],towns=['046018']));assert r['status']=='not_computable' and all(o['notApplicable'] for o in r['observations']),r
 for mode,key,reason in [
  ('denominator',b.KEYS[1],'bathing_invalid_native_components'),('partition',b.KEYS[1],'bathing_catalog_source_mismatch'),
  ('qualitypartition',b.KEYS[0],'bathing_catalog_source_mismatch'),('definition',b.KEYS[1],'bathing_native_definition_changed'),
  ('window',b.KEYS[0],'bathing_native_definition_changed'),('fractional',b.KEYS[0],'bathing_invalid_native_components'),
  ('public',b.KEYS[1],'bathing_catalog_source_mismatch'),('identity',b.KEYS[0],'bathing_row_identity_changed'),
  ('cohort',b.KEYS[2],'bathing_native_cohort_changed'),('hash',b.KEYS[1],'bathing_native_reference_changed'),
  ('years',b.KEYS[2],'bathing_native_definition_changed'),('rule',b.KEYS[2],'bathing_native_definition_changed'),
  ('publicseries',b.KEYS[2],'bathing_public_components_changed'),('fee',b.KEYS[2],'bathing_fee_localities_not_reconciled'),
  ('revoked',b.KEYS[2],'bathing_fee_localities_not_reconciled'),('duplicate',b.KEYS[2],'bathing_invalid_native_components')]:
  g=QueryEngine(path,layer='effective');s,ref=g.file(b.NATIVE);s=copy.deepcopy(s);d=s[b.FAMILIES[key]];n=d['towns']['046005']
  if mode=='denominator':n['all']['total']=0
  elif mode=='partition':n['all']['nonCompliant']+=1
  elif mode=='qualitypartition':n['kilometres']['excellent']+=.01
  elif mode=='definition':d['deduplicationKey']=['Codice area','Data']
  elif mode=='window':d['period']='Classificazione 2025 sui dati 2021-2025'
  elif mode=='fractional':n['areas']['excellent']=2.5
  elif mode=='public':next(r for r in g._catalog['metrics'][key]['rows'] if r['code']=='046005')['parts'][0]['total']+=1
  elif mode=='identity':n['name']='Massarosa'
  elif mode=='cohort':d['towns']['046018']=copy.deepcopy(n)
  elif mode=='hash':s['sources']['arpatSamples2025']['sha256']='0'*64
  elif mode=='years':d['years'][0]=2018
  elif mode=='rule':s['sources']['blueFlagArchive']['countingRule']='split slash names'
  elif mode=='publicseries':next(r for r in g._catalog['metrics'][key]['rows'] if r['code']=='046005')['series']['values'][0]=2
  elif mode=='duplicate':n['localities2026']*=2
  else:
   f,fr=g.file(b.FEE);f=copy.deepcopy(f);v=next(r for r in f['records'] if r['town']=='Camaiore');v['localities']=['Lido','Camaiore'] if mode=='fee' else v['localities'];v['revoked']=mode=='revoked';g.files[b.FEE]=(f,fr)
  g.files[b.NATIVE]=(s,ref);rejected(g,dict(request('compare',key),allowPartial=True),reason)
 print(f'A6 bathing PASS: {nchecks} fixed-reference observations including aliases and 32 historical counts; 4 coastal/3 n.a., native area/km/sample weighting, targeted controls, FEE locality reconciliation and valid 2021 zero')

if __name__=='__main__':regressions(ROOT/'dist/data/site-data.json')
