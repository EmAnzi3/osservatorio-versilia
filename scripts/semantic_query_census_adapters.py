"""Reviewed census carriers, precision and breaks; frozen evidence is not live availability."""
import base64
import csv
import hashlib
import io
import math
from urllib.parse import urlparse
from semantic_operations import finite
from semantic_query_adapters import ratio, CENSUS_PATH, CENSUS_BENCHMARK, AGE_SNAPSHOT

NATIVE='data/source-snapshots/istat-lavoro-istruzione-eta-genere-2024.json'
HISTORY='data/source-snapshots/a3-istat-history-extension.json'
LIA='data/source-snapshots/lia-v1.4.0.json'
BENCH24='data/source-snapshots/a3-istat-census-benchmark-2024.json'
DEMOGRAPHIC=('employmentRate','unemploymentRate','activityRate','diplomaPlus','tertiary')
HOUSING={'vacantHomes':('A3','A8'),'singleHouseholds':('PF3','PF1'),'cohabitingHouseholds':('PF9','PF1')}
KEYS=(*DEMOGRAPHIC,*HOUSING,'employmentGenderGap','householdSize','oldAgeIndex')
RATIOS=('cohabitingHouseholds',)
LABOUR=('employmentRate','unemploymentRate','activityRate')


def close(actual,expected,tolerance=1e-8):
 if actual is not None and (not finite(actual) or not finite(expected) or not math.isclose(actual,expected,rel_tol=0,abs_tol=tolerance)):
  raise ValueError('census_catalog_source_mismatch')


def dimensions(key):
 if key not in DEMOGRAPHIC:return ['total']
 ages=('15-24','25-49','50-64','65plus','25-64','15plus') if key in LABOUR else ('9-24','25-49','50-64','65plus','25-64','9plus')
 return ['total']+[f'age:{a}|sex:{s}' for a in ages for s in ('total','men','women')]


def benchmark_scopes(key,dimension='total'):
 return ['tuscany','italy'] if dimension=='total' and key in (*HOUSING,'employmentGenderGap',*LABOUR,'tertiary') else []


def context(metric,key,dimension):
 if dimension not in dimensions(key):raise ValueError('census_dimension_not_reviewed')
 unit='percentagePoints' if key=='employmentGenderGap' else 'decimal' if key=='householdSize' else 'index' if key=='oldAgeIndex' else 'percent'
 if metric['meta']['unit']!=unit:raise ValueError('census_unit_changed')
 if urlparse(metric.get('sourceUrl','')).hostname not in ('www.istat.it','esploradati.istat.it'):raise ValueError('census_source_changed')
 if key in DEMOGRAPHIC and (metric['meta'].get('defaultAge')!='25-64' or metric['meta'].get('defaultGender')!='total' or str(metric['meta']['year'])!='2024'):raise ValueError('census_primary_universe_changed')
 scope='25–64 total residents' if key in DEMOGRAPHIC and dimension=='total' else dimension
 population='resident labour force; '+scope if key=='unemploymentRate' else 'resident households' if key in ('singleHouseholds','cohabitingHouseholds','householdSize') else 'censused homes including non-resident occupation' if key=='vacantHomes' else 'resident population; '+scope
 definition=(HOUSING[key][0]+' / '+HOUSING[key][1]+' * 100') if key in HOUSING else 'male employment rate minus female employment rate; residents 15–64' if key=='employmentGenderGap' else 'residents 65+ / residents 0–14 * 100' if key=='oldAgeIndex' else key+'; '+scope
 if key in DEMOGRAPHIC:
  formula={'employmentRate':'employed / resident population','unemploymentRate':'unemployed / resident labour force','activityRate':'resident labour force / resident population','diplomaPlus':'upper secondary or higher title / resident population','tertiary':'tertiary title / resident population'}[key]
  definition=formula+' * 100; '+scope
 return dict(unit=unit,population=population,definition=definition,method='Istat published census carrier; explicit frozen source reconciliation',frequency='annual',periodBasis='stock at January 1 of reference year' if key=='oldAgeIndex' else 'census reference year; specified resident universe',adapter='istat-census-carriers/'+key+'/v1')


