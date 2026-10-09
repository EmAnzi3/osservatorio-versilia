"""Frozen SISBON administrative proceedings; never an estimate of contamination."""
import math
from semantic_operations import finite

KEYS=('remediationProceedings',)
NATIVE='data/source-snapshots/ambiente-acqua-v124-data.json'
MANIFEST='data/source-snapshots/ambiente-acqua-v124-manifest.json'
SUMMARY='data/source-snapshots/ambiente-acqua-bonifiche-v124.json'
URL='https://sira.arpat.toscana.it/apex/f?p=SISBON:REPORT_PER_RT::CSV:IR_REPORT_GEOSCOPIO'
SHA='e5bd50e5b6a4a88b0f7bec0762b8719b69064ae1841bdbde925c5501e363dbcb'
PERIOD='2026-08-29'
ACTIVE=('10','40','50','60','70','120','135','140')
CLOSED=('200','210','220','230','280')
FIELDS={'total':'active','view:active':'active','view:closed':'closed','view:all':'all','share:active':'share'}

def token(key,period):return PERIOD if str(period)=='29 agosto 2026' else str(period)
def dimensions(key):return list(FIELDS)
def weighted(key,dim):return dim=='share:active'
def operations(key,dim):return ['compare','rank',*(['weighted_ratio'] if weighted(key,dim) else [])]
def selection_guard(key,dim,op):
    if dim not in FIELDS:raise ValueError('remediation_dimension_not_reviewed')
    if op in ('series','absolute_change','relative_change','percentage_points','trend'):raise ValueError('remediation_history_not_frozen')
    if op=='correlation':raise ValueError('remediation_pair_not_reviewed')
    if op=='anomaly':raise ValueError('remediation_anomaly_not_reviewed')
    if op=='benchmark_gap':raise ValueError('remediation_benchmark_not_reviewed')
    if op=='weighted_ratio' and not weighted(key,dim):raise ValueError('remediation_verified_ratio_required')

def close(a,b):
    if not finite(a) or not finite(b) or not math.isclose(a,b,rel_tol=0,abs_tol=1e-8):raise ValueError('remediation_catalog_source_mismatch')

def context(m,key,dim):
    if dim not in FIELDS:raise ValueError('remediation_dimension_not_reviewed')
    if m['meta'].get('unit')!='number' or m['meta'].get('year')!='29 agosto 2026' or m.get('sourceUrl')!=URL or m['meta'].get('sourceMeta',{}).get('snapshot')!=NATIVE:raise ValueError('remediation_definition_or_reference_changed')
    return dict(unit='percent' if weighted(key,dim) else 'number',population='distinct regional SISBON proceedings assigned to municipality in frozen snapshot',definition=FIELDS[dim]+' administrative proceedings; not currently contaminated sites, risk or remediation effectiveness',method='unique regional code; reviewed active/closed state partition, coincident coordinates never merged',frequency='weekly',periodBasis='administrative stock acquired 29 August 2026; not new cases or completed remediation during a year',adapter='remediation/'+FIELDS[dim]+'/v1')

