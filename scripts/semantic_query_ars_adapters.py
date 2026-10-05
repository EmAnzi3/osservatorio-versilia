"""Reviewed ARS carriers: published measurements, never reconstructed aggregates."""
import json
import math
import re
from pathlib import Path
from urllib.parse import urlparse

from semantic_operations import finite

ROOT = Path(__file__).resolve().parents[1]
DEMOGRAPHIC = 'data/source-snapshots/ars-salute-demographics-v140.json'
LEGACY = 'data/source-snapshots/ars-a3-5-legacy-history.json'
HISTORY = 'data/source-snapshots/ars-salute-11-v140.json'
LIFE = 'data/source-snapshots/ars-life-expectancy-1290-2008-2022.json'
SEX = {'total':'totale', 'sex:men':'maschi', 'sex:women':'femmine'}
# Discover reviewed source definitions, not a second canonical metric inventory.
_DEMOS = json.loads((ROOT/DEMOGRAPHIC).read_text())['indicators']
_LEGACY = json.loads((ROOT/LEGACY).read_text())['indicators']
_SPECS = {s['key']:dict(id=i,unit=s['unit'],period=s['period'],ages=s['strato1Values']) for i,s in _DEMOS.items()}
LEGACY_ONLY = ('chronicTotal','hospitalizedAll')
for key in LEGACY_ONLY:
    _SPECS[key] = dict(id=str(_LEGACY[key]['indicatorId']),unit='per1000',period=_LEGACY[key]['periods'][-1],ages=[])
KEYS = tuple(k for k in _SPECS if k != 'elderlyHomeCare')


def token(period):
    value=str(period).replace('–','-').replace('—','-')
    if re.fullmatch(r'\d{4}',value):return value
    if re.fullmatch(r'\d{4}-\d{4}',value) and int(value[:4])<int(value[-4:]):return value
    raise ValueError('ars_explicit_year_or_window_required')


def order(period):
    p=token(period);return (int(p[-4:]),int(p[:4]))


def dimensions(key):
    spec=_SPECS[key]
    if key in LEGACY_ONLY:return ['total']
    dims=list(SEX)
    for age in spec['ages']:
        if age!='totale':dims.extend('age:'+age+'|'+sex for sex in SEX)
    return dims


def selection(dimension):
    if dimension in SEX:return 'totale',SEX[dimension]
    age,sex=dimension.split('|');return age.removeprefix('age:'),SEX[sex]


def context(metric,key,dimension):
    spec=_SPECS[key];meta=metric['meta']
    if dimension not in dimensions(key):raise ValueError('ars_dimension_not_reviewed')
    if meta.get('unit')!=spec['unit'] or token(meta['year'])!=spec['period']:
        raise ValueError('ars_unit_or_publication_period_changed')
    if key in LEGACY_ONLY and any(not isinstance(r.get('series'),dict) or r['series'].get('sourceSnapshot')!=LEGACY for r in metric['rows']):
        raise ValueError('ars_history_carrier_not_materialized')
    source=meta.get('demographicSource')
    if key not in LEGACY_ONLY:
        if not source:raise ValueError('ars_dimension_carrier_not_materialized')
        if str(source.get('indicatorId'))!=spec['id'] or source.get('snapshot')!=DEMOGRAPHIC or token(source.get('period'))!=spec['period']:
            raise ValueError('ars_source_context_changed')
        measurement='misura_grezza' if key=='lifeExpectancy' else 'misura_standardizzata (Totale); misura_grezza (fasce d’età)' if spec['ages'] else 'misura_standardizzata'
        if source.get('measurement')!=measurement:raise ValueError('ars_measurement_changed')
    if urlparse(metric.get('sourceUrl','')).hostname!='www.ars.toscana.it':raise ValueError('ars_source_changed')
    age,sex=selection(dimension);measure='raw' if key=='lifeExpectancy' or age!='totale' else 'standardized'
    width=int(spec['period'][-4:])-int(spec['period'][:4])+1 if '-' in spec['period'] else 1
    return dict(unit=spec['unit'],population=f'ARS {key} source reference universe; age {age}; sex {sex}',
        definition=f'ARS {spec["id"]} {key}; {measure} published measure; age {age}; sex {sex}',
        method='ARS published '+measure+' measure',frequency='annual' if width==1 else f'rolling_{width}_year_window',
        periodBasis='ARS calendar reference year' if width==1 else f'complete ARS {width}-year window; never endpoint year',
        adapter=f'ars-{spec["id"]}-reviewed/v1')


def close(actual,expected,tolerance=1e-8):
    if actual is None and expected is None:return
    if not finite(actual) or not finite(expected) or not math.isclose(actual,expected,rel_tol=0,abs_tol=tolerance):
        raise ValueError('ars_catalog_source_reconciliation_failed')


def source(engine,path,pointer,url,**extra):
    _,ref=engine.file(path)
    return dict(ref,kind='source_snapshot',recordPointer=pointer,sourceUrl=url,**extra)


