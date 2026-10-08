"""Frozen agriculture census carriers; localized land and farm-center scopes differ."""
import math
from semantic_operations import finite

SNAPSHOT = 'data/source-snapshots/istat-agricoltura-territorio-2020.json'
BENCHMARK = 'data/source-snapshots/a3-istat-agriculture-benchmark-2020.json'
SOURCE = 'https://www.istat.it/statistiche-per-temi/censimenti/agricoltura/7-censimento-generale/risultati/'
KEYS = ('agriculturalFarms','agriculturalUsedArea','averageAgriculturalFarmSize','cropProfile','irrigatedAgriculturalArea')
CROPS = ('ARLAND','OLIVOOILTR','OLIVTTR','VINEY','PGRAPM')
UNITS = dict(zip(KEYS,('number','hectares','hectaresPerFarm','hectares','hectares')))
FLOWS = {'farmsAndAreas':'DF_DCAT_CENSAGRIC2020_SURF_ALL','localizedCrops':'DF_DCAT_CENSAGRIC2020_UA_CROPS_2','irrigation':'DF_DCAT_CENSAGRIC2020_SURF_IRR_CONS'}


def close(value, expected):
    if value is None and expected is None:return
    if not finite(value) or not finite(expected) or not math.isclose(value,expected,rel_tol=0,abs_tol=1e-8):
        raise ValueError('agriculture_source_or_component_mismatch')


def dimensions(key):
    if key=='cropProfile':return ['total',*('part:'+c for c in CROPS)]
    return ['total','view:normalized'] if key in ('agriculturalUsedArea','irrigatedAgriculturalArea') else ['total']


def weighted(key, dimension):
    return key=='averageAgriculturalFarmSize' or (key in ('agriculturalUsedArea','irrigatedAgriculturalArea') and dimension=='view:normalized')


def scopes(key, dimension):
    return ['tuscany','italy'] if key=='averageAgriculturalFarmSize' and dimension=='total' else []


def context(metric,key,dimension):
    if dimension not in dimensions(key):raise ValueError('agriculture_dimension_not_reviewed')
    if metric['meta'].get('unit')!=UNITS[key] or str(metric['meta'].get('year'))!='2020' or metric.get('sourceUrl')!=SOURCE or metric.get('method',{}).get('snapshot')!=SNAPSHOT:
        raise ValueError('agriculture_definition_or_reference_changed')
    normalized=dimension=='view:normalized'
    if normalized and metric['meta'].get('normalized',{}).get('unit')!='percent':raise ValueError('agriculture_normalization_changed')
    localized=key in ('agriculturalUsedArea','cropProfile')
    definition={'agriculturalFarms':'HO: farms by farm center; not farms with SAU',
                'agriculturalUsedArea':'ARU/ALL/TOT: physically localized agricultural area'+(' / municipal area 2020 * 100' if normalized else ' in hectares'),
                'averageAgriculturalFarmSize':'farm-center SAU / farms with SAU (FUAA), not all farms (HO)',
                'cropProfile':'physically localized '+('all SAU' if dimension=='total' else dimension[5:])+' area; selected categories do not exhaust SAU',
                'irrigatedAgriculturalArea':'area irrigated at least once, attributed by farm center'+(' / farm-center SAU * 100' if normalized else ' in hectares')}[key]
    return dict(unit='percent' if normalized else UNITS[key],population='physically localized agricultural land' if localized else 'agricultural holdings attributed by farm center',definition=definition,
                method='Istat frozen agriculture census 2020; native components with published precision',frequency='irregular',periodBasis='agricultural year 2019/2020; municipal area December 31 2020 when used',adapter='agriculture/'+key+'/v1')


def native(engine):
    snap,ref=engine.file(SNAPSHOT)
    if snap.get('schemaVersion')!=1 or snap.get('referenceYear')!=2020 or snap.get('cropReference')!='annata agraria 2019/2020':raise ValueError('agriculture_snapshot_reference_changed')
    for group,flow in FLOWS.items():
        if snap['sources'][group].get('flow')!=flow:raise ValueError('agriculture_source_flow_changed')
    if snap['sources']['farmsAndAreas'].get('perspective')!='centro aziendale' or snap['sources']['irrigation'].get('perspective')!='centro aziendale' or snap['sources']['localizedCrops'].get('perspective')!='Comune di localizzazione dei terreni' or snap['sources']['municipalArea'].get('referenceDate')!='2020-12-31':raise ValueError('agriculture_geographic_scope_changed')
    if set(snap['towns'])!=set(engine.codes):raise ValueError('agriculture_native_cohort_changed')
    return snap,ref


