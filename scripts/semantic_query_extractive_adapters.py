"""RTCave records, reported extraction and PRC planning: distinct frozen universes."""
from collections import Counter
import math
from semantic_operations import finite
KEYS=('extractiveSites','extractiveProduction','extractivePlanning')
NATIVE='data/source-snapshots/attivita-estrattive-v128.json'
LABELS=('2 settembre 2026','2025','PRC vigente · variante 2025')
PERIODS=('2026-09-02','2025','PRC-2025')
URLS=('https://cave.regione.toscana.it/api/v1/cave_public','https://www.regione.toscana.it/it/-/monitoraggio-del-piano-regionale-cave','https://www.regione.toscana.it/piano-regionale-cave')
PRODUCERS=('046028','046030')
SITE={'state_active':('stato','Attiva'),'state_inactive':('stato','Inattiva'),'state_suspended':('stato','Sospesa'),'state_expired':('stato','Scaduta'),'state_restoration':('stato','In ripristino'),'state_closed':('stato','Chiusa'),'state_nd':('stato',None),'type_ordinary':('tipologia','Cava Ordinaria'),'type_restoreworks':('tipologia','Opere di ripristino'),'type_recovery':('tipologia','Piano di recupero'),'prod_ornamental':('tipo_produzione','ORNAMENTALE'),'prod_industrial':('tipo_produzione','INDUSTRIALE'),'prod_construction':('tipo_produzione','COSTRUZIONE')}
PLANNING=tuple(c+'_'+u for c in ('g','gp','acc') for u in ('ha','pct','n'))+('mos','pmos','sed')

def close(a,b,tol=1e-8):
 if not finite(a) or not finite(b) or not math.isclose(a,b,rel_tol=0,abs_tol=tol):raise ValueError('extractive_catalog_source_mismatch')
def count(v):return isinstance(v,int) and not isinstance(v,bool) and v>=0

def token(key,period):return PERIODS[KEYS.index(key)] if str(period)==LABELS[KEYS.index(key)] else str(period)
def dimensions(key):return ['total',*('view:'+f for f in (SITE if key==KEYS[0] else PLANNING if key==KEYS[2] else [])),*(['share:g','share:gp','share:acc'] if key==KEYS[2] else [])]
def field(key,dim):return ('total' if key!=KEYS[2] else 'g_ha') if dim=='total' else dim.removeprefix('share:')+'_pct' if dim.startswith('share:') else dim.removeprefix('view:')
def weighted(key,dim):return key==KEYS[2] and dim in ('share:g','share:gp','share:acc')
def operations(key,dim):return ['compare','rank',*(['series'] if key==KEYS[1] else []),*(['weighted_ratio'] if weighted(key,dim) else [])]
def selection_guard(key,dim,op):
 if op in ('absolute_change','relative_change','percentage_points','trend') or op=='series' and key!=KEYS[1]:raise ValueError('extractive_history_continuity_not_reviewed')
 if op=='correlation':raise ValueError('extractive_universes_not_jointly_comparable')
 if op=='anomaly':raise ValueError('extractive_anomaly_not_reviewed')
 if op=='benchmark_gap':raise ValueError('extractive_totals_not_municipal_reference')
 if op=='weighted_ratio' and not weighted(key,dim):raise ValueError('extractive_verified_area_ratio_required')
def context(metric,key,dim):
 i=KEYS.index(key);meta=metric['meta'];f=field(key,dim)
 if str(meta.get('year'))!=LABELS[i] or meta.get('unit')!=('number','cubicMetres','hectares')[i] or metric.get('sourceUrl')!=URLS[i] or meta.get('sourceMeta',{}).get('snapshot')!=NATIVE:raise ValueError('extractive_definition_or_reference_changed')
 unit='percent' if field(key,dim).endswith('_pct') else 'number' if i==0 or f.endswith('_n') or f in ('mos','pmos','sed') else ('cubicMetres' if i==1 else 'hectares')
 populations=('distinct codice_rt RTCave records, not independent physical quarries','reported PRC information-obligation extraction, only reviewed basin-to-municipality correspondence','PRC union and intersection per separate planning category, not excavated or authorized surface')
 return dict(unit=unit,population=populations[i],definition=populations[i]+'; '+f+('; reconstructed ratio from rounded native area components' if weighted(key,dim) else '; published GIS percentage' if f.endswith('_pct') else ''),method='frozen RTCave records / PRC monitoring components / EPSG:3003 planning intersections, never interchangeable universes',frequency='annual' if i==1 else 'irregular_snapshot',periodBasis=('RTCave acquisition 2 September 2026','annual reported extraction 2019-2025; OPS 2019-2038 is planning, not extraction','PRC in force, variant 2025; acquisition 2 September 2026')[i],adapter='extractive/'+key+'/'+f+'/v1')
