"""Frozen Iter.Net clipped lengths; public density and component ratio distinct."""
import math
from semantic_query_library_adapters import TOWNS, fingerprint

KEYS = ('roadNetworkProfile',)
SNAPSHOT = 'data/source-snapshots/territorio-v137-official.json'
SNAPSHOT_SHA = 'a9de6f423577f7cf99b8fa020940e43e3ab6e7dc0aeed0531155066abacb25b9'
PUBLIC_HASH = '872433466aa911e9287a78b93ea9d9c930469a0d9ea26765ed10ec5b74a20267'
FIELDS = {'length':('graphKm',), 'density':('graphDensity',),
          'adminMunicipal':('administrativeClassKm','municipal'),
          'adminProvincial':('administrativeClassKm','provincial'),
          'adminRegional':('administrativeClassKm','regional'),
          'adminState':('administrativeClassKm','state'),
          'adminPrivate':('administrativeClassKm','private'),
          'paved':('pavementKm','paved'), 'unpaved':('pavementKm','unpaved'),
          'pavementUnclassified':('pavementKm','unclassified')}
PERIOD = '2022-map/2026-boundaries'
NOTES = ['road_network_elements_not_unique_roads_or_maintenance_liability',
         'road_network_2022_map_clipped_to_2026_boundaries_not_current_condition',
         'road_network_normalized_snapshot_replay_not_original_geometry_replay',
         'road_network_admin_and_pavement_are_separate_partitions_do_not_add',
         'road_network_density_native_ratio_distinct_from_rounded_public_value',
         'road_network_numeric_rank_not_quality_accessibility_or_policy_priority']


def token(key, period):
    if str(period) not in ('2022', PERIOD): raise ValueError('road_network_period_not_frozen')
    return PERIOD


def dimensions(key): return ['total', *('view:'+k for k in FIELDS), 'nativeRatio']
def scopes(key, dim): return []
def operations(key, dim): return ['compare','rank']+(['weighted_ratio'] if dim=='nativeRatio' else [])


def selection_guard(key, dim, op):
    if op in ('series','absolute_change','relative_change','percentage_points','trend'):
        raise ValueError('road_network_single_snapshot_no_history')
    if op=='weighted_ratio' and dim!='nativeRatio': raise ValueError('road_network_only_native_density_pooling_reviewed')
    if op=='benchmark_gap': raise ValueError('road_network_geographic_benchmark_not_reviewed')
    if op=='anomaly': raise ValueError('road_network_peer_anomaly_not_reviewed')
    if op=='correlation': raise ValueError('road_network_pair_not_jointly_reviewed')


def context(metric, key, dim):
    if key not in KEYS or dim not in dimensions(key): raise ValueError('road_network_dimension_not_reviewed')
    if fingerprint(metric)!=PUBLIC_HASH: raise ValueError('road_network_public_definition_or_values_changed')
    view='density' if dim=='nativeRatio' else 'length' if dim=='total' else dim.split(':',1)[1]
    return dict(unit='km_per_km2' if view=='density' else 'km',
                population='Iter.Net 4.48 road graph elements clipped to municipal boundaries',
                definition='native graph length divided by native municipal area' if dim=='nativeRatio' else 'published '+view+' of clipped road graph elements',
                method='ratio of frozen six-decimal km/km2 components' if dim=='nativeRatio' else 'frozen GIS result at published six-decimal precision',
                frequency='irregular_snapshot', periodBasis='Iter.Net June 2022; generalized Istat boundaries 1 January 2026; EPSG:3003; normalized snapshot verified September 2026',
                nativeComponentsAvailable=dim=='nativeRatio', adapter='road_network/'+dim+'/v1')


def number(value):
    if type(value) not in (int,float) or not math.isfinite(value) or value<0: raise ValueError('road_network_invalid_components')
    return value


def close(a,b,tolerance=1e-8):
    if not math.isclose(number(a),number(b),rel_tol=0,abs_tol=tolerance): raise ValueError('road_network_component_reconciliation_failed')


def observation(engine,key,index,dim,period,historical):
    metric=engine._catalog['metrics'][key];ctx=context(metric,key,dim)
    if period!=PERIOD: raise ValueError('road_network_period_not_frozen')
    towns=engine._catalog['towns']
    if len(towns)!=7 or {t['code']:t['name'] for t in towns}!=TOWNS: raise ValueError('road_network_municipal_identity_changed')
    snap,ref=engine.file(SNAPSHOT)
    # Verify the cached object as well as its original bytes, including boundary metadata.
    if ref.get('sha256')!=SNAPSHOT_SHA or fingerprint(snap)!=SNAPSHOT_FINGERPRINT: raise ValueError('road_network_frozen_snapshot_changed')
    block=snap['roadNetworkProfile'];row=metric['rows'][index];native=block['municipalities'][row['town']]
    if snap['measurementBoundary']['istatCodes']!={v:k for k,v in TOWNS.items()}: raise ValueError('road_network_municipal_identity_changed')
    length=number(native['graphKm']);area=number(native['municipalAreaKm2'])
    if area<=0: raise ValueError('road_network_invalid_components')
    close(row['municipalAreaKm2'],area);close(row['value'],length)
    for field in ('administrativeClassKm','pavementKm'):
        close(math.fsum(number(v) for v in native[field].values()),length,3e-6)
    # GIS density was rounded independently, before length/area were rounded.
    # Propagate half a six-decimal unit for both components and the density.
    lower=(length-5e-7)/(area+5e-7)-5e-7
    upper=(length+5e-7)/(area-5e-7)+5e-7
    if not lower<=number(native['graphDensity'])<=upper: raise ValueError('road_network_component_reconciliation_failed')
    close(math.fsum(number(v['graphKm']) for v in block['municipalities'].values()),block['versilia']['graphKm'],1e-5)
    close(math.fsum(number(v['municipalAreaKm2']) for v in block['municipalities'].values()),block['versilia']['unionAreaKm2'],1e-5)
    view='density' if dim=='nativeRatio' else 'length' if dim=='total' else dim.split(':',1)[1]
    j=next(i for i,p in enumerate(row['parts']) if p['key']==view)
    published=row['value'] if dim=='total' else row['parts'][j]['value']
    expected=native
    for f in FIELDS[view]:expected=expected[f]
    close(published,expected)
    parts=dict(numerator=length,denominator=area,scale=1) if dim=='nativeRatio' else {}
    pointer=f'/metrics/{key}/rows/{index}/'+('value' if dim=='total' else f'parts/{j}/value')
    record='/roadNetworkProfile/municipalities/'+row['town']
    evidence=[dict(kind='catalog_snapshot',path=engine.catalog_path,sha256=engine.catalog_hash,valuePointer=pointer),
              dict(ref,kind='source_snapshot',recordPointer=record,componentPointers=dict(numerator=record+'/graphKm',denominator=record+'/municipalAreaKm2'),replayScope='normalized clipped lengths and boundary metadata; original shapefile and GIS clip not replayed')]
    return dict(ctx,**parts,metric=key,dimension=dim,geography=row['code'],period=period,
                value=length/area if parts else published,publishedValue=published,source=metric['sourceUrl'],
                evidence=evidence,provenance=evidence,notApplicable=False,dataUnavailable=False,missingReason=None),NOTES[:]

SNAPSHOT_FINGERPRINT = '341af19cb80ec6d7f4f0ed6e3d626639b8e24e1b13801a13a046cc5d3ea427c5'
