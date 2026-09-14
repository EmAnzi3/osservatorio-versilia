#!/usr/bin/env python3
"""Materializza Salute v1.40 da snapshot ufficiali ARS/Regione Toscana."""
from __future__ import annotations
import argparse,csv,hashlib,io,json,urllib.request,zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data/site-data.json'; REGISTRY=ROOT/'data/source-registry.json'
ARS_SNAPSHOT=ROOT/'data/source-snapshots/ars-salute-11-v140.json'
RSA_SNAPSHOT=ROOT/'data/source-snapshots/regione-toscana-rsa-accreditate-2025-v140.json'
ARS_PROFILE='ars-toscana-mixed'; RSA_PROFILE='regione-toscana-rsa'
TOWNS={'46005':'Camaiore','46013':'Forte dei Marmi','46018':'Massarosa','46024':'Pietrasanta','46028':'Seravezza','46030':'Stazzema','46033':'Viareggio','202M':'Versilia'}
EXPECTED_SHA={255:'3af05ca683f059b15f75895df669d7f74bbb2e39181b3f3357ad25db6beb1f46',261:'1cc87498861022532c3d8ad0d50b2829ba0f067a81fd929764b5766c53113263',268:'45d590d512801ffa0b36cfe77706562046ab871a63c5231318f0a3131c673dba',269:'2c8136cbe8d574e86394ae16e5268020c4389d90db73e2e0c8cc52352158b035',272:'5f1966a09022f3ca831ecd849db8c7db2bff704b0170b3b0ef974eee500b1b07',273:'b2617c533563ae69bf8e5d11883930eca4e4d318a871e1909e3b9aa27425e69f',1325:'e6c6f031b48dc90c37dce81e813a7016a242cb28c854a0506816c82000e2e061',1327:'982c17c547c1d39f62d62462fcd84c12e7a4418893b2be69fcb012b45e7cfb9c',1425:'e3409e64547f11dfd2c4cdd3452331f64a034644e9c5ef3496e2c4d1fd59dec1',1499:'bed981c6e4744de20accc3e815ff6eae7b8f3d24d8e4e09dba19ec5b9d6174ee',1606:'56045015354693fc766e06772bda154b34f9c4a2432dc42cec03172755ce8b2f'}
SPECS={
1499:dict(key='mortalityCancer',label='Mortalità per tumori',short='Mortalità per tumori',unit='per100k',unitLabel='ogni 100.000',strato=None,source='ARS Toscana / ISPRO — Registro di mortalità',polarity='negative',definition='Decessi per tumori nella popolazione residente.',numerator='Residenti deceduti per tumori nel periodo di riferimento.',denominator='Popolazione residente nel periodo di riferimento.',standard='Età; popolazione standard Europa 2013.'),
1327:dict(key='mortalityCirculatory',label='Mortalità per malattie del sistema circolatorio',short='Mortalità circolatoria',unit='per100k',unitLabel='ogni 100.000',strato=None,source='ARS Toscana / ISPRO — Registro di mortalità',polarity='negative',definition='Decessi per malattie del sistema circolatorio nella popolazione residente.',numerator='Residenti deceduti per malattie del sistema circolatorio nel periodo di riferimento.',denominator='Popolazione residente nel periodo di riferimento.',standard='Età; popolazione standard Europa 2013.'),
1606:dict(key='mortalityRespiratory',label="Mortalità per malattie dell’apparato respiratorio",short='Mortalità respiratoria',unit='per100k',unitLabel='ogni 100.000',strato=None,source='ARS Toscana / ISPRO — Registro di mortalità',polarity='negative',definition="Decessi per malattie dell’apparato respiratorio nella popolazione residente.",numerator="Residenti deceduti per malattie dell’apparato respiratorio nel periodo di riferimento.",denominator='Popolazione residente nel periodo di riferimento.',standard='Età; popolazione standard Europa 2013.'),
255:dict(key='hypertensionPrevalence',label='Prevalenza ipertensione',short='Ipertensione',unit='per1000',unitLabel='ogni 1.000',strato='totale',source='ARS Toscana — banca dati MaCro',polarity='negative',definition='Residenti di età 16+ identificati dalla banca dati MaCro con ipertensione.',numerator="Residenti 16+ prevalenti per ipertensione al 1° gennaio dell'anno di riferimento.",denominator="Popolazione residente di età 16+ al 1° gennaio.",standard='Età; popolazione standard Toscana 2006.'),
268:dict(key='copdPrevalence',label='Prevalenza BPCO',short='BPCO',unit='per1000',unitLabel='ogni 1.000',strato='totale',source='ARS Toscana — banca dati MaCro',polarity='negative',definition='Residenti di età 16+ identificati dalla banca dati MaCro con BPCO.',numerator="Residenti 16+ prevalenti per BPCO al 1° gennaio dell'anno di riferimento.",denominator="Popolazione residente di età 16+ al 1° gennaio.",standard='Età; popolazione standard Toscana 2006.'),
269:dict(key='ischemicHeartDiseasePrevalence',label='Prevalenza cardiopatia ischemica',short='Cardiopatia ischemica',unit='per1000',unitLabel='ogni 1.000',strato='totale',source='ARS Toscana — banca dati MaCro',polarity='negative',definition='Residenti di età 16+ identificati dalla banca dati MaCro con cardiopatia ischemica.',numerator="Residenti 16+ prevalenti per cardiopatia ischemica al 1° gennaio dell'anno di riferimento.",denominator="Popolazione residente di età 16+ al 1° gennaio.",standard='Età; popolazione standard Toscana 2006.'),
272:dict(key='heartFailurePrevalence',label='Prevalenza insufficienza cardiaca/scompenso',short='Scompenso cardiaco',unit='per1000',unitLabel='ogni 1.000',strato='totale',source='ARS Toscana — banca dati MaCro',polarity='negative',definition='Residenti di età 16+ identificati dalla banca dati MaCro con insufficienza cardiaca/scompenso.',numerator="Residenti 16+ prevalenti per insufficienza cardiaca/scompenso al 1° gennaio dell'anno di riferimento.",denominator="Popolazione residente di età 16+ al 1° gennaio.",standard='Età; popolazione standard Toscana 2006.'),
273:dict(key='priorStrokePrevalence',label='Prevalenza pregresso ictus',short='Pregresso ictus',unit='per1000',unitLabel='ogni 1.000',strato='totale',source='ARS Toscana — banca dati MaCro',polarity='negative',definition='Residenti di età 16+ identificati dalla banca dati MaCro con pregresso ictus.',numerator="Residenti 16+ prevalenti per pregresso ictus al 1° gennaio dell'anno di riferimento.",denominator="Popolazione residente di età 16+ al 1° gennaio.",standard='Età; popolazione standard Toscana 2006.'),
261:dict(key='permanentRsaAssisted',label='Anziani assistiti in RSA permanente',short='Anziani in RSA',unit='per1000',unitLabel='ogni 1.000',strato=None,source='ARS Toscana — assistenza residenziale',polarity='neutral',definition='Anziani residenti assistiti in RSA permanente con almeno un giorno di permanenza nell’anno.',numerator="Residenti di età superiore a 64 anni con almeno un giorno di permanenza in RSA permanente nell'anno.",denominator='Popolazione residente di età superiore a 64 anni.',standard='Tasso standardizzato per età pubblicato da ARS.'),
1425:dict(key='specialistVisits7Psr',label='Accessi per visite specialistiche – 7 specialità PSR',short='Visite specialistiche',unit='per1000',unitLabel='ogni 1.000',strato=None,source='ARS Toscana — RT Prestazioni ambulatoriali (SPA)',polarity='neutral',definition='Accessi dei residenti alle visite specialistiche comprese nelle 7 specialità del PSR.',numerator='Numero di accessi per le 7 specialità nell’anno di riferimento, per residenza del paziente.',denominator='Popolazione residente nell’anno di riferimento.',standard='Tasso standardizzato per età pubblicato da ARS.'),
1325:dict(key='diagnosticImagingServices',label='Accessi per prestazioni di diagnostica per immagini',short='Diagnostica per immagini',unit='per1000',unitLabel='ogni 1.000',strato=None,source='ARS Toscana — RT Prestazioni ambulatoriali (SPA)',polarity='neutral',definition='Accessi dei residenti a prestazioni di diagnostica per immagini.',numerator='Numero di accessi per diagnostica per immagini nell’anno di riferimento, per residenza del paziente.',denominator='Popolazione residente nell’anno di riferimento.',standard='Tasso standardizzato per età pubblicato da ARS.'),}
EXPECTED_PERIODS={1499:('2002-2011','2013-2022',12),1327:('2002-2011','2013-2022',12),1606:('2002-2011','2013-2022',12),255:('2015','2025',11),268:('2015','2025',11),269:('2015','2025',11),272:('2015','2025',11),273:('2015','2025',11),261:('2016','2024',9),1425:('2010','2025',16),1325:('2010','2025',16)}
RSA_VALUES={'Camaiore':5,'Forte dei Marmi':0,'Massarosa':0,'Pietrasanta':2,'Seravezza':2,'Stazzema':0,'Viareggio':4}

