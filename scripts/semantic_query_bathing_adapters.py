"""Frozen ARPAT classifications/samples and FEE awards, with distinct universes."""
import math
from semantic_operations import finite

KEYS=('bathingWaterQuality','bathingNonCompliantSamples','blueFlagBeaches')
COASTAL=('046005','046013','046024','046033')
NA=('046018','046028','046030')
NATIVE='data/source-snapshots/costa-mare-v123.json'
FEE='data/source-snapshots/a3-fee-blue-flag-benchmark-2026.json'
ARPAT='https://www.arpat.toscana.it/pubblicazione/il-controllo-delle-acque-di-balneazione-stagione-2025/'
BLUE='https://www.bandierablu.org/common/blueflag.asp?anno=2026&tipo=bb'
URLS=dict(zip(KEYS,(ARPAT,ARPAT,BLUE)))
LABELS=dict(zip(KEYS,('2025','2025','2026')))
PERIODS=dict(zip(KEYS,('2022-2025','2025','2026')))
FAMILIES=dict(zip(KEYS,('bathingWaterQuality2025','bathingNonCompliantSamples2025','blueFlagBeaches')))
CLASSES=('excellent','good','sufficient','poor')
SAMPLES=('all','routine','supplementary')
COUNTING='Si contano le localita elencate separatamente; le denominazioni unite da una barra restano una sola localita.'
DEFINITION='Campione non conforme se Enterococchi intestinali > 200 MPN/100 ml oppure Escherichia coli > 500 MPN/100 ml.'

def close(a,b):
    if not finite(a) or not finite(b) or not math.isclose(a,b,rel_tol=0,abs_tol=1e-8):raise ValueError('bathing_catalog_source_mismatch')

def count(v):return isinstance(v,int) and not isinstance(v,bool) and v>=0

def token(key,period):return PERIODS[key] if str(period)==LABELS[key] else str(period)

def dimensions(key):
    if key==KEYS[0]:return ['total',*('share:'+basis+':'+c for basis in ('areas','kilometres') for c in CLASSES),*('count:areas:'+c for c in (*CLASSES,'total')),*('kilometres:'+c for c in (*CLASSES,'total'))]
    if key==KEYS[1]:return ['total',*('share:'+s for s in SAMPLES),*('nonCompliant:'+s for s in SAMPLES),*('samples:'+s for s in SAMPLES)]
    return ['total']

def field(key,dimension):
    if dimension not in dimensions(key):raise ValueError('bathing_dimension_not_reviewed')
    if key==KEYS[2]:return ('count','localities','total')
    if key==KEYS[0]:
        if dimension=='total':return ('share','areas','excellent')
        p=dimension.split(':');return tuple(p) if len(p)==3 else ('count','kilometres',p[1])
    if dimension=='total':return ('share','all','nonCompliant')
    kind,scope=dimension.split(':');return (kind,scope,'nonCompliant' if kind!='samples' else 'total')

def weighted(key,dimension):return field(key,dimension)[0]=='share'

def operations(key,dimension):return ['compare','rank',*(['weighted_ratio'] if weighted(key,dimension) else []),*(['series'] if key==KEYS[2] else [])]

def selection_guard(key,dimension,operation):
    if operation in ('absolute_change','relative_change','percentage_points','trend'):raise ValueError('bathing_historical_change_not_reviewed' if key==KEYS[2] else 'bathing_classification_or_samples_history_not_frozen')
    if operation=='series' and key!=KEYS[2]:raise ValueError('bathing_classification_or_samples_history_not_frozen')
    if operation=='correlation':raise ValueError('bathing_universes_not_jointly_comparable')
    if operation=='anomaly':raise ValueError('bathing_anomaly_not_reviewed')
    if operation=='weighted_ratio' and not weighted(key,dimension):raise ValueError('bathing_verified_ratio_required')
    if operation=='benchmark_gap':raise ValueError('bathing_totals_not_municipal_reference')

