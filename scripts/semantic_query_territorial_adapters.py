"""Source-specific A6 adapters for reviewed territorial policy questions."""
from semantic_operations import finite
from semantic_query_adapters import AGE_BANDS, AGE_SNAPSHOT, ratio, reconcile

DEMOGRAPHY = 'data/source-snapshots/a3-istat-demography-benchmark-2026.json'
CHILD = 'data/source-snapshots/a3-toscana-early-childhood-benchmark-2024-25.json'
TOURISM = 'data/source-snapshots/a3-regione-toscana-tourism-benchmark-2025.json'
ARS = 'data/source-snapshots/ars-salute-demographics-v140.json'
NEW_KEYS = ('earlyChildhoodPotentialCapacityRate','tourismPresences','tourismIntensity','elderlyHomeCare')
SEX = {'sex:total':'totale','sex:men':'maschi','sex:women':'femmine'}
RATIOS = ('earlyChildhoodPotentialCapacityRate','tourismIntensity')
CURRENT_ONLY = ('earlyChildhoodPotentialCapacityRate','tourismIntensity','elderlyHomeCare')


def integer(value):
    if type(value) is not int or value<0:
        raise ValueError('invalid_source_count')
    return value


def context(metric, key, dimension):
    meta=metric['meta']
    if key=='population' and dimension in ('sex:men','sex:women'):
        if not any(r.get('sexDimension') for r in metric['rows']):
            raise ValueError('population_sex_carrier_not_materialized')
        if meta.get('unit')!='number' or metric['sourceUrl']!='https://demo.istat.it/':
            raise ValueError('population_definition_changed')
        return dict(unit='number',population=f'resident population {dimension} at January 1',
            definition=f'resident count {dimension}',method='Istat POSAS published sex counts',
            frequency='annual',periodBasis='stock at January 1 of reference year',adapter='istat-posas-population-sex/v1')
    if key=='elderlyHomeCare':
        if dimension not in SEX:
            raise ValueError('explicit_ars_sex_dimension_required')
        source=meta.get('demographicSource',{})
        if not source:
            raise ValueError('ars_dimension_carrier_not_materialized')
        if meta.get('unit')!='per1000' or source.get('indicatorId')!=260 or source.get('snapshot')!=ARS or source.get('measurement')!='misura_standardizzata':
            raise ValueError('ars_measurement_or_definition_changed')
        return dict(unit='per1000',population=f'ARS elderly resident reference population {SEX[dimension]}',
            definition='ARS 260 age-standardized home care rate; not crude num/den',
            method='ARS published age-standardized measure',frequency='annual',
            periodBasis='ARS reference year; source standard population and universe retained',adapter='ars-260-standardized-sex/v1')
    if dimension!='total':
        raise ValueError('dimension_adapter_not_implemented')
    if key=='earlyChildhoodPotentialCapacityRate':
        if meta.get('unit')!='percent' or metric['sourceUrl']!='https://dati.toscana.it/dataset/serviziprimainfanzia' or metric.get('method',{}).get('formula')!='Totale Ricettività potenziale / Totale 3-36 mesi x 100':
            raise ValueError('child_capacity_definition_changed')
        return dict(unit='percent',population='resident children aged 3–36 months',
            definition='potential local educational places / resident children aged 3–36 months * 100',
            method='Tuscany explicit municipal capacity and children counts',frequency='educational_year',
            periodBasis='educational year token; not calendar year',adapter='tuscany-child-capacity/v1')
    if key in ('tourismPresences','tourismIntensity'):
        unit='number' if key=='tourismPresences' else 'decimal'
        if meta.get('unit')!=unit or metric['sourceUrl']!='https://www.regione.toscana.it/-/arrivi-e-presenze-nelle-strutture-ricettive-e-struttura-dell-offerta-dati-2025%C2%A0':
            raise ValueError('tourism_definition_changed')
        return dict(unit=unit,population='registered accommodation nights excluding locazioni' if key=='tourismPresences' else 'resident population at January 1 2026',
            definition='registered accommodation nights' if key=='tourismPresences' else 'registered accommodation nights 2025 / POSAS residents January 1 2026',
            method='Tuscany municipal movement counts excluding locazioni',frequency='annual',
            periodBasis='tourism flow in reference calendar year' if key=='tourismPresences' else 'tourism flow 2025 divided by stock January 1 2026',
            adapter=f'tuscany-{key}/v1')
    raise ValueError('adapter_not_implemented')


