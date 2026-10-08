"""Frozen SID titles and amounts due: territorial assignment, never cash receipts."""
import math
from semantic_operations import finite

KEYS=('maritimeConcessions','maritimeConcessionFeesDue')
COASTAL=('046005','046013','046024','046033')
NA=('046018','046028','046030')
NAMES=('Camaiore','Forte dei Marmi','Pietrasanta','Viareggio')
NA_NAMES=('Massarosa','Seravezza','Stazzema')
NATIVE='data/source-snapshots/demanio-marittimo-v127.json'
URL='https://dati.mit.gov.it/catalog/dataset/concessioni-demaniali-marittime-a-agosto-2026'
LABEL='agosto 2026'
PERIOD='2026-08'
CAP_IDS={'Camaiore':('2016Q003837',),'Forte dei Marmi':('2011T000201','1963O000009'),'Pietrasanta':('2016L009133',),'Viareggio':('1959T000009','1958Q000007','1958P000006','1963G000010','1991A000749','1953K000015','1953L000016','1960E000011','2017O005580','2017A050898','1971F000010','1976O000032','2024Y002752')}
CSV_SHA='66b492555b29147421693080555f7d29eb5f7469f2c3aa5bffe00aa5d27ad28d'
FIELD_MAP={KEYS[0]:{'total':'totalConcessions','view:tourist':'touristRecreationalConcessions','share:tourist':'touristShare','view:minimumCount':'minimumCanoneCount','share:minimum':'minimumShare','view:expiryMissing':'expiryMissing'},KEYS[1]:{'total':'canoneDovutoEur','view:touristDue':'touristRecreationalCanoneDovutoEur','share:touristDue':'touristDueShare','view:mean':'meanDue','view:touristMean':'touristMeanDue','view:median':'medianCanoneEur'}}
RATIOS={'touristShare':('touristRecreationalConcessions','totalConcessions',100),'minimumShare':('minimumCanoneCount','totalConcessions',100),'touristDueShare':('touristRecreationalCanoneDovutoEur','canoneDovutoEur',100),'meanDue':('canoneDovutoEur','totalConcessions',1),'touristMeanDue':('touristRecreationalCanoneDovutoEur','touristRecreationalConcessions',1)}
BREAKDOWNS=('usageBreakdown','categoryBreakdown','titleTypeBreakdown','grantingAuthorityBreakdown','expiryYearBreakdown')

def close(a,b,tolerance=1e-8):
    if not finite(a) or not finite(b) or not math.isclose(a,b,rel_tol=0,abs_tol=tolerance):raise ValueError('maritime_catalog_source_mismatch')

def count(v):return isinstance(v,int) and not isinstance(v,bool) and v>=0

def token(key,period):return PERIOD if str(period)==LABEL else str(period)

def dimensions(key):return list(FIELD_MAP[key])

def field(key,dimension):
    if dimension not in FIELD_MAP[key]:raise ValueError('maritime_dimension_not_reviewed')
    return FIELD_MAP[key][dimension]

def weighted(key,dimension):return field(key,dimension) in RATIOS

def operations(key,dimension):return ['compare','rank',*(['weighted_ratio'] if weighted(key,dimension) else [])]

def selection_guard(key,dimension,operation):
    f=field(key,dimension)
    if operation in ('series','absolute_change','relative_change','percentage_points','trend'):raise ValueError('maritime_previous_snapshots_not_harmonized')
    if operation=='correlation':raise ValueError('maritime_context_pair_not_reviewed')
    if operation=='anomaly':raise ValueError('maritime_anomaly_not_reviewed')
    if operation=='benchmark_gap':raise ValueError('maritime_benchmark_not_reviewed')
    if operation=='weighted_ratio' and not weighted(key,dimension):raise ValueError('maritime_median_not_additive' if f=='medianCanoneEur' else 'maritime_verified_ratio_required')

def context(metric,key,dimension):
    f=field(key,dimension);m=metric['meta']
    if m.get('unit')!=('number' if key==KEYS[0] else 'currency2') or str(m.get('year'))!=LABEL or metric.get('sourceUrl')!=URL or m.get('sourceMeta',{}).get('snapshot')!=NATIVE:raise ValueError('maritime_definition_or_reference_changed')
    unit='percent' if f in ('touristShare','minimumShare','touristDueShare') else 'number' if key==KEYS[0] else 'currency2'
    population='distinct SID idconc registered Vigente in August 2026; frozen municipal plus geolocated non-municipal territorial assignment'
    return dict(unit=unit,population=population,definition=population+'; '+f+'; EUR due per title' if f in ('meanDue','touristMeanDue') else population+'; '+f,method='frozen SID native counts and 2026 amounts due; ratios from own components; native median never averaged or reconstructed',frequency='irregular_snapshot',periodBasis='SID snapshot August 2026; 2026 annual amounts due, not observed receipts, municipal revenue or a flow over eight months',adapter='maritime/'+key+'/'+f+'/v1')

