"""Frozen regional protections, linear network and hydraulic census; no geometry acquisition."""
import math
import json
import hashlib
from semantic_operations import finite

KEYS = ('protectedNaturalAreas','managedReticulumLength','hydraulicWorksCensusElements')
TERRITORY = 'data/source-snapshots/territorio-v137-official.json'
GIS = 'data/source-snapshots/bonifica-rischio-v126-gis.json'
CATEGORIES = ('total','parksReserves','anpil','natura2000','zsc','zps','ramsar')
LAYERS = ('area','line','point')
LABELS = {'protectedNaturalAreas':'archivi geografici ufficiali Regione Toscana · consultati 12 settembre 2026','managedReticulumLength':'DCRT 24/2025 · confini Istat 1 gennaio 2026','hydraulicWorksCensusElements':'2021'}
PERIODS = {'protectedNaturalAreas':'2026-09-12','managedReticulumLength':'2025-map/2026-boundaries','hydraulicWorksCensusElements':'2021-census/2026-boundaries'}
URLS = {'protectedNaturalAreas':'https://www.regione.toscana.it/sistema-aree-naturali-protette','managedReticulumLength':'https://www.regione.toscana.it/-/reticolo-idrografico-e-di-gestione','hydraulicWorksCensusElements':'https://www.regione.toscana.it/-/censimento-delle-opere-idrauliche'}

def close(a,b,tol=1e-8):
    if not finite(a) or not finite(b) or not math.isclose(a,b,rel_tol=0,abs_tol=tol):raise ValueError('territory_catalog_source_mismatch')

def token(key,period):return PERIODS[key] if str(period)==LABELS[key] else str(period)

def dimensions(key):
    if key=='protectedNaturalAreas':return ['total',*('part:'+c for c in CATEGORIES),*('hectares:'+c for c in CATEGORIES)]
    if key=='managedReticulumLength':return ['total','view:full','view:managed','view:density']
    return ['total',*('layer:'+c for c in LAYERS)]

def view(key,dimension):
    if dimension not in dimensions(key):raise ValueError('territory_dimension_not_reviewed')
    return ('total' if key!='managedReticulumLength' else 'full') if dimension=='total' else dimension.split(':',1)[1]

def weighted(key,dimension):return key=='protectedNaturalAreas' and not dimension.startswith('hectares:') or key=='managedReticulumLength' and dimension=='view:density'

def context(metric,key,dimension):
    v=view(key,dimension)
    if str(metric['meta'].get('year'))!=LABELS[key] or metric.get('sourceUrl')!=URLS[key] or metric['meta'].get('unit')!={'protectedNaturalAreas':'percent','managedReticulumLength':'km','hydraulicWorksCensusElements':'number'}[key]:raise ValueError('territory_definition_or_reference_changed')
    u=('hectares' if dimension.startswith('hectares:') else 'percent') if key=='protectedNaturalAreas' else ('km_per_km2' if v=='density' else 'km') if key=='managedReticulumLength' else 'number'
    definition=('protected surface '+v+'; total is geometric union, categories overlap' if key=='protectedNaturalAreas' else 'regional hydrological network '+v+'; managed subset is not an additional network' if key=='managedReticulumLength' else 'official source features intersecting municipality, '+v+'; crossing features recur across towns, not physical works or projects')
    return dict(unit=u,population='municipal territory clipped with Istat 1 January 2026 boundaries',definition=definition,method='frozen regional GIS edition; native clipped geometry or source feature identity',frequency='irregular',periodBasis=PERIODS[key]+('; consultation is not legal designation date' if key=='protectedNaturalAreas' else '; source edition and clipping boundaries are separate references'),adapter='territory/'+key+'/'+v+'/v1')

def selection_guard(key,operation):
    if operation in ('series','absolute_change','relative_change','percentage_points','trend'):raise ValueError('territory_history_not_frozen')

def correlation_guard(observations,axis):
    if axis=='periods' and any(o['metric'] in KEYS for o in observations):raise ValueError('territory_history_not_frozen')

