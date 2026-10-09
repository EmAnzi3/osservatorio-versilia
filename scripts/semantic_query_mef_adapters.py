"""MEF native components: source-specific means and distinct income universes."""
import hashlib
import json
import math
from semantic_operations import finite

KEYS=('incomeDistribution','incomeSourceProfile','pensionIncomeShare','taxpayersAdultPopulationRate')
DISTRIBUTION,PROFILE,PENSION,TAXPAYERS=KEYS
CURRENT='data/source-snapshots/mef-income-lotto-a-2024.json'
HISTORY='data/source-snapshots/a3-simple-mef-history-2023-2024.json'
DEMO='data/source-snapshots/istat-demography-lotto-a-2026-08.json'
BENCH='data/source-snapshots/a3-mef-benchmark-2024.json'
TAX_BENCH='data/source-snapshots/a3-mef-taxpayers-benchmark-2024.json'
URL='https://www1.finanze.gov.it/finanze/analisi_stat/public/index.php'
HYBRID='MEF a.i. 2024 · residenti 1.1.2026'
SOURCES=('employment','pension','selfEmployment','entrepreneurOrdinary','entrepreneurSimplified','participation','buildings')
LABELS=('Lavoro dipendente e assimilati','Pensione','Lavoro autonomo','Impresa · contabilità ordinaria','Impresa · contabilità semplificata','Partecipazione','Fabbricati')
BANDS=('le0','0to10k','10to15k','15to26k','26to55k','55to75k','75to120k','over120k')
MACROS=((0,1,2),(3,),(4,),(5,6,7))
MACRO_LABELS=('Fino a 15.000 €','15.001–26.000 €','26.001–55.000 €','Oltre 55.000 €')
HASHES={
 CURRENT:('f5ed030543cfbcac9ea630ffbfdf71d9f00bf5c1978bed2d5a670c25264032d3','9da6749489071735c25f5a75d7598c83d1950b80707e609bc393128b4c24584b'),
 HISTORY:('079d6cdff7a09f65e9384d4381d2c2f3e9742286a29959271b96f0d2503b15b2','f16cef0609fab86ac916f823a5e9444cf60f717a4d9445f461118d894be16db0'),
 DEMO:('8ec47305870a84cd0da4fd0b36dc0ee33693557cec4df0796f56d04f78bb68f7','24713ad8f1ebeb3b588790973fa4909aa2151f1005b63342691e4129ca852a07'),
 BENCH:('ad51c1eac33d05465ea6082a273a30f51a4f6fb7abded8727aa5e4c01b0794e7','d9b5aca421cf848b6a5c947fd2cb10bc6b476581451b565902262fff66104d48'),
 TAX_BENCH:('88adb57f13ab83fa7a77b5179dfbcefd7399086ac307627c21907662add34e52','bca5845084c55263508c7deef0758e432dbf3cee8bd6e45de44e3be84eb068aa')}


def dimensions(key):
    if key==DISTRIBUTION:return ['total',*('macro:'+str(i) for i in range(4)),*('band:'+b for b in BANDS)]
    if key==PROFILE:return ['total',*('source:'+s for s in SOURCES)]
    return ['total']


def token(key,period):
    t=str(period)
    if key==TAXPAYERS:
        if t!=HYBRID:raise ValueError('mef_hybrid_period_required')
    elif t not in ('2023','2024'):raise ValueError('mef_period_not_frozen')
    return t


def selected(key,dim):
    if key==PROFILE:return SOURCES[0] if dim=='total' else dim[7:]
    if key==DISTRIBUTION:return 'macro:0' if dim=='total' else dim
    return dim


def scopes(key,dim):return ['tuscany','italy'] if key in (PENSION,TAXPAYERS) or key==PROFILE and selected(key,dim)=='employment' else []
def operations(key,dim):return ['compare','rank','weighted_ratio',*(['series'] if key in (PROFILE,PENSION) else []),*(['benchmark_gap'] if scopes(key,dim) else [])]
def selection_guard(key,dim,op):
    if op=='correlation':raise ValueError('mef_pair_not_jointly_reviewed')
    if op in ('absolute_change','relative_change','percentage_points','trend'):raise ValueError('mef_temporal_change_not_reviewed')
    if op=='series' and key not in (PROFILE,PENSION):raise ValueError('mef_history_not_frozen')
    if op=='anomaly':raise ValueError('mef_peer_anomaly_not_reviewed')
    if op=='benchmark_gap' and not scopes(key,dim):raise ValueError('mef_benchmark_dimension_not_reviewed')


