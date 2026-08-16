#!/usr/bin/env python3
"""Materialize validated TARI, IMU, fuel, waste and long-income context after IRPEF draft."""
from __future__ import annotations
import json, statistics
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data/site-data.json'; REG=ROOT/'data/source-registry.json'
SNAP=ROOT/'data/source-snapshots/costi-fiscalita-validated-2026-08.json'
TARI='tariStandardHousehold'; IMU='municipalImuStandard'; FUEL='fuelPrices'; WASTE='wasteServiceCost'; IRPEF='municipalIrpef'
TARI_URL='https://www1.finanze.gov.it/finanze2/dipartimentopolitichefiscali/fiscalitalocale/nuova_at/'
IMU_URL='https://www1.finanze.gov.it/finanze2/dipartimentopolitichefiscali/fiscalitalocale/nuova_imu/'
MEF_INCOME='https://www1.finanze.gov.it/finanze/analisi_stat/public/index.php'

def load(p): return json.loads(p.read_text(encoding='utf-8'))
def save(p,v): p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def avg(v):
    x=[float(n) for n in v if n is not None]; return statistics.fmean(x) if x else None

def ids(data): return {r['town']:{'code':r['code'],'slug':r['slug']} for r in data['metrics']['income']['rows']}
def row(town,ident,value,year):
    return {'town':town,'code':ident[town]['code'],'slug':ident[town]['slug'],'value':value,'formatted':'','series':{'years':[year],'values':[value]},'normalized':None,'benchmarkValue':value}

def tari(data,s):
    raw=s['tari']; ident=ids(data); rows=[]; vals=[]
    for base in data['metrics']['income']['rows']:
        town=base['town']; value=float(raw['towns'][town]['annualCost']); vals.append(value); r=row(town,ident,value,raw['year']); r['tariffDetail']=raw['towns'][town]; rows.append(r)
    return {'meta':{'key':TARI,'theme':'economia','label':'TARI standardizzata · 3 persone, 100 m²','shortLabel':'TARI · 3 persone / 100 m²','description':'Spesa annua TARI per una stessa utenza domestica teorica residente di 3 componenti e 100 m², senza agevolazioni personali. Include TEFA e componenti perequative 2025.','unit':'currency2','year':'2025','source':'Comuni / MEF / ARERA','polarity':'neutral','searchTerms':['tari','tariffa rifiuti','tassa rifiuti','100 mq','3 persone']},'sourceUrl':TARI_URL,'rows':rows,'aggregate':{'value':avg(vals),'label':'Media semplice dei 7 comuni','note':'Confronto standardizzato della stessa utenza teorica; ogni Comune pesa allo stesso modo.'},'normalizedAggregate':None,'method':{'type':'Elaborazione Osservatorio su tariffe ufficiali 2025','formula':'100 m² × quota fissa + quota variabile per 3 componenti; TEFA 5%; + 7,60 € di componenti perequative ARERA 2025.','caveat':'Nessuna riduzione personale. Stazzema usa l’importo ufficiale pubblicato per 3 componenti / 100 m² come base.','coverage':'7/7'}}

def imu(data,s):
    raw=s['imu']; ident=ids(data); rows=[]; taxes=[]; rates=[]
    for base in data['metrics']['income']['rows']:
        town=base['town']; tr=raw['towns'][town]; tax=float(tr['annualTax']); rate=float(tr['ratePercent']); taxes.append(tax); rates.append(rate); parts=[{'label':'Imposta annua','selectorLabel':'Imposta annua','value':tax,'unit':'currency'},{'label':'Aliquota','selectorLabel':'Aliquota','value':rate,'unit':'percent'}]; r=row(town,ident,tax,raw['year']); r.update({'parts':parts,'componentSeries':{'Imposta annua':{'years':[raw['year']],'values':[tax]},'Aliquota':{'years':[raw['year']],'values':[rate]}}}); rows.append(r)
    ap=[{'label':'Imposta annua','selectorLabel':'Imposta annua','value':avg(taxes),'unit':'currency'},{'label':'Aliquota','selectorLabel':'Aliquota','value':avg(rates),'unit':'percent'}]
    return {'meta':{'key':IMU,'theme':'economia','label':'IMU seconda abitazione standardizzata','shortLabel':'IMU seconda abitazione','description':'Imposta annua teorica su una seconda abitazione A/2 con base imponibile IMU identica di 100.000 €, usando l’aliquota 2025 «Altri fabbricati».','unit':'currency','year':'2025','source':'Dipartimento delle Finanze — MEF','polarity':'neutral','compositeType':'securityMeasures','selectorLabel':'Lettura','searchTerms':['imu','seconda casa','seconda abitazione','aliquota imu']},'sourceUrl':IMU_URL,'rows':rows,'aggregate':{'value':ap[0]['value'],'label':'Media semplice dei 7 comuni','note':'Benchmark su base imponibile identica di 100.000 €; non rappresenta una casa tipica.','parts':ap},'normalizedAggregate':None,'method':{'type':'Elaborazione Osservatorio su prospetti ufficiali MEF','formula':'100.000 € × aliquota IMU 2025 della categoria «Altri fabbricati».','caveat':'La base imponibile è standardizzata per isolare l’effetto dell’aliquota comunale.','coverage':'7/7'}}

