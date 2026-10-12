"""Published census worker shares; distinct from work-matrix commuter margins."""
from semantic_query_library_adapters import TOWNS, fingerprint

KEYS = ('outsideMunicipality',)
PUBLIC_HASH = '1c3ad84d4574a5e0466f498f14b7f4e51fb85729c9787efb10a75755a17af74b'
NOTES = ['outside_census_resident_worker_share_not_work_matrix_commuter_universe',
         'outside_not_complement_of_matrix_self_containment',
         'outside_public_catalog_replay_not_original_census_records',
         'outside_native_numerator_denominator_not_frozen_no_count_reconstruction',
         'outside_seven_town_simple_mean_not_versilia_worker_share',
         'outside_work_in_other_municipality_not_outside_versilia',
         'outside_2021_reference_not_current_daily_travel_or_study_mobility',
         'outside_numerical_rank_not_transport_need_or_policy_priority']


def token(key, period):
    if str(period) != '2021': raise ValueError('outside_only_census_2021_frozen')
    return '2021'


def dimensions(key): return ['total']
def scopes(key, dim): return []
def operations(key, dim): return ['compare', 'rank']


def selection_guard(key, dim, op):
    if op in ('series', 'absolute_change', 'relative_change', 'percentage_points', 'trend'):
        raise ValueError('outside_single_census_no_comparable_history_frozen')
    if op == 'weighted_ratio': raise ValueError('outside_census_components_not_frozen_no_pooling')
    if op == 'benchmark_gap': raise ValueError('outside_geographic_benchmark_not_reconciled')
    if op == 'anomaly': raise ValueError('outside_peer_anomaly_not_reviewed')
    if op == 'correlation': raise ValueError('outside_pair_not_jointly_reviewed')


def context(metric, key, dim):
    if key not in KEYS or dim not in dimensions(key): raise ValueError('outside_dimension_not_reviewed')
    if fingerprint(metric) != PUBLIC_HASH: raise ValueError('outside_public_definition_or_values_changed')
    return dict(unit='percent', population='resident employed persons in the published census indicator; not work-matrix daily commuters',
                definition='published share of resident workers whose workplace is in another municipality',
                method='published census percentage at one decimal; no native counts or denominator reconstructed',
                frequency='census_snapshot', periodBasis='published census reference 2021; no comparable history frozen',
                nativeComponentsAvailable=False, nativeRecordReplayAvailable=False,
                adapter='outside_municipality/total/v1')


def observation(engine, key, index, dim, period, historical):
    metric = engine._catalog['metrics'][key]; ctx = context(metric, key, dim)
    towns = engine._catalog['towns']
    if len(towns) != 7 or {t['code']:t['name'] for t in towns} != TOWNS:
        raise ValueError('outside_municipal_identity_changed')
    if period != '2021': raise ValueError('outside_only_census_2021_frozen')
    row = metric['rows'][index]
    evidence = [dict(kind='catalog_snapshot', path=engine.catalog_path, sha256=engine.catalog_hash,
                     valuePointer=f'/metrics/{key}/rows/{index}/value', periodPointer=f'/metrics/{key}/meta/year',
                     replayScope='published census share only; not original census records or work-matrix reconstruction')]
    return dict(ctx, metric=key, dimension=dim, geography=row['code'], period=period, value=row['value'],
                source=metric['sourceUrl'], evidence=evidence, provenance=evidence,
                notApplicable=False, dataUnavailable=False, missingReason=None), NOTES[:]
