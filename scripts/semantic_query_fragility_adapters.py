"""Frozen IFC ordinal classes and effective-2019 municipal accessibility."""
import math
import hashlib
import json
from statistics import median
from semantic_operations import finite

KEYS = ('municipalFragility', 'lowProductivityEmployment', 'essentialServicesAccessibility')
ORDINAL = KEYS[:2]
NATIVE = 'data/source-snapshots/fragilita-comunale-v133.json'
BENCHMARK = 'data/source-snapshots/a3-istat-accessibility-benchmark-2019.json'
URL = 'https://www.istat.it/comunicato-stampa/la-fragilita-dei-comuni-italiani-anno-2022/'
FIELDS = dict(zip(KEYS, ('COMP_FRAG_INDEX_DECILE', 'PERSEMP_LU_LOW_PRO_INDSERV_VENTILE', 'INDEX_ACCES_ESSENT_SERVICES')))
YEARS = [2018, 2019, 2021, 2022]

def close(a, b):
    if not finite(a) or not finite(b) or not math.isclose(a,b,rel_tol=0,abs_tol=1e-8):
        raise ValueError('fragility_catalog_source_mismatch')

def token(key, period): return str(period)
def dimensions(key): return ['total']
def scopes(key): return ['tuscany','italy'] if key==KEYS[2] else []
def operations(key):
    return ['compare','series'] if key in ORDINAL else ['compare','rank','benchmark_gap']

def selection_guard(key, operation):
    if operation not in operations(key):
        raise ValueError('fragility_ordinal_operation_not_supported' if key in ORDINAL else 'accessibility_operation_not_attested')

def context(metric, key, dimension):
    ordinal=key in ORDINAL; unit='decile' if key==KEYS[0] else 'ventile' if ordinal else 'minutes'
    meta=metric['meta']; year='2022' if ordinal else '2019'; maximum=10 if key==KEYS[0] else 20
    if dimension!='total' or meta.get('unit')!=unit or str(meta.get('year'))!=year or metric.get('sourceUrl')!=URL:
        raise ValueError('fragility_definition_or_reference_changed')
    if ordinal and (meta.get('ordinalScale',{}).get('min')!=1 or meta.get('ordinalScale',{}).get('max')!=maximum or meta.get('suppressRank') is not True):
        raise ValueError('fragility_ordinal_scale_changed')
    return dict(unit=unit,population='municipalities; each ordinal class is a relative position, not an amount' if ordinal else 'municipal center to nearest Polo/Polo intercomunale; not resident travel times',
        definition='IFC '+FIELDS[key]+' ordinal class; unequal intervals cannot be assumed' if ordinal else 'car journey time from municipal center to nearest essential-service pole',
        method='frozen Istat published ordinal classes; no cardinal transformations' if ordinal else 'Istat accessibility component, effective 2019; exported in IFC 2022',
        frequency='irregular' if ordinal else 'snapshot',periodBasis='2018, 2019, 2021, 2022; 2020 absent; IFC deciles use 2018 distribution' if key==KEYS[0] else 'published IFC ventiles 2018, 2019, 2021, 2022; no cardinal productivity amounts' if ordinal else 'effective 2019; release 2022, municipal geography December 31 2022',
        adapter='fragility/'+key+'/v1')

def native(engine, key, row):
    snap,ref=engine.file(NATIVE);src=snap['sources']['istat']
    if snap.get('schemaVersion')!=1 or src.get('referenceYear')!=2022 or src.get('availableYears')!=YEARS or src.get('officialUrl')!=URL or hashlib.sha256(json.dumps(snap['provenance']['inputs'],sort_keys=True,separators=(',',':')).encode()).hexdigest()!='6080f3414ac93254c22cfcee648df7a6b384d00f46212a1fec154a8cca9f6617':
        raise ValueError('fragility_native_reference_changed')
    rows=engine._catalog['metrics'][key]['rows']
    if len(rows)!=7 or {r['town'] for r in rows}!=set(snap['istatByTown']):raise ValueError('fragility_native_cohort_changed')
    n=snap['istatByTown'][row['town']]
    if n['code']!=row['code'] or n['slug']!=row['slug'] or not any(t['name']==row['town'] and t['code']==row['code'] for t in engine._catalog['towns']):raise ValueError('fragility_row_identity_changed')
    f=FIELDS[key];v=n['latest2022'][f]
    if key in ORDINAL:
        h=n['series'][f];maximum=10 if key==KEYS[0] else 20
        if [x['year'] for x in h]!=YEARS or any(type(x['value']) is not int or not 1<=x['value']<=maximum for x in h) or h[-1]['value']!=v:raise ValueError('fragility_invalid_ordinal_history')
        if row.get('series')!={'years':YEARS,'values':[x['value'] for x in h]}:raise ValueError('fragility_public_history_changed')
    else:
        if not finite(v) or v<0 or row.get('series') is not None or '2019' not in src.get('componentReferenceNotes',{}).get(f,''):raise ValueError('accessibility_effective_reference_changed')
    if row.get('value') is not None:close(row['value'],v)
    return n,ref

