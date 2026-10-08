"""ISPRA hazard snapshots: source populations, scenario overlap and rounded history."""
import math
import json
import hashlib
from semantic_operations import finite

KEYS=('floodExposure','landslideExposure')
NATIVE='data/source-snapshots/fragilita-comunale-v133.json'
URL='https://idrogeo.isprambiente.it/'
SPECS={'floodExposure':('flood','ispraFlood','2020',2011,('P3','P2','P1'),'P2'), 'landslideExposure':('landslide','ispraLandslide','2024',2021,('P3+P4','P4','P3','P2','P1','AA'),'P3+P4')}
FIELDS=('residentsPct','residents','areaPct','areaKm2')
HISTORY='history:areaPct:P3+P4'

def close(a,b,tol=1e-8):
    if not finite(a) or not finite(b) or not math.isclose(a,b,rel_tol=0,abs_tol=tol):raise ValueError('hazard_catalog_source_mismatch')

def token(key,period):return str(period)

def dimensions(key):return ['total',*(f'{f}:{s}' for s in SPECS[key][4] for f in FIELDS),*([HISTORY] if key=='landslideExposure' else [])]

def field_scenario(key,dimension):
    if dimension not in dimensions(key):raise ValueError('hazard_dimension_not_reviewed')
    return ('residentsPct',SPECS[key][5]) if dimension=='total' else ('history','P3+P4') if dimension==HISTORY else tuple(dimension.split(':',1))

def weighted(key,dimension):return field_scenario(key,dimension)[0] in ('residentsPct','areaPct')

def scopes(key,dimension):return []

def context(metric,key,dimension):
    kind,source,year,pop,scenarios,default=SPECS[key];field,scenario=field_scenario(key,dimension);meta=metric['meta']
    if str(meta.get('year'))!=year or meta.get('unit')!='percent' or meta.get('populationReference')!=pop or meta.get('defaultScenario')!=default or metric.get('sourceUrl')!=URL:raise ValueError('hazard_definition_or_reference_changed')
    unit='number' if field=='residents' else 'km2' if field=='areaKm2' else 'percent'
    population='source PAI area history; native past denominators not frozen' if field=='history' else f'ISPRA map {year}; municipal limits 2024; census residents {pop}' if field.startswith('residents') else 'ISPRA cartographic municipal territory; own frozen source denominator'
    return dict(unit=unit,population=population,definition=f'{kind} {scenario} '+('P3+P4 area history rounded to two decimals; not resident exposure' if field=='history' else field+' from official source scenario, not sums of classes'),method='frozen official mosaic; integer residents or native km2; published precision preserved',frequency='irregular',periodBasis='PAI area-share editions 2017, 2020, 2024; no attested continuity or historical raw components' if field=='history' else f'hazard map {year}; limits 2024; resident denominator {pop}; history continuity not attested',adapter='hazard/'+key+'/'+field+'/'+scenario+'/v1')

def selection_guard(key,dimension,operation):
    if operation in ('absolute_change','relative_change','percentage_points','trend'):raise ValueError('hazard_temporal_comparability_not_attested')
    if operation=='series' and dimension!=HISTORY:raise ValueError('hazard_historical_dimension_not_frozen')

def correlation_guard(observations,axis):
    if axis=='periods' and any(o['metric'] in KEYS for o in observations):raise ValueError('hazard_temporal_comparability_not_attested')

