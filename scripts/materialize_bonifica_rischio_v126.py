#!/usr/bin/env python3
"""Materializza gli indicatori verificati del Lotto 6 v1.26.0."""
from __future__ import annotations
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SITE=ROOT/'data/site-data.json'; REGISTRY=ROOT/'data/source-registry.json'; STATE=ROOT/'data/source-monitor-state.json'
SNAPSHOT=ROOT/'data/source-snapshots/bonifica-rischio-v126.json'; GIS=ROOT/'data/source-snapshots/bonifica-rischio-v126-gis.json'
PAB_URL='https://www.regione.toscana.it/-/manutenzione-del-reticolo-idrografico-piani-delle-attivit%C3%A0-dei-consorzi-di-bonifica'
PORTAL_URL='https://cbtoscananord.it/comunicazione/pmo-manutenzione-mappa-navigabile/'
RETICOLO_URL='https://www.regione.toscana.it/-/reticolo-idrografico-e-di-gestione'
OPERE_URL='https://www.regione.toscana.it/-/censimento-delle-opere-idrauliche'
KEYS=('pabProgrammedInterventionLength','pabProgrammedInterventions','pabProgrammedMaintenanceValue','managedReticulumLength','hydraulicWorksCensusElements')


def load(p): return json.loads(p.read_text(encoding='utf-8'))
def save(p,v): p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def it(v,d=0): return f'{v:,.{d}f}'.replace(',','X').replace('.',',').replace('X','.')
def town_index(site):
    sample=site['metrics']['landUse']['rows']
    return {r['town']:(r['code'],r['slug']) for r in sample}
def rows(site, values, formatter):
    index=town_index(site)
    return [{'town':t['name'],'code':index[t['name']][0],'slug':index[t['name']][1],'value':values[t['name']],'formatted':formatter(values[t['name']]),'series':None,'normalized':None,'benchmarkValue':values[t['name']]} for t in site['towns']]
def meta(key,label,short,desc,unit,year,source,terms,note,snapshot):
    return {'key':key,'theme':'ambiente','label':label,'shortLabel':short,'description':desc,'unit':unit,'year':year,'source':source,'polarity':'neutral','context':'Bonifica e manutenzione idraulica','searchTerms':terms,'sourceMeta':{'snapshot':snapshot,'note':note}}


