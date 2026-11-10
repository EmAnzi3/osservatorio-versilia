"""ACI registered cars: published rounding, native ratios and dated residents."""
from a6_pins import Pin as _pin
import math
from decimal import Decimal, ROUND_HALF_UP

from semantic_operations import finite
from semantic_query_library_adapters import TOWNS, fingerprint
from acquire_a3_benchmark_aci_istat_annual import latest_snapshot

MOTOR, EURO = KEYS = ('motorization', 'pollutingCars')
NATIVE = latest_snapshot()
Y = NATIVE[-9:-5]
POPULATION = 'data/source-snapshots/istat-demography-lotto-a-2026-08.json'
DEMO = 'data/source-snapshots/a3-istat-demography-benchmark-2026.json'
URL = 'https://aci.gov.it/attivita-e-progetti/studi-e-ricerche/autoritratto/'
UNITS = {MOTOR: 'per1000', EURO: 'percent'}
FORMULAS = {MOTOR: f'Autovetture ACI {Y} / popolazione residente al 1° gennaio 2026 × 1.000', EURO: 'autovetture Euro 0–3 / autovetture totali × 100'}
HASHES = {
    NATIVE: (_pin('vehicle#1'), _pin('vehicle#2')),
    POPULATION: (_pin('vehicle#3'), _pin('vehicle#4')),
    DEMO: (_pin('vehicle#5'), _pin('vehicle#6'))}
NOTES = ['vehicles_registered_stock_not_traffic_actual_use_or_resident_ownership',
         'vehicles_euro_classes_not_measured_air_quality_or_emissions',
         'vehicles_no_automatic_causal_or_policy_priority_claim']


def frozen(engine, path):
    data, ref = engine.file(path)
    if ref.get('path') != path or (ref.get('sha256'), fingerprint(data)) != HASHES[path]:
        raise ValueError('vehicles_frozen_input_changed')
    return data, ref


def equal(actual, expected):
    if not finite(actual) or not math.isclose(actual, expected, rel_tol=0, abs_tol=1e-9):
        raise ValueError('vehicles_public_native_mismatch')


def dimensions(key): return ['total', 'nativeRatio']
def scopes(key, dim): return ['tuscany', 'italy']
def operations(key, dim): return ['compare', 'rank', 'benchmark_gap'] + (['weighted_ratio'] if dim == 'nativeRatio' else [])


def selection_guard(key, dim, op):
    if op in ('series', 'absolute_change', 'relative_change', 'percentage_points', 'trend'):
        raise ValueError('vehicles_single_snapshot_no_history')
    if op == 'weighted_ratio' and dim != 'nativeRatio':
        raise ValueError('vehicles_native_ratio_dimension_required')
    if op == 'correlation': raise ValueError('vehicles_pair_not_jointly_reviewed')
    if op == 'anomaly': raise ValueError('vehicles_peer_anomaly_not_reviewed')


def context(metric, key, dim):
    meta = metric['meta']
    if (dim not in dimensions(key) or meta.get('key') != key or meta.get('theme') != 'mobilita'
            or meta.get('year') != Y or meta.get('unit') != UNITS[key]
            or meta.get('polarity') != ('neutral' if key == MOTOR else 'negative')
            or metric.get('sourceUrl') != URL or metric.get('method', {}).get('formula') != FORMULAS[key]
            or metric['method'].get('coverage') != '7/7'):
        raise ValueError('vehicles_definition_changed')
    return dict(unit=UNITS[key], population=f'ACI PRA registered municipal car stock {Y}; administrative location, not vehicle use',
                definition=FORMULAS[key], method='published one-decimal rate retained' if dim == 'total' else 'native integer components; no reverse derivation from public rounded rates',
                frequency='annual_snapshot', periodBasis=f'car stock {Y}; resident denominator 1 January 2026' if key == MOTOR else f'Euro 0–3 and all registered cars, both {Y}',
                nativeComponentsAvailable=dim == 'nativeRatio', adapter='vehicles/'+key+'/'+dim+'/v1')


def components(key, record, population):
    counts = record[4:]
    return (counts[-1], population, 1000) if key == MOTOR else (sum(counts[:4]), counts[-1], 100)


