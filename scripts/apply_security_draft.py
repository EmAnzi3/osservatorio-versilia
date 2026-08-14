#!/usr/bin/env python3
from __future__ import annotations
import csv, io, json, statistics, urllib.request, zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT/'data'/'site-data.json'
REGISTRY_PATH = ROOT/'data'/'source-registry.json'
SNAPSHOT_PATH = ROOT/'data'/'source-snapshots'/'sicurezza-territorio-draft-2026-08.json'
APP00 = ROOT/'assets'/'app-parts'/'00.txt'
APP03 = ROOT/'assets'/'app-parts'/'03.txt'
OPENBDAP_BASE='https://openbdap.rgs.mef.gov.it'
OPENBDAP_PORTAL=OPENBDAP_BASE+'/it/FET/Analizza'
TOWN_CODES={'Massarosa':'018','Viareggio':'033','Camaiore':'005','Pietrasanta':'024','Seravezza':'028','Forte dei Marmi':'013','Stazzema':'030'}

def load(path): return json.loads(path.read_text(encoding='utf-8'))
def save(path,value): path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def avg(values):
    clean=[float(v) for v in values if v is not None]
    return statistics.fmean(clean) if clean else None

def pop_lookup(data):
    out={}
    for row in data['metrics']['population']['rows']:
        s=row.get('series') or {}
        out[row['town']]={int(y):float(v) for y,v in zip(s.get('years',[]),s.get('values',[]))}
        out[row['town']].setdefault(int(data['metrics']['population']['meta']['year']),float(row['value']))
    return out

def fetch_mission03(year):
    url=f'{OPENBDAP_BASE}/Datasets_FET/Rendiconto/{year}/{year}_Rendiconto%20-%20Schemi%20di%20bilancio_TOSCANA.zip'
    req=urllib.request.Request(url,headers={'User-Agent':'OsservatorioVersilia/1.0'})
    with urllib.request.urlopen(req,timeout=120) as response: payload=response.read()
    with zipfile.ZipFile(io.BytesIO(payload)) as z:
        members=[i for i in z.infolist() if i.filename.endswith('Rendiconto SDB Spese Riepilogo Missioni_TOSCANA.csv')]
        if len(members)!=1: raise RuntimeError(f'{year}: file missioni inatteso')
        raw=z.read(members[0])
    text=None
    for enc in ('utf-8-sig','utf-8','cp1252','latin-1'):
        try: text=raw.decode(enc); break
        except UnicodeDecodeError: pass
    reverse={c:t for t,c in TOWN_CODES.items()}; result={}
    for row in csv.DictReader(io.StringIO(text),delimiter=';'):
        if (row.get('Codice Tipologia Soggetto') or '').strip()!='ELCOMU': continue
        if (row.get('Codice Provincia') or '').strip()!='046': continue
        code=(row.get('Codice Comune') or '').strip().zfill(3)
        if code not in reverse: continue
        if (row.get('Codice Missione') or '').strip().zfill(2)!='03': continue
        value=(row.get('Impegni') or '').strip()
        if value: result[reverse[code]]=float(value)
    if set(result)!=set(TOWN_CODES): raise RuntimeError(f'{year}: Missione 03 incompleta')
    return result

