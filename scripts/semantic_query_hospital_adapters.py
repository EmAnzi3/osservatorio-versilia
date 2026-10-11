"""Published hospital presence and bed rates; no invented native components."""
from semantic_query_library_adapters import TOWNS, fingerprint

KEYS = ('hospitals',)
HASHES = {'970682de2adb5f646afd3ede56aba448da426d087e84745015f0198867678c36',
          '2c0f2d7503c6910ab2e4d8d1d8be90841df15cfba62fd86ac9505f2cc2c9d4a5'}
NOTES = ['hospital_local_presence_not_accessibility_or_care_quality',
         'hospital_sites_and_bed_rates_are_distinct_measures',
         'hospital_public_catalog_replay_not_original_ministerial_records',
         'hospital_2025_public_reference_exact_stock_date_not_frozen',
         'hospital_bed_rate_native_components_and_denominator_date_not_frozen',
         'hospital_zero_local_presence_not_absence_of_health_services',
         'hospital_numerical_rank_not_policy_priority']


def dimensions(key): return ['total', 'view:normalized']
def scopes(key, dim): return []
def operations(key, dim): return ['compare', 'rank']


def selection_guard(key, dim, op):
    if op in ('series', 'absolute_change', 'relative_change', 'percentage_points', 'trend'):
        raise ValueError('hospital_single_public_snapshot_no_history')
    if op == 'weighted_ratio': raise ValueError('hospital_native_components_not_frozen_no_pooling')
    if op == 'benchmark_gap': raise ValueError('hospital_geographic_benchmark_not_frozen')
    if op == 'anomaly': raise ValueError('hospital_peer_anomaly_not_reviewed')
    if op == 'correlation': raise ValueError('hospital_pair_not_jointly_reviewed')


def context(metric, key, dim):
    if key not in KEYS or dim not in dimensions(key):
        raise ValueError('hospital_dimension_not_reviewed')
    if fingerprint(metric) not in HASHES:
        raise ValueError('hospital_public_definition_or_values_changed')
    normalized = dim == 'view:normalized'
    return dict(unit='per10k' if normalized else 'number',
                population='hospital beds physically localized in municipality / resident population' if normalized else 'hospital facilities physically localized in municipality',
                definition='published hospital beds per 10000 residents' if normalized else 'published count of localized hospital facilities',
                method='published catalog value; native bed and population components not separately frozen' if normalized else 'published catalog integer count; original ministerial facility records not replayed',
                frequency='annual_snapshot', periodBasis='2025 public reference; exact stock date and bed-rate denominator date not separately frozen',
                nativeComponentsAvailable=False, adapter='hospital/'+dim+'/v1')


def observation(engine, key, index, dim, period, historical):
    metric = engine._catalog['metrics'][key]
    ctx = context(metric, key, dim)
    towns = engine._catalog['towns']
    if len(towns) != 7 or {t['code']:t['name'] for t in towns} != TOWNS:
        raise ValueError('hospital_municipal_identity_changed')
    if period != '2025': raise ValueError('hospital_period_not_frozen')
    row = metric['rows'][index]
    field = 'normalized/value' if dim == 'view:normalized' else 'value'
    value = row['normalized']['value'] if dim == 'view:normalized' else row['value']
    evidence = [dict(kind='catalog_snapshot',path=engine.catalog_path,sha256=engine.catalog_hash,
                     valuePointer=f'/metrics/{key}/rows/{index}/{field}',
                     replayScope='published catalog only; not original ministerial workbook or individual facility records')]
    return dict(ctx,metric=key,dimension=dim,geography=row['code'],period=period,value=value,
                source=metric['sourceUrl'],evidence=evidence,provenance=evidence,
                notApplicable=False,dataUnavailable=False,missingReason=None), NOTES[:]