def load(p): return json.loads(p.read_text(encoding='utf-8'))
def save(p,v): p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def parse_num(x,integer=False):
 s=str(x or '').strip()
 if not s:return None
 s=s.replace('.','').replace(',','.') if ',' in s and '.' in s else s.replace(',','.')
 v=float(s); return int(v) if integer else v

def csv_bytes_from_export(iid):
 req=urllib.request.Request(f'https://www.ars.toscana.it/banche-dati/actions/esporta.php?indicatore={iid}',headers={'User-Agent':'OsservatorioVersilia-source-audit/1.0','Accept-Language':'it-IT,it;q=0.9'})
 with urllib.request.urlopen(req,timeout=120) as r: payload=r.read()
 try:
  with zipfile.ZipFile(io.BytesIO(payload)) as z:
   names=z.namelist(); csvname=next((n for n in names if n.lower().endswith('.csv')),None)
   if csvname:return z.read(csvname)
   nested=next((n for n in names if n.lower().endswith('.zip')),None)
   if nested:
    with zipfile.ZipFile(io.BytesIO(z.read(nested))) as z2:
     csvname=next(n for n in z2.namelist() if n.lower().endswith('.csv')); return z2.read(csvname)
 except zipfile.BadZipFile: pass
 raise RuntimeError(f'ARS {iid}: export ZIP/CSV non leggibile')

