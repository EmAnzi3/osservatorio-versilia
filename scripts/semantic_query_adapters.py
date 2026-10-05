"""Reviewed A6 adapters: rules, not a second inventory of published metrics."""
import math

from semantic_operations import finite

CENSUS_PATH = 'data/source-snapshots/istat-sections-history-v1.8.0.json'
CENSUS_BENCHMARK = 'data/source-snapshots/a3-istat-census-benchmark-2023.json'
MEF_BENCHMARK = 'data/source-snapshots/a3-mef-taxable-income-benchmark-2024.json'
CENSUS_URL = 'https://www.istat.it/notizia/dati-per-sezioni-di-censimento/'
CENSUS = {
    'femaleEmploymentRate': ('percent', 'P103', 'female1564', 100, 'women resident aged 15–64', 'Donne occupate'),
    'maleEmploymentRate': ('percent', 'P102', 'male1564', 100, 'men resident aged 15–64', 'Uomini occupati'),
    'housingStockPer1000': ('per1000', 'A8', 'P1', 1000, 'resident population', 'Numero complessivo di abitazioni censite'),
    'nonOccupiedHomesPer1000': ('per1000', 'A3', 'P1', 1000, 'resident population', 'Abitazioni vuote o occupate soltanto da persone non residenti'),
}


def ratio(numerator, denominator, scale):
    if not finite(numerator) or numerator < 0 or not finite(denominator) or denominator <= 0:
        raise ValueError('invalid_source_ratio_components')
    return numerator / denominator * scale


def reconcile(actual, expected):
    if not finite(actual) or not math.isclose(actual, expected, rel_tol=0, abs_tol=1e-8):
        raise ValueError('source_ratio_reconciliation_failed')


def census_context(metric, key):
    unit,n,d,scale,population,description = CENSUS[key]
    meta = metric['meta']
    if meta.get('unit') != unit or metric.get('sourceUrl') != CENSUS_URL or not meta.get('description','').startswith(description):
        raise ValueError('census_definition_changed')
    return dict(unit=unit, population=population, definition=f'{n} / {d} * {scale}',
                method='Istat permanent census section additive variables', frequency='annual',
                periodBasis='census reference year; not POSAS January 1 stock', adapter=f'istat-census-{key}/v1')


def census_observation(engine, key, row, period, value):
    snapshot,ref = engine.file(CENSUS_PATH)
    if snapshot['comparabilityCheck']['result'] != 'accepted' or not any(x['key']==key and int(period) in x['years'] for x in snapshot['acceptedIndicators']):
        raise ValueError('census_comparability_not_attested')
    records = [(i,r) for i,r in enumerate(snapshot['raw'].get(period,[])) if str(r['code']) == str(row['code'])]
    if len(records) != 1 or records[0][1]['town'] != row['town']:
        raise ValueError('census_record_not_available_or_identity_mismatch')
    i,record = records[0]
    _,n,d,scale,_,_ = CENSUS[key]
    expected = ratio(record[n],record[d],scale)
    if value is not None:
        reconcile(value,expected)
    source = snapshot['source']['files'][period]
    evidence = dict(ref,kind='source_snapshot',recordPointer=f'/raw/{period}/{i}',
                    numeratorPointer=f'/raw/{period}/{i}/{n}',denominatorPointer=f'/raw/{period}/{i}/{d}',
                    generatedAt=snapshot['created'],sourceUrl=source['download'],archiveMember=source['data'],
                    comparabilityEvidence=snapshot['comparabilityCheck'])
    return dict(numerator=record[n],denominator=record[d],scale=scale),evidence,source['download']


def benchmark_observation(engine, key, scope, municipal):
    if scope not in ('tuscany','italy'):
        raise ValueError('benchmark_scope_not_supported')
    path = CENSUS_BENCHMARK if key in CENSUS else MEF_BENCHMARK if key == 'income' else None
    if path is None:
        raise ValueError('benchmark_adapter_not_implemented')
    snapshot,ref = engine.file(path)
    spec = snapshot['benchmarks'][key]
    if snapshot['qualityGate']['status'] != 'PASS' or str(spec['year']) != municipal['period'] or spec['unit'] != municipal['unit']:
        raise ValueError('benchmark_period_unit_or_quality_mismatch')
    raw = snapshot['raw'][scope]
    if key in CENSUS:
        _,n,d,scale,_,_ = CENSUS[key]
        if snapshot['profileId'] != 'istat-census-annual' or str(snapshot['referenceYear']) != municipal['period'] or snapshot['source']['regionalWorkbookCount'] != 20:
            raise ValueError('benchmark_census_scope_or_method_changed')
        # Same official Tuscany workbook underpinning the municipal observations.
        municipal_source = engine.file(CENSUS_PATH)[0]['source']['files'][municipal['period']]['data']
        if municipal_source['sha256'] != snapshot['source']['tuscanyWorkbook']['sha256'] or spec['formula'] != f'{n} / {d} × {scale}':
            raise ValueError('benchmark_census_source_or_formula_changed')
        numerator,denominator = raw[n],raw[d]
        source = snapshot['source']['url']
    else:
        source_spec = snapshot['source']
        if snapshot['profileId'] != 'mef-irpef-annual' or str(source_spec['actualTaxYear']) != municipal['period'] or source_spec['amountHeader'] != 'Reddito imponibile - Ammontare in euro' or source_spec['frequencyHeader'] != 'Reddito imponibile - Frequenza' or spec['formula'] != 'Reddito imponibile — Ammontare / Frequenza':
            raise ValueError('benchmark_mef_definition_changed')
        numerator,denominator,scale = raw['amount'],raw['frequency'],1
        n,d = 'amount','frequency'
        source = snapshot['sourceUrl']
    value = ratio(numerator,denominator,scale)
    reconcile(spec[scope],value)
    published = engine.catalog['metrics'][key]['meta'].get('benchmark')
    if published is not None:
        if str(published.get('year')) != municipal['period'] or published.get('sourceSnapshot') != path:
            raise ValueError('published_benchmark_context_mismatch')
        reconcile(published.get(scope),value)
    evidence = [dict(ref,kind='benchmark_snapshot',valuePointer=f'/benchmarks/{key}/{scope}',
                     numeratorPointer=f'/raw/{scope}/{n}',denominatorPointer=f'/raw/{scope}/{d}',
                     sourceUrl=source,sourceArchive=snapshot['source'],qualityGate=snapshot['qualityGate'],
                     methodEvidence=snapshot.get('method',snapshot.get('scope')))]
    if published is not None:
        evidence.append(dict(kind='published_benchmark',path=engine.catalog_path,sha256=engine.catalog_hash,
                             valuePointer=f'/metrics/{key}/meta/benchmark/{scope}'))
    return dict(engine.context(key),metric=key,dimension='total',geography=scope,period=municipal['period'],
                value=value,source=source,evidence=evidence,provenance=evidence,
                numerator=numerator,denominator=denominator,scale=scale,notApplicable=False,dataUnavailable=False)


