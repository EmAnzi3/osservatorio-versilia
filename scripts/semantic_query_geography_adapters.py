"""Reviewed geography and forest snapshots; observation and publication dates differ."""
import math
from semantic_operations import finite

KEYS = ('municipalSurface', 'populationDensity', 'altitudeProfile', 'forestCoverIndex')
GEO = 'data/source-snapshots/biometria-comune-v135.json'
FOREST = 'data/source-snapshots/foreste-in-comune-v136.json'
BENCHMARK = 'data/source-snapshots/a3-istat-geography-benchmark-2021.json'
POP_BENCHMARK = 'data/source-snapshots/a3-istat-demography-benchmark-2026.json'
SOURCE = 'https://www.istat.it/classificazione/principali-statistiche-geografiche-sui-comuni/'
FOREST_SOURCE = 'https://uncem.it/il-rapporto-foreste-in-comune-presentato-a-marcetelli-con-pefc-uncem-legambiente-caire/'
BANDS = ('0_299','300_599','600_899','900_1199','1200_1499','1500_1999','2000_2499','2500_plus')
YEARS = dict(zip(KEYS, ('31 dicembre 2021','2026','31 dicembre 2021','CFI 2020 · aggiornamento 2024')))
UNITS = dict(zip(KEYS, ('squareKm','peoplePerSquareKm','percent','percent')))

def close(value, expected, tolerance=1e-8):
    if not finite(value) or not finite(expected) or not math.isclose(value,expected,rel_tol=0,abs_tol=tolerance):
        raise ValueError('geography_source_or_component_mismatch')

def token(key, period):
    period = str(period)
    return ('2020-2024' if key=='forestCoverIndex' else '2026' if key=='populationDensity' else '2021') if period==YEARS[key] else period

def dimensions(key):
    if key=='altitudeProfile':return ['total',*('part:'+b for b in BANDS),'stat:min','stat:mean','stat:max']
    return ['total','view:hectares'] if key=='forestCoverIndex' else ['total']

def weighted(key, dimension):
    return key=='populationDensity' or (key=='forestCoverIndex' and dimension=='total')

def scopes(key, dimension):
    return ['tuscany','italy'] if key!='forestCoverIndex' and dimension=='total' else []

def context(metric,key,dimension):
    if dimension not in dimensions(key):raise ValueError('geography_dimension_not_reviewed')
    if metric['meta'].get('unit')!=UNITS[key] or str(metric['meta'].get('year'))!=YEARS[key] or metric.get('sourceUrl')!=(FOREST_SOURCE if key=='forestCoverIndex' else SOURCE):
        raise ValueError('geography_definition_or_reference_changed')
    unit='meters' if dimension.startswith('stat:') else 'hectares' if dimension=='view:hectares' else UNITS[key]
    definition = {'municipalSurface':'official municipal area in km2, December 31 2021',
        'populationDensity':'canonical resident stock January 1 2026 / municipal area December 31 2021',
        'altitudeProfile':'official municipal altitude distribution; rounded share >=300 m' if dimension=='total' else 'official altitude band '+dimension[5:] if dimension.startswith('part:') else 'official municipal altitude '+dimension[5:]+' in meters',
        'forestCoverIndex':'CFI nominal 2020 updated through 2024; forest area in hectares' if dimension=='view:hectares' else 'forest area / municipal area * 100 from frozen hectares; published index retained separately at three decimals'}[key]
    return dict(unit=unit,population='municipal territory' if key!='populationDensity' else 'resident population January 1 2026 over municipal territory 2021',definition=definition,
        method='frozen official municipal snapshot; published precision preserved',frequency='irregular',periodBasis=definition,adapter='geography/'+key+'/v1')

