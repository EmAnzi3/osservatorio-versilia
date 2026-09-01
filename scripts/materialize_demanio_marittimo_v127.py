#!/usr/bin/env python3
"""Materializza il lotto Demanio marittimo v1.27.0 da snapshot SID congelato."""
from __future__ import annotations
import json, subprocess, sys
from collections import OrderedDict
from pathlib import Path
R=Path(__file__).resolve().parents[1]
SITE=R/'data/site-data.json'; REG=R/'data/source-registry.json'; STATE=R/'data/source-monitor-state.json'; SNAP=R/'data/source-snapshots/demanio-marittimo-v127.json'
FINAL=R/'scripts/finalize_catalog_release.py'; README=R/'README.md'; APP00=R/'assets/app-parts/00.txt'; APP03=R/'assets/app-parts/03.txt'; APP05=R/'assets/app-parts/05.txt'; PAGES=R/'.github/workflows/pages.yml'; CAT=R/'scripts/test_catalog_release_v116.py'
URL='https://dati.mit.gov.it/catalog/dataset/concessioni-demaniali-marittime-a-agosto-2026'; KEYS=('maritimeConcessions','maritimeConcessionFeesDue'); NA={'046018','046028','046030'}
OLD='20260831-v126-bonifica-rischio'; NEW='20260901-v127-demanio-marittimo'
def load(p): return json.loads(p.read_text(encoding='utf-8'))
def save(p,v): p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def repl(p,a,b,all_=True):
 t=p.read_text(encoding='utf-8')
 if b in t and a not in t:return
 if a not in t: raise RuntimeError(f'Token non trovato in {p}: {a[:80]}')
 p.write_text(t.replace(a,b) if all_ else t.replace(a,b,1),encoding='utf-8')
def meta(key,label,short,desc,unit,terms):
 return {'key':key,'theme':'ambiente','label':label,'shortLabel':short,'description':desc,'unit':unit,'year':'agosto 2026','source':'MIT / SID — Il Portale del Mare','polarity':'neutral','detailGroup':'coast','searchTerms':terms,'sourceMeta':{'snapshot':'data/source-snapshots/demanio-marittimo-v127.json','note':'Quattro Comuni costieri; Massarosa, Seravezza e Stazzema sono non applicabili e restano n.a.'},'compositeType':'securityMeasures','selectorLabel':'Lettura','comparisonReference':'aggregate','comparisonDifference':'absolute','comparisonLabel':'Versilia costiera','comparisonOverline':'Rispetto alla Versilia costiera','comparisonNote':'Il riferimento è la somma dei quattro Comuni costieri; i tre Comuni non costieri sono n.a. e non entrano nell’aggregato.'}
