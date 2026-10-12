"""Separate frozen fuel statistics; published EV density with unresolved components."""
import calendar
import math
import re
from semantic_query_library_adapters import TOWNS,fingerprint

KEYS=('fuelPrices','evPoints')
PUBLIC_HASHES={'fuelPrices':'0a4f6ada152b6f53fc182dbf028d85406ae0244f7e4c38e47f59fc74dab2e6a4','evPoints':'56bda8706b02b0756b903de6e4216a6c547473de81d4f8e9b25576ea1af2cb0d'}
FILES={'daily':('data/source-snapshots/fuel-history-mimit.json','7f34927e952370836c2ed1a49b73ad543b12518c831630c391cac869a78696ec','b78d6a6d597f81feb87c5c04772eccb46208b4c3a8ca5681904e04a0f3161a8c'),
       'monthly':('data/source-snapshots/fuel-history-mimit-monthly.json','2f8eb340a8a65b5f78c9cbcd8c422483e66a24b54735514177fbe339e068ad3b','973ba78c37341c49db0d013f3065bcc7f06d2eb799a48d09d4f39a89c0fd6c0e')}
FUEL_NOTES=['fuel_snapshot_median_not_monthly_mean_of_daily_medians',
            'fuel_observed_price_not_volume_weighted_or_actual_household_spend',
            'fuel_changing_station_reporting_universe_not_fixed_station_panel',
            'fuel_monthly_days_observed_not_all_calendar_days',
            'fuel_normalized_summary_replay_not_original_csv_tar_or_station_records',
            'fuel_mean_of_municipal_medians_not_versilia_station_median',
            'fuel_stazzema_missing_price_not_zero_or_all_future_absence']
EV_NOTES=['ev_published_rounded_density_only_no_native_point_count_reconstruction',
          'ev_point_connector_station_identity_and_exact_reference_date_unresolved',
          'ev_generic_commuting_caveat_not_ev_reference_evidence',
          'ev_no_power_accessibility_availability_or_charging_quality_inference']


def token(key,period):
    p=str(period)
    if key=='evPoints':
        if p!='2026':raise ValueError('energy_period_not_frozen')
    elif not re.fullmatch(r'\d{4}-\d{2}(?:-\d{2})?',p):raise ValueError('energy_period_not_frozen')
    return p


def order(p):return int(p.replace('-',''))
def dimensions(key):return ['total'] if key=='evPoints' else ['total','fuel:benzina','fuel:gasolio','monthly:benzina','monthly:gasolio']
def resolve(dim):return ('monthly' if dim.startswith('monthly:') else 'daily','gasolio' if dim.endswith(':gasolio') else 'benzina')
def scopes(key,dim):return []
def operations(key,dim):return ['compare','rank']+(['series'] if key=='fuelPrices' else [])


def selection_guard(key,dim,op):
    if op=='series' and key=='evPoints':raise ValueError('energy_ev_history_not_frozen')
    if op in ('absolute_change','relative_change','percentage_points','trend'):raise ValueError('energy_temporal_continuity_not_reviewed')
    if op=='weighted_ratio':raise ValueError('energy_native_pooling_not_reviewed')
    if op=='benchmark_gap':raise ValueError('energy_geographic_benchmark_not_reviewed')
    if op=='anomaly':raise ValueError('energy_peer_anomaly_not_reviewed')
    if op=='correlation':raise ValueError('energy_pair_not_jointly_reviewed')


def context(metric,key,dim):
    if dim not in dimensions(key):raise ValueError('energy_dimension_not_reviewed')
    if fingerprint(metric)!=PUBLIC_HASHES[key]:raise ValueError('energy_public_definition_or_values_changed')
    if key=='evPoints':return dict(unit='per1000',population='published public active charging-point density; point/connector identity not certified from native rows',
        definition='published rounded density per 1000 residents; components not frozen',method='public catalog replay only; exact source and denominator dates unresolved',
        frequency='snapshot_year_only',periodBasis='public year 2026; exact observation and population-reference dates not frozen',
        nativeComponentsAvailable=False,nativeRecordReplayAvailable=False,normalizedRecordReplayAvailable=False,adapter='energy/ev_published_density/v1')
    mode,fuel=resolve(dim)
    return dict(unit='eurliter',population='self-service '+fuel+' reported at active MIMIT municipal stations; changing reporting universe',
        definition='mean of available daily municipal medians' if mode=='monthly' else 'municipal station-price median on selected snapshot date',
        method='frozen three-decimal normalized summary; original station records and archives not replayed',
        frequency='monthly' if mode=='monthly' else 'irregular_snapshot',periodBasis='calendar month with explicit observed days' if mode=='monthly' else 'exact frozen snapshot date',
        nativeComponentsAvailable=False,nativeRecordReplayAvailable=False,normalizedRecordReplayAvailable=True,adapter='energy/fuel/'+mode+'/'+fuel+'/v1')