def observation(engine,key,index,dimension,period,historical):
    if period!='2020':raise ValueError('agriculture_period_not_frozen')
    metric=engine._catalog['metrics'][key];row=metric['rows'][index];ctx=context(metric,key,dimension);snap,ref=native(engine)
    r=snap['towns'][row['code']]
    if r['name']!=row['town'] or str(row.get('year'))!='2020':raise ValueError('agriculture_row_identity_changed')
    for k in ('farms','farmsWithSau'):
        if type(r[k]) is not int or r[k]<0:raise ValueError('agriculture_invalid_native_count')
    if r['farmsWithSau']>r['farms']:raise ValueError('agriculture_invalid_native_count')
    for k in ('sauCenterHa','sauLocalizedHa','municipalAreaKm2','irrigatedAreaHa'):
        if not finite(r[k]) or r[k]<0:raise ValueError('agriculture_invalid_native_area')
    if r['irrigatedAreaHa']>r['sauCenterHa']:raise ValueError('agriculture_irrigated_area_exceeds_center_sau')
    value=row.get('value');pointer=f'/metrics/{key}/rows/{index}/value';parts={};field={'agriculturalFarms':'farms','agriculturalUsedArea':'sauLocalizedHa','cropProfile':'sauLocalizedHa','irrigatedAgriculturalArea':'irrigatedAreaHa'}.get(key)
    expected=r[field] if field else None
    record_pointer=f'/towns/{row["code"]}'
    if key=='cropProfile' and dimension!='total':
        crop=dimension[5:];matches=[(i,p) for i,p in enumerate(row['parts']) if p['key']==crop]
        if len(matches)!=1 or matches[0][1].get('unit')!='hectares':raise ValueError('agriculture_crop_identity_changed')
        j,p=matches[0];value=p.get('value');pointer=f'/metrics/{key}/rows/{index}/parts/{j}/value';expected=r['cropsHa'][crop];record_pointer+='/cropsHa/'+crop
        if expected is not None and (not finite(expected) or expected<0 or expected>r['sauLocalizedHa']):raise ValueError('agriculture_invalid_native_area')
    if key=='averageAgriculturalFarmSize' or dimension=='view:normalized':
        n,d,scale=(r['sauCenterHa'],r['farmsWithSau'],1) if key=='averageAgriculturalFarmSize' else (r['sauLocalizedHa'],r['municipalAreaKm2']*100,100) if key=='agriculturalUsedArea' else (r['irrigatedAreaHa'],r['sauCenterHa'],100)
        if d<=0:raise ValueError('agriculture_positive_denominator_required')
        parts=dict(numerator=n,denominator=d,scale=scale,numeratorPeriod='2020',denominatorPeriod='2020');expected=n/d*scale
        if dimension=='view:normalized':
            value=row['normalized'].get('value');pointer=f'/metrics/{key}/rows/{index}/normalized/value'
            if row['normalized'].get('unit')!='percent' or str(row['normalized'].get('year'))!='2020':raise ValueError('agriculture_normalization_changed')
        components=row.get('sourceBackedComponents')
        if components is not None:
            if components.get('sourceSnapshot')!=SNAPSHOT or str(components.get('referenceYear'))!='2020' or components.get('transform')!='ratio':raise ValueError('agriculture_component_reference_changed')
            for name,expected_part in [('numerator',n),('denominator',d),('scale',scale)]:close(components.get(name),expected_part)
    if value is not None:close(value,expected)
    evidence=[dict(kind='catalog_snapshot',path=engine.catalog_path,sha256=engine.catalog_hash,valuePointer=pointer,periodPointer=f'/metrics/{key}/meta/year'),dict(ref,kind='source_snapshot',recordPointer=record_pointer,sources=snap['sources'])]
    notes=['agriculture_census_2020_not_current_2026_conditions','farm_center_attribution_not_physical_location_of_all_land','pooled_farm_center_land_may_extend_outside_selected_municipalities','selected_crop_categories_not_exhaustive_partition','agriculture_not_productivity_income_water_volume_or_policy_effect']
    if key=='averageAgriculturalFarmSize':notes.append('farm_size_denominator_farms_with_sau_not_all_farms')
    if key=='cropProfile':notes.append('absent_crop_rows_are_missing_not_zero')
    return dict(ctx,**parts,metric=key,dimension=dimension,geography=row['code'],period='2020',value=value,source=SOURCE,evidence=evidence,provenance=evidence,agricultureScope='localized_land' if key in ('agriculturalUsedArea','cropProfile') else 'farm_center',notApplicable=bool(row.get('notApplicable')),dataUnavailable=value is None or bool(row.get('dataUnavailable'))),notes


def correlation_guard(observations):
    scopes_={o['agricultureScope'] for o in observations if 'agricultureScope' in o}
    if len(scopes_)>1:raise ValueError('agriculture_localized_and_center_scopes_not_jointly_comparable')


def benchmark(engine,key,scope,municipal):
    if scope not in scopes(key,municipal['dimension']):raise ValueError('agriculture_benchmark_extent_or_normalization_not_comparable')
    snap,ref=engine.file(BENCHMARK)
    if snap.get('sourceProfileId')!='istat-agriculture-census-2020' or snap.get('sourceUrl')!=SOURCE or snap.get('qualityGate',{}).get('status')!='PASS' or snap['qualityGate'].get('errors'):raise ValueError('agriculture_benchmark_gate_changed')
    entry=snap['benchmarks'][key];raw=snap['components'][scope]
    if str(entry['year'])!='2020' or entry['unit']!='hectaresPerFarm':raise ValueError('agriculture_benchmark_definition_changed')
    n,d=raw['sauCenterHa'],raw['farmsWithSau']
    if not finite(n) or n<0 or type(d) is not int or d<=0 or d>raw['farms']:raise ValueError('agriculture_invalid_benchmark_components')
    value=n/d;close(entry[scope],value);meta=engine._catalog['metrics'][key]['meta']['benchmark']
    if meta.get('sourceSnapshot')!=BENCHMARK or str(meta.get('year'))!='2020' or meta.get('url')!=SOURCE:raise ValueError('agriculture_benchmark_reference_changed')
    close(meta.get(scope),value);evidence=[dict(ref,kind='benchmark_snapshot',valuePointer=f'/benchmarks/{key}/{scope}',recordPointer=f'/components/{scope}',sourceUrl=SOURCE)]
    return dict({k:municipal[k] for k in ('metric','dimension','unit','population','definition','method','frequency','periodBasis','adapter','period')},geography=scope,value=value,numerator=n,denominator=d,scale=1,source=SOURCE,evidence=evidence,provenance=evidence,notApplicable=False,dataUnavailable=False)
