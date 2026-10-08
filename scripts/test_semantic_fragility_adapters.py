"""Literal IFC source inputs; ordinal semantics, effective dates and native medians."""
import copy
import math
from semantic_query_engine import QueryEngine, ROOT
from test_semantic_query_engine import request, rejected
import semantic_query_fragility_adapters as f

# Municipality-code order; fixed independently of adapter output.
REFERENCE = {
 '046005': ([4,4,3,2],[10,11,10,9],0),
 '046013': ([4,4,4,4],[5,5,6,5],19.2),
 '046018': ([4,4,3,4],[10,10,9,11],17.1),
 '046024': ([4,4,3,3],[9,9,9,8],20),
 '046028': ([1,2,1,1],[9,10,9,10],22),
 '046030': ([6,7,7,7],[11,14,12,14],28.3),
 '046033': ([3,3,2,2],[10,11,9,9],0),
}

def regressions(path):
 e=QueryEngine(path,layer='effective');count=0
 if not all(k in e._catalog['metrics'] for k in f.KEYS):return
 try:
  for k in f.KEYS:f.context(e._catalog['metrics'][k],k,'total')
 except ValueError:return  # Source carrier stubs are not the materialized IFC catalog.
 for ki,key in enumerate(f.KEYS):
  r=e.query(request('compare',key));assert r['status']=='computed',r
  for o in r['observations']:
   expected=REFERENCE[o['geography']][ki];expected=expected[-1] if ki<2 else expected
   assert o['value']==expected and len(o['provenance'])==2 and all(len(x['sha256'])==64 for x in o['provenance']);count+=1
   assert o['period']==('2022' if ki<2 else '2019')
  for code,values in REFERENCE.items():
   if ki<2:
    r=e.query(request('series',key,towns=[code]));assert r['status']=='computed',r
    assert [o['value'] for o in r['observations']]==values[ki] and [o['period'] for o in r['observations']]==['2018','2019','2021','2022'];count+=4
   else:
    for scope,median_value in [('tuscany',33.2),('italy',27.1)]:
     r=e.query(dict(request('benchmark_gap',key,towns=[code]),benchmark=scope));assert r['status']=='computed',r
     assert math.isclose(r['result']['value'],values[2]-median_value,rel_tol=0,abs_tol=1e-8),r
     assert r['observations'][1]['benchmarkAggregation']=='unweighted municipality median';count+=2
  reason='fragility_ordinal_operation_not_supported' if ki<2 else 'accessibility_operation_not_attested'
  for op in ('absolute_change','relative_change','percentage_points','trend','weighted_ratio','anomaly','correlation',*(['rank','benchmark_gap'] if ki<2 else ['series'])):
   q=request(op,key,towns=['046018']);
   if op=='correlation':q.update(selectors=[{'metric':key},{'metric':'population'}],method='spearman',axis='municipalities',purpose='descriptive association')
   rejected(e,q,reason)
  rejected(e,request('compare',key,periods=['2020']),'fragility_period_not_frozen')
  g=QueryEngine(path,layer='effective');g._catalog['metrics'][key]['rows'][0]['value']=None
  rejected(g,request('compare',key),'partial_coverage_requires_opt_in');r=g.query(dict(request('compare',key),allowPartial=True));assert r['status']=='computed' and len(r['excluded'])==1
 r=e.query(request('rank',f.KEYS[2]));assert r['status']=='computed' and sum(o['value']==0 for o in r['observations'])==2
 for mode,reason in [('scale','fragility_ordinal_scale_changed'),('identity','fragility_row_identity_changed'),('ordinal','fragility_invalid_ordinal_history'),('history','fragility_public_history_changed'),('release','fragility_native_reference_changed'),('minutes','accessibility_effective_reference_changed'),('repeated','accessibility_effective_reference_changed'),('value','fragility_catalog_source_mismatch'),('bench-year','accessibility_benchmark_reference_changed'),('bench-record','accessibility_benchmark_cohort_changed'),('bench-value','fragility_catalog_source_mismatch')]:
  key=f.KEYS[2] if mode in ('minutes','repeated','bench-year','bench-record','bench-value') else f.KEYS[0];g=QueryEngine(path,layer='effective');row=g._catalog['metrics'][key]['rows'][0];s,ref=g.file(f.NATIVE);s=copy.deepcopy(s);n=s['istatByTown'][row['town']]
  if mode=='scale':g._catalog['metrics'][key]['meta']['ordinalScale']['max']=100
  elif mode=='identity':n['code']='000000'
  elif mode=='ordinal':n['series'][f.FIELDS[key]][0]['value']=4.5
  elif mode=='history':row['series']['years'][2]=2020
  elif mode=='release':s['sources']['istat']['referenceYear']=2023
  elif mode=='minutes':n['latest2022'][f.FIELDS[key]]=-1
  elif mode=='repeated':row['series']={'years':[2022],'values':[row['value']]}
  elif mode=='value':row['value']+=1
  else:
   b,br=g.file(f.BENCHMARK);b=copy.deepcopy(b)
   if mode=='bench-year':b['referenceYear']=2022
   elif mode=='bench-record':b['records'].append(b['records'][0])
   else:b['benchmarks'][key]['tuscany']+=1
   g.files[f.BENCHMARK]=(b,br)
  g.files[f.NATIVE]=(s,ref)
  q=dict(request('benchmark_gap',key,towns=['046018']),benchmark='tuscany') if mode.startswith('bench') else request('compare',key)
  rejected(g,q,reason)
 print(f'A6 IFC PASS: {count} fixed-reference observations including series and repeated benchmark gaps; ordinal refusals, effective 2019, zero minutes, native medians, nulls and adversarial guards')

if __name__=='__main__':regressions(ROOT/'dist/data/site-data.json')