def build_road_safety(data,snap):
    old=data['metrics']['roadInjuries']; rows=[]; accum=[[],[],[],[]]
    for oldrow in old['rows']:
        raw=snap['towns'][oldrow['town']]
        specs=[
          ('Incidenti con lesioni','Incidenti',raw['roadIncidentRate'],'per1000'),
          ('Indice di mortalità','Mortalità',raw['roadMortalityIndex'],'per100'),
          ('Indice di lesività','Lesività',raw['roadInjuryIndex'],'per100'),
          ('Feriti ogni 10.000 residenti','Feriti',{'years':oldrow['series']['years'],'values':oldrow['series']['values']},'per10k')]
        parts=[]; component={}
        for i,(label,selector,series,unit) in enumerate(specs):
            value=series['values'][-1]; accum[i].append(value)
            parts.append({'label':label,'selectorLabel':selector,'value':value,'unit':unit})
            component[selector]=series
        rows.append({'town':oldrow['town'],'code':oldrow['code'],'slug':oldrow['slug'],'value':parts[0]['value'],'formatted':'','series':specs[0][2],'normalized':None,'benchmarkValue':parts[0]['value'],'parts':parts,'componentSeries':component})
    labels=[('Incidenti con lesioni','Incidenti','per1000'),('Indice di mortalità','Mortalità','per100'),('Indice di lesività','Lesività','per100'),('Feriti ogni 10.000 residenti','Feriti','per10k')]
    agg=[{'label':l,'selectorLabel':s,'value':avg(accum[i]),'unit':u} for i,(l,s,u) in enumerate(labels)]
    b=snap['benchmarks']['roadIncidentRate']
    return {'meta':{'key':'roadSafety','theme':'sicurezza','label':'Sicurezza stradale','shortLabel':'Sicurezza stradale','description':'Incidenti stradali con lesioni e gravità delle conseguenze. Il selettore distingue incidentalità, mortalità, lesività e feriti.','unit':'per1000','year':'2024','source':'Istat — A misura di Comune, incidenti stradali','polarity':'negative','compositeType':'securityMeasures','selectorLabel':'Lettura','searchTerms':['incidenti','mortalità stradale','lesività','feriti'],'benchmark':{'year':2024,'tuscany':b['tuscany'],'italy':b['italy'],'source':'Istat — A misura di Comune','url':snap['sources']['istat15a']['url'],'note':'Benchmark riferito agli incidenti con lesioni ogni 1.000 residenti.'}},'sourceUrl':snap['sources']['istat15a']['url'],'rows':rows,'aggregate':{'value':agg[0]['value'],'label':'Media semplice dei 7 comuni','note':'Ogni Comune pesa allo stesso modo; non è un dato ufficiale di area.','parts':agg},'normalizedAggregate':None,'method':{'type':'Dati ufficiali ed elaborazione Osservatorio','formula':'Incidentalità: incidenti con lesioni / popolazione residente media × 1.000; mortalità: morti / incidenti × 100; lesività: feriti / incidenti × 100; feriti: feriti / residenti × 10.000.','caveat':'L’intensità del traffico e la funzione delle strade incidono sul confronto. Mortalità e lesività sono instabili nei Comuni con pochi incidenti.','coverage':'7/7'}}

def build_fines(snap):
    rows=[]; acc=[[],[]]
    for town,raw in snap['towns'].items():
        parts=[{'label':'Proventi complessivi per abitante','selectorLabel':'Proventi €/abitante','value':raw['roadFinesPerResident']['values'][-1],'unit':'currency'},{'label':'Quota riferita ai limiti di velocità','selectorLabel':'Quota da velocità','value':raw['speedFineShare']['values'][-1],'unit':'percent'}]
        acc[0].append(parts[0]['value']); acc[1].append(parts[1]['value'])
        rows.append({'town':town,'code':raw['code'],'slug':town.lower().replace(' ','-').replace('à','a'),'value':parts[0]['value'],'formatted':'','series':raw['roadFinesPerResident'],'normalized':None,'benchmarkValue':parts[0]['value'],'parts':parts,'componentSeries':{'Proventi €/abitante':raw['roadFinesPerResident'],'Quota da velocità':raw['speedFineShare']}})
    agg=[{'label':'Proventi complessivi per abitante','selectorLabel':'Proventi €/abitante','value':avg(acc[0]),'unit':'currency'},{'label':'Quota riferita ai limiti di velocità','selectorLabel':'Quota da velocità','value':avg(acc[1]),'unit':'percent'}]
    b=snap['benchmarks']['roadFinesPerResident']
    return {'meta':{'key':'roadFinesPerResident','theme':'sicurezza','label':'Proventi da sanzioni al Codice della strada','shortLabel':'Sanzioni stradali','description':'Proventi per violazioni al Codice della strada rapportati alla popolazione residente media; il dettaglio distingue la quota riferita ai limiti di velocità.','unit':'currency','year':'2024','source':'Istat / Ministero dell’Interno — A misura di Comune','polarity':'neutral','compositeType':'securityMeasures','selectorLabel':'Lettura','searchTerms':['multe','sanzioni','codice della strada','autovelox'],'benchmark':{'year':2024,'tuscany':b['tuscany'],'italy':b['italy'],'source':'Istat / Ministero dell’Interno','url':snap['sources']['istat15c']['url'],'note':'Benchmark riferito ai proventi complessivi per abitante.'}},'sourceUrl':snap['sources']['istat15c']['url'],'rows':rows,'aggregate':{'value':agg[0]['value'],'label':'Media semplice dei 7 comuni','note':'Ogni Comune pesa allo stesso modo; il dato non misura direttamente il livello di sicurezza.','parts':agg},'normalizedAggregate':None,'method':{'type':'Dato ufficiale Istat / DAIT','formula':'Proventi complessivi CdS / popolazione residente media; quota velocità: proventi per violazioni dei limiti / proventi CdS complessivi × 100.','caveat':'Il valore dipende anche da turismo, traffico di attraversamento, intensità dei controlli e organizzazione della riscossione. Polarità neutra.','coverage':'7/7'}}

