"""Frozen Rendiconto/SIOPE evidence; accounting flows and denominator dates explicit."""
import math
import re
from urllib.parse import urlparse
from a6_pins import Pin as _pin
from openbdap_benchmarks import METRICS as BENCHMARKED, RATIOS as BENCHMARK_RATIOS
from semantic_operations import finite
from materialize_a3_5_openbdap_ratio_components import BILANCI_TARGETS, MISSION_CODES

BILANCI='data/source-snapshots/bilanci-v1.6.0.json'
SIOPE='data/source-snapshots/siope-history-v1.6.0.json'
EXTENSION='data/source-snapshots/bilanci-v139.json'
PUBLISHED=('fcdePerResident','yearEndCashFundPerResident','generalAdministrationMissionExpenditurePerResident','territorialPlanningMissionExpenditurePerResident','civilProtectionMissionExpenditurePerResident')
CASH={'siopePayments':'cash_payments','currentPayments':'current_payments','capitalPayments':'capital_payments','cashReceiptsPerResident':'cash_receipts','cashBalancePerResident':'cash_balance'}
PERCENT={'ownRevenueShare':('own_revenue_accruals_titles_1_3','current_revenue_accruals_titles_1_2_3'),'currentCollectionCapacity':('current_revenue_competence_receipts_titles_1_2_3','current_revenue_accruals_titles_1_2_3'),'currentPaymentCapacity':('current_expenditure_competence_payments_title_1','current_expenditure_commitments_title_1')}
AMOUNTS={'currentRevenueAccruedPerResident':'current_revenue_accruals_titles_1_2_3','currentExpenditureCommittedPerResident':'current_expenditure_commitments_title_1','capitalExpenditureCommittedPerResident':'capital_expenditure_commitments_title_2','availableAdministrationResultPerResident':'available_administration_result_code_0502'}
KEYS=(*BILANCI_TARGETS,'rigidExpenditureShare',*PUBLISHED,*CASH)
RATIOS=(*BILANCI_TARGETS,*CASH)


def close(actual,expected):
 if actual is not None and (not finite(actual) or not finite(expected) or not math.isclose(actual,expected,rel_tol=0,abs_tol=1e-7)):
  raise ValueError('finance_catalog_source_mismatch')


def context(metric,key,dimension):
 if dimension!='total':raise ValueError('finance_dimension_not_reviewed')
 unit='percent' if key in PERCENT or key=='rigidExpenditureShare' else 'currency'
 if metric['meta']['unit']!=unit:raise ValueError('finance_unit_changed')
 if urlparse(metric.get('sourceUrl','')).hostname not in (('www.siope.it','openbdap.rgs.mef.gov.it','bdap-opendata.rgs.mef.gov.it') if key in CASH else ('openbdap.rgs.mef.gov.it',)):raise ValueError('finance_source_changed')
 method='SIOPE annual December cumulative cash; resident denominator at next January 1' if key in CASH else ('Rendiconto official accounting ratio; no resident denominator' if unit=='percent' else 'Rendiconto accrual/commitment or year-end stock; resident denominator at exercise January 1')
 definition=(CASH[key]+' / next January 1 residents') if key in CASH else ' / '.join(PERCENT[key])+' * 100' if key in PERCENT else AMOUNTS[key]+' / exercise January 1 residents' if key in AMOUNTS else 'mission commitments '+ '+'.join(MISSION_CODES[key])+' / exercise January 1 residents' if key in MISSION_CODES else 'official PDI 01.01 rigid expenditure share; rounded published measure' if key=='rigidExpenditureShare' else metric['meta']['description']
 return dict(unit=unit,population='municipal accounting perimeter; resident normalization is not beneficiaries',definition=definition,method=method,frequency='annual',periodBasis='accounting exercise; denominator date explicit',adapter='rgs-finance/'+key+'/v1')


def available_periods(engine,key,dimension,row):
 series=row.get('series')
 if not isinstance(series,dict):raise ValueError('finance_series_not_available')
 years=list(map(str,series.get('years',[])))
 if not years or len(years)!=len(set(years)) or len(years)!=len(series.get('values',[])):raise ValueError('finance_series_periods_mismatch')
 return sorted(years,key=int)