def frozen(engine,path):
    s,ref=engine.file(path);a,b=HASHES[path]
    if ref.get('sha256')!=a or hashlib.sha256(json.dumps(s,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()!=b:raise ValueError('mef_frozen_input_changed')
    return s,ref


def close(actual,expected):
    if expected is None:
        if actual is not None:raise ValueError('mef_public_native_mismatch')
    elif not finite(actual) or not math.isclose(actual,expected,rel_tol=0,abs_tol=1e-8):raise ValueError('mef_public_native_mismatch')


def ratio(n,d,scale=1):return None if n is None or d is None or d==0 else n/d*scale


def context(metric,key,dim):
    if dim not in dimensions(key):raise ValueError('mef_dimension_not_reviewed')
    meta=metric['meta'];unit={DISTRIBUTION:'percent',PROFILE:'currency',PENSION:'percent',TAXPAYERS:'per100'}[key]
    if meta.get('unit')!=unit or meta.get('year')!=(HYBRID if key==TAXPAYERS else '2024') or metric.get('sourceUrl')!=URL:raise ValueError('mef_definition_changed')
    if key in (DISTRIBUTION,PROFILE) and meta.get('compositeType')!=('distribution' if key==DISTRIBUTION else 'securityMeasures'):raise ValueError('mef_definition_changed')
    p=selected(key,dim)
    definitions={PROFILE:'nominal income amount / declarant frequency for source '+p+'; frequencies overlap across income sources',PENSION:'pension income amount / total income amount; not share of pensioners',TAXPAYERS:'all MEF taxpayers / Istat resident population aged 18+; numerator may include minors',DISTRIBUTION:'known published class frequencies / sum of known class frequencies' if p.startswith('macro:') else 'published frequency in MEF class '+p[5:]+' / reported total-income frequency; unreported class remains missing'}
    return dict(unit=unit,population='municipal fiscal records; selected income-source declarants' if key==PROFILE else 'municipal declared income amounts' if key==PENSION else 'MEF taxpayers and distinct Istat adult resident population' if key==TAXPAYERS else 'known class frequencies only' if p.startswith('macro:') else 'reported total-income declarant frequency',definition=definitions[key],method='frozen native component ratio; no imputation or cross-source frequency sum',frequency='hybrid_snapshot' if key==TAXPAYERS else 'annual',periodBasis=HYBRID if key==TAXPAYERS else 'tax year, not declaration/publication year',adapter='mef/'+key+'/'+p+'/v1')


def identity(engine,metric,row,native):
    codes={t['code']:t['name'] for t in engine._catalog['towns']}
    if len(metric['rows'])!=len(codes) or {r['code'] for r in metric['rows']}!=set(codes) or {n['code'] for n in native['towns'].values()}!=set(codes) or row['town']!=codes[row['code']] or row.get('slug')!='-'.join(row['town'].lower().split()) or row.get('notApplicable') or row.get('dataUnavailable'):raise ValueError('mef_municipal_identity_changed')
    n=native['towns'][row['town']]
    if n['code']!=row['code'] or n['town']!=row['town'] or n['slug']!=row['slug']:raise ValueError('mef_municipal_identity_changed')
    return n


def available_periods(engine,key,dim,row):
    if key not in (PROFILE,PENSION):raise ValueError('mef_history_not_frozen')
    series=row.get('series') if key==PENSION or dim=='total' else row.get('componentSeries',{}).get(LABELS[SOURCES.index(selected(key,dim))])
    if not isinstance(series,dict):raise ValueError('mef_history_not_materialized')
    return [str(y) for y in series['years']]


def observation(engine,key,index,dim,period,historical):
    m=engine._catalog['metrics'][key];row=m['rows'][index];ctx=context(m,key,dim);s,ref=frozen(engine,CURRENT);n=identity(engine,m,row,s);p=selected(key,dim);path='/towns/'+row['town'];base=f'/metrics/{key}/rows/{index}/';pointer=base+'value';refs=[];warnings=['mef_nominal_declared_income_not_disposable_income','mef_income_source_frequencies_overlap_do_not_sum_people','mef_frozen_extraction_not_new_live_acquisition'];extra={};scale=100 if key!=PROFILE else 1
    if key in (PROFILE,PENSION):
        raw=n
        if historical or period=='2023':
            h,href=frozen(engine,HISTORY);item=h['towns'][row['town']]
            if item['code']!=row['code'] or any(item['countsByYear']['2024'][f]!=n[f] for f in ('totalIncome','incomeSources','pensionIncome')):raise ValueError('mef_history_current_mismatch')
            raw=item['countsByYear'][period];ref=href;path+='/countsByYear/'+period
        if key==PROFILE:
            j=SOURCES.index(p);items={v['key']:v for v in raw['incomeSources']};source=items[p];num=source['amountEuro'];den=source['frequency'];expected=ratio(num,den)
            current=next(v for v in n['incomeSources'] if v['key']==p)
            if [v.get('selectorLabel') for v in row['parts']]!=list(LABELS):raise ValueError('mef_public_parts_changed')
            part=row['parts'][j]
            if part.get('unit')!='currency':raise ValueError('mef_public_parts_changed')
            close(part['count'],current['frequency']);close(part['amountEuro'],current['amountEuro']);close(part['value'],ratio(current['amountEuro'],current['frequency']));close(row['value'],row['parts'][0]['value'])
            path+='/incomeSources/'+str(raw['incomeSources'].index(source));pointer=base+('value' if dim=='total' else f'parts/{j}/value')
        else:
            num=raw['pensionIncome']['amountEuro'];den=raw['totalIncome']['amountEuro'];expected=ratio(num,den,100);close(row['value'],ratio(n['pensionIncome']['amountEuro'],n['totalIncome']['amountEuro'],100))
        if historical or period=='2023':
            periods=available_periods(engine,key,dim,row)
            if period not in periods:raise ValueError('mef_period_not_in_public_history')
            series=row['series'] if key==PENSION or dim=='total' else row['componentSeries'][LABELS[j]];i=periods.index(period);close(series['values'][i],expected)
            pointer=base+('series' if key==PENSION or dim=='total' else 'componentSeries/'+LABELS[j])+f'/values/{i}'
        if key in (PROFILE,PENSION) and row.get('mefScaleComponents') is not None:
            c=row['mefScaleComponents'];current_n=n['pensionIncome']['amountEuro'] if key==PENSION else next(v for v in n['incomeSources'] if v['key']=='employment')['amountEuro'];current_d=n['totalIncome']['amountEuro'] if key==PENSION else next(v for v in n['incomeSources'] if v['key']=='employment')['frequency']
            if c.get('sourceSnapshot')!=CURRENT or c.get('scale')!=(100 if key==PENSION else 1):raise ValueError('mef_public_scale_components_changed')
            close(c.get('numerator'),current_n);close(c.get('denominator'),current_d);close(c.get('normalized'),ratio(current_n,current_d,100 if key==PENSION else 1))
        value=expected
        extra['numeratorPointer']=path+'/amountEuro' if key==PROFILE else path+'/pensionIncome/amountEuro';extra['denominatorPointer']=path+'/frequency' if key==PROFILE else path+'/totalIncome/amountEuro'
    elif key==DISTRIBUTION:
        if period!='2024':raise ValueError('mef_distribution_period_not_frozen')
        bands=n['incomeBands'];coverage=n['bandCoverage']
        if [b['key'] for b in bands]!=list(BANDS) or row.get('detailCoverage')!=coverage or [b.get('key') for b in row['detailParts']]!=list(BANDS):raise ValueError('mef_public_band_coverage_changed')
        den_all=n['totalIncome']['frequency'];known=sum(b['frequency'] for b in bands if b['frequency'] is not None)
        if known!=coverage['availableFrequencyTotal'] or den_all!=coverage['reportedTotalIncomeFrequency']:raise ValueError('mef_native_band_coverage_changed')
        for j,b in enumerate(bands):
            pub=row['detailParts'][j]
            if pub.get('label')!=b['label'] or pub.get('unit')!='percent':raise ValueError('mef_public_parts_changed')
            close(pub['count'],b['frequency']);close(pub['amountEuro'],b['amountEuro']);close(pub['value'],ratio(b['frequency'],den_all,100))
        for j,indices in enumerate(MACROS):
            pub=row['parts'][j];count=sum(bands[i]['frequency'] for i in indices if bands[i]['frequency'] is not None)
            if pub.get('label')!=MACRO_LABELS[j]:raise ValueError('mef_public_parts_changed')
            close(pub['count'],count);close(pub['value'],ratio(count,known,100))
        close(row['value'],row['parts'][0]['value'])
        if p.startswith('macro:'):
            j=int(p[6:]);num=row['parts'][j]['count'];den=known;value=row['parts'][j]['value'];pointer=base+('value' if dim=='total' else f'parts/{j}/value');extra['componentPointers']=[path+f'/incomeBands/{i}/frequency' for i in MACROS[j]];extra['denominatorPointers']=[path+f'/incomeBands/{i}/frequency' for i in range(8) if bands[i]['frequency'] is not None]
        else:
            j=BANDS.index(p[5:]);num=bands[j]['frequency'];den=den_all;value=row['detailParts'][j]['value'];pointer=base+f'detailParts/{j}/value';extra.update(numeratorPointer=path+f'/incomeBands/{j}/frequency',denominatorPointer=path+'/totalIncome/frequency')
        extra.update(bandCoverage=coverage,missingBandKeys=[b['key'] for b in bands if b['frequency'] is None]);warnings+=['mef_macro_known_cells_denominator_differs_from_eight_band_total_denominator','mef_missing_band_cells_not_zero_or_redistributed','mef_bands_not_current_tax_brackets']
    else:
        if period!=HYBRID:raise ValueError('mef_hybrid_period_required')
        demo,dref=frozen(engine,DEMO);age=demo['posas']['ageSex2026'][row['town']];adults=sum(r['total'] for r in age if 18<=r['age']<=120);num=n['taxpayers'];den=adults;value=ratio(num,den,100)
        close(n['adultPopulation2026'],adults);close(row['taxpayers'],num);close(row['adultPopulation2026'],adults);close(row['value'],value)
        refs.append(dict(dref,kind='source_snapshot',recordPointer='/posas/ageSex2026/'+row['town'],includedAges='18–120',sourceUrl='https://demo.istat.it/'));extra.update(numeratorPointer=path+'/taxpayers',denominatorSnapshot=DEMO,denominatorPointer='/posas/ageSex2026/'+row['town']);warnings+=['mef_taxpayers_may_include_minors_not_share_of_adults_paying_irpef','mef_tax_year_2024_and_adult_population_2026_distinct']
    evidence=[dict(kind='catalog_snapshot',path=engine.catalog_path,sha256=engine.catalog_hash,valuePointer=pointer),dict(ref,kind='source_snapshot',recordPointer=path,**extra),*refs]
    if key in (PROFILE,PENSION) and period=='2023':source_url=frozen(engine,HISTORY)[0]['source']['url']
    else:source_url=s['source']['downloadUrl']
    return dict(ctx,metric=key,dimension=dim,geography=row['code'],period=period,value=value,numerator=num,denominator=den,scale=scale,numeratorPeriod='2024' if key==TAXPAYERS else period,denominatorPeriod='2026-01-01' if key==TAXPAYERS else period,source=source_url,evidence=evidence,provenance=evidence,notApplicable=False,dataUnavailable=value is None),warnings


def benchmark(engine,key,scope,municipal):
    dim=municipal['dimension']
    if scope not in scopes(key,dim) or municipal['period']!=(HYBRID if key==TAXPAYERS else '2024'):raise ValueError('mef_benchmark_scope_or_period_not_reviewed')
    path=TAX_BENCH if key==TAXPAYERS else BENCH;s,ref=frozen(engine,path);b=s['benchmarks'][key];meta=engine._catalog['metrics'][key]['meta']['benchmark']
    if meta.get('sourceSnapshot')!=path or meta.get('year')!=municipal['period'] or meta.get('url')!=URL:raise ValueError('mef_benchmark_definition_changed')
    if key==TAXPAYERS:n=b['raw'][scope];num=n['taxpayers'];den=n['adultPopulation2026']
    else:
        n=s['components'][scope];num=n['employmentIncomeAmountEuro' if key==PROFILE else 'pensionIncomeAmountEuro'];den=n['employmentIncomeFrequency' if key==PROFILE else 'totalIncomeAmountEuro']
    expected=ratio(num,den,municipal['scale']);close(b[scope],expected);close(meta[scope],expected)
    if key==PROFILE and (meta.get('part')!=LABELS[0] or b.get('part')!=LABELS[0]):raise ValueError('mef_benchmark_definition_changed')
    ev=[dict(ref,kind='benchmark_snapshot',valuePointer='/benchmarks/'+key+'/'+scope,componentPointer='/benchmarks/'+key+'/raw/'+scope if key==TAXPAYERS else '/components/'+scope)]
    return dict({k:municipal[k] for k in ('metric','dimension','unit','population','definition','method','frequency','periodBasis','adapter','period','numeratorPeriod','denominatorPeriod')},geography=scope,value=expected,source=URL,evidence=ev,provenance=ev,notApplicable=False,dataUnavailable=False)
