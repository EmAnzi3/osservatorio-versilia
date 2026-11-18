"""Standard needs (OpenCivitas, SOSE/MEF): historical vs standard spending, services vs standard level."""
from a6_pins import Pin as _pin
import math
import re

from opencivitas_needs import build_metrics, spending_gap, SPENDING, SERVICE, TOWNS as OC_TOWNS
from semantic_operations import finite
from semantic_query_library_adapters import TOWNS, fingerprint

KEYS = (SPENDING, SERVICE)
# Lo snapshot cambia a ogni annualità (update_source_data.py opencivitas-needs): percorso e anno
# vengono dal catalogo e dallo snapshot, le impronte restano nei pin.
PATH_RE = re.compile(r'data/source-snapshots/opencivitas-fabbisogni-(20[0-9]{2})[.]json')
HASH = _pin('standard_needs#1')
FINGERPRINT = _pin('standard_needs#2')
NOTES = ['standard_needs_estimate_not_budget_target_or_efficiency_verdict',
         'standard_needs_model_includes_tourism_per_resident_values_use_residents',
         'standard_needs_fundamental_functions_only',
         'standard_needs_single_vintage_no_time_comparison',
         'standard_needs_no_automatic_causal_or_policy_priority_inference']
SPENDING_NOTES = ['standard_needs_spending_gap_read_with_service_gap']
SERVICE_NOTES = ['standard_needs_service_gap_quantity_not_quality']


def frozen_path(engine, key):
    path = engine._catalog['metrics'][key]['meta'].get('sourceMeta', {}).get('snapshot')
    if not PATH_RE.fullmatch(str(path)):
        raise ValueError('standard_needs_frozen_input_changed')
    return path


def dimensions(key): return ['total']
def scopes(key, dim): return ['tuscany', 'italy']
def operations(key, dim): return ['compare', 'rank', 'benchmark_gap']


def selection_guard(key, dim, op):
    if op in ('absolute_change', 'relative_change', 'percentage_points', 'trend', 'series'):
        raise ValueError('standard_needs_single_vintage_no_time_comparison')
    if op == 'weighted_ratio': raise ValueError('standard_needs_pooling_not_reviewed')
    if op == 'correlation': raise ValueError('standard_needs_pair_not_jointly_reviewed')
    if op == 'anomaly': raise ValueError('standard_needs_peer_anomaly_not_reviewed')


def context(metric, key, dim):
    meta = metric['meta']
    if (key not in KEYS or dim != 'total' or meta.get('key') != key or meta.get('unit') != 'percent'
            or meta.get('polarity') != 'neutral' or meta.get('theme') != 'bilanci'):
        raise ValueError('standard_needs_definition_changed')
    spending = key == SPENDING
    return dict(unit='percent',
                population='municipality as a local authority, fundamental functions (OpenCivitas «Totale funzioni»)',
                definition=('(historical spending / standard spending − 1) × 100' if spending
                            else 'published percentage gap between services delivered and the standard service level (DIFF_OUT_PERC_TOT)'),
                method=('native euro components in the snapshot; Versilia and benchmarks on euro totals' if spending
                        else 'published municipal gap; Versilia and benchmarks as means weighted by standard spending'),
                frequency='annual_vintage', periodBasis='OpenCivitas vintage year',
                nativeComponentsAvailable=spending, adapter='standard-needs/'+key+'/v1')


def equal(actual, expected):
    if not finite(actual) or not math.isclose(actual, expected, rel_tol=0, abs_tol=1e-9):
        raise ValueError('standard_needs_public_native_mismatch')