def native(engine,key,row):
    snap,ref=engine.file(NATIVE);kind,source,year,pop,scenarios,default=SPECS[key];src=snap['sources'][source]
    if hashlib.sha256(json.dumps(snap['provenance']['inputs'],sort_keys=True,separators=(',',':')).encode()).hexdigest()!='6080f3414ac93254c22cfcee648df7a6b384d00f46212a1fec154a8cca9f6617' or snap.get('schemaVersion')!=1 or (src.get('hazardReference'),src.get('municipalLimitsReference'),src.get('populationReference'))!=(int(year),2024,pop):raise ValueError('hazard_native_reference_changed')
    if len(engine._catalog['metrics'][key]['rows'])!=7 or set(snap['hazardsByTown'])!={r['town'] for r in engine._catalog['metrics'][key]['rows']}:raise ValueError('hazard_native_cohort_changed')
    identity=snap['istatByTown'][row['town']]
    if identity['code']!=row['code'] or identity['slug']!=row['slug'] or not any(t['name']==row['town'] and t['code']==row['code'] for t in engine._catalog['towns']):raise ValueError('hazard_row_identity_changed')
    n=snap['hazardsByTown'][row['town']];d=n['municipalAreaKm2'];p=n[f'population{pop}']
    if not finite(d) or d<=0 or type(p) is not int or p<=0 or set(n[kind])!=set(scenarios):raise ValueError('hazard_invalid_native_components')
    close(row['municipalAreaKm2'],d);close(row['populationBase'],p)
    if row.get('populationReference')!=pop:raise ValueError('hazard_population_reference_changed')
    if [v['key'] for v in row['parts']]!=list(scenarios):raise ValueError('hazard_scenario_order_changed')
    for scenario in scenarios:
        a=n[kind][scenario];public=next(v for v in row['parts'] if v['key']==scenario)
        if not finite(a['areaKm2']) or not 0<=a['areaKm2']<=d or type(a['residents']) is not int or not 0<=a['residents']<=p:raise ValueError('hazard_invalid_native_components')
        close(a['areaPct'],a['areaKm2']/d*100,.00050001);close(a['residentsPct'],a['residents']/p*100,.00050001)
        for f in FIELDS:close(public[f],a[f])
        close(public['value'],a['residentsPct'])
    if kind=='flood':
        for f in ('areaKm2','residents'):
            if not n[kind]['P3'][f]<=n[kind]['P2'][f]<=n[kind]['P1'][f]:raise ValueError('hazard_nested_scenarios_changed')
    # P3+P4 is the authoritative source field; never reconstructed from rounded classes.
    return n,ref

def available_periods(engine,key,dimension,row):
    n,ref=native(engine,key,row)
    if key!='landslideExposure' or dimension!=HISTORY:return [SPECS[key][2]]
    h=n['landslideP3P4History']
    if [v['year'] for v in h]!=[2017,2020,2024] or row.get('hazardHistory')!=h or any(not finite(v['value']) or not 0<=v['value']<=100 for v in h):raise ValueError('hazard_history_reference_changed')
    close(h[-1]['value'],n['landslide']['P3+P4']['areaPct'],.00500001)
    return [str(v['year']) for v in h]

def observation(engine,key,index,dimension,period,historical):
    m=engine._catalog['metrics'][key];row=m['rows'][index];ctx=context(m,key,dimension);kind,source,year,pop,scenarios,default=SPECS[key];field,scenario=field_scenario(key,dimension)
    n,ref=native(engine,key,row);parts={};notes=['hazard_maps_are_not_observed_damage_probabilities_or_policy_effects','hazard_flood_scenarios_nested_do_not_sum' if kind=='flood' else 'hazard_p3_p4_combined_official_field_not_sum_of_rounded_classes']
    if period not in available_periods(engine,key,dimension,row):raise ValueError('hazard_period_or_dimension_not_frozen')
    if field=='history':
        i=[str(v['year']) for v in n['landslideP3P4History']].index(period);value=n['landslideP3P4History'][i]['value'];pointer=f'/metrics/{key}/rows/{index}/hazardHistory/{i}/value';record=f'/hazardsByTown/{row["town"]}/landslideP3P4History/{i}/value'
        notes+=['hazard_history_area_pct_two_decimals_no_native_historical_components','hazard_history_readable_no_attested_temporal_comparability']
    else:
        a=n[kind][scenario];i=scenarios.index(scenario);value=row.get('value') if dimension=='total' else row['parts'][i][field]
        pointer=f'/metrics/{key}/rows/{index}/value' if dimension=='total' else f'/metrics/{key}/rows/{index}/parts/{i}/{field}';record=f'/hazardsByTown/{row["town"]}/{kind}/{scenario}/{field}'
        if value is not None:close(value,a[field])
        if field in ('residentsPct','areaPct'):
            resident=field=='residentsPct';parts=dict(numerator=a['residents' if resident else 'areaKm2'],denominator=n[f'population{pop}' if resident else 'municipalAreaKm2'],scale=100,numeratorPeriod=year,denominatorPeriod=str(pop) if resident else '2024')
        notes+=['hazard_residents_are_frozen_census_population_not_current_posas','hazard_native_ratios_and_published_three_decimal_percent_kept_separate']
    published=value
    if parts and value is not None:value=parts['numerator']/parts['denominator']*100
    evidence=[dict(kind='catalog_snapshot',path=engine.catalog_path,sha256=engine.catalog_hash,valuePointer=pointer),dict(ref,kind='source_snapshot',recordPointer=record)]
    return dict(ctx,**parts,metric=key,dimension=dimension,geography=row['code'],period=period,value=value,publishedValue=published,source=URL,provenance=evidence,evidence=evidence,notApplicable=bool(row.get('notApplicable')),dataUnavailable=value is None or bool(row.get('dataUnavailable'))),notes

def benchmark(engine,key,scope,municipal):raise ValueError('hazard_benchmark_not_frozen')
