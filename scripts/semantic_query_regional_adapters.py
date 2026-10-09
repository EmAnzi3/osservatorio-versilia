"""Regional published observations; no inferred counts or percentile pooling."""
import hashlib
import json
import math
from statistics import median
from semantic_operations import finite

YOUTH, FOREIGN, EMS, DISABILITY, ONLINE, INNOVATION = KEYS = (
    'youthOtherStatus', 'foreignBornSoleProprietorShare', 'emsResponseTimeP75',
    'disability064Per1000', 'municipalOnlineServicesAdvanced', 'innovationBusinessShare')
NATIVE = 'data/source-snapshots/toscana-indicatori-v1.5.0.json'
SERVICES = 'data/source-snapshots/regione-toscana-servizi-online-2018-2022.json'
BENCHMARK = 'data/source-snapshots/a3-regione-toscana-indicators-benchmark-2024.json'
URL = 'https://www.regione.toscana.it/it/statistiche/indicatori-comunali-per-le-politiche-locali'
METADATA = 'https://www.regione.toscana.it/documents/d/guest/modellometadatinew-1'
CODES = dict(zip(KEYS, ('ind05', 'ind10', 'ind14', 'ind16', 'ind18', 'ind19')))
UNITS = dict(zip(KEYS, ('percent', 'percent', 'minutes', 'per1000', 'percent', 'percent')))
TOWNS = {'046005':'Camaiore', '046013':'Forte dei Marmi', '046018':'Massarosa',
         '046024':'Pietrasanta', '046028':'Seravezza', '046030':'Stazzema', '046033':'Viareggio'}
HASHES = {
 NATIVE: ('fecb17aa645878d58a4f22d3897f21c7dfa4b050d47f7d095bf269423bc51c77', '83eb8bf4143efd70e21e90b0dbad4a236c448d5d930cc671de505eadf742e69a'),
 SERVICES: ('321f154fc161fc9186b9ecdaf54fffaf435a52c4cdf595199fbf2a67fbe17576', '0bb6847adabcbb23b22ec32ed93cd3b93769d68772e0e4f62ab1ec96f862d441'),
 BENCHMARK: ('79756910e1a13307fb0bde0ab9253777d19df7d1e259c630b3a1de6d9c72dd87', 'ec6175398eb795d58e39ec9979f79fafc4f2717fea670d61b026aabed64fa301'),
}
POPULATIONS = {
 YOUTH: 'resident young people aged 15–24 in the source professional-condition classification',
 FOREIGN: 'active sole proprietorships; birthplace of operator, not citizenship',
 EMS: 'NSIS P3 call-to-first-rescue-arrival intervals; native municipal distribution',
 DISABILITY: 'recognized disability, including severe, aged 0–64 / residents aged 0–64',
 ONLINE: 'services offered by each municipality in Istat ICT local public administration survey; levels 3 and 4',
 INNOVATION: 'active enterprises in regional selected Ateco divisions; not measured innovation output',
}
FORMULAS = {
 YOUTH: 'young people 15–24 in other professional condition / young people 15–24 × 100',
 FOREIGN: 'active sole proprietorships with foreign-born operator / all active sole proprietorships × 100',
 EMS: '75th percentile of call-to-first-rescue-arrival interval distribution, minutes',
 DISABILITY: 'recognized disabled people 0–64 / residents 0–64 × 1000',
 ONLINE: 'services offered online at levels 3 or 4 / relevant offered services in survey × 100',
 INNOVATION: 'active enterprises in selected Ateco divisions / all active enterprises × 100',
}
NOTES = ['regional_published_values_no_native_counts_or_joint_distribution',
         'regional_no_reverse_derived_counts_or_population_weights',
         'regional_municipal_summary_not_official_versilia',
         'regional_historical_release_continuity_not_attested']
