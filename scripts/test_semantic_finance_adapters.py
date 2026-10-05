"""Accounting reconciliation on all towns/years and false-certification guards."""
import copy
import json
import math
import shutil
import tempfile
from pathlib import Path
from semantic_query_engine import QueryEngine, ROOT
from test_semantic_query_engine import request, rejected
import semantic_query_finance_adapters as f


def regressions(path):
 e=QueryEngine(path,layer='effective')
 for k in f.KEYS:
  if k not in e._catalog['metrics']:continue
  r=e.query(request('compare',k));assert r['status']=='computed',(k,r['reasons']);assert r['coverage']['usable']==7
  for code in sorted(e.codes):
   r=e.query(request('series',k,towns=[code]));assert r['status']=='computed',(k,code,r['reasons']);assert len(r['observations'])>=5
   periods=[o['period'] for o in r['observations']]
   r=e.query(request('absolute_change',k,towns=[code],periods=[periods[0],periods[-1]]));assert r['status']=='computed',(k,code,r['reasons'])
  r=e.query(request('weighted_ratio',k))
  if k in f.RATIOS:assert r['status']=='computed',(k,r['reasons'])
  else:assert 'verified_ratio_adapter_required' in r['reasons']
  rejected(e,dict(request('benchmark_gap',k,towns=['046018']),benchmark='tuscany'),'finance_benchmark_components_or_complete_scope_not_frozen')
 for key,value in [('currentRevenueAccruedPerResident',31550784.64/21806),('ownRevenueShare',30149960.78/31550784.64*100),('socialMissionExpenditurePerResident',4284516.36/21806),('rigidExpenditureShare',20.66),('cashBalancePerResident',(36273551.04-38649263.81)/21782),('fcdePerResident',508.0258616894433)]:
  if key not in e._catalog['metrics']:continue
  r=e.query(request('compare',key,towns=['046018','046033']));assert math.isclose(r['observations'][0]['value'],value,abs_tol=1e-7),(key,r['observations'][0]['value'],value)
 r=e.query(request('compare','rigidExpenditureShare'));assert all('denominatorReferenceDate' not in o for o in r['observations'])
 r=e.query(request('compare','cashReceiptsPerResident'));assert all(o['denominatorPeriod']=='2026' and o['denominatorReferenceDate']=='1 gennaio 2026' for o in r['observations'])
 with tempfile.TemporaryDirectory() as t:
  root=Path(t)
  for p in (f.BILANCI,f.SIOPE,f.EXTENSION):
   target=root/p;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/p,target)
  original=e.catalog;path=root/'catalog.json'
  def changed(data):path.write_text(json.dumps(data));return QueryEngine(path,repository_root=root,layer='effective')
  for k in ('currentRevenueAccruedPerResident','ownRevenueShare','cashBalancePerResident','fcdePerResident'):
   if k not in original['metrics']:continue
   data=copy.deepcopy(original);data['metrics'][k]['rows'][0]['value']+=1
   rejected(changed(data),request('compare',k),'finance_catalog_source_mismatch')
  data=copy.deepcopy(original);data['metrics']['currentPaymentCapacity']['rows'][0]['ratioComponents']['numerator']['value']+=1
  rejected(changed(data),request('compare','currentPaymentCapacity'),'finance_catalog_source_mismatch')
  data=copy.deepcopy(original);data['metrics']['cashBalancePerResident']['rows'][0]['value']=None
  rejected(changed(data),request('compare','cashBalancePerResident'),'partial_coverage_requires_opt_in')
  r=changed(data).query(dict(request('compare','cashBalancePerResident'),allowPartial=True));assert r['status']=='computed' and r['coverage']['usable']==6
  snap=root/f.SIOPE;raw=json.loads(snap.read_text());saved=copy.deepcopy(raw);raw['raw']['Massarosa']['2025']['population_reference_date']='1 gennaio 2025';snap.write_text(json.dumps(raw))
  rejected(changed(original),request('compare','cashReceiptsPerResident'),'finance_population_reference_date_changed');snap.write_text(json.dumps(saved))
  snap=root/f.BILANCI;raw=json.loads(snap.read_text());del raw['raw']['Massarosa']['years']['2025']['mission_commitments']['12'];snap.write_text(json.dumps(raw))
  rejected(changed(original),request('compare','socialMissionExpenditurePerResident'),'finance_mission_amount_missing')
 print('A6 finance: all admitted carriers × seven towns × admitted years, ratios, denominator dates, nulls and negative cases PASS')


if __name__=='__main__':regressions(ROOT/'dist/data/site-data.json')
