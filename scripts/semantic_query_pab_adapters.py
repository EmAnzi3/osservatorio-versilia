"""Approved A-1 codes, portal activity length and frozen WFS status stay distinct."""
import hashlib,json,math
from semantic_operations import finite

PLAN=('pabProgrammedInterventionLength','pabProgrammedInterventions','pabProgrammedMaintenanceValue')
COUNTS=('pabInterventionsInProgress','pabInterventionsCompleted')
GROSS=('pabInProgressOperationalGrossValue','pabCompletedOperationalGrossValue')
KEYS=PLAN+COUNTS+GROSS
NATIVE='data/source-snapshots/bonifica-rischio-v126.json'
A1='data/source-snapshots/a3-pab-native-source-verification-2026.json'
STATUS='data/source-snapshots/bonifica-rischio-v126-status.json'
REGION='https://www.regione.toscana.it/-/manutenzione-del-reticolo-idrografico-piani-delle-attivit%C3%A0-dei-consorzi-di-bonifica'
PORTAL='https://cbtoscananord.it/comunicazione/pmo-manutenzione-mappa-navigabile/'
PDF_SHA='c97b4c3dc7d1ac838121c381a279a41335cc012fb3823d9d073f91d626c6c0d9'
RECORD_SHA='11f4159a315569587cafdbebc20df96139b9fb8794bbfcc68c9caa08b87ea15c'
WFS_SHA='81cb1aa82f7df4b4243f4372e35e5ab7bac2624e42ded67c25a6e1a911f4f322'
EXPORT_SHA={'Camaiore': 'eff12cc8be8022c4ac2e7021e6d63ca943419366b28f176d2a38ab6c788d2632', 'Forte dei Marmi': 'f13ad60580a7cf3d9b1d27d17523c6bc56c9c5e1a6280569a8b8d72cbbfe2997', 'Massarosa': '7a8081d2f4dac3d3e7f767e1b9537d83444be835223ee23fea4c0e9f72fe9cdb', 'Pietrasanta': '5e186ae4abb2b6eb060d47a9e0f113194edc4533ca99673f2685c3e0eff73fca', 'Seravezza': '5e34973da1dbfb93f3f2a90ce68d54ee4eec6fb309e87ffd4063eed4de774ec0', 'Stazzema': '49db01bdb5073120cec5fed3a74b298e8f59d2e44d2916fbe9112d1da6f5a006', 'Viareggio': 'b45b9aa23deda61c2f6b1f66ab63f48d12e35e5c856156c26983d50f4bb4b4f1'}
STAMP='2026-08-31T17:19:31+02:00'
STATES=('programmato','in_corso','completato')
RULE={'programmato':'lavori_inizio vuoto e lavori_fine vuoto','in_corso':'lavori_inizio valorizzato e lavori_fine vuoto','completato':'lavori_fine valorizzato'}

def phase(key):return 'in_corso' if key in (COUNTS[0],GROSS[0]) else 'completato'
def token(key,period):return '2026-08-31' if key not in PLAN and str(period)=='2026' else str(period)
def dimensions(key):return ['total',*(['share:operational'] if key in COUNTS else [])]
def weighted(key,dim):return key in COUNTS and dim=='share:operational'
def operations(key,dim):return ['compare','rank',*(['weighted_ratio'] if weighted(key,dim) else [])]
def selection_guard(key,dim,op):
    if dim not in dimensions(key):raise ValueError('pab_dimension_not_reviewed')
    if op in ('series','absolute_change','relative_change','percentage_points','trend'):raise ValueError('pab_history_not_frozen')
    if op=='correlation':raise ValueError('pab_approved_operational_or_risk_pair_not_reviewed')
    if op=='anomaly':raise ValueError('pab_anomaly_not_reviewed')
    if op=='benchmark_gap':raise ValueError('pab_regional_national_scope_not_certified')
    if op=='weighted_ratio' and not weighted(key,dim):raise ValueError('pab_verified_operational_share_required')

def close(a,b,tolerance=1e-8):
    if not finite(a) or not finite(b) or not math.isclose(a,b,rel_tol=0,abs_tol=tolerance):raise ValueError('pab_catalog_source_mismatch')
def count(v):return isinstance(v,int) and not isinstance(v,bool) and v>=0

