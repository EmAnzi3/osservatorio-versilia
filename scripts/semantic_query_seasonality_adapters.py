"""Published top-three-month concentration; monthly panels are not frozen."""
import copy
import math
from a6_pins import Pin as _pin
from semantic_query_library_adapters import TOWNS, fingerprint

KEYS = ('tourismSeasonality',)
PUBLIC_HASH = _pin('seasonality#1')
BENCHMARK = 'data/source-snapshots/a3-regione-toscana-tourism-benchmark-2025.json'
# Reviewed file bytes and parsed-object fingerprints, checked also after cache access.
BENCHMARK_HASHES = (_pin('seasonality#2'), _pin('seasonality#3'))
HISTORY = 'data/source-snapshots/regione-toscana-stagionalita-serie.json'
HISTORY_HASHES = (_pin('seasonality#4'), _pin('seasonality#5'))
NOTES = ['seasonality_top_three_months_not_fixed_summer_quarter',
         'seasonality_public_replay_not_native_monthly_panel',
         'seasonality_sum_of_local_top_three_not_regional_top_three',
         'seasonality_concentration_not_volume_quality_or_policy_priority',
         'seasonality_annual_measure_not_monthly_time_series']


def dimensions(key): return ['total']
def scopes(key, dim): return ['tuscany']
def operations(key, dim): return ['compare', 'rank', 'benchmark_gap']


def selection_guard(key, dim, op):
    if op in ('series', 'absolute_change', 'relative_change', 'percentage_points', 'trend'):
        raise ValueError('seasonality_single_annual_measure_no_monthly_or_historical_panel')
    if op == 'weighted_ratio': raise ValueError('seasonality_monthly_panels_not_frozen_no_pooling')
    if op == 'anomaly': raise ValueError('seasonality_peer_anomaly_not_reviewed')
    if op == 'correlation': raise ValueError('seasonality_pair_not_jointly_reviewed')


def without_history(metric):
    """Il catalogo costruito aggiunge la serie 2024–2025 (verificata in `history_checked`); il resto resta quello fissato."""
    if not any(r.get('series') for r in metric['rows']): return metric
    out = copy.deepcopy(metric)
    for row in out['rows']: row['series'] = None
    out['method'].pop('historyNote', None)
    meta = out['meta'].get('sourceMeta')
    if isinstance(meta, dict):
        meta.pop('historySnapshot', None)
        if not meta: out['meta'].pop('sourceMeta')
    return out


def history_checked(engine, metric):
    """La serie del catalogo costruito deve essere esattamente quella dello snapshot fissato (operazioni sul tempo ancora bloccate)."""
    if not any(r.get('series') for r in metric['rows']): return
    snap, ref = engine.file(HISTORY)
    if ref.get('path') != HISTORY or (ref.get('sha256'), fingerprint(snap)) != HISTORY_HASHES or snap.get('qualityGate', {}).get('status') != 'PASS':
        raise ValueError('seasonality_history_changed')
    for row in metric['rows']:
        want = {'years': list(snap['years']), 'values': [snap['towns'][row['town']][str(y)]['share'] for y in snap['years']]}
        if row.get('series') != want or not math.isclose(want['values'][-1], row['value'], rel_tol=0, abs_tol=1e-12):
            raise ValueError('seasonality_history_changed')


def context(metric, key, dim):
    if key not in KEYS or dim != 'total': raise ValueError('seasonality_dimension_not_reviewed')
    if fingerprint(without_history(metric)) != PUBLIC_HASH: raise ValueError('seasonality_public_definition_or_values_changed')
    return dict(unit='percent',population='recorded tourist overnight stays in reporting accommodation establishments',
                definition='share of annual overnight stays in the three months with the most overnight stays, independently selected per geography',
                method='published concentration; monthly counts and selected month identities not separately frozen; no reverse-derived numerator',
                frequency='annual',periodBasis='2025 movement; source release updated May 2026; annual concentration, not monthly observations',
                nativeComponentsAvailable=False,adapter='seasonality/total/v1')


def observation(engine, key, index, dim, period, historical):
    metric=engine._catalog['metrics'][key];ctx=context(metric,key,dim)
    history_checked(engine,metric)
    towns=engine._catalog['towns']
    if len(towns)!=7 or {t['code']:t['name'] for t in towns}!=TOWNS: raise ValueError('seasonality_municipal_identity_changed')
    if period!='2025': raise ValueError('seasonality_period_not_frozen')
    row=metric['rows'][index]
    evidence=[dict(kind='catalog_snapshot',path=engine.catalog_path,sha256=engine.catalog_hash,
                   valuePointer=f'/metrics/{key}/rows/{index}/value',periodPointer=f'/metrics/{key}/meta/year',
                   replayScope='published annual concentration only; not the twelve monthly counts or original workbook')]
    return dict(ctx,metric=key,dimension=dim,geography=row['code'],period=period,value=row['value'],
                source=metric['sourceUrl'],evidence=evidence,provenance=evidence,
                notApplicable=False,dataUnavailable=False,missingReason=None),NOTES[:]


def benchmark(engine, key, scope, municipal):
    context(engine._catalog['metrics'][key],key,'total')
    if scope!='tuscany' or municipal['period']!='2025': raise ValueError('seasonality_benchmark_scope_or_period_not_reviewed')
    snap,ref=engine.file(BENCHMARK)
    if (ref.get('sha256'),fingerprint(snap))!=BENCHMARK_HASHES: raise ValueError('seasonality_frozen_benchmark_changed')
    value=snap['benchmarks'][key]['tuscany']
    evidence=[dict(ref,kind='source_snapshot',recordPointer=f'/benchmarks/{key}/tuscany'),
              dict(kind='catalog_snapshot',path=engine.catalog_path,sha256=engine.catalog_hash,valuePointer=f'/metrics/{key}/meta/benchmark/tuscany')]
    return dict(municipal,geography=scope,value=value,source=snap['sources']['monthly'],evidence=evidence,provenance=evidence,
                benchmarkAggregation='published regional top-three-month concentration; region selects its own three months; not a mean or sum of municipal concentrations')