SPECIAL = {
 YOUTH: ['regional_other_status_not_unemployment_or_neet', 'regional_youth_2020_absent_not_interpolated'],
 FOREIGN: ['regional_foreign_birth_not_citizenship_all_enterprises_or_residents'],
 EMS: ['regional_p75_not_mean_or_pooled_percentile', 'regional_small_intervention_counts_not_frozen'],
 DISABILITY: ['regional_administrative_recognition_not_health_prevalence'],
 ONLINE: ['regional_online_effective_2022_not_release_2024', 'regional_online_basket_24_to_27_not_homogeneous'],
 INNOVATION: ['regional_ateco_classification_not_innovation_quality_or_research_spending'],
}


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()


def frozen(engine, path):
    value, ref = engine.file(path)
    if (ref.get('sha256'), fingerprint(value)) != HASHES[path]: raise ValueError('regional_frozen_input_changed')
    return value, ref


def close(actual, expected):
    if not finite(actual) or not finite(expected) or not math.isclose(actual, expected, rel_tol=0, abs_tol=1e-9): raise ValueError('regional_public_native_mismatch')


def year(key): return '2022' if key == ONLINE else '2024'
def years(key): return [2018, 2022] if key == ONLINE else [2018, 2019, 2021, 2022, 2023, 2024] if key == YOUTH else list(range(2018, 2025))
def dimensions(key): return ['total']
def scopes(key, dim): return ['tuscany']
def operations(key, dim): return ['compare', 'rank', 'series', 'benchmark_gap']


def selection_guard(key, dim, op):
    if op == 'weighted_ratio': raise ValueError('regional_native_components_or_joint_distribution_not_frozen')
    if op in ('absolute_change', 'relative_change', 'percentage_points', 'trend'): raise ValueError('regional_temporal_continuity_not_reviewed')
    if op == 'correlation': raise ValueError('regional_pair_not_jointly_reviewed')
    if op == 'anomaly': raise ValueError('regional_peer_anomaly_not_reviewed')


def context(metric, key, dim):
    meta = metric['meta']
    if dim != 'total' or str(meta.get('year')) != year(key) or meta.get('unit') != UNITS[key] or meta.get('key') != key or metric.get('sourceUrl') != URL: raise ValueError('regional_definition_changed')
    return dict(unit=UNITS[key], population=POPULATIONS[key], definition=FORMULAS[key],
        method='direct frozen regional published observation; formula documents source definition, counts/distribution not frozen; numerical rank is not policy quality',
        frequency='irregular_survey' if key == ONLINE else 'annual',
        periodBasis='effective 31 December 2022; 2018 basket 24 services, 2022 basket 27; release 2024 is not an extra observation' if key == ONLINE else 'regional source reference year; 2020 absent for ind05; no certified cross-release continuity',
        nativeComponentsAvailable=False, sourceCode=CODES[key], metadataUrl=METADATA,
        adapter='regional/' + key + '/v1')


def validated(engine, key):
    metric = engine._catalog['metrics'][key]; context(metric, key, 'total')
    path = SERVICES if key == ONLINE else NATIVE
    snap, ref = frozen(engine, path)
    rows = metric['rows']
    if len(rows) != 7 or {r.get('code') for r in rows} != set(TOWNS) or {t['code']:t['name'] for t in engine._catalog['towns']} != TOWNS: raise ValueError('regional_municipal_identity_changed')
    native = snap['towns'] if key == ONLINE else {r['town']:r for r in snap['indicators'][key]['rows']}
    if key != ONLINE and snap['indicators'][key]['sourceCode'] != CODES[key]: raise ValueError('regional_native_definition_changed')
    if set(native) != set(TOWNS.values()): raise ValueError('regional_municipal_identity_changed')
    for row in rows:
        code = row['code']; name = TOWNS[code]; n = native[name]
        if row.get('town') != name or row.get('slug') != '-'.join(name.lower().split()) or n.get('istatCode' if key == ONLINE else 'code') != code or row.get('notApplicable') or row.get('dataUnavailable'): raise ValueError('regional_municipal_identity_changed')
        vals = [n[str(y)] for y in years(key)] if key == ONLINE else n['values']
        if key != ONLINE and n['years'] != years(key): raise ValueError('regional_native_periods_changed')
        if len(vals) != len(years(key)) or any(not finite(v) or not 0 <= v <= (1000 if key == DISABILITY else 100 if key != EMS else float('inf')) for v in vals): raise ValueError('regional_native_values_invalid')
        if row.get('series') != dict(years=years(key), values=vals): raise ValueError('regional_public_history_changed')
        close(row.get('value'), vals[-1])
        if row.get('normalized') is not None or row.get('ratioComponents') is not None: raise ValueError('regional_unreviewed_components_changed')
    aggregate = metric.get('aggregate') or {}
    summary = math.fsum(r['value'] for r in rows) / 7 if key == ONLINE else median(r['value'] for r in rows)
    close(aggregate.get('value'), summary)
    if key == ONLINE:
        if 'Media aritmetica' not in aggregate.get('note', '') or snap.get('referenceDate') != '2022-12-31': raise ValueError('regional_summary_or_reference_changed')
    elif aggregate.get('label') != 'Mediana dei 7 Comuni' or 'non ponderata' not in aggregate.get('note', ''): raise ValueError('regional_summary_or_reference_changed')
    return snap, ref, native