def narow(t,slug,parts): return {'town':t['name'],'code':t['code'],'slug':slug,'value':None,'formatted':'n.a.','series':None,'normalized':None,'benchmarkValue':None,'notApplicable':True,'applicabilityNote':'Comune non costiero: indicatore demaniale marittimo non applicabile.','parts':[{**p,'value':None} for p in parts]}
def apply_site(site,s):
 tm={t['code']:t for t in site['towns']}; sl={t['code']:t['name'].lower().replace(' ','-') for t in site['towns']}
 for m in site['metrics'].values():
  for r in m.get('rows',[]):
   if r.get('code') in sl and r.get('slug'): sl[r['code']]=r['slug']
 cp=[{'key':'total','label':'Concessioni totali','selectorLabel':'Totale','unit':'number'},{'key':'tourist','label':'Concessioni turistico-ricreative','selectorLabel':'Turistico-ricreative','unit':'number'}]
 fp=[{'key':'total','label':'Canoni dovuti totali','selectorLabel':'Totale','unit':'currency2'},{'key':'tourist','label':'Canoni dovuti turistico-ricreativi','selectorLabel':'Turistico-ricreative','unit':'currency2'}]
 cr=[]; fr=[]
 for code in [t['code'] for t in site['towns']]:
  t=tm[code]
  if code in NA: cr.append(narow(t,sl[code],cp)); fr.append(narow(t,sl[code],fp)); continue
  d=s['towns'][t['name']]; cparts=[{**cp[0],'value':d['totalConcessions']},{**cp[1],'value':d['touristRecreationalConcessions']}]; fparts=[{**fp[0],'value':d['canoneDovutoEur']},{**fp[1],'value':d['touristRecreationalCanoneDovutoEur']}]
  common={'town':t['name'],'code':code,'slug':sl[code],'series':None,'normalized':None,'coastDetail':dict(d)}
  cr.append({**common,'value':cparts[0]['value'],'formatted':str(cparts[0]['value']),'benchmarkValue':cparts[0]['value'],'parts':cparts})
  fr.append({**common,'value':fparts[0]['value'],'formatted':f"€ {d['canoneDovutoEur']:,.2f}".replace(',','X').replace('.',',').replace('X','.'),'benchmarkValue':fparts[0]['value'],'parts':fparts})
 v=s['versiliaCoast']
 concessions={'meta':meta(KEYS[0],'Concessioni demaniali marittime','Concessioni demaniali','Titoli concessori demaniali marittimi vigenti nello snapshot SID di agosto 2026, conteggiati una sola volta per identificativo idconc nel Comune costiero di ricaduta.','number',['concessioni demaniali','demanio marittimo','balneari','turistico ricreative','sid']),'sourceUrl':URL,'rows':cr,'aggregate':{'value':v['totalConcessions'],'label':'Versilia costiera · concessioni','parts':[{**cp[0],'value':v['totalConcessions']},{**cp[1],'value':v['touristRecreationalConcessions']}],'note':'Somma di Camaiore, Forte dei Marmi, Pietrasanta e Viareggio dopo deduplica per idconc.'},'normalizedAggregate':None,'method':{'type':'Elaborazione Osservatorio su open data MIT/SID','formula':'Conteggio dei titoli vigenti distinti per idconc. Selector Turistico-ricreative: stesso universo filtrato per uso = Turistico Ricreativo. Aggregato Versilia come somma dei quattro Comuni costieri.','caveat':'Una concessione non equivale a uno stabilimento balneare. Il campo amministrazione non è usato da solo per Viareggio: lo snapshot congela anche i titoli dell’Autorità Portuale Regione Toscana e della Capitaneria attribuiti dalla posizione SID. Nessuna geometria poligonale incompleta è trasformata in superficie.','coverage':'4/4 Comuni costieri + 3 n.a.','snapshot':'data/source-snapshots/demanio-marittimo-v127.json'}}
 fees={'meta':meta(KEYS[1],'Canoni demaniali dovuti','Canoni demaniali dovuti','Somma del canone demaniale dovuto registrato dal SID per i titoli vigenti attribuiti territorialmente al Comune. È un importo dovuto, non un incasso né un gettito comunale.','currency2',['canoni demaniali','canone dovuto','demanio marittimo','sid','balneari']),'sourceUrl':URL,'rows':fr,'aggregate':{'value':v['canoneDovutoEur'],'label':'Versilia costiera · canoni dovuti','parts':[{**fp[0],'value':v['canoneDovutoEur']},{**fp[1],'value':v['touristRecreationalCanoneDovutoEur']}],'note':'Somma del campo SID dovuto sui 799 titoli unici dei quattro Comuni costieri; non rappresenta somme incassate dai Comuni.'},'normalizedAggregate':None,'method':{'type':'Elaborazione Osservatorio su open data MIT/SID','formula':'Somma del campo dovuto una sola volta per idconc. Selector Turistico-ricreative: somma sul sottoinsieme uso = Turistico Ricreativo. Aggregato Versilia come somma dei quattro Comuni costieri.','caveat':'Il valore è il canone dovuto registrato nel SID per il 2026: non è incasso, gettito comunale o imposta regionale. Media, mediana e canone minimo sono dettagli descrittivi sul medesimo universo.','coverage':'4/4 Comuni costieri + 3 n.a.','snapshot':'data/source-snapshots/demanio-marittimo-v127.json'}}
 out=OrderedDict(); inserted=False
 for k,m in site['metrics'].items():
  if k in KEYS: continue
  out[k]=m
  if k=='rigidDefenceProtectedCoast': out[KEYS[0]]=concessions; out[KEYS[1]]=fees; inserted=True
 if not inserted: raise RuntimeError('Punto di inserimento Costa e mare non trovato')
 site['metrics']=out; theme=site['themes']['ambiente']; coast=next(x for x in theme['sections'] if x.get('key')=='costa-mare'); coast['description']='Balneazione, concessioni demaniali e assetto fisico del litorale nei quattro Comuni costieri.'; coast['metrics']=[k for k in coast['metrics'] if k not in KEYS]+list(KEYS); theme['metrics']=[k for sec in theme['sections'] for k in sec['metrics']]; site['version']='v1.27.0'; site['updated']='1 settembre 2026'
