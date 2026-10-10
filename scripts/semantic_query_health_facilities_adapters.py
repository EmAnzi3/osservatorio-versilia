"""Frozen pharmacy locations and accredited RSA; presence is not care access."""
import math

from semantic_operations import finite
from semantic_query_library_adapters import TOWNS, fingerprint

PHARMACY, RSA = KEYS = ('pharmaciesPer1000', 'accreditedRsaCount')
PHARMACY_FILE = 'data/source-snapshots/a3-health-pharmacies-benchmark-2025.json'
RSA_FILE = 'data/source-snapshots/a3-toscana-rsa-accredited-benchmark-2025.json'
RSA_LOCAL = 'data/source-snapshots/regione-toscana-rsa-accreditate-2025-v140.json'
POPULATION = 'data/source-snapshots/istat-demography-lotto-a-2026-08.json'
DEMO = 'data/source-snapshots/a3-istat-demography-benchmark-2026.json'
PATHS = {PHARMACY: PHARMACY_FILE, RSA: RSA_FILE}
UNITS = {PHARMACY: 'per1000', RSA: 'count'}
URLS = {PHARMACY: 'https://www.dati.salute.gov.it/', RSA: 'https://servizi.toscana.it/RT/RSA/'}
HASHES = {'data/source-snapshots/a3-health-pharmacies-benchmark-2025.json': ('b3cd66730e3b18dffd2e4bcfd138051ad1ab4ab262f38b8dffef0ee0783be4f4', 'b6b490ed0dc132a7184959cc59b7c2e47a9828e1a095c01b77b624d61b389ec4'), 'data/source-snapshots/a3-toscana-rsa-accredited-benchmark-2025.json': ('db7b92da7ef9855341dac701053e703676c768eaacbc5c0aa5709f55a728d3e6', '74aad180601b2e7053ca65ec3a7a3e07927c0594b06da655ceaccbf4ab0f0025'), 'data/source-snapshots/regione-toscana-rsa-accreditate-2025-v140.json': ('f8249dbeaf3a3c484439dcc5bff39887cc9c2885e418f5cc746a868d5125b3ae', 'a9d2c5d2c6eb464f82a3c3b62b17d147bd4e1c4dc38f068fdd6b616b60654318'), 'data/source-snapshots/istat-demography-lotto-a-2026-08.json': ('8ec47305870a84cd0da4fd0b36dc0ee33693557cec4df0796f56d04f78bb68f7', '24713ad8f1ebeb3b588790973fa4909aa2151f1005b63342691e4129ca852a07'), 'data/source-snapshots/a3-istat-demography-benchmark-2026.json': ('63a5fdefa71a4484edd65f69d1a754ce4f291fd563f9683c76332635a145f943', '82ea7b47b6f4ca16d7c4a71cd1a6806d537aa75940ffbb4aa9dc1f79776acef3')}  # Filled from the reviewed, versioned snapshots; never generated at runtime.
NOTES = ['health_facilities_presence_not_access_capacity_quality_or_policy_priority',
         'health_facilities_zero_is_local_presence_not_absence_of_services',
         'health_facilities_no_automatic_relation_to_resident_health_outcomes']


def frozen(engine, path):
    value, ref = engine.file(path)
    if ref.get('path') != path or (ref.get('sha256'), fingerprint(value)) != HASHES[path]:
        raise ValueError('health_facilities_frozen_input_changed')
    return value, ref


def equal(actual, expected):
    if not finite(actual) or not math.isclose(actual, expected, rel_tol=0, abs_tol=1e-9):
        raise ValueError('health_facilities_public_native_mismatch')


def dimensions(key): return ['total']
def scopes(key, dim): return ['tuscany', 'italy'] if key == PHARMACY else []
def operations(key, dim): return ['compare', 'rank'] + (['benchmark_gap'] if key == PHARMACY else [])


def selection_guard(key, dim, op):
    if op in ('series', 'absolute_change', 'relative_change', 'percentage_points', 'trend'):
        raise ValueError('health_facilities_single_snapshot_no_history')
    if op == 'weighted_ratio': raise ValueError('health_facilities_public_rounded_rate_no_reviewed_pooling')
    if op == 'correlation': raise ValueError('health_facilities_pair_not_jointly_reviewed')
    if op == 'anomaly': raise ValueError('health_facilities_peer_anomaly_not_reviewed')
    if op == 'benchmark_gap' and key == RSA:
        raise ValueError('health_facilities_rsa_absolute_regional_stock_not_municipal_rate')


