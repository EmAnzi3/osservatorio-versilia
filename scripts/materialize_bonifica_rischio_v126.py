#!/usr/bin/env python3
"""Materializza i tre indicatori pubblicabili del Lotto 6 v1.26.0.

Il contratto è deliberatamente conservativo: usa soltanto i valori congelati
nello snapshot. Reticolo fisico, quota manutenzionata, stato lavori e opere
idrauliche restano rinviati finché non sono disponibili i vettori necessari al
clipping/deduplica o un'estrazione massiva dello stato lavori.
"""
from __future__ import annotations
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SITE=ROOT/'data/site-data.json'; REGISTRY=ROOT/'data/source-registry.json'; STATE=ROOT/'data/source-monitor-state.json'; SNAPSHOT=ROOT/'data/source-snapshots/bonifica-rischio-v126.json'
PAB_URL='https://www.regione.toscana.it/-/manutenzione-del-reticolo-idrografico-piani-delle-attivit%C3%A0-dei-consorzi-di-bonifica'
PORTAL_URL='https://cbtoscananord.it/comunicazione/pmo-manutenzione-mappa-navigabile/'
KEYS=('pabProgrammedInterventionLength','pabProgrammedInterventions','pabProgrammedMaintenanceValue')

def load(p): return json.loads(p.read_text(encoding='utf-8'))
def save(p,v): p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def it(v,d=0): return f'{v:,.{d}f}'.replace(',','X').replace('.',',').replace('X','.')
def town_index(site):
    sample=site['metrics']['landUse']['rows']
    return {r['town']:(r['code'],r['slug']) for r in sample}
def rows(site, values, formatter):
    index=town_index(site)
    return [{'town':t['name'],'code':index[t['name']][0],'slug':index[t['name']][1],'value':values[t['name']],'formatted':formatter(values[t['name']]),'series':None,'normalized':None,'benchmarkValue':values[t['name']]} for t in site['towns']]
def meta(key,label,short,desc,unit,source,terms,note):
    return {'key':key,'theme':'ambiente','label':label,'shortLabel':short,'description':desc,'unit':unit,'year':'2026','source':source,'polarity':'neutral','context':'Bonifica e manutenzione idraulica','searchTerms':terms,'sourceMeta':{'snapshot':'data/source-snapshots/bonifica-rischio-v126.json','note':note}}