def build_mission(data):
    try:
        raw={y:fetch_mission03(y) for y in (2024,2025)}; pops=pop_lookup(data); rows=[]; total=0; poptot=0
        poprows={r['town']:r for r in data['metrics']['population']['rows']}
        for town in TOWN_CODES:
            vals=[raw[y][town]/pops[town][y] for y in (2024,2025)]; r=poprows[town]
            rows.append({'town':town,'code':r['code'],'slug':r['slug'],'value':vals[-1],'formatted':'','series':{'years':[2024,2025],'values':vals},'normalized':None,'benchmarkValue':vals[-1]})
            total+=raw[2025][town]; poptot+=pops[town][2025]
        return {'meta':{'key':'securityMissionExpenditurePerResident','theme':'sicurezza','label':'Spesa impegnata per ordine pubblico e sicurezza per residente','shortLabel':'Spesa per sicurezza','description':'Impegni della Missione 03 «Ordine pubblico e sicurezza» del rendiconto comunale, rapportati ai residenti.','unit':'currency','year':'2025','source':'Ragioneria generale dello Stato — OpenBDAP','polarity':'neutral','searchTerms':['ordine pubblico','sicurezza','missione 03','spesa sicurezza']},'sourceUrl':OPENBDAP_PORTAL,'rows':rows,'aggregate':{'value':total/poptot,'label':'Valore pro capite Versilia','note':'Totale degli impegni Missione 03 dei sette Comuni rapportato alla popolazione complessiva.'},'normalizedAggregate':None,'method':{'type':'Elaborazione Osservatorio su dati ufficiali','formula':'Impegni Missione 03 / popolazione residente.','caveat':'La classificazione comprende spesa corrente e in conto capitale; gestione associata, stagionalità e organizzazione dei servizi incidono sul confronto.','coverage':'7/7'}}, 'ok'
    except Exception as e: return None, f'{type(e).__name__}: {e}'