def native(engine,key):
    s,ref=engine.file(NATIVE);m,mref=engine.file(MANIFEST);summary,sref=engine.file(SUMMARY)
    src=s.get('sources',{}).get('sisbon',{})
    if s.get('schemaVersion')!=2 or s.get('acquiredAt')!=PERIOD or src.get('url')!=URL or src.get('validatedCsvSha256')!=SHA or src.get('fetchedSha256')!=SHA or m.get('acquiredAt')!=PERIOD or m['sources']['sisbon'].get('csvSha256')!=SHA or m['sources']['sisbon'].get('snapshot')!=PERIOD or m['sources']['sisbon'].get('url')!=URL or summary['sources']['sisbon'].get('sha256')!=SHA:raise ValueError('remediation_native_reference_changed')
    if s['remediationProceedings'].get('closedStateCodes')!=list(CLOSED) or m.get('activeStateCodes')!=list(ACTIVE) or m.get('closedStateCodes')!=list(CLOSED):raise ValueError('remediation_state_partition_changed')
    towns={t['code']:t['name'] for t in engine._catalog['towns']};rows=engine._catalog['metrics'][key]['rows']
    if len(rows)!=7 or len(towns)!=7 or {r['code'] for r in rows}!=set(towns):raise ValueError('remediation_public_cohort_changed')
    rs=s['remediationProceedings']['procedures'];ids=[r.get('id') for r in rs]
    if len(ids)!=152 or len(set(ids))!=152 or any(not isinstance(i,str) or not i for i in ids):raise ValueError('remediation_duplicate_or_invalid_id')
    counts={code:dict(active=0,closed=0,total=0) for code in towns}
    for r in rs:
        code=r.get('townCode');state=r.get('stateCode')
        if code not in towns:raise ValueError('remediation_native_identity_changed')
        if state not in ACTIVE+CLOSED or not r.get('procedureState','').startswith(state+'-'):raise ValueError('remediation_state_partition_changed')
        status='closed' if state in CLOSED else 'active'
        if r.get('status')!=status:raise ValueError('remediation_state_partition_changed')
        counts[code][status]+=1;counts[code]['total']+=1
    if summary['remediationProceedings']['countsByMunicipality']!=counts or summary['remediationProceedings']['versilia']!=m['versilia']['remediationProceedings'] or any(sum(n[f] for n in counts.values())!=m['versilia']['remediationProceedings'][f] for f in ('active','closed','total')):raise ValueError('remediation_catalog_source_mismatch')
    for row in rows:
        code=row['code'];rr=[r for r in rs if r['townCode']==code]
        if row['town']!=towns[code] or row['slug']!='-'.join(towns[code].lower().split()) or row.get('notApplicable') or row.get('series') is not None:raise ValueError('remediation_public_identity_or_history_changed')
        public=row.get('procedures',[])
        if len(public)!=len(rr) or {r['id']:r for r in public}!={r['id']:r for r in rr}:raise ValueError('remediation_public_records_changed')
        if [p['key'] for p in row.get('parts',[])]!=['active','closed']:raise ValueError('remediation_public_components_changed')
        for p in row['parts']:close(p['value'],counts[code][p['key']])
        if row.get('value') is not None:close(row['value'],counts[code]['active'])
    return counts,[(ref,'/remediationProceedings/procedures'),(mref,'/versilia/remediationProceedings'),(sref,'/remediationProceedings/countsByMunicipality')]

def observation(engine,key,index,dim,period,historical):
    row=engine._catalog['metrics'][key]['rows'][index];ctx=context(engine._catalog['metrics'][key],key,dim)
    if period!=PERIOD:raise ValueError('remediation_period_not_frozen')
    counts,refs=native(engine,key);n=counts[row['code']];f=FIELDS[dim];parts={}
    if f=='share':
        if n['total']<=0:raise ValueError('remediation_denominator_not_positive')
        value=n['active']/n['total']*100;parts=dict(numerator=n['active'],denominator=n['total'],scale=100,numeratorPeriod=period,denominatorPeriod=period)
    else:value=n['total' if f=='all' else f]
    if dim=='total' and row.get('value') is None:value=None
    pointer=f'/metrics/{key}/rows/{index}/'+('value' if dim=='total' else 'parts/0/value' if f=='active' else 'parts/1/value' if f=='closed' else 'procedures')
    evidence=[dict(kind='catalog_snapshot',path=engine.catalog_path,sha256=engine.catalog_hash,valuePointer=pointer)]+[dict(ref,kind='source_snapshot',recordPointer=p) for ref,p in refs]
    return dict(ctx,**parts,metric=key,dimension=dim,geography=row['code'],period=period,value=value,source=URL,evidence=evidence,provenance=evidence,notApplicable=False,dataUnavailable=value is None),['sisbon_proceeding_not_current_contamination_or_risk','sisbon_closed_not_necessarily_remediated','sisbon_administrative_stock_not_annual_flow','sisbon_regional_id_not_coordinates_is_identity','sisbon_active_share_not_remediation_effectiveness']