def context(metric, key, dim):
    meta = metric['meta']
    if (dim != 'total' or meta.get('key') != key or meta.get('year') != '2025'
            or meta.get('unit') != UNITS[key] or meta.get('polarity') != 'neutral'
            or metric.get('sourceUrl') != URLS[key]):
        raise ValueError('health_facilities_definition_changed')
    return dict(unit=UNITS[key], population='localized public pharmacy sites, including branches and dispensaries' if key == PHARMACY else 'localized accredited RSA structures, not residents assisted or beds',
                definition='valid unique ministerial site at 31 December 2025 / estimated residents 1 January 2026 × 1000' if key == PHARMACY else 'unique accredited RSA structures present at 31 December 2025',
                method='native site count / native POSAS residents, public round(value,2) retained' if key == PHARMACY else 'native municipal name and facility name deduplication, exact integer count',
                frequency='annual_snapshot', periodBasis='stock 31 December 2025; pharmacy denominator 1 January 2026 explicit',
                nativeComponentsAvailable=False, adapter='health-facilities/'+key+'/v1')


def validated(engine, key):
    metric = engine._catalog['metrics'][key]; context(metric, key, 'total')
    snap, ref = frozen(engine, PATHS[key]); rows = metric['rows']
    if (len(rows) != 7 or {r.get('code') for r in rows} != set(TOWNS)
            or {t['code']: t['name'] for t in engine._catalog['towns']} != TOWNS):
        raise ValueError('health_facilities_municipal_identity_changed')
    if key == PHARMACY:
        demo, _ = frozen(engine, POPULATION); regional, _ = frozen(engine, DEMO)
        populations = {c: next(x['population'] for x in demo['posas']['towns'][n] if x['year'] == 2026) for c,n in TOWNS.items()}
        counts = {c: sum(r[2] == c for r in snap['records']) for c in TOWNS}
        values = {c: round(counts[c]/populations[c]*1000, 2) for c in TOWNS}
        public_pop = engine._catalog['metrics']['population']
        if public_pop['meta']['year'] != '2026': raise ValueError('health_facilities_denominator_period_changed')
        pop_rows = public_pop['rows']
        if len(pop_rows) != 7 or {r.get('code') for r in pop_rows} != set(TOWNS):
            raise ValueError('health_facilities_denominator_identity_changed')
        for row in pop_rows:
            if row['town'] != TOWNS[row['code']]: raise ValueError('health_facilities_denominator_identity_changed')
            equal(row.get('value'), populations[row['code']])
        total = sum(counts.values()) / sum(populations.values()) * 1000
        if metric['method'].get('formula') != 'Sedi con codice ministeriale univoco valide al 31 dicembre 2025 / popolazione residente al 1° gennaio 2026 × 1.000.':
            raise ValueError('health_facilities_formula_changed')
        for scope in ('tuscany','italy'):
            equal(snap['raw'][scope]['population'],regional['benchmarks']['population'][scope])
    else:
        local, _ = frozen(engine, RSA_LOCAL)
        unique = {(r[0],r[2]) for r in snap['records']}
        counts = {c: sum(town.casefold() == n.casefold() for town,_ in unique) for c,n in TOWNS.items()}
        values = counts; populations = None; total = sum(counts.values())
        if len(unique) != snap['benchmarks'][key]['tuscany'] or counts != {c:local['series'][n] for c,n in TOWNS.items()}:
            raise ValueError('health_facilities_rsa_reconciliation_changed')
        if metric['method'].get('formula') != 'Conteggio delle strutture accreditate presenti nel Comune.':
            raise ValueError('health_facilities_formula_changed')
    for row in rows:
        code = row['code']
        if (row.get('town') != TOWNS[code] or row.get('slug') != '-'.join(TOWNS[code].lower().split())
                or row.get('notApplicable') or row.get('dataUnavailable')):
            raise ValueError('health_facilities_municipal_identity_changed')
        equal(row.get('value'), values[code]); equal(row.get('benchmarkValue'), values[code])
        history = row.get('series')
        if key == PHARMACY and history is not None or key == RSA and (history != dict(years=[2025],values=[values[code]]) or not finite(history['values'][0])):
            raise ValueError('health_facilities_history_changed')
        if row.get('normalized') is not None or row.get('ratioComponents') is not None:
            raise ValueError('health_facilities_unreviewed_components_changed')
    aggregate = metric.get('aggregate') or {}; equal(aggregate.get('value'), total)
    if aggregate.get('label') != ('Densità Versilia' if key == PHARMACY else 'Totale nei 7 Comuni') or metric.get('normalizedAggregate') is not None:
        raise ValueError('health_facilities_aggregate_definition_changed')
    meta = metric['meta'].get('benchmark') or {}; native = snap['benchmarks'][key]
    if meta.get('year') != '2025' or meta.get('sourceSnapshot') != PATHS[key] or meta.get('url') != snap['sourceUrl']:
        raise ValueError('health_facilities_benchmark_definition_changed')
    for scope in ('tuscany','italy'):
        if native[scope] is None:
            if meta.get(scope) is not None: raise ValueError('health_facilities_benchmark_imputed')
        else: equal(meta.get(scope), native[scope])
    return snap, ref, counts, populations


