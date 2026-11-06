"""Public route inventory: replay frozen memberships, never municipal geometry."""
from a6_pins import Pin as _pin
import base64
from collections import Counter
import gzip
import hashlib
import json

from semantic_query_library_adapters import TOWNS, fingerprint

MODES = {'slowMobilityRoutes': None, 'slowMobilityTrekking': 'trekking',
         'slowMobilityCammini': 'cammino', 'slowMobilityBici': 'bicycle',
         'slowMobilityMtb': 'mtb'}
KEYS = tuple(MODES)
PERIOD = '2026-08-12'
PUBLIC_HASHES = {
    'slowMobilityRoutes': _pin('slow_mobility#1'),
    'slowMobilityTrekking': _pin('slow_mobility#2'),
    'slowMobilityCammini': _pin('slow_mobility#3'),
    'slowMobilityBici': _pin('slow_mobility#4'),
    'slowMobilityMtb': _pin('slow_mobility#5')}
# Original base64 bytes, decoded JSON bytes, semantic properties projection.
PART_HASHES = [
 (_pin('slow_mobility#6'), _pin('slow_mobility#7'), _pin('slow_mobility#8')),
 (_pin('slow_mobility#9'), _pin('slow_mobility#10'), _pin('slow_mobility#11')),
 (_pin('slow_mobility#12'), _pin('slow_mobility#13'), _pin('slow_mobility#14')),
 (_pin('slow_mobility#15'), _pin('slow_mobility#16'), _pin('slow_mobility#17')),
 (_pin('slow_mobility#18'), _pin('slow_mobility#19'), _pin('slow_mobility#20'))]
METADATA = {
 'percorsi/data/site_stats.json': (_pin('slow_mobility#21'), _pin('slow_mobility#22')),
 'percorsi/data/master_summary.json': (_pin('slow_mobility#23'), _pin('slow_mobility#24'))}
NOTES = ['slow_mobility_inventory_not_exhaustive_or_current_safety',
         'slow_mobility_A0_B1_provenance_not_accessibility_quality',
         'slow_mobility_municipal_memberships_overlap_not_additive_unique_routes',
         'slow_mobility_primary_mode_not_all_possible_activities',
         'slow_mobility_membership_replay_not_geometry_intersection_replay',
         'slow_mobility_inventory_20260812_not_current_route_status',
         'slow_mobility_no_municipal_lengths_or_reverse_derived_rates',
         'slow_mobility_numeric_rank_not_policy_priority']


def token(key, period):
    if str(period) not in ('2026', PERIOD): raise ValueError('slow_mobility_period_not_frozen')
    return PERIOD


def dimensions(key): return ['total']
def scopes(key, dim): return []
def operations(key, dim): return ['compare', 'rank']


def selection_guard(key, dim, op):
    if op in ('series', 'absolute_change', 'relative_change', 'percentage_points', 'trend'):
        raise ValueError('slow_mobility_inventory_history_editorial_not_territorial_series')
    if op == 'weighted_ratio': raise ValueError('slow_mobility_municipal_memberships_overlap_no_pooling')
    if op == 'benchmark_gap': raise ValueError('slow_mobility_geographic_benchmark_not_reviewed')
    if op == 'anomaly': raise ValueError('slow_mobility_inventory_peer_anomaly_not_reviewed')
    if op == 'correlation': raise ValueError('slow_mobility_shared_route_records_pair_not_reviewed')


def context(metric, key, dim):
    if key not in KEYS or dim != 'total': raise ValueError('slow_mobility_dimension_not_reviewed')
    if fingerprint(metric) != PUBLIC_HASHES[key]: raise ValueError('slow_mobility_public_definition_or_values_changed')
    return dict(unit='count', population='public A0/B1 route records with frozen municipal membership',
                definition='count distinct route IDs assigned to municipality; '+('all primary modes' if MODES[key] is None else 'primary mode '+MODES[key]),
                method='replay frozen editorial inventory memberships; not geometric reintersection or current condition survey',
                frequency='editorial_inventory_snapshot', periodBasis='inventory published 12 August 2026; route evidence dates and unrechecked 2023 statuses remain distinct',
                nativeComponentsAvailable=False, nativeRecordReplayAvailable=True,
                adapter='slow_mobility/'+key+'/v1')


