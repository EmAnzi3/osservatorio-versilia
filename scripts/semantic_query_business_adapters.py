"""Reviewed ASIA and Frame SBS carriers; no live acquisition or implicit universes."""
import csv
import hashlib
import io
import math
import re
from pathlib import Path
from urllib.parse import urlparse
from semantic_operations import finite

ASIA='data/source-snapshots/agid-asia-agcom-2026-08.json'
FRAME='data/source-snapshots/economia-prodotta-frame-sbs-v134.json'
ASIA_BENCH='data/source-snapshots/a3-istat-business-benchmark-2023.json'
FRAME_BENCH='data/source-snapshots/a3-frame-sbs-benchmark-2023.json'
MICRO='data/source-snapshots/a3-istat-micro-units-benchmark-2023.json'
# These are adapter formula rules. Catalog IDs/availability remain canonical.
FRAME_FIELDS={
 'businessTurnover':('turnoverThousandEuro',.001,'millionCurrency'),
 'businessValueAdded':('valueAddedThousandEuro',.001,'millionCurrency'),
 'labourProductivity':('valueAddedPerPersonEmployedThousandEuro',1000,'currency'),
 'valueAddedTurnoverShare':('valueAddedTurnoverPercent',1,'percent'),
 'averageGrossRemunerationPerEmployee':('averageGrossRemunerationPerEmployeeThousandEuro',1000,'currency'),
 'labourCost':('labourCostThousandEuro',.001,'millionCurrency'),
 'grossOperatingMargin':(None,1,'millionCurrency'),
 'turnoverPerPersonEmployed':(None,1,'currency')}
SHARES={'industryValueAddedShare':'valueAddedThousandEuro','industryWorkerShare':'personsEmployed'}
ASIA_UNITS={'localUnits':'number','localEmployees':'people','employeesPerLocalUnit':'decimal','localUnitsChange':'percent','localEmployeesChange':'percent','microUnits':'percent'}
KEYS=tuple(FRAME_FIELDS)+tuple(SHARES)+tuple(ASIA_UNITS)
CHANGES=('localUnitsChange','localEmployeesChange')
RATIOS=('turnoverPerPersonEmployed','employeesPerLocalUnit',*SHARES)


def token(key,period):
 s=str(period).replace('–','-').replace('—','-')
 if key in CHANGES:
  if not re.fullmatch(r'2018-20[0-9]{2}',s):raise ValueError('business_explicit_baseline_interval_required')
  if int(s[-4:])<2018:raise ValueError('business_baseline_period_reversed')
 elif not re.fullmatch(r'[0-9]{4}',s):raise ValueError('business_explicit_annual_period_required')
 return s


def order(period):return int(str(period)[-4:])


def dimensions(key):return ['total','sector:industry','sector:services'] if key in FRAME_FIELDS else ['total']


def benchmark_scopes(key,dimension='total'):
 return ['tuscany','italy'] if key not in SHARES and dimension=='total' else []


def context(metric,key,dimension):
 if dimension not in dimensions(key):raise ValueError('business_dimension_not_reviewed')
 unit=FRAME_FIELDS[key][2] if key in FRAME_FIELDS else 'percent' if key in SHARES else ASIA_UNITS[key]
 if metric['meta']['unit']!=unit:raise ValueError('business_unit_changed')
 current=token(key,metric['meta']['year'])
 if key=='microUnits' and current!='2023':raise ValueError('business_micro_reference_year_changed')
 if urlparse(metric.get('sourceUrl','')).hostname not in ('www.istat.it','esploradati.istat.it'):raise ValueError('business_source_changed')
 frame=key in FRAME_FIELDS or key in SHARES
 if key in FRAME_FIELDS and not all(isinstance(r.get('economicScopes'),dict) for r in metric['rows']):raise ValueError('business_sector_carrier_not_materialized')
 universe='Frame SBS local units of industry and services' if frame else 'ASIA active local units; annual average employment at workplace'
 scope=dimension.split(':')[-1] if dimension!='total' else 'industry and services' if frame else 'ASIA total'
 definition=f'{key}; {scope}; published nominal measure' if frame else f'{key}; ASIA published measure'
 if key in SHARES:definition+= '; industry divided by total industry and services'
 if key in CHANGES:definition+='; cumulative change from fixed 2018 baseline'
 return dict(unit=unit,population=universe+'; '+scope,definition=definition,
  method='Istat Frame SBS published measures and explicit formulas' if frame else 'Istat ASIA snapshot via AgID; explicit source formulas',
  frequency='cumulative_from_2018' if key in CHANGES else 'annual',
  periodBasis='full baseline-to-end interval; not year-on-year' if key in CHANGES else 'calendar reference year; workplace economic activity',
  adapter='istat-business/'+('frame-sbs' if frame else 'asia')+'/v1')