def context(m,key,dim):
    if dim not in dimensions(key):raise ValueError('pab_dimension_not_reviewed')
    unit='km' if key==PLAN[0] else 'number' if key in (*COUNTS,PLAN[1]) else 'currency2'
    path=NATIVE if key in PLAN else STATUS;url=REGION if key in PLAN[1:] else PORTAL
    if m['meta'].get('unit')!=unit or str(m['meta'].get('year'))!='2026' or m['meta'].get('sourceMeta',{}).get('snapshot')!=path or m.get('sourceUrl')!=url:raise ValueError('pab_definition_or_reference_changed')
    basis='approved unique A-1 regional codes, assigned to native municipality; excluded A-3 and unallocated NULL' if key in PLAN[1:] else 'portal municipal export activity rows, repeated interventions on same physical reach retained' if key==PLAN[0] else 'municipal export matched WFS cb_pmo_lineare operational features; alternative punctual representation excluded'
    definition='planned activity kilometres, not unique physical network length' if key==PLAN[0] else 'approved planned intervention count' if key==PLAN[1] else 'approved planned EUR, not paid or liquidated spending' if key==PLAN[2] else phase(key)+' features / all operational features * 100, not approved A-1 execution rate' if weighted(key,dim) else phase(key)+' operational '+('feature counts' if key in COUNTS else 'importo_lordo EUR; not approved budget or payments')
    return dict(unit='percent' if weighted(key,dim) else unit,population=basis,definition=definition,method='frozen native A-1 records in cents' if key in PLAN[1:] else 'frozen municipal export sums' if key==PLAN[0] else 'frozen reviewed WFS aggregate; individual WFS IDs and actual work dates are not replayed by this adapter',frequency='annual' if key in PLAN else 'irregular_snapshot',periodBasis='PAB 2026 approved 30 March; municipal portal acquisition 31 August for activity length' if key in PLAN else 'work-status snapshot '+STAMP+'; annual PAB reference 2026, not year-end or live completion',adapter='pab/'+key+'/'+dim+'/v1')