def part(engine, number):
    path=f'percorsi/data/routes-part-{number:02d}.b64'
    byte_hash, decoded_hash, projection_hash = PART_HASHES[number]
    reference=dict(path=path, sha256=byte_hash, decodedSha256=decoded_hash,
                   encoding='base64+gzip+json', cacheProjection='record properties only; geometry omitted')
    if path not in engine.files:
        body=(engine.root/path).read_bytes()
        if hashlib.sha256(body).hexdigest()!=byte_hash: raise ValueError('slow_mobility_frozen_route_part_changed')
        raw=gzip.decompress(base64.b64decode(body.strip(),validate=True))
        if hashlib.sha256(raw).hexdigest()!=decoded_hash: raise ValueError('slow_mobility_frozen_route_part_changed')
        decoded=json.loads(raw)
        # Original bytes are attested; coordinates do not participate in the query.
        engine.files[path]=([{'p':record['p']} for record in decoded], reference.copy())
    records, ref=engine.files[path]
    if ref!=reference or fingerprint(records)!=projection_hash: raise ValueError('slow_mobility_frozen_route_part_changed')
    return records, ref


def inventory(engine):
    parts=[part(engine, i) for i in range(len(PART_HASHES))]
    records=[record['p'] for rows,_ in parts for record in rows]
    ids=[p['id'] for p in records]
    if len(set(ids))!=len(ids): raise ValueError('slow_mobility_route_identity_not_unique')
    for p in records:
        members=p['municipalities']
        if (not members or len(members)!=len(set(members)) or not set(members)<=set(TOWNS.values())
            or p['primary_mode'] not in ('trekking','cammino','bicycle','mtb')
            or p['quality_code'] not in ('A0','B1') or p['public_default'] is not True
            or p['publication_status']!='published' or not p['source_url']):
            raise ValueError('slow_mobility_inventory_scope_changed')
    metadata=[]
    for path,(byte_hash,object_hash) in METADATA.items():
        obj,ref=engine.file(path)
        if ref!={'path':path,'sha256':byte_hash} or fingerprint(obj)!=object_hash:
            raise ValueError('slow_mobility_frozen_inventory_metadata_changed')
        metadata.append((obj,ref))
    stats,summary=metadata[0][0],metadata[1][0]
    modes=dict(Counter(p['primary_mode'] for p in records));qualities=dict(Counter(p['quality_code'] for p in records))
    if (len(records)!=summary['public_total'] or len(records)!=stats['versilia']['routes']
        or modes!=summary['by_mode'] or modes!=stats['versilia']['by_mode']
        or qualities!=summary['by_quality'] or qualities!=stats['versilia']['by_quality']):
        raise ValueError('slow_mobility_inventory_reconciliation_failed')
    for town in TOWNS.values():
        members=[p for p in records if town in p['municipalities']]
        published=next(v for v in stats['municipalities'].values() if v['name']==town)
        if (published['routes']!=len(members) or summary['by_municipality'][town]!=len(members)
            or published['by_mode']!={m:sum(p['primary_mode']==m for p in members) for m in modes}
            or published['by_quality']!={q:sum(p['quality_code']==q for p in members) for q in qualities}):
            raise ValueError('slow_mobility_inventory_reconciliation_failed')
    return parts,metadata


def observation(engine, key, index, dim, period, historical):
    metric=engine._catalog['metrics'][key];ctx=context(metric,key,dim)
    if period!=PERIOD: raise ValueError('slow_mobility_period_not_frozen')
    towns=engine._catalog['towns']
    if len(towns)!=7 or {t['code']:t['name'] for t in towns}!=TOWNS: raise ValueError('slow_mobility_municipal_identity_changed')
    row=metric['rows'][index];parts,metadata=inventory(engine);mode=MODES[key]
    evidence=[dict(kind='catalog_snapshot',path=engine.catalog_path,sha256=engine.catalog_hash,
                   valuePointer=f'/metrics/{key}/rows/{index}/value')]
    matched=[]
    for records,ref in parts:
        indices=[i for i,r in enumerate(records) if row['town'] in r['p']['municipalities'] and (mode is None or r['p']['primary_mode']==mode)]
        matched.extend(records[i]['p']['id'] for i in indices)
        evidence.append(dict(ref,kind='source_snapshot',recordPointers=[f'/{i}/p' for i in indices],
                             replayScope='native route IDs, primary modes, public classes and curated municipality memberships; geometry not reintersected'))
    if type(row['value']) is not int or row['value']!=len(matched): raise ValueError('slow_mobility_native_count_not_reconciled')
    evidence.extend(dict(ref,kind='source_snapshot',replayScope='frozen inventory summaries') for _,ref in metadata)
    return dict(ctx,metric=key,dimension=dim,geography=row['code'],period=period,value=row['value'],
                source=metric['sourceUrl'],countedRouteIds=sorted(matched),evidence=evidence,provenance=evidence,
                notApplicable=False,dataUnavailable=False,missingReason=None),NOTES[:]