def observation(engine, key, index, dim, period, historical):
    metric = engine._catalog['metrics'][key]; ctx = context(metric,key,dim)
    snap, ref, counts, populations = validated(engine,key); row = metric['rows'][index]; code=row['code']
    if period != '2025': raise ValueError('health_facilities_period_not_frozen')
    evidence = [dict(kind='catalog_snapshot',path=engine.catalog_path,sha256=engine.catalog_hash,valuePointer=f'/metrics/{key}/rows/{index}/value'),
                dict(ref,kind='source_snapshot',recordPointer='/records',recordSelection=dict(municipalityCode=code) if key == PHARMACY else dict(municipalityName=row['town'],deduplicateBy=['municipalityName','facilityName']),nativeCount=counts[code])]
    notes=NOTES[:]
    if key == PHARMACY:
        _, popref = frozen(engine,POPULATION)
        j=next(i for i,r in enumerate(engine.file(POPULATION)[0]['posas']['towns'][row['town']]) if r['year']==2026)
        evidence.append(dict(popref,kind='source_snapshot',recordPointer=f'/posas/towns/{row["town"]}/{j}/population',nativeDenominator=populations[code],denominatorDate='2026-01-01'))
        notes += ['health_pharmacies_public_two_decimals_benchmark_unrounded', 'health_pharmacies_branches_and_seasonal_dispensaries_included', 'health_pharmacies_2025_stock_2026_resident_estimate']
    else: notes += ['health_rsa_accredited_not_contracted_beds_or_residents_assisted','health_rsa_tuscany_336_not_a_comparable_municipal_rate']
    return dict(ctx,metric=key,dimension=dim,geography=code,period=period,value=row['value'],source=snap['sourceUrl'],evidence=evidence,provenance=evidence,notApplicable=False,dataUnavailable=False,missingReason=None), notes


def benchmark(engine,key,scope,municipal):
    if key != PHARMACY or scope not in scopes(key,'total') or municipal['period'] != '2025':
        raise ValueError('health_facilities_benchmark_scope_not_reviewed')
    snap,ref,_,_=validated(engine,key); _,demo_ref=frozen(engine,DEMO)
    evidence=[dict(ref,kind='source_snapshot',recordPointer=f'/benchmarks/{key}/{scope}',nativeComponents=snap['raw'][scope]),dict(demo_ref,kind='source_snapshot',recordPointer=f'/benchmarks/population/{scope}'),dict(kind='catalog_snapshot',path=engine.catalog_path,sha256=engine.catalog_hash,valuePointer=f'/metrics/{key}/meta/benchmark/{scope}')]
    return dict(municipal,geography=scope,value=snap['benchmarks'][key][scope],evidence=evidence,provenance=evidence,benchmarkAggregation='native unique active sites / POSAS estimated residents 1 January 2026; unrounded benchmark, public municipal rounding explicit')