def fuel(data,s):
    raw=s['fuel']; ident=ids(data); rows=[]; ps=[]; ds=[]
    for base in data['metrics']['income']['rows']:
        town=base['town']; tr=raw['towns'][town]; p=tr.get('benzina'); d=tr.get('gasolio'); ps.extend([] if p is None else [p]); ds.extend([] if d is None else [d]); parts=[{'label':'Benzina self','selectorLabel':'Benzina self','value':p,'unit':'eurliter'},{'label':'Gasolio self','selectorLabel':'Gasolio self','value':d,'unit':'eurliter'}]; r=row(town,ident,p,raw['referenceDate']); r.update({'parts':parts,'stationCount':tr.get('stations',0),'componentSeries':{'Benzina self':{'years':[raw['referenceDate']],'values':[p]},'Gasolio self':{'years':[raw['referenceDate']],'values':[d]}}}); rows.append(r)
    ap=[{'label':'Benzina self','selectorLabel':'Benzina self','value':avg(ps),'unit':'eurliter'},{'label':'Gasolio self','selectorLabel':'Gasolio self','value':avg(ds),'unit':'eurliter'}]
    return {'meta':{'key':FUEL,'theme':'mobilita','label':'Prezzi carburanti self-service','shortLabel':'Prezzi carburanti','description':'Mediana comunale dei prezzi self-service negli impianti attivi MIMIT. Stazzema è n.d. perché non risultano impianti attivi.','unit':'eurliter','year':raw['referenceDate'],'source':'MIMIT — Osservaprezzi carburanti','polarity':'neutral','compositeType':'securityMeasures','selectorLabel':'Carburante','searchTerms':['benzina','gasolio','diesel','carburante']},'sourceUrl':raw['sourceUrls']['prezzi'],'rows':rows,'aggregate':{'value':ap[0]['value'],'label':'Media delle mediane comunali disponibili','note':'Media semplice dei sei Comuni con impianti attivi; Stazzema resta n.d.','parts':ap},'normalizedAggregate':None,'method':{'type':'Elaborazione Osservatorio su open data MIMIT','formula':'Mediana dei prezzi self-service degli impianti attivi per Comune e carburante.','caveat':'Fotografia del 14 agosto 2026; Stazzema non ha impianti attivi nel dataset.','coverage':'6/7'}}

def waste(data,s):
    raw=s['waste']; ident=ids(data); rows=[]; vals=[]
    for base in data['metrics']['income']['rows']:
        town=base['town']; value=float(raw['towns'][town]['ctotPerResident']); vals.append(value); rows.append(row(town,ident,value,raw['year']))
    return {'meta':{'key':WASTE,'theme':'ambiente','label':'Costo totale del servizio rifiuti per abitante','shortLabel':'Costo servizio rifiuti','description':'Costi totali di gestione del servizio di igiene urbana (CTOTab) rapportati agli abitanti.','unit':'eurPerResident','year':'2024','source':'ISPRA — Catasto nazionale rifiuti','polarity':'neutral','searchTerms':['costo rifiuti','ctotab','igiene urbana']},'sourceUrl':raw['sourceUrl'],'rows':rows,'aggregate':{'value':avg(vals),'label':'Media semplice dei 7 comuni','note':'Ogni Comune pesa allo stesso modo; non è un dato ufficiale aggregato della Versilia.'},'normalizedAggregate':None,'method':{'type':'Dato ufficiale ISPRA','formula':'CTOTab: costi totali di gestione del servizio di igiene urbana / abitanti.','caveat':'Accettate esclusivamente righe comunali ISPRA con «N. di comuni = 1».','coverage':'7/7'}}

def add_after(items,key,after):
    if key in items:return
    items.insert(items.index(after)+1,key) if after in items else items.append(key)

def themes(data):
    e=data['themes']['economia']; add_after(e['metrics'],TARI,IRPEF); add_after(e['metrics'],IMU,TARI); sec=next((x for x in e['sections'] if x.get('key')=='costi-fiscalita'),None)
    if sec: sec.update({'description':'Tributi e costi standardizzati per confrontare regole comunali diverse sullo stesso caso teorico.','metrics':[IRPEF,TARI,IMU]})
    else: sec={'key':'costi-fiscalita','label':'Costi e fiscalità locale','description':'Tributi e costi standardizzati per confrontare regole comunali diverse sullo stesso caso teorico.','metrics':[IRPEF,TARI,IMU]}; i=next((i for i,x in enumerate(e['sections']) if x.get('key')=='redditi'),-1);e['sections'].insert(i+1,sec)
    e['description']='Redditi, costo della vita, fiscalità locale, unità locali, addetti, struttura produttiva, imprenditorialità e capacità turistica.'
    m=data['themes']['mobilita']; add_after(m['metrics'],FUEL,'pollutingCars'); vs=next((x for x in m['sections'] if 'motorization' in x.get('metrics',[])),None)
    if vs: add_after(vs['metrics'],FUEL,'pollutingCars'); vs['label']='Mezzi, carburanti e infrastrutture';vs['description']='Motorizzazione, veicoli più inquinanti, prezzi dei carburanti self-service e ricarica elettrica.'
    a=data['themes']['ambiente']; add_after(a['metrics'],WASTE,'wastePerResident'); ws=next((x for x in a['sections'] if 'wastePerResident' in x.get('metrics',[]) or 'recycling' in x.get('metrics',[])),None)
    if ws: add_after(ws['metrics'],WASTE,'wastePerResident' if 'wastePerResident' in ws['metrics'] else 'recycling');ws['description']='Produzione, raccolta differenziata e costo complessivo del servizio rifiuti.'