def refresh_ars():
 out={'schemaVersion':1,'version':'salute-ars-v140','retrieved':'2026-09-14','publisher':'ARS Toscana','versiliaAggregate':{'geographyCode':'202M','method':'Aggregato ufficiale Zona Versilia; nessuna media comunale.'},'indicators':{}}
 for iid,spec in SPECS.items():
  raw=csv_bytes_from_export(iid); sha=hashlib.sha256(raw).hexdigest()
  if sha!=EXPECTED_SHA[iid]: raise RuntimeError(f'ARS {iid}: SHA dati.csv inatteso {sha}')
  reader=csv.DictReader(io.StringIO(raw.decode('utf-8-sig')))
  required={'id_indicatore','anno','codice_geografia','geografia','den','num','misura_grezza','misura_standardizzata','liminf','limsup','sesso','strato1','strato2'}
  if not required.issubset(reader.fieldnames or []): raise RuntimeError(f'ARS {iid}: schema inatteso')
  rows=[]
  for row in reader:
   code=str(row['codice_geografia']).strip(); sex=str(row['sesso']).strip().lower(); strato=str(row['strato1']).strip().lower()
   if code not in TOWNS or sex!='totale' or str(row['id_indicatore']).strip()!=str(iid): continue
   if spec['strato'] is not None and strato!=spec['strato']: continue
   if spec['strato'] is None and strato not in ('','totale'): continue
   rows.append({'period':str(row['anno']).strip(),'geoCode':code,'geography':TOWNS[code],'den':parse_num(row['den'],True),'num':parse_num(row['num'],True),'raw':parse_num(row['misura_grezza']),'standardized':parse_num(row['misura_standardizzata']),'ci95Low':parse_num(row['liminf']),'ci95High':parse_num(row['limsup'])})
  period_sets=[{r['period'] for r in rows if r['geography']==geo} for geo in TOWNS.values()]
  periods=sorted(set.intersection(*period_sets),key=lambda s:(int(s.split('-')[0]),s))
  first,last,count=EXPECTED_PERIODS[iid]
  if (periods[0],periods[-1],len(periods))!=(first,last,count): raise RuntimeError(f'ARS {iid}: periodi inattesi {periods}')
  series={}
  for geo in TOWNS.values():
   vals=[next((r for r in rows if r['geography']==geo and r['period']==p),None) for p in periods]
   if any(v is None for v in vals): raise RuntimeError(f'ARS {iid}: serie incompleta {geo}')
   if any(v['standardized'] is None or v['ci95Low'] is None or v['ci95High'] is None for v in vals): raise RuntimeError(f'ARS {iid}: misura standardizzata/IC mancante {geo}')
   series[geo]=vals
  out['indicators'][str(iid)]={'indicatorId':iid,'key':spec['key'],'label':spec['label'],'indicatorUrl':f'https://www.ars.toscana.it/banche-dati/dettaglio_indicatore-{iid}','exportUrl':f'https://www.ars.toscana.it/banche-dati/actions/esporta.php?indicatore={iid}','sex':'totale','strato1':spec['strato'],'measurementField':'misura_standardizzata','unit':spec['unitLabel'],'definition':spec['definition'],'numerator':spec['numerator'],'denominator':spec['denominator'],'standardization':spec['standard'],'periods':periods,'coverage':'7/7','sourceFile':{'name':f'{iid}-dati.csv','sha256':sha,'bytes':len(raw)},'series':series}
 save(ARS_SNAPSHOT,out)