def source_record(engine, path, pointer, source, **extra):
    _,ref=engine.file(path)
    return dict(ref,kind='source_snapshot',recordPointer=pointer,sourceUrl=source,**extra)


def population_sex(engine, metric, row, dimension, period):
    if period!='2026':
        raise ValueError('population_sex_period_not_available')
    snapshot,_=engine.file(AGE_SNAPSHOT)
    group=row.get('sexDimension',{})
    if str(group.get('year'))!=period or group.get('unit')!='number' or group.get('total')!=row['value']:
        raise ValueError('population_sex_context_mismatch')
    raw=snapshot['posas']['ageSex2026'][row['town']]
    if len(raw)!=101 or {r['age'] for r in raw}!=set(range(101)):
        raise ValueError('population_sex_age_detail_incomplete')
    for r in raw:
        if integer(r['men'])+integer(r['women'])!=integer(r['total']):
            raise ValueError('population_sex_counts_inconsistent')
    total=sum(r['total'] for r in raw)
    if total!=group['total']:
        raise ValueError('population_sex_total_mismatch')
    groups=group.get('groups',[])
    if len(groups)!=2 or {g['key'] for g in groups}!={'men','women'}:
        raise ValueError('population_sex_groups_incomplete')
    for g in groups:
        if integer(g['count'])!=sum(r[g['key']] for r in raw):
            raise ValueError('population_sex_count_mismatch')
        if g.get('value') is not None:reconcile(g['value'],g['count'])
    index=next(i for i,g in enumerate(groups) if 'sex:'+g['key']==dimension)
    source=next(s['url'] for s in snapshot['posas']['sources'] if str(s['year'])==period)
    evidence=source_record(engine,AGE_SNAPSHOT,f'/posas/ageSex2026/{row["town"]}',source,
        generatedAt=snapshot.get('generatedAt'),status=snapshot.get('status'))
    return groups[index].get('value'),f'/sexDimension/groups/{index}/value',{},[evidence],source,[]


