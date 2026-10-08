"""Distinct frozen Istat coastline, ISPRA protection and shoreline-change universes."""
import math
from semantic_operations import finite

KEYS=('statisticalCoastlineLength','rigidDefenceProtectedCoast','shorelineDynamics')
COASTAL=('046005','046013','046024','046033')
NA=('046018','046028','046030')
NATIVE='data/source-snapshots/costa-mare-v123.json'
ISTAT='data/source-snapshots/territorio-ucs-v136.json'
LINE_BENCHMARK='data/source-snapshots/a3-istat-coastline-benchmark-2021.json'
BENCHMARK='data/source-snapshots/a3-ispra-coast-benchmark-2020.json'
URLS={KEYS[0]:'https://www.istat.it/classificazione/principali-statistiche-geografiche-sui-comuni/',KEYS[1]:'https://indicatoriambientali.isprambiente.it/it/coste/costa-protetta',KEYS[2]:'https://indicatoriambientali.isprambiente.it/it/coste/dinamica-litoranea'}
LABELS=dict(zip(KEYS,('31 dicembre 2021','2020','2006–2020')))
PERIODS=dict(zip(KEYS,('2021','2020','2006-2020')))
CATEGORIES=('erosion','stable','advance')

def close(a,b,tolerance=1e-8):
    if not finite(a) or not finite(b) or not math.isclose(a,b,rel_tol=0,abs_tol=tolerance):raise ValueError('coast_catalog_source_mismatch')

def token(key,period):return PERIODS[key] if str(period)==LABELS[key] else str(period)

def dimensions(key):
    if key==KEYS[0]:return ['total']
    if key==KEYS[1]:return ['total','view:protectedKm','view:coastKm']
    return ['total',*('share:'+c for c in CATEGORIES),*('kilometres:'+c for c in CATEGORIES),'view:analysedKm']

def field(key,dimension):
    if dimension not in dimensions(key):raise ValueError('coast_dimension_not_reviewed')
    if key==KEYS[0]:return 'lengthKm'
    if key==KEYS[1]:return 'protectedShare' if dimension=='total' else dimension[5:]
    return 'erosionShare' if dimension=='total' else dimension[6:]+'Share' if dimension.startswith('share:') else dimension[11:]+'Km' if dimension.startswith('kilometres:') else 'analysedKm'

def weighted(key,dimension):return field(key,dimension).endswith('Share')
def scopes(key,dimension):return ['tuscany','italy'] if key==KEYS[1] and dimension=='total' else []

def operations(key,dimension):return ['compare','rank',*(['weighted_ratio'] if weighted(key,dimension) else []),*(['benchmark_gap'] if scopes(key,dimension) else [])]

def selection_guard(key,dimension,operation):
    if operation in ('series','absolute_change','relative_change','percentage_points','trend'):raise ValueError('coast_history_not_frozen')
    if operation=='correlation':raise ValueError('coast_universes_not_jointly_comparable')
    if operation=='anomaly':raise ValueError('coast_anomaly_not_reviewed')
    if operation=='weighted_ratio' and not weighted(key,dimension):raise ValueError('coast_verified_ratio_required')
    if operation=='benchmark_gap' and not scopes(key,dimension):raise ValueError('coast_benchmark_not_comparable')

def context(metric,key,dimension):
    f=field(key,dimension);meta=metric['meta']
    if meta.get('unit')!=('km' if key==KEYS[0] else 'percent') or str(meta.get('year'))!=LABELS[key] or metric.get('sourceUrl')!=URLS[key]:raise ValueError('coast_definition_or_reference_changed')
    population='Istat statistical coastline including artificial structures; directly littoral municipalities' if key==KEYS[0] else 'ISPRA 2020 coastal universe; rigid defence excludes nourishment' if key==KEYS[1] else 'ISPRA natural low coast analysed 2006–2020; displacement threshold 5 metres'
    return dict(unit='percent' if weighted(key,dimension) else 'km',population=population,definition=population+'; '+f,
        method='frozen source lengths; independent source universes and denominators',frequency='multi_year_interval' if key==KEYS[2] else 'snapshot',periodBasis='2006–2020 endpoint comparison, not annual erosion rate or annual time series' if key==KEYS[2] else '2021-12-31 statistical coastline' if key==KEYS[0] else '2020 cartographic protection photograph',adapter='coast/'+key+'/'+f+'/v1')

