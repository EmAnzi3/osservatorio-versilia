"""Frozen ISPRA stock/flow and UCS cover; definitions and denominators stay separate."""
import math
from semantic_operations import finite

KEYS = ('landUse', 'landUseChange', 'landCoverProfile')
SOIL = 'data/source-snapshots/territorio-v137-official.json'
UCS = 'data/source-snapshots/territorio-ucs-v136.json'
BENCHMARK = 'data/source-snapshots/a3-ispra-soil-benchmark-2024.json'
URL = 'https://www.isprambiente.gov.it/it/attivita/suolo-e-territorio/suolo/il-consumo-di-suolo/i-dati-sul-consumo-di-suolo'
UCS_URL = 'https://dati.toscana.it/dataset/ucs'
UCS_PUBLIC_URL = 'https://www502.regione.toscana.it/geonetwork/srv/api/records/r_toscan:0d4d6640-9a1c-47a4-9a5d-a85cdb36927c'
CATEGORIES = ('artificialized','agricultural','forest_seminatural_total','wetlands','water','forest','seminativi','permanent_crops','seminatural_nonforest','urban_green_cartographic')
YEARS = {'landUse':'2006, 2012, 2015–2024','landUseChange':'2012, 2015–2024','landCoverProfile':'2007–2019'}

def close(actual, expected, tolerance=1e-8):
    if not finite(actual) or not finite(expected) or not math.isclose(actual,expected,rel_tol=0,abs_tol=tolerance):
        raise ValueError('soil_catalog_source_mismatch')

def token(key, period):
    return ('2019' if key=='landCoverProfile' else '2024') if str(period)==YEARS[key] else str(period)

def dimensions(key):
    if key=='landUse':return ['total','view:percent','view:hectares','view:sqmPerResident']
    if key=='landUseChange':return ['total','view:net','view:gross']
    return ['total',*('part:'+k for k in CATEGORIES),*('hectares:'+k for k in CATEGORIES)]

def view(key, dimension):
    if dimension not in dimensions(key):raise ValueError('soil_dimension_not_reviewed')
    if key=='landUse':return 'percent' if dimension=='total' else dimension[5:]
    if key=='landUseChange':return 'net' if dimension=='total' else dimension[5:]
    return 'artificialized' if dimension=='total' else dimension.split(':',1)[1]

def unit(key, dimension):
    v=view(key,dimension)
    return 'hectares' if key=='landUseChange' or v=='hectares' or dimension.startswith('hectares:') else 'sqm_per_resident' if v=='sqmPerResident' else 'percent'

def weighted(key,dimension):
    return key!='landUseChange' and unit(key,dimension)!='hectares'

def scopes(key,dimension):
    return ['tuscany','italy'] if key=='landUse' and unit(key,dimension)=='percent' else []

def context(metric,key,dimension):
    v=view(key,dimension)
    if str(metric['meta'].get('year'))!=YEARS[key] or metric['meta'].get('unit')!=('hectares' if key=='landUseChange' else 'percent') or metric.get('sourceUrl')!=(UCS_PUBLIC_URL if key=='landCoverProfile' else URL):
        raise ValueError('soil_definition_or_reference_changed')
    definition=('UCS '+v+': cartographic cover class; hierarchical details overlap macroclasses' if key=='landCoverProfile' else 'ISPRA frozen '+v+' soil consumption '+('stock' if key=='landUse' else 'increment; endpoint labels do not attest equal observation intervals'))
    return dict(unit=unit(key,dimension),population='municipal cartographic territory; UCS and ISPRA surfaces are not interchangeable',definition=definition,
        method='frozen official edition; native hectares and explicit source denominator',frequency='irregular',
        periodBasis='snapshot year; historical continuity not independently attested' if key!='landUseChange' else 'increment ending at labelled year; historical interval comparability not independently attested',adapter='soil/'+key+'/'+v+'/v1')

def selection_guard(key,operation):
    if operation in ('absolute_change','relative_change','percentage_points','trend'):
        raise ValueError('soil_historical_comparability_not_attested')

def correlation_guard(observations,axis):
    if axis=='periods' and any(o['metric'] in KEYS for o in observations):raise ValueError('soil_historical_comparability_not_attested')

