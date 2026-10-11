"""Frozen scheduled TPL: municipal trip memberships, GTFS access IDs and span."""
import math
import re

from materialize_mobilita_tpl_v119 import build_metrics, validate_snapshot, clock_seconds
from semantic_query_library_adapters import TOWNS, fingerprint

TRIPS, POINTS, SPAN = KEYS = ('scheduledTplTripsPer1000', 'activeTplAccessPoints', 'tplServiceSpan')
PATH = 'data/source-snapshots/mobilita-tpl-2026-08-26.json'
HASH = 'f7178d3bff676b95cf27bf31669147974b0edb7276181b6af2377f77a71ed2ca'
FINGERPRINT = '5b792e7aaecfff9c65619e7204075d26bd3e3580202b0c4b8545367942e22f3b'
DATE = '2026-08-26'
LABEL = '26 agosto 2026'
URL = 'https://dati.toscana.it/dataset/rt-oraritb'
FIELDS = {TRIPS: 'trips', POINTS: 'activeAccessPoints', SPAN: 'serviceSpanHours'}
NOTES = ['tpl_scheduled_summer_weekday_not_actual_service_reliability_capacity_or_passengers',
         'tpl_municipal_trip_memberships_not_unique_territorial_trips',
         'tpl_feed_stop_ids_not_unique_physical_stops_or_walk_access',
         'tpl_span_not_frequency_or_continuous_service',
         'tpl_gtfs_calendar_spatial_join_and_raw_feeds_not_replayed',
         'tpl_no_automatic_causal_or_policy_priority_inference']


def token(key, period):
    if str(period) == LABEL: return DATE
    if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', str(period)):
        raise ValueError('tpl_explicit_service_date_required')
    if str(period) != DATE: raise ValueError('tpl_service_date_not_frozen')
    return DATE


def dimensions(key): return ['total'] + (['view:normalized'] if key != SPAN else [])
def scopes(key, dim): return []
def operations(key, dim): return ['compare', 'rank']


def selection_guard(key, dim, op):
    if op in ('series', 'absolute_change', 'relative_change', 'percentage_points', 'trend'):
        raise ValueError('tpl_single_service_day_no_history')
    if op == 'weighted_ratio': raise ValueError('tpl_pooling_not_reviewed_memberships_and_access_ids')
    if op == 'benchmark_gap': raise ValueError('tpl_geographic_benchmark_not_frozen')
    if op == 'anomaly': raise ValueError('tpl_peer_anomaly_not_reviewed')
    if op == 'correlation': raise ValueError('tpl_pair_not_jointly_reviewed')


def context(metric, key, dim):
    meta = metric['meta']
    if (dim not in dimensions(key) or meta.get('key') != key or meta.get('year') != LABEL
            or meta.get('unit') != ('hours' if key == SPAN else 'number')
            or meta.get('polarity') != 'neutral' or meta.get('theme') != 'mobilita'
            or metric.get('sourceUrl') != URL or meta.get('benchmark') is not None):
        raise ValueError('tpl_definition_changed')
    return dict(unit='per1000' if dim == 'view:normalized' else meta['unit'],
                population='municipal scheduled trip memberships' if key == TRIPS else 'active passenger-usable (feed, stop_id) pairs' if key == POINTS else 'scheduled municipal departure window',
                definition='count of trips serving at least one usable geolocated access ID, deduplicated within municipality' if key == TRIPS else 'count of distinct feed and stop ID pairs serving the municipality on service date' if key == POINTS else 'last minus first departure in GTFS service-day seconds, rounded to two decimal hours',
                method=('native municipal count / frozen residents × 1000' if dim == 'view:normalized' else 'normalized frozen GTFS municipal count' if key != SPAN else '(last GTFS seconds - first GTFS seconds) / 3600; round(value,2)'),
                frequency='single_service_day_snapshot', periodBasis='service day 26 August 2026; normalized denominator residents 1 January 2026; GTFS hours beyond 24 retained',
                nativeComponentsAvailable=False, adapter='tpl/'+key+'/v1')


def validated(engine, key):
    snap, ref = engine.file(PATH)
    if ref.get('path') != PATH or ref.get('sha256') != HASH or fingerprint(snap) != FINGERPRINT:
        raise ValueError('tpl_frozen_input_changed')
    towns = engine._catalog['towns']
    if len(towns) != 7 or {x['code']: x['name'] for x in towns} != TOWNS:
        raise ValueError('tpl_municipal_identity_changed')
    validate_snapshot(snap, towns)
    metric = engine._catalog['metrics'][key]
    # Reconcile the full published definition, both scales and all aggregates.
    # The reference materializer is not a replay of calendar/stop IDs/geometries.
    expected = build_metrics(engine._catalog, snap)[key]
    if fingerprint(metric) != fingerprint(expected):
        raise ValueError('tpl_catalog_native_reconciliation_changed')
    if key != SPAN:
        population = engine._catalog['metrics']['population']
        rows = population['rows']
        if (population['meta']['year'] != '2026' or len(rows) != 7
                or {r['code'] for r in rows} != set(TOWNS)):
            raise ValueError('tpl_denominator_identity_or_period_changed')
        for row in rows:
            value = row.get('value')
            if (row.get('town') != TOWNS[row['code']] or type(value) not in (int, float)
                    or not math.isfinite(value) or value != snap['raw'][row['town']]['population']):
                raise ValueError('tpl_denominator_reconciliation_changed')
    return snap, ref


def observation(engine, key, index, dim, period, historical):
    metric = engine._catalog['metrics'][key]; ctx = context(metric, key, dim)
    if period != DATE: raise ValueError('tpl_service_date_not_frozen')
    snap, ref = validated(engine, key); row = metric['rows'][index]
    name = row['town']; raw = snap['raw'][name]; field = FIELDS[key]
    normalized = dim == 'view:normalized'
    value = row['normalized']['value'] if normalized else row['value']
    evidence = [dict(kind='catalog_snapshot', path=engine.catalog_path, sha256=engine.catalog_hash,
                     valuePointer=f'/metrics/{key}/rows/{index}/'+('normalized/value' if normalized else 'value')),
                dict(ref, kind='source_snapshot', recordPointer=f'/raw/{name}/{field}',
                     nativeCount=raw[field] if key != SPAN else None,
                     nativeComponents=dict(busTrips=raw['busTrips'], railTrips=raw['railTrips']) if key == TRIPS else dict(first=raw['first'], last=raw['last'], firstSeconds=clock_seconds(raw['first']), lastSeconds=clock_seconds(raw['last'])) if key == SPAN else dict(identifier='feed,stop_id', rawIdsFrozen=False),
                     replayScope='normalized municipal snapshot reconciliation; calendar, feed records and spatial join not replayed')]
    if normalized:
        evidence.append(dict(ref, kind='source_snapshot', recordPointer=f'/raw/{name}/population',
                             nativeDenominator=raw['population'], denominatorDate='2026-01-01'))
    notes = NOTES[:] + (['tpl_normalized_residents_2026_not_passengers_or_population_served'] if normalized else [])
    if key == SPAN: notes += ['tpl_gtfs_hours_beyond_24_same_service_day_public_two_decimals']
    return dict(ctx, metric=key, dimension=dim, geography=row['code'], period=period, value=value,
                source=URL, evidence=evidence, provenance=evidence, notApplicable=False,
                dataUnavailable=False, missingReason=None), notes