def identity(engine,key,row):
    rows=engine._catalog['metrics'][key]['rows']
    if len(rows)!=7 or {r['code'] for r in rows}!=set(COASTAL+NA):raise ValueError('maritime_public_cohort_changed')
    if not any(t['code']==row['code'] and t['name']==row['town'] for t in engine._catalog['towns']) or row['slug']!='-'.join(row['town'].lower().split()):raise ValueError('maritime_row_identity_changed')
    if row['code'] in NA:
        if row['town']!=NA_NAMES[NA.index(row['code'])] or row.get('notApplicable') is not True or row.get('value') is not None or row.get('series') is not None or row.get('coastDetail') is not None or any(p.get('value') is not None for p in row.get('parts',[])):raise ValueError('maritime_not_applicable_changed')
    elif row.get('notApplicable') or row.get('series') is not None:raise ValueError('maritime_applicability_or_history_changed')

def native(engine,key,row):
    identity(engine,key,row);s,ref=engine.file(NATIVE)
    if s.get('schemaVersion')!=1 or s.get('snapshotDate')!=PERIOD or s['source'].get('url')!=URL or s['source'].get('resourceCsv4326')!='41663e2c-a1a3-4685-953e-9025084363f5' or s['source']['files']['concessioni-epsg4326.csv'].get('sha256')!=CSV_SHA:raise ValueError('maritime_native_reference_changed')
    if s['coverage'].get('coastalMunicipalities')!=list(NAMES) or s['coverage'].get('notApplicable')!=list(NA_NAMES) or set(s['towns'])!=set(NAMES):raise ValueError('maritime_native_cohort_changed')
    quality=s['quality'];assign=quality['territorialAssignment'];cap=assign['nonMunicipalAssignments']['Capitaneria di Porto Viareggio'];port=assign['nonMunicipalAssignments']['Autorità Portuale Regione Toscana']
    if quality.get('allRowsStatus')!='Vigente' or quality.get('nationalCsvRows')!=29248 or quality.get('nationalDistinctIdconc')!=29242 or quality.get('perfectDuplicateRows')!=6 or s['source']['files']['concessioni-epsg4326.csv'].get('rows')!=29248 or assign.get('frozen') is not True:raise ValueError('maritime_deduplication_or_status_changed')
    if port.get('to')!='Viareggio' or port.get('count')!=165 or cap.get('total')!=17 or set(cap)!=set(('total',*NAMES)):raise ValueError('maritime_territorial_assignment_changed')
    ids=[v for name in NAMES for v in cap[name]]
    if len(ids)!=17 or len(set(ids))!=17 or any(not isinstance(v,str) or not v for v in ids) or any(set(cap[name])!=set(CAP_IDS[name]) for name in NAMES):raise ValueError('maritime_territorial_assignment_changed')
    for name,code in zip(NAMES,COASTAL):
        n=s['towns'][name]
        if n.get('code')!=code:raise ValueError('maritime_row_identity_changed')
        total=n['totalConcessions']
        if not count(total) or total<=0 or any(not count(n[f]) or not 0<=n[f]<=total for f in ('touristRecreationalConcessions','minimumCanoneCount','expiryMissing')):raise ValueError('maritime_invalid_native_components')
        for f in ('canoneDovutoEur','touristRecreationalCanoneDovutoEur','meanCanoneEur','medianCanoneEur'):
            if not finite(n[f]) or n[f]<0:raise ValueError('maritime_invalid_native_components')
            close(n[f],round(n[f],2))
        if n['touristRecreationalCanoneDovutoEur']>n['canoneDovutoEur']:raise ValueError('maritime_invalid_native_components')
        close(n['meanCanoneEur'],n['canoneDovutoEur']/total,.00500001)
        close(n['touristRecreationalShare'],n['touristRecreationalConcessions']/total*100,.00000051);close(n['minimumCanoneShare'],n['minimumCanoneCount']/total*100,.00000051)
        for basis in BREAKDOWNS:
            records=n[basis]
            if not isinstance(records,list) or any(not isinstance(r.get('label'),str) or not r['label'] or not count(r.get('count')) for r in records) or len({r['label'] for r in records})!=len(records):raise ValueError('maritime_invalid_native_components')
            close(sum(r['count'] for r in records),total)
        authority={r['label']:r['count'] for r in n['grantingAuthorityBreakdown']}
        expected={('Comune Forte Dei Marmi' if name=='Forte dei Marmi' else 'Comune '+name):assign['municipalAuthorityCounts'][name],'Capitaneria di Porto Viareggio':len(cap[name])}
        if name=='Viareggio':expected['Autorità Portuale Regione Toscana']=port['count']
        if authority!=expected or total!=sum(expected.values()):raise ValueError('maritime_territorial_assignment_changed')
        if next((r['count'] for r in n['usageBreakdown'] if r['label']=='Turistico Ricreativo'),None)!=n['touristRecreationalConcessions'] or next((r['count'] for r in n['expiryYearBreakdown'] if r['label']=='n.d.'),0)!=n['expiryMissing']:raise ValueError('maritime_catalog_source_mismatch')
    agg=s['versiliaCoast']
    for f in ('totalConcessions','touristRecreationalConcessions','minimumCanoneCount','canoneDovutoEur','touristRecreationalCanoneDovutoEur'):close(math.fsum(n[f] for n in s['towns'].values()),agg[f])
    close(assign['publishedDistinctIdconc'],agg['totalConcessions']);close(agg['meanCanoneEur'],agg['canoneDovutoEur']/agg['totalConcessions'],.00500001)
    close(agg['touristRecreationalShare'],agg['touristRecreationalConcessions']/agg['totalConcessions']*100,.00000051);close(agg['minimumCanoneShare'],agg['minimumCanoneCount']/agg['totalConcessions']*100,.00000051)
    if row['code'] in NA:return None,ref
    n=s['towns'][row['town']]
    if row.get('coastDetail')!=n or [p['key'] for p in row.get('parts',[])]!=['total','tourist']:raise ValueError('maritime_public_components_changed')
    fields=('totalConcessions','touristRecreationalConcessions') if key==KEYS[0] else ('canoneDovutoEur','touristRecreationalCanoneDovutoEur')
    for p,f in zip(row['parts'],fields):close(p['value'],n[f])
    if row.get('value') is not None:close(row['value'],n[fields[0]])
    return n,ref

