"""Bank branches (Banca d'Italia GIAVA): presence of branches, not access to credit."""
from a6_pins import Pin as _pin
import math
import re

from bank_branches import build_metric, ISTAT_2022, TOWNS as BDI_TOWNS
from semantic_operations import finite
from semantic_query_library_adapters import TOWNS, fingerprint

KEYS = ('bankBranchesPer1000',)
# Lo snapshot cambia ogni anno (update_source_data.py bdi-branches): percorso e anni vengono
# dal catalogo e dallo snapshot, le impronte restano nei pin.
PATH_RE = re.compile(r'data/source-snapshots/bdi-sportelli-bancari-(20[0-9]{2})[.]json')
HASH = _pin('bank_branches#1')
FINGERPRINT = _pin('bank_branches#2')
NOTES = ['bank_branches_presence_not_access_to_credit_opening_hours_or_services',
         'bank_branches_atm_post_offices_and_representative_offices_excluded',
         'bank_branches_small_municipality_counts_move_rate_strongly',
         'bank_branches_2022_reconciled_with_istat_municipal_series',
         'bank_branches_no_automatic_causal_or_policy_priority_inference']


def frozen_path(engine, key):
    path = engine._catalog['metrics'][key]['meta'].get('sourceMeta', {}).get('snapshot')
    if not PATH_RE.fullmatch(str(path)):
        raise ValueError('bank_branches_frozen_input_changed')
    return path


def dimensions(key): return ['total']
def scopes(key, dim): return ['tuscany', 'italy']
def operations(key, dim): return ['compare', 'rank', 'series', 'benchmark_gap']


def selection_guard(key, dim, op):
    if op in ('absolute_change', 'relative_change', 'percentage_points', 'trend'):
        raise ValueError('bank_branches_temporal_analysis_not_reviewed')
    if op == 'weighted_ratio': raise ValueError('bank_branches_pooling_not_reviewed')
    if op == 'correlation': raise ValueError('bank_branches_pair_not_jointly_reviewed')
    if op == 'anomaly': raise ValueError('bank_branches_peer_anomaly_not_reviewed')


def context(metric, key, dim):
    meta = metric['meta']
    if (key not in KEYS or dim != 'total' or meta.get('key') != key or meta.get('unit') != 'per1000'
            or meta.get('polarity') != 'neutral' or meta.get('theme') != 'economia'):
        raise ValueError('bank_branches_definition_changed')
    return dict(unit='per1000', population='bank branches operating in the municipality (Banca d\'Italia branch register), not ATMs, post offices or representative offices',
                definition='branches operating on 31 December / residents 1 January of the following year × 1000',
                method='branch register versions valid on the day, key intermediary + branch; native counts and residents in the snapshot',
                frequency='annual_snapshot_of_continuous_register', periodBasis='stock 31 December; denominator residents 1 January of the following year',
                nativeComponentsAvailable=True, adapter='bank-branches/'+key+'/v1')


def equal(actual, expected):
    if not finite(actual) or not math.isclose(actual, expected, rel_tol=0, abs_tol=1e-12):
        raise ValueError('bank_branches_public_native_mismatch')


def validated(engine, key):
    path = frozen_path(engine, key)
    snap, ref = engine.file(path)
    if ref.get('path') != path or ref.get('sha256') != HASH or fingerprint(snap) != FINGERPRINT:
        raise ValueError('bank_branches_frozen_input_changed')
    if {t['code']: t['name'] for t in engine._catalog['towns']} != TOWNS or set(BDI_TOWNS) != set(TOWNS):
        raise ValueError('bank_branches_municipal_identity_changed')
    if snap.get('qualityGate', {}).get('istat2022') != ISTAT_2022 or snap['qualityGate'].get('status') != 'PASS':
        raise ValueError('bank_branches_istat_reconciliation_missing')
    metric = engine._catalog['metrics'][key]
    population = engine._catalog['metrics']['population']['rows']
    # Ricostruisce l'intera definizione pubblica (valori, serie, aggregato, benchmark) dallo snapshot.
    if fingerprint(metric) != fingerprint(build_metric(snap, population, path)):
        raise ValueError('bank_branches_catalog_native_reconciliation_changed')
    for code in TOWNS:
        counts, residents = snap['branches'][code], snap['population']['towns'][code]
        if len(counts) != len(snap['years']) or len(residents) != len(snap['years']):
            raise ValueError('bank_branches_series_incomplete')
        if any(not isinstance(n, int) or n < 0 for n in counts) or any(not isinstance(p, int) or p <= 0 for p in residents):
            raise ValueError('bank_branches_native_domain_changed')
    return snap, ref


def available_periods(engine, key, dim, row):
    snap, _ = validated(engine, key)
    return [str(y) for y in snap['years']]


def observation(engine, key, index, dim, period, historical):
    metric = engine._catalog['metrics'][key]; ctx = context(metric, key, dim)
    snap, ref = validated(engine, key)
    years = [str(y) for y in snap['years']]
    if period not in years: raise ValueError('bank_branches_period_not_frozen')
    row = metric['rows'][index]; code = row['code']; j = years.index(period)
    count, residents = snap['branches'][code][j], snap['population']['towns'][code][j]
    value = row['series']['values'][j]
    equal(value, count / residents * 1000)
    pointer = f'/metrics/{key}/rows/{index}/value' if j == len(years) - 1 else f'/metrics/{key}/rows/{index}/series/values/{j}'
    evidence = [dict(kind='catalog_snapshot', path=engine.catalog_path, sha256=engine.catalog_hash, valuePointer=pointer),
                dict(ref, kind='source_snapshot', recordPointer=f'/branches/{code}/{j}', nativeComponents=dict(numerator=count, denominator=residents, scale=1000),
                     denominatorPointer=f'/population/towns/{code}/{j}', denominatorDate=f'{int(period) + 1}-01-01')]
    result = dict(ctx, metric=key, dimension=dim, geography=code, period=period, value=value, source=snap['sourceUrl'],
                  evidence=evidence, provenance=evidence, notApplicable=False, dataUnavailable=False, missingReason=None,
                  numerator=count, denominator=residents, scale=1000, numeratorPeriod=f'{period}-12-31', denominatorPeriod=f'{int(period) + 1}-01-01')
    return result, NOTES[:]


def benchmark(engine, key, scope, municipal):
    snap, ref = validated(engine, key)
    last = str(snap['years'][-1])
    if key not in KEYS or scope not in scopes(key, 'total') or municipal['period'] != last:
        raise ValueError('bank_branches_benchmark_scope_not_reviewed')
    count, residents = snap['scopes'][scope], snap['population'][scope]
    value = count / residents * 1000
    equal(engine._catalog['metrics'][key]['meta']['benchmark'][scope], value)
    evidence = [dict(ref, kind='source_snapshot', recordPointer=f'/scopes/{scope}', nativeComponents=dict(numerator=count, denominator=residents, scale=1000)),
                dict(kind='catalog_snapshot', path=engine.catalog_path, sha256=engine.catalog_hash, valuePointer=f'/metrics/{key}/meta/benchmark/{scope}')]
    return dict(municipal, geography=scope, value=value, evidence=evidence, provenance=evidence,
                benchmarkAggregation='branches operating on 31 December counted with the same rule as municipalities / residents 1 January of the following year')