def identity(engine,key,row):
    rows=engine._catalog['metrics'][key]['rows']
    if len(rows)!=7 or {r['code'] for r in rows}!=set(COASTAL+NA):raise ValueError('coast_public_cohort_changed')
    if not any(t['name']==row['town'] and t['code']==row['code'] for t in engine._catalog['towns']):raise ValueError('coast_row_identity_changed')
    if row['slug']!='-'.join(row['town'].lower().split()):raise ValueError('coast_row_identity_changed')
    if row['code'] in NA:
        if row.get('value') is not None or row.get('notApplicable') is not True or row.get('series') is not None or row.get('coastDetail') is not None or any(p.get('value') is not None or p.get('kilometres') is not None for p in row.get('parts',[])):raise ValueError('coast_not_applicable_changed')
    elif row.get('notApplicable') or row.get('series') is not None:raise ValueError('coast_applicability_or_history_changed')

def native(engine,key,row):
    identity(engine,key,row)
    if key==KEYS[0]:
        s,ref=engine.file(ISTAT);src=s['sources']['istatCoastline']
        if s.get('schemaVersion')!=2 or src.get('referenceDate')!='2021-12-31' or src.get('page')!=URLS[key] or src.get('sha256')!='d0d2a693dfefe78ac77a113b1a3358cd8aff6f5149f2850b5650a19df727467e' or src.get('lengthField')!='SHAPE_Leng' or src.get('lengthUnit')!='metres':raise ValueError('coast_native_reference_changed')
        if set(s['coastlineKm'])!={r['town'] for r in engine._catalog['metrics'][key]['rows']}:raise ValueError('coast_native_cohort_changed')
        n=s['coastlineKm'][row['town']]
        if s['classifications'][row['town']]['littoral']!=(row['code'] in COASTAL) or (n is None)!=(row['code'] in NA):raise ValueError('coast_applicability_or_history_changed')
        if n is not None:
            if not finite(n) or n<=0:raise ValueError('coast_invalid_native_components')
            if row.get('value') is not None:close(row['value'],n)
            b,br=engine.file(LINE_BENCHMARK)
            if b.get('schemaVersion')!=2 or b.get('sourceSha256')!=src['sha256'] or b.get('sourceUrl')!=URLS[key] or b.get('qualityGate',{}).get('status')!='PASS':raise ValueError('coast_native_reference_changed')
            records=b['records'];matches=[(i,r) for i,r in enumerate(records) if r['code']==row['code']]
            if len(records)!=646 or len({r['code'] for r in records})!=646 or len(matches)!=1 or matches[0][1]['region']!=9:raise ValueError('coast_native_cohort_changed')
            close(n,matches[0][1]['lengthKm'],.00000000051);close(n,b['municipalReconciliation'][row['code']]['publicValueKm'])
            return {'lengthKm':n},ref,[dict(br,kind='source_snapshot',recordPointer=f'/records/{matches[0][0]}/lengthKm')]
        return None,ref,[]
    s,ref=engine.file(NATIVE);source='ispraProtectedCoast' if key==KEYS[1] else 'ispraShorelineDynamics';family='rigidDefenceProtectedCoast2020' if key==KEYS[1] else 'shorelineDynamics2006_2020';src=s['sources'][source]
    sha='9ca2b81cff7375f4af9f86af50543637d23329828d3556ccbe174a16e27d956e' if key==KEYS[1] else 'a00fb97649e293c73c923e43fd0ee53ecfa42df9568ec162a9668c2adb4c9b11'
    if s.get('schemaVersion')!=1 or src.get('url')!=URLS[key] or src.get('sha256')!=sha or s['scope'].get('coastalTownCodes')!=list(COASTAL) or s['scope'].get('notApplicableTownCodes')!=list(NA):raise ValueError('coast_native_reference_changed')
    towns=s[family]['towns']
    if set(towns)!=set(COASTAL):raise ValueError('coast_native_cohort_changed')
    if key==KEYS[1] and s[family].get('excludes')!='Ripascimenti artificiali':raise ValueError('coast_native_definition_changed')
    if key==KEYS[2] and s[family].get('definition')!={'erosion':'Arretramento superiore a 5 m','stable':'Variazione entro +/-5 m','advance':'Avanzamento superiore a 5 m'}:raise ValueError('coast_native_definition_changed')
    if row['code'] in NA:return None,ref,[]
    n=towns[row['code']];den='coastKm' if key==KEYS[1] else 'analysedKm';fields=('protectedKm',) if key==KEYS[1] else tuple(c+'Km' for c in CATEGORIES)
    if n.get('name')!=row['town']:raise ValueError('coast_row_identity_changed')
    if not finite(n[den]) or n[den]<=0 or any(not finite(n[f]) or not 0<=n[f]<=n[den] for f in fields):raise ValueError('coast_invalid_native_components')
    if key==KEYS[2]:close(math.fsum(n[f] for f in fields),n[den])
    if row.get('coastDetail')!=n:raise ValueError('coast_public_components_changed')
    if key==KEYS[2]:
        if [p['key'] for p in row.get('parts',[])]!=list(CATEGORIES):raise ValueError('coast_public_components_changed')
        for c,p in zip(CATEGORIES,row['parts']):close(p['kilometres'],n[c+'Km']);close(p['value'],n[c+'Km']/n[den]*100)
    if row.get('value') is not None:close(row['value'],n[fields[0]]/n[den]*100)
    return n,ref,[]