def native(engine,key,row):
    path=GIS if key=='hydraulicWorksCensusElements' else TERRITORY;s,ref=engine.file(path)
    if s.get('schemaVersion')!=1:raise ValueError('territory_native_reference_changed')
    family=s['hydraulicWorks' if key=='hydraulicWorksCensusElements' else 'reticulum' if key=='managedReticulumLength' else 'protectedNaturalAreas']
    towns=family['byTown' if key=='hydraulicWorksCensusElements' else 'municipalities']
    if len(engine._catalog['metrics'][key]['rows'])!=7 or set(towns)!={r['town'] for r in engine._catalog['metrics'][key]['rows']}:raise ValueError('territory_native_cohort_changed')
    if not any(t['name']==row['town'] and t['code']==row['code'] for t in engine._catalog['towns']):raise ValueError('territory_row_identity_changed')
    if key=='hydraulicWorksCensusElements':
        if family.get('approval')!='DGRT 1155/2021' or s['sources']['hydraulicWorks'].get('sha256')!='532b29090ce6fd09f06cf87a1f074b173eeddb57cb3ee1a92560e74ef17bb560' or s['sources']['istatBoundaries'].get('sha256')!='b011a590656c3a3ebc297fba80726a376aa843b6f164641cf6a4a990021a81d6':raise ValueError('territory_native_reference_changed')
        if s['boundaries']['byTown'][row['town']]['istatCode']!=row['code']:raise ValueError('territory_row_identity_changed')
    else:
        if family.get('referenceLabel')!=LABELS[key]:raise ValueError('territory_native_reference_changed')
        source=s['sources']['regioneProtectedAreas' if key=='protectedNaturalAreas' else 'regioneHydrography']
        if source.get('page')!=URLS[key]:raise ValueError('territory_native_reference_changed')
        if key=='protectedNaturalAreas':
            if family.get('categoryOrder')!=list(CATEGORIES[1:]) or hashlib.sha256(json.dumps(source.get('layers',{}),sort_keys=True,separators=(',',':')).encode()).hexdigest()!='aeb290eecdff230595a8b4ab9455b286218355873b8a986a184416583e6ee117' or any(len(l.get('sha256',''))!=64 for l in source['layers'].values()):raise ValueError('territory_native_reference_changed')
        elif source.get('sourceLayer')!='reticoloDCR242025.shp' or source.get('acquisition',{}).get('sha256')!='68d6bb2986c056e1c041009a21e3b9eb89de81d02830d412354c5770d7d9b122':raise ValueError('territory_native_reference_changed')
    return family,towns[row['town']],ref