def observation(engine,key,index,dimension,period,historical):
 metric=engine._catalog['metrics'][key];row=metric['rows'][index];ctx=context(metric,key,dimension)
 pointer=f'/metrics/{key}/rows/{index}';current=str(metric['meta']['year'])
 if historical:
  years=available_periods(engine,key,dimension,row)
  if period not in years:raise ValueError('finance_period_not_available')
  j=list(map(str,row['series']['years'])).index(period);value=row['series']['values'][j];vp=pointer+f'/series/values/{j}';pp=pointer+f'/series/years/{j}'
 else:
  if period!=current:raise ValueError('finance_current_period_mismatch')
  value=row.get('value');vp=pointer+'/value';pp=f'/metrics/{key}/meta/year'
 evidence=[dict(kind='catalog_snapshot',path=engine.catalog_path,sha256=engine.catalog_hash,valuePointer=vp,periodPointer=pp)]
 warnings=['municipal_accounting_perimeter_not_service_quality_or_policy_effect','gross_municipal_amounts_not_consolidated_for_interentity_transfers']
 if ctx['unit']=='currency':warnings.append('nominal_finance_values_not_real_growth')
 components={};dates={}
 if key in PUBLISHED:
  snap,ref=engine.file(EXTENSION);series=snap['series'][key]['towns'][row['town']];years=list(map(str,series['years']))
  if len(years)!=len(set(years)) or len(years)!=len(series['values']) or period not in years:raise ValueError('finance_frozen_series_periods_mismatch')
  dates=dict(numeratorPeriod=period,denominatorPeriod=period,denominatorReferenceDate='1 gennaio '+period)
  expected=series['values'][years.index(period)];source=snap['source']['archives'][period]['url']
  archive=snap['source']['archives'][period]
  if archive['container_drift']!=(archive['sha256']!=archive['baseline_sha256']):raise ValueError('finance_archive_drift_attestation_changed')
  if archive['container_drift']:warnings.append('finance_extension_archive_revision_differs_from_legacy_frozen_carriers')
  evidence.append(dict(ref,kind='source_snapshot',recordPointer=f'/series/{key}/towns/{row["town"]}',sourceUrl=source,archive=archive,limitation='frozen normalized extraction; original amount not present, no implied additive components'))
  warnings.append('finance_raw_amount_not_frozen_no_implicit_weighting')
  if key=='fcdePerResident':warnings.append('fcde_is_prudential_reserve_not_measured_bad_debt')
  if key=='yearEndCashFundPerResident':warnings.append('year_end_cash_stock_not_free_spendable_cash_or_annual_balance')
 else:
  path=SIOPE if key in CASH else BILANCI;snap,ref=engine.file(path)
  rawtown=snap['raw'][row['town']]
  if key in CASH:
   raw=rawtown[period];date='1 gennaio '+str(int(period)+1)
   if raw['population_reference_date']!=date:raise ValueError('finance_population_reference_date_changed')
   n=raw[CASH[key]];d=raw['population_resident'];scale=1
   if key=='cashBalancePerResident':close(n,raw['cash_receipts']-raw['cash_payments']);warnings.append('annual_cash_balance_not_year_end_cash_stock')
   refs={k:v for k,v in snap['source']['resources'].items() if k.endswith('-'+period+'-toscana')}
   if len(refs)!=2:raise ValueError('finance_cash_sources_missing')
   source=refs[('entrata' if key=='cashReceiptsPerResident' else 'spesa')+'-'+period+'-toscana']['url']
   dates=dict(numeratorPeriod=period,denominatorPeriod=str(int(period)+1),denominatorReferenceDate=date)
   warnings+=['cash_including_residual_payments_not_accrual_or_commitments','siope_next_year_resident_denominator']
   rp=f'/raw/{row["town"]}/{period}'
  else:
   if rawtown['code']!=row['code']:raise ValueError('finance_geography_mismatch')
   raw=rawtown['years'][period];refs=snap['source']['years'][period];source=refs['indicatori' if key=='rigidExpenditureShare' else 'schemi']['url'];rp=f'/raw/{row["town"]}/years/{period}'
   dates=dict(numeratorPeriod=period,denominatorPeriod=period,denominatorReferenceDate='1 gennaio '+period)
   if key=='rigidExpenditureShare':
    dates={}
    expected=raw['rigid_expenditure_share_official_code_01_01'];warnings.append('official_rounded_pdi_no_implicit_weighting')
   elif key in PERCENT:
    nf,df=PERCENT[key];n,d,scale=raw[nf],raw[df],100;dates={};warnings.append('accounting_ratio_not_service_outcome')
   else:
    d=raw['population_at_1_january'];scale=1
    if key in AMOUNTS:n=raw[AMOUNTS[key]]
    else:
     missions=raw['mission_commitments']
     if any(code not in missions or not finite(missions[code]) for code in MISSION_CODES[key]):raise ValueError('finance_mission_amount_missing')
     n=math.fsum(missions[code] for code in MISSION_CODES[key]);warnings.append('mission_commitments_include_current_and_capital_not_delivered_services')
  if key!='rigidExpenditureShare':
   if not finite(n) or not finite(d) or d<=0:raise ValueError('finance_invalid_components')
   expected=n/d*scale;components=dict(numerator=n,denominator=d,scale=scale)
  evidence.append(dict(ref,kind='source_snapshot',recordPointer=rp,sourceUrl=source,sourceFiles=refs,archiveVerification='declared extraction hashes; original archives not reread'))
  payload=row.get('ratioComponents') if not historical and key in RATIOS else None
  if payload:
   if str(payload['year'])!=period or payload['sourceSnapshot']!=path:raise ValueError('finance_component_context_changed')
   close(payload['numerator']['value'],n);close(payload['denominator']['value'],d);close(payload['scale'],scale)
 close(value,expected)
 if historical and period==current:close(row.get('value'),value)
 return dict(ctx,**components,**dates,metric=key,dimension=dimension,geography=row['code'],period=period,value=value,source=source,evidence=evidence,provenance=evidence,notApplicable=bool(row.get('notApplicable')) if not historical else False,dataUnavailable=value is None or (bool(row.get('dataUnavailable')) if not historical else False)),warnings