def close(actual,expected,tolerance=1e-6):
 if actual is None:return
 if not finite(actual) or not finite(expected) or not math.isclose(actual,expected,rel_tol=0,abs_tol=tolerance):raise ValueError('business_catalog_source_mismatch')


def frame_index(engine):
 if hasattr(engine,'_business_frame_index'):return engine._business_frame_index
 manifest,ref=engine.file(FRAME);index={}
 for name in manifest['parts']:
  if Path(name).name!=name or not name.startswith('economia-prodotta-frame-sbs-v134-'):raise ValueError('business_snapshot_part_invalid')
  part,path=engine.file('data/source-snapshots/'+name)
  if len(set(part['columns']))!=len(part['columns']):raise ValueError('business_duplicate_columns')
  for i,values in enumerate(part['rows']):
   if len(values)!=len(part['columns']):raise ValueError('business_source_row_width_mismatch')
   raw=dict(zip(part['columns'],values));identity=(str(raw['year']),raw['scope'],str(raw['code']))
   if identity in index:raise ValueError('business_source_record_not_unique')
   index[identity]=(raw,dict(path,kind='source_snapshot',recordPointer=f'/rows/{i}',sourceRow=raw['sourceRow'],manifest=ref))
 engine._business_frame_index=index
 return index


def frame_record(engine,year,scope,code):
 records=frame_index(engine)
 if (year,scope,code) not in records:raise ValueError('business_frame_period_or_scope_not_available')
 raw,ref=records[year,scope,code]
 manifest,_=engine.file(FRAME);sources=[s for s in manifest['sources'] if str(s['anno'])==year]
 if len(sources)!=1:raise ValueError('business_source_release_not_unique')
 return raw,dict(ref,sourceUrl=sources[0]['url'],archiveSha256=sources[0]['sha256'],archive=sources[0]['file'])


def frame_value(key,raw,total=None):
 if key in SHARES:return raw[SHARES[key]]/total[SHARES[key]]*100
 field,scale,_=FRAME_FIELDS[key]
 if field:return raw[field]*scale
 if key=='grossOperatingMargin':return (raw['valueAddedThousandEuro']-raw['labourCostThousandEuro'])/1000
 return round(raw['turnoverThousandEuro']/raw['personsEmployed']*1000,6)


def available_periods(engine,key,dimension,row):
 carrier=row.get('economicScopes',{}).get(dimension.split(':')[-1] if dimension!='total' else 'total',row) if key in FRAME_FIELDS else row
 series=carrier.get('series')
 if not isinstance(series,dict):raise ValueError('business_series_not_available')
 years=list(map(str,series['years']))
 if len(years)!=len(set(years)) or len(years)!=len(series['values']):raise ValueError('business_history_periods_mismatch')
 return ['2018-'+y for y in years] if key in CHANGES else years


