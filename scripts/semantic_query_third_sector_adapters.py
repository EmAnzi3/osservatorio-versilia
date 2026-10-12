"""RUNTS legal-seat stock, with separately dated population components."""
import math
from semantic_query_library_adapters import TOWNS, fingerprint

KEYS = ('thirdSector',)
PERIOD = '2026-10-11'
POPULATION_PERIOD = '2026-01-01'
PATH = 'data/source-snapshots/runts-public-2026-10-11.json'
HASH = '6ced81b1212547ab366a195be0ed51d56cbc928f5955b07f61f009c9d7fcfd83'
OBJECT_HASH = '002601d8a0dd4bba639770d55c532e14b48584167b1a48d6da66299813371a85'
PUBLIC_HASH = 'e564b7027c414f82e906aa221290dc04359fb54168e70470ab683989adff3da9'
NOTES = ['third_sector_legal_seat_not_activity_services_or_volunteer_count',
         'third_sector_register_20261011_population_20260101_distinct_dates',
         'third_sector_normalized_snapshot_not_original_excel_entity_replay',
         'third_sector_all_registered_sections_not_all_local_associations',
         'third_sector_no_reconstructed_2025_history_or_seat_transfers',
         'third_sector_numeric_rank_not_quality_or_policy_priority']


def token(key, period):
    if str(period) not in ('2026', PERIOD): raise ValueError('third_sector_period_not_frozen')
    return PERIOD


def dimensions(key): return ['total', 'registeredEntities', 'nativeRatio']
def scopes(key, dim): return []
def operations(key, dim): return ['compare', 'rank'] + (['weighted_ratio'] if dim == 'nativeRatio' else [])


def selection_guard(key, dim, op):
    if op in ('series', 'absolute_change', 'relative_change', 'percentage_points', 'trend'):
        raise ValueError('third_sector_legal_seat_history_not_frozen')
    if op == 'weighted_ratio' and dim != 'nativeRatio': raise ValueError('third_sector_native_ratio_dimension_required')
    if op == 'benchmark_gap': raise ValueError('third_sector_geographic_benchmark_not_reviewed')
    if op == 'anomaly': raise ValueError('third_sector_peer_anomaly_not_reviewed')
    if op == 'correlation': raise ValueError('third_sector_pair_not_jointly_reviewed')


def context(metric, key, dim):
    if key not in KEYS or dim not in dimensions(key): raise ValueError('third_sector_dimension_not_reviewed')
    if fingerprint(metric) != PUBLIC_HASH: raise ValueError('third_sector_public_definition_or_values_changed')
    count = dim == 'registeredEntities'
    return dict(unit='count' if count else 'per1000',
                population='RUNTS entities assigned once by current legal municipality, all registered sections',
                definition='unique fiscal-code registered entities by legal seat' if count else 'registered entities by legal seat / resident population × 1000',
                method='frozen normalized municipal counts and Istat denominators; original Excel individual records not replayed',
                frequency='register_snapshot', periodBasis='RUNTS stock 11 October 2026; resident denominator 1 January 2026',
                nativeComponentsAvailable=dim == 'nativeRatio', nativeRecordReplayAvailable=False,
                adapter='third_sector/'+dim+'/v1')


def validated(engine, key):
    snap, ref = engine.file(PATH)
    if ref != dict(path=PATH, sha256=HASH) or fingerprint(snap) != OBJECT_HASH:
        raise ValueError('third_sector_frozen_input_changed')
    towns = engine._catalog['towns']
    if len(towns) != 7 or {t['code']:t['name'] for t in towns} != TOWNS:
        raise ValueError('third_sector_municipal_identity_changed')
    rows = snap['rows']
    if len(rows) != 7 or {r['code']:r['town'] for r in rows} != TOWNS:
        raise ValueError('third_sector_snapshot_identity_changed')
    public = {r['code']:r for r in engine._catalog['metrics'][key]['rows']}
    for r in rows:
        p = public[r['code']]
        if (type(r['count']) is not int or r['count'] < 0 or type(r['population']) is not int or r['population'] <= 0
            or r['populationReference'] != POPULATION_PERIOD or p['populationReference'] != POPULATION_PERIOD
            or p['registeredEntities'] != r['count'] or p['residentPopulation'] != r['population']
            or not math.isclose(r['per1000'],r['count']/r['population']*1000,rel_tol=0,abs_tol=1e-12)
            or p['value'] != r['per1000']):
            raise ValueError('third_sector_components_not_reconciled')
    count = sum(r['count'] for r in rows); population = sum(r['population'] for r in rows)
    if (snap['versilia'] != dict(count=count,population=population)
        or engine._catalog['metrics'][key]['aggregate']['value'] != count/population*1000):
        raise ValueError('third_sector_aggregate_not_reconciled')
    return snap, ref


def observation(engine, key, index, dim, period, historical):
    metric=engine._catalog['metrics'][key];ctx=context(metric,key,dim)
    if period != PERIOD: raise ValueError('third_sector_period_not_frozen')
    snap,ref=validated(engine,key);row=metric['rows'][index]
    j=next(i for i,r in enumerate(snap['rows']) if r['code']==row['code']);r=snap['rows'][j]
    field='registeredEntities' if dim=='registeredEntities' else 'value'
    evidence=[dict(kind='catalog_snapshot',path=engine.catalog_path,sha256=engine.catalog_hash,
                   valuePointer=f'/metrics/{key}/rows/{index}/{field}'),
              dict(ref,kind='source_snapshot',recordPointer=f'/rows/{j}',
                   sourceDocumentSha256=snap['sourceSha256'],
                   replayScope=snap['replayScope'],
                   nativeComponents=dict(numerator=r['count'],denominator=r['population'],scale=1000))]
    result=dict(ctx,metric=key,dimension=dim,geography=row['code'],period=period,
                value=r['count'] if dim=='registeredEntities' else r['per1000'],
                source=snap['sourceUrl'],evidence=evidence,provenance=evidence,
                notApplicable=False,dataUnavailable=False,missingReason=None)
    if dim=='nativeRatio':
        result.update(numerator=r['count'],denominator=r['population'],scale=1000,
                      numeratorPeriod=PERIOD,denominatorPeriod=POPULATION_PERIOD)
    return result,NOTES[:]
