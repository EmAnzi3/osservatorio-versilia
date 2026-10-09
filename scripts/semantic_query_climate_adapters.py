"""Read-only external climate series; annual values and fitted changes are distinct."""
import hashlib,json,math,re
from semantic_operations import finite

KEYS=('climateTemperatureTrend50y','climatePrecipitationTrend50y','climateTminTrend','climateTmaxTrend')
FIELDS=('temperature','precipitation','tmin','tmax')
ANNUAL='data/meteo-clima-poc.json'
MINMAX='data/meteo-clima-minmax-poc.json'
UI='assets/climate-ux-v3.js'
UI_SHA='a40e61ecb05e2daa9f4e5647885016bdba507964c8a42e56af3cd5272edc0626'
HASHES={ANNUAL:('2c9c340ae557c25f708f77d8f5411b71d5a409f4cfe6f55b626b614a790b62c9','cf9a11dcb95d5d23d5fed8b5bf83079b02299b32f916b0cbd2a82f87224fde0f'),MINMAX:('50be932eea3e96352e0c8403fce7a944782071c87bbf04c4a75e69143f8e23c2','446776257b92b2fe344a5395da3e9d1e2d15fc0973b08e8c9091deedad978eeb')}
TREND='trend:1975-2025'
PERCENT='trend_percent:1975-2025'

def path(key):return ANNUAL if key in KEYS[:2] else MINMAX
def field(key):return FIELDS[KEYS.index(key)]
def token(key,period):
    p=str(period).replace('–','-')
    if p!='1975-2025' and not re.fullmatch(r'[0-9]{4}',p):raise ValueError('climate_period_token_not_reviewed')
    return p
def dimensions(key):return ['total',TREND,*([PERCENT] if key==KEYS[1] else [])]
def default_period(dim):return '2025' if dim=='total' else '1975-2025'
def operations(key,dim):
    return ['compare','rank',*(['series'] if dim=='total' else []),*(['absolute_change','trend'] if dim=='total' and key in KEYS[2:] else [])]
def selection_guard(key,dim,op):
    if op=='relative_change':raise ValueError('climate_relative_change_not_reviewed_celsius_not_ratio_scale')
    if op in ('absolute_change','trend') and dim=='total' and key in KEYS[:2]:raise ValueError('climate_stitched_sources_no_arbitrary_temporal_change')
    if op in ('series','absolute_change','trend','percentage_points') and dim!='total':raise ValueError('climate_fitted_window_is_not_annual_series')
    reasons={'weighted_ratio':'climate_no_native_spatial_components_for_pooling','benchmark_gap':'climate_normals_are_temporal_not_geographic_benchmarks','anomaly':'climate_peer_anomaly_not_reviewed','correlation':'climate_pair_not_jointly_reviewed','percentage_points':'climate_annual_values_not_percentages'}
    if op in reasons:raise ValueError(reasons[op])

def context(m,key,dim):
    if dim not in dimensions(key):raise ValueError('climate_dimension_not_reviewed')
    expected=dict(type='external-climate',builder='annual-trend' if key in KEYS[:2] else 'minmax-trend',path=path(key),seriesKey=field(key),trendFrom=1975,trendTo=2025,decimals=1 if key==KEYS[1] else 3,normalizedPercent=key==KEYS[1])
    if m.get('dataStorage')!=expected or m.get('rows')!=[] or m['meta'].get('unit')!=('climateMm' if key==KEYS[1] else 'climateCelsius') or token(key,m['meta']['year'])!='1975-2025' or m.get('sourceUrl')!='https://dati.lamma.toscana.it/':raise ValueError('climate_external_catalog_contract_changed')
    unit='mm' if key==KEYS[1] else 'celsius'
    native_method='LaMMA 1995-2015 with calibrated ERA5-Land outside overlap; frozen reconstruction, raw calibration not replayed' if key in KEYS[:2] else 'continuous ERA5-Land hourly 1975-2025; daily extrema from 24 UTC samples, one constant municipal LaMMA 2011-2015 level offset; no slope correction'
    definition={'temperature':'municipal territorial annual mean temperature','precipitation':'municipal territorial annual precipitation total in mm, not municipal total water volume','tmin':'annual mean of daily territorial minima; not lowest annual extreme','tmax':'annual mean of daily territorial maxima; not highest annual extreme'}[field(key)]
    if dim!= 'total':definition=('OLS fitted 2025 minus fitted 1975, not observed endpoint difference' if dim==TREND else 'OLS fitted change / positive fitted 1975 precipitation * 100; not annual observed change')+'; '+definition
    return dict(unit='percent' if dim==PERCENT else unit,population='municipal territory, fractionally weighted raster cells on Istat 2026 boundaries; not station observations or resident exposure',definition=definition,method=native_method,frequency='annual' if dim=='total' else 'fixed_fitted_window',periodBasis='complete calendar years; latest 2025' if dim=='total' else '51 annual observations 1975-2025, 50-year fitted change',adapter='climate/'+field(key)+'/'+dim+'/v1')