def observation(engine,key,row_index,dimension,period,historical):
 metric=engine._catalog['metrics'][key];row=metric['rows'][row_index];ctx=context(metric,key,dimension)
 current=token(key,metric['meta']['year']);year=period[-4:];pointer=f'/metrics/{key}/rows/{row_index}';period_pointer=f'/metrics/{key}/meta/year'
 carrier=row;suffix=''
 if key in FRAME_FIELDS and dimension!='total':
  suffix='/economicScopes/'+dimension.split(':')[1];carrier=row['economicScopes'][dimension.split(':')[1]]
 if historical:
  periods=available_periods(engine,key,dimension,row)
  if period not in periods:raise ValueError('business_history_period_not_available')
  if key in FRAME_FIELDS and carrier['series'].get('unit')!=ctx['unit']:raise ValueError('business_series_unit_changed')
  i=periods.index(period);value=carrier['series']['values'][i];suffix+=f'/series/values/{i}';period_pointer=pointer+suffix.rsplit('/values/',1)[0]+f'/years/{i}'
 else:
  if period!=current:raise ValueError('business_current_period_mismatch')
  value=carrier.get('value');suffix+='/value'
 evidence=[dict(kind='catalog_snapshot',path=engine.catalog_path,sha256=engine.catalog_hash,valuePointer=pointer+suffix,periodPointer=period_pointer)]
 warnings=['workplace_activity_not_resident_employment'];components={}
 if key in FRAME_FIELDS or key in SHARES:
  scope=dimension.split(':')[1] if dimension!='total' else 'industry' if key in SHARES else 'total'
  raw,ref=frame_record(engine,year,scope,str(row['code']));total,totref=frame_record(engine,year,'total',str(row['code']))
  if raw['town']!=row['town'] or total['town']!=row['town']:raise ValueError('business_geography_mismatch')
  expected=frame_value(key,raw,total);close(value,expected)
  source=ref['sourceUrl'];evidence.append(ref)
  release_year=re.search(r'anno-([0-9]{4})',source)
  if release_year and release_year.group(1)!=year:warnings.append('source_release_url_label_differs_from_reference_year')
  if key in SHARES:
   evidence.append(totref);components=dict(numerator=raw[SHARES[key]],denominator=total[SHARES[key]],scale=100)
  elif key=='turnoverPerPersonEmployed':components=dict(numerator=raw['turnoverThousandEuro']*1000,denominator=raw['personsEmployed'],scale=1)
  warnings+=['nominal_economic_values_not_real_growth','frame_value_added_not_municipal_gdp','frame_and_asia_universes_differ']
  if key in ('labourProductivity','valueAddedTurnoverShare','averageGrossRemunerationPerEmployee'):warnings.append('official_rounded_measure_preserved_no_implicit_weighting')
  # A current carrier must also agree with the materialized category and total.
  if not historical and key in FRAME_FIELDS:
   scope=dimension.split(':')[1] if dimension!='total' else 'total'
   close(row['economicScopes'][scope]['value'],expected)
 elif key=='microUnits':
  snap,ref=engine.file(MICRO);record=snap['records'][str(row['code'])];csv_source=snap['sources'][str(row['code'])]
  if hashlib.sha256(csv_source['csv'].encode()).hexdigest()!=csv_source['sha256']:raise ValueError('business_csv_hash_mismatch')
  csv_rows=list(csv.DictReader(io.StringIO(csv_source['csv'])))
  if len(csv_rows)!=2 or any(r['REF_AREA']!=str(row['code']) or r['TIME_PERIOD']!='2023' or r['DATA_TYPE']!='LU' or r['ECON_ACTIVITY_NACE_2007']!='0010' for r in csv_rows):raise ValueError('business_micro_csv_context_changed')
  if set(r['PERS_EMPL_SIZE_CLASS'] for r in csv_rows)!={'TOTAL','W0_9'}:raise ValueError('business_micro_classes_changed')
  for r in csv_rows:close(record[r['PERS_EMPL_SIZE_CLASS']],float(r['OBS_VALUE']))
  expected=record['W0_9']/record['TOTAL']*100
  close(value,expected,.0051);source=snap['sources'][str(row['code'])]['url']
  evidence.append(dict(ref,kind='source_snapshot',recordPointer='/records/'+str(row['code']),sourceUrl=source,csvSha256=snap['sources'][str(row['code'])]['sha256'],numerator=record['W0_9'],denominator=record['TOTAL']))
  warnings.append('micro_unit_share_rounded_no_inferred_counts')
 else:
  snap,ref=engine.file(ASIA);records=[(i,r) for i,r in enumerate(snap['towns']) if str(r['code'])==str(row['code'])]
  if len(records)!=1:raise ValueError('business_source_record_not_unique')
  i,record=records[0];asia=record['asia'];years=list(map(str,asia['years']))
  if len(set(years))!=len(years) or any(len(asia[f])!=len(years) for f in ('localUnits','employeesAverageAnnual')):raise ValueError('business_source_years_mismatch')
  if year not in years:raise ValueError('business_asia_period_not_available')
  j=years.index(year);units=asia['localUnits'][j];employees=asia['employeesAverageAnnual'][j]
  expected=units if key=='localUnits' else employees if key=='localEmployees' else employees/units
  if key in CHANGES:
   field='localUnits' if key=='localUnitsChange' else 'employeesAverageAnnual';base=asia[field][years.index('2018')];expected=(asia[field][j]/base-1)*100
   warnings.append('cumulative_baseline_change_not_year_on_year')
  close(value,expected)
  if key=='employeesPerLocalUnit':components=dict(numerator=employees,denominator=units,scale=1)
  source=snap['sources']['asia']['url'];evidence.append(dict(ref,kind='source_snapshot',recordPointer=f'/towns/{i}/asia',sourceUrl=source,acquisitionLayer=snap['acquisitionLayer']))
  if key in ('employeesPerLocalUnit',*CHANGES) and not historical:
   c=row.get('sourceBackedComponents')
   if c is not None:
    if c['sourceSnapshot']!=ASIA:raise ValueError('business_components_not_materialized')
    if key=='employeesPerLocalUnit':
     close(c['numerator'],employees);close(c['denominator'],units);close(c['normalized'],value)
    else:
     close(c['numerator'],asia[field][j]);close(c['denominator'],base);close(c['normalized'],value);close(c['absolute'],asia[field][j]-base)
    if token(key,c['referenceYear'])!=period or c['scale']!=(100 if key in CHANGES else 1):raise ValueError('business_component_context_changed')
 if historical and value is not None and year==current[-4:] and dimension=='total':close(row.get('value'),value)
 obs=dict(ctx,**components,metric=key,dimension=dimension,geography=str(row['code']),period=period,value=value,source=source,evidence=evidence,provenance=evidence,
  notApplicable=bool(row.get('notApplicable')) if not historical else False,dataUnavailable=value is None or (bool(row.get('dataUnavailable')) if not historical else False))
 if key in CHANGES:obs.update(baselinePeriod='2018',endpointPeriod=year)
 return obs,warnings