def long_income(data,s):
    inc=data['metrics']['income']; long=s['incomeLongHistory']; years=long['years']
    for r in inc['rows']: r['longSeries']={'years':years,'values':long['towns'][r['town']]['values']}
    inc['meta'].update({'longHistoryLabel':'Reddito imponibile medio · serie lunga','longHistoryYears':'2011–2024','longHistorySource':'Dipartimento delle Finanze — MEF','longHistorySourceUrl':MEF_INCOME,'longHistoryNote':'Il valore corrente resta il reddito complessivo medio dichiarato. La vista 2011–2024 usa la variabile MEF omogenea «Reddito imponibile — Ammontare / Frequenza», distinta dal dato corrente.'}); inc['longAggregate']={'years':years,'values':long['aggregate']['values'],'label':'Imponibile medio Versilia','note':long['aggregate']['method']}; ctx=dict(s['incomeInflationContext']);ctx.update({'incomeSourceUrl':MEF_INCOME,'priceSourceUrl':s['nicToscana']['sourceUrl'],'priceSource':s['nicToscana']['source']});data['incomeInflationContext']=ctx

def registry(data,s):
    reg=load(REG); external=int(reg.get('expectedExternalMetricCount',4));reg['expectedMetricCount']=len(data['metrics']);reg['expectedInlineMetricCount']=len(data['metrics'])-external;reg['expectedExternalMetricCount']=external; profiles=reg.setdefault('sourceProfiles',{});mapping=reg.setdefault('sourceProfileByUrl',{});over=reg.setdefault('metricOverrides',{})
    profiles['mef-municipal-tax-annual']={'publisher':'Dipartimento delle Finanze — MEF / Comuni','frequency':'annual','frequencyLabel':'Annuale','expectedRelease':'Dopo la pubblicazione delle aliquote o tariffe annuali','acquisitionMethod':'Lettura dei prospetti e delle tariffe ufficiali; scenari comparabili senza agevolazioni personali.','licenseName':'Condizioni indicate dalle fonti','licenseUrl':IMU_URL}; profiles['mimit-fuel-daily']={'publisher':'Ministero delle Imprese e del Made in Italy','frequency':'daily','frequencyLabel':'Giornaliera','expectedRelease':'Aggiornamento quotidiano','acquisitionMethod':'Incrocio anagrafica impianti attivi e prezzi self-service; mediana comunale.','licenseName':'Open data MIMIT','licenseUrl':s['fuel']['sourceUrls']['prezzi']}; mapping[TARI_URL]='mef-municipal-tax-annual';mapping[IMU_URL]='mef-municipal-tax-annual';mapping[s['fuel']['sourceUrls']['prezzi']]='mimit-fuel-daily'; over[TARI]={'profile':'mef-municipal-tax-annual'};over[IMU]={'profile':'mef-municipal-tax-annual'};over[FUEL]={'profile':'mimit-fuel-daily'};over[WASTE]={'profile':'ispra-environment-annual'};save(REG,reg)

def main():
    data=load(DATA);s=load(SNAP)
    if IRPEF in data['metrics']:
        data['metrics'][IRPEF]['meta']['unit']='currency2'
        for r in data['metrics'][IRPEF]['rows']:
            for p in r.get('parts',[]):p['unit']='currency2'
        for p in data['metrics'][IRPEF].get('aggregate',{}).get('parts',[]):p['unit']='currency2'
    data['metrics'][TARI]=tari(data,s);data['metrics'][IMU]=imu(data,s);data['metrics'][FUEL]=fuel(data,s);data['metrics'][WASTE]=waste(data,s);long_income(data,s);themes(data);data['costsFiscalDraft']={'status':'draft','auditDate':s['created'],'publishedInDraft':[IRPEF,TARI,IMU,FUEL,WASTE],'contextViews':['incomeLongHistory','incomeInflationContext'],'notPublished':['schoolMeals'],'note':'Mensa esclusa per eterogeneità. Carburanti 6/7 con Stazzema n.d.; gli altri nuovi indicatori 7/7.'};save(DATA,data);registry(data,s);print(f"Validated costs draft materialized: {len(data['metrics'])} metrics = {len(data['metrics'])-4} inline + 4 external")
if __name__=='__main__':main()