def observation(engine,key,index,dimension,period,historical):
    if period!=PERIODS[key]:raise ValueError('territory_period_not_frozen')
    m=engine._catalog['metrics'][key];r=m['rows'][index];ctx=context(m,key,dimension);v=view(key,dimension);f,n,ref=native(engine,key,r);parts={}
    notes=['territory_single_frozen_edition_no_temporal_inference']
    if key=='protectedNaturalAreas':
        d=n['municipalAreaHa'];h=n['totalUnionHa'] if v=='total' else n['categoriesHa'][v]
        if not finite(d) or d<=0 or set(n['categoriesHa'])!=set(CATEGORIES[1:]) or any(not finite(x) or not 0<=x<=n['totalUnionHa']<=d for x in n['categoriesHa'].values()):raise ValueError('territory_invalid_native_components')
        for c in ('zsc','zps'):
            if n['categoriesHa'][c]>n['categoriesHa']['natura2000']:raise ValueError('territory_protection_hierarchy_changed')
        close(r['municipalAreaHa'],d)
        # Reconcile native union totals across the non-overlapping municipal partition.
        for field in ('municipalAreaHa','totalUnionHa'):close(math.fsum(x[field] for x in f['municipalities'].values()),f['versilia'][field],1e-5)
        for c in CATEGORIES[1:]:close(math.fsum(x['categoriesHa'][c] for x in f['municipalities'].values()),f['versilia']['categoriesHa'][c],1e-5)
        expected=h if dimension.startswith('hectares:') else h/d*100
        pub=next(p for p in r['parts'] if p['key']==v)
        close(pub['ha'],h);close(pub['value'],h/d*100)
        value=r.get('value') if dimension=='total' else pub['ha' if dimension.startswith('hectares:') else 'value']
        if weighted(key,dimension):parts=dict(numerator=h,denominator=d,scale=100)
        notes+=['protected_categories_overlap_total_is_native_geometric_union_not_category_sum','anpil_transitional_status_not_new_designation','protected_consultation_date_not_uniform_layer_reference_year']
    elif key=='managedReticulumLength':
        d=n['municipalAreaKm2'];full=n['fullNetworkKm'];managed=n['managedNetworkKm']
        if not finite(d) or d<=0 or not finite(full) or not finite(managed) or not 0<=managed<=full:raise ValueError('territory_invalid_native_components')
        close(r['municipalAreaKm2'],d);close(n['fullNetworkDensity'],full/d,.00000051)
        for field in ('fullNetworkKm','managedNetworkKm'):close(math.fsum(x[field] for x in f['municipalities'].values()),f['versilia'][field],1e-5)
        close(math.fsum(x['municipalAreaKm2'] for x in f['municipalities'].values()),f['versilia']['unionAreaKm2'],1e-5)
        expected=n[{'full':'fullNetworkKm','managed':'managedNetworkKm','density':'fullNetworkDensity'}[v]]
        value=r.get('value') if dimension=='total' else next(p['value'] for p in r['parts'] if p['key']==v)
        if weighted(key,dimension):parts=dict(numerator=full,denominator=d,scale=1)
        notes+=['managed_network_is_subset_do_not_add_to_full','density_native_km_over_own_area_not_resident_weight','native_union_and_municipal_sums_reconciled_at_geometry_rounding_precision']
    else:
        counts=[]
        for c in LAYERS:
            a=n[c];count=a['sourceFeaturesIntersecting']
            if not isinstance(count,int) or count<0 or any(not isinstance(x,int) or x<0 for x in a['types'].values()) or sum(a['types'].values())!=count:raise ValueError('territory_invalid_native_components')
            counts.append(count)
        if sum(counts)!=n['featurePresenceTotal']:raise ValueError('territory_invalid_native_components')
        expected=n['featurePresenceTotal'] if v=='total' else n[v]['sourceFeaturesIntersecting']
        value=r.get('value') if v=='total' else expected
        notes+=['hydraulic_features_cross_municipal_boundaries_no_naive_sum_for_unique_versilia','census_features_are_not_works_projects_or_operational_status','regional_total_is_context_not_comparable_municipal_rate']
    if value is not None:close(value,expected)
    published=value
    if parts and value is not None:value=parts['numerator']/parts['denominator']*parts['scale']
    pointer=f'/metrics/{key}/rows/{index}/value' if dimension=='total' else f'/metrics/{key}/rows/{index}/code' if key=='hydraulicWorksCensusElements' else f'/metrics/{key}/rows/{index}/parts/{next(i for i,p in enumerate(r["parts"]) if p["key"]==v)}/'+('ha' if dimension.startswith('hectares:') else 'value')
    record=('/hydraulicWorks/byTown/' if key=='hydraulicWorksCensusElements' else '/reticulum/municipalities/' if key=='managedReticulumLength' else '/protectedNaturalAreas/municipalities/')+r['town']
    evidence=[dict(kind='catalog_snapshot',path=engine.catalog_path,sha256=engine.catalog_hash,valuePointer=pointer),dict(ref,kind='source_snapshot',recordPointer=record+('/'+v+'/sourceFeaturesIntersecting' if key=='hydraulicWorksCensusElements' and v!='total' else '/featurePresenceTotal' if key=='hydraulicWorksCensusElements' else ''))]
    return dict(ctx,**parts,metric=key,dimension=dimension,geography=r['code'],period=period,value=value,publishedValue=published,source=m['sourceUrl'],provenance=evidence,evidence=evidence,notApplicable=bool(r.get('notApplicable')),dataUnavailable=value is None or bool(r.get('dataUnavailable'))),notes

def benchmark(engine,key,scope,municipal):
    raise ValueError('territory_regional_count_not_comparable' if key=='hydraulicWorksCensusElements' else 'territory_benchmark_not_reviewed')
