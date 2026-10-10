"""Published municipal library indices, with missing observations and gaps intact."""
import hashlib
import json
import math

from semantic_operations import finite

LOANS, BORROWERS, HOURS = KEYS = (
    'libraryLoansPerResident', 'libraryActiveBorrowersPer100', 'libraryWeeklyOpeningHours')
NATIVE = 'data/source-snapshots/regione-toscana-cultura-biblioteche-2024.json'
BENCHMARK = 'data/source-snapshots/a3-regione-toscana-libraries-benchmark-2024.json'
URL = 'https://dati.toscana.it/dataset/rt-monit-bibi-ente-locale'
BENCHMARK_URL = 'https://www.regione.toscana.it/-/il-valore-delle-biblioteche-pubbliche-di-ente-locale-e-della-cooperazione-bibliotecaria'
TOWNS = {'046005': 'Camaiore', '046013': 'Forte dei Marmi', '046018': 'Massarosa',
         '046024': 'Pietrasanta', '046028': 'Seravezza', '046030': 'Stazzema', '046033': 'Viareggio'}
FIELDS = dict(zip(KEYS, ('Indice di prestito Comunale', 'Indice di impatto Comunale',
                        'Ore medie di apertura settimanale Comunale')))
UNITS = dict(zip(KEYS, ('decimal', 'per100', 'hours')))
HASHES = {
    NATIVE: ('f956dc0db8762a94742cc42af2cd52b0f8b1408b27d51d969698e5ccafe15edf',
             '395ac8695f1b9f5af0aea03fc613057f40d35581c13f1a4f9ddbcf27d1291cbf'),
    BENCHMARK: ('afea34efd1a38eb84cd756e77bce1f33c5a21dae1d405d958d27e74f16f78e07',
                'a2e395af749fd4d0bfff933e83231f9af67ec3c6e9537cc217749f01e3e6e810'),
}
NOTES = ['library_current_coverage_5_of_7_no_imputation_or_last_value_carry',
         'library_published_rounded_indices_not_reconstructed_native_ratios',
         'library_available_municipal_mean_not_official_versilia',
         'library_historical_release_continuity_not_reviewed',
         'library_pandemic_2020_context_not_automatic_anomaly']
SPECIAL = {
    LOANS: ['library_loans_are_transactions_not_unique_readers'],
    BORROWERS: ['library_per100_not_percent_or_per1000',
                'library_users_not_deduplicated_across_municipalities_or_residence'],
    HOURS: ['library_weekly_hours_not_opening_index_or_annual_hours',
            'library_hours_history_starts_2022_no_pre2022_substitution'],
}


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                     ensure_ascii=False).encode()).hexdigest()


def frozen(engine, path):
    value, ref = engine.file(path)
    if (ref.get('sha256'), fingerprint(value)) != HASHES[path]:
        raise ValueError('library_frozen_input_changed')
    return value, ref


def equal(actual, expected):
    if expected is None:
        if actual is not None:
            raise ValueError('library_missing_value_imputed')
    elif not finite(actual) or not math.isclose(actual, expected, rel_tol=0, abs_tol=1e-9):
        raise ValueError('library_public_native_mismatch')


def dimensions(key): return ['total']
def scopes(key, dim): return ['tuscany']
def operations(key, dim): return ['compare', 'rank', 'series', 'benchmark_gap']


def selection_guard(key, dim, op):
    if op == 'weighted_ratio':
        raise ValueError('library_published_indices_not_poolable')
    if op in ('absolute_change', 'relative_change', 'percentage_points', 'trend'):
        raise ValueError('library_temporal_continuity_not_reviewed')
    if op == 'correlation':
        raise ValueError('library_pair_not_jointly_reviewed')
    if op == 'anomaly':
        raise ValueError('library_peer_anomaly_not_reviewed')


def context(metric, key, dim):
    meta = metric['meta']
    if (dim != 'total' or meta.get('key') != key or str(meta.get('year')) != '2024'
            or meta.get('unit') != UNITS[key] or metric.get('sourceUrl') != URL
            or meta.get('sourceMeta', {}).get('snapshot') != NATIVE):
        raise ValueError('library_definition_changed')
    return dict(unit=UNITS[key], population='municipal public library services included in regional annual monitoring',
                definition=FIELDS[key], method='direct published municipal index; rounded source precision retained; no pooling or reverse-derived counts',
                frequency='annual', periodBasis='regional annual monitoring reference year; gaps preserved, pandemic 2020 explicit; weekly hours only 2022–2024',
                nativeComponentsAvailable=False, adapter='library/' + key + '/v1')