def native(engine):
    if getattr(engine,'_pab_validation',None) is not None:return engine._pab_validation
    s,sref=engine.file(NATIVE);a,aref=engine.file(A1);t,tref=engine.file(STATUS)
    if s.get('schemaVersion')!=1 or s.get('referenceYear')!=2026 or s.get('snapshotVersion')!='2026-08-31-v2' or s['sources']['pabA1'].get('sha256')!=PDF_SHA or s['sources']['pabA1'].get('url')!=REGION or s['sources']['pabA1'].get('approval')!='DGR Toscana 367 del 30/03/2026':raise ValueError('pab_native_reference_changed')
    if a.get('referenceYear')!=2026 or a.get('profileId')!='regione-toscana-pab-annual' or a.get('status')!='NATIVE_SOURCE_ACQUIRED_BENCHMARK_UNRESOLVED' or a['remainingScope'].get('benchmarkCandidate') is not False:raise ValueError('pab_native_reference_changed')
    if not any(y.get('id')=='5508096' and y.get('sha256')==PDF_SHA for src in a['sources'] for y in src.get('attachments',[])):raise ValueError('pab_native_reference_changed')
    records=a['cb1A1']['records'];ids=[r[0] for r in records]
    if len(records)!=5328 or len(set(ids))!=5328 or any(len(r)!=5 or not isinstance(r[0],str) or not r[0].startswith(('2026CB1E','2026CB1P')) or not count(r[3]) or not count(r[4]) or not 10<=r[4]<=56 for r in records):raise ValueError('pab_duplicate_or_invalid_approved_records')
    if a['cb1A1'].get('recordFields')!=['code','town','province','amountCents','physicalPdfPage'] or a['cb1A1'].get('recordsSha256')!=RECORD_SHA or hashlib.sha256(json.dumps(records,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()!=RECORD_SHA:raise ValueError('pab_approved_records_changed')
    close(sum(r[3] for r in records),a['cb1A1']['amountCents']);close(len(records),a['cb1A1']['uniqueInterventions'])
    if [r for r in records if r[1]=='NULL']!=a['cb1A1']['unallocatedRecords']:raise ValueError('pab_unallocated_identity_changed')
    towns={r['name']:r['code'] for r in engine._catalog['towns']}
    if len(towns)!=7 or set(s['portalExports']['files'])!=set(towns) or set(s['pabA1ByTown'])!=set(towns) or set(t['byTown'])!=set(towns):raise ValueError('pab_native_cohort_changed')
    totals={}
    for name in towns:
        rs=[r for r in records if r[1]==name];n=s['pabA1ByTown'][name]
        if any(r[2]!='Lucca' for r in rs):raise ValueError('pab_native_identity_changed')
        close(n['interventions'],len(rs));close(n['programmedAmountEur'],sum(r[3] for r in rs)/100)
        totals[name]=dict(approvedCount=len(rs),approvedAmount=sum(r[3] for r in rs)/100,km=s['portalExports']['files'][name]['metres']/1000)
    exports=s['portalExports'];files=exports['files']
    if any(files[n].get('sha256')!=EXPORT_SHA[n] for n in files):raise ValueError('pab_native_reference_changed')
    for f in files.values():
        if not count(f['rows']) or not count(f['metres']) or not count(f['amount']) or not isinstance(f.get('sha256'),str) or len(f['sha256'])!=64:raise ValueError('pab_invalid_export_components')
    for field,total in [('rows','rowsTotal'),('metres','metresTotal'),('amount','amountCsvTotal')]:close(sum(f[field] for f in files.values()),exports[total])
    for key,field in zip(PLAN,('km','approvedCount','approvedAmount')):
        p=s['published'][key]
        if p.get('unit')!=('km-intervento','number','EUR')[PLAN.index(key)]:raise ValueError('pab_native_reference_changed')
        if set(p['byTown'])!=set(towns):raise ValueError('pab_native_cohort_changed')
        for name in towns:close(p['byTown'][name],totals[name][field])
        close(p['total'],math.fsum(n[field] for n in totals.values()))
    if t.get('schemaVersion')!=1 or t.get('referenceTimestamp')!=STAMP or t.get('snapshotVersion')!='2026-08-31-wfs-status-v1' or t['scope'].get('project')!='pmo_stato_lavori' or t['scope'].get('featureType')!='cb_pmo_lineare' or t.get('statusRule')!=RULE or t['wfs']['files']['cb_pmo_lineare.csv'].get('sha256')!=WFS_SHA:raise ValueError('pab_operational_reference_or_rule_changed')
    match=t['matching']
    if any(match.get(f)!=1265 for f in ('municipalExportRows','matchedRows','uniqueWfsFeatureIds')) or match.get('wfsCodeBreakdown')!={'2026CB1E':1244,'2026CB1P':16,'withoutCodiceRt':5} or t['punctualLayer'].get('featuresGlobal')!=251 or t['punctualLayer'].get('sharedIdsWithCbPmoLineare')!=251:raise ValueError('pab_operational_matching_changed')
    for name in towns:
        states=t['byTown'][name]
        if set(states)!=set(STATES):raise ValueError('pab_operational_state_partition_changed')
        for n in states.values():
            if not count(n['features']) or any(not finite(n[f]) or n[f]<0 for f in ('grossAmountEur','activityMetres')):raise ValueError('pab_invalid_operational_components')
        close(sum(n['features'] for n in states.values()),files[name]['rows'])
        totals[name]['features']=sum(n['features'] for n in states.values())
    for state in STATES:
        for f in ('features','grossAmountEur','activityMetres'):close(math.fsum(n[state][f] for n in t['byTown'].values()),t['aggregateSevenTowns'][state][f])
    close(sum(n['features'] for n in totals.values()),1265)
    close(math.fsum(t['aggregateSevenTowns'][state]['grossAmountEur'] for state in STATES),t['economicField']['sumGrossAmountEur'])
    close(t['economicField']['municipalCsvRoundedSumEur'],exports['amountCsvTotal']);close(t['economicField']['pabA1ApprovedProgrammedAmountEur'],s['published'][PLAN[2]]['total'])
    engine._pab_validation=(s,sref,a,aref,t,tref,totals)
    return engine._pab_validation

def observation(engine,key,index,dim,period,historical):
    m=engine._catalog['metrics'][key];row=m['rows'][index];ctx=context(m,key,dim)
    if period!=('2026' if key in PLAN else '2026-08-31'):raise ValueError('pab_period_not_frozen')
    s,sref,a,aref,t,tref,totals=native(engine);name=row['town'];n=totals.get(name)
    if n is None or not any(r['name']==name and r['code']==row['code'] for r in engine._catalog['towns']) or row['slug']!='-'.join(name.lower().split()) or row.get('notApplicable') or row.get('series') is not None or len(m['rows'])!=7 or len({r['code'] for r in m['rows']})!=7:raise ValueError('pab_public_identity_or_history_changed')
    refs=[];parts={}
    if key in PLAN:
        field=('km','approvedCount','approvedAmount')[PLAN.index(key)];expected=n[field]
        refs=[dict(sref,kind='source_snapshot',recordPointer='/portalExports/files/'+name if key==PLAN[0] else '/pabA1ByTown/'+name)]
        if key in PLAN[1:]:refs.append(dict(aref,kind='source_snapshot',recordPointer='/cb1A1/records'))
    else:
        field='features' if key in COUNTS else 'grossAmountEur';expected=t['byTown'][name][phase(key)][field]
        refs=[dict(tref,kind='source_snapshot',recordPointer='/byTown/'+name+'/'+phase(key)+'/'+field),dict(tref,kind='source_snapshot',recordPointer='/matching')]
    if row.get('value') is not None:close(row['value'],expected)
    value=row.get('value');pointer=f'/metrics/{key}/rows/{index}/value'
    if weighted(key,dim):
        if n['features']<=0:raise ValueError('pab_operational_denominator_not_positive')
        value=expected/n['features']*100;parts=dict(numerator=expected,denominator=n['features'],scale=100,numeratorPeriod=period,denominatorPeriod=period)
        refs.append(dict(tref,kind='source_snapshot',recordPointer='/byTown/'+name))
    evidence=[dict(kind='catalog_snapshot',path=engine.catalog_path,sha256=engine.catalog_hash,valuePointer=pointer)]+refs
    warnings=['pab_approved_codes_not_operational_features','pab_activity_km_not_unique_physical_network','pab_status_snapshot_not_live_or_year_end','pab_operational_gross_not_approved_budget_or_paid_spending','pab_punctual_representation_not_additive','pab_missing_geometry_no_physical_maintenance_share','pab_operational_share_not_approved_plan_execution_or_risk_reduction','pab_status_aggregate_without_individual_id_date_replay']
    return dict(ctx,**parts,metric=key,dimension=dim,geography=row['code'],period=period,value=value,source=REGION if key in PLAN[1:] else PORTAL,evidence=evidence,provenance=evidence,notApplicable=False,dataUnavailable=value is None),warnings