def validated(engine,mode):
    path,sha,obj=FILES[mode];snap,ref=engine.file(path)
    if ref!=dict(path=path,sha256=sha) or fingerprint(snap)!=obj:raise ValueError('energy_frozen_fuel_input_changed')
    if len(engine._catalog['towns'])!=7 or {t['code']:t['name'] for t in engine._catalog['towns']}!=TOWNS:raise ValueError('energy_municipal_identity_changed')
    points=snap['points'];periods=[p['referenceDate'] for p in points]
    if len(periods)!=len(set(periods)) or periods!=sorted(periods):raise ValueError('energy_fuel_periods_not_reconciled')
    for p in points:
        if set(p['towns'])!=set(TOWNS.values()):raise ValueError('energy_fuel_town_identity_changed')
        for town,r in p['towns'].items():
            for fuel in ['benzina','gasolio']:
                v=r[fuel]
                if v is not None and (type(v) not in (int,float) or not math.isfinite(v) or not .5<=v<=5):raise ValueError('energy_fuel_value_invalid')
                if mode=='monthly':
                    year,month=map(int,p['referenceDate'].split('-'));days=r[fuel+'Days']
                    if (type(days) is not int or not 0<=days<=r['observationDays']<=calendar.monthrange(year,month)[1]
                        or (v is None)!=(days==0)):raise ValueError('energy_fuel_observation_days_invalid')
            if mode=='daily' and (type(r['stations']) is not int or r['stations']<0):raise ValueError('energy_fuel_station_summary_invalid')
    if mode=='daily':
        metric=engine._catalog['metrics']['fuelPrices'];context(metric,'fuelPrices','total')
        for row in metric['rows']:
            town=row['town'];j=len(points)-1
            if row['stationCount']!=points[j]['towns'][town]['stations']:raise ValueError('energy_fuel_public_summary_not_reconciled')
            for fuel,label,k in [('benzina','Benzina self',0),('gasolio','Gasolio self',1)]:
                vals=[p['towns'][town][fuel] for p in points]
                if row['parts'][k]['value']!=vals[-1] or row['componentSeries'][label]!=dict(years=periods,values=vals):raise ValueError('energy_fuel_public_summary_not_reconciled')
                if fuel=='benzina' and (row['value']!=vals[-1] or row['series']!=dict(years=periods,values=vals)):raise ValueError('energy_fuel_public_summary_not_reconciled')
    return snap,ref


def default_period(engine,key,dim):
    if key=='evPoints':return '2026'
    snap,ref=validated(engine,resolve(dim)[0]);return snap['points'][-1]['referenceDate']


def available_periods(engine,key,dim,row):
    snap,ref=validated(engine,resolve(dim)[0]);return [p['referenceDate'] for p in snap['points']]


def observation(engine,key,index,dim,period,historical):
    metric=engine._catalog['metrics'][key];ctx=context(metric,key,dim);row=metric['rows'][index]
    if len(engine._catalog['towns'])!=7 or {t['code']:t['name'] for t in engine._catalog['towns']}!=TOWNS:raise ValueError('energy_municipal_identity_changed')
    base=dict(ctx,metric=key,dimension=dim,geography=row['code'],period=period,source=metric['sourceUrl'],notApplicable=False)
    if key=='evPoints':
        if period!='2026':raise ValueError('energy_period_not_frozen')
        evidence=[dict(kind='catalog_snapshot',path=engine.catalog_path,sha256=engine.catalog_hash,valuePointer=f'/metrics/{key}/rows/{index}/value')]
        return dict(base,value=row['value'],evidence=evidence,provenance=evidence,dataUnavailable=False,missingReason=None),EV_NOTES[:]
    mode,fuel=resolve(dim);snap,ref=validated(engine,mode)
    match=[i for i,p in enumerate(snap['points']) if p['referenceDate']==period]
    if len(match)!=1:raise ValueError('energy_period_not_frozen_for_selected_statistic')
    j=match[0];r=snap['points'][j]['towns'][row['town']];v=r[fuel];path=f'/points/{j}/towns/{row["town"]}/{fuel}'
    evidence=[dict(ref,kind='source_snapshot',valuePointer=path,recordPointer=f'/points/{j}/towns/{row["town"]}',replayScope='normalized municipal summaries; no individual station or original archive replay'),
              dict(kind='catalog_snapshot',path=engine.catalog_path,sha256=engine.catalog_hash,carrierPointer=f'/metrics/{key}/rows/{index}')]
    result=dict(base,value=v,evidence=evidence,provenance=evidence,dataUnavailable=v is None,missingReason='fuel_no_reported_municipal_price' if v is None else None)
    if mode=='monthly':result.update(observationDays=r['observationDays'],fuelObservationDays=r[fuel+'Days'],calendarDays=calendar.monthrange(*map(int,period.split('-')))[1])
    else:result.update(reportedStationCountSummary=r['stations'],stationCountDefinition='maximum of available benzina/gasolio price counts; not certified union of station IDs')
    return result,FUEL_NOTES[:]