def observation(engine,key,index,dimension,period,historical):
    m=engine._catalog['metrics'][key];row=m['rows'][index];ctx=context(m,key,dimension);f=field(key,dimension)
    if period!=PERIOD:raise ValueError('maritime_period_not_frozen')
    n,ref=native(engine,key,row);value=None;components={};pointer=f'/metrics/{key}/rows/{index}/value';record=f'/towns/{row["town"]}'
    if n is not None:
        if f in RATIOS:
            num,den,scale=RATIOS[f]
            if n[den]<=0:raise ValueError('maritime_ratio_denominator_not_positive')
            value=n[num]/n[den]*scale;components=dict(numerator=n[num],denominator=n[den],scale=scale,numeratorPeriod=period,denominatorPeriod=period)
            pointer=f'/metrics/{key}/rows/{index}/coastDetail';record+=f'/{num}'
        else:
            value=n[f];record+='/'+f
            pointer=f'/metrics/{key}/rows/{index}/parts/{1 if dimension in ("view:tourist","view:touristDue") else 0}/value' if dimension in ('total','view:tourist','view:touristDue') else f'/metrics/{key}/rows/{index}/coastDetail/{f}'
        if dimension=='total' and row.get('value') is None:value=None
    else:record=f'/coverage/notApplicable/{NA.index(row["code"])}'
    evidence=[dict(kind='catalog_snapshot',path=engine.catalog_path,sha256=engine.catalog_hash,valuePointer=pointer),dict(ref,kind='source_snapshot',recordPointer=record)]
    if n is not None:evidence+=[dict(ref,kind='source_snapshot',recordPointer='/quality/territorialAssignment')]
    notes=['sid_due_not_collected_or_municipal_revenue','sid_title_not_bathing_establishment','sid_incomplete_geometry_not_area_or_coastline','sid_four_coastal_three_not_applicable']
    if f in ('meanDue','touristMeanDue'):notes+=['sid_mean_derived_from_native_amounts_and_title_counts_not_mean_of_municipal_means']
    if f=='medianCanoneEur':notes+=['sid_native_median_not_additive_or_reconstructed']
    return dict(ctx,**components,metric=key,dimension=dimension,geography=row['code'],period=period,value=value,source=URL,provenance=evidence,evidence=evidence,notApplicable=bool(row.get('notApplicable')),dataUnavailable=value is None and not bool(row.get('notApplicable')) or bool(row.get('dataUnavailable'))),notes