def native(engine,key):
    p=path(key)
    if p in getattr(engine,'_climate_validation',{}):return engine._climate_validation[p]
    s,ref=engine.file(p)
    if ref['sha256']!=HASHES[p][0] or hashlib.sha256(json.dumps(s,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()!=HASHES[p][1]:raise ValueError('climate_frozen_series_changed')
    if hashlib.sha256((engine.root/UI).read_bytes()).hexdigest()!=UI_SHA:raise ValueError('climate_public_runtime_definition_changed')
    names=[t['name'] for t in engine._catalog['towns']];codes=[t['code'] for t in engine._catalog['towns']]
    if len(names)!=7 or len(set(names))!=7 or len(set(codes))!=7 or set(names)!=set(s['municipalities']):raise ValueError('climate_native_cohort_changed')
    start=1950 if p==ANNUAL else 1975
    for n in s['municipalities'].values():
        if n['years']!=list(range(start,2026)):raise ValueError('climate_incomplete_or_duplicate_annual_axis')
        for f in (FIELDS[:2] if p==ANNUAL else FIELDS[2:]):
            if len(n[f])!=len(n['years']) or any(not finite(v) or (f=='precipitation' and v<0) for v in n[f]):raise ValueError('climate_invalid_annual_values')
    if not hasattr(engine,'_climate_validation'):engine._climate_validation={}
    engine._climate_validation[p]=(s,ref)
    return s,ref

def rows(engine,key):
    return [dict(town=t['name'],code=t['code']) for t in engine._catalog['towns']]
def available_periods(engine,key,dim,row=None):
    if dim!='total':raise ValueError('climate_fitted_window_is_not_annual_series')
    s,_=native(engine,key);return list(map(str,s['municipalities'][row['town']]['years']))

def fitted(years,values):
    pairs=[(y,v) for y,v in zip(years,values) if 1975<=y<=2025]
    if len(pairs)!=51:raise ValueError('climate_full_fitted_window_required')
    average=math.fsum(v for _,v in pairs)/51
    slope=math.fsum((y-2000)*v for y,v in pairs)/math.fsum((y-2000)**2 for y,_ in pairs)
    start=average-slope*25;end=average+slope*25
    return dict(n=51,slope=slope,fittedStart=start,fittedEnd=end,fittedChange=slope*50,windowStart='1975',windowEnd='2025')

def observation(engine,key,index,dim,period,historical):
    m=engine._catalog['metrics'][key];ctx=context(m,key,dim);s,ref=native(engine,key);r=rows(engine,key)[index];n=s['municipalities'][r['town']];f=field(key)
    base='/municipalities/'+r['town']
    components={}
    if dim=='total':
        if not period.isdigit() or int(period) not in n['years']:raise ValueError('climate_annual_period_not_frozen')
        i=n['years'].index(int(period));value=n[f][i];pointer=base+'/'+f+'/'+str(i)
    else:
        if period!='1975-2025':raise ValueError('climate_fitted_window_period_required')
        components=fitted(n['years'],n[f]);value=components['fittedChange'];pointer=base+'/'+f
        if dim==PERCENT:
            if components['fittedStart']<=0:raise ValueError('climate_positive_fitted_precipitation_reference_required')
            value=value/components['fittedStart']*100
    evidence=[dict(ref,kind='source_snapshot',valuePointer=pointer,recordPointer=base+'/years'),dict(kind='catalog_snapshot',path=engine.catalog_path,sha256=engine.catalog_hash,valuePointer='/metrics/'+key+'/dataStorage'),dict(kind='runtime_definition',path=UI,sha256=UI_SHA,record='configs and rowsFor: annual 2025 separate from fitted trend')]
    warnings=['climate_frozen_reconstruction_not_live_or_station_record','climate_legacy_catalog_label_not_primary_annual_definition','climate_raw_grids_calibration_validation_not_replayed','climate_no_areal_or_population_pooled_average','climate_ols_descriptive_no_significance_forecast_or_causality','climate_draft_named_input_already_used_by_public_runtime']
    warnings+=['climate_stitched_observations_and_calibrated_reanalysis'] if key in KEYS[:2] else ['climate_minmax_continuous_era5_not_legacy_lamma_stitch','climate_daily_extrema_24_utc_samples_not_annual_record']
    return dict(ctx,**components,metric=key,dimension=dim,geography=r['code'],period=period,value=value,source='https://dati.lamma.toscana.it/' if key in KEYS[:2] else 'https://cds.climate.copernicus.eu/',evidence=evidence,provenance=evidence,notApplicable=False,dataUnavailable=False),warnings