def write_rsa_snapshot():
 save(RSA_SNAPSHOT,{'schemaVersion':1,'version':'rsa-accreditate-2025-v140','retrieved':'2026-09-14','publisher':'Regione Toscana','indicator':{'key':'accreditedRsaCount','label':'RSA accreditate presenti nel Comune','year':'2025','unit':'strutture','sourceUrl':'https://servizi.toscana.it/RT/RSA/','note':'Presenza territoriale di strutture accreditate; non misura posti letto, capacità o convenzionamento SSR.'},'series':RSA_VALUES,'versilia':{'value':sum(RSA_VALUES.values()),'method':'Somma delle strutture presenti nei sette Comuni.'}})

def fmt(v,label):
 s=f'{v:,.2f}'.replace(',','X').replace('.',',').replace('X','.')
 return f'{s} {label}'
def add_after(items,anchor,additions):
 clean=[x for x in items if x not in additions]; pos=clean.index(anchor)+1 if anchor in clean else len(clean); return clean[:pos]+additions+clean[pos:]

def validate_snapshots(ars,rsa):
 if set(map(int,ars.get('indicators',{})))!=set(SPECS): raise RuntimeError('Snapshot ARS: indicatori inattesi')
 if rsa.get('series')!=RSA_VALUES or rsa.get('versilia',{}).get('value')!=13: raise RuntimeError('Snapshot RSA: valori inattesi')
 for iid,spec in SPECS.items():
  x=ars['indicators'][str(iid)]
  if x.get('coverage')!='7/7' or x.get('sex')!='totale' or x.get('measurementField')!='misura_standardizzata': raise RuntimeError(f'ARS {iid}: gate metadata fallito')
  if x.get('sourceFile',{}).get('sha256')!=EXPECTED_SHA[iid]: raise RuntimeError(f'ARS {iid}: hash snapshot inatteso')