def available_periods(engine,key,dim,row):return [str(y) for y in engine.file(NATIVE)[0]['production'].get(row['code'],{}).get('years',[2025])]

def native(engine,key,row):
 s,ref=engine.file(NATIVE);towns={t['code']:t['name'] for t in engine._catalog['towns']};rows=engine._catalog['metrics'][key]['rows']
 if len(rows)!=7 or {r['code'] for r in rows}!=set(towns) or row['town']!=towns.get(row['code']) or row['slug']!='-'.join(row['town'].lower().split()) or row.get('notApplicable'):raise ValueError('extractive_row_identity_changed')
 if s.get('snapshotId')!='attivita-estrattive-v128' or s.get('retrievedAt')!='2026-09-02T10:49:00+00:00' or [s['sourceUrls'][f] for f in ('rtcave','prcMonitor','prc')]!=list(URLS):raise ValueError('extractive_native_reference_changed')
 rtc=s['rtcave'];records=rtc['records']
 if rtc.get('sha256')!='f507c5bb018619ac95bd8a681d24b9aaa3a584c41c3f8d67632b72dd685f62f2' or any(rtc.get(f)!=666 for f in ('regionalRecordCount','regionalUniqueCodiceRt','regionalUniqueIdCava')):raise ValueError('extractive_native_reference_changed')
 if len(records)!=90 or rtc.get('versiliaRecordCount')!=90 or any(not isinstance(r.get('codice_rt'),str) or not r['codice_rt'] or not count(r.get('id_cava')) for r in records) or len({r['codice_rt'] for r in records})!=90 or len({r['id_cava'] for r in records})!=90:raise ValueError('extractive_duplicate_or_invalid_records')
 for r in records:
  if r['cod_istat'] not in towns or r['nome_comune']!=towns[r['cod_istat']]:raise ValueError('extractive_native_identity_changed')
  for f in ('stato','tipologia','tipo_produzione'):
   if r.get(f) not in {v for basis,v in SITE.values() if basis==f}:raise ValueError('extractive_unreviewed_native_category')
 prc=s['prc']
 if set(prc['towns'])!=set(towns) or prc.get('crs')!='EPSG:3003' or prc.get('surfaceMethod')!='Union per categoria + intersection sui confini comunali ufficiali; conteggi per attribuzione comunale PRC.' or prc.get('sedNote')!='I SED sono una ricognizione PRC non esaustiva e sono usati solo come dettaglio.':raise ValueError('extractive_planning_method_changed')
 for code,n in prc['towns'].items():
  if n['town']!=towns[code] or not finite(n['municipalKm2']) or n['municipalKm2']<=0:raise ValueError('extractive_invalid_native_components')
  for c in ('g','gp','acc'):
   v=n[c]
   if len(v)!=3 or not count(v[0]) or not finite(v[1]) or not 0<=v[1]<=n['municipalKm2']*100:raise ValueError('extractive_invalid_native_components')
   close(v[1],round(v[1],3));close(n['municipalKm2'],round(n['municipalKm2'],2));close(v[2],round(v[2],3))
   # GIS percentage preceded rounding: propagate 0.0005 ha, 0.005 km2 and 0.0005 pp.
   close(v[2],v[1]/n['municipalKm2'],.00050001+.0005/n['municipalKm2']+v[1]*.005/(n['municipalKm2']*(n['municipalKm2']-.005)))
  if any(not count(n[f]) for f in ('mos','pmos','sed')):raise ValueError('extractive_invalid_native_components')
 for c in ('g','gp','acc'):
  a=prc['aggregate'][c];close(a[0],sum(n[c][0] for n in prc['towns'].values()));close(a[1],math.fsum(n[c][1] for n in prc['towns'].values()));close(a[2],a[1]/math.fsum(n['municipalKm2'] for n in prc['towns'].values()),.00050001)
 if set(s['production'])!=set(PRODUCERS):raise ValueError('extractive_production_cohort_changed')
 for code,n in s['production'].items():
  if n['town']!=towns[code] or n['years']!=list(range(2019,2026)) or len(n['values'])!=7 or len(n['components'])!=7:raise ValueError('extractive_production_period_or_identity_changed')
  for y,v,c in zip(n['years'],n['values'],n['components']):
   fields=('bacinoSeravezza',) if code==PRODUCERS[0] else ('bacinoStazzema','cardosoApuane')
   if c['year']!=y or any(not finite(c[f]) or c[f]<0 for f in fields) or not finite(v) or v<0:raise ValueError('extractive_invalid_native_components')
   close(v,math.fsum(c[f] for f in fields))
   if code==PRODUCERS[1]:close(c['total'],v)
  close(sum(m['value'] for m in n['materials2025']),n['values'][-1])
  if any(m['unit']!='cubicMetres' for m in n['materials2025']):raise ValueError('extractive_invalid_native_components')
 return s,ref