def context(metric,key,dimension):
    kind,basis,category=field(key,dimension);meta=metric['meta']
    if meta.get('unit')!=('number' if key==KEYS[2] else 'percent') or str(meta.get('year'))!=LABELS[key] or metric.get('sourceUrl')!=URLS[key] or meta.get('sourceMeta',{}).get('snapshot')!=NATIVE:raise ValueError('bathing_definition_or_reference_changed')
    population='ARPAT classified marine bathing areas; count and classified kilometres are distinct denominators' if key==KEYS[0] else 'ARPAT unique marine bathing samples; routine and targeted supplementary controls kept separate' if key==KEYS[1] else 'FEE separately listed coastal awarded localities; slash-joined names count once'
    return dict(unit='percent' if kind=='share' else 'km' if basis=='kilometres' else 'number',population=population,definition=population+'; '+':'.join((kind,basis,category)),method='frozen native components; no inference on bathers, days, health risk or microbiological quality from awards',frequency='rolling_four_year_classification' if key==KEYS[0] else 'annual',periodBasis='2025 classification based on 2022–2025 observations' if key==KEYS[0] else '2025 monitoring season, not four-year classification' if key==KEYS[1] else 'annual FEE awards 2019–2026; historical locality identities not frozen',adapter='bathing/'+key+'/'+':'.join((kind,basis,category))+'/v1')

def identity(engine,key,row):
    rows=engine._catalog['metrics'][key]['rows']
    if len(rows)!=7 or {r['code'] for r in rows}!=set(COASTAL+NA):raise ValueError('bathing_public_cohort_changed')
    if not any(t['name']==row['town'] and t['code']==row['code'] for t in engine._catalog['towns']) or row['slug']!='-'.join(row['town'].lower().split()):raise ValueError('bathing_row_identity_changed')
    if row['code'] in NA:
        if row.get('value') is not None or row.get('notApplicable') is not True or row.get('series') is not None or row.get('coastDetail') is not None or any(any(p.get(f) is not None for f in ('value','nonCompliant','total')) for p in row.get('parts',[])):raise ValueError('bathing_not_applicable_changed')
    elif row.get('notApplicable') or key!=KEYS[2] and row.get('series') is not None:raise ValueError('bathing_applicability_or_history_changed')