# Explicit non-overlapping published dimensions; never interpret primary value
# (20–34 share) as the whole distribution or as mean age.
AGE_BANDS = {
    'age:0-14': ('0–14',0,14), 'age:15-19': ('15–19',15,19),
    'age:20-34': ('20–34',20,34), 'age:35-49': ('35–49',35,49),
    'age:50-64': ('50–64',50,64), 'age:65-79': ('65–79',65,79),
    'age:80-84': ('80–84',80,84), 'age:85+': ('85+',85,100),
}
AGE_SNAPSHOT = 'data/source-snapshots/istat-demography-lotto-a-2026-08.json'


def age_context(metric, dimension):
    meta = metric['meta']
    if meta.get('unit')!='percent' or meta.get('compositeType')!='distribution' or metric.get('sourceUrl')!='https://demo.istat.it/app/?a=2025&i=POS' or '1° gennaio 2026' not in metric.get('method',{}).get('caveat',''):
        raise ValueError('age_distribution_definition_changed')
    if dimension not in AGE_BANDS:
        raise ValueError('explicit_age_band_required')
    return dict(unit='percent',population='resident population at January 1',
                definition=f'residents {dimension} / all residents * 100',
                method='Istat POSAS single-age additive counts',frequency='annual',
                periodBasis='stock at January 1 of reference year',adapter='istat-posas-age-band/v1')


def age_observation(engine, row, period, dimension):
    if period!='2026':
        raise ValueError('age_snapshot_period_not_available')
    snapshot,ref = engine.file(AGE_SNAPSHOT)
    detail = snapshot['posas']['ageSex2026'][row['town']]
    # Age 100 is the official open terminal class; validate completeness and sex totals.
    if len(detail)!=101 or {x['age'] for x in detail}!=set(range(101)):
        raise ValueError('age_snapshot_non_exhaustive_or_duplicate')
    for item in detail:
        if any(type(item.get(k)) is not int or item[k]<0 for k in ('age','men','women','total')) or item['men']+item['women']!=item['total']:
            raise ValueError('age_snapshot_invalid_counts')
    total=sum(x['total'] for x in detail)
    records=[r for r in snapshot['posas']['towns'][row['town']] if str(r['year'])==period]
    sources=[s for s in snapshot['posas']['sources'] if str(s['year'])==period]
    if len(records)!=1 or len(sources)!=1 or records[0]['population']!=total or total<=0:
        raise ValueError('age_population_or_source_mismatch')
    parts=row.get('parts')
    if not isinstance(parts,list) or len(parts)!=len(AGE_BANDS) or {x.get('selectorLabel') for x in parts}!={v[0] for v in AGE_BANDS.values()}:
        raise ValueError('age_catalog_non_exhaustive_or_duplicate')
    # Reconcile every band, not just the selected one; nulls remain null.
    for label,lo,hi in AGE_BANDS.values():
        part=next(x for x in parts if x['selectorLabel']==label)
        count=sum(x['total'] for x in detail if lo<=x['age']<=hi)
        if type(part.get('count')) is not int or part['count']!=count:
            raise ValueError('age_band_count_mismatch')
        if part.get('value') is not None:
            reconcile(part['value'],ratio(count,total,100))
    label,lo,hi=AGE_BANDS[dimension]
    index=next(i for i,p in enumerate(parts) if p['selectorLabel']==label)
    count=parts[index]['count']
    evidence=dict(ref,kind='source_snapshot',record=f'posas.ageSex2026.{row["town"]}',
                  ageRange=[lo,hi],terminalClass='100 = 100 years and over',
                  numerator=count,denominator=total,generatedAt=snapshot.get('generatedAt'),
                  status=snapshot.get('status'),sourceUrl=sources[0]['url'])
    return parts[index].get('value'),index,dict(numerator=count,denominator=total,scale=100),evidence,sources[0]['url']