def apply_registry(r):
 r['expectedMetricCount']=177;r['expectedInlineMetricCount']=173;r['expectedExternalMetricCount']=4; p='mit-sid-demanio-irregular'; r.setdefault('sourceProfiles',{})[p]={'publisher':'Ministero delle Infrastrutture e dei Trasporti / SID','frequency':'irregular','frequencyLabel':'Irregolare','expectedRelease':'Quando il MIT pubblica un nuovo snapshot open data SID omogeneo','acquisitionMethod':'Download CSV/SHP MIT/SID, deduplica per idconc e fotografia comunale congelata nello snapshot della repository.','licenseName':'CC BY','licenseUrl':URL}; r.setdefault('sourceProfileByUrl',{})[URL]=p; r.setdefault('sourceUrlProfiles',{})[URL]=p
 for k in KEYS:r.setdefault('metricOverrides',{})[k]={'profile':p}
def apply_state(s):
 src=s.setdefault('sources',{}).setdefault(URL,{}); defaults={'url':URL,'ok':True,'status':200,'finalUrl':URL,'contentType':'text/html','contentLength':None,'etag':'','lastModified':'','contentSha256':'','hashTruncated':False,'error':'','metrics':list(KEYS),'roles':['primary'],'profileIds':['mit-sid-demanio-irregular'],'frequencies':['irregular']}
 for k,v in defaults.items():src.setdefault(k,v)
 for k in KEYS:s.setdefault('metrics',{})[k]={'publishedPeriod':'2026-08','checkedAt':'2026-09-01T16:30:00+00:00','observedLatestPeriod':'2026-08','status':'current'}