def benchmark(engine,key,scope,municipal):
 if scope not in benchmark_scopes(key,municipal['dimension']):raise ValueError('business_benchmark_scope_or_dimension_not_available')
 metric=engine._catalog['metrics'][key];period=municipal['period']
 if period!=token(key,metric['meta']['year']):raise ValueError('business_historical_benchmark_not_available')
 path=MICRO if key=='microUnits' else ASIA_BENCH if key in ASIA_UNITS else FRAME_BENCH
 snap,ref=engine.file(path);published=metric['meta'].get('benchmark')
 if not published or token(key,published['year'])!=period:raise ValueError('business_benchmark_carrier_mismatch')
 geography='Toscana' if scope=='tuscany' else 'Italia'
 if key in FRAME_FIELDS:
  raw=snap['raw'][geography]
  formulas={'businessTurnover':raw[7]/1000,'businessValueAdded':raw[6]/1000,'labourCost':raw[5]/1000,'grossOperatingMargin':(raw[6]-raw[5])/1000,'turnoverPerPersonEmployed':round(raw[7]/raw[2]*1000,6),'valueAddedTurnoverShare':raw[10],'averageGrossRemunerationPerEmployee':raw[13]*1000,'labourProductivity':raw[9]*1000}
  value=formulas[key];record_pointer='/raw/'+geography
 elif key=='microUnits':
  geo='ITE1' if scope=='tuscany' else 'IT';r=snap['records'][geo];value=r['W0_9']/r['TOTAL']*100;record_pointer='/records/'+geo
 else:
  raw=snap['evidence'];u=raw['LU'][scope];e=raw['LUEMPDAA'][scope]
  formulas={'localUnits':u['2023'],'localEmployees':e['2023'],'employeesPerLocalUnit':e['2023']/u['2023'],'localUnitsChange':(u['2023']/u['2018']-1)*100,'localEmployeesChange':(e['2023']/e['2018']-1)*100}
  value=formulas[key];record_pointer='/evidence'
 if key!='labourProductivity':
  b=snap['benchmarks'][key]
  if b['unit']!=municipal['unit'] and not (key=='localEmployees' and b['unit']=='number'):raise ValueError('business_benchmark_unit_changed')
  if 'year' in b and token(key,b['year'])!=period:raise ValueError('business_benchmark_source_period_mismatch')
  close(b[scope],value)
 close(published[scope],value)
 source=snap['sourceUrl'];evidence=[dict(ref,kind='source_snapshot',recordPointer=record_pointer,officialGeography=scope,sourceUrl=source),
  dict(kind='catalog_snapshot',path=engine.catalog_path,sha256=engine.catalog_hash,valuePointer=f'/metrics/{key}/meta/benchmark/{scope}',periodPointer=f'/metrics/{key}/meta/benchmark/year')]
 return dict(context(metric,key,municipal['dimension']),metric=key,dimension=municipal['dimension'],geography=scope,period=period,value=value,source=source,evidence=evidence,provenance=evidence,notApplicable=False,dataUnavailable=False)