def observation(engine, key, row, dimension, period, value):
    notes=[];components={}
    if key=='earlyChildhoodPotentialCapacityRate':
        snapshot,_=engine.file(CHILD)
        if snapshot['sourceProfileId']!='regione-toscana-early-childhood' or snapshot['qualityGate']['status']!='PASS' or str(snapshot['benchmarks'][key]['year'])!=period:
            raise ValueError('child_period_or_quality_mismatch')
        record=snapshot['municipalReconciliation'][str(row['code'])]
        if record['town']!=row['town'] or row.get('potentialCapacity')!=record['capacity'] or row.get('children3to36Months')!=record['children3to36Months']:
            raise ValueError('child_components_mismatch')
        n,d=integer(record['capacity']),integer(record['children3to36Months'])
        expected=ratio(n,d,100);reconcile(record['value'],expected)
        if value is not None:reconcile(value,expected)
        components=dict(numerator=n,denominator=d,scale=100)
        source=snapshot['sources']['data'];pointer=f'/municipalReconciliation/{row["code"]}'
        evidence=source_record(engine,CHILD,pointer,source,archiveSha256=snapshot['sources']['csvSha256'],qualityGate=snapshot['qualityGate'])
        notes=['potential_capacity_not_attendance_or_access','cross_boundary_use_waiting_lists_and_quality_not_measured']
    elif key in ('tourismPresences','tourismIntensity'):
        snapshot,_=engine.file(TOURISM);history=snapshot['municipalMovementHistory']
        if snapshot['qualityGate']['status']!='PASS' or snapshot['sourceProfileId']!='regione-toscana-tourism-annual' or history['scope']!='al netto delle locazioni' or int(period) not in history['years']:
            raise ValueError('tourism_period_scope_or_quality_mismatch')
        n=integer(history['countsByYear'][period][str(row['code'])]['presences'])
        if key=='tourismPresences':expected=n
        else:
            if period!='2025':raise ValueError('tourism_ratio_period_not_available')
            pop,popref=engine.file(AGE_SNAPSHOT)
            records=[r for r in pop['posas']['towns'][row['town']] if str(r['year'])=='2026']
            if len(records)!=1:raise ValueError('tourism_population_record_not_unique')
            d=integer(records[0]['population']);expected=ratio(n,d,1)
            components=dict(numerator=n,denominator=d,scale=1,numeratorPeriod='2025',denominatorPeriod='2026')
            notes.append('tourism_flow_2025_resident_stock_2026')
        if value is not None:reconcile(value,expected)
        source=history['sources'][period]['url'];pointer=f'/municipalMovementHistory/countsByYear/{period}/{row["code"]}/presences'
        evidence=source_record(engine,TOURISM,pointer,source,archive=history['sources'][period],scope=history['scope'],qualityGate=snapshot['qualityGate'])
        notes.extend(['registered_nights_exclude_locazioni_and_day_visitors','tourism_intensity_is_not_daily_peak_or_service_demand'])
        extra=[]
        if key=='tourismIntensity':
            extra=[dict(popref,kind='denominator_snapshot',record=f'posas.towns.{row["town"]}.year=2026',
                period='2026',sourceUrl=next(s['url'] for s in pop['posas']['sources'] if str(s['year'])=='2026'))]
        return value,'',components,[evidence]+extra,source,notes
    elif key=='elderlyHomeCare':
        snapshot,_=engine.file(ARS);spec=snapshot['indicators']['260']
        if spec['key']!=key or spec['period']!=period or spec['unit']!='per1000':
            raise ValueError('ars_period_or_indicator_mismatch')
        sex=SEX[dimension];parts=row.get('parts',[])
        selected=[(i,p) for i,p in enumerate(parts) if p.get('key')==sex]
        records=[(i,r) for i,r in enumerate(spec['rows']) if str(r['geoCode']).zfill(6)==str(row['code']) and r['sex']==sex and r['period']==period and r['strato1'] is None and r['strato2'] is None]
        if len(selected)!=1 or len(records)!=1:raise ValueError('ars_record_or_part_not_unique')
        index,part=selected[0];rawindex,record=records[0]
        if part.get('measurement')!='standardized' or part.get('unit')!='per1000':raise ValueError('ars_measurement_changed')
        if part.get('value') is not None:reconcile(part['value'],record['standardized'])
        for a,b in [('raw','raw'),('standardized','standardized'),('numerator','num'),('denominator','den'),('ci95Low','ci95Low'),('ci95High','ci95High')]:
            reconcile(part[a],record[b])
        source=spec['exportUrl'];pointer=f'/indicators/260/rows/{rawindex}'
        evidence=source_record(engine,ARS,pointer,source,archiveSha256=spec['sourceSha256'],
            reportedNumerator=record['num'],reportedDenominator=record['den'],crudeRate=record['raw'],
            standardizedRate=record['standardized'],ci95Low=record['ci95Low'],ci95High=record['ci95High'],
            componentUse='num/den describes crude rate; never aggregate standardized rates by these counts')
        return part.get('value'),f'/parts/{index}/value',{},[evidence],source,['standardized_rate_not_crude_ratio','care_delivery_not_unmet_need_or_quality']
    else:raise ValueError('adapter_not_implemented')
    return value,'',components,[evidence],source,notes