def build_metrics(site,snap,gis):
    pub=snap['published']; L=pub['pabProgrammedInterventionLength']['byTown']; N=pub['pabProgrammedInterventions']['byTown']; E=pub['pabProgrammedMaintenanceValue']['byTown']
    R={town:item['km'] for town,item in gis['managedReticulum']['byTown'].items()}
    W={town:item['featurePresenceTotal'] for town,item in gis['hydraulicWorks']['byTown'].items()}
    base_snapshot=str(SNAPSHOT.relative_to(ROOT)); gis_snapshot=str(GIS.relative_to(ROOT))
    return {
      KEYS[0]:{'meta':meta(KEYS[0],'Lunghezza interventi PAB programmati','Interventi PAB · km-intervento','Somma delle lunghezze delle attività di manutenzione ordinaria programmate nel PAB 2026 nei sette Comuni. La misura è espressa in km-intervento: interventi ripetuti sullo stesso tratto vengono contati separatamente.','kmIntervention','2026','Consorzio 1 Toscana Nord — Portale manutenzioni PAB 2026',['bonifica','pab','manutenzione','reticolo','corsi d’acqua','km-intervento'],'Il dato misura attività programmate e non chilometri fisici unici di reticolo.',base_snapshot),'sourceUrl':PORTAL_URL,'rows':rows(site,L,lambda v:it(v,3)+' km-intervento'),'aggregate':{'value':pub[KEYS[0]]['total'],'label':'Versilia · totale programmato','note':'Somma dei km-intervento programmati nei sette Comuni; non rappresenta la lunghezza fisica unica del reticolo sottoposto a manutenzione.'},'normalizedAggregate':None,'method':{'type':'Elaborazione da export ufficiale Consorzio 1 Toscana Nord','formula':'Somma del campo Metri per Comune / 1.000.','caveat':'Se lo stesso tratto è oggetto di più interventi nell’anno, la sua lunghezza ricorre più volte: il dato è km-intervento, non km di reticolo fisico.','coverage':'7/7','snapshot':base_snapshot}},
      KEYS[1]:{'meta':meta(KEYS[1],'Interventi PAB programmati','Interventi PAB programmati','Numero di interventi di manutenzione ordinaria programmati nel PAB 2026, conteggiati tramite il codice univoco dell’Allegato A-1 per i sette Comuni.','number','2026','Regione Toscana / Consorzio 1 Toscana Nord — PAB 2026, Allegato A-1',['bonifica','pab','interventi','manutenzione','allegato a-1'],'Conteggio dei codici univoci PAB 2026; non equivale al numero di righe degli export del portale.',base_snapshot),'sourceUrl':PAB_URL,'rows':rows(site,N,lambda v:it(v,0)),'aggregate':{'value':pub[KEYS[1]]['total'],'label':'Versilia · totale programmato','note':'Conteggio dei codici intervento univoci del PAB 2026 attribuiti ai sette Comuni.'},'normalizedAggregate':None,'method':{'type':'Conteggio da Allegato A-1 PAB 2026','formula':'Conteggio dei codici univoci 2026CB1E… associati ai sette Comuni.','caveat':'Programmazione approvata; non misura lo stato di avanzamento.','coverage':'7/7','snapshot':base_snapshot}},
      KEYS[2]:{'meta':meta(KEYS[2],'Valore manutenzione PAB programmata','Valore PAB programmato','Valore economico degli interventi di manutenzione ordinaria programmati nel PAB 2026 per i sette Comuni, ricostruito dagli importi dell’Allegato A-1.','currency2','2026','Regione Toscana / Consorzio 1 Toscana Nord — PAB 2026, Allegato A-1',['bonifica','pab','manutenzione','importi','valore','allegato a-1'],'Somma degli importi programmati; non rappresenta spesa liquidata, pagata o valore dei soli lavori completati.',base_snapshot),'sourceUrl':PAB_URL,'rows':rows(site,E,lambda v:'€ '+it(v,2)),'aggregate':{'value':pub[KEYS[2]]['total'],'label':'Versilia · valore programmato','note':'Somma degli importi PAB 2026 degli interventi univoci attribuiti ai sette Comuni.'},'normalizedAggregate':None,'method':{'type':'Somma da Allegato A-1 PAB 2026','formula':'Somma degli importi ufficiali associati ai codici univoci PAB 2026 dei sette Comuni.','caveat':'Importo programmato, non spesa sostenuta o valore eseguito.','coverage':'7/7','snapshot':base_snapshot}},
      KEYS[3]:{'meta':meta(KEYS[3],'Reticolo idrografico in gestione','Reticolo in gestione','Lunghezza fisica del reticolo idrografico attribuito alla gestione del Consorzio 1 Toscana Nord all’interno del confine comunale Istat 2026.','km','2025','Regione Toscana — Reticolo idrografico e di gestione DCRT 24/2025',['bonifica','reticolo','corsi d’acqua','consorzio','toscana nord','gestione'],'Il reticolo è filtrato sui campi ufficiali COMPLR79=Toscana Nord e RETGESLR79=SI; la lunghezza è ricalcolata dopo il clipping comunale.',gis_snapshot),'sourceUrl':RETICOLO_URL,'rows':rows(site,R,lambda v:it(v,3)+' km'),'aggregate':{'value':gis['managedReticulum']['aggregateSevenTowns']['km'],'label':'Versilia · reticolo in gestione','note':'Lunghezza sul perimetro unito dei sette Comuni; non somma valori provinciali o UIO esterne al perimetro dell’Osservatorio.'},'normalizedAggregate':None,'method':{'type':'Elaborazione GIS da reticolo ufficiale DCRT 24/2025 e confini Istat 2026','formula':'Filtro COMPLR79=Toscana Nord e RETGESLR79=SI; intersezione con ciascun poligono comunale; ricalcolo della lunghezza della geometria risultante in EPSG:3003.','caveat':'Non viene riutilizzato il campo LENGTH dopo il clipping. Il controllo geometrico sul reticolo filtrato non rileva sovrapposizioni lineari significative.','coverage':'7/7','snapshot':gis_snapshot}},
      KEYS[4]:{'meta':meta(KEYS[4],'Elementi di opere idrauliche censiti','Opere idrauliche · elementi censiti','Numero di feature ufficiali del censimento regionale delle opere idrauliche che intersecano il territorio comunale, considerando separatamente elementi areali, lineari e puntuali.','number','2021','Regione Toscana — Ricognizione opere idrauliche DGRT 1155/2021',['opere idrauliche','argini','difese di sponda','briglie','soglie','casse di espansione','sfioratori'],'È un conteggio di elementi censiti, non una stima del numero di cantieri o interventi. Una feature che attraversa più Comuni compare in ciascuna scheda comunale.',gis_snapshot),'sourceUrl':OPERE_URL,'rows':rows(site,W,lambda v:it(v,0)),'aggregate':{'value':gis['hydraulicWorks']['aggregateSevenTowns']['uniqueSourceFeaturesTotal'],'label':'Versilia · elementi distinti censiti','note':'Conteggio deduplicato delle feature sorgente che intersecano l’unione dei sette Comuni: aree, linee e punti.'},'normalizedAggregate':None,'method':{'type':'Elaborazione GIS dal censimento opere idrauliche DGRT 1155/2021 e confini Istat 2026','formula':'Intersezione delle feature OPI areali, lineari e puntuali con ciascun Comune; somma delle presenze per la scheda comunale. L’aggregato Versilia è ricalcolato sulla geometria unita dei sette Comuni e deduplicato per feature sorgente.','caveat':'Il valore misura elementi cartografici censiti. Una struttura lineare può essere articolata in più feature e una feature di confine può appartenire a più schede comunali.','coverage':'7/7','snapshot':gis_snapshot}}
    }