def build_metrics(site,snap):
    pub=snap['published']; L=pub['pabProgrammedInterventionLength']['byTown']; N=pub['pabProgrammedInterventions']['byTown']; E=pub['pabProgrammedMaintenanceValue']['byTown']
    return {
      KEYS[0]:{'meta':meta(KEYS[0],'Lunghezza interventi PAB programmati','Interventi PAB · km-intervento','Somma delle lunghezze delle attività di manutenzione ordinaria programmate nel PAB 2026 nei sette Comuni. La misura è espressa in km-intervento: interventi ripetuti sullo stesso tratto vengono contati separatamente.','kmIntervention','Consorzio 1 Toscana Nord — Portale manutenzioni PAB 2026',['bonifica','pab','manutenzione','reticolo','corsi d’acqua','km-intervento'],'Il dato misura attività programmate e non chilometri fisici unici di reticolo.'),'sourceUrl':PORTAL_URL,'rows':rows(site,L,lambda v:it(v,3)+' km-intervento'),'aggregate':{'value':pub[KEYS[0]]['total'],'label':'Versilia · totale programmato','note':'Somma dei km-intervento programmati nei sette Comuni; non rappresenta la lunghezza fisica unica del reticolo sottoposto a manutenzione.'},'normalizedAggregate':None,'method':{'type':'Elaborazione da export ufficiale Consorzio 1 Toscana Nord','formula':'Somma del campo Metri per Comune / 1.000.','caveat':'Se lo stesso tratto è oggetto di più interventi nell’anno, la sua lunghezza ricorre più volte: il dato è km-intervento, non km di reticolo fisico.','coverage':'7/7','snapshot':str(SNAPSHOT.relative_to(ROOT))}},
      KEYS[1]:{'meta':meta(KEYS[1],'Interventi PAB programmati','Interventi PAB programmati','Numero di interventi di manutenzione ordinaria programmati nel PAB 2026, conteggiati tramite il codice univoco dell’Allegato A-1 per i sette Comuni.','number','Regione Toscana / Consorzio 1 Toscana Nord — PAB 2026, Allegato A-1',['bonifica','pab','interventi','manutenzione','allegato a-1'],'Conteggio dei codici univoci PAB 2026; non equivale al numero di righe degli export del portale.'),'sourceUrl':PAB_URL,'rows':rows(site,N,lambda v:it(v,0)),'aggregate':{'value':pub[KEYS[1]]['total'],'label':'Versilia · totale programmato','note':'Conteggio dei codici intervento univoci del PAB 2026 attribuiti ai sette Comuni.'},'normalizedAggregate':None,'method':{'type':'Conteggio da Allegato A-1 PAB 2026','formula':'Conteggio dei codici univoci 2026CB1E… associati ai sette Comuni.','caveat':'Programmazione approvata; non misura lo stato di avanzamento.','coverage':'7/7','snapshot':str(SNAPSHOT.relative_to(ROOT))}},
      KEYS[2]:{'meta':meta(KEYS[2],'Valore manutenzione PAB programmata','Valore PAB programmato','Valore economico degli interventi di manutenzione ordinaria programmati nel PAB 2026 per i sette Comuni, ricostruito dagli importi dell’Allegato A-1.','currency2','Regione Toscana / Consorzio 1 Toscana Nord — PAB 2026, Allegato A-1',['bonifica','pab','manutenzione','importi','valore','allegato a-1'],'Somma degli importi programmati; non rappresenta spesa liquidata, pagata o valore dei soli lavori completati.'),'sourceUrl':PAB_URL,'rows':rows(site,E,lambda v:'€ '+it(v,2)),'aggregate':{'value':pub[KEYS[2]]['total'],'label':'Versilia · valore programmato','note':'Somma degli importi PAB 2026 degli interventi univoci attribuiti ai sette Comuni.'},'normalizedAggregate':None,'method':{'type':'Somma da Allegato A-1 PAB 2026','formula':'Somma degli importi ufficiali associati ai codici univoci PAB 2026 dei sette Comuni.','caveat':'Importo programmato, non spesa sostenuta o valore eseguito.','coverage':'7/7','snapshot':str(SNAPSHOT.relative_to(ROOT))}}
    }