def observation(engine,key,index,dim,period,historical):
 row=engine._catalog['metrics'][key]['rows'][index];ctx=context(engine._catalog['metrics'][key],key,dim);s,ref=native(engine,key,row);f=field(key,dim);code=row['code'];value=None;components={};pointer=f'/metrics/{key}/rows/{index}/value';record='/production';unavailable=False
 if key!=KEYS[1] and period!=PERIODS[KEYS.index(key)]:raise ValueError('extractive_period_not_frozen')
 if key==KEYS[0]:
  rs=[r for r in s['rtcave']['records'] if r['cod_istat']==code]
  if row.get('series') is not None or {r['codice_rt']:r for r in row.get('extractiveDetail',{}).get('records',[])}!={r['codice_rt']:r for r in rs} or len(row.get('extractiveDetail',{}).get('records',[]))!=len(rs):raise ValueError('extractive_public_records_changed')
  counts={'total':len(rs),**{k:sum(r[basis]==label for r in rs) for k,(basis,label) in SITE.items()}}
  if [p['key'] for p in row['parts']]!=list(counts):raise ValueError('extractive_public_components_changed')
  for p in row['parts']:close(p['value'],counts[p['key']])
  if row['value'] is not None:close(row['value'],counts['total'])
  value=counts[f];pointer=f'/metrics/{key}/rows/{index}/parts/{list(counts).index(f)}/value';record='/rtcave/records'
 elif key==KEYS[2]:
  n=s['prc']['towns'][code]
  if row.get('prcDetail')!=n or row.get('series') is not None:raise ValueError('extractive_public_components_changed')
  counts={c+'_'+u:n[c][j] for c in ('g','gp','acc') for u,j in (('ha',1),('pct',2),('n',0))}
  if [p['key'] for p in row['parts']]!=list(counts):raise ValueError('extractive_public_components_changed')
  for p in row['parts']:close(p['value'],counts[p['key']])
  if row['value'] is not None:close(row['value'],n['g'][1])
  record='/prc/towns/'+code;pointer=f'/metrics/{key}/rows/{index}/prcDetail'
  if f in ('mos','pmos','sed'):value=n[f]
  elif weighted(key,dim):
   value=n[f.split('_')[0]][1]/n['municipalKm2'];components=dict(numerator=n[f.split('_')[0]][1],denominator=n['municipalKm2']*100,scale=100,numeratorPeriod=period,denominatorPeriod=period)
  else:value=counts[f]
 else:
  if period not in [str(y) for y in range(2019,2026)]:raise ValueError('extractive_period_not_frozen')
  n=s['production'].get(code)
  if n is None:
   if row.get('value') is not None or row.get('series') is not None or row.get('productionDetail') is not None or row.get('dataUnavailable') is not True:raise ValueError('extractive_missing_production_not_zero')
   unavailable=True
  else:
   if row.get('productionDetail')!=n or row.get('series')!={'years':n['years'],'values':n['values']}:raise ValueError('extractive_public_components_changed')
   if row['value'] is not None:close(row['value'],n['values'][-1])
   j=n['years'].index(int(period));value=n['values'][j];record+='/'+code+'/values/'+str(j)
   pointer=f'/metrics/{key}/rows/{index}/series/values/{j}'
 if dim=='total' and period==PERIODS[KEYS.index(key)] and row.get('value') is None:value=None
 evidence=[dict(kind='catalog_snapshot',path=engine.catalog_path,sha256=engine.catalog_hash,valuePointer=pointer),dict(ref,kind='source_snapshot',recordPointer=record)]
 notes=['extractive_records_not_physical_quarries','extractive_closed_inactive_sed_distinct','extractive_planning_not_excavated_or_authorized_surface','extractive_categories_not_additive','extractive_production_two_towns_not_full_versilia','extractive_sed_inventory_not_exhaustive','extractive_prc_ratio_reconstructed_from_rounded_area_components']
 return dict(ctx,**components,metric=key,dimension=dim,geography=code,period=period,value=value,source=URLS[KEYS.index(key)],provenance=evidence,evidence=evidence,notApplicable=False,dataUnavailable=unavailable or value is None),notes
