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
  bench=e._catalog['metrics'][k]['meta'].get('benchmark') or {}
  if k in f.BENCHMARKED and isinstance(bench.get('tuscany'),(int,float)):
   snap,_=e.file(bench['sourceSnapshot']);ent=snap['benchmarks'][k]['tuscany']
   r=e.query(dict(request('benchmark_gap',k,towns=['046018']),benchmark='tuscany'));assert r['status']=='computed',(k,r['reasons'])
   assert ent['populationShare']>=0.9 and math.isclose(r['observations'][1]['value'],ent['numerator']/ent['denominator']*(100 if k in f.BENCHMARK_RATIOS else 1),abs_tol=1e-9)
  else:rejected(e,dict(request('benchmark_gap',k,towns=['046018']),benchmark='tuscany'),'finance_benchmark')
 for key,value in [('currentRevenueAccruedPerResident',31550784.64/21806),('ownRevenueShare',30149960.78/31550784.64*100),('socialMissionExpenditurePerResident',4284516.36/21806),('rigidExpenditureShare',20.66),('cashBalancePerResident',(36273551.04-38649263.81)/21782),('fcdePerResident',508.0258616894433)]:
  if key not in e._catalog['metrics']:continue
  r=e.query(request('compare',key,towns=['046018','046033']));assert math.isclose(r['observations'][0]['value'],value,abs_tol=1e-7),(key,r['observations'][0]['value'],value)
 # Confronto bilanci 2025 (OpenBDAP, Comuni che hanno trasmesso il rendiconto, soglia 90% dei residenti): ancore indipendenti.
 if 'benchmark' in (e._catalog['metrics']['currentRevenueAccruedPerResident']['meta'] or {}) and e._catalog['metrics']['currentRevenueAccruedPerResident']['meta']['benchmark']:
  r=e.query(dict(request('benchmark_gap','currentRevenueAccruedPerResident',towns=['046018']),benchmark='tuscany'));assert r['status']=='computed',r['reasons']
  assert math.isclose(r['observations'][1]['value'],5062879022.64/3652987,abs_tol=1e-9) and r['observations'][1]['evidence'][0]['coverage']['municipalities']==272
  rejected(e,dict(request('benchmark_gap','tourismDevelopmentMissionExpenditurePerResident',towns=['046018']),benchmark='italy'),'finance_benchmark_scope_below_coverage_threshold')
  rejected(e,dict(request('benchmark_gap','availableAdministrationResultPerResident',towns=['046018']),benchmark='tuscany'),'finance_benchmark')
  g=QueryEngine(path,layer='effective')
  snap,_=g.file(g._catalog['metrics']['ownRevenueShare']['meta']['benchmark']['sourceSnapshot']);snap['benchmarks']['ownRevenueShare']['tuscany']['numerator']*=1.01
  rejected(g,dict(request('benchmark_gap','ownRevenueShare',towns=['046018']),benchmark='tuscany'),'finance_catalog_source_mismatch')
 r=e.query(request('compare','rigidExpenditureShare'));assert all('denominatorReferenceDate' not in o for o in r['observations'])
 r=e.query(request('compare','cashReceiptsPerResident'));assert all(o['denominatorPeriod']=='2026' and o['denominatorReferenceDate']=='1 gennaio 2026' for o in r['observations'])
 # Cassa SIOPE 2025, Toscana (273/273 Comuni in entrambi i flussi, residenti POSAS 1.1.2026 = 3.659.222):
 # incassi 7.059.647.759,85 €; saldo incassi − pagamenti −105.544.995,01 €. Italia non calcolata.
 for key,n in (('cashReceiptsPerResident',7059647759.85),('cashBalancePerResident',-105544995.01)):
  r=e.query(dict(request('benchmark_gap',key,towns=['046018']),benchmark='tuscany'));assert r['status']=='computed',r['reasons']
  assert math.isclose(r['observations'][1]['value'],n/3659222,abs_tol=1e-6) and r['observations'][1]['evidence'][0]['coverage']['municipalities']==273
  rejected(e,dict(request('benchmark_gap',key,towns=['046018']),benchmark='italy'),'finance_benchmark')
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