def patch_ui():
 t=APP03.read_text(encoding='utf-8'); marker="""    } else if (key === 'rigidDefenceProtectedCoast') {
      head = '<tr><th>Comune</th><th>Costa km</th><th>Protetta km</th><th>Quota</th></tr>';
      body = applicable.map(row => { const d=row.coastDetail; return `<tr><th>${html(row.town)}</th><td>${html(number3.format(d.coastKm))}</td><td>${html(number3.format(d.protectedKm))}</td><td>${html(formatValue(row.value,'percent'))}</td></tr>`; }).join('');
      note = 'Sono considerate le opere rigide della metodologia ISPRA 2020; i ripascimenti artificiali sono esclusi.';
    }
"""
 add=marker+"""    else if (key === 'maritimeConcessions') {
      head = '<tr><th>Comune</th><th>Totali</th><th>Turistico-ricreative</th><th>Quota TR</th><th>Licenze</th><th>Atti formali</th><th>Consegne</th></tr>';
      body = applicable.map(row => { const d=row.coastDetail, types=Object.fromEntries((d.titleTypeBreakdown||[]).map(x=>[x.label,x.count])); return `<tr><th>${html(row.town)}</th><td>${html(number0.format(d.totalConcessions))}</td><td>${html(number0.format(d.touristRecreationalConcessions))}</td><td>${html(number1.format(d.touristRecreationalShare))}%</td><td>${html(number0.format(types['Licenza']||0))}</td><td>${html(number0.format(types['Atto Formale']||0))}</td><td>${html(number0.format(types['Consegna']||0))}</td></tr>`; }).join('');
      note = 'Il dettaglio usa i titoli unici idconc. Una concessione classificata dal SID come stabilimento balneare non viene trasformata nel conteggio degli stabilimenti.';
    } else if (key === 'maritimeConcessionFeesDue') {
      head = '<tr><th>Comune</th><th>Dovuto totale</th><th>Dovuto TR</th><th>Media totale</th><th>Mediana totale</th><th>Canone minimo</th></tr>';
      body = applicable.map(row => { const d=row.coastDetail; return `<tr><th>${html(row.town)}</th><td>${html(formatValue(d.canoneDovutoEur,'currency2'))}</td><td>${html(formatValue(d.touristRecreationalCanoneDovutoEur,'currency2'))}</td><td>${html(formatValue(d.meanCanoneEur,'currency2'))}</td><td>${html(formatValue(d.medianCanoneEur,'currency2'))}</td><td>${html(number0.format(d.minimumCanoneCount))} · ${html(number1.format(d.minimumCanoneShare))}%</td></tr>`; }).join('');
      note = 'Sono canoni dovuti registrati dal SID, non incassi o gettito comunale. Media e mediana sono calcolate sul totale dei titoli del Comune.';
    }
"""
 if "key === 'maritimeConcessions'" not in t:
  if marker not in t:raise RuntimeError('Blocco Costa e mare non trovato')
  APP03.write_text(t.replace(marker,add,1),encoding='utf-8')
def patch_static():
 t=APP00.read_text(encoding='utf-8'); m="    rigidDefenceProtectedCoast: ['costa protetta', 'opere rigide', 'difesa costiera'],"; a=m+"\n    maritimeConcessions: ['concessioni demaniali', 'demanio marittimo', 'balneari', 'turistico ricreative', 'sid'],\n    maritimeConcessionFeesDue: ['canoni demaniali', 'canone dovuto', 'demanio marittimo', 'sid', 'balneari'],"
 if 'maritimeConcessions:' not in t:
  if m not in t:raise RuntimeError('Sinonimi Costa non trovati')
  APP00.write_text(t.replace(m,a,1),encoding='utf-8')
 t=APP05.read_text(encoding='utf-8'); m="['ISPRA','https://www.isprambiente.gov.it/'],"; a=m+"['MIT / SID — Il Portale del Mare','https://dati.mit.gov.it/catalog/dataset/concessioni-demaniali-marittime-a-agosto-2026'],"
 if 'MIT / SID — Il Portale del Mare' not in t:
  if m not in t:raise RuntimeError('Elenco fonti non trovato')
  APP05.write_text(t.replace(m,a,1),encoding='utf-8')