def metric_from_ars(iid,spec,src,town_meta):
 periods=src['periods']; latest=periods[-1]; rows=[]
 for town,base in town_meta.items():
  cells=src['series'][town]; values=[round(float(c['standardized'])+1e-12,2) for c in cells]; value=values[-1]
  rows.append({'town':town,'code':base['code'],'slug':base['slug'],'value':value,'formatted':fmt(value,spec['unitLabel']),'series':{'years':periods,'values':values},'normalized':None,'benchmarkValue':value})
 vcells=src['series']['Versilia']; vvalues=[round(float(c['standardized'])+1e-12,2) for c in vcells]; v=vvalues[-1]
 return {'meta':{'key':spec['key'],'theme':'salute','label':spec['label'],'shortLabel':spec['short'],'description':spec['definition']+' Tasso standardizzato per età pubblicato da ARS.','unit':spec['unit'],'year':latest.replace('-', '–'),'source':spec['source'],'polarity':spec['polarity'],'sourceMeta':{'publisher':'ARS Toscana','indicatorId':iid,'measurement':'misura_standardizzata','snapshot':'data/source-snapshots/ars-salute-11-v140.json'}},'sourceUrl':src['indicatorUrl'],'sourceUrls':{'indicator':src['indicatorUrl'],'export':src['exportUrl']},'rows':rows,'aggregate':{'value':v,'formatted':fmt(v,spec['unitLabel']),'label':'Valore ARS Versilia','note':'Aggregato Zona Versilia pubblicato direttamente da ARS Toscana; non è una media dei tassi comunali.','series':{'years':periods,'values':vvalues}},'normalizedAggregate':None,'history':{'periods':periods,'coverage':'7/7','sex':'totale','measurement':'misura_standardizzata','confidenceIntervals':'95% nello snapshot','snapshot':'data/source-snapshots/ars-salute-11-v140.json'},'method':{'type':'Dato ufficiale ARS Toscana','formula':'Valore standardizzato pubblicato dalla fonte, senza trasformazioni statistiche dell’Osservatorio.','definition':src['definition'],'numerator':src['numerator'],'denominator':src['denominator'],'standardization':src['standardization'],'caveat':'Nessuna stima, interpolazione o media comunale. Grezzo, standardizzato, IC 95%, numeratore e denominatore sono conservati nello snapshot.','coverage':'7/7'}}