def native(engine,key,row):
    path=UCS if key=='landCoverProfile' else SOIL;snap,ref=engine.file(path)
    if snap.get('schemaVersion')!=(2 if key=='landCoverProfile' else 1):raise ValueError('soil_native_reference_changed')
    family=snap['landCover' if key=='landCoverProfile' else key]
    if set(family['municipalities'])!={r['town'] for r in engine._catalog['metrics'][key]['rows']} or len(engine._catalog['metrics'][key]['rows'])!=7:
        raise ValueError('soil_native_cohort_changed')
    if not any(t['name']==row['town'] and t['code']==row['code'] for t in engine._catalog['towns']):raise ValueError('soil_row_identity_changed')
    if key=='landCoverProfile':
        s=snap['sources']['regioneToscanaUcs']
        if s.get('page')!=UCS_URL or s.get('referenceYears')!=[2007,2010,2013,2016,2019] or s.get('crs')!='EPSG:3003' or s.get('scale')!='1:10000' or s.get('sha256')!='0cc9527546e6220b99632a9cedc2e908d775e729e4e97de00ebb417fadde8a9d' or family.get('valueOrder')!=list(CATEGORIES) or [(x['key'],x['ucs']) for x in family['categoryDefinitions']]!=list(zip(CATEGORIES,('1','2','3','4','5','31','21','22','32+33','141'))):raise ValueError('soil_native_reference_changed')
    elif snap['sources']['ispraSoil'].get('page')!=URL or snap['sources']['ispraSoil'].get('acquisition',{}).get('sha256')!='5cf250383dbb32cfe18d0a6f7181762f5564307b641b14b66aaade0ccb12e23d':
        raise ValueError('soil_native_reference_changed')
    return family,family['municipalities'][row['town']],ref

def available_periods(engine,key,dimension,row):
    family,n,ref=native(engine,key,row);v=view(key,dimension)
    years=[str(y) for y in family['years']]
    expected=[2007,2010,2013,2016,2019] if key=='landCoverProfile' else [2006,2012,*range(2015,2025)] if key=='landUse' else [2012,*range(2015,2025)]
    if years!=list(map(str,expected)):raise ValueError('soil_native_periods_changed')
    if set(n['rows'])!=set(years):raise ValueError('soil_native_periods_changed')
    if key=='landUse' and v=='sqmPerResident':years=[y for y in years if n['rows'][y]['sqmPerResident'] is not None]
    series=row['coverSeries'][v] if key=='landCoverProfile' else row['seriesByView'][v]
    if list(map(str,series['years']))!=years:raise ValueError('soil_public_periods_changed')
    return years

