"""Census dimensions, all towns, frozen evidence and explicit refusals."""
import copy
import json
import math
import shutil
import tempfile
from pathlib import Path
from semantic_query_engine import QueryEngine, ROOT
import semantic_query_census_adapters as c
from test_semantic_query_engine import request, rejected


def regressions(path):
 e=QueryEngine(path,layer='effective')
 for key in c.KEYS:
  for dimension in c.dimensions(key):
   r=e.query(request('compare',key,dimension=dimension));assert r['status']=='computed',(key,dimension,r['reasons']);assert r['coverage']['usable']==7
   for code in sorted(e.codes):
    for scope in c.benchmark_scopes(key,dimension):
     r=e.query(dict(request('benchmark_gap',key,dimension=dimension,towns=[code]),benchmark=scope));assert r['status']=='computed',(key,scope,r['reasons'])
  for code in sorted(e.codes):
   row=next(r for r in e._catalog['metrics'][key]['rows'] if r['code']==code)
   for dimension in c.dimensions(key):
    try:periods=c.available_periods(e,key,dimension,row)
    except ValueError:continue
    if key=='diplomaPlus' and dimension=='total':
     rejected(e,request('trend',key,towns=[code]),'census_method_break_trend_not_supported')
    r=e.query(request('series',key,dimension=dimension,towns=[code]));assert r['status']=='computed',(key,dimension,code,r['reasons'])
    assert [o['period'] for o in r['observations']]==periods
    if key=='diplomaPlus' and dimension in ('total','age:25-64|sex:total'):
     rejected(e,request('absolute_change',key,dimension=dimension,towns=[code],periods=[periods[0],periods[-1]]),'census_method_break_change_not_supported')
    else:
     r=e.query(request('absolute_change',key,dimension=dimension,towns=[code],periods=[periods[0],periods[-1]]));assert r['status']=='computed',(key,dimension,r['reasons'])
  if key not in c.RATIOS:rejected(e,request('weighted_ratio',key),'verified_ratio_adapter_required')
 for key,dimension,value in [('employmentRate','total',73.4),('tertiary','total',17.3),('vacantHomes','total',17.9),('singleHouseholds','total',29.2),('householdSize','total',2.38),('oldAgeIndex','total',257.2),('employmentRate','age:15-24|sex:total',491/2091*100),('diplomaPlus','age:25-49|sex:total',4331/6015*100)]:
  r=e.query(request('compare',key,dimension=dimension,towns=['046018','046033']));assert math.isclose(r['observations'][0]['value'],value,abs_tol=1e-8)
 rejected(e,request('series','employmentRate',towns=['046018']),'census_historical_dimension_not_available')
 rejected(e,request('series','householdSize',towns=['046018']),'census_historical_dimension_not_available')
 rejected(e,dict(request('benchmark_gap','diplomaPlus',towns=['046018']),benchmark='tuscany'),'census_benchmark_scope_dimension_or_method_not_reviewed')
 rejected(e,dict(request('benchmark_gap','tertiary',dimension='age:25-49|sex:total',towns=['046018']),benchmark='tuscany'),'census_benchmark_scope_dimension_or_method_not_reviewed')
 rejected(e,dict(request('benchmark_gap','oldAgeIndex',towns=['046018']),benchmark='tuscany'),'census_benchmark_scope_dimension_or_method_not_reviewed')
 r=e.query(request('weighted_ratio','cohabitingHouseholds'));assert r['status']=='computed';assert math.isclose(r['result']['value'],1712/73331*100,abs_tol=1e-8)
 with tempfile.TemporaryDirectory() as t:
  root=Path(t)
  for source in (c.NATIVE,c.HISTORY,c.CENSUS_PATH,c.LIA,c.CENSUS_BENCHMARK,c.BENCH24,c.AGE_SNAPSHOT):
   target=root/source;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/source,target)
  path=root/'catalog.json';original=e.catalog
  def changed(data):path.write_text(json.dumps(data));return QueryEngine(path,repository_root=root,layer='effective')
  for key in ('employmentRate','vacantHomes','employmentGenderGap','oldAgeIndex'):
   data=copy.deepcopy(original);data['metrics'][key]['rows'][0]['value']+=1
   rejected(changed(data),request('compare',key),'census_catalog_source_mismatch')
  data=copy.deepcopy(original);data['metrics']['tertiary']['rows'][0]['parts'][0]['numerator']+=1
  rejected(changed(data),request('compare','tertiary',dimension='age:9-24|sex:total'),'census_catalog_source_mismatch')
  data=copy.deepcopy(original);data['metrics']['singleHouseholds']['rows'][0]['value']=None
  rejected(changed(data),request('compare','singleHouseholds'),'partial_coverage_requires_opt_in')
  r=changed(data).query(dict(request('compare','singleHouseholds'),allowPartial=True));assert r['status']=='computed' and r['coverage']['usable']==6
  data=copy.deepcopy(original);data['metrics']['employmentRate']['meta']['defaultAge']='15plus'
  rejected(changed(data),request('compare','employmentRate'),'census_primary_universe_changed')
  snapshot=root/c.HISTORY;raw=json.loads(snapshot.read_text());saved=copy.deepcopy(raw);raw['historicalDiploma']['towns']['046018']['sha256']='0'*64;snapshot.write_text(json.dumps(raw))
  rejected(changed(original),request('series','diplomaPlus',towns=['046018']),'census_history_csv_hash_changed');snapshot.write_text(json.dumps(saved))
  snapshot=root/c.CENSUS_PATH;raw=json.loads(snapshot.read_text());raw['raw']['2023'].append(copy.deepcopy(raw['raw']['2023'][0]));snapshot.write_text(json.dumps(raw))
  rejected(changed(original),request('compare','singleHouseholds'),'census_record_missing_or_duplicate')
 print('A6 census: 11 carriers, all current age/sex dimensions, seven-town histories/benchmarks, independent values and negative cases PASS')


if __name__=='__main__':regressions(ROOT/'dist/data/site-data.json')