def apply_overlay():
 data=load(DATA); registry=load(REGISTRY); ars=load(ARS_SNAPSHOT); rsa=load(RSA_SNAPSHOT); validate_snapshots(ars,rsa)
 population_rows=data['metrics']['population']['rows']; town_meta={r['town']:r for r in population_rows}; expected=set(RSA_VALUES)
 if set(town_meta)!=expected: raise RuntimeError('Perimetro dei sette Comuni inatteso')
 for iid,spec in SPECS.items():
  if spec['key'] in data['metrics']: raise RuntimeError(f"Metrica già presente: {spec['key']}")
  data['metrics'][spec['key']]=metric_from_ars(iid,spec,ars['indicators'][str(iid)],town_meta)
 rows=[]
 for town,base in town_meta.items():
  value=RSA_VALUES[town]; rows.append({'town':town,'code':base['code'],'slug':base['slug'],'value':value,'formatted':f'{value} strutture' if value!=1 else '1 struttura','series':{'years':[2025],'values':[value]},'normalized':None,'benchmarkValue':value})
 data['metrics']['accreditedRsaCount']={'meta':{'key':'accreditedRsaCount','theme':'salute','label':'RSA accreditate presenti nel Comune','shortLabel':'RSA accreditate','description':'Numero di Residenze sanitarie assistenziali accreditate presenti nel territorio comunale.','unit':'count','year':'2025','source':'Regione Toscana — elenco RSA accreditate','polarity':'neutral','sourceMeta':{'publisher':'Regione Toscana','snapshot':'data/source-snapshots/regione-toscana-rsa-accreditate-2025-v140.json'}},'sourceUrl':'https://servizi.toscana.it/RT/RSA/','rows':rows,'aggregate':{'value':13,'formatted':'13 strutture','label':'Totale nei 7 Comuni','note':'Somma delle RSA accreditate presenti nei sette Comuni della Versilia.'},'normalizedAggregate':None,'method':{'type':'Conteggio da fonte ufficiale','formula':'Conteggio delle strutture accreditate presenti nel Comune.','caveat':'Non misura posti letto, capacità ricettiva né strutture convenzionate SSR.','coverage':'7/7'}}
 theme=data['themes']['salute']; esiti=['mortalityCancer','mortalityCirculatory','mortalityRespiratory','hypertensionPrevalence','copdPrevalence','ischemicHeartDiseasePrevalence','heartFailurePrevalence','priorStrokePrevalence']; territorio=['permanentRsaAssisted','specialistVisits7Psr','diagnosticImagingServices','accreditedRsaCount']
 theme['metrics']=add_after(theme['metrics'],'mortalityAll',esiti[:3]); theme['metrics']=add_after(theme['metrics'],'chronicTotal',esiti[3:]); theme['metrics']=add_after(theme['metrics'],'elderlyHomeCare',territorio)
 sections={s['key']:s for s in theme.get('sections',[])}; sections['esiti']['metrics']=add_after(sections['esiti']['metrics'],'mortalityAll',esiti[:3]); sections['esiti']['metrics']=add_after(sections['esiti']['metrics'],'chronicTotal',esiti[3:]); sections['territorio']['metrics']=add_after(sections['territorio']['metrics'],'elderlyHomeCare',territorio)
 theme['description']='Speranza di vita, mortalità, cronicità, disabilità riconosciuta, emergenza, ricoveri, assistenza, specialistica e presìdi.'
 data['version']='v1.40.0'; data['release_version']='1.40.0'; data['updated']='14 settembre 2026'
 registry['expectedMetricCount']=len(data['metrics']); registry['expectedExternalMetricCount']=int(registry.get('expectedExternalMetricCount',4)); registry['expectedInlineMetricCount']=registry['expectedMetricCount']-registry['expectedExternalMetricCount']
 for iid,spec in SPECS.items():
  for url in (ars['indicators'][str(iid)]['indicatorUrl'],ars['indicators'][str(iid)]['exportUrl']): registry.setdefault('sourceProfileByUrl',{})[url]=ARS_PROFILE; registry.setdefault('sourceUrlProfiles',{})[url]=ARS_PROFILE
  registry.setdefault('metricOverrides',{})[spec['key']]={'profile':ARS_PROFILE}
 rsa_url='https://servizi.toscana.it/RT/RSA/'
 registry.setdefault('sourceProfiles',{})[RSA_PROFILE]={'publisher':'Regione Toscana','frequency':'annual_or_irregular','frequencyLabel':'Annuale o irregolare','expectedRelease':'Secondo aggiornamento dell’elenco regionale','acquisitionMethod':'Consultazione dell’elenco ufficiale regionale delle RSA accreditate; conteggio comunale senza stime.','licenseName':'Condizioni indicate dalla fonte','licenseUrl':''}
 registry.setdefault('sourceProfileByUrl',{})[rsa_url]=RSA_PROFILE; registry.setdefault('sourceUrlProfiles',{})[rsa_url]=RSA_PROFILE; registry.setdefault('metricOverrides',{})['accreditedRsaCount']={'profile':RSA_PROFILE}
 save(DATA,data); save(REGISTRY,registry)
 print(f"Salute v1.40 materializzata: {len(data['metrics'])} indicatori nel workspace")

def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--refresh-source',action='store_true'); ap.add_argument('--snapshot-only',action='store_true'); a=ap.parse_args()
 if a.refresh_source: refresh_ars(); write_rsa_snapshot()
 if not ARS_SNAPSHOT.exists() or not RSA_SNAPSHOT.exists(): raise RuntimeError('Snapshot Salute v1.40 mancanti')
 if not a.snapshot_only: apply_overlay()
if __name__=='__main__': main()