def observation(engine,key,index,dimension,period,historical):
    if period!=token(key,YEARS[key]):raise ValueError('geography_period_not_frozen')
    metric=engine._catalog['metrics'][key];row=metric['rows'][index];ctx=context(metric,key,dimension)
    if not any(t['code']==row['code'] and t['name']==row['town'] for t in engine._catalog['towns']):raise ValueError('geography_row_identity_changed')
    path=FOREST if key=='forestCoverIndex' else GEO;snap,ref=engine.file(path)
    if set(snap['municipalities'])!={r['town'] for r in metric['rows']} or len(metric['rows'])!=7:raise ValueError('geography_native_cohort_changed')
    native=snap['municipalities'][row['town']];parts={};pointer=f'/metrics/{key}/rows/{index}/value';value=row.get('value')
    evidence=[dict(ref,kind='source_snapshot',recordPointer='/municipalities/'+row['town'])]
    if key=='forestCoverIndex':
        if snap.get('schemaVersion')!=1 or snap['reference'].get('forestMapNominalYear')!=2020 or snap['reference'].get('forestMapUpdatedThrough')!=2024 or snap.get('publication')!='giugno 2026' or native.get('istatCode')!=row['code']:
            raise ValueError('forest_reference_changed')
        n,d=native['forestAreaHa'],native['municipalityAreaHa']
        if not finite(n) or not finite(d) or d<=0 or n<0 or n>d:raise ValueError('geography_invalid_native_components')
        geo,geo_ref=engine.file(GEO)
        if geo.get('referenceDate')!='2021-12-31':raise ValueError('geography_native_reference_changed')
        close(d,geo['municipalities'][row['town']]['surfaceKm2']*100)
        evidence.append(dict(geo_ref,kind='area_reference_snapshot',recordPointer='/municipalities/'+row['town']))
        close(native['forestCoverPct'],n/d*100,.00050001)
        for field in ('forestAreaHa','municipalityAreaHa','forestCoverPct'):close(row.get(field),native[field])
        expected=native['forestCoverPct']
        if dimension=='view:hectares':value=row.get('forestAreaHa');expected=n;pointer=f'/metrics/{key}/rows/{index}/forestAreaHa'
        else:parts=dict(numerator=n,denominator=d,scale=100,numeratorPeriod='2020-2024',denominatorPeriod='2021')
    else:
        if snap.get('schemaVersion')!=2 or snap.get('referenceDate')!='2021-12-31' or snap.get('status')!='verified-istat-2021-xlsx' or snap['source'].get('page')!=SOURCE:raise ValueError('geography_native_reference_changed')
        area=native['surfaceKm2']
        if not finite(area) or area<=0:raise ValueError('geography_invalid_native_components')
        expected=area
        if key=='populationDensity':
            popmetric=engine._catalog['metrics']['population']
            if str(popmetric['meta'].get('year'))!='2026':raise ValueError('density_population_period_changed')
            matches=[(i,r) for i,r in enumerate(popmetric['rows']) if r['code']==row['code'] and r['town']==row['town']]
            if len(matches)!=1:raise ValueError('density_population_identity_changed')
            pi,pr=matches[0];pop,notes=engine.observation('population',pi,'2026',historical=False)
            if not finite(pop['value']) or pop['value']<0:raise ValueError('density_population_missing')
            n=pop['value'];close(row.get('populationBase'),n);close(row.get('surfaceKm2'),area)
            expected=n/area;parts=dict(numerator=n,denominator=area,scale=1,numeratorPeriod='2026',denominatorPeriod='2021');evidence+=pop['provenance']
        elif key=='altitudeProfile':
            bandvalues=native['altitudeBandsPct']
            if set(bandvalues)!=set(BANDS) or any(not finite(v) or v<0 or v>100 for v in bandvalues.values()) or abs(math.fsum(bandvalues.values())-100)>.0005:raise ValueError('altitude_partition_changed')
            close(native['from300Pct'],round(math.fsum(bandvalues[b] for b in BANDS[1:]),1))
            stats=[native['altitudeMinM'],native['altitudeMeanM'],native['altitudeMaxM']]
            if not all(finite(v) for v in stats) or not stats[0]<=stats[1]<=stats[2] or native.get('altitudeStatus')!='verified-istat-2021-xlsx':raise ValueError('altitude_statistics_changed')
            expected=native['from300Pct']
            if dimension.startswith('part:'):
                b=dimension[5:];matches=[(i,p) for i,p in enumerate(row['parts']) if p['key']==b]
                if len(matches)!=1 or matches[0][1].get('unit')!='percent':raise ValueError('altitude_part_changed')
                i,p=matches[0];value=p.get('value');expected=bandvalues[b];pointer=f'/metrics/{key}/rows/{index}/parts/{i}/value'
            elif dimension.startswith('stat:'):
                name=dimension[5:];field={'min':'altitudeMinM','mean':'altitudeMeanM','max':'altitudeMaxM'}[name];value=row['altitudeStats'].get(name+'M');expected=native[field];pointer=f'/metrics/{key}/rows/{index}/altitudeStats/{name}M'
                if row['altitudeStats'].get('status')!='verified-istat-2021-xlsx':raise ValueError('altitude_statistics_changed')
    if value is not None:close(value,expected)
    published=value
    if key=='forestCoverIndex' and dimension=='total' and value is not None:value=parts['numerator']/parts['denominator']*100
    evidence.insert(0,dict(kind='catalog_snapshot',path=engine.catalog_path,sha256=engine.catalog_hash,valuePointer=pointer,periodPointer=f'/metrics/{key}/meta/year'))
    notes=['geography_single_snapshot_not_current_year_or_temporal_change','geography_shared_area_denominators_are_not_independent_effects']
    if key=='populationDensity':notes+=['density_population_2026_surface_2021_reviewed_mixed_reference','density_not_daily_presence_or_service_demand']
    if key=='altitudeProfile':notes+=['altitude_summary_rounded_one_decimal_bands_four_decimals','altitude_percentage_components_not_native_hectares_no_weighted_ratio']
    if key=='forestCoverIndex':notes+=['forest_map_nominal_2020_updated_2024_report_2026','forest_published_percent_three_decimals_pooled_ratio_uses_native_hectares','forest_not_ucs_time_series_or_ecological_quality']
    return dict(ctx,**parts,metric=key,dimension=dimension,geography=row['code'],period=period,value=value,publishedValue=published,source=metric['sourceUrl'],evidence=evidence,provenance=evidence,notApplicable=bool(row.get('notApplicable')),dataUnavailable=value is None or bool(row.get('dataUnavailable'))),notes