def available_periods(engine, key, dim, row):
    validated(engine, key)
    return list(map(str, years(key)))


def observation(engine, key, index, dim, period, historical):
    metric = engine._catalog['metrics'][key]; ctx = context(metric, key, dim)
    snap, ref, native = validated(engine, key); row = metric['rows'][index]
    if period not in list(map(str, years(key))): raise ValueError('regional_period_not_frozen')
    if not historical and period != year(key): raise ValueError('regional_period_not_frozen')
    i = years(key).index(int(period)); name = row['town']
    pointer = f'/metrics/{key}/rows/{index}/series/values/{i}' if historical else f'/metrics/{key}/rows/{index}/value'
    record = f'/towns/{name}/{period}' if key == ONLINE else f'/indicators/{key}/rows/{next(i for i,n in enumerate(snap["indicators"][key]["rows"]) if n["town"] == name)}/values/{i}'
    value = row['series']['values'][i] if historical else row['value']
    evidence = [dict(kind='catalog_snapshot', path=engine.catalog_path, sha256=engine.catalog_hash, valuePointer=pointer), dict(ref, kind='source_snapshot', recordPointer=record)]
    return dict(ctx, metric=key, dimension=dim, geography=row['code'], period=period, value=value,
        source=URL, evidence=evidence, provenance=evidence, notApplicable=False, dataUnavailable=False), NOTES + SPECIAL[key]


def benchmark(engine, key, scope, municipal):
    if scope != 'tuscany' or municipal['period'] != year(key): raise ValueError('regional_benchmark_scope_or_period_not_reviewed')
    validated(engine, key); snap, ref = frozen(engine, BENCHMARK)
    spec = snap['benchmarks'][key]; meta = engine._catalog['metrics'][key]['meta'].get('benchmark') or {}
    if spec.get('sourceCode') != CODES[key] or spec.get('year') != year(key) or spec.get('unit') != UNITS[key] or spec.get('italy') is not None or meta.get('year') != year(key) or meta.get('url') != URL or meta.get('sourceSnapshot') != BENCHMARK or meta.get('italy') is not None: raise ValueError('regional_benchmark_definition_changed')
    for row in engine._catalog['metrics'][key]['rows']: close(row['value'], snap['publicRows'][key][row['town']])
    close(meta.get('tuscany'), spec['tuscany'])
    evidence = [dict(ref, kind='source_snapshot', recordPointer=f'/benchmarks/{key}/tuscany'), dict(kind='catalog_snapshot', path=engine.catalog_path, sha256=engine.catalog_hash, valuePointer=f'/metrics/{key}/meta/benchmark/tuscany')]
    return dict(municipal, geography=scope, value=spec['tuscany'], evidence=evidence, provenance=evidence,
        benchmarkAggregation='official published regional row; native counts or interval distribution not embedded; not municipal mean or median')