def validated(engine, key):
    metric = engine._catalog['metrics'][key]; context(metric, key, 'total')
    snap, ref = frozen(engine, NATIVE); demo, _ = frozen(engine, DEMO); posas, _ = frozen(engine, POPULATION)
    populations = {c: next(r['population'] for r in posas['posas']['towns'][name] if r['year'] == 2026) for c,name in TOWNS.items()}
    popmetric = engine._catalog['metrics']['population']
    if popmetric['meta'].get('year') != '2026' or len(popmetric['rows']) != 7 or {r.get('code') for r in popmetric['rows']} != set(TOWNS):
        raise ValueError('vehicles_denominator_period_or_identity_changed')
    for row in popmetric['rows']:
        if row['town'] != TOWNS[row['code']]: raise ValueError('vehicles_denominator_period_or_identity_changed')
        equal(row.get('value'), populations[row['code']])
    if (len(metric['rows']) != 7 or {r.get('code') for r in metric['rows']} != set(TOWNS)
            or {t['code']:t['name'] for t in engine._catalog['towns']} != TOWNS):
        raise ValueError('vehicles_municipal_identity_changed')
    records = {r[0]:(i,r) for i,r in enumerate(snap['records'])}; selected = {}
    for row in metric['rows']:
        code = row['code']; proof = snap['municipalReconciliation'][code]; index, record = records[proof['nativeRow']]
        if (row.get('town') != TOWNS[code] or row.get('slug') != '-'.join(TOWNS[code].lower().split())
                or record[1:4] != ['TOSCANA','LUCCA',TOWNS[code].upper()] or proof['town'] != TOWNS[code]
                or row.get('notApplicable') or row.get('dataUnavailable')
                or any(row.get(f) is not None for f in ('series','normalized','ratioComponents'))):
            raise ValueError('vehicles_municipal_definition_changed')
        equal(proof['population'], populations[code]); num,den,scale = components(key, record, populations[code])
        published = float((Decimal(num)/Decimal(den)*scale).quantize(Decimal('0.1'), rounding=ROUND_HALF_UP))
        equal(row.get('value'), published); equal(row.get('benchmarkValue'), published)
        selected[code] = (index, record, num, den, scale)
    total = sum(r[2] for r in selected.values())/sum(r[3] for r in selected.values())*next(iter(selected.values()))[4]
    if key == EURO:
        total = math.fsum(row['value']*selected[row['code']][3] for row in metric['rows'])/sum(r[3] for r in selected.values())
    equal(metric.get('aggregate', {}).get('value'), total)
    if metric['aggregate'].get('label') != ('Tasso Versilia' if key == MOTOR else 'Quota ponderata Versilia') or metric.get('normalizedAggregate') is not None:
        raise ValueError('vehicles_aggregate_definition_changed')
    meta = metric['meta'].get('benchmark') or {}
    if meta.get('year') != Y or meta.get('sourceSnapshot') != NATIVE or meta.get('url') != URL:
        raise ValueError('vehicles_benchmark_definition_changed')
    for scope, counts in [('tuscany',snap['regionTotals']['TOSCANA']),('italy',snap['officialNational'])]:
        population = demo['benchmarks']['population'][scope]
        equal(snap['population']['scopes'][scope], population)
        value = counts[-1]/population*1000 if key == MOTOR else sum(counts[:4])/counts[-1]*100
        equal(snap['benchmarks'][key][scope], value); equal(meta.get(scope), value)
    return snap, ref, selected, populations


def observation(engine, key, index, dim, period, historical):
    metric = engine._catalog['metrics'][key]; ctx = context(metric,key,dim)
    if period != Y: raise ValueError('vehicles_period_not_frozen')
    snap, ref, selected, populations = validated(engine,key); row = metric['rows'][index];code = row['code']
    j,record,num,den,scale = selected[code]
    evidence = [dict(kind='catalog_snapshot',path=engine.catalog_path,sha256=engine.catalog_hash,valuePointer=f'/metrics/{key}/rows/{index}/value',publishedPrecision='one decimal',nativeRatioDistinct=dim == 'nativeRatio'),
                dict(ref,kind='source_snapshot',recordPointer=f'/records/{j}',nativeRow=record[0],nativeCounts=record[4:],numeratorPointers=[f'/records/{j}/{i}' for i in ([19] if key == MOTOR else range(4,8))],workbookSha256=snap['source']['workbookSha256'],sourceUrl=URL)]
    if key == MOTOR:
        posas,pref = frozen(engine,POPULATION);k=next(i for i,r in enumerate(posas['posas']['towns'][row['town']]) if r['year'] == 2026)
        evidence.append(dict(pref,kind='denominator_snapshot',recordPointer=f'/posas/towns/{row["town"]}/{k}/population',denominatorDate='2026-01-01',nativeDenominator=den))
    else: evidence[1]['denominatorPointer'] = f'/records/{j}/19'
    notes = NOTES + ['vehicles_public_one_decimal_native_ratio_distinct', 'vehicles_public_euro_aggregate_weights_rounded_rates_native_pooling_distinct', f'vehicles_{Y}_stock_2026_residents_hybrid_explicit' if key == MOTOR else 'vehicles_total_includes_undefined_and_not_contemplated_classes_no_imputation']
    out = dict(ctx,metric=key,dimension=dim,geography=code,period=period,value=row['value'] if dim == 'total' else num/den*scale,source=URL,evidence=evidence,provenance=evidence,notApplicable=False,dataUnavailable=False,missingReason=None)
    if dim == 'nativeRatio': out.update(numerator=num,denominator=den,scale=scale,numeratorPeriod=Y,denominatorPeriod='2026-01-01' if key == MOTOR else Y)
    return out, notes


def benchmark(engine,key,scope,municipal):
    if scope not in scopes(key,municipal['dimension']) or municipal['period'] != Y:
        raise ValueError('vehicles_benchmark_scope_not_reviewed')
    snap,ref,_,_ = validated(engine,key)
    pointer = '/regionTotals/TOSCANA' if scope == 'tuscany' else '/officialNational'
    ev = [dict(ref,kind='source_snapshot',recordPointer=f'/benchmarks/{key}/{scope}',nativeCountsPointer=pointer,nativePanelRows=len(snap['records']),workbookSha256=snap['source']['workbookSha256']),dict(kind='catalog_snapshot',path=engine.catalog_path,sha256=engine.catalog_hash,valuePointer=f'/metrics/{key}/meta/benchmark/{scope}')]
    if key == MOTOR:
        _,dref = frozen(engine,DEMO);ev.append(dict(dref,kind='denominator_snapshot',recordPointer=f'/benchmarks/population/{scope}',denominatorDate='2026-01-01'))
    return dict(municipal,geography=scope,value=snap['benchmarks'][key][scope],evidence=ev,provenance=ev,benchmarkAggregation=f'native ACI {Y} count ratio; original workbook and full localization panel frozen, provincial/regional total rows excluded from sums; undefined/foreign locations retained',nativeComponentsAvailable=False,**({'numerator':None,'denominator':None,'scale':None} if 'numerator' in municipal else {}))