def observation(engine,key,index,dimension,period,historical):
    m=engine._catalog['metrics'][key];row=m['rows'][index];ctx=context(m,key,dimension);f=field(key,dimension)
    if period!=PERIODS[key]:raise ValueError('coast_period_not_frozen')
    n,ref,extra=native(engine,key,row);value=None;parts={};pointer=f'/metrics/{key}/rows/{index}/value';family='rigidDefenceProtectedCoast2020' if key==KEYS[1] else 'shorelineDynamics2006_2020';record=f'/coastlineKm/{row["town"]}' if key==KEYS[0] else f'/{family}/towns/{row["code"]}'
    if n is not None:
        if weighted(key,dimension):
            denominator=n['coastKm' if key==KEYS[1] else 'analysedKm'];num=n['protectedKm' if key==KEYS[1] else f[:-5]+'Km'];value=num/denominator*100;parts=dict(numerator=num,denominator=denominator,scale=100,numeratorPeriod=period,denominatorPeriod=period)
            if key==KEYS[2] and dimension!='total':pointer=f'/metrics/{key}/rows/{index}/parts/{CATEGORIES.index(f[:-5])}/value'
        else:
            value=n[f]
            if key!=KEYS[0]:pointer=f'/metrics/{key}/rows/{index}/coastDetail/{f}'
        if row.get('value') is None and dimension=='total':value=None
    if n is None and key!=KEYS[0]:record=f'/scope/notApplicableTownCodes/{NA.index(row["code"])}'
    evidence=[dict(kind='catalog_snapshot',path=engine.catalog_path,sha256=engine.catalog_hash,valuePointer=pointer),dict(ref,kind='source_snapshot',recordPointer=record),*extra]
    notes=['coast_source_universes_not_interchangeable','coast_four_littoral_three_not_applicable']
    if key==KEYS[2]:notes+=['shoreline_interval_not_annual_rate','shoreline_natural_low_coast_threshold_five_metres']
    if key==KEYS[1]:notes+=['rigid_defence_excludes_nourishment_not_effectiveness_or_damage_risk']
    if key==KEYS[0]:notes+=['istat_regional_national_totals_not_municipal_reference']
    return dict(ctx,**parts,metric=key,dimension=dimension,geography=row['code'],period=period,value=value,source=URLS[key],provenance=evidence,evidence=evidence,notApplicable=bool(row.get('notApplicable')),dataUnavailable=value is None and not bool(row.get('notApplicable')) or bool(row.get('dataUnavailable'))),notes

def benchmark(engine,key,scope,municipal):
    if key!=KEYS[1] or scope not in scopes(key,municipal['dimension']):raise ValueError('coast_benchmark_not_comparable')
    s,ref=engine.file(BENCHMARK);b=s['benchmarks'][key];meta=engine._catalog['metrics'][key]['meta']['benchmark']
    if s.get('schemaVersion')!=2 or s.get('sourceUrl')!=URLS[key] or s.get('qualityGate',{}).get('status')!='PASS' or b.get('year')!='2020' or b.get('unit')!='percent' or str(meta.get('year'))!='2020' or meta.get('url')!=URLS[key] or meta.get('sourceSnapshot')!=BENCHMARK:raise ValueError('coast_benchmark_reference_changed')
    n=s['components']['toscana' if scope=='tuscany' else 'italia'];num=n['protectedKm'];den=n['coastKm']
    if not finite(num) or not finite(den) or den<=0 or not 0<=num<=den:raise ValueError('coast_invalid_native_components')
    value=num/den*100;close(n['percent'],value);close(b[scope],value);close(meta[scope],value)
    evidence=[dict(ref,kind='source_snapshot',recordPointer='/components/'+('toscana' if scope=='tuscany' else 'italia')),dict(kind='catalog_snapshot',path=engine.catalog_path,sha256=engine.catalog_hash,valuePointer=f'/metrics/{key}/meta/benchmark/{scope}')]
    return dict(municipal,geography=scope,value=value,numerator=num,denominator=den,scale=100,provenance=evidence,evidence=evidence)