def carrier(engine,key,row,dimension):
 if dimension=='total':return row,'',str(engine._catalog['metrics'][key]['meta']['year'])
 a,s=dimension.split('|');a=a[4:];s=s[4:]
 records=[(i,p) for i,p in enumerate(row.get('parts',[])) if p.get('ageKey')==a and p.get('genderKey')==s]
 if len(records)!=1:raise ValueError('census_part_missing_or_duplicate')
 i,p=records[0]
 if p.get('unit')!='percent':raise ValueError('census_part_unit_changed')
 return p,f'/parts/{i}',str(engine._catalog['metrics'][key]['meta']['year'])


def available_periods(engine,key,dimension,row):
 part,_,current=carrier(engine,key,row,dimension)
 series=part.get('series')
 if not isinstance(series,dict) or not series.get('years'):raise ValueError('census_historical_dimension_not_available')
 return sorted(map(str,series['years']),key=int)


def section(engine,key,row,period):
 path=LIA if key=='cohabitingHouseholds' else CENSUS_PATH
 snap,ref=engine.file(path)
 if key=='cohabitingHouseholds':
  if period!='2023':raise ValueError('census_historical_dimension_not_available')
  records=snap['raw']['istat2023'];prefix='/raw/istat2023';source=snap['sources']['istatSections2023']
 else:
  if snap['comparabilityCheck']['result']!='accepted' or not any(x['key']==key and int(period) in x['years'] for x in snap['acceptedIndicators']):raise ValueError('census_comparability_not_attested')
  records=snap['raw'].get(period,[]);prefix='/raw/'+period;source=snap['source']['files'][period]
 matches=[(i,r) for i,r in enumerate(records) if str(r['code'])==row['code'] and r['town']==row['town']]
 if len(matches)!=1:raise ValueError('census_record_missing_or_duplicate')
 i,r=matches[0];components={}
 if key=='employmentGenderGap':value=ratio(r['P102'],r['male1564'],100)-ratio(r['P103'],r['female1564'],100)
 else:
  n,d=HOUSING[key];value=ratio(r[n],r[d],100)
  if key in RATIOS:components=dict(numerator=r[n],denominator=r[d],scale=100)
 return value,components,dict(ref,kind='source_snapshot',recordPointer=f'{prefix}/{i}',sourceUrl=source['download'],sourceFiles=source.get('files',source.get('data')),comparabilityEvidence=snap.get('comparabilityCheck')),source['download']


def native(engine,key,row,dimension):
 snap,ref=engine.file(NATIVE)
 if str(snap['referenceYear'])!='2024':raise ValueError('census_native_year_changed')
 r=snap['towns'][row['town']]
 if r['code']!=row['code']:raise ValueError('census_native_identity_mismatch')
 age,sex=('25-64','total') if dimension=='total' else tuple(x.split(':')[1] for x in dimension.split('|'))
 family='labour' if key in LABOUR else 'education';raw=r[family][age][sex]
 field='tertiaryRate' if key=='tertiary' else key
 value=raw[field]
 n,d=('employed','population') if key=='employmentRate' else ('unemployed','active') if key=='unemploymentRate' else ('active','population') if key=='activityRate' else ('upperSecondaryPlus','population') if key=='diplomaPlus' else ('tertiary','population')
 close(value,ratio(raw[n],raw[d],100))
 if dimension!='total':
  part=carrier(engine,key,row,dimension)[0]
  close(part.get('numerator'),raw[n]);close(part.get('denominator'),raw[d])
 source=snap['source']['api']
 return value,{},dict(ref,kind='source_snapshot',recordPointer=f'/towns/{row["town"]}/{family}/{age}/{sex}',sourceUrl=source,sourceDataflow=snap['source'][family+'Dataflow'],componentEvidence=dict(numerator=raw[n],denominator=raw[d],scale=100),componentCaution='frozen derived SDMX components; no implicit additivity or weighting certification'),source


