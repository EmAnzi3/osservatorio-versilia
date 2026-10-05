#!/usr/bin/env python3
"""Business source reconciliation, full municipal histories and independent arithmetic."""
import copy
import json
import math
import shutil
import tempfile
from pathlib import Path
from semantic_query_engine import QueryEngine, ROOT, operations
import semantic_query_business_adapters as b
from test_semantic_query_engine import request, rejected


def regressions(catalog_path):
 e=QueryEngine(catalog_path,layer='effective')
 for key in b.KEYS:
  for dimension in b.dimensions(key):
   current=e.query(request('compare',key,dimension=dimension));assert current['status']=='computed',(key,dimension,current['reasons'])
   assert current['coverage']['usable']==7
   for code in sorted(e.codes):
    for scope in b.benchmark_scopes(key,dimension):
     result=e.query(dict(request('benchmark_gap',key,dimension=dimension,towns=[code]),benchmark=scope))
     assert result['status']=='computed',(key,dimension,code,scope,result['reasons'])
     assert result['observations'][0]['definition']==result['observations'][1]['definition']
    if key=='microUnits':continue
    series=e.query(request('series',key,dimension=dimension,towns=[code]));assert series['status']=='computed',(key,dimension,code,series['reasons'])
    assert len(series['observations'])>=3
    first,last=series['observations'][0],series['observations'][-1]
    change=e.query(request('absolute_change',key,dimension=dimension,towns=[code],periods=[first['period'],last['period']]))
    assert change['status']=='computed'
    assert math.isclose(change['result']['value'],last['value']-first['value'],rel_tol=0,abs_tol=1e-8)
    if key in b.CHANGES:
     assert all(o['baselinePeriod']=='2018' for o in series['observations'])
     rejected(e,request('trend',key,towns=[code]),'business_cumulative_trend_not_supported')
    else:
     trend=e.query(request('trend',key,dimension=dimension,towns=[code]));assert trend['status']=='computed',trend['reasons']
   if key in b.RATIOS:
    ratio=e.query(request('weighted_ratio',key,dimension=dimension));assert ratio['status']=='computed',ratio['reasons']
    assert 'workplace' in ratio['policy']['disjointPopulationEvidence']['method']
   else:rejected(e,request('weighted_ratio',key,dimension=dimension),'verified_ratio_adapter_required')
 # Independent transcriptions and arithmetic, including differences in units/universes.
 expected=[('localEmployees','total',4938.33),('businessValueAdded','sector:industry',92.849),('labourProductivity','total',53005),('averageGrossRemunerationPerEmployee','sector:industry',31226),('microUnits','total',95.45)]
 for key,dimension,value in expected:
  q=e.query(request('compare',key,dimension=dimension,towns=['046018','046033']));assert q['status']=='computed',q['reasons'];assert math.isclose(q['observations'][0]['value'],value,rel_tol=0,abs_tol=1e-8)
 weighted=e.query(request('weighted_ratio','employeesPerLocalUnit'));assert math.isclose(weighted['result']['value'],54392.17/17967,rel_tol=0,abs_tol=1e-10)
 industry=e.query(request('weighted_ratio','turnoverPerPersonEmployed',dimension='sector:industry'));assert math.isclose(industry['result']['value'],3270358000/16477,rel_tol=0,abs_tol=1e-8)
 rejected(e,request('compare','localUnitsChange',periods=['2023']),'business_explicit_baseline_interval_required')
 rejected(e,request('series','microUnits',towns=['046018']),'business_series_not_available')
 rejected(e,dict(request('benchmark_gap','industryWorkerShare',towns=['046018']),benchmark='tuscany'),'business_benchmark_scope_or_dimension_not_available')
 rejected(e,dict(request('benchmark_gap','businessValueAdded',dimension='sector:industry',towns=['046018']),benchmark='tuscany'),'business_benchmark_scope_or_dimension_not_available')
 rejected(e,dict(request('benchmark_gap','localUnits',periods=['2022'],towns=['046018']),benchmark='tuscany'),'business_historical_benchmark_not_available')
 rejected(e,request('series','labourCost',towns=['046018'],periods=['2015']),'business_history_period_not_available')
 rejected(e,dict(operation='correlation',selectors=[dict(metric=k,towns=['046018']) for k in b.CHANGES],axis='periods',method='spearman',purpose='Cumulative intervals require refusal'),'business_cumulative_temporal_correlation_not_supported')
 with tempfile.TemporaryDirectory(prefix='a6-business-') as temporary:
  root=Path(temporary);path=root/'catalog.json';original=e.catalog
  def changed(data):
   path.write_text(json.dumps(data));return QueryEngine(path,repository_root=root,layer='effective')
  for snapshot in (b.ASIA,b.FRAME,b.MICRO,b.ASIA_BENCH,b.FRAME_BENCH):
   target=root/snapshot;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/snapshot,target)
  for name in json.loads((ROOT/b.FRAME).read_text())['parts']:shutil.copyfile(ROOT/'data/source-snapshots'/name,root/'data/source-snapshots'/name)
  data=copy.deepcopy(original);data['metrics']['localEmployees']['rows'][0]['value']+=1
  rejected(changed(data),request('compare','localEmployees'),'business_catalog_source_mismatch')
  data=copy.deepcopy(original);data['metrics']['businessValueAdded']['rows'][0]['economicScopes']['industry']['value']+=1
  rejected(changed(data),request('compare','businessValueAdded',dimension='sector:industry'),'business_catalog_source_mismatch')
  data=copy.deepcopy(original);data['metrics']['labourProductivity']['rows'][0]['value']=None
  rejected(changed(data),request('compare','labourProductivity'),'partial_coverage_requires_opt_in')
  partial=changed(data).query(dict(request('compare','labourProductivity'),allowPartial=True));assert partial['status']=='computed' and partial['coverage']['usable']==6 and partial['excluded'][0]['observation']['value'] is None
  data=copy.deepcopy(original);data['metrics']['businessTurnover']['rows'][0]['economicScopes']['industry']['series']['values'][1]=None
  rejected(changed(data),request('series','businessTurnover',dimension='sector:industry',towns=['046018']),'partial_coverage_requires_opt_in')
  partial=changed(data).query(dict(request('series','businessTurnover',dimension='sector:industry',towns=['046018']),allowPartial=True));assert partial['status']=='computed' and partial['coverage']['usable']==8 and partial['excluded'][0]['observation']['value'] is None
  data=copy.deepcopy(original);data['metrics']['businessTurnover']['rows'][0]['economicScopes']['industry']['series']['years'][1]=2015
  try:changed(data)
  except AssertionError as exc:assert 'Periodi duplicati' in str(exc)
  else:raise AssertionError('duplicate carrier periods accepted')
  part=root/'data/source-snapshots/economia-prodotta-frame-sbs-v134-2021-2023.json';raw=json.loads(part.read_text());raw['rows'].append(copy.deepcopy(raw['rows'][0]));part.write_text(json.dumps(raw))
  rejected(changed(original),request('compare','businessValueAdded'),'business_source_record_not_unique')
  shutil.copyfile(ROOT/'data/source-snapshots'/part.name,part)
  snap=json.loads((root/b.MICRO).read_text());snap['sources']['046018']['csv']+='corrupt';(root/b.MICRO).write_text(json.dumps(snap))
  rejected(changed(original),request('compare','microUnits'),'business_csv_hash_mismatch')
  snap=json.loads((root/b.ASIA_BENCH).read_text());snap['evidence']['LU']['tuscany']['2023']+=1;(root/b.ASIA_BENCH).write_text(json.dumps(snap))
  rejected(changed(original),dict(request('benchmark_gap','localUnits',towns=['046018']),benchmark='tuscany'),'business_catalog_source_mismatch')
 print('A6 business: 16 adapters, reviewed sectors, all seven municipal histories/benchmarks, independent arithmetic and refusals PASS')


if __name__=='__main__':regressions(ROOT/'dist/data/site-data.json')
