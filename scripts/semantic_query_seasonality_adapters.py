"""Published top-three-month concentration; monthly panels are not frozen."""
from semantic_query_library_adapters import TOWNS, fingerprint

KEYS = ('tourismSeasonality',)
PUBLIC_HASH = 'ce65820031c12b57bba095e0a235548408599168d7fa0845f14d79e934b86172'
BENCHMARK = 'data/source-snapshots/a3-regione-toscana-tourism-benchmark-2025.json'
# Reviewed file bytes and parsed-object fingerprints, checked also after cache access.
BENCHMARK_HASHES = ('f09c50bc3016cc2793eab4737c6dff1f625da67798b4c8b5c4dae16af2c8ac37', 'bc2b4f4f8a5233e7233e8ee92b5bc4a0102c36baf443efcd5a160114613cb2e8')
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


def context(metric, key, dim):
    if key not in KEYS or dim != 'total': raise ValueError('seasonality_dimension_not_reviewed')
    if fingerprint(metric) != PUBLIC_HASH: raise ValueError('seasonality_public_definition_or_values_changed')
    return dict(unit='percent',population='recorded tourist overnight stays in reporting accommodation establishments',
                definition='share of annual overnight stays in the three months with the most overnight stays, independently selected per geography',
                method='published concentration; monthly counts and selected month identities not separately frozen; no reverse-derived numerator',
                frequency='annual',periodBasis='2025 movement; source release updated May 2026; annual concentration, not monthly observations',
                nativeComponentsAvailable=False,adapter='seasonality/total/v1')


def observation(engine, key, index, dim, period, historical):
    metric=engine._catalog['metrics'][key];ctx=context(metric,key,dim)
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