def historical(engine,key,row,dimension,period):
 snap,ref=engine.file(HISTORY)
 if snap['referenceSnapshot']['sha256']!=engine.file(NATIVE)[1]['sha256']:raise ValueError('census_history_reference_hash_changed')
 if dimension in ('total','age:25-64|sex:total') and key=='diplomaPlus':
  item=snap['historicalDiploma']['towns'][row['code']]
  if item['town']!=row['town']:raise ValueError('census_history_identity_changed')
  raw=base64.b64decode(item['rawCsvBase64']);
  if hashlib.sha256(raw).hexdigest()!=item['sha256']:raise ValueError('census_history_csv_hash_changed')
  rows=list(csv.DictReader(io.StringIO(raw.decode(item['encoding'])),delimiter=';'))
  matches=[r for r in rows if str(r.get('AnnoCP'))==period and r.get('Denominazione11')==row['town'] and r.get('Nome indicatore')=='Incidenza di adulti con diploma o laurea']
  if len(matches)!=1:raise ValueError('census_history_period_missing_or_duplicate')
  value=float(matches[0]['Value'].replace(',','.'));source=item['url'];pointer=f'/historicalDiploma/towns/{row["code"]}'
 else:
  spec=snap['componentHistories'][key]
  if dimension!='age:'+spec['partKey'].replace('|','|sex:'):raise ValueError('census_historical_dimension_not_available')
  if int(period) not in spec['years']:raise ValueError('census_history_period_not_available')
  matches=[(i,r) for i,r in enumerate(spec['rows']) if str(r['cells'][6])==row['code'] and r['cells'][5]==row['town']]
  if len(matches)!=1:raise ValueError('census_history_record_missing_or_duplicate')
  i,item=matches[0];cols=[i for i,x in enumerate(spec['header']) if str(x)==period]
  if len(cols)!=1:raise ValueError('census_history_header_missing_or_duplicate')
  value=item['cells'][cols[0]]
  if spec['transform']=='100-minus-native':value=100-value
  elif spec['transform']!='identity':raise ValueError('census_history_transform_changed')
  source=snap['componentWorkbooks'][spec['workbook']]['url'];pointer=f'/componentHistories/{key}/rows/{i}/cells/{cols[0]}'
 return value,{},dict(ref,kind='source_snapshot',recordPointer=pointer,sourceUrl=source,transform=snap.get('componentHistories',{}).get(key,{}).get('transform','identity'),archiveHashes='declared frozen extraction; original workbook not reread'),source


def observation(engine,key,index,dimension,period,historical_selection):
 metric=engine._catalog['metrics'][key];row=metric['rows'][index];part,suffix,current=carrier(engine,key,row,dimension);pointer=f'/metrics/{key}/rows/{index}'+suffix
 if period==current and not historical_selection:
  value=part.get('value');vp=pointer+'/value';pp=f'/metrics/{key}/meta/year'
 else:
  series=part.get('series')
  if not isinstance(series,dict) or period not in list(map(str,series.get('years',[]))):raise ValueError('census_historical_dimension_not_available')
  j=list(map(str,series['years'])).index(period);value=series['values'][j];vp=pointer+f'/series/values/{j}';pp=pointer+f'/series/years/{j}'
 notes=[];components={}
 if key in (*HOUSING,'employmentGenderGap'):
  expected,components,ref,source=section(engine,key,row,period);tolerance=.0500001 if key in ('vacantHomes','singleHouseholds') and period=='2023' else 1e-8
  close(value,expected,tolerance)
  if key in ('vacantHomes','singleHouseholds'):notes.append('published_rounding_preserved_no_implicit_weighting')
  if key=='vacantHomes':notes.append('non_resident_occupied_homes_are_not_necessarily_vacant')
  if key=='singleHouseholds':notes.append('single_household_not_direct_measure_of_loneliness')
 elif key in DEMOGRAPHIC:
  if period=='2024':expected,components,ref,source=native(engine,key,row,dimension);close(value,expected,.0500001 if dimension=='total' else 1e-8)
  else:expected,components,ref,source=historical(engine,key,row,dimension,period);close(value,expected)
  notes.extend(['resident_employment_not_workplace_jobs','frozen_derived_components_no_implicit_weighting'] if key in LABOUR else ['education_title_not_skills_or_job_match'])
  if dimension in ('total','age:25-64|sex:total') and key=='diplomaPlus':notes.append('traditional_to_permanent_census_method_break')
  if dimension=='total':notes.append('published_rounding_preserved_no_implicit_weighting')
 elif key=='oldAgeIndex':
  snap,ref=engine.file(AGE_SNAPSHOT);records=[r for r in snap['posas']['towns'][row['town']] if str(r['year'])==period];sources=[s for s in snap['posas']['sources'] if str(s['year'])==period]
  if len(records)!=1 or len(sources)!=1:raise ValueError('census_posas_record_missing_or_duplicate')
  expected=ratio(records[0]['age65plus'],records[0]['age0to14'],100);close(value,expected,.0500001);source=sources[0]['url'];ref=dict(ref,kind='source_snapshot',record=f'posas.towns.{row["town"]}.year={period}',sourceUrl=source);notes.append('old_age_index_not_share_of_population')
 else:
  if period!='2023':raise ValueError('census_historical_dimension_not_available')
  source=metric['sourceUrl'];ref=dict(kind='published_method_note',path=engine.catalog_path,sha256=engine.catalog_hash,valuePointer=vp,text=metric.get('method'),limitation='municipal raw household members not frozen or not reconciled; no count reconstruction')
  notes.append('household_size_raw_components_not_reconciled')
 if key=='employmentGenderGap':notes.append('gender_gap_in_percentage_points_not_relative_percent')
 evidence=[dict(kind='catalog_snapshot',path=engine.catalog_path,sha256=engine.catalog_hash,valuePointer=vp,periodPointer=pp),ref]
 return dict(context(metric,key,dimension),**components,metric=key,dimension=dimension,geography=row['code'],period=period,value=value,source=source,evidence=evidence,provenance=evidence,notApplicable=bool(row.get('notApplicable')) if period==current else False,dataUnavailable=bool(row.get('dataUnavailable')) or value is None),notes