def available_periods(engine,key,dimension,row):
    native(engine,key,row)
    return list(map(str,YEARS)) if key in ORDINAL else ['2019']

def observation(engine,key,index,dimension,period,historical):
    metric=engine._catalog['metrics'][key];row=metric['rows'][index];ctx=context(metric,key,dimension);n,ref=native(engine,key,row);field=FIELDS[key]
    if period not in available_periods(engine,key,dimension,row):raise ValueError('fragility_period_not_frozen')
    if historical and key in ORDINAL:
        i=YEARS.index(int(period));value=row['series']['values'][i];pointer=f'/metrics/{key}/rows/{index}/series/values/{i}';record=f'/istatByTown/{row["town"]}/series/{field}/{i}/value'
    else:
        value=row.get('value');pointer=f'/metrics/{key}/rows/{index}/value';record=f'/istatByTown/{row["town"]}/latest2022/{field}'
        if key in ORDINAL and period!='2022':raise ValueError('fragility_period_not_frozen')
    evidence=[dict(kind='catalog_snapshot',path=engine.catalog_path,sha256=engine.catalog_hash,valuePointer=pointer),dict(ref,kind='source_snapshot',recordPointer=record)]
    notes=['ordinal_classes_not_amounts_no_mean_changes_or_rank'] if key in ORDINAL else ['accessibility_2019_not_2022_no_repeated_export_history','municipal_center_time_not_resident_population_mean','zero_minutes_is_valid_pole_location']
    return dict(ctx,metric=key,dimension=dimension,geography=row['code'],period=period,value=value,source=URL,provenance=evidence,evidence=evidence,notApplicable=bool(row.get('notApplicable')),dataUnavailable=value is None or bool(row.get('dataUnavailable'))),notes

def benchmark(engine,key,scope,municipal):
    if key!=KEYS[2] or scope not in scopes(key):raise ValueError('fragility_benchmark_scope_not_reviewed')
    s,ref=engine.file(BENCHMARK);meta=engine._catalog['metrics'][key]['meta']['benchmark']
    if s.get('schemaVersion')!=1 or s.get('referenceYear')!=2019 or s.get('releaseYear')!=2022 or s.get('sourceUrl')!=URL or s.get('aggregation')!='median-municipalities' or s['source'].get('csvSha256')!='ef2632be1de3466cfda3b81ee335a5247504e7b36980b8cb6259f9caf1c24f0a' or s['source'].get('structureSha256')!='85ec85c259f644de767309199a29bc57d369e7665bf2182f1a2e973d26f36d20' or s.get('qualityGate',{}).get('status')!='PASS':raise ValueError('accessibility_benchmark_reference_changed')
    records=s['records'];codes=[r[0] for r in records];tuscany=[v for c,v in records if c[:3] in ('045','046','047','048','049','050','051','052','053','100')]
    if len(records)!=7903 or len(set(codes))!=7903 or '081025' in codes or len(tuscany)!=273 or any(not finite(v) or v<0 for c,v in records):raise ValueError('accessibility_benchmark_cohort_changed')
    for row in engine._catalog['metrics'][key]['rows']:
        n,_=native(engine,key,row);v=n['latest2022'][FIELDS[key]];close(dict(records)[row['code']],v);close(s['municipalReconciliation'][row['code']]['value'],v)
    if str(meta.get('year'))!='2019' or meta.get('url')!=URL or meta.get('sourceSnapshot')!=BENCHMARK or s['benchmarks'][key].get('unit')!='minutes' or s['benchmarks'][key].get('year')!='2019':raise ValueError('accessibility_benchmark_reference_changed')
    value=median(tuscany if scope=='tuscany' else [v for c,v in records]);close(value,s['benchmarks'][key][scope]);close(value,meta[scope])
    evidence=[dict(ref,kind='source_snapshot',recordPointer=f'/benchmarks/{key}/{scope}'),dict(kind='catalog_snapshot',path=engine.catalog_path,sha256=engine.catalog_hash,valuePointer=f'/metrics/{key}/meta/benchmark/{scope}')]
    return dict(municipal,geography=scope,value=value,provenance=evidence,evidence=evidence,benchmarkAggregation='unweighted municipality median',benchmarkMunicipalities=273 if scope=='tuscany' else 7903)
