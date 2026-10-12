"""Public route inventory: replay frozen memberships, never municipal geometry."""
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
    'slowMobilityRoutes': '835310443f11b0bb09039cd6a3b7b98a5d770bd05b34f15f06978852c73ee289',
    'slowMobilityTrekking': '9518add82d6baad2661eff27715c5007b06c89fd3d1be9274ea5e5b6e5a4a65d',
    'slowMobilityCammini': '77bcf4b6607b1469d794d1ec4f31ca8d139cfbf3f6152f1dc78cccd57ebd2d34',
    'slowMobilityBici': 'f3fdc4bfed838d6a00f842e178af0126b079cdd3d15abca7b59b05c4689dcde8',
    'slowMobilityMtb': '2325ab1415faa03a4c722ab75fb457e3a545c395d58d3317fb4a9678faabb113'}
# Original base64 bytes, decoded JSON bytes, semantic properties projection.
PART_HASHES = [
 ('15e1caad4b394c58c7dee358a78d4a91fa16186910b19c43afe8ea5ccf47f4af', '4a3c90ef9377bbc46cb2220f7529b5d4963658100d4ddcab151b9835b1414269', '054a267a62de1bd389da30175b9dd5f28da795c07440b7a00637095bd12961e3'),
 ('aca055f94bc35a096d28293eaa20cd1bf0e074a016c6ec3c4f6c5142874d4a56', 'ebe10fcea41b321e630f05b8128e10cb9a47cf9e1454f59fe4ee4559876399cd', 'd6981c1a9f5e34aac22dd2b2fe9ef9ae63e2a4b04afdb88ae8a215a36dcd5083'),
 ('84386a17d3966281c742b416479f13f8a46a80e1fc7e6ad5e48c512335f26c3b', '9c1b91c38844036538d3b420caa282490c4a8cf37e6d021123346b958e17f569', '46099beb6761968cfa17ca766adbc53f79f8e6b1337f0887da404da22769bb95'),
 ('e32cc09bfe8f29b8c87b7cc62714d630db800ce749ef1ae3fb659c822c534b0b', '4cbfde87748a8d743c1033cbf5677b4991193e3a91a21c672a595241bafddf16', 'f7232360ad9b2a26857dd6d0aeaf8587886e37573fca2074881b046aed538df5'),
 ('d1d511628c92e3e35f2aca5dad92da21b0a53c6cc8d255c886e60043b06a3fa5', 'b28d11f4ff6975b3817af9c1229644b6052f23912b1f847f8c117863df4e7851', '9b1082fb2634ae0fc97420ade1945856adc26f8ad13f9938bdc3b2ec24edbb2d')]
METADATA = {
 'percorsi/data/site_stats.json': ('958dd79ad99f06c2edfc7116d253722787f793a36b4b0b7e96afc2ea6b59fac4', 'e45f04f4e8a5a2da49f3e4c6471dc89085114efda4f155bc4f4da8a2b60b96df'),
 'percorsi/data/master_summary.json': ('e7c70bebae9da2e295d7af0b451493bbd58c4f72165fdb124bbfde443ee5bcc1', '2ad450e1a60e331dcac0215215b8ffb03a5c7abe7685cdbb08720c50a2a24cdf')}
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