def history(engine,key,dimension):
    if key=='lifeExpectancy':
        s,_=engine.file(LIFE)
        if s['indicator']['id']!=1290:raise ValueError('ars_history_indicator_changed')
        return list(map(str,s['scope']['years']))
    if dimension!='total':raise ValueError('ars_historical_dimension_not_available')
    if key in _LEGACY:
        s,_=engine.file(LEGACY);return s['indicators'][key]['periods']
    s,_=engine.file(HISTORY);spec=s['indicators'][_SPECS[key]['id']]
    if spec['key']!=key or spec['measurementField']!='misura_standardizzata':raise ValueError('ars_history_measurement_changed')
    return spec['periods']


def available_periods(engine,key,dimension):return list(map(token,history(engine,key,dimension)))


def historical_value(engine,metric,row,key,dimension,period):
    periods=available_periods(engine,key,dimension)
    if period not in periods:raise ValueError('ars_history_period_not_available')
    index=periods.index(period)
    if key=='lifeExpectancy':
        s,_=engine.file(LIFE);sex=selection(dimension)[1]
        expected=s['series'][str(row['code'])][sex][index]
        partindex=next(i for i,p in enumerate(row['parts']) if p['key']==sex)
        carrier=row['parts'][partindex]['series'];prefix=f'/parts/{partindex}/series'
        ref=source(engine,LIFE,f'/series/{row["code"]}/{sex}/{index}',s['indicator']['exportUrl'],archiveSha256=s['source']['csvSha256'],measurement='raw')
        tolerance=.0051
    elif key in _LEGACY:
        s,_=engine.file(LEGACY);spec=s['indicators'][key]
        if str(spec['indicatorId'])!=_SPECS[key]['id']:raise ValueError('ars_history_indicator_changed')
        expected=spec['values'][row['town']][index]
        carrier=row['series'];prefix='/series'
        if not isinstance(carrier,dict):raise ValueError('ars_history_carrier_not_materialized')
        if carrier.get('sourceSnapshot')!=LEGACY:raise ValueError('ars_history_carrier_changed')
        ref=source(engine,LEGACY,f'/indicators/{key}/values/{row["town"]}/{index}',spec['exportUrl'],archiveSha256=spec['sourceFile']['sha256'],measurement='standardized')
        tolerance=1e-8
    else:
        s,_=engine.file(HISTORY);spec=s['indicators'][_SPECS[key]['id']]
        records=[(i,r) for i,r in enumerate(spec['series'][row['town']]) if r['period']==period]
        if len(records)!=1:raise ValueError('ars_history_record_not_unique')
        rawindex,raw=records[0];expected=raw['standardized'];carrier=row['series'];prefix='/series'
        ref=source(engine,HISTORY,f'/indicators/{_SPECS[key]["id"]}/series/{row["town"]}/{rawindex}',spec['exportUrl'],archiveSha256=spec['sourceFile']['sha256'],measurement='standardized',ci95Low=raw['ci95Low'],ci95High=raw['ci95High'])
        tolerance=.0051
    if not isinstance(carrier,dict):raise ValueError('ars_history_carrier_not_materialized')
    if list(map(token,carrier['years']))!=periods or len(carrier['values'])!=len(periods):raise ValueError('ars_history_carrier_periods_mismatch')
    value=carrier['values'][index]
    if value is not None:close(value,expected,tolerance)
    return value,prefix+f'/values/{index}',prefix+f'/years/{index}',ref


def demographic_record(engine,key,dimension,geo,period):
    s,_=engine.file(DEMOGRAPHIC);spec=s['indicators'][_SPECS[key]['id']]
    if spec['key']!=key or spec['unit']!=_SPECS[key]['unit'] or spec['period']!=period:raise ValueError('ars_record_context_mismatch')
    age,sex=selection(dimension)
    records=[(i,r) for i,r in enumerate(spec['rows']) if str(r['geoCode']).zfill(6)==str(geo).zfill(6) and r['period']==period and r['sex']==sex and (r['strato1'] or 'totale')==age and r['strato2'] is None]
    if len(records)!=1:raise ValueError('ars_record_not_unique')
    index,record=records[0];measure='raw' if key=='lifeExpectancy' or age!='totale' else 'standardized'
    ref=source(engine,DEMOGRAPHIC,f'/indicators/{_SPECS[key]["id"]}/rows/{index}',spec['exportUrl'],archiveSha256=spec['sourceSha256'],measurement=measure,
        reportedNumerator=record['num'],reportedDenominator=record['den'],crudeRate=record['raw'],standardizedRate=record['standardized'],
        ci95Low=None if measure=='raw' and record['ci95Low']==record['ci95High']==0 else record['ci95Low'],
        ci95High=None if measure=='raw' and record['ci95Low']==record['ci95High']==0 else record['ci95High'],
        componentUse='source context only; never weights for standardized rates or life expectancy')
    return record[measure],record,ref


