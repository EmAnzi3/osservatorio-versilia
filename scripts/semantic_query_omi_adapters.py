"""Reviewed published OMI municipal reference means; no transaction-price claim."""
import math
from semantic_query_library_adapters import TOWNS, fingerprint
from semantic_operations import finite

KEYS = ('omiResidential',)
PERIOD = '2025-S2'
PUBLIC_HASH = 'ef123ce68f6d9d863159b272568b1439c8c3d011e0a3542ee440e84a3a7e486a'
NOTES = ['omi_reference_quotations_not_transaction_prices_or_registered_rents',
         'omi_municipal_mean_is_unweighted_mean_of_displayed_zones_not_official_municipal_omi_mean',
         'omi_versilia_mean_of_seven_municipal_means_not_transaction_or_dwelling_weighted',
         'omi_zone_codes_are_local_to_each_municipality_not_comparable_neighbourhoods',
         'omi_public_zone_values_replayed_original_omi_ranges_and_files_not_frozen',
         'omi_sale_euro_per_m2_and_rent_euro_per_m2_per_month_are_distinct',
         'omi_second_semester_2025_not_current_2026_or_full_year_average',
         'omi_numerical_rank_not_affordability_or_policy_priority']


def token(key, period):
    if str(period) in (PERIOD, '2° semestre 2025'): return PERIOD
    raise ValueError('omi_exact_semester_required')


def dimensions(key): return ['total', 'saleMean', 'rentMean']
def scopes(key, dim): return []
def operations(key, dim): return ['compare', 'rank']


def selection_guard(key, dim, op):
    if op in ('series', 'absolute_change', 'relative_change', 'percentage_points', 'trend'):
        raise ValueError('omi_single_semester_no_comparable_history_frozen')
    if op == 'weighted_ratio': raise ValueError('omi_transaction_or_dwelling_weights_not_frozen_no_pooling')
    if op == 'benchmark_gap': raise ValueError('omi_geographic_benchmark_not_reviewed')
    if op == 'anomaly': raise ValueError('omi_peer_anomaly_not_reviewed')
    if op == 'correlation': raise ValueError('omi_pair_not_jointly_reviewed')


def context(metric, key, dim):
    if key not in KEYS or dim not in dimensions(key): raise ValueError('omi_dimension_not_reviewed')
    if fingerprint(metric) != PUBLIC_HASH: raise ValueError('omi_public_definition_or_values_changed')
    rent = dim == 'rentMean'
    return dict(unit='eurm2month' if rent else 'eurm2',
                population='displayed residential OMI zones; civil dwellings, normal state, public reference selection',
                definition='unweighted municipal mean of displayed residential zone '+('rental' if rent else 'sale')+' reference quotations',
                method='arithmetic mean of published zone reference values; original OMI min/max ranges and selection records not replayed',
                frequency='semester', periodBasis='second semester 2025; neither annual average nor current 2026 market',
                nativeComponentsAvailable=False, nativeRecordReplayAvailable=False,
                adapter='omi/'+dim+'/v1')


def validated(engine, metric):
    towns = engine._catalog['towns']
    if len(towns) != 7 or {t['code']:t['name'] for t in towns} != TOWNS:
        raise ValueError('omi_municipal_identity_changed')
    rows = metric['rows']
    if len(rows) != 7 or {r['code']:r['town'] for r in rows} != TOWNS:
        raise ValueError('omi_municipal_identity_changed')
    for row in rows:
        zones = row['zones']
        if not zones or len({z['code'] for z in zones}) != len(zones):
            raise ValueError('omi_zone_partition_not_reconciled')
        for field in ('sale', 'rent'):
            if any(not finite(z[field]) or z[field] < 0 for z in zones):
                raise ValueError('omi_zone_value_invalid')
            expected = math.fsum(z[field] for z in zones)/len(zones)
            if not math.isclose(row[field+'Mean'], expected, rel_tol=0, abs_tol=1e-10):
                raise ValueError('omi_zone_mean_not_reconciled')
        if row['value'] != row['saleMean']: raise ValueError('omi_default_sale_alias_not_reconciled')
    for field in ('saleMean', 'rentMean'):
        expected = math.fsum(r[field] for r in rows)/len(rows)
        if not math.isclose(metric['aggregate'][field], expected, rel_tol=0, abs_tol=1e-10):
            raise ValueError('omi_municipal_aggregate_not_reconciled')


def observation(engine, key, index, dim, period, historical):
    metric = engine._catalog['metrics'][key]; ctx = context(metric, key, dim)
    if period != PERIOD: raise ValueError('omi_exact_semester_required')
    validated(engine, metric)
    row = metric['rows'][index]; field = 'value' if dim == 'total' else dim
    zonefield = 'rent' if dim == 'rentMean' else 'sale'
    evidence = [dict(kind='catalog_snapshot', path=engine.catalog_path, sha256=engine.catalog_hash,
                     valuePointer=f'/metrics/{key}/rows/{index}/{field}',
                     periodPointer=f'/metrics/{key}/meta/year',
                     zoneValuePointers=[f'/metrics/{key}/rows/{index}/zones/{i}/{zonefield}' for i in range(len(row['zones']))],
                     replayScope='published zone reference values only; original OMI quotation ranges and source files not frozen')]
    return dict(ctx, metric=key, dimension=dim, geography=row['code'], period=period, value=row[field],
                source=metric['sourceUrl'], evidence=evidence, provenance=evidence,
                notApplicable=False, dataUnavailable=False, missingReason=None), NOTES[:]