def validated(engine, key):
    metric = engine._catalog['metrics'][key]
    context(metric, key, 'total')
    snap, ref = frozen(engine, NATIVE)
    series = snap['series'][key]
    years = series['years']
    current = {r['code']: r for r in snap['current2024']}
    rows = metric['rows']
    if (len(rows) != 7 or {r.get('code') for r in rows} != set(TOWNS)
            or {t['code']: t['name'] for t in engine._catalog['towns']} != TOWNS
            or set(current) != set(TOWNS)):
        raise ValueError('library_municipal_identity_changed')
    for row in rows:
        code = row['code']; name = TOWNS[code]; native = current[code]
        if (row.get('town') != name or row.get('slug') != '-'.join(name.lower().split())
                or row.get('notApplicable') or row.get('dataUnavailable')):
            raise ValueError('library_municipal_identity_changed')
        values = series['values'][name]
        pairs = [(y, v) for y, v in zip(years, values) if v is not None]
        expected_series = dict(years=[y for y, _ in pairs], values=[v for _, v in pairs]) if pairs else None
        if row.get('series') != expected_series:
            raise ValueError('library_public_history_changed')
        expected = (native.get('selectedIndicatorRow') or {}).get(FIELDS[key])
        equal(values[-1], expected)
        equal(row.get('value'), expected)
        equal(row.get('benchmarkValue'), expected)
        if row.get('normalized') is not None or row.get('ratioComponents') is not None:
            raise ValueError('library_unreviewed_components_changed')
    available = [r['value'] for r in rows if r['value'] is not None]
    aggregate = metric.get('aggregate') or {}
    equal(aggregate.get('value'), math.fsum(available) / len(available))
    if (aggregate.get('label') != 'Versilia · comuni con dato disponibile (5/7)'
            or 'Media aritmetica' not in aggregate.get('note', '')
            or metric.get('method', {}).get('coverage') != '5/7'
            or metric.get('method', {}).get('snapshot') != NATIVE
            or metric.get('normalizedAggregate') is not None):
        raise ValueError('library_summary_definition_changed')
    return snap, ref


def available_periods(engine, key, dim, row):
    snap, _ = validated(engine, key)
    # Include null years explicitly: partial queries must opt in, never silently fill gaps.
    return list(map(str, snap['series'][key]['years']))


def observation(engine, key, index, dim, period, historical):
    metric = engine._catalog['metrics'][key]; ctx = context(metric, key, dim)
    snap, ref = validated(engine, key); row = metric['rows'][index]
    series = snap['series'][key]; years = list(map(str, series['years']))
    if period not in years or (not historical and period != '2024'):
        raise ValueError('library_period_not_frozen')
    i = years.index(period); value = series['values'][row['town']][i]
    pointer = f'/metrics/{key}/rows/{index}/value'
    catalog_evidence = dict(kind='catalog_snapshot', path=engine.catalog_path, sha256=engine.catalog_hash)
    if historical:
        public = row.get('series')
        if value is not None:
            j = list(map(str, public['years'])).index(period)
            pointer = f'/metrics/{key}/rows/{index}/series/values/{j}'
        else:
            pointer = f'/metrics/{key}/rows/{index}/series'
            catalog_evidence['absentPeriod'] = period
            catalog_evidence['absenceMeaning'] = 'no numeric value for this period in published sparse series'
    catalog_evidence['valuePointer'] = pointer
    evidence = [catalog_evidence, dict(ref, kind='source_snapshot',
                recordPointer=f'/series/{key}/values/{row["town"]}/{i}')]
    reason = 'row_absent_from_regional_monitoring' if row['code'] == '046030' else 'regional_indicator_value_not_reported'
    return dict(ctx, metric=key, dimension=dim, geography=row['code'], period=period, value=value,
                source=URL, evidence=evidence, provenance=evidence, notApplicable=False,
                dataUnavailable=value is None, missingReason=reason if value is None else None), NOTES + SPECIAL[key]


def benchmark(engine, key, scope, municipal):
    if scope != 'tuscany' or municipal['period'] != '2024':
        raise ValueError('library_benchmark_scope_or_period_not_reviewed')
    validated(engine, key); snap, ref = frozen(engine, BENCHMARK)
    spec = snap['benchmarks'][key]
    meta = engine._catalog['metrics'][key]['meta'].get('benchmark') or {}
    if (spec.get('year') != '2024' or spec.get('unit') != UNITS[key]
            or spec.get('formula') != FIELDS[key] or spec.get('italy') is not None
            or meta.get('year') != '2024' or meta.get('unit', UNITS[key]) != UNITS[key] or meta.get('url') != BENCHMARK_URL
            or meta.get('sourceSnapshot') != BENCHMARK or meta.get('italy') is not None):
        raise ValueError('library_benchmark_definition_changed')
    equal(meta.get('tuscany'), spec['tuscany'])
    evidence = [dict(ref, kind='source_snapshot', recordPointer=f'/benchmarks/{key}/tuscany'),
                dict(kind='catalog_snapshot', path=engine.catalog_path, sha256=engine.catalog_hash,
                     valuePointer=f'/metrics/{key}/meta/benchmark/tuscany')]
    return dict(municipal, geography=scope, value=spec['tuscany'], evidence=evidence, provenance=evidence,
                dataUnavailable=False, missingReason=None,
                benchmarkAggregation='official published Tuscany monitoring index, not mean of five Versilia municipalities')