def benchmark(engine,key,scope,municipal):
    if scope not in scopes(key,municipal['dimension']):raise ValueError('geography_benchmark_dimension_not_frozen')
    snap,ref=engine.file(BENCHMARK);gate=snap.get('qualityGate',{})
    if snap.get('schemaVersion')!=1 or snap.get('profileId')!='istat-geografia-comunale-2021' or snap.get('referenceYear')!=2021 or gate.get('status')!='PASS' or gate.get('errors') or gate.get('publicSnapshotReconciliation')!='7/7 PASS' or gate.get('municipalityCountItaly')!=7904 or gate.get('municipalityCountTuscany')!=273:raise ValueError('geography_benchmark_gate_changed')
    raw=snap['scopes'][scope];b=snap['benchmarks'][key];meta=engine._catalog['metrics'][key]['meta']['benchmark']
    formula={'municipalSurface':'total surface / municipality count','populationDensity':'scope population / scope surface','altitudeProfile':'area >=300 m / total area × 100'}[key]
    if b['unit']!=UNITS[key] or b.get('formula')!=formula or str(b['year'])!=('2026 / superficie 2021' if key=='populationDensity' else '31 dicembre 2021') or meta.get('sourceSnapshot')!=BENCHMARK or str(meta.get('year'))!=str(b['year']) or meta.get('url')!=SOURCE:raise ValueError('geography_benchmark_reference_changed')
    area=raw['totalSurfaceKm2']
    if not finite(area) or area<=0 or type(raw['municipalities']) is not int or raw['municipalities']!=(273 if scope=='tuscany' else 7904):raise ValueError('geography_invalid_benchmark_components')
    parts={};evidence=[dict(ref,kind='benchmark_snapshot',valuePointer=f'/benchmarks/{key}/{scope}',recordPointer='/scopes/'+scope)]
    if key=='municipalSurface':value=area/raw['municipalities'];close(raw['meanMunicipalSurfaceKm2'],value)
    elif key=='populationDensity':
        ps,pr=engine.file(POP_BENCHMARK);pb=ps['benchmarks']['population']
        if ps.get('qualityGate',{}).get('status')!='PASS' or str(pb.get('year'))!='2026' or pb.get('unit')!='number':raise ValueError('density_benchmark_population_changed')
        close(raw['population'],pb[scope]);value=raw['population']/area;close(raw['populationDensity'],value)
        parts=dict(numerator=raw['population'],denominator=area,scale=1,numeratorPeriod='2026',denominatorPeriod='2021');evidence.append(dict(pr,kind='population_benchmark_snapshot',valuePointer=f'/benchmarks/population/{scope}'))
    else:
        value=raw['from300Pct']
        if not finite(value) or not 0<=value<=100:raise ValueError('geography_invalid_benchmark_components')
    close(b[scope],value);close(meta[scope],value)
    return dict({k:municipal[k] for k in ('metric','dimension','unit','population','definition','method','frequency','periodBasis','adapter','period')},**parts,geography=scope,value=value,source=SOURCE,evidence=evidence,provenance=evidence,notApplicable=False,dataUnavailable=False,benchmarkMeaning='mean area per municipality, not total regional area' if key=='municipalSurface' else 'scope aggregate population / area' if key=='populationDensity' else 'area-weighted share >=300 m; municipal summary rounded')