def native(engine,key,row):
    identity(engine,key,row);s,ref=engine.file(NATIVE);family=FAMILIES[key];data=s[family];towns=data['towns'];extra=[]
    if s.get('schemaVersion')!=1 or s['scope'].get('coastalTownCodes')!=list(COASTAL) or s['scope'].get('notApplicableTownCodes')!=list(NA):raise ValueError('bathing_native_reference_changed')
    if set(towns)!=set(COASTAL):raise ValueError('bathing_native_cohort_changed')
    sources=('arpatReport2025','arpatSamples2025') if key!=KEYS[2] else ('blueFlag2026',)
    hashes={'arpatReport2025':'c190a78c0cf0d8a3e728d84aaa5fd50c7aefc6c0918cb8efa06305d0b965e76a','arpatSamples2025':'90d25c2b47ceae7d2222c718948a46fac6d11985eb0df464a30cc6236be4f1bf','blueFlag2026':'dbfbb3f4f7ea1397015f69b93b91f0acaa2ec71f7cd2e7a2fcad8f76bbd048fc'}
    for source in sources:
        if s['sources'][source].get('url')!=URLS[key] or s['sources'][source].get('sha256')!=hashes[source]:raise ValueError('bathing_native_reference_changed')
    if key==KEYS[0]:
        if data.get('period')!='Classificazione 2025 sui dati 2022-2025':raise ValueError('bathing_native_definition_changed')
        for n in towns.values():
            for basis in ('areas','kilometres'):
                v=n[basis]
                if set(v)!=set((*CLASSES,'total')) or any(not finite(v[c]) or v[c]<0 or basis=='areas' and not count(v[c]) for c in v) or v['total']<=0:raise ValueError('bathing_invalid_native_components')
                close(math.fsum(v[c] for c in CLASSES),v['total'])
        for basis in ('areas','kilometres'):
            for c in (*CLASSES,'total'):close(math.fsum(n[basis][c] for n in towns.values()),data['versilia'][basis][c])
    elif key==KEYS[1]:
        if data.get('definition')!=DEFINITION or data.get('deduplicationKey')!=['Codice area','Data','Rout. Suppl.']:raise ValueError('bathing_native_definition_changed')
        for n in towns.values():
            for scope in SAMPLES:
                v=n[scope]
                if not count(v['nonCompliant']) or not count(v['total']) or v['total']<=0 or v['nonCompliant']>v['total']:raise ValueError('bathing_invalid_native_components')
            for f in ('total','nonCompliant'):close(n['all'][f],n['routine'][f]+n['supplementary'][f])
            if not count(n['routine']['affectedAreas']) or not count(n['routine']['areas']) or not 0<=n['routine']['affectedAreas']<=n['routine']['areas']:raise ValueError('bathing_invalid_native_components')
        for scope in SAMPLES:
            for f in data['versilia'][scope]:close(math.fsum(n[scope][f] for n in towns.values()),data['versilia'][scope][f])
        close(data['uniqueSamples'],data['versilia']['all']['total'])
    else:
        years=list(range(2019,2027));archive=s['sources']['blueFlagArchive']
        if data.get('years')!=years or archive.get('years')!=years or archive.get('countingRule')!=COUNTING or archive.get('urlTemplate')!='https://www.bandierablu.org/common/blueflag.asp?anno={year}&tipo=bb':raise ValueError('bathing_native_definition_changed')
        for n in towns.values():
            if len(n['values'])!=8 or any(not count(v) for v in n['values']) or not isinstance(n['localities2026'],list) or any(not isinstance(v,str) or not v.strip() for v in n['localities2026']) or len(set(n['localities2026']))!=len(n['localities2026']):raise ValueError('bathing_invalid_native_components')
            close(n['values'][-1],len(n['localities2026']))
        if len(data['versiliaValues'])!=8:raise ValueError('bathing_invalid_native_components')
        for i,v in enumerate(data['versiliaValues']):close(v,sum(n['values'][i] for n in towns.values()))
    if row['code'] in NA:return None,ref,extra
    n=towns[row['code']]
    if n.get('name')!=row['town']:raise ValueError('bathing_row_identity_changed')
    if key==KEYS[2]:
        if row.get('series')!={'years':data['years'],'values':n['values']} or row.get('coastDetail')!={'localities2026':n['localities2026']}:raise ValueError('bathing_public_components_changed')
        b,br=engine.file(FEE)
        if b.get('schemaVersion')!=2 or b.get('sourceUrl')!=BLUE or b.get('sourceSha256')!='f67d97acc2dd1d202d8d045fab928a2ea690ba3e891c74787171cb83609e1603' or b.get('qualityGate',{}).get('status')!='PASS' or b['scope'].get('year')!=2026:raise ValueError('bathing_native_reference_changed')
        norm=lambda t:' '.join(t.split()).casefold()
        matches=[(i,r) for i,r in enumerate(b['records']) if r['region']=='Toscana' and norm(r['town'])==norm(row['town'])]
        if len(matches)!=1 or matches[0][1].get('revoked') is not False or [norm(v) for v in matches[0][1]['localities']]!=[norm(v) for v in n['localities2026']]:raise ValueError('bathing_fee_localities_not_reconciled')
        extra=[dict(br,kind='source_snapshot',recordPointer=f'/records/{matches[0][0]}')];value=n['values'][-1]
    else:
        detail={basis:n[basis] for basis in ('areas','kilometres')} if key==KEYS[0] else n
        if row.get('coastDetail')!=detail:raise ValueError('bathing_public_components_changed')
        bases=('areas','kilometres') if key==KEYS[0] else SAMPLES
        if [p['key'] for p in row.get('parts',[])]!=list(bases):raise ValueError('bathing_public_components_changed')
        for basis,p in zip(bases,row['parts']):
            v=n[basis];num=v['excellent' if key==KEYS[0] else 'nonCompliant'];close(p['value'],num/v['total']*100)
            if key==KEYS[1]:close(p['nonCompliant'],num);close(p['total'],v['total'])
        value=row['parts'][0]['value']
    if row.get('value') is not None:close(row['value'],value)
    return n,ref,extra