def patch_app(app):
    reps=[
      ("    if (metric.meta.compositeType === 'mobility') return { choice:'part-2', scale:'rate' };\n    return { choice:'', scale:'value' };", "    if (metric.meta.compositeType === 'mobility') return { choice:'part-2', scale:'rate' };\n    if (metric.meta.compositeType === 'securityMeasures') return { choice:'part-0', scale:'value' };\n    return { choice:'', scale:'value' };") ,
      ("    if (metric.meta.compositeType === 'mobility') {\n      const index = Math.max(0, Math.min(2, Number(String(choice || 'part-2').replace('part-','')) || 0));", "    if (metric.meta.compositeType === 'securityMeasures') {\n      const index=Math.max(0,Number(String(choice || 'part-0').replace('part-','')) || 0); const part=row.parts?.[index] || {}; return {value:part.value,unit:part.unit || metric.meta.unit,part,index};\n    }\n    if (metric.meta.compositeType === 'mobility') {\n      const index = Math.max(0, Math.min(2, Number(String(choice || 'part-2').replace('part-','')) || 0));"),
      ("    if (metric.meta.compositeType === 'mobility') {\n      const index = Math.max(0, Math.min(2, Number(String(choice || 'part-2').replace('part-','')) || 0));\n      const part = metric.aggregate?.parts?.[index] || {};", "    if (metric.meta.compositeType === 'securityMeasures') {\n      const index=Math.max(0,Number(String(choice || 'part-0').replace('part-','')) || 0); const part=metric.aggregate?.parts?.[index] || {}; return {value:part.value,unit:part.unit || metric.meta.unit,label:`Versilia · ${part.label || metric.meta.label}`,note:metric.aggregate?.note};\n    }\n    if (metric.meta.compositeType === 'mobility') {\n      const index = Math.max(0, Math.min(2, Number(String(choice || 'part-2').replace('part-','')) || 0));\n      const part = metric.aggregate?.parts?.[index] || {};"),
      ("    if (metric.meta.compositeType === 'mobility') {\n      const labels = metric.rows?.[0]?.parts || [];", "    if (metric.meta.compositeType === 'securityMeasures') {\n      const labels=metric.rows?.[0]?.parts || []; return `<div class=\"compare-view-controls\"><label class=\"compare-choice-select\"><span>${html(metric.meta.selectorLabel || 'Lettura')}</span><select data-composite-component>${labels.map((part,index)=>`<option value=\"part-${index}\" ${choice === `part-${index}` ? 'selected' : ''}>${html(part.selectorLabel || part.label)}</option>`).join('')}</select></label></div>`;\n    }\n    if (metric.meta.compositeType === 'mobility') {\n      const labels = metric.rows?.[0]?.parts || [];"),
      ("    const selectableComposite = ['stock','mobility','omi'].includes(compositeType);", "    const selectableComposite = ['stock','mobility','omi','securityMeasures'].includes(compositeType);"),
      ("    if (metric.meta.compositeType === 'mobility') {\n      const headParts = metric.rows?.[0]?.parts || [];", "    if (metric.meta.compositeType === 'securityMeasures') { const defaults=compositeCompareDefaults(metric); return `<div class=\"comparison-bars\">${compositeCompareBarRows(data,metricKey,defaults.choice,defaults.scale)}</div>`; }\n    if (metric.meta.compositeType === 'mobility') {\n      const headParts = metric.rows?.[0]?.parts || [];"),
      ("    if (metric.meta.compositeType === 'mobility') {\n      return `<div class=\"composite-town-mobility\">${parts.map((part,index)=>", "    if (metric.meta.compositeType === 'securityMeasures') { return `<div class=\"composite-town-mobility\">${parts.map((part,index)=>`<article class=\"${index===0?'balance':''}\"><span>${html(part.label)}</span><strong>${html(formatValue(part.value,part.unit || metric.meta.unit))}</strong><small>${html(metric.meta.year)}</small></article>`).join('')}</div>`; }\n    if (metric.meta.compositeType === 'mobility') {\n      return `<div class=\"composite-town-mobility\">${parts.map((part,index)=>"),
      ("    const panelOverline = composite ? (metric.meta.compositeType === 'mobility' ? 'Flussi e saldo' : omi ? 'Mercato immobiliare OMI' : stock ? 'Cittadinanza dei residenti' : 'Distribuzione completa')", "    const panelOverline = composite ? (metric.meta.compositeType === 'mobility' ? 'Flussi e saldo' : metric.meta.compositeType === 'securityMeasures' ? 'Letture del fenomeno' : omi ? 'Mercato immobiliare OMI' : stock ? 'Cittadinanza dei residenti' : 'Distribuzione completa')"),
      ("    const panelTitle = composite ? (metric.meta.compositeType === 'mobility' ? html(metric.meta.label) : omi ? `Quotazioni e zone OMI · ${metric.meta.year}` : stock ? `Residenti stranieri · ${metric.meta.year}` : `Composizione · ${metric.meta.year}`)", "    const panelTitle = composite ? (metric.meta.compositeType === 'mobility' ? html(metric.meta.label) : metric.meta.compositeType === 'securityMeasures' ? `${html(metric.meta.label)} · ${html(metric.meta.year)}` : omi ? `Quotazioni e zone OMI · ${metric.meta.year}` : stock ? `Residenti stranieri · ${metric.meta.year}` : `Composizione · ${metric.meta.year}`)"),
      ("    else if (metric.meta.compositeType) rows.forEach(row => (row.parts || []).forEach(part => lines.push([row.town, row.code, label, metric.meta.year, part.label, part.value, metric.meta.unit, part.count, metric.sourceUrl])));", "    else if (metric.meta.compositeType) rows.forEach(row => (row.parts || []).forEach(part => lines.push([row.town, row.code, label, metric.meta.year, part.label, part.value, part.unit || metric.meta.unit, part.count, metric.sourceUrl])));")]
    for old,new in reps:
        if new in app: continue
        if old not in app: raise RuntimeError('Patch app non applicabile: '+old[:80])
        app=app.replace(old,new,1)
    old="      ${themeKey === 'sicurezza' ? crimeMarkup(data) : ''}\n      ${themeKey === 'demografia' ? brainDrainMarkup(data) : ''}"
    new="      ${themeKey === 'sicurezza' ? localPoliceDraftMarkup(data) + crimeMarkup(data) : ''}\n      ${themeKey === 'demografia' ? brainDrainMarkup(data) : ''}"
    if new not in app:
        if old not in app: raise RuntimeError('Inserimento Polizia Locale compare non trovato')
        app=app.replace(old,new,1)
    old="    context.innerHTML = themeKey === 'sicurezza' ? crimeMarkup(data) : (themeKey === 'demografia' ? brainDrainMarkup(data) : '');"
    new="    context.innerHTML = themeKey === 'sicurezza' ? localPoliceDraftMarkup(data) + crimeMarkup(data) : (themeKey === 'demografia' ? brainDrainMarkup(data) : '');"
    if new not in app:
        if old not in app: raise RuntimeError('Inserimento Polizia Locale town non trovato')
        app=app.replace(old,new,1)
    if 'function localPoliceDraftMarkup(data)' not in app:
        marker='  function crimeMarkup(data) {'
        fn="""  function localPoliceDraftMarkup(data) {
    const p=data.securityDraft?.localPolice; if(!p) return '';
    return `<section class=\"crime-context brain-drain-context page-width\" id=\"polizia-locale\"><div class=\"crime-context-copy\"><span class=\"overline\">Presidio locale · dato in verifica</span><h2>Polizia Locale</h2><p>Il monitoraggio regionale 2025 quantifica il personale complessivo toscano, ma le tavole pubblicate non espongono righe comunali utilizzabili per un confronto 7/7. L’Osservatorio non attribuisce quindi valori stimati ai singoli Comuni.</p><a class=\"source-pill\" href=\"${html(p.sourceUrl)}\" target=\"_blank\" rel=\"noreferrer\">Fonte Regione Toscana ↗</a></div><div class=\"crime-context-data\"><h3>Monitoraggio regionale · 2025</h3><div class=\"crime-stats\"><article><span>Addetti rilevati</span><strong>${html(number0.format(p.tuscanyStaff))}</strong><small>totale Toscana</small></article><article><span>Strutture rispondenti</span><strong>${html(number0.format(p.respondingStructures))}</strong><small>Polizie Locali</small></article><article><span>Comuni rappresentati</span><strong>${html(number0.format(p.municipalitiesRepresented))}</strong><small>dato aggregato</small></article></div><p class=\"brain-drain-note\">Il riquadro non è conteggiato come indicatore comunale: verrà promosso solo con una fonte ufficiale omogenea per Comune.</p></div></section>`;
  }

"""
        if marker not in app: raise RuntimeError('crimeMarkup non trovato')
        app=app.replace(marker,fn+marker,1)
    return app