def main():
    site=load(SITE); reg=load(REGISTRY); state=load(STATE); snap=load(SNAPSHOT); gis=load(GIS)
    assert snap['portalExports']['rowsTotal']==1265 and snap['portalExports']['metresTotal']==1004094
    assert snap['published'][KEYS[0]]['total']==1004.094 and snap['published'][KEYS[1]]['total']==1259 and snap['published'][KEYS[2]]['total']==5196433.08
    assert gis['managedReticulum']['aggregateSevenTowns']['km']==745.041751
    assert gis['hydraulicWorks']['aggregateSevenTowns']['uniqueSourceFeaturesTotal']==265
    built=build_metrics(site,snap,gis); site['metrics'].update(built)
    amb=site['themes']['ambiente']; amb['description']='Ambiente, clima, costa, acqua, bonifiche, agricoltura, rifiuti e rischi del territorio.'
    terr=next(s for s in amb['sections'] if s['key']=='territorio')
    terr['description']='Consumo di suolo, esposizione idrogeologica, reticolo in gestione, opere idrauliche e programmazione della manutenzione.'
    for k in KEYS:
        if k not in amb['metrics']: amb['metrics'].append(k)
        if k not in terr['metrics']: terr['metrics'].append(k)
    site['version']='v1.26.0'; site['updated']='31 agosto 2026'

    profiles=reg.setdefault('sourceProfiles',{})
    profiles['cb1-pmo-2026']={'publisher':'Consorzio 1 Toscana Nord','frequency':'annual','frequencyLabel':'Annuale, secondo il Piano delle Attività di Bonifica','expectedRelease':'Dopo l’approvazione annuale del PAB e l’aggiornamento del portale manutenzioni','acquisitionMethod':'Export CSV comunali del portale manutenzioni; somma del campo Metri per Comune e conversione in km-intervento, senza deduplicare come reticolo fisico.','licenseName':'Condizioni indicate dal Consorzio 1 Toscana Nord','licenseUrl':'https://cbtoscananord.it/'}
    profiles['regione-toscana-pab-annual']={'publisher':'Regione Toscana / Consorzio 1 Toscana Nord','frequency':'annual','frequencyLabel':'Annuale','expectedRelease':'Dopo l’approvazione del PAB da parte della Giunta regionale','acquisitionMethod':'Lettura dell’Allegato A-1 approvato; conteggio dei codici intervento univoci e somma degli importi per Comune. Nessuna stima di avanzamento lavori.','licenseName':'Condizioni indicate da Regione Toscana e Consorzio 1 Toscana Nord','licenseUrl':'https://www.regione.toscana.it/open-data'}
    profiles['regione-toscana-reticolo-2025']={'publisher':'Regione Toscana','frequency':'irregular','frequencyLabel':'Aggiornamento con deliberazione del Consiglio regionale','expectedRelease':'Alla revisione del reticolo idrografico e di gestione','acquisitionMethod':'Download shapefile DCRT 24/2025, filtro del reticolo in gestione del Consorzio 1 Toscana Nord, clipping sui confini comunali Istat 2026 e ricalcolo geometrico delle lunghezze.','licenseName':'Open data Regione Toscana','licenseUrl':'https://www.regione.toscana.it/open-data'}
    profiles['regione-toscana-opere-idrauliche-2021']={'publisher':'Regione Toscana','frequency':'irregular','frequencyLabel':'Ricognizione normativa non annuale','expectedRelease':'A eventuale aggiornamento della ricognizione regionale','acquisitionMethod':'Download shapefile DGRT 1155/2021 e attribuzione spaziale delle feature areali, lineari e puntuali ai confini comunali Istat 2026.','licenseName':'Open data Regione Toscana','licenseUrl':'https://www.regione.toscana.it/open-data'}
    mappings=((PORTAL_URL,'cb1-pmo-2026'),(PAB_URL,'regione-toscana-pab-annual'),(RETICOLO_URL,'regione-toscana-reticolo-2025'),(OPERE_URL,'regione-toscana-opere-idrauliche-2021'))
    for url,profile in mappings:
        reg.setdefault('sourceProfileByUrl',{})[url]=profile; reg.setdefault('sourceUrlProfiles',{})[url]=profile
    reg.setdefault('metricOverrides',{}).update({KEYS[0]:{'profile':'cb1-pmo-2026'},KEYS[1]:{'profile':'regione-toscana-pab-annual'},KEYS[2]:{'profile':'regione-toscana-pab-annual'},KEYS[3]:{'profile':'regione-toscana-reticolo-2025'},KEYS[4]:{'profile':'regione-toscana-opere-idrauliche-2021'}})
    reg['expectedMetricCount']=171; reg['expectedInlineMetricCount']=167; reg['expectedExternalMetricCount']=4

    checked='2026-08-30T23:42:08+00:00'
    def source_state(url, metrics, profile, frequency):
        return {'url':url,'ok':True,'status':200,'finalUrl':url,'contentType':'text/html','contentLength':None,'etag':'','lastModified':'','contentSha256':'','hashTruncated':False,'error':'','metrics':metrics,'roles':['primary'],'profileIds':[profile],'frequencies':[frequency]}
    state.setdefault('sources',{})[PORTAL_URL]=source_state(PORTAL_URL,[KEYS[0]],'cb1-pmo-2026','annual')
    state['sources'][PAB_URL]=source_state(PAB_URL,[KEYS[1],KEYS[2]],'regione-toscana-pab-annual','annual')
    state['sources'][RETICOLO_URL]=source_state(RETICOLO_URL,[KEYS[3]],'regione-toscana-reticolo-2025','irregular')
    state['sources'][OPERE_URL]=source_state(OPERE_URL,[KEYS[4]],'regione-toscana-opere-idrauliche-2021','irregular')
    periods={KEYS[0]:'2026',KEYS[1]:'2026',KEYS[2]:'2026',KEYS[3]:'2025',KEYS[4]:'2021'}
    for k in KEYS:
        state.setdefault('metrics',{})[k]={'publishedPeriod':periods[k],'checkedAt':checked,'observedLatestPeriod':periods[k],'status':'current'}
    state['checkedAt']=checked

    app0=ROOT/'assets/app-parts/00.txt'; txt=app0.read_text(encoding='utf-8')
    marker="      case 'hectaresPerFarm': return `${number2.format(v)} ha/azienda`;\n"
    additions=[]
    if "case 'km':" not in txt: additions.append("      case 'km': return `${number3.format(v)} km`;\n")
    if "case 'kmIntervention':" not in txt: additions.append("      case 'kmIntervention': return `${number3.format(v)} km-intervento`;\n")
    if additions:
        if marker not in txt: raise RuntimeError('Punto di inserimento formatter km non trovato')
        txt=txt.replace(marker,marker+''.join(additions),1); app0.write_text(txt,encoding='utf-8')

    app5=ROOT/'assets/app-parts/05.txt'; txt=app5.read_text(encoding='utf-8')
    old="      ['2026.08.31-v1.26.0','31 agosto 2026','169 indicatori complessivi in 11 temi, inclusi i 4 indicatori climatici. Aggiunto il lotto Bonifica e rischio idraulico con tre indicatori PAB 2026: km-intervento programmati, numero di interventi univoci e valore economico programmato; restano rinviati i dati che richiedono clipping del reticolo o estrazione massiva dello stato lavori.'],\n"
    new="      ['2026.08.31-v1.26.0','31 agosto 2026','171 indicatori complessivi in 11 temi, inclusi i 4 indicatori climatici. Lotto Bonifica e rischio idraulico: tre indicatori PAB 2026, lunghezza del reticolo in gestione DCRT 24/2025 e censimento comunale degli elementi di opere idrauliche DGRT 1155/2021. Restano rinviati solo i km fisici manutenzionati e lo stato lavori, che richiedono geometrie o estrazioni massive dedicate.'],\n"
    if old in txt: txt=txt.replace(old,new,1)
    elif '2026.08.31-v1.26.0' not in txt:
        marker5='    const versions = [\n'
        if marker5 not in txt: raise RuntimeError('Storico versioni non trovato')
        txt=txt.replace(marker5,marker5+new,1)
    app5.write_text(txt,encoding='utf-8')

    save(SITE,site); save(REGISTRY,reg); save(STATE,state)
    print('Bonifica e rischio idraulico v1.26.0 materializzato: 5 indicatori verificati; 2 candidati restano rinviati.')
if __name__=='__main__': main()