def validated(engine, key):
    path = frozen_path(engine, key)
    snap, ref = engine.file(path)
    if ref.get('path') != path or ref.get('sha256') != HASH or fingerprint(snap) != FINGERPRINT:
        raise ValueError('standard_needs_frozen_input_changed')
    if {t['code']: t['name'] for t in engine._catalog['towns']} != TOWNS or set(OC_TOWNS) != set(TOWNS):
        raise ValueError('standard_needs_municipal_identity_changed')
    if snap.get('qualityGate', {}).get('status') != 'PASS' or set(snap.get('towns', {})) != set(TOWNS):
        raise ValueError('standard_needs_quality_gate_missing')
    for code, t in snap['towns'].items():
        if t.get('username') != OC_TOWNS[code] or t.get('notEvaluable') != 0:
            raise ValueError('standard_needs_municipal_identity_changed')
        if not all(finite(t.get(k)) and t[k] > 0 for k in ('spesaStorica', 'spesaStandard', 'spesaStoricaProAb', 'spesaStandardProAb')) or not finite(t.get('serviceGapPct')):
            raise ValueError('standard_needs_native_domain_changed')
    population = engine._catalog['metrics']['population']['rows']
    # Ricostruisce entrambe le definizioni pubbliche (valori, aggregati, benchmark) dallo snapshot.
    for k, rebuilt in build_metrics(snap, population, path).items():
        if fingerprint(engine._catalog['metrics'][k]) != fingerprint(rebuilt):
            raise ValueError('standard_needs_catalog_native_reconciliation_changed')
    return snap, ref


def available_periods(engine, key, dim, row):
    snap, _ = validated(engine, key)
    return [str(snap['year'])]


def observation(engine, key, index, dim, period, historical):
    metric = engine._catalog['metrics'][key]; ctx = context(metric, key, dim)
    snap, ref = validated(engine, key)
    if period != str(snap['year']): raise ValueError('standard_needs_period_not_frozen')
    row = metric['rows'][index]; code = row['code']; t = snap['towns'][code]
    value = row['value']
    if key == SPENDING:
        equal(value, spending_gap(t['spesaStorica'], t['spesaStandard']))
        native = dict(historicalSpending=t['spesaStorica'], standardSpending=t['spesaStandard'],
                      historicalSpendingPerResident=t['spesaStoricaProAb'], standardSpendingPerResident=t['spesaStandardProAb'])
        notes = SPENDING_NOTES
    else:
        equal(value, t['serviceGapPct'])
        native = dict(serviceGapPct=t['serviceGapPct'], serviceLevel0to10=t['serviceLevel'])
        notes = SERVICE_NOTES
    evidence = [dict(kind='catalog_snapshot', path=engine.catalog_path, sha256=engine.catalog_hash, valuePointer=f'/metrics/{key}/rows/{index}/value'),
                dict(ref, kind='source_snapshot', recordPointer=f'/towns/{code}', nativeComponents=native)]
    result = dict(ctx, metric=key, dimension=dim, geography=code, period=period, value=value, source=snap['sourceUrl'],
                  evidence=evidence, provenance=evidence, notApplicable=False, dataUnavailable=False, missingReason=None)
    return result, NOTES + notes


def benchmark(engine, key, scope, municipal):
    snap, ref = validated(engine, key)
    if key not in KEYS or scope not in scopes(key, 'total') or municipal['period'] != str(snap['year']):
        raise ValueError('standard_needs_benchmark_scope_not_reviewed')
    s = snap['scopes'][scope]
    if key == SPENDING:
        value = spending_gap(s['spesaStorica'], s['spesaStandard'])
        aggregation = 'sum of historical spending / sum of standard spending − 1, evaluable municipalities'
    else:
        value = s['serviceGapWeightedSum'] / s['spesaStandard']
        aggregation = 'mean of municipal service gaps weighted by standard spending, evaluable municipalities'
    equal(engine._catalog['metrics'][key]['meta']['benchmark'][scope], value)
    evidence = [dict(ref, kind='source_snapshot', recordPointer=f'/scopes/{scope}', nativeComponents=dict(s)),
                dict(kind='catalog_snapshot', path=engine.catalog_path, sha256=engine.catalog_hash, valuePointer=f'/metrics/{key}/meta/benchmark/{scope}')]
    return dict(municipal, geography=scope, value=value, evidence=evidence, provenance=evidence, benchmarkAggregation=aggregation)