def main():
    data=load(DATA_PATH); snap=load(SNAPSHOT_PATH)
    if 'roadInjuries' in data['metrics']:
        data['metrics']['roadSafety']=build_road_safety(data,snap); data['metrics'].pop('roadInjuries')
    data['metrics']['roadFinesPerResident']=build_fines(snap)
    mission,status=build_mission(data)
    if mission: data['metrics']['securityMissionExpenditurePerResident']=mission
    else: data['metrics'].pop('securityMissionExpenditurePerResident',None)
    metrics=['roadSafety']+(['securityMissionExpenditurePerResident'] if mission else [])+['roadFinesPerResident']
    data['themes']['sicurezza'].update({'question':'Quanto è sicuro il territorio e quali risorse vengono dedicate al presidio?','description':'Sicurezza stradale, risorse comunali e controllo della circolazione, mantenendo criminalità e Polizia Locale alla scala realmente disponibile.','metrics':metrics,'sections':[{'key':'sicurezza-stradale','label':'Sicurezza stradale','description':'Frequenza degli incidenti e gravità delle conseguenze, con serie comunali omogenee.','metrics':['roadSafety']},{'key':'risorse-controllo','label':'Risorse e controllo','description':'Spesa comunale per ordine pubblico e sicurezza e proventi delle sanzioni al Codice della strada.','metrics':[k for k in ('securityMissionExpenditurePerResident','roadFinesPerResident') if k in data['metrics']]}],'featured':metrics[:3]})
    lp=snap['sources']['localPolice2025']; data['securityDraft']={'status':'draft','mission03Status':status,'localPolice':{'sourceUrl':lp['url'],'usableForMunicipalComparison':False,'note':lp['note'],'tuscanyStaff':lp['tuscany']['staff'],'respondingStructures':lp['tuscany']['respondingStructures'],'municipalitiesRepresented':lp['tuscany']['municipalitiesRepresented']}}
    save(DATA_PATH,data)
    reg=load(REGISTRY_PATH); ext=int(reg.get('expectedExternalMetricCount',4)); reg['expectedMetricCount']=len(data['metrics']); reg['expectedInlineMetricCount']=len(data['metrics'])-ext; reg['expectedExternalMetricCount']=ext
    reg.setdefault('sourceProfileByUrl',{})[snap['sources']['istat15a']['url']]='istat-road-annual'; reg['sourceProfileByUrl'][snap['sources']['istat15c']['url']]='istat-road-annual'
    reg.setdefault('metricOverrides',{})['roadSafety']={'profile':'istat-road-annual'}; reg['metricOverrides']['roadFinesPerResident']={'profile':'istat-road-annual'}
    if mission: reg['metricOverrides']['securityMissionExpenditurePerResident']={'frequency':'annual','frequencyLabel':'Annuale','expectedRelease':'Dopo il consolidamento del rendiconto','acquisitionMethod':'Download OpenBDAP del rendiconto e lettura degli impegni della Missione 03.','publisher':'Ragioneria generale dello Stato — OpenBDAP'}
    save(REGISTRY_PATH,reg)
    a0=APP00.read_text(encoding='utf-8'); anchor="    capitalPayments: ['investimenti', 'conto capitale', 'pagamenti capitale']"
    if 'roadSafety:' not in a0:
        if anchor not in a0: raise RuntimeError('Anchor sinonimi non trovato')
        a0=a0.replace(anchor,"    roadSafety: ['incidenti', 'sicurezza stradale', 'mortalità', 'lesività', 'feriti'],\n    roadFinesPerResident: ['multe', 'sanzioni', 'codice della strada', 'autovelox'],\n    securityMissionExpenditurePerResident: ['ordine pubblico', 'sicurezza', 'missione 03', 'spesa sicurezza'],\n"+anchor,1)
        APP00.write_text(a0,encoding='utf-8')
    APP03.write_text(patch_app(APP03.read_text(encoding='utf-8')),encoding='utf-8')
    print(f'Draft sicurezza applicato: {len(data["metrics"])} indicatori; Missione 03: {status}')

if __name__=='__main__': main()