def observation(engine,key,index,dimension,period,historical):
    metric=engine._catalog['metrics'][key];row=metric['rows'][index];ctx=context(metric,key,dimension);v=view(key,dimension)
    years=available_periods(engine,key,dimension,row)
    if period not in years:raise ValueError('soil_period_not_frozen')
    family,n,ref=native(engine,key,row);i=years.index(period);parts={};notes=['soil_history_readable_comparability_not_attested','soil_ispra_consumption_ucs_cover_and_cfi_forest_are_distinct']
    if key=='landCoverProfile':
        d=n['totalHa'];values=n['rows'][period]
        if not finite(d) or d<=0 or len(values)!=len(CATEGORIES) or any(not finite(x) or x<0 or x>d for x in values):raise ValueError('soil_invalid_native_components')
        close(math.fsum(values[:5]),d,1e-5)
        for child,parent in [('forest','forest_seminatural_total'),('seminatural_nonforest','forest_seminatural_total'),('seminativi','agricultural'),('permanent_crops','agricultural'),('urban_green_cartographic','artificialized')]:
            if values[CATEGORIES.index(child)]>values[CATEGORIES.index(parent)]:raise ValueError('soil_category_hierarchy_changed')
        h=values[CATEGORIES.index(v)];hectares=dimension.startswith('hectares:');expected=h if hectares else h/d*100
        field='ha' if hectares else 'pct';series=row['coverSeries'][v];value=series[field][i];close(row['totalHa'][period],d)
        if not hectares:parts=dict(numerator=h,denominator=d,scale=100)
        notes+=['ucs_detail_classes_overlap_macroclasses_do_not_sum','ucs_total_surface_not_istat_or_ispra_municipal_surface']
        pointer=f'/metrics/{key}/rows/{index}/coverSeries/{v}/{field}/{i}'
    else:
        r=n['rows'][period];series=row['seriesByView'][v];value=series['values'][i]
        pointer=f'/metrics/{key}/rows/{index}/seriesByView/{v}/values/{i}'
        if key=='landUse':
            d=n['municipalAreaHa'];h=r['consumedHa']
            if not finite(d) or d<=0 or not finite(h) or not 0<=h<=d:raise ValueError('soil_invalid_native_components')
            close(row['municipalAreaHa'],d);close(r['consumedPct'],h/d*100,.00050001)
            expected=r[{'percent':'consumedPct','hectares':'consumedHa','sqmPerResident':'sqmPerResident'}[v]]
            if v=='percent':parts=dict(numerator=h,denominator=d,scale=100)
            if v=='sqmPerResident':
                p=r['population']
                if not finite(p) or p<=0:raise ValueError('soil_invalid_native_components')
                close(expected,h*10000/p,.00000051);parts=dict(numerator=h*10000,denominator=p,scale=1)
                notes+=['soil_resident_denominator_from_ispra_same_year_not_current_posas']
            notes+=['soil_published_percent_three_decimals_native_pooled_ratio_may_differ']
        else:
            expected=r['grossHa' if v=='gross' else 'netHa']
            if not finite(r['grossHa']) or r['grossHa']<0 or not finite(r['netHa']) or r['netHa']>r['grossHa']+1e-8:raise ValueError('soil_invalid_native_components')
            notes+=['soil_net_can_be_negative_not_a_certified_restoration_effect','soil_flow_not_difference_of_rounded_stocks_or_annualized_irregular_intervals']
    if value is not None:close(value,expected)
    if not historical and dimension=='total' and row.get('value') is None:value=None
    if period==token(key,YEARS[key]):
        fieldvalue=row.get('value') if dimension=='total' else next((p['value'] for p in row['parts'] if p['key']==v),None) if not dimension.startswith('hectares:') else next((p['ha'] for p in row['parts'] if p['key']==v),value)
        if fieldvalue is not None:close(fieldvalue,expected)
    published=value
    if key=='landUse' and parts and value is not None:value=parts['numerator']/parts['denominator']*parts['scale']
    provenance=[dict(kind='catalog_snapshot',path=engine.catalog_path,sha256=engine.catalog_hash,valuePointer=pointer),dict(ref,kind='source_snapshot',recordPointer=('/landCover' if key=='landCoverProfile' else '/'+key)+'/municipalities/'+row['town']+'/rows/'+period)]
    return dict(ctx,**parts,metric=key,dimension=dimension,geography=row['code'],period=period,value=value,publishedValue=published,source=metric['sourceUrl'],provenance=provenance,evidence=provenance,notApplicable=bool(row.get('notApplicable')),dataUnavailable=value is None or bool(row.get('dataUnavailable'))),notes

def benchmark(engine,key,scope,municipal):
    if scope not in scopes(key,municipal['dimension']) or municipal['period']!='2024':raise ValueError('soil_benchmark_dimension_or_scope_not_reviewed')
    snap,ref=engine.file(BENCHMARK);b=snap['benchmarks'][key];gate=snap.get('qualityGate',{})
    if snap.get('schemaVersion')!=2 or snap.get('sourceProfileId')!='ispra-consumo-suolo-2024' or snap.get('sourceUrl')!=URL or gate.get('status')!='PASS' or gate.get('errors') or gate.get('publicReconciliation')!='2 metrics × 7/7 PASS' or b.get('unit')!='percent' or b.get('year')!='2024' or b.get('formula')!='suolo consumato / superficie territoriale × 100':raise ValueError('soil_benchmark_gate_changed')
    meta=engine._catalog['metrics'][key]['meta']['benchmark']
    if meta.get('sourceSnapshot')!=BENCHMARK or str(meta.get('year'))!='2024' or meta.get('url')!=URL:raise ValueError('soil_benchmark_reference_changed')
    value=b[scope];close(meta[scope],value)
    if not 0<=value<=100:raise ValueError('soil_invalid_native_components')
    evidence=[dict(ref,kind='benchmark_snapshot',valuePointer=f'/benchmarks/{key}/{scope}')]
    return dict({k:municipal[k] for k in ('metric','dimension','unit','population','definition','method','frequency','periodBasis','adapter','period')},geography=scope,value=value,source=URL,evidence=evidence,provenance=evidence,notApplicable=False,dataUnavailable=False)