def benchmark(engine,key,scope,municipal):
 if scope not in benchmark_scopes(key,municipal['dimension']):raise ValueError('census_benchmark_scope_dimension_or_method_not_reviewed')
 path=BENCH24 if key in (*LABOUR,'tertiary') else CENSUS_BENCHMARK
 snap,ref=engine.file(path);spec=snap['benchmarks'][key]
 if snap['qualityGate']['status']!='PASS' or str(spec['year'])!=municipal['period'] or spec['unit']!=municipal['unit']:raise ValueError('census_benchmark_period_unit_or_quality_mismatch')
 if path==BENCH24:
  family='labour' if key in LABOUR else 'education';raw=snap['components'][scope][family]
  n,d=('employed','population') if key=='employmentRate' else ('unemployed','active') if key=='unemploymentRate' else ('active','population') if key=='activityRate' else ('tertiary','population')
  if spec['formula']!=f'{n} / {d} × 100' or snap['source']['referenceSnapshot']!=NATIVE:raise ValueError('census_benchmark_formula_or_source_changed')
  value=ratio(raw[n],raw[d],100);source=snap['source']['api']
 else:
  raw=snap['raw'][scope];source=snap['source']['url']
  if snap['source']['regionalWorkbookCount']!=20:raise ValueError('census_benchmark_regional_scope_changed')
  municipal_source=engine.file(LIA)[0]['sources']['istatSections2023']['files']['data'] if key=='cohabitingHouseholds' else engine.file(CENSUS_PATH)[0]['source']['files']['2023']['data']
  if municipal_source['sha256']!=snap['source']['tuscanyWorkbook']['sha256']:raise ValueError('census_benchmark_workbook_changed')
  if key=='employmentGenderGap':value=ratio(raw['P102'],raw['male1564'],100)-ratio(raw['P103'],raw['female1564'],100)
  else:n,d=HOUSING[key];value=ratio(raw[n],raw[d],100)
 close(spec[scope],value)
 published=engine._catalog['metrics'][key]['meta'].get('benchmark',{})
 if str(published.get('year'))!=municipal['period'] or published.get('sourceSnapshot')!=path:raise ValueError('census_published_benchmark_context_changed')
 close(published.get(scope),value)
 evidence=[dict(ref,kind='benchmark_snapshot',valuePointer=f'/benchmarks/{key}/{scope}',sourceUrl=source,methodEvidence=snap['method'],qualityGate=snap['qualityGate']),dict(kind='published_benchmark',path=engine.catalog_path,sha256=engine.catalog_hash,valuePointer=f'/metrics/{key}/meta/benchmark/{scope}')]
 return dict(context(engine._catalog['metrics'][key],key,municipal['dimension']),metric=key,dimension=municipal['dimension'],geography=scope,period=municipal['period'],value=value,source=source,evidence=evidence,provenance=evidence,notApplicable=False,dataUnavailable=False)