def observation(engine,key,row_index,dimension,period,historical):
    metric=engine._catalog['metrics'][key];row=metric['rows'][row_index];ctx=context(metric,key,dimension)
    current=token(metric['meta']['year']);base=f'/metrics/{key}/rows/{row_index}'
    notes=['snapshot_is_not_live_source_verification','health_indicator_not_cause_or_policy_priority']
    if key in ('chronicTotal','diabetes','dementia') or _SPECS[key]['ages']:notes+=['administrative_detection_not_total_population_need']
    if 'standardized' in ctx['method']:notes+=['standardized_rate_not_crude_ratio']
    elif key=='lifeExpectancy':notes+=['life_expectancy_raw_field_not_crude_event_rate','structural_zero_components_not_weights']
    else:notes+=['age_specific_raw_rate_not_standardized','structural_zero_standardized_field_not_observed_zero']
    if '-' in period:
        if '-' not in current or int(period[-4:])-int(period[:4])!=int(current[-4:])-int(current[:4]):raise ValueError('ars_window_width_mismatch')
        notes+=['overlapping_windows_not_independent_years']
    if historical and key not in _LEGACY:notes+=['published_history_rounding_preserved']
    if period!=current or historical:
        value,pointer,period_pointer,ref=historical_value(engine,metric,row,key,dimension,period)
    elif key in LEGACY_ONLY:
        value,pointer,period_pointer,ref=historical_value(engine,metric,row,key,dimension,period)
        close(row['value'],value,.055)
    else:
        expected,raw,ref=demographic_record(engine,key,dimension,row['code'],period)
        age,sex=selection(dimension);partkey=sex if not _SPECS[key]['ages'] else age+'|'+sex
        selected=[(i,p) for i,p in enumerate(row['parts']) if p['key']==partkey]
        if len(selected)!=1:raise ValueError('ars_part_not_unique')
        i,part=selected[0];measure=ref['measurement']
        if part['measurement']!=measure or part['unit']!=ctx['unit']:raise ValueError('ars_measurement_changed')
        value=part['value']
        if value is not None:close(value,expected)
        for name in ('raw','standardized'):close(part[name],raw[name])
        for name,field in [('numerator','num'),('denominator','den')]:
            expected_component=None if raw['num']==raw['den']==0 else raw[field]
            close(part[name],expected_component)
        close(part['ci95Low'],ref['ci95Low']);close(part['ci95High'],ref['ci95High'])
        if dimension=='total' and row['value'] is not None:close(row['value'],expected,.055)
        pointer=f'/parts/{i}/value';period_pointer=f'/metrics/{key}/meta/year'
    if not period_pointer.startswith('/metrics/'):period_pointer=base+period_pointer
    evidence=[dict(kind='catalog_snapshot',path=engine.catalog_path,sha256=engine.catalog_hash,valuePointer=base+pointer,periodPointer=period_pointer),ref]
    if historical and period==current and finite(value):
        expected=row['value'] if dimension=='total' else next(p['value'] for p in row['parts'] if p['key']==selection(dimension)[1])
        close(value,expected,.055)
    return dict(ctx,metric=key,dimension=dimension,geography=str(row['code']),period=period,value=value,source=ref['sourceUrl'],evidence=evidence,provenance=evidence,
        notApplicable=bool(row.get('notApplicable')) if not historical else False,dataUnavailable=value is None or bool(row.get('dataUnavailable'))),notes


def benchmark(engine,key,scope,municipal):
    if scope not in ('tuscany','versilia'):raise ValueError('ars_benchmark_scope_not_available')
    period=municipal['period'];dimension=municipal['dimension'];metric=engine._catalog['metrics'][key]
    if period!=token(metric['meta']['year']):raise ValueError('ars_historical_benchmark_not_available')
    if key in LEGACY_ONLY:
        if scope!='versilia':raise ValueError('ars_benchmark_scope_not_available')
        s,_=engine.file(LEGACY);spec=s['indicators'][key];index=spec['periods'].index(period);value=spec['values']['Versilia'][index]
        close(metric['aggregate']['value'],value,.055)
        ref=source(engine,LEGACY,f'/indicators/{key}/values/Versilia/{index}',spec['exportUrl'],archiveSha256=spec['sourceFile']['sha256'])
    else:
        value,_,ref=demographic_record(engine,key,dimension,'90' if scope=='tuscany' else '202M',period)
        age,sex=selection(dimension)
        partkey=sex if not _SPECS[key]['ages'] else age+'|'+sex
        carrier=metric['tuscany'] if scope=='tuscany' else metric['aggregate']
        parts=[p for p in carrier['parts'] if p['key']==partkey]
        if len(parts)!=1:raise ValueError('ars_benchmark_part_not_unique')
        published=parts[0]
        if published['unit']!=municipal['unit'] or published['measurement']!=ref['measurement']:raise ValueError('ars_benchmark_measurement_changed')
        close(published['value'],value)
        if scope=='tuscany' and token(carrier['period'])!=period:raise ValueError('ars_published_benchmark_period_changed')
    evidence=[dict(ref,kind='benchmark_snapshot',officialGeography='Regione Toscana' if scope=='tuscany' else 'Zona Versilia')]
    return dict(context(metric,key,dimension),metric=key,dimension=dimension,geography=scope,period=period,value=value,source=ref['sourceUrl'],evidence=evidence,provenance=evidence,notApplicable=False,dataUnavailable=value is None)