def patch_release():
 for a,b in [('catalogo pubblico v1.26.0','catalogo pubblico v1.27.0'),('VERSION = "v1.26.0"','VERSION = "v1.27.0"'),('UPDATED = "31 agosto 2026"','UPDATED = "1 settembre 2026"'),('EXPECTED_METRICS = 175','EXPECTED_METRICS = 177'),('EXPECTED_INLINE = 171','EXPECTED_INLINE = 173')]:repl(FINAL,a,b)
 for a,b in [('Versione dati corrente: **v1.26.0** — 31 agosto 2026.','Versione dati corrente: **v1.27.0** — 1 settembre 2026.'),('175 indicatori nel catalogo canonico: 171 con valori incorporati','177 indicatori nel catalogo canonico: 173 con valori incorporati'),('`indicatori/`: 171 pagine canoniche','`indicatori/`: 173 pagine canoniche'),('catalogo canonico dei 175 indicatori, con dati incorporati per 171','catalogo canonico dei 177 indicatori, con dati incorporati per 173'),('metadati dei 175 indicatori','metadati dei 177 indicatori'),('valida tutti i 175 indicatori canonici, la ripartizione fra 171 valori incorporati','valida tutti i 177 indicatori canonici, la ripartizione fra 173 valori incorporati'),('ciascuno dei 171 indicatori incorporati','ciascuno dei 173 indicatori incorporati')]:repl(README,a,b)
 for rel in ['assets/app.js','assets/export-v161.js','assets/ux-history.js','scripts/build_static_safe.py','scripts/build_static_brand.py']:repl(R/rel,OLD,NEW)
 repl(R/'service-worker.js','ov-pwa-'+OLD,'ov-pwa-'+NEW); repl(R/'scripts/build_static_brand.py','PWA_JS_REVISION = "catalog-v126"','PWA_JS_REVISION = "catalog-v127"')
 v126="      ['2026.08.31-v1.26.0','31 agosto 2026','175 indicatori complessivi in 11 temi, inclusi i 4 indicatori climatici. Lotto Bonifica e rischio idraulico: indicatori PAB 2026, reticolo in gestione DCRT 24/2025, opere idrauliche DGRT 1155/2021 e stato operativo degli interventi al 31 agosto 2026. Restano rinviati soltanto i km fisici unici manutenzionati e la relativa quota di reticolo, perché 49 feature operative non espongono geometria.'],"; v127="      ['2026.09.01-v1.27.0','1 settembre 2026','177 indicatori complessivi in 11 temi, inclusi i 4 indicatori climatici. Aggiunte Concessioni demaniali marittime e Canoni demaniali dovuti dallo snapshot MIT/SID agosto 2026, con selector Totale / Turistico-ricreative e copertura 4 Comuni costieri + 3 n.a. Superficie, metri e quota di litorale restano rinviati per incompletezza geometrica.'],"
 t=APP05.read_text(encoding='utf-8')
 if v127 not in t:
  if v126 not in t:raise RuntimeError('Changelog v1.26.0 non trovato')
  APP05.write_text(t.replace(v126,v127+'\n'+v126,1),encoding='utf-8')
 repl(CAT,'release v1.26.0','release v1.27.0'); repl(CAT,"'2026.08.31-v1.26.0' in app5 and '175 indicatori complessivi' in app5 and '2026.08.30-v1.25.0' in app5","'2026.09.01-v1.27.0' in app5 and '177 indicatori complessivi' in app5 and '2026.08.31-v1.26.0' in app5"); repl(CAT,"assert '**v1.26.0** — 31 agosto 2026' in readme and '175 indicatori' in readme and '171 con valori incorporati' in readme","assert '**v1.27.0** — 1 settembre 2026' in readme and '177 indicatori' in readme and '173 con valori incorporati' in readme")
def patch_workflow():
 t=PAGES.read_text(encoding='utf-8')
 if 'test_demanio_marittimo_v127.py' in t:return
 t=t.replace('          python scripts/test_costa_mare_v123.py\n','          python scripts/test_costa_mare_v123.py\n          python scripts/test_demanio_marittimo_v127.py\n',1).replace('          python -m json.tool data/source-snapshots/costa-mare-v123.json > /dev/null\n','          python -m json.tool data/source-snapshots/costa-mare-v123.json > /dev/null\n          python -m json.tool data/source-snapshots/demanio-marittimo-v127.json > /dev/null\n',1).replace('      - name: Validate Ambiente acqua e bonifiche\n','      - name: Validate Demanio marittimo\n        run: python scripts/test_demanio_marittimo_v127_browser.py --base http://127.0.0.1:8123/\n\n      - name: Validate Ambiente acqua e bonifiche\n',1); PAGES.write_text(t,encoding='utf-8')
def main():
 site=load(SITE); reg=load(REG); state=load(STATE); snap=load(SNAP); apply_site(site,snap);apply_registry(reg);apply_state(state);save(SITE,site);save(REG,reg);save(STATE,state);patch_ui();patch_static();patch_release();patch_workflow();subprocess.run([sys.executable,str(FINAL)],cwd=R,check=True);print('Demanio marittimo v1.27.0 materializzato: 2 card, 4/4 costieri + 3 n.a.')
if __name__=='__main__':main()