BENCHMARK_RE=re.compile(r'data/source-snapshots/openbdap-benchmark-(20[0-9]{2})[.]json')
BENCHMARK_HASH=_pin('finance#1')


_PUBLISHED_SCOPES={}


def published_scopes():
 """Territori con un confronto pubblicato nell'ultimo snapshot (≥90% dei residenti, riconciliazione 7/7 superata)."""
 if not _PUBLISHED_SCOPES:
  import json
  from pathlib import Path
  root=Path(__file__).resolve().parents[1]/'data'/'source-snapshots'
  found=sorted(p for p in root.glob('openbdap-benchmark-*.json') if BENCHMARK_RE.fullmatch('data/source-snapshots/'+p.name))
  if found:
   snap=json.loads(found[-1].read_text(encoding='utf-8'))
   for key,entries in snap.get('benchmarks',{}).items():
    _PUBLISHED_SCOPES[key]=[sc for sc in ('tuscany','italy') if (entries.get(sc) or {}).get('value') is not None]
  _PUBLISHED_SCOPES.setdefault('',[])
 return _PUBLISHED_SCOPES


def scopes(key,dimension):
 return list(published_scopes().get(key,[])) if key in BENCHMARKED and dimension=='total' else []


def benchmark(engine,key,scope,municipal):
 """Toscana/Italia sui Comuni che hanno trasmesso il rendiconto (≥90% dei residenti), componenti native nello snapshot."""
 if key not in BENCHMARKED or scope not in ('tuscany','italy'):raise ValueError('finance_benchmark_components_or_complete_scope_not_frozen')
 published=engine._catalog['metrics'][key]['meta'].get('benchmark') or {}
 path=str(published.get('sourceSnapshot'))
 if not BENCHMARK_RE.fullmatch(path):raise ValueError('finance_benchmark_components_or_complete_scope_not_frozen')
 snap,ref=engine.file(path)
 if ref.get('sha256')!=BENCHMARK_HASH or snap.get('qualityGate',{}).get('status')!='PASS':raise ValueError('finance_benchmark_frozen_input_changed')
 if municipal['period']!=str(snap['year']) or str(published.get('year'))!=str(snap['year']):raise ValueError('finance_benchmark_period_not_frozen')
 entry=snap['benchmarks'][key][scope]
 if entry.get('value') is None or entry['populationShare']<snap['minCoverage']:raise ValueError('finance_benchmark_scope_below_coverage_threshold')
 scale=100 if key in BENCHMARK_RATIOS else 1
 value=entry['numerator']/entry['denominator']*scale
 close(value,entry['value']);close(published.get(scope),value)
 evidence=[dict(ref,kind='source_snapshot',recordPointer=f'/benchmarks/{key}/{scope}',nativeComponents=dict(numerator=entry['numerator'],denominator=entry['denominator'],scale=scale),
               coverage=dict(municipalities=entry['municipalities'],municipalitiesTotal=entry['municipalitiesTotal'],populationShare=entry['populationShare'])),
           dict(kind='catalog_snapshot',path=engine.catalog_path,sha256=engine.catalog_hash,valuePointer=f'/metrics/{key}/meta/benchmark/{scope}')]
 return dict(municipal,geography=scope,value=value,evidence=evidence,provenance=evidence,
             benchmarkAggregation='sum over municipalities that filed the Rendiconto with the required rows / their own denominators (residents 1 January for per-resident values); published only with ≥90% of residents covered')