def benchmark(engine, key, scope, municipal):
    dimension=municipal['dimension'];period=municipal['period']
    if key=='ageDistribution':
        if scope not in ('tuscany','italy'):raise ValueError('benchmark_scope_not_supported')
        snapshot,_=engine.file(DEMOGRAPHY);spec=snapshot['benchmarks'][key]
        if snapshot['sourceProfileId']!='istat-demography-annual' or snapshot['qualityGate']['status']!='PASS' or not snapshot['qualityGate']['ageBandsExhaustive'] or spec['year']!=period or spec['unit']!='percent':
            raise ValueError('age_benchmark_context_mismatch')
        raw=snapshot['components'][scope][key];bands=raw['bands']
        if set(bands)!={k.removeprefix('age:') for k in AGE_BANDS} or sum(integer(v) for v in bands.values())!=integer(raw['population']):
            raise ValueError('age_benchmark_bands_not_exhaustive')
        n,d=bands[dimension.removeprefix('age:')],raw['population'];value=ratio(n,d,100)
        source=snapshot['sources']['posas2026']['url'];pointer=f'/components/{scope}/ageDistribution'
        ref=source_record(engine,DEMOGRAPHY,pointer,source,qualityGate=snapshot['qualityGate'],retrieved=snapshot['retrieved'])
        # Primary benchmark is specifically 20–34; never substitute it for another band.
        if dimension=='age:20-34':
            reconcile(spec[scope],value)
            published=engine.catalog['metrics'][key]['meta'].get('benchmark')
            if published:
                if str(published['year'])!=period or published['sourceSnapshot']!=DEMOGRAPHY:raise ValueError('published_benchmark_context_mismatch')
                reconcile(published[scope],value)
        components=dict(numerator=n,denominator=d,scale=100)
    elif key=='earlyChildhoodPotentialCapacityRate':
        if scope!='tuscany':raise ValueError('benchmark_scope_not_available')
        snapshot,_=engine.file(CHILD);spec=snapshot['benchmarks'][key]
        if snapshot['qualityGate']['status']!='PASS' or spec['year']!=period or spec['unit']!='percent':raise ValueError('child_benchmark_context_mismatch')
        raw=snapshot['raw']['tuscany'];n,d=integer(raw['capacity']),integer(raw['children3to36Months'])
        value=ratio(n,d,100);reconcile(spec[scope],value)
        source=snapshot['sources']['data'];pointer='/raw/tuscany'
        ref=source_record(engine,CHILD,pointer,source,archiveSha256=snapshot['sources']['csvSha256'],qualityGate=snapshot['qualityGate'])
        components=dict(numerator=n,denominator=d,scale=100)
    elif key=='tourismIntensity':
        if scope!='tuscany' or period!='2025':raise ValueError('benchmark_scope_or_period_not_available')
        snapshot,_=engine.file(TOURISM);demo,demoref=engine.file(DEMOGRAPHY)
        spec=snapshot['benchmarks'][key]
        if snapshot['qualityGate']['status']!='PASS' or spec['formula']!='presenze 2025 / popolazione benchmark 2026' or spec['year']!=period or spec['unit']!='decimal' or demo['qualityGate']['status']!='PASS' or demo['benchmarks']['population']['year']!='2026':
            raise ValueError('tourism_benchmark_context_mismatch')
        n,d=snapshot['benchmarks']['tourismPresences']['tuscany'],demo['benchmarks']['population']['tuscany']
        integer(n);integer(d);value=ratio(n,d,1);reconcile(spec['tuscany'],value)
        source=snapshot['sources']['movement'];ref=source_record(engine,TOURISM,'/benchmarks/tourismPresences/tuscany',source,
            qualityGate=snapshot['qualityGate'],acquisitionEvidence=snapshot['acquisitionEvidence'])
        components=dict(numerator=n,denominator=d,scale=1,numeratorPeriod='2025',denominatorPeriod='2026')
        extra=[dict(demoref,kind='denominator_snapshot',recordPointer='/benchmarks/population/tuscany',period='2026',sourceUrl=demo['sources']['posas2026']['url'])]
    elif key=='elderlyHomeCare':
        if scope not in ('tuscany','versilia'):raise ValueError('benchmark_scope_not_available')
        snapshot,_=engine.file(ARS);spec=snapshot['indicators']['260'];sex=SEX[dimension]
        if spec['period']!=period:raise ValueError('ars_benchmark_period_mismatch')
        code='90' if scope=='tuscany' else '202M'
        records=[(i,r) for i,r in enumerate(spec['rows']) if r['geoCode']==code and r['sex']==sex and r['period']==period and r['strato1'] is None and r['strato2'] is None]
        if len(records)!=1:raise ValueError('ars_benchmark_record_not_unique')
        i,raw=records[0];value=raw['standardized'];source=spec['exportUrl']
        ref=source_record(engine,ARS,f'/indicators/260/rows/{i}',source,archiveSha256=spec['sourceSha256'],
            ci95Low=raw['ci95Low'],ci95High=raw['ci95High'],officialGeography=raw['geography'])
        components={}
        if scope=='tuscany':
            published=engine.catalog['metrics'][key]['meta']['benchmarksBySex'][sex]
            if str(published['year'])!=period:raise ValueError('published_benchmark_context_mismatch')
            reconcile(published['tuscany'],value)
    else:raise ValueError('benchmark_adapter_not_implemented')
    if not finite(value):raise ValueError('invalid_benchmark_value')
    if key in ('earlyChildhoodPotentialCapacityRate','tourismIntensity'):
        published=engine.catalog['metrics'][key]['meta'].get('benchmark')
        if published:
            expected_path=CHILD if key=='earlyChildhoodPotentialCapacityRate' else TOURISM
            if str(published['year'])!=period or published['sourceSnapshot']!=expected_path:raise ValueError('published_benchmark_context_mismatch')
            reconcile(published[scope],value)
    evidence=[dict(ref,kind='benchmark_snapshot')]+(extra if key=='tourismIntensity' else [])
    return dict(engine.context(key,dimension),**components,metric=key,dimension=dimension,geography=scope,
        period=period,value=value,source=source,evidence=evidence,provenance=evidence,notApplicable=False,dataUnavailable=False)