def available_periods(engine,key,dimension,row):
    if key!=KEYS[2]:raise ValueError('bathing_classification_or_samples_history_not_frozen')
    native(engine,key,row)
    return [str(y) for y in range(2019,2027)]

def observation(engine,key,index,dimension,period,historical):
    metric=engine._catalog['metrics'][key];row=metric['rows'][index];ctx=context(metric,key,dimension);kind,basis,category=field(key,dimension)
    if period not in ([str(y) for y in range(2019,2027)] if key==KEYS[2] else [PERIODS[key]]):raise ValueError('bathing_period_not_frozen')
    n,ref,extra=native(engine,key,row);value=None;parts={};pointer=f'/metrics/{key}/rows/{index}/value';record=f'/{FAMILIES[key]}/towns/{row["code"]}'
    if n is not None:
        if key==KEYS[2]:
            i=int(period)-2019;value=n['values'][i];record+=f'/values/{i}'
            if historical or period!='2026':pointer=f'/metrics/{key}/rows/{index}/series/values/{i}'
        else:
            num=n[basis][category];den=n[basis]['total'];value=num/den*100 if kind=='share' else num
            record+=f'/{basis}'
            if kind=='share':parts=dict(numerator=num,denominator=den,scale=100,numeratorPeriod=period,denominatorPeriod=period)
            # Non-excellent classification shares are derived from the attested component object.
            if key==KEYS[0]:pointer=f'/metrics/{key}/rows/{index}/coastDetail/{basis}' if kind=='share' and category!='excellent' else f'/metrics/{key}/rows/{index}/parts/{0 if basis=="areas" else 1}/value' if kind=='share' else f'/metrics/{key}/rows/{index}/coastDetail/{basis}/{category}'
            else:pointer=f'/metrics/{key}/rows/{index}/parts/{SAMPLES.index(basis)}/value' if kind=='share' else f'/metrics/{key}/rows/{index}/coastDetail/{basis}/{category}'
        if row.get('value') is None and dimension=='total' and period==PERIODS[key] and not historical:value=None
    else:record=f'/scope/notApplicableTownCodes/{NA.index(row["code"])}'
    evidence=[dict(kind='catalog_snapshot',path=engine.catalog_path,sha256=engine.catalog_hash,valuePointer=pointer),dict(ref,kind='source_snapshot',recordPointer=record),*extra]
    notes=['bathing_four_coastal_three_not_applicable','bathing_classification_samples_awards_not_interchangeable']
    notes+=['bathing_supplementary_targeted_not_random_sample_or_exposure_risk'] if key==KEYS[1] else ['blue_flag_multicriteria_not_microbiological_proxy','blue_flag_slash_names_unsplit_historical_zero_not_interpolated'] if key==KEYS[2] else ['bathing_four_year_classification_not_current_live_safety']
    return dict(ctx,**parts,metric=key,dimension=dimension,geography=row['code'],period=period,value=value,source=URLS[key] if key!=KEYS[2] else BLUE.replace('2026',period),provenance=evidence,evidence=evidence,notApplicable=bool(row.get('notApplicable')),dataUnavailable=value is None and not bool(row.get('notApplicable')) or bool(row.get('dataUnavailable'))),notes