def main():
    site=load(SITE); reg=load(REGISTRY); state=load(STATE); snap=load(SNAPSHOT)
    assert snap['portalExports']['rowsTotal']==1265 and snap['portalExports']['metresTotal']==1004094
    assert snap['published'][KEYS[0]]['total']==1004.094
    assert snap['published'][KEYS[1]]['total']==1259
    assert snap['published'][KEYS[2]]['total']==5196433.08
    built=build_metrics(site,snap)
    site['metrics'].update(built)
    amb=site['themes']['ambiente']
    amb['description']='Ambiente, clima, costa, acqua, bonifiche, agricoltura, rifiuti e rischi del territorio.'
    terr=next(s for s in amb['sections'] if s['key']=='territorio')
    terr['description']='Consumo di suolo, esposizione idrogeologica e programmazione della manutenzione idraulica.'
    for k in KEYS:
        if k not in amb['metrics']: amb['metrics'].append(k)
        if k not in terr['metrics']: terr['metrics'].append(k)
    site['version']='v1.26.0'; site['updated']='31 agosto 2026'
    reg.setdefault('sourceProfiles',{})['cb1-pmo-2026']={'publisher':'Consorzio 1 Toscana Nord','frequency':'annual','frequencyLabel':'Annuale, secondo il Piano delle Attività di Bonifica','expectedRelease':'Dopo l’approvazione annuale del PAB e l’aggiornamento del portale manutenzioni','acquisitionMethod':'Export CSV comunali del portale manutenzioni; somma del campo Metri per Comune e conversione in km-intervento, senza deduplicare come reticolo fisico.','licenseName':'Condizioni indicate dal Consorzio 1 Toscana Nord','licenseUrl':'https://cbtoscananord.it/'}
    reg['sourceProfiles']['regione-toscana-pab-annual']={'publisher':'Regione Toscana / Consorzio 1 Toscana Nord','frequency':'annual','frequencyLabel':'Annuale','expectedRelease':'Dopo l’approvazione del PAB da parte della Giunta regionale','acquisitionMethod':'Lettura dell’Allegato A-1 approvato; conteggio dei codici intervento univoci e somma degli importi per Comune. Nessuna stima di avanzamento lavori.','licenseName':'Condizioni indicate da Regione Toscana e Consorzio 1 Toscana Nord','licenseUrl':'https://www.regione.toscana.it/open-data'}
    for url,profile in ((PORTAL_URL,'cb1-pmo-2026'),(PAB_URL,'regione-toscana-pab-annual')):
        reg.setdefault('sourceProfileByUrl',{})[url]=profile
        reg.setdefault('sourceUrlProfiles',{})[url]=profile
    reg.setdefault('metricOverrides',{}).update({KEYS[0]:{'profile':'cb1-pmo-2026'},KEYS[1]:{'profile':'regione-toscana-pab-annual'},KEYS[2]:{'profile':'regione-toscana-pab-annual'}})
    reg['expectedMetricCount']=169; reg['expectedInlineMetricCount']=165; reg['expectedExternalMetricCount']=4
    checked='2026-08-31T00:30:00+00:00'
    def source_state(url, metrics, profile):
        return {'url':url,'ok':True,'status':200,'finalUrl':url,'contentType':'text/html','contentLength':None,'etag':'','lastModified':'','contentSha256':'','hashTruncated':False,'error':'','metrics':metrics,'roles':['primary'],'profileIds':[profile],'frequencies':['annual']}
    state.setdefault('sources',{})[PORTAL_URL]=source_state(PORTAL_URL,[KEYS[0]],'cb1-pmo-2026')
    state['sources'][PAB_URL]=source_state(PAB_URL,[KEYS[1],KEYS[2]],'regione-toscana-pab-annual')
    for k in KEYS:
        state.setdefault('metrics',{})[k]={'publishedPeriod':'2026','checkedAt':checked,'observedLatestPeriod':'2026','status':'current'}
    state['checkedAt']=checked
    app0=ROOT/'assets/app-parts/00.txt'
    txt=app0.read_text(encoding='utf-8')
    formatter="      case 'kmIntervention': return `${number3.format(v)} km-intervento`;\n"
    if formatter not in txt:
        marker="      case 'hectaresPerFarm': return `${number2.format(v)} ha/azienda`;\n"
        if marker not in txt: raise RuntimeError('Punto di inserimento formatter km-intervento non trovato')
        txt=txt.replace(marker,marker+formatter,1)
        app0.write_text(txt,encoding='utf-8')
    app5=ROOT/'assets/app-parts/05.txt'
    txt=app5.read_text(encoding='utf-8')
    entry="      ['2026.08.31-v1.26.0','31 agosto 2026','169 indicatori complessivi in 11 temi, inclusi i 4 indicatori climatici. Aggiunto il lotto Bonifica e rischio idraulico con tre indicatori PAB 2026: km-intervento programmati, numero di interventi univoci e valore economico programmato; restano rinviati i dati che richiedono clipping del reticolo o estrazione massiva dello stato lavori.'],\n"
    if '2026.08.31-v1.26.0' not in txt:
        marker='    const versions = [\n'
        if marker not in txt: raise RuntimeError('Storico versioni non trovato')
        app5.write_text(txt.replace(marker,marker+entry,1),encoding='utf-8')
    save(SITE,site); save(REGISTRY,reg); save(STATE,state)
    print('Bonifica e rischio idraulico v1.26.0 materializzato: 3 indicatori pubblicabili; candidati GIS/stato lavori rinviati.')
if __name__=='__main__': main()
